from flightplanner.models.airport import get_coords
from flightplanner.models.aircraft import get_aircraft_for_calc
from flightplanner.services.navigation import gc_dist, bearing, wind_corr
from flightplanner.services.performance import get_cruise, get_climb
from flightplanner.services.weather import simulate_winds


def calculate_route(data):
    dep = data.get('departure', '').upper()
    dest = data.get('destination', '').upper()
    wpts = [w.upper() for w in data.get('waypoints', []) if w.strip()]
    alt = int(data.get('cruise_altitude', 6000))
    rpm = int(data.get('rpm', 2400))
    aircraft_id = data.get('aircraft_id')

    ac = get_aircraft_for_calc(aircraft_id)
    if not ac:
        return {'success': False, 'error': 'No aircraft configured'}

    pts = [dep] + wpts + [dest]
    coords = []
    for p in pts:
        c = get_coords(p)
        if not c:
            return {'success': False, 'error': f'Not found: {p}'}
        coords.append({
            'identifier': p,
            'latitude': c[0], 'longitude': c[1],
            'type': c[2], 'data': c[3],
        })

    cruise = get_cruise(ac, alt, rpm)

    mid = coords[len(coords) // 2]
    winds = simulate_winds(mid['latitude'], mid['longitude'])

    wdir, wspd = 0, 0
    if winds and 'levels' in winds:
        lvls = sorted(winds['levels'].keys())
        nrst = min(lvls, key=lambda x: abs(x - alt))
        wdir = winds['levels'][nrst]['direction']
        wspd = winds['levels'][nrst]['speed']

    segs = []
    tot_dist, tot_time, tot_fuel = 0, 0, 0

    for i in range(len(coords) - 1):
        fr, to = coords[i], coords[i + 1]
        dist = gc_dist(fr['latitude'], fr['longitude'], to['latitude'], to['longitude'])
        tc = bearing(fr['latitude'], fr['longitude'], to['latitude'], to['longitude'])
        wca, gs = wind_corr(tc, cruise['true_airspeed'], wdir, wspd)
        mh = (tc + wca) % 360
        lt = (dist / gs) * 60 if gs > 0 else 0
        lf = (lt / 60) * cruise['fuel_flow_gph']

        segs.append({
            'from': fr['identifier'], 'to': to['identifier'],
            'distance_nm': round(dist, 1), 'true_course': round(tc, 0),
            'wind_correction': round(wca, 0), 'magnetic_heading': round(mh, 0),
            'ground_speed': round(gs, 0), 'time_minutes': round(lt, 0),
            'fuel_gallons': round(lf, 1),
        })
        tot_dist += dist
        tot_time += lt
        tot_fuel += lf

    dep_elev = coords[0]['data'].get('elevation', 0) if coords[0]['data'] else 0
    climb = get_climb(ac, dep_elev, alt)
    taxi = ac['taxi_fuel']
    reserve = 0.75 * cruise['fuel_flow_gph']

    return {
        'success': True,
        'aircraft': {'id': ac['id'], 'tail_number': ac['tail_number'], 'type_model': ac['type_model']},
        'route_points': coords,
        'segments': segs,
        'winds_aloft': {'altitude': alt, 'direction': wdir, 'speed': wspd, 'source': 'estimated'},
        'cruise': {
            'altitude': alt, 'rpm': rpm,
            'true_airspeed': cruise['true_airspeed'],
            'fuel_flow_gph': cruise['fuel_flow_gph'],
        },
        'climb': climb,
        'totals': {
            'distance_nm': round(tot_dist, 1),
            'time_minutes': round(tot_time + climb['time_minutes'], 0),
            'taxi_fuel': taxi,
            'climb_fuel': climb['fuel_gallons'],
            'cruise_fuel': round(tot_fuel, 1),
            'reserve_fuel': round(reserve, 1),
            'total_fuel': round(taxi + climb['fuel_gallons'] + tot_fuel + reserve, 1),
        },
    }
