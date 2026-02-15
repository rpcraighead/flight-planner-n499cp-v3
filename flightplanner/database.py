import sqlite3
from config import DATABASE_PATH


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS airports (
        icao TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT,
        state TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        elevation INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS runways (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        airport_icao TEXT NOT NULL,
        runway_id TEXT NOT NULL,
        length INTEGER DEFAULT 0,
        surface TEXT,
        FOREIGN KEY (airport_icao) REFERENCES airports(icao)
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_runways_airport ON runways(airport_icao)')

    c.execute('''CREATE TABLE IF NOT EXISTS navaids (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS aircraft (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tail_number TEXT UNIQUE NOT NULL,
        type_model TEXT NOT NULL,
        is_default INTEGER DEFAULT 0,
        empty_weight REAL NOT NULL,
        empty_weight_moment REAL NOT NULL,
        max_takeoff_weight REAL NOT NULL,
        usable_fuel REAL NOT NULL,
        fuel_weight_per_gallon REAL DEFAULT 6.0,
        fuel_arm REAL NOT NULL,
        taxi_fuel REAL DEFAULT 1.4,
        cg_forward_limit REAL NOT NULL,
        cg_aft_limit REAL NOT NULL,
        cruise_performance TEXT NOT NULL,
        climb_performance TEXT NOT NULL,
        takeoff_distance TEXT NOT NULL,
        landing_distance TEXT NOT NULL,
        v_speeds TEXT,
        weight_limits TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS flight_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        aircraft_id INTEGER NOT NULL,
        departure_icao TEXT NOT NULL,
        destination_icao TEXT NOT NULL,
        cruise_altitude INTEGER DEFAULT 6000,
        cruise_rpm INTEGER DEFAULT 2400,
        pilot_weight REAL,
        front_pax_weight REAL,
        rear_pax_weight REAL,
        baggage_weight REAL,
        fuel_gallons REAL,
        route_data TEXT,
        weather_data TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (aircraft_id) REFERENCES aircraft(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS flight_plan_waypoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_plan_id INTEGER NOT NULL,
        sequence INTEGER NOT NULL,
        identifier TEXT NOT NULL,
        FOREIGN KEY (flight_plan_id) REFERENCES flight_plans(id) ON DELETE CASCADE
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_fp_waypoints ON flight_plan_waypoints(flight_plan_id, sequence)')

    conn.commit()
    conn.close()
