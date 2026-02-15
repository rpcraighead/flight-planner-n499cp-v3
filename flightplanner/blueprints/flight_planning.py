from flask import Blueprint, jsonify, request
from flightplanner.services.route import calculate_route
from flightplanner.models.flight_plan import (
    list_flight_plans, save_flight_plan, load_flight_plan,
    update_flight_plan, delete_flight_plan
)

flight_planning_bp = Blueprint('flight_planning', __name__)


@flight_planning_bp.route('/calculate', methods=['POST'])
def calc_route():
    data = request.json
    result = calculate_route(data)
    return jsonify(result)


@flight_planning_bp.route('', methods=['GET'])
def list_plans():
    plans = list_flight_plans()
    return jsonify({'success': True, 'plans': plans})


@flight_planning_bp.route('', methods=['POST'])
def save_plan():
    data = request.json
    plan_id = save_flight_plan(data)
    return jsonify({'success': True, 'id': plan_id})


@flight_planning_bp.route('/<int:plan_id>', methods=['GET'])
def load_plan(plan_id):
    plan = load_flight_plan(plan_id)
    if not plan:
        return jsonify({'success': False, 'error': 'Plan not found'})
    return jsonify({'success': True, 'plan': plan})


@flight_planning_bp.route('/<int:plan_id>', methods=['PUT'])
def update_plan(plan_id):
    data = request.json
    update_flight_plan(plan_id, data)
    return jsonify({'success': True})


@flight_planning_bp.route('/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    delete_flight_plan(plan_id)
    return jsonify({'success': True})
