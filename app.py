from flightplanner import create_app

app = create_app()

if __name__ == '__main__':
    print('=' * 60)
    print('N499CP Flight Planner v3 - CAP San Diego Sr. Sq. 57')
    print('=' * 60)
    print('Starting server at http://localhost:5000')
    print('=' * 60)
    app.run(debug=False, host='0.0.0.0', port=5000)
