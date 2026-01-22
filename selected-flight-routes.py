from flask import Blueprint, request, jsonify
from Database import get_db_connection, add_travellers
import psycopg2

selected_flight_bp = Blueprint('flight_bp', __name__)

@selected_flight_bp.route('/selected-flight', methods=['POST'])
def selected_flight():
    data = request.json
    flight_name = data.get("flight_name")
    user_id = data.get("user_id")
    travellers_list = data.get("travellers")

    if not flight_name or not user_id:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT flight_id, flight_name, airline, from_airport, to_airport, 
               departure_time, arrival_time, duration, price, airplane
        FROM flights
        WHERE flight_name = %s
    """, (flight_name,))
    
    flight_row = cur.fetchone()
    cur.close()
    conn.close()

    if not flight_row:
        return jsonify({"success": False, "message": "Flight not found"}), 404

    flight = {
        "flight_id": flight_row[0],
        "flight_name": flight_row[1],
        "airline": flight_row[2],
        "from_airport": flight_row[3],
        "to_airport": flight_row[4],
        "departure_time": flight_row[5],
        "arrival_time": flight_row[6],
        "duration": flight_row[7],
        "price": float(flight_row[8]),
        "airplane": flight_row[9]
    }

    if travellers_list and isinstance(travellers_list, list):
        add_travellers(user_id, travellers_list)

    return jsonify({"success": True, "flight": flight, "message": "Traveller(s) added!" if travellers_list else "Flight fetched successfully"})