import threading
from flask import Blueprint, jsonify
from flightplanner.services.data_import import download_database, update_status
from flightplanner.database import get_db
from config import TILE_SOURCES

data_bp = Blueprint('data', __name__)


@data_bp.route('/update', methods=['POST'])
def trigger_update():
    if update_status['in_progress']:
        return jsonify({'success': False, 'message': 'Update already in progress'})
    threading.Thread(target=download_database, daemon=True).start()
    return jsonify({'success': True})


@data_bp.route('/status')
def get_status():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM airports')
    cnt = c.fetchone()[0]
    conn.close()
    return jsonify({
        'in_progress': update_status['in_progress'],
        'message': update_status['message'],
        'progress': update_status['progress'],
        'airports': cnt,
    })


@data_bp.route('/tile-sources')
def tile_sources():
    return jsonify(TILE_SOURCES)
