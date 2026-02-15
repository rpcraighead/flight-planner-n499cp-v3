from flask import Blueprint, jsonify, request
from flightplanner.models.airport import get_airport, get_runways, search_airports

airports_bp = Blueprint('airports', __name__)


@airports_bp.route('/<icao>')
def airport_info(icao):
    a = get_airport(icao.upper())
    if not a:
        return jsonify({'success': False, 'error': f'Airport {icao} not found'})
    return jsonify({'success': True, 'airport': a, 'runways': get_runways(icao.upper())})


@airports_bp.route('/search')
def airport_search():
    q = request.args.get('q', '').strip().upper()
    if len(q) < 2:
        return jsonify({'results': []})
    return jsonify({'results': search_airports(q)})
