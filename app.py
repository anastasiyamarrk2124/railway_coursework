from flask import Flask, render_template, request, redirect, session
from db import get_connection
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "railway_secret_key"

def is_admin():
    return session.get("role") == "admin"


def is_operator_or_admin():
    return session.get("role") in ["admin", "operator"]


def is_logged_in():
    return "user_id" in session

def admin_required():
    if session.get("role") != "admin":
        return False
    return True

@app.route("/")
def index():
    search = request.args.get("search", "")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM stations
        WHERE station_name ILIKE %s
           OR city ILIKE %s
           OR station_code ILIKE %s
        ORDER BY station_name;
    """, (f"%{search}%", f"%{search}%", f"%{search}%"))

    stations = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", stations=stations, search=search)


@app.route("/add_station", methods=["GET", "POST"])
def add_station():
    if not admin_required():
        return "Доступ запрещен. Это действие доступно только администратору."
    if request.method == "POST":
        station_code = request.form["station_code"]
        station_name = request.form["station_name"]
        city = request.form["city"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO stations (station_code, station_name, city)
            VALUES (%s, %s, %s)
        """, (station_code, station_name, city))

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/")

    return render_template("add_station.html")


@app.route("/edit_station/<int:station_id>", methods=["GET", "POST"])
def edit_station(station_id):
    if not admin_required():
        return "Доступ запрещен. Это действие доступно только администратору."
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        station_code = request.form["station_code"]
        station_name = request.form["station_name"]
        city = request.form["city"]

        cur.execute("""
            UPDATE stations
            SET station_code = %s,
                station_name = %s,
                city = %s
            WHERE station_id = %s;
        """, (station_code, station_name, city, station_id))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/")

    cur.execute("""
        SELECT *
        FROM stations
        WHERE station_id = %s;
    """, (station_id,))

    station = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("edit_station.html", station=station)


@app.route("/delete_station/<int:station_id>", methods=["POST"])
def delete_station(station_id):
    if not admin_required():
        return "Доступ запрещен. Это действие доступно только администратору."

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM stations
            WHERE station_id = %s;
        """, (station_id,))

        conn.commit()

    except (psycopg2.errors.RestrictViolation, psycopg2.errors.ForeignKeyViolation):
        conn.rollback()
        cur.close()
        conn.close()

        return "Нельзя удалить станцию, потому что она используется в маршруте."

    cur.close()
    conn.close()

    return redirect("/")


@app.route("/trains")
def trains():

    search = request.args.get("search", "")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM trains
        WHERE train_number ILIKE %s
           OR train_type ILIKE %s
        ORDER BY train_number
    """, (f"%{search}%", f"%{search}%"))

    trains = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "trains.html",
        trains=trains,
        search=search
    )


@app.route("/add_train", methods=["GET", "POST"])
def add_train():
    if not admin_required():
        return "Доступ запрещен. Это действие доступно только администратору."
    if request.method == "POST":
        train_number = request.form["train_number"]
        train_type = request.form["train_type"]
        seat_count = request.form["seat_count"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO trains (train_number, train_type, seat_count)
            VALUES (%s, %s, %s);
        """, (train_number, train_type, seat_count))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/trains")

    return render_template("add_train.html")


@app.route("/edit_train/<int:train_id>", methods=["GET", "POST"])
def edit_train(train_id):
    if not admin_required():
        return "Доступ запрещен. Это действие доступно только администратору."
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        train_number = request.form["train_number"]
        train_type = request.form["train_type"]
        seat_count = request.form["seat_count"]

        cur.execute("""
            UPDATE trains
            SET train_number = %s,
                train_type = %s,
                seat_count = %s
            WHERE train_id = %s;
        """, (train_number, train_type, seat_count, train_id))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/trains")

    cur.execute("""
        SELECT *
        FROM trains
        WHERE train_id = %s;
    """, (train_id,))

    train = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("edit_train.html", train=train)


@app.route("/delete_train/<int:train_id>", methods=["POST"])
def delete_train(train_id):
    if not admin_required():
        return "Доступ запрещен. Это действие доступно только администратору."

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM trains
            WHERE train_id = %s;
        """, (train_id,))

        conn.commit()

    except (psycopg2.errors.RestrictViolation, psycopg2.errors.ForeignKeyViolation):
        conn.rollback()
        cur.close()
        conn.close()

        return "Нельзя удалить поезд, потому что он используется в рейсе."

    cur.close()
    conn.close()

    return redirect("/trains")



@app.route("/routes")
def routes():
    search = request.args.get("search", "")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM routes
        WHERE route_name ILIKE %s
        ORDER BY route_name;
    """, (f"%{search}%",))

    routes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("routes.html", routes=routes, search=search)


@app.route("/add_route", methods=["GET", "POST"])
def add_route():
    if not admin_required():
        return "Доступ запрещен. Это действие доступно только администратору."
    if request.method == "POST":
        route_name = request.form["route_name"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO routes (route_name)
            VALUES (%s);
        """, (route_name,))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/routes")

    return render_template("add_route.html")


@app.route("/edit_route/<int:route_id>", methods=["GET", "POST"])
def edit_route(route_id):
    if not admin_required():
        return "Доступ запрещен. Это действие доступно только администратору."
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        route_name = request.form["route_name"]

        cur.execute("""
            UPDATE routes
            SET route_name = %s
            WHERE route_id = %s;
        """, (route_name, route_id))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/routes")

    cur.execute("""
        SELECT *
        FROM routes
        WHERE route_id = %s;
    """, (route_id,))

    route = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("edit_route.html", route=route)


@app.route("/delete_route/<int:route_id>", methods=["POST"])
def delete_route(route_id):
    if not admin_required():
        return "Доступ запрещен. Это действие доступно только администратору."

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM routes
            WHERE route_id = %s;
        """, (route_id,))

        conn.commit()

    except (psycopg2.errors.RestrictViolation, psycopg2.errors.ForeignKeyViolation):
        conn.rollback()
        cur.close()
        conn.close()

        return "Нельзя удалить маршрут, потому что он используется в рейсе или списке станций маршрута."

    cur.close()
    conn.close()

    return redirect("/routes")


@app.route("/trips")
def trips():
    search = request.args.get("search", "")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            trips.trip_id,
            trains.train_number,
            routes.route_name,
            trips.departure_date,
            trips.departure_time,
            trips.arrival_date,
            trips.arrival_time,
            trips.status
        FROM trips
        JOIN trains ON trips.train_id = trains.train_id
        JOIN routes ON trips.route_id = routes.route_id
        WHERE trains.train_number ILIKE %s
           OR routes.route_name ILIKE %s
           OR trips.status ILIKE %s
        ORDER BY trips.departure_date, trips.departure_time;
    """, (f"%{search}%", f"%{search}%", f"%{search}%"))

    trips = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("trips.html", trips=trips, search=search)


@app.route("/add_trip", methods=["GET", "POST"])
def add_trip():
    if not is_operator_or_admin():
        return "Доступ запрещен."
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        train_id = request.form["train_id"]
        route_id = request.form["route_id"]
        departure_date = request.form["departure_date"]
        departure_time = request.form["departure_time"]
        arrival_date = request.form["arrival_date"]
        arrival_time = request.form["arrival_time"]
        status = request.form["status"]

        cur.execute("""
            INSERT INTO trips (
                train_id, route_id,
                departure_date, departure_time,
                arrival_date, arrival_time,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (
            train_id, route_id,
            departure_date, departure_time,
            arrival_date, arrival_time,
            status
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/trips")

    cur.execute("SELECT * FROM trains ORDER BY train_number;")
    trains = cur.fetchall()

    cur.execute("SELECT * FROM routes ORDER BY route_name;")
    routes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "add_trip.html",
        trains=trains,
        routes=routes
    )



@app.route("/edit_trip/<int:trip_id>", methods=["GET", "POST"])
def edit_trip(trip_id):
    if not is_operator_or_admin():
        return "Доступ запрещен."

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        train_id = request.form["train_id"]
        route_id = request.form["route_id"]
        departure_date = request.form["departure_date"]
        departure_time = request.form["departure_time"]
        arrival_date = request.form["arrival_date"]
        arrival_time = request.form["arrival_time"]
        status = request.form["status"]

        cur.execute("""
            UPDATE trips
            SET train_id = %s,
                route_id = %s,
                departure_date = %s,
                departure_time = %s,
                arrival_date = %s,
                arrival_time = %s,
                status = %s
            WHERE trip_id = %s;
        """, (
            train_id, route_id,
            departure_date, departure_time,
            arrival_date, arrival_time,
            status,
            trip_id
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/trips")

    cur.execute("SELECT * FROM trips WHERE trip_id = %s;", (trip_id,))
    trip = cur.fetchone()

    cur.execute("SELECT * FROM trains ORDER BY train_number;")
    trains = cur.fetchall()

    cur.execute("SELECT * FROM routes ORDER BY route_name;")
    routes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "edit_trip.html",
        trip=trip,
        trains=trains,
        routes=routes
    )


@app.route("/delete_trip/<int:trip_id>", methods=["POST"])
def delete_trip(trip_id):
    if not is_operator_or_admin():
        return "Доступ запрещен."

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM trips
            WHERE trip_id = %s;
        """, (trip_id,))

        conn.commit()

    except psycopg2.errors.ForeignKeyViolation:
        conn.rollback()
        cur.close()
        conn.close()

        return "Нельзя удалить рейс, потому что на него оформлены билеты."

    cur.close()
    conn.close()

    return redirect("/trips")


@app.route("/tickets")
def tickets():
    search = request.args.get("search", "")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            tickets.ticket_id,
            tickets.seat_number,
            tickets.price,
            tickets.status,
            tickets.purchase_date,
            users.username,
            trains.train_number,
            routes.route_name,
            trips.departure_date,
            trips.departure_time
        FROM tickets
        JOIN users ON tickets.user_id = users.user_id
        JOIN trips ON tickets.trip_id = trips.trip_id
        JOIN trains ON trips.train_id = trains.train_id
        JOIN routes ON trips.route_id = routes.route_id
        WHERE users.username ILIKE %s
           OR trains.train_number ILIKE %s
           OR routes.route_name ILIKE %s
           OR tickets.status ILIKE %s
        ORDER BY tickets.purchase_date DESC;
    """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))

    tickets = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("tickets.html", tickets=tickets, search=search)


@app.route("/add_ticket", methods=["GET", "POST"])
def add_ticket():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        trip_id = request.form["trip_id"]
        user_id = request.form["user_id"]
        seat_number = request.form["seat_number"]
        price = request.form["price"]
        status = request.form["status"]

        cur.execute("""
            INSERT INTO tickets (trip_id, user_id, seat_number, price, status)
            VALUES (%s, %s, %s, %s, %s);
        """, (trip_id, user_id, seat_number, price, status))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/tickets")

    cur.execute("""
        SELECT
            trips.trip_id,
            trains.train_number,
            routes.route_name,
            trips.departure_date,
            trips.departure_time
        FROM trips
        JOIN trains ON trips.train_id = trains.train_id
        JOIN routes ON trips.route_id = routes.route_id
        ORDER BY trips.departure_date, trips.departure_time;
    """)
    trips = cur.fetchall()

    cur.execute("""
        SELECT *
        FROM users
        ORDER BY username;
    """)
    users = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("add_ticket.html", trips=trips, users=users)


@app.route("/edit_ticket/<int:ticket_id>", methods=["GET", "POST"])
def edit_ticket(ticket_id):
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        trip_id = request.form["trip_id"]
        user_id = request.form["user_id"]
        seat_number = request.form["seat_number"]
        price = request.form["price"]
        status = request.form["status"]

        cur.execute("""
            UPDATE tickets
            SET trip_id = %s,
                user_id = %s,
                seat_number = %s,
                price = %s,
                status = %s
            WHERE ticket_id = %s;
        """, (trip_id, user_id, seat_number, price, status, ticket_id))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/tickets")

    cur.execute("SELECT * FROM tickets WHERE ticket_id = %s;", (ticket_id,))
    ticket = cur.fetchone()

    cur.execute("""
        SELECT
            trips.trip_id,
            trains.train_number,
            routes.route_name,
            trips.departure_date,
            trips.departure_time
        FROM trips
        JOIN trains ON trips.train_id = trains.train_id
        JOIN routes ON trips.route_id = routes.route_id
        ORDER BY trips.departure_date, trips.departure_time;
    """)
    trips = cur.fetchall()

    cur.execute("SELECT * FROM users ORDER BY username;")
    users = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "edit_ticket.html",
        ticket=ticket,
        trips=trips,
        users=users
    )

@app.route("/delete_ticket/<int:ticket_id>", methods=["POST"])
def delete_ticket(ticket_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM tickets
        WHERE ticket_id = %s;
    """, (ticket_id,))

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/tickets")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = "passenger"

        password_hash = generate_password_hash(password)

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s);
            """, (username, password_hash, role))

            conn.commit()

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            cur.close()
            conn.close()
            return "Пользователь с таким логином уже существует."

        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM users
            WHERE username = %s;
        """, (username,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect("/")

        return "Неверный логин или пароль."

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/buy_ticket/<int:trip_id>", methods=["GET", "POST"])
def buy_ticket(trip_id):
    if not is_logged_in():
        return redirect("/login")

    if session.get("role") != "passenger":
        return "Покупка билета доступна только пассажиру."

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        seat_number = request.form["seat_number"]
        price = request.form["price"]

        try:
            cur.execute("""
                INSERT INTO tickets (trip_id, user_id, seat_number, price, status)
                VALUES (%s, %s, %s, %s, 'paid');
            """, (
                trip_id,
                session["user_id"],
                seat_number,
                price
            ))

            conn.commit()

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            cur.close()
            conn.close()
            return "Это место уже занято на выбранный рейс."

        cur.close()
        conn.close()

        return redirect("/my_tickets")

    cur.execute("""
        SELECT
            trips.trip_id,
            trains.train_number,
            routes.route_name,
            trips.departure_date,
            trips.departure_time,
            trips.arrival_date,
            trips.arrival_time
        FROM trips
        JOIN trains ON trips.train_id = trains.train_id
        JOIN routes ON trips.route_id = routes.route_id
        WHERE trips.trip_id = %s;
    """, (trip_id,))

    trip = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("buy_ticket.html", trip=trip)


@app.route("/my_tickets")
def my_tickets():
    if not is_logged_in():
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            tickets.ticket_id,
            tickets.seat_number,
            tickets.price,
            tickets.status,
            tickets.purchase_date,
            trains.train_number,
            routes.route_name,
            trips.departure_date,
            trips.departure_time
        FROM tickets
        JOIN trips ON tickets.trip_id = trips.trip_id
        JOIN trains ON trips.train_id = trains.train_id
        JOIN routes ON trips.route_id = routes.route_id
        WHERE tickets.user_id = %s
        ORDER BY tickets.purchase_date DESC;
    """, (session["user_id"],))

    tickets = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("my_tickets.html", tickets=tickets)


@app.route("/reports")
def reports():
    if session.get("role") not in ["admin", "operator"]:
        return "Доступ запрещен."

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM trip_income
        ORDER BY total_income DESC;
    """)
    income_report = cur.fetchall()

    cur.execute("""
        SELECT
            status,
            COUNT(*) AS count
        FROM tickets
        GROUP BY status
        ORDER BY count DESC;
    """)
    ticket_status_report = cur.fetchall()

    cur.execute("""
        SELECT
            routes.route_name,
            COUNT(trips.trip_id) AS trips_count
        FROM routes
        LEFT JOIN trips ON routes.route_id = trips.route_id
        GROUP BY routes.route_name
        ORDER BY trips_count DESC;
    """)
    routes_report = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "reports.html",
        income_report=income_report,
        ticket_status_report=ticket_status_report,
        routes_report=routes_report
    )



@app.route("/debug_db")
def debug_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT current_database(), current_schema();")
    db_info = cur.fetchone()

    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "db_info": dict(db_info),
        "tables": [dict(row) for row in tables]
    }


if __name__ == "__main__":
    app.run(debug=True)