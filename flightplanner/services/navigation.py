import math


def gc_dist(lat1, lon1, lat2, lon2):
    """Great circle distance in nautical miles (haversine formula)."""
    R = 3440.065
    la1, la2 = math.radians(lat1), math.radians(lat2)
    dla, dlo = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing(lat1, lon1, lat2, lon2):
    """Initial true course in degrees."""
    la1, la2 = math.radians(lat1), math.radians(lat2)
    dlo = math.radians(lon2 - lon1)
    x = math.sin(dlo) * math.cos(la2)
    y = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlo)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def wind_corr(tc, tas, wd, ws):
    """Wind correction angle and ground speed."""
    if ws == 0:
        return 0, tas
    swc = (ws / tas) * math.sin(math.radians(wd - tc))
    swc = max(-1, min(1, swc))
    wca = math.degrees(math.asin(swc))
    gs = tas * math.cos(math.asin(swc)) + ws * math.cos(math.radians(wd - tc))
    return round(wca, 1), max(round(gs, 1), 0)
