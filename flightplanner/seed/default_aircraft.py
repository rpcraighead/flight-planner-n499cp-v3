import json
from flightplanner.database import get_db

# N499CP - Cessna 172S NAV III (exact data from v2)
N499CP = {
    'tail_number': 'N499CP',
    'type_model': 'Cessna 172S NAV III',
    'is_default': 1,
    'empty_weight': 1642,
    'empty_weight_moment': 62.6,
    'max_takeoff_weight': 2550,
    'usable_fuel': 53,
    'fuel_weight_per_gallon': 6.0,
    'fuel_arm': 48.0,
    'taxi_fuel': 1.4,
    'cg_forward_limit': 35.0,
    'cg_aft_limit': 47.3,
    'cruise_performance': {
        '4000': {'2500': [69, 115, 9.5], '2400': [61, 109, 8.5]},
        '6000': {'2600': [73, 119, 9.9], '2500': [65, 114, 9.0], '2400': [57, 108, 8.2]},
        '8000': {'2600': [68, 119, 9.4], '2500': [61, 112, 8.6], '2400': [54, 106, 7.8]},
        '10000': {'2600': [64, 117, 9.0], '2500': [57, 111, 8.2]},
    },
    'climb_performance': {
        '0': [0, 0.0, 0], '2000': [3, 0.8, 4], '4000': [6, 1.5, 8],
        '6000': [10, 2.2, 13], '8000': [14, 3.0, 19], '10000': [20, 3.9, 27],
    },
    'takeoff_distance': {
        '0': {'15': [940, 1630], '30': [1070, 1810]},
        '2000': {'15': [1150, 1960], '30': [1285, 2190]},
        '4000': {'15': [1390, 2390], '30': [1550, 2685]},
        '6000': {'15': [1680, 2950], '30': [1875, 3320]},
    },
    'landing_distance': {
        '0': {'15': [575, 1335], '30': [605, 1380]},
        '2000': {'15': [620, 1405], '30': [650, 1455]},
        '4000': {'15': [665, 1480], '30': [700, 1535]},
        '6000': {'15': [720, 1560], '30': [755, 1620]},
    },
    'v_speeds': {
        'Vx': 62, 'Vy': 74, 'Va': 105, 'Vfe': 110,
        'Vno': 129, 'Vne': 163, 'Vs0': 40, 'Vs1': 48,
        'Best Glide': 68,
    },
    'weight_limits': {
        'max_ramp_weight': 2558,
        'max_takeoff_weight': 2550,
        'max_landing_weight': 2550,
        'max_baggage_area1': 120,
        'max_baggage_area2': 50,
        'fuel_capacity_gal': 56,
        'usable_fuel_gal': 53,
        'pilot_arm': 40, 'front_pax_arm': 40,
        'rear_pax_arm': 73, 'baggage_arm': 95,
    },
    'notes': 'CAP San Diego Sr. Sq. 57 primary trainer',
}

# Cessna 182T Skylane (generic template - common CAP aircraft)
C182T_TEMPLATE = {
    'tail_number': 'N182XX',
    'type_model': 'Cessna 182T Skylane',
    'is_default': 0,
    'empty_weight': 1970,
    'empty_weight_moment': 81.4,
    'max_takeoff_weight': 3100,
    'usable_fuel': 87,
    'fuel_weight_per_gallon': 6.0,
    'fuel_arm': 46.0,
    'taxi_fuel': 1.6,
    'cg_forward_limit': 35.0,
    'cg_aft_limit': 47.2,
    'cruise_performance': {
        '4000': {'2400': [75, 145, 13.2], '2300': [68, 139, 12.0]},
        '6000': {'2400': [71, 143, 12.8], '2300': [64, 137, 11.6]},
        '8000': {'2400': [67, 141, 12.3], '2300': [60, 135, 11.2]},
        '10000': {'2400': [63, 138, 11.8], '2300': [56, 132, 10.7]},
    },
    'climb_performance': {
        '0': [0, 0.0, 0], '2000': [2, 0.9, 3], '4000': [5, 1.8, 7],
        '6000': [8, 2.8, 12], '8000': [12, 3.9, 18], '10000': [17, 5.2, 26],
    },
    'takeoff_distance': {
        '0': {'15': [795, 1465], '30': [905, 1620]},
        '2000': {'15': [970, 1760], '30': [1095, 1960]},
        '4000': {'15': [1185, 2140], '30': [1340, 2395]},
        '6000': {'15': [1455, 2655], '30': [1640, 2985]},
    },
    'landing_distance': {
        '0': {'15': [590, 1350], '30': [620, 1400]},
        '2000': {'15': [635, 1425], '30': [665, 1480]},
        '4000': {'15': [685, 1510], '30': [720, 1565]},
        '6000': {'15': [740, 1600], '30': [780, 1660]},
    },
    'v_speeds': {
        'Vx': 65, 'Vy': 80, 'Va': 110, 'Vfe': 110,
        'Vno': 140, 'Vne': 175, 'Vs0': 40, 'Vs1': 50,
        'Best Glide': 72,
    },
    'weight_limits': {
        'max_ramp_weight': 3110,
        'max_takeoff_weight': 3100,
        'max_landing_weight': 3100,
        'max_baggage_area1': 120,
        'max_baggage_area2': 80,
        'fuel_capacity_gal': 92,
        'usable_fuel_gal': 87,
        'pilot_arm': 37, 'front_pax_arm': 37,
        'rear_pax_arm': 73, 'baggage_arm': 95,
    },
    'notes': 'Template - update tail number and weights for your specific aircraft',
}

# Cessna 206H Stationair (common CAP mission aircraft)
C206H_TEMPLATE = {
    'tail_number': 'N206XX',
    'type_model': 'Cessna 206H Stationair',
    'is_default': 0,
    'empty_weight': 2175,
    'empty_weight_moment': 92.0,
    'max_takeoff_weight': 3600,
    'usable_fuel': 87,
    'fuel_weight_per_gallon': 6.0,
    'fuel_arm': 46.0,
    'taxi_fuel': 1.8,
    'cg_forward_limit': 35.0,
    'cg_aft_limit': 47.3,
    'cruise_performance': {
        '4000': {'2400': [75, 148, 14.5], '2300': [67, 142, 13.2]},
        '6000': {'2400': [71, 146, 14.0], '2300': [63, 140, 12.8]},
        '8000': {'2400': [67, 143, 13.5], '2300': [60, 137, 12.3]},
        '10000': {'2400': [62, 140, 13.0], '2300': [56, 134, 11.8]},
    },
    'climb_performance': {
        '0': [0, 0.0, 0], '2000': [3, 1.0, 3], '4000': [6, 2.0, 7],
        '6000': [10, 3.1, 12], '8000': [15, 4.4, 18], '10000': [22, 6.0, 26],
    },
    'takeoff_distance': {
        '0': {'15': [900, 1600], '30': [1020, 1790]},
        '2000': {'15': [1095, 1940], '30': [1240, 2170]},
        '4000': {'15': [1340, 2370], '30': [1515, 2660]},
        '6000': {'15': [1655, 2945], '30': [1870, 3310]},
    },
    'landing_distance': {
        '0': {'15': [635, 1395], '30': [670, 1445]},
        '2000': {'15': [685, 1475], '30': [720, 1530]},
        '4000': {'15': [740, 1565], '30': [780, 1620]},
        '6000': {'15': [805, 1660], '30': [845, 1720]},
    },
    'v_speeds': {
        'Vx': 66, 'Vy': 84, 'Va': 115, 'Vfe': 110,
        'Vno': 143, 'Vne': 180, 'Vs0': 47, 'Vs1': 56,
        'Best Glide': 76,
    },
    'weight_limits': {
        'max_ramp_weight': 3612,
        'max_takeoff_weight': 3600,
        'max_landing_weight': 3600,
        'max_baggage_area1': 150,
        'max_baggage_area2': 100,
        'fuel_capacity_gal': 92,
        'usable_fuel_gal': 87,
        'pilot_arm': 37, 'front_pax_arm': 37,
        'rear_pax_arm': 73, 'baggage_arm': 95,
    },
    'notes': 'Template - update tail number and weights for your specific aircraft',
}

# GA8 Airvan (common CAP mission aircraft for search and rescue)
GA8_TEMPLATE = {
    'tail_number': 'NGA8XX',
    'type_model': 'GippsAero GA8 Airvan',
    'is_default': 0,
    'empty_weight': 2183,
    'empty_weight_moment': 93.0,
    'max_takeoff_weight': 4000,
    'usable_fuel': 100,
    'fuel_weight_per_gallon': 6.0,
    'fuel_arm': 48.0,
    'taxi_fuel': 2.0,
    'cg_forward_limit': 72.0,
    'cg_aft_limit': 86.4,
    'cruise_performance': {
        '4000': {'2500': [72, 120, 16.0], '2400': [65, 115, 14.5]},
        '6000': {'2500': [68, 118, 15.5], '2400': [61, 113, 14.0]},
        '8000': {'2500': [64, 115, 15.0], '2400': [57, 110, 13.5]},
        '10000': {'2500': [60, 112, 14.5], '2400': [54, 107, 13.0]},
    },
    'climb_performance': {
        '0': [0, 0.0, 0], '2000': [3, 1.2, 4], '4000': [7, 2.5, 9],
        '6000': [12, 3.9, 15], '8000': [18, 5.5, 22], '10000': [26, 7.4, 31],
    },
    'takeoff_distance': {
        '0': {'15': [1050, 1750], '30': [1190, 1960]},
        '2000': {'15': [1280, 2120], '30': [1450, 2375]},
        '4000': {'15': [1565, 2590], '30': [1770, 2905]},
        '6000': {'15': [1930, 3220], '30': [2180, 3615]},
    },
    'landing_distance': {
        '0': {'15': [680, 1450], '30': [715, 1505]},
        '2000': {'15': [735, 1535], '30': [775, 1595]},
        '4000': {'15': [795, 1630], '30': [840, 1690]},
        '6000': {'15': [865, 1730], '30': [910, 1795]},
    },
    'v_speeds': {
        'Vx': 72, 'Vy': 87, 'Va': 105, 'Vfe': 91,
        'Vno': 130, 'Vne': 163, 'Vs0': 52, 'Vs1': 61,
        'Best Glide': 80,
    },
    'weight_limits': {
        'max_ramp_weight': 4010,
        'max_takeoff_weight': 4000,
        'max_landing_weight': 4000,
        'max_baggage_area1': 200,
        'max_baggage_area2': 0,
        'fuel_capacity_gal': 106,
        'usable_fuel_gal': 100,
        'pilot_arm': 80, 'front_pax_arm': 80,
        'rear_pax_arm': 117, 'baggage_arm': 145,
    },
    'notes': 'Template - update tail number and weights for your specific aircraft',
}

DEFAULT_AIRCRAFT = [N499CP, C182T_TEMPLATE, C206H_TEMPLATE, GA8_TEMPLATE]


def seed_aircraft():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM aircraft')
    if c.fetchone()[0] > 0:
        conn.close()
        return

    for ac in DEFAULT_AIRCRAFT:
        c.execute('''INSERT INTO aircraft
            (tail_number, type_model, is_default, empty_weight, empty_weight_moment,
             max_takeoff_weight, usable_fuel, fuel_weight_per_gallon, fuel_arm, taxi_fuel,
             cg_forward_limit, cg_aft_limit, cruise_performance, climb_performance,
             takeoff_distance, landing_distance, v_speeds, weight_limits, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (ac['tail_number'], ac['type_model'], ac['is_default'],
             ac['empty_weight'], ac['empty_weight_moment'],
             ac['max_takeoff_weight'], ac['usable_fuel'],
             ac['fuel_weight_per_gallon'], ac['fuel_arm'], ac['taxi_fuel'],
             ac['cg_forward_limit'], ac['cg_aft_limit'],
             json.dumps(ac['cruise_performance']),
             json.dumps(ac['climb_performance']),
             json.dumps(ac['takeoff_distance']),
             json.dumps(ac['landing_distance']),
             json.dumps(ac.get('v_speeds', {})),
             json.dumps(ac.get('weight_limits', {})),
             ac.get('notes', '')))

    conn.commit()
    conn.close()
