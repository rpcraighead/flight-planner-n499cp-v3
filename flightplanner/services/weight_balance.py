from flightplanner.models.aircraft import get_aircraft_for_calc


def calc_weight_balance(data):
    """Calculate weight and balance. Uses aircraft-specific arm values."""
    aircraft_id = data.get('aircraft_id')
    ac = get_aircraft_for_calc(aircraft_id)
    if not ac:
        return {'error': 'No aircraft found'}

    wl = ac.get('weight_limits', {})

    ew = float(data.get('empty_weight', ac['empty_weight']))
    em = float(data.get('empty_moment', ac['empty_weight_moment']))
    pilot = float(data.get('pilot_weight', 0))
    front_pax = float(data.get('front_passenger_weight', 0))
    rear_pax = float(data.get('rear_passenger_weight', 0))
    baggage = float(data.get('baggage_weight', 0))
    fuel_gal = float(data.get('fuel_gallons', 0))

    pilot_arm = wl.get('pilot_arm', 40)
    front_pax_arm = wl.get('front_pax_arm', 40)
    rear_pax_arm = wl.get('rear_pax_arm', 73)
    baggage_arm = wl.get('baggage_arm', 95)

    fw = fuel_gal * ac['fuel_weight_per_gallon']
    tw = ew + pilot + front_pax + rear_pax + baggage + fw
    tm = (em * 1000
          + pilot * pilot_arm
          + front_pax * front_pax_arm
          + rear_pax * rear_pax_arm
          + baggage * baggage_arm
          + fw * ac['fuel_arm'])
    cg = tm / tw if tw > 0 else 0

    return {
        'total_weight': round(tw, 1),
        'max_weight': ac['max_takeoff_weight'],
        'weight_margin': round(ac['max_takeoff_weight'] - tw, 1),
        'cg': round(cg, 2),
        'cg_forward_limit': ac['cg_forward_limit'],
        'cg_aft_limit': ac['cg_aft_limit'],
        'within_weight_limits': tw <= ac['max_takeoff_weight'],
        'within_cg_limits': ac['cg_forward_limit'] <= cg <= ac['cg_aft_limit'],
        'within_all_limits': (tw <= ac['max_takeoff_weight']
                              and ac['cg_forward_limit'] <= cg <= ac['cg_aft_limit']),
        'moment_1000': round(tm / 1000, 1),
    }
