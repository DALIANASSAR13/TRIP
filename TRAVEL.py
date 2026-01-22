from flask import Flask, request, redirect, url_for, session, render_template, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from psycopg2.extras import RealDictCursor
from Database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# ================== AUTH & HOME ================== #
@app.route("/")
@app.route("/home") 
@app.route("/index")
def home():
    username = session.get("username")
    return render_template("index.html", username=username)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not first_name or not email or not password:
            return "All fields are required!"

        username = f"{first_name} {last_name}".strip()
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users_data WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return "Email already registered!"

        cur.execute("""
            INSERT INTO users_data (username, email, password_hash)
            VALUES (%s, %s, %s) RETURNING user_id
        """, (username, email, hashed_pw))
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        session["user_id"] = user_id
        session["username"] = username
        return redirect(url_for("home"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT user_id, password_hash, username FROM users_data WHERE email=%s", (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row and check_password_hash(row['password_hash'], password):
            session["user_id"] = row['user_id']
            session["username"] = row['username']
            return redirect(url_for("home"))

        return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ================== SEARCH ================== #
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html")

    from_val = request.form.get("from_city", "").strip()
    to_val = request.form.get("to_city", "").strip()
    travellers_str = request.form.get("travellers", "1").strip()
    travellers = int(travellers_str) if travellers_str else 1
    depart_date = request.form.get("depart_date", "")
    return_date = request.form.get("return_date", "")
    flight_class = request.form.get("flight_class", "")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Parse depart_date and create datetime objects
    from datetime import datetime, timedelta
    depart_datetime = datetime.strptime(depart_date, '%Y-%m-%d') if depart_date else datetime.now()
    arrival_datetime = depart_datetime + timedelta(hours=2)

    cur.execute("""
        SELECT
            ROW_NUMBER() OVER () AS flight_id,
            f."Airline" AS airline,
            a1."IATA" AS from_airport,
            a1."City" AS from_city,
            a2."IATA" AS to_airport,
            a2."City" AS to_city,
            %s::timestamp AS departure_time,
            %s::timestamp AS arrival_time,
            '2h' AS duration,
            500 AS price
        FROM flights f
        JOIN airports a1 ON f."Source airport ID" = a1."Airport ID"::TEXT
        JOIN airports a2 ON f."Destination airport ID" = a2."Airport ID"::TEXT
        WHERE
            (a1."City" ILIKE %s OR a1."Country" ILIKE %s OR f."Source airport" ILIKE %s)
          AND
            (a2."City" ILIKE %s OR a2."Country" ILIKE %s OR f."Destination airport" ILIKE %s)
        LIMIT 50;
    """, (depart_datetime.strftime('%Y-%m-%d %H:%M:%S'), arrival_datetime.strftime('%Y-%m-%d %H:%M:%S'),
          f"%{from_val}%", f"%{from_val}%", from_val,
          f"%{to_val}%", f"%{to_val}%", to_val))

    flights = cur.fetchall()
    cur.close()
    conn.close()

    # If no flights found in database, return static flights for testing
    if not flights:
        # Create datetime objects for the user's selected date
        depart_datetime = datetime.strptime(depart_date, '%Y-%m-%d') if depart_date else datetime.now()
        arrival_datetime_1 = depart_datetime + timedelta(hours=12)  # 12 hours later
        arrival_datetime_2 = depart_datetime + timedelta(hours=12, minutes=30)  # 12.5 hours later, but next day

        flights = [
            {
                "flight_id": 1,
                "airline": "American Airlines",
                "from_airport": "JFK",
                "from_city": from_val,
                "to_airport": "LHR",
                "to_city": to_val,
                "departure_time": depart_datetime.replace(hour=8, minute=0),
                "arrival_time": arrival_datetime_1.replace(hour=20, minute=0),
                "duration": "12h 00m",
                "price": 850.00
            },
            {
                "flight_id": 2,
                "airline": "British Airways",
                "from_airport": "JFK",
                "from_city": from_val,
                "to_airport": "LHR",
                "to_city": to_val,
                "departure_time": depart_datetime.replace(hour=14, minute=30),
                "arrival_time": arrival_datetime_2.replace(hour=2, minute=30),
                "duration": "12h 00m",
                "price": 920.00
            }
        ]

    # Create search_info object to pass to template
    search_info = {
        "from_city": from_val,
        "to_city": to_val,
        "travellers": travellers,
        "depart_date": depart_date,
        "return_date": return_date,
        "flight_class": flight_class
    }

    # Store search info and flights in session for fallback in traveller page
    session["search_info"] = search_info
    session["flights"] = flights

    return render_template("search_results.html", flights=flights, search_info=search_info)

# ================== TRAVELLERS ================== #
@app.route("/travellers/<int:flight_id>")
def travellers_with_flight(flight_id):
    travellers_num = int(request.args.get("travellers", 1))

    # Try to get flight data from session first (from search results)
    selected_flight = session.get("selected_flight")

    if selected_flight and str(selected_flight.get("flight_id")) == str(flight_id):
        # Use the selected flight data from session
        flight = selected_flight
    else:
        # Check if the flight is in the search results stored in session
        flights = session.get("flights", [])
        for f in flights:
            if str(f.get("flight_id")) == str(flight_id):
                flight = f
                break
        else:
            # Fallback to database query if session data not available
            try:
                conn = get_db_connection()
                cur = conn.cursor(cursor_factory=RealDictCursor)

                cur.execute("""
                    SELECT
                        ROW_NUMBER() OVER () AS flight_id,
                        f."Airline" AS airline,
                        a1."IATA" AS from_airport,
                        a1."City" AS from_city,
                        a2."IATA" AS to_airport,
                        a2."City" AS to_city,
                        500 AS price
                    FROM flights f
                    JOIN airports a1 ON f."Source airport ID" = a1."Airport ID"::TEXT
                    JOIN airports a2 ON f."Destination airport ID" = a2."Airport ID"::TEXT
                    OFFSET %s LIMIT 1;
                """, (flight_id - 1,))

                flight = cur.fetchone()
                cur.close()
                conn.close()
            except Exception as e:
                print(f"Database error: {e}")
                flight = None

    if not flight:
        return "Flight not found"

    return render_template("Travellers.html", flight=flight, travellers_num=travellers_num)

@app.route("/traveller", methods=["POST"])
def save_traveller():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        # Handle FormData instead of JSON
        travellers_json = request.form.get("travellers")
        if not travellers_json:
            return jsonify({"success": False, "error": "Missing traveller data"}), 400

        travellers = []
        try:
            travellers = eval(travellers_json)  # Since it's passed as string from JavaScript
        except:
            return jsonify({"success": False, "error": "Invalid traveller data format"}), 400

        flight_id = request.form.get("flight_id")
        total_amount = request.form.get("total_amount", 0)

        # Validate traveller count (1-9 travellers)
        if not travellers or len(travellers) < 1 or len(travellers) > 9:
            return jsonify({"success": False, "error": "Invalid number of travellers (1-9 allowed)"}), 400

        if not flight_id:
            return jsonify({"success": False, "error": "Missing flight ID"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Save each traveller
        for traveller in travellers:
            # Validate required fields
            if not traveller.get("full_name") or not traveller.get("age") or not traveller.get("passport_number"):
                return jsonify({"success": False, "error": "Missing required traveller information"}), 400

            cur.execute("""
                INSERT INTO traveller_data (user_id, full_name, age, passport_number, nationality, gender, email, phone_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session["user_id"],
                traveller.get("full_name"),
                traveller.get("age"),
                traveller.get("passport_number"),
                traveller.get("nationality", "Not Provided"),
                traveller.get("gender", "Not Specified"),
                traveller.get("email", ""),
                traveller.get("phone_number", "Not Provided")
            ))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": f"{len(travellers)} traveller details saved successfully"})

    except Exception as e:
        print(f"Error saving traveller: {e}")
        return jsonify({"success": False, "error": "Failed to save traveller details"}), 500

# ================== PAYMENT ================== #
@app.route("/payment/<int:flight_id>")
def payment_with_flight(flight_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Get travellers number from query parameters
    travellers_num = int(request.args.get("travellers", 1))

    # Try to get flight data from session first (from search results)
    selected_flight = session.get("selected_flight")

    if selected_flight and str(selected_flight.get("flight_id")) == str(flight_id):
        # Use the selected flight data from session
        flight = selected_flight
    else:
        # Fallback to database query if session data not available
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                ROW_NUMBER() OVER () AS flight_id,
                f."Airline" AS airline,
                a1."Name" AS from_airport,
                a1."City" AS from_city,
                a2."Name" AS to_airport,
                a2."City" AS to_city,
                500 AS price
            FROM flights f
            JOIN airports a1 ON f."Source airport ID" = a1."Airport ID"::TEXT
            JOIN airports a2 ON f."Destination airport ID" = a2."Airport ID"::TEXT
            OFFSET %s LIMIT 1;
        """, (flight_id - 1,))

        flight = cur.fetchone()
        cur.close()
        conn.close()

    if not flight:
        return "Flight not found"

    return render_template("payment.html", flight=flight, travellers_num=travellers_num)

@app.route("/store_selected_flight", methods=["POST"])
def store_selected_flight():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No flight data provided"}), 400

    # Store the selected flight in session
    session["selected_flight"] = data
    return jsonify({"success": True})

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

    # Get the selected flight from session instead of database
    selected_flight = session.get("selected_flight")

    if not selected_flight or str(selected_flight.get("flight_id")) != str(flight_id):
        # Fallback to database if session data not available
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT
                    ROW_NUMBER() OVER () AS flight_id,
                    f."Airline" AS airline,
                    a1."IATA" AS from_airport,
                    a2."IATA" AS to_airport,
                    NOW() AS departure_time,
                    NOW() + interval '2 hour' AS arrival_time,
                    '2h' AS duration,
                    500 AS price,
                    'Flight ' || ROW_NUMBER() OVER () AS flight_name
                FROM flights f
                JOIN airports a1 ON f."Source airport ID" = a1."Airport ID"::TEXT
                JOIN airports a2 ON f."Destination airport ID" = a2."Airport ID"::TEXT
                OFFSET %s LIMIT 1;
            """, (flight_id - 1,))

            flight = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Database error in process_payment: {e}")
            return jsonify({"success": False, "message": "Database error"}), 500

        if not flight:
            return jsonify({"success": False, "message": "Flight not found"}), 404
    else:
        # Use the selected flight data from session
        flight = selected_flight

    if not flight:
        return jsonify({"success": False, "message": "Flight data not found"}), 404

    total_amount = flight["price"] * travellers
    payment_status = f"Paid via {payment_method.capitalize()}"

    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"}), 500

        cur = conn.cursor(cursor_factory=RealDictCursor)

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
        if not payment_row:
            return jsonify({"success": False, "message": "Failed to create payment record"}), 500

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error saving payment: {e}")
        return jsonify({"success": False, "message": "Failed to save payment"}), 500

    # ✅ Full ticket summary for frontend using actual flight data
    ticket_summary = {
        "flight_id": flight["flight_id"],
        "airline": flight.get("airline", "Unknown Airline"),
        "flight_name": flight.get("flight_name", f"Flight {flight_id}"),
        "from_airport": flight.get("from_airport", flight.get("from", "N/A")),
        "to_airport": flight.get("to_airport", flight.get("to", "N/A")),
        "departure_time": str(flight.get("departure_time", "")),
        "arrival_time": str(flight.get("arrival_time", "")),
        "duration": flight.get("duration", "N/A"),
        "travellers_number": travellers,
        "price_per_traveller": flight["price"],
        "total_amount": total_amount,
        "payment_method": payment_method.capitalize(),
        "payment_status": payment_status,
        "payment_id": payment_row["payment_id"],
        "payment_created_at": str(payment_row["created_at"])
    }

    return jsonify({"success": True, "ticket_summary": ticket_summary})
    

# ================== POST-PAYMENT SUCCESS ROUTES ================== #
@app.route("/success")
@app.route("/confirmation")
@app.route("/done")
@app.route("/payment_success")
@app.route("/complete")
def success_page():
    try:
        return render_template("success.html")
    except:
        return render_template("index.html", message="Thank you! Your payment was successful")

@app.route("/bookings")
@app.route("/my-bookings")
def bookings_page():
    return render_template("index.html", message="Your booking is confirmed!")

# ==================Ticket-summary- Routes==================#
@app.route("/ticket-summary-page")
def ticket_summary_page():
    return render_template("ticket_summary.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)