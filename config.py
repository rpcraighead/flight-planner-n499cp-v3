import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(BASE_DIR, 'aviation_data.db')

AVIATION_WEATHER_BASE = 'https://aviationweather.gov/api/data'

TILE_SOURCES = {
    'vfr': 'https://tiles.arcgis.com/tiles/ssFJjBXIUyZDrSYZ/arcgis/rest/services/VFR_Sectional/MapServer/tile/{z}/{y}/{x}',
    'ifr_low': 'https://tiles.arcgis.com/tiles/ssFJjBXIUyZDrSYZ/arcgis/rest/services/IFR_Low/MapServer/tile/{z}/{y}/{x}',
    'ifr_high': 'https://tiles.arcgis.com/tiles/ssFJjBXIUyZDrSYZ/arcgis/rest/services/IFR_High/MapServer/tile/{z}/{y}/{x}',
}

OURAIRPORTS_URLS = {
    'airports': 'https://davidmegginson.github.io/ourairports-data/airports.csv',
    'runways': 'https://davidmegginson.github.io/ourairports-data/runways.csv',
    'navaids': 'https://davidmegginson.github.io/ourairports-data/navaids.csv',
}

HTTP_HEADERS = {
    'User-Agent': 'N499CP-FlightPlanner/3.0',
    'Referer': 'https://www.faa.gov/',
}

# FAA NOTAM API credentials (free registration at https://api.faa.gov/s/)
# Set these to enable real NOTAM and TFR data.
# Without these, the app falls back to scraping tfr.faa.gov for TFRs
# and providing NOTAM links only.
FAA_NOTAM_API_URL = 'https://external-api.faa.gov/notamapi/v1/notams'
FAA_NOTAM_CLIENT_ID = os.environ.get('FAA_NOTAM_CLIENT_ID', '')
FAA_NOTAM_CLIENT_SECRET = os.environ.get('FAA_NOTAM_CLIENT_SECRET', '')
