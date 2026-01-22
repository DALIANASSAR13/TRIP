from flask import Blueprint, request, jsonify
from Database import get_db_connection

flight_bp = Blueprint('flight_bp', __name__)

@flight_bp.route('/search-flights', methods=['POST'])
def search_flights():
    data = request.json

    departure = data.get("departure")
    arrival = data.get("arrival")
    dates = data.get("dates")
    trip_type = data.get("trip_type") 
    travellers_number = data.get("travellers_number")
    class_type = data.get("class_type")

    if not departure or not arrival or not dates or not trip_type or not travellers_number or not class_type:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    if trip_type == "one-way" and len(dates) != 1:
        return jsonify({"success": False, "message": "One-way trip must have 1 date"}), 400
    elif trip_type == "round-trip" and len(dates) != 2:
        return jsonify({"success": False, "message": "Round-trip must have 2 dates"}), 400
    elif trip_type == "multi-trip" and (len(dates) < 2 or len(dates) > 4):
        return jsonify({"success": False, "message": "Multi-trip must have 2 to 4 dates"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT flight_name, airline, from_airport, to_airport, departure_time, arrival_time, duration, price
        FROM flights
        WHERE from_airport = %s AND to_airport = %s
    """, (departure, arrival))
    flights_rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for i, row in enumerate(flights_rows):
        for date in dates:
            results.append({
                "flight_id": i+1,
                "flight_name": row[0],
                "from": row[2],
                "to": row[3],
                "date": date,
                "trip_type": trip_type,
                "airline": row[1],
                "departure_time": row[4],
                "arrival_time": row[5],
                "duration": row[6],
                "price": float(row[7])
            })

    return jsonify({"success": True, "flights": results})