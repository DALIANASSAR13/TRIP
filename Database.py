import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = "postgresql://postgres.umqcumxtjtinghhzkhtf:CLOUDTRIP-123@aws-1-eu-central-1.pooler.supabase.com:5432/postgres"

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print("Database connection failed:", e)
        return None

def ensure_users_table():
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users_data (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()

def ensure_traveller_table():
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS traveller_data (
                traveller_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users_data(user_id),
                full_name VARCHAR(255) NOT NULL,
                passport_number VARCHAR(50),
                nationality VARCHAR(100),
                age INTEGER,
                gender VARCHAR(20),
                email VARCHAR(255),
                phone_number VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()

def ensure_flights_table():
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS flights (
                flight_id SERIAL PRIMARY KEY,
                "Airline" VARCHAR(255),
                "Source airport ID" VARCHAR(10),
                "Destination airport ID" VARCHAR(10),
                "flight_name" VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Ensure the flight_name column exists in case the table was created without it
        cur.execute("ALTER TABLE flights ADD COLUMN IF NOT EXISTS \"flight_name\" VARCHAR(50);")
        conn.commit()
        cur.close()
    finally:
        conn.close()

def ensure_airports_table():
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS airports (
                "Airport ID" VARCHAR(10) PRIMARY KEY,
                "Name" VARCHAR(255),
                "City" VARCHAR(100),
                "Country" VARCHAR(100),
                "IATA" VARCHAR(3),
                "ICAO" VARCHAR(4),
                "Latitude" DECIMAL(10,6),
                "Longitude" DECIMAL(10,6),
                "Altitude" INTEGER,
                "Timezone" DECIMAL(3,1),
                "DST" VARCHAR(1),
                "Tz database time zone" VARCHAR(50),
                "Type" VARCHAR(20),
                "Source" VARCHAR(20)
            );
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()

def ensure_payments_table():
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users_data(user_id),
                flight_id INTEGER REFERENCES flights(flight_id),
                amount NUMERIC NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                payment_status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()

def populate_sample_data():
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()

        # Insert sample airports
        airports_data = [
            ("1", "John F Kennedy International Airport", "New York", "United States", "JFK", "KJFK", 40.6413, -73.7781, 13, -5.0, "A", "America/New_York", "large_airport", "OurAirports"),
            ("2", "London Heathrow Airport", "London", "United Kingdom", "LHR", "EGLL", 51.4775, -0.4614, 83, 0.0, "E", "Europe/London", "large_airport", "OurAirports"),
            ("3", "Paris Charles de Gaulle Airport", "Paris", "France", "CDG", "LFPG", 49.0097, 2.5479, 392, 1.0, "E", "Europe/Paris", "large_airport", "OurAirports"),
            ("4", "Frankfurt am Main Airport", "Frankfurt", "Germany", "FRA", "EDDF", 50.0379, 8.5622, 364, 1.0, "E", "Europe/Berlin", "large_airport", "OurAirports")
        ]

        for airport in airports_data:
            try:
                cur.execute("""
                    INSERT INTO airports ("Airport ID", "Name", "City", "Country", "IATA", "ICAO", "Latitude", "Longitude", "Altitude", "Timezone", "DST", "Tz database time zone", "Type", "Source")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, airport)
            except psycopg2.errors.UniqueViolation:
                # Skip if already exists
                pass

        # Insert sample flights
        flights_data = [
            ("American Airlines", "1", "2", "AA101"),
            ("British Airways", "2", "1", "BA202"),
            ("Air France", "3", "4", "AF303"),
            ("Lufthansa", "4", "3", "LH404")
        ]

        cur.executemany("""
            INSERT INTO flights ("Airline", "Source airport ID", "Destination airport ID", "flight_name")
            VALUES (%s, %s, %s, %s)
        """, flights_data)

        conn.commit()
        cur.close()
    finally:
        conn.close()

def add_travellers(user_id, travellers_list):
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        for traveller in travellers_list:
            cur.execute("""
                INSERT INTO traveller_data
                (user_id, full_name, passport_number, nationality, age, gender, email, phone_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                traveller.get("full_name"),
                traveller.get("passport_number"),
                traveller.get("nationality"),
                traveller.get("age"),
                traveller.get("gender"),
                traveller.get("email"),
                traveller.get("phone_number")
            ))
        conn.commit()
        cur.close()
    finally:
        conn.close()

def init_db():
    ensure_users_table()
    ensure_traveller_table()
    ensure_flights_table()
    ensure_airports_table()
    ensure_payments_table()
    populate_sample_data()

if __name__ == "__main__":
    init_db()
    print("✅ Database ready")