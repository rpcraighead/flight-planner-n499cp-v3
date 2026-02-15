from flask import Blueprint, jsonify, request
from flightplanner.services.weather import get_weather_briefing

weather_bp = Blueprint('weather', __name__)


@weather_bp.route('/briefing', methods=['POST'])
def briefing():
    data = request.json
    result = get_weather_briefing(data)
    return jsonify(result)
