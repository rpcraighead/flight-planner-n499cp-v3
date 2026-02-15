import json
from flightplanner.database import get_db

JSON_FIELDS = ['cruise_performance', 'climb_performance', 'takeoff_distance',
               'landing_distance', 'v_speeds', 'weight_limits']


def _row_to_dict(row):
    d = dict(row)
    for field in JSON_FIELDS:
        if d.get(field):
            d[field] = json.loads(d[field])
    return d


def list_aircraft():
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT id, tail_number, type_model, is_default, empty_weight,
                        max_takeoff_weight, usable_fuel
                 FROM aircraft ORDER BY is_default DESC, tail_number''')
    results = [dict(r) for r in c.fetchall()]
    conn.close()
    return results


def get_aircraft(aircraft_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM aircraft WHERE id=?', (aircraft_id,))
    r = c.fetchone()
    conn.close()
    if r:
        return _row_to_dict(r)
    return None


def get_default_aircraft():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM aircraft WHERE is_default=1 LIMIT 1')
    r = c.fetchone()
    if not r:
        c.execute('SELECT * FROM aircraft LIMIT 1')
        r = c.fetchone()
    conn.close()
    if r:
        return _row_to_dict(r)
    return None


def get_aircraft_for_calc(aircraft_id=None):
    if aircraft_id:
        return get_aircraft(aircraft_id)
    return get_default_aircraft()


def create_aircraft(data):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO aircraft
        (tail_number, type_model, is_default, empty_weight, empty_weight_moment,
         max_takeoff_weight, usable_fuel, fuel_weight_per_gallon, fuel_arm, taxi_fuel,
         cg_forward_limit, cg_aft_limit, cruise_performance, climb_performance,
         takeoff_distance, landing_distance, v_speeds, weight_limits, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (data['tail_number'], data['type_model'], data.get('is_default', 0),
         data['empty_weight'], data['empty_weight_moment'],
         data['max_takeoff_weight'], data['usable_fuel'],
         data.get('fuel_weight_per_gallon', 6.0), data['fuel_arm'],
         data.get('taxi_fuel', 1.4),
         data['cg_forward_limit'], data['cg_aft_limit'],
         json.dumps(data['cruise_performance']),
         json.dumps(data['climb_performance']),
         json.dumps(data['takeoff_distance']),
         json.dumps(data['landing_distance']),
         json.dumps(data.get('v_speeds', {})),
         json.dumps(data.get('weight_limits', {})),
         data.get('notes', '')))
    ac_id = c.lastrowid
    conn.commit()
    conn.close()
    return ac_id


def update_aircraft(aircraft_id, data):
    conn = get_db()
    c = conn.cursor()
    fields = []
    values = []
    for key in ['tail_number', 'type_model', 'is_default', 'empty_weight',
                'empty_weight_moment', 'max_takeoff_weight', 'usable_fuel',
                'fuel_weight_per_gallon', 'fuel_arm', 'taxi_fuel',
                'cg_forward_limit', 'cg_aft_limit', 'notes']:
        if key in data:
            fields.append(f'{key}=?')
            values.append(data[key])
    for key in JSON_FIELDS:
        if key in data:
            fields.append(f'{key}=?')
            values.append(json.dumps(data[key]))
    if fields:
        fields.append("updated_at=datetime('now')")
        values.append(aircraft_id)
        c.execute(f'UPDATE aircraft SET {", ".join(fields)} WHERE id=?', values)
        conn.commit()
    conn.close()


def delete_aircraft(aircraft_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM aircraft WHERE id=?', (aircraft_id,))
    conn.commit()
    conn.close()
