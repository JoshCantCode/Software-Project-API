import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS

import db

app = Flask(__name__)
CORS(app)


@app.before_request
def ensure_tables():
    if not hasattr(app, "_tables_created"):
        db.create_tables(db.get_db())
        app._tables_created = True  # ty:ignore[invalid-assignment]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/register", methods=["POST"])
def register():
    email = request.json.get("email")
    password = request.json.get("password")

    if not email or not password:
        return jsonify(
            {"code": 400, "message": "Email and password are required!"}
        ), 400

    db_conn = db.get_db()
    if db.email_in_use(db_conn, email):
        db.close_db(db_conn)
        return jsonify(
            {"code": 400, "message": "A user with this email already exists!"}
        ), 400

    randomId = str(uuid.uuid4())

    cur = db_conn.cursor()
    if db.is_testing():
        cur.execute(
            "INSERT INTO users (id, email, password) VALUES (?, ?, ?)",
            (randomId, email, password),
        )
        cur.execute(
            "INSERT INTO stats (id, prompts, water, co2, power) VALUES (?, ?, ?, ?, ?)",
            (randomId, 0, 0, 0, 0),
        )
    else:
        cur.execute(
            "INSERT INTO users (id, email, password) VALUES (%s, %s, %s)",
            (randomId, email, password),
        )
        cur.execute(
            "INSERT INTO stats (id, prompts, water, co2, power) VALUES (%s, %s, %s, %s, %s)",
            (randomId, 0, 0, 0, 0),
        )
    db_conn.commit()
    cur.close()
    db.close_db(db_conn)

    return jsonify(randomId)


@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email")
    password = request.json.get("password")

    db_conn = db.get_db()
    cur = db_conn.cursor()
    if db.is_testing():
        cur.execute(
            "SELECT id FROM users WHERE password = ? AND email = ?", (password, email)
        )
    else:
        cur.execute(
            "SELECT id FROM users WHERE password = %s AND email = %s", (password, email)
        )
    row = cur.fetchone()
    cur.close()
    db.close_db(db_conn)

    if row is None:
        return jsonify({"code": 400, "message": "Invalid email or password!"}), 400

    return jsonify(row[0])


@app.route("/stats/<id>/save", methods=["POST"])
def save_stat(id: str):
    prompts = request.json.get("prompts", 0)
    water = request.json.get("water", 0)
    co2 = request.json.get("co2", 0)
    power = request.json.get("power", 0)

    db_conn = db.get_db()
    if not db.user_exists(db_conn, id):
        db.close_db(db_conn)
        return jsonify({"code": 400, "message": "Invalid user ID!"}), 400

    cur = db_conn.cursor()
    if db.is_testing():
        cur.execute(
            "UPDATE stats SET prompts = prompts + ?, water = water + ?, co2 = co2 + ?, power = power + ? WHERE id = ?",
            (prompts, water, co2, power, id),
        )
        cur.execute(
            "INSERT INTO stat_history (user_id, prompts, water, co2, power) VALUES (?, ?, ?, ?, ?)",
            (id, prompts, water, co2, power),
        )
    else:
        cur.execute(
            "UPDATE stats SET prompts = prompts + %s, water = water + %s, co2 = co2 + %s, power = power + %s WHERE id = %s",
            (prompts, water, co2, power, id),
        )
        cur.execute(
            "INSERT INTO stat_history (user_id, prompts, water, co2, power) VALUES (%s, %s, %s, %s, %s)",
            (id, prompts, water, co2, power),
        )
    db_conn.commit()
    cur.close()
    db.close_db(db_conn)

    return jsonify({"code": 200, "message": "Stats saved!"})


@app.route("/stats/worldwide", methods=["GET"])
def worldwide_stats():
    valid_intervals = {
        "today": "1 DAY",
        "weekly": "7 DAY",
        "monthly": "1 MONTH",
        "yearly": "1 YEAR",
    }

    db_conn = db.get_db()
    cur = db_conn.cursor()

    if db.is_testing():
        cur.execute("SELECT SUM(prompts), SUM(water), SUM(co2), SUM(power) FROM stats")
    else:
        cur.execute("SELECT SUM(prompts), SUM(water), SUM(co2), SUM(power) FROM stats")

    total_result = cur.fetchone()

    history_results = {}
    for interval_name, interval_value in valid_intervals.items():
        days = interval_value.split()[0]
        if db.is_testing():
            cur.execute(
                f'SELECT SUM(prompts), SUM(water), SUM(co2), SUM(power) FROM stat_history WHERE recorded_at >= datetime("now", "-{days} days")',
            )
        else:
            cur.execute(
                f"SELECT SUM(prompts), SUM(water), SUM(co2), SUM(power) FROM stat_history WHERE recorded_at >= NOW() - INTERVAL {interval_value}"
            )
        history_results[interval_name] = db.row_to_dict(cur.fetchone())

    cur.close()
    db.close_db(db_conn)

    return jsonify(
        {
            "total": db.row_to_dict(total_result),
            "today": history_results["today"],
            "weekly": history_results["weekly"],
            "monthly": history_results["monthly"],
            "yearly": history_results["yearly"],
        }
    )


@app.route("/stats/<id>", methods=["GET"])
def fetch_stats(id: str):
    valid_intervals = {
        "today": "1 DAY",
        "weekly": "7 DAY",
        "monthly": "1 MONTH",
        "yearly": "1 YEAR",
    }

    db_conn = db.get_db()
    if not db.user_exists(db_conn, id):
        db.close_db(db_conn)
        return jsonify({"code": 400, "message": "Invalid user ID!"}), 400

    cur = db_conn.cursor()

    if db.is_testing():
        cur.execute("SELECT prompts, water, co2, power FROM stats WHERE id = ?", (id,))
    else:
        cur.execute("SELECT prompts, water, co2, power FROM stats WHERE id = %s", (id,))

    total_result = cur.fetchone()

    history_results = {}
    for interval_name, interval_value in valid_intervals.items():
        days = interval_value.split()[0]
        if db.is_testing():
            cur.execute(
                f'SELECT SUM(prompts), SUM(water), SUM(co2), SUM(power) FROM stat_history WHERE user_id = ? AND recorded_at >= datetime("now", "-{days} days")',
                (id,),
            )
        else:
            cur.execute(
                f"SELECT SUM(prompts), SUM(water), SUM(co2), SUM(power) FROM stat_history WHERE user_id = %s AND recorded_at >= NOW() - INTERVAL {interval_value}",
                (id,),
            )
        history_results[interval_name] = db.row_to_dict(cur.fetchone())

    cur.close()
    db.close_db(db_conn)

    if total_result is None:
        return jsonify({"code": 404, "message": "No stats found!"}), 404

    return jsonify(
        {
            "total": db.row_to_dict(total_result),
            "today": history_results["today"],
            "weekly": history_results["weekly"],
            "monthly": history_results["monthly"],
            "yearly": history_results["yearly"],
        }
    )
