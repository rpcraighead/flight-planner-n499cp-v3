from flask import Blueprint, jsonify, request
from flightplanner.services.performance import calc_takeoff, calc_landing
from flightplanner.services.weight_balance import calc_weight_balance

performance_bp = Blueprint('performance', __name__)


@performance_bp.route('/takeoff', methods=['POST'])
def takeoff():
    d = request.json
    aircraft_id = d.get('aircraft_id')
    result = calc_takeoff(
        int(d.get('weight', 2550)),
        int(d.get('pressure_altitude', 0)),
        int(d.get('temperature', 15)),
        int(d.get('headwind', 0)),
        aircraft_id=aircraft_id
    )
    return jsonify(result)


@performance_bp.route('/landing', methods=['POST'])
def landing():
    d = request.json
    aircraft_id = d.get('aircraft_id')
    result = calc_landing(
        int(d.get('pressure_altitude', 0)),
        int(d.get('temperature', 15)),
        int(d.get('headwind', 0)),
        aircraft_id=aircraft_id
    )
    return jsonify(result)


@performance_bp.route('/weight-balance', methods=['POST'])
def weight_balance():
    d = request.json
    result = calc_weight_balance(d)
    return jsonify(result)
