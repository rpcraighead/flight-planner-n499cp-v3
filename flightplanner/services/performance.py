from flightplanner.models.aircraft import get_aircraft_for_calc


def get_cruise(aircraft, altitude, rpm):
    """Get cruise performance for given altitude and RPM.
    Aircraft cruise_performance keys are strings."""
    cd = aircraft['cruise_performance']
    alts = sorted(int(k) for k in cd.keys())
    a = min(alts, key=lambda x: abs(x - altitude))
    a_key = str(a)
    if a_key not in cd:
        return {'power_percent': 65, 'true_airspeed': 110, 'fuel_flow_gph': 8.5}
    rpms = sorted(int(k) for k in cd[a_key].keys())
    r = min(rpms, key=lambda x: abs(x - rpm))
    r_key = str(r)
    if r_key not in cd[a_key]:
        return {'power_percent': 65, 'true_airspeed': 110, 'fuel_flow_gph': 8.5}
    pwr, tas, gph = cd[a_key][r_key]
    return {'power_percent': pwr, 'true_airspeed': tas, 'fuel_flow_gph': gph}


def get_climb(aircraft, from_alt, to_alt):
    """Get climb performance between two altitudes.
    Aircraft climb_performance keys are strings."""
    cd = aircraft['climb_performance']
    alts = sorted(int(k) for k in cd.keys())
    f = min(alts, key=lambda x: abs(x - from_alt))
    t = min(alts, key=lambda x: abs(x - to_alt))
    fd = cd[str(f)]
    td = cd[str(t)]
    return {
        'time_minutes': max(0, td[0] - fd[0]),
        'fuel_gallons': max(0, td[1] - fd[1]),
        'distance_nm': max(0, td[2] - fd[2]),
    }


def calc_takeoff(weight, altitude, temp, headwind=0, aircraft_id=None):
    """Calculate takeoff distances."""
    aircraft = get_aircraft_for_calc(aircraft_id)
    if not aircraft:
        return {'error': 'No aircraft found'}
    tbl = aircraft['takeoff_distance']
    alts = sorted(int(k) for k in tbl.keys())
    a = min([x for x in alts if x >= altitude], default=alts[-1])
    a_key = str(a)
    temps = sorted(int(k) for k in tbl[a_key].keys())
    t = min([x for x in temps if x >= temp], default=temps[-1])
    t_key = str(t)
    gr, tot = tbl[a_key][t_key]
    wf = 1.0 - (headwind / 9 * 0.10) if headwind > 0 else 1.0
    return {'ground_roll': int(gr * wf), 'total_over_50ft': int(tot * wf)}


def calc_landing(altitude, temp, headwind=0, aircraft_id=None):
    """Calculate landing distances."""
    aircraft = get_aircraft_for_calc(aircraft_id)
    if not aircraft:
        return {'error': 'No aircraft found'}
    tbl = aircraft['landing_distance']
    alts = sorted(int(k) for k in tbl.keys())
    a = min([x for x in alts if x >= altitude], default=alts[-1])
    a_key = str(a)
    temps = sorted(int(k) for k in tbl[a_key].keys())
    t = min([x for x in temps if x >= temp], default=temps[-1])
    t_key = str(t)
    gr, tot = tbl[a_key][t_key]
    wf = 1.0 - (headwind / 9 * 0.10) if headwind > 0 else 1.0
    return {'ground_roll': int(gr * wf), 'total_over_50ft': int(tot * wf)}
