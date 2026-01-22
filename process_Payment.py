from flask import Flask, app, request, session, jsonify
from psycopg2.extras import RealDictCursor
from Database import get_db_connection

@app.route("/process_payment", methods=["POST"])
def process_payment():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()

    flight_id = data.get("flight_id")
    payment_method = data.get("payment_method")
    travellers = int(data.get("travellers", 1))

    if not flight_id or not payment_method:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    if payment_method.lower() not in ["stripe", "paypal"]:
        return jsonify({"success": False, "message": "Invalid payment method"}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            %s AS flight_id,
            f."Airline" AS airline,
            a1."Name" AS from_airport,
            a2."Name" AS to_airport,
            NOW() AS departure_time,
            NOW() + interval '2 hour' AS arrival_time,
            '2h' AS duration,
            500 AS price,
            'Flight ' || %s AS flight_name
        FROM flights f
        JOIN airports a1 ON f."Source airport ID" = a1."Airport ID"::TEXT
        JOIN airports a2 ON f."Destination airport ID" = a2."Airport ID"::TEXT
        OFFSET %s LIMIT 1;
    """, (flight_id, flight_id, flight_id - 1))

    flight = cur.fetchone()
    if not flight:
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": "Flight not found"}), 404

    total_amount = flight["price"] * travellers
    payment_status = f"Paid via {payment_method.capitalize()}"

    cur.execute("""
        INSERT INTO payments (user_id, flight_id, amount, payment_method, payment_status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING payment_id, created_at
    """, (
        session["user_id"],
        flight_id,
        total_amount,
        payment_method.capitalize(),
        payment_status
    ))

    payment_row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    # ✅ Full ticket summary for frontend
    ticket_summary = {
        "flight_id": flight["flight_id"],
        "airline": flight["airline"],
        "flight_name": flight["flight_name"],
        "from_airport": flight["from_airport"],
        "to_airport": flight["to_airport"],
        "departure_time": str(flight["departure_time"]),
        "arrival_time": str(flight["arrival_time"]),
        "duration": flight["duration"],
        "travellers_number": travellers,
        "price_per_traveller": flight["price"],
        "total_amount": total_amount,
        "payment_method": payment_method.capitalize(),
        "payment_status": payment_status,
        "payment_id": payment_row["payment_id"],
        "payment_created_at": str(payment_row["created_at"])
    }

    return jsonify({"success": True, "ticket_summary": ticket_summary})
