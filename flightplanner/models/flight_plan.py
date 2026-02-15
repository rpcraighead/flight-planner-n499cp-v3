import json
from flightplanner.database import get_db


def list_flight_plans():
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT fp.id, fp.name, fp.departure_icao, fp.destination_icao,
                        fp.cruise_altitude, fp.aircraft_id, a.tail_number,
                        fp.created_at, fp.updated_at
                 FROM flight_plans fp
                 LEFT JOIN aircraft a ON fp.aircraft_id = a.id
                 ORDER BY fp.updated_at DESC''')
    plans = [dict(r) for r in c.fetchall()]
    conn.close()
    return plans


def save_flight_plan(data):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO flight_plans
        (name, aircraft_id, departure_icao, destination_icao, cruise_altitude,
         cruise_rpm, pilot_weight, front_pax_weight, rear_pax_weight,
         baggage_weight, fuel_gallons, route_data, weather_data, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (data['name'], data['aircraft_id'],
         data['departure_icao'], data['destination_icao'],
         data.get('cruise_altitude', 6000), data.get('cruise_rpm', 2400),
         data.get('pilot_weight'), data.get('front_pax_weight'),
         data.get('rear_pax_weight'), data.get('baggage_weight'),
         data.get('fuel_gallons'),
         json.dumps(data.get('route_data')) if data.get('route_data') else None,
         json.dumps(data.get('weather_data')) if data.get('weather_data') else None,
         data.get('notes', '')))
    plan_id = c.lastrowid

    waypoints = data.get('waypoints', [])
    for i, wp in enumerate(waypoints):
        c.execute('INSERT INTO flight_plan_waypoints (flight_plan_id, sequence, identifier) VALUES (?,?,?)',
                  (plan_id, i, wp))

    conn.commit()
    conn.close()
    return plan_id


def load_flight_plan(plan_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM flight_plans WHERE id=?', (plan_id,))
    r = c.fetchone()
    if not r:
        conn.close()
        return None
    plan = dict(r)
    if plan.get('route_data'):
        plan['route_data'] = json.loads(plan['route_data'])
    if plan.get('weather_data'):
        plan['weather_data'] = json.loads(plan['weather_data'])

    c.execute('SELECT identifier FROM flight_plan_waypoints WHERE flight_plan_id=? ORDER BY sequence', (plan_id,))
    plan['waypoints'] = [row['identifier'] for row in c.fetchall()]

    conn.close()
    return plan


def update_flight_plan(plan_id, data):
    conn = get_db()
    c = conn.cursor()
    fields = []
    values = []
    for key in ['name', 'aircraft_id', 'departure_icao', 'destination_icao',
                'cruise_altitude', 'cruise_rpm', 'pilot_weight', 'front_pax_weight',
                'rear_pax_weight', 'baggage_weight', 'fuel_gallons', 'notes']:
        if key in data:
            fields.append(f'{key}=?')
            values.append(data[key])
    for key in ['route_data', 'weather_data']:
        if key in data:
            fields.append(f'{key}=?')
            values.append(json.dumps(data[key]) if data[key] else None)

    if fields:
        fields.append("updated_at=datetime('now')")
        values.append(plan_id)
        c.execute(f'UPDATE flight_plans SET {", ".join(fields)} WHERE id=?', values)

    if 'waypoints' in data:
        c.execute('DELETE FROM flight_plan_waypoints WHERE flight_plan_id=?', (plan_id,))
        for i, wp in enumerate(data['waypoints']):
            c.execute('INSERT INTO flight_plan_waypoints (flight_plan_id, sequence, identifier) VALUES (?,?,?)',
                      (plan_id, i, wp))

    conn.commit()
    conn.close()


def delete_flight_plan(plan_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM flight_plan_waypoints WHERE flight_plan_id=?', (plan_id,))
    c.execute('DELETE FROM flight_plans WHERE id=?', (plan_id,))
    conn.commit()
    conn.close()
