from datetime import datetime, timedelta, timezone
import math
import re
import requests
from config import (
    AVIATION_WEATHER_BASE, HTTP_HEADERS,
    FAA_NOTAM_API_URL, FAA_NOTAM_CLIENT_ID, FAA_NOTAM_CLIENT_SECRET,
)
from flightplanner.models.airport import get_coords


def _utc_now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Well-known permanent / long-standing TFRs with geometry
# These are always included when they fall within the route bounding box.
# Coordinates from FAA aeronautical data.
# ---------------------------------------------------------------------------

KNOWN_TFRS = [
    {
        'notam_id': 'FDC 1/9440',
        'type': 'Permanent - 14 CFR 91.143',
        'description': (
            'DISNEYLAND RESORT, ANAHEIM CA - Flight restriction. '
            'No person may operate an aircraft within a 3 NM radius of '
            "33°48'33\"N / 117°55'08\"W (Disneyland Resort) SFC-3000 AGL. "
            '14 CFR 91.143. Except DOD, law enforcement, air ambulance, '
            'and aircraft in contact with ATC.'
        ),
        'center_lat': 33.8092,
        'center_lon': -117.9189,
        'radius_nm': 3,
        'effective': 'Permanent',
        'expires': 'None',
        'coords': [],
        'simulated': False,
    },
    {
        'notam_id': 'FDC 1/0481',
        'type': 'Permanent - 14 CFR 91.143',
        'description': (
            'WALT DISNEY WORLD, ORLANDO FL - Flight restriction. '
            'No person may operate an aircraft within a 3 NM radius of '
            "28°25'12\"N / 081°34'52\"W (Walt Disney World) SFC-3000 AGL. "
            '14 CFR 91.143.'
        ),
        'center_lat': 28.4200,
        'center_lon': -81.5811,
        'radius_nm': 3,
        'effective': 'Permanent',
        'expires': 'None',
        'coords': [],
        'simulated': False,
    },
    {
        'notam_id': 'DC SFRA/FRZ',
        'type': 'Permanent - DC SFRA',
        'description': (
            'WASHINGTON DC - Special Flight Rules Area (SFRA). '
            '30 NM radius of DCA VOR/DME SFC-18000 MSL. '
            'Flight Restricted Zone (FRZ) within 15 NM. '
            'All aircraft must comply with 14 CFR 93.B procedures.'
        ),
        'center_lat': 38.8512,
        'center_lon': -77.0402,
        'radius_nm': 30,
        'effective': 'Permanent',
        'expires': 'None',
        'coords': [],
        'simulated': False,
    },
]


def _get_known_tfrs_for_bbox(route_bbox):
    """Return well-known TFRs that overlap the route bounding box."""
    if not route_bbox:
        return []
    min_lat, min_lon, max_lat, max_lon = route_bbox
    # Extend bbox by 1 degree for proximity check
    min_lat -= 1
    min_lon -= 1
    max_lat += 1
    max_lon += 1

    result = []
    for tfr in KNOWN_TFRS:
        lat = tfr['center_lat']
        lon = tfr['center_lon']
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            result.append(dict(tfr))
    return result


# ---------------------------------------------------------------------------
# Simulated fallbacks (kept from v2 for when APIs are unreachable)
# ---------------------------------------------------------------------------

def simulate_metar(station):
    now = _utc_now()
    h = sum(ord(c) for c in station) + now.hour
    wd, ws = (h * 37) % 36 * 10, 5 + (h % 15)
    t, d = 15 + (h % 20) - 10, 10 + (h % 15) - 10
    alt = 29.80 + (h % 40) / 100
    vis = 10 if (h % 10) > 2 else (h % 10) + 3
    fltcat = 'VFR' if vis >= 5 else ('MVFR' if vis >= 3 else 'IFR')
    return {
        'icaoId': station,
        'rawOb': f"{station} {now.strftime('%d%H%M')}Z {wd:03d}{ws:02d}KT {vis}SM FEW050 {t:02d}/{d:02d} A{int(alt * 100)}",
        'fltcat': fltcat, 'simulated': True,
    }


def simulate_taf(station):
    now = _utc_now()
    h = sum(ord(c) for c in station)
    end = now + timedelta(hours=24)
    return {
        'icaoId': station,
        'rawTAF': f"TAF {station} {now.strftime('%d%H%M')}Z {now.strftime('%d%H')}/{end.strftime('%d%H')} {(h * 41) % 36 * 10:03d}{8 + (h % 12):02d}KT P6SM FEW050",
        'simulated': True,
    }


def simulate_winds(lat, lon):
    h = int((lat * 100 + lon * 100) % 1000)
    return {
        'station': 'ESTIMATED', 'simulated': True,
        'levels': {
            3000: {'direction': (h * 7) % 360, 'speed': 10 + (h % 10), 'temp': 10},
            6000: {'direction': (h * 11) % 360, 'speed': 15 + (h % 15), 'temp': 3},
            9000: {'direction': (h * 13) % 360, 'speed': 20 + (h % 20), 'temp': -4},
            12000: {'direction': (h * 17) % 360, 'speed': 25 + (h % 25), 'temp': -11},
        },
    }


# ---------------------------------------------------------------------------
# METAR / TAF (aviationweather.gov - free, no key)
# ---------------------------------------------------------------------------

def fetch_metar(station):
    try:
        r = requests.get(
            f"{AVIATION_WEATHER_BASE}/metar?ids={station}&format=json",
            timeout=8, headers=HTTP_HEADERS,
        )
        if r.status_code == 200 and r.text.strip().startswith('['):
            data = r.json()
            if data:
                data[0]['simulated'] = False
                return data[0]
    except Exception:
        pass
    return simulate_metar(station)


def fetch_taf(station):
    try:
        r = requests.get(
            f"{AVIATION_WEATHER_BASE}/taf?ids={station}&format=json",
            timeout=8, headers=HTTP_HEADERS,
        )
        if r.status_code == 200 and r.text.strip().startswith('['):
            data = r.json()
            if data:
                data[0]['simulated'] = False
                return data[0]
    except Exception:
        pass
    return simulate_taf(station)


# ---------------------------------------------------------------------------
# PIREPs (aviationweather.gov - free, no key)
# ---------------------------------------------------------------------------

def fetch_pireps(stations):
    """Fetch PIREPs near route stations."""
    pireps = []
    seen = set()
    for station in stations:
        try:
            r = requests.get(
                f"{AVIATION_WEATHER_BASE}/pirep",
                params={'id': station, 'distance': 100, 'format': 'json'},
                timeout=10, headers=HTTP_HEADERS,
            )
            if r.status_code == 200 and r.text.strip().startswith('['):
                for p in r.json():
                    raw = p.get('rawOb', '')
                    if raw and raw not in seen:
                        seen.add(raw)
                        pireps.append({
                            'station': p.get('icaoId', ''),
                            'type': p.get('pirepType', 'UA'),
                            'rawOb': raw,
                            'lat': p.get('lat'),
                            'lon': p.get('lon'),
                            'altitude': p.get('fltLvl', ''),
                            'aircraft': p.get('acType', ''),
                            'turbulence': _format_turb(p),
                            'icing': _format_ice(p),
                            'simulated': False,
                        })
        except Exception:
            pass
    return pireps


def _format_turb(p):
    intensity = p.get('tbInt1', '')
    if not intensity:
        return ''
    base = p.get('tbBas1', '')
    top = p.get('tbTop1', '')
    parts = [intensity]
    if base or top:
        parts.append(f"{base}-{top}" if base and top else str(base or top))
    return ' '.join(str(x) for x in parts if x)


def _format_ice(p):
    intensity = p.get('icgInt1', '')
    if not intensity:
        return ''
    base = p.get('icgBas1', '')
    top = p.get('icgTop1', '')
    parts = [intensity]
    if base or top:
        parts.append(f"{base}-{top}" if base and top else str(base or top))
    return ' '.join(str(x) for x in parts if x)


# ---------------------------------------------------------------------------
# AIRMETs / SIGMETs (aviationweather.gov - free, no key)
# ---------------------------------------------------------------------------

def fetch_airmets_sigmets(route_bbox):
    """Fetch AIRMETs/SIGMETs filtered to route area."""
    results = []
    try:
        r = requests.get(
            f"{AVIATION_WEATHER_BASE}/airsigmet",
            params={'format': 'json'},
            timeout=10, headers=HTTP_HEADERS,
        )
        if r.status_code == 200 and r.text.strip().startswith('['):
            for item in r.json():
                coords = item.get('coords', [])
                if _coords_overlap_bbox(coords, route_bbox):
                    results.append({
                        'type': item.get('airSigmetType', 'UNKNOWN'),
                        'hazard': item.get('hazard', ''),
                        'severity': item.get('severity', ''),
                        'raw': item.get('rawAirSigmet', ''),
                        'valid_from': item.get('validTimeFrom', ''),
                        'valid_to': item.get('validTimeTo', ''),
                        'altitude_low': item.get('altitudeLow1', ''),
                        'altitude_high': item.get('altitudeHi1', ''),
                        'coords': coords,
                        'simulated': False,
                    })
    except Exception:
        pass
    return results


def _coords_overlap_bbox(coords, bbox):
    if not coords or not bbox:
        return True
    min_lat, min_lon, max_lat, max_lon = bbox
    min_lat -= 2
    min_lon -= 2
    max_lat += 2
    max_lon += 2
    for c in coords:
        lat = c.get('lat', 0)
        lon = c.get('lon', 0)
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return True
    return False


# ---------------------------------------------------------------------------
# NOTAMs (FAA NOTAM API - requires free API key from api.faa.gov)
# ---------------------------------------------------------------------------

def _has_notam_api_key():
    return bool(FAA_NOTAM_CLIENT_ID and FAA_NOTAM_CLIENT_SECRET)


def fetch_notams(station):
    """Fetch NOTAMs for a station."""
    if not _has_notam_api_key():
        return [{
            'airport': station,
            'text': f'Configure FAA API key for live NOTAMs. '
                    f'Check https://notams.aim.faa.gov for {station}',
            'classification': 'INFO',
            'simulated': True,
        }]

    notams = []
    try:
        r = requests.get(
            FAA_NOTAM_API_URL,
            params={
                'icaoLocation': station,
                'responseFormat': 'geoJson',
            },
            headers={
                'client_id': FAA_NOTAM_CLIENT_ID,
                'client_secret': FAA_NOTAM_CLIENT_SECRET,
            },
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get('items', [])
            if not items and 'features' in data:
                items = data['features']

            for item in items[:25]:
                props = item.get('properties', item)
                core = props.get('coreNOTAMData', {}).get('notam', props)

                notam_text = core.get('text', core.get('message', ''))
                if not notam_text:
                    continue

                classification = core.get('classification', '')
                notam_id = core.get('id', core.get('notamId', ''))
                effective = core.get('effectiveStart', '')
                expires = core.get('effectiveEnd', '')
                location = core.get('location', station)

                notams.append({
                    'airport': location if location else station,
                    'notam_id': notam_id,
                    'text': notam_text,
                    'classification': classification,
                    'effective': effective,
                    'expires': expires,
                    'simulated': False,
                })
    except Exception as e:
        notams.append({
            'airport': station,
            'text': f'Error fetching NOTAMs: {e}. '
                    f'Check https://notams.aim.faa.gov for {station}',
            'classification': 'ERROR',
            'simulated': True,
        })

    if not notams:
        notams.append({
            'airport': station,
            'text': f'No active NOTAMs for {station}',
            'classification': 'NONE',
            'simulated': False,
        })

    return notams


# ---------------------------------------------------------------------------
# TFRs (FAA NOTAM API for FDC NOTAMs + fallback: scrape tfr.faa.gov)
# ---------------------------------------------------------------------------

def fetch_tfrs(route_bbox):
    """Fetch TFRs relevant to the route, always including known permanent TFRs."""
    # Start with well-known permanent TFRs near the route
    tfrs = _get_known_tfrs_for_bbox(route_bbox)
    known_ids = {t['notam_id'] for t in tfrs}

    # Fetch live TFRs from API or scrape
    if _has_notam_api_key():
        live = _fetch_tfrs_via_api(route_bbox)
    else:
        live = _fetch_tfrs_via_scrape(route_bbox)

    # Merge, avoiding duplicates
    for t in live:
        if t['notam_id'] not in known_ids:
            tfrs.append(t)

    if not tfrs:
        tfrs.append({
            'notam_id': 'INFO',
            'type': 'INFO',
            'description': 'No TFRs found along route. '
                           'Always verify at https://tfr.faa.gov',
            'coords': [],
            'simulated': False,
        })

    # Always add advisory
    tfrs.append({
        'notam_id': 'ADVISORY',
        'type': 'INFO',
        'description': 'Always verify TFRs at https://tfr.faa.gov before flight',
        'coords': [],
        'simulated': False,
    })

    return tfrs


def _fetch_tfrs_via_api(route_bbox):
    """Fetch TFRs from FAA NOTAM API (FDC type)."""
    tfrs = []
    min_lat, min_lon, max_lat, max_lon = route_bbox
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    radius_nm = max(50, int(
        math.sqrt((max_lat - min_lat) ** 2 + (max_lon - min_lon) ** 2) * 60 / 2
    ))

    try:
        r = requests.get(
            FAA_NOTAM_API_URL,
            params={
                'responseFormat': 'geoJson',
                'notamType': 'FDC',
                'locationLongitude': center_lon,
                'locationLatitude': center_lat,
                'locationRadius': min(radius_nm, 200),
            },
            headers={
                'client_id': FAA_NOTAM_CLIENT_ID,
                'client_secret': FAA_NOTAM_CLIENT_SECRET,
            },
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get('items', [])
            if not items and 'features' in data:
                items = data['features']

            for item in items:
                props = item.get('properties', item)
                core = props.get('coreNOTAMData', {}).get('notam', props)
                text = core.get('text', core.get('message', ''))
                text_upper = text.upper()

                is_tfr = any(kw in text_upper for kw in [
                    'TEMPORARY FLIGHT RESTRICTION', 'TFR',
                    'FLIGHT RESTRICTION', 'SPORTING EVENT',
                    'VIP MOVEMENT', 'HAZARDS',
                    '91.137', '91.138', '91.141', '91.143',
                ])
                if not is_tfr:
                    continue

                geometry = item.get('geometry', {})
                coords = []
                if geometry.get('type') == 'Polygon':
                    coords = geometry.get('coordinates', [[]])[0]
                elif geometry.get('type') == 'Point':
                    coords = [geometry.get('coordinates', [])]

                tfrs.append({
                    'notam_id': core.get('id', core.get('notamId', '')),
                    'type': _classify_tfr(text_upper),
                    'description': text[:500],
                    'effective': core.get('effectiveStart', ''),
                    'expires': core.get('effectiveEnd', ''),
                    'coords': coords,
                    'simulated': False,
                })
    except Exception:
        pass

    return tfrs


def _fetch_tfrs_via_scrape(route_bbox):
    """Scrape the FAA TFR list page for active TFRs."""
    tfrs = []
    try:
        r = requests.get(
            'https://tfr.faa.gov/tfr2/list.html',
            timeout=15,
            headers={
                'User-Agent': 'Mozilla/5.0 N499CP-FlightPlanner/3.0',
                'Accept': 'text/html',
            },
        )
        if r.status_code == 200:
            html = r.text
            # Parse table rows from the TFR list page
            table_rows = re.findall(
                r'<tr[^>]*class="[^"]*"[^>]*>(.*?)</tr>',
                html, re.DOTALL,
            )

            for row_html in table_rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
                if len(cells) < 5:
                    continue

                clean = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

                link_match = re.search(
                    r'href="([^"]*detail_[^"]*\.html)"', row_html
                )
                detail_url = ''
                if link_match:
                    href = link_match.group(1)
                    if href.startswith('/'):
                        detail_url = 'https://tfr.faa.gov' + href
                    elif href.startswith('http'):
                        detail_url = href
                    else:
                        detail_url = 'https://tfr.faa.gov/' + href

                date_str = clean[0] if len(clean) > 0 else ''
                notam_id = clean[1] if len(clean) > 1 else ''
                facility = clean[2] if len(clean) > 2 else ''
                state = clean[3] if len(clean) > 3 else ''
                tfr_type = clean[4] if len(clean) > 4 else ''

                if not notam_id:
                    continue

                tfrs.append({
                    'notam_id': notam_id,
                    'type': tfr_type or 'TFR',
                    'description': f'{tfr_type} - {facility}, {state} '
                                   f'(NOTAM {notam_id})',
                    'state': state,
                    'facility': facility,
                    'date': date_str,
                    'detail_url': detail_url,
                    'coords': [],
                    'simulated': False,
                })

    except Exception:
        pass

    return tfrs


def _classify_tfr(text_upper):
    if '91.141' in text_upper or 'VIP' in text_upper or 'PRESIDENT' in text_upper:
        return 'VIP/Presidential'
    if '91.137' in text_upper:
        if 'DISASTER' in text_upper or 'HAZARD' in text_upper:
            return 'Disaster/Hazard'
        return 'Special Security'
    if '91.138' in text_upper or 'NATIONAL DEFENSE' in text_upper:
        return 'National Defense'
    if '91.143' in text_upper or 'SPACE' in text_upper or 'LAUNCH' in text_upper:
        return 'Space Operations'
    if 'SPORTING' in text_upper or 'STADIUM' in text_upper:
        return 'Sporting Event'
    if 'FIRE' in text_upper or 'WILDFIRE' in text_upper:
        return 'Wildfire'
    return 'TFR'


# ---------------------------------------------------------------------------
# Route bounding box helper
# ---------------------------------------------------------------------------

def _compute_route_bbox(stations):
    lats, lons = [], []
    for s in stations:
        c = get_coords(s)
        if c:
            lats.append(c[0])
            lons.append(c[1])
    if not lats:
        return (32.0, -118.0, 34.0, -116.0)
    return (min(lats), min(lons), max(lats), max(lons))


# ---------------------------------------------------------------------------
# Main briefing function
# ---------------------------------------------------------------------------

def get_weather_briefing(data):
    try:
        dep = data.get('departure', '').upper()
        dest = data.get('destination', '').upper()
        wpts = [w.upper() for w in data.get('waypoints', []) if w.strip()]
        stations = [s for s in [dep] + wpts + [dest] if s]
        departure_time = data.get('departure_time', '')

        briefing = {
            'generated_at': _utc_now().strftime('%Y-%m-%d %H:%M UTC'),
            'departure_time': departure_time or 'Now',
            'route': ' -> '.join(stations),
            'metars': [],
            'tafs': [],
            'winds_aloft': None,
            'pireps': [],
            'airmets_sigmets': [],
            'notams': [],
            'tfrs': [],
        }

        # METARs and TAFs
        for s in stations:
            briefing['metars'].append(fetch_metar(s))
            briefing['tafs'].append(fetch_taf(s))

        # Winds aloft (estimated)
        dc = get_coords(dep)
        nc = get_coords(dest)
        if dc and nc:
            mlat = (dc[0] + nc[0]) / 2
            mlon = (dc[1] + nc[1]) / 2
            briefing['winds_aloft'] = simulate_winds(mlat, mlon)

        # Route bounding box for spatial queries
        route_bbox = _compute_route_bbox(stations)

        # PIREPs along the route
        briefing['pireps'] = fetch_pireps(stations)

        # AIRMETs / SIGMETs near the route
        briefing['airmets_sigmets'] = fetch_airmets_sigmets(route_bbox)

        # NOTAMs for each station
        for s in stations:
            briefing['notams'].extend(fetch_notams(s))

        # TFRs along the route
        briefing['tfrs'] = fetch_tfrs(route_bbox)

        return {'success': True, 'briefing': briefing}
    except Exception as e:
        return {'success': False, 'error': str(e)}
