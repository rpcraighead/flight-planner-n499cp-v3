from flask import Blueprint, jsonify, request
from flightplanner.models.aircraft import (
    list_aircraft, get_aircraft, create_aircraft,
    update_aircraft, delete_aircraft
)

aircraft_bp = Blueprint('aircraft', __name__)


@aircraft_bp.route('', methods=['GET'])
def list_all():
    return jsonify({'success': True, 'aircraft': list_aircraft()})


@aircraft_bp.route('/<int:aircraft_id>', methods=['GET'])
def get_one(aircraft_id):
    ac = get_aircraft(aircraft_id)
    if not ac:
        return jsonify({'success': False, 'error': 'Aircraft not found'})
    return jsonify({'success': True, 'aircraft': ac})


@aircraft_bp.route('', methods=['POST'])
def create():
    data = request.json
    ac_id = create_aircraft(data)
    return jsonify({'success': True, 'id': ac_id})


@aircraft_bp.route('/<int:aircraft_id>', methods=['PUT'])
def update(aircraft_id):
    data = request.json
    update_aircraft(aircraft_id, data)
    return jsonify({'success': True})


@aircraft_bp.route('/<int:aircraft_id>', methods=['DELETE'])
def delete(aircraft_id):
    delete_aircraft(aircraft_id)
    return jsonify({'success': True})
