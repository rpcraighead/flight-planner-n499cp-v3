from flightplanner.database import get_db


def get_airport(icao):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT icao, name, city, state, latitude, longitude, elevation FROM airports WHERE icao=?', (icao,))
    r = c.fetchone()
    conn.close()
    if r:
        return dict(r)
    return None


def get_runways(icao):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT runway_id, length, surface FROM runways WHERE airport_icao=? ORDER BY length DESC', (icao,))
    rws = [dict(r) for r in c.fetchall()]
    conn.close()
    return rws


def get_navaid(nid):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, name, type, latitude, longitude FROM navaids WHERE id=?', (nid,))
    r = c.fetchone()
    conn.close()
    if r:
        return dict(r)
    return None


def get_coords(ident):
    a = get_airport(ident)
    if a:
        return (a['latitude'], a['longitude'], 'airport', a)
    n = get_navaid(ident)
    if n:
        return (n['latitude'], n['longitude'], 'navaid', n)
    return None


def search_airports(query, limit=15):
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT icao, name, city, state, latitude, longitude, elevation
                 FROM airports
                 WHERE icao LIKE ? OR name LIKE ? OR city LIKE ?
                 ORDER BY CASE WHEN icao = ? THEN 0
                               WHEN icao LIKE ? THEN 1
                               ELSE 2 END
                 LIMIT ?''',
              (f'{query}%', f'%{query}%', f'%{query}%', query, f'{query}%', limit))
    results = [dict(r) for r in c.fetchall()]
    conn.close()
    return results
