from flask import Flask
from flightplanner.database import init_db
from flightplanner.seed.default_aircraft import seed_aircraft


def create_app():
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    init_db()
    seed_aircraft()

    from flightplanner.blueprints.main import main_bp
    from flightplanner.blueprints.airports import airports_bp
    from flightplanner.blueprints.flight_planning import flight_planning_bp
    from flightplanner.blueprints.weather import weather_bp
    from flightplanner.blueprints.performance import performance_bp
    from flightplanner.blueprints.aircraft import aircraft_bp
    from flightplanner.blueprints.export import export_bp
    from flightplanner.blueprints.data import data_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(airports_bp, url_prefix='/api/airports')
    app.register_blueprint(flight_planning_bp, url_prefix='/api/routes')
    app.register_blueprint(weather_bp, url_prefix='/api/weather')
    app.register_blueprint(performance_bp, url_prefix='/api/performance')
    app.register_blueprint(aircraft_bp, url_prefix='/api/aircraft')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(data_bp, url_prefix='/api/data')

    return app
