from flask import Blueprint, request, jsonify
from Database import get_db_connection

ticket_bp = Blueprint('ticket_bp', __name__)

@ticket_bp.route('/ticket-summary', methods=['POST'])
def summary():
    data = request.json 
    flight_name = data.get("flight_name")
    payment_method = data.get("payment_method")
    total_amount = data.get("total_amount")
    travellers_number = data.get("travellers_number")
    dates = data.get("dates")
    trip_type = data.get("trip_type") 
    departure = data.get("departure")
    arrival = data.get("arrival")

    if not flight_name or not payment_method or not total_amount or not travellers_number or not dates or not trip_type or not departure or not arrival:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT flight_name, airline, from_airport, to_airport, departure_time, arrival_time, duration, price
        FROM flights
        WHERE flight_name = %s
    """, (flight_name,))
    flight_row = cur.fetchone()
    cur.close()
    conn.close()

    if not flight_row:
        return jsonify({"success": False, "message": "Flight not found"}), 404

    flight = {
        "flight_name": flight_row[0],
        "airline": flight_row[1],
        "from": flight_row[2],
        "to": flight_row[3],
        "departure_time": flight_row[4],
        "arrival_time": flight_row[5],
        "duration": flight_row[6],
        "price": float(flight_row[7])
    }

    expected_amount = flight["price"] * travellers_number
    if total_amount != expected_amount:
        return jsonify({"success": False, "message": "Amount does not match flight price"}), 400

    if payment_method.lower() not in ["paypal","stripe"]:
        return jsonify({"success": False, "message": "Invalid payment method"}), 400

    ticket_summary = {
        "flight_name": flight["flight_name"],
        "from": flight["from"],
        "to": flight["to"],
        "dates": dates,
        "trip_type": trip_type,
        "airline": flight["airline"],
        "departure_time": flight["departure_time"],
        "arrival_time": flight["arrival_time"],
        "duration": flight["duration"],
        "travellers_number": travellers_number,
        "total_amount": total_amount,
        "payment_method": payment_method,
        "payment_status": "Paid via " + payment_method.capitalize()
    }

    return jsonify({"success": True, "ticket_summary": ticket_summary})