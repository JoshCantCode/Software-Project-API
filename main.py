from time import sleep
import uuid
from flask import Flask, request, jsonify
import mysql.connector
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv('.env')

# sorry about this

def get_db(retries=3):
    last_error = None
    for i in range(retries):
        try:
            return mysql.connector.connect(
                host=os.getenv('MYSQLHOST'),
                port=int(os.getenv('MYSQLPORT', 3306)),
                user=os.getenv('MYSQLUSER'),
                password=os.getenv('MYSQLPASSWORD'),
                database=os.getenv('MYSQLDATABASE'),
                connection_timeout=5
            )
        except Exception as e:
            last_error = e
            print(f"Couldn't connect to Database. Attempt {i+1}/{retries}: {e}")
            sleep(1)
    raise RuntimeError(f"Failed to connect to database after {retries} attempts: {last_error}")

def createTables():
    db = get_db()
    cur = db.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id CHAR(36) PRIMARY KEY, email TEXT, password TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS stats (id CHAR(36) PRIMARY KEY, prompts INT DEFAULT 0, water INT DEFAULT 0, co2 INT DEFAULT 0, power INT DEFAULT 0, FOREIGN KEY (id) REFERENCES users(id))')
    cur.execute('CREATE TABLE IF NOT EXISTS stat_history (entry_id INT AUTO_INCREMENT PRIMARY KEY, user_id CHAR(36), prompts INT DEFAULT 0, water INT DEFAULT 0, co2 INT DEFAULT 0, power INT DEFAULT 0, recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))')
    db.commit()
    cur.close()
    db.close()

createTables()

def user_exists(id: str) -> bool:
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT 1 FROM users WHERE id = %s', (id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row is not None

def email_in_use(email: str) -> bool:
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT 1 FROM users WHERE email = %s', (email,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row is not None

def row_to_dict(row):
    if not row or row[0] is None:
        return {'prompts': 0, 'water': 0, 'co2': 0, 'power': 0}
    return {'prompts': row[0], 'water': row[1], 'co2': row[2], 'power': row[3]}

@app.route('/health', methods=["GET"])
def health():
    return jsonify({'status': 'ok'})

@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        return jsonify({'code': 400, 'message': 'Email and password are required!'}), 400

    if email_in_use(email):
        return jsonify({'code': 400, 'message': 'A user with this email already exists!'}), 400

    randomId = str(uuid.uuid4())

    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO users (id, email, password) VALUES (%s, %s, %s)', (randomId, email, password))
    cur.execute('INSERT INTO stats (id, prompts, water, co2, power) VALUES (%s, %s, %s, %s, %s)', (randomId, 0, 0, 0, 0))
    db.commit()
    cur.close()
    db.close()

    return jsonify(randomId)


@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id FROM users WHERE password = %s AND email = %s', (password, email))
    row = cur.fetchone()
    cur.close()
    db.close()

    if row is None:
        return jsonify({'code': 400, 'message': 'Invalid email or password!'}), 400

    return jsonify(row[0])




@app.route('/stats/<id>/save', methods=['POST'])
def save_stat(id: str):
    prompts = request.json.get('prompts', 0)
    water = request.json.get('water', 0)
    co2 = request.json.get('co2', 0)
    power = request.json.get('power', 0)

    if not user_exists(id):
        return jsonify({'code': 400, 'message': 'Invalid user ID!'}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute(
        'UPDATE stats SET prompts = prompts + %s, water = water + %s, co2 = co2 + %s, power = power + %s WHERE id = %s',
        (prompts, water, co2, power, id)
    )
    cur.execute(
        'INSERT INTO stat_history (user_id, prompts, water, co2, power) VALUES (%s, %s, %s, %s, %s)',
        (id, prompts, water, co2, power)
    )
    db.commit()
    cur.close()
    db.close()

    return jsonify({'code': 200, 'message': 'Stats saved!'})


@app.route('/stats/worldwide', methods=['GET'])
def worldwide_stats():
    interval = request.args.get('interval')

    valid_intervals = {
        'today': '1 DAY',
        'weekly': '7 DAY',
        'monthly': '1 MONTH',
        'yearly': '1 YEAR',
    }

    db = get_db()
    cur = db.cursor()

    if not interval:
        cur.execute('SELECT SUM(prompts), SUM(water), SUM(co2), SUM(power) FROM stats')
    else:
        if interval not in valid_intervals:
            return jsonify({'code': 400, 'message': 'Invalid interval.'}), 400
        cur.execute(
            f'SELECT SUM(prompts), SUM(water), SUM(co2), SUM(power) FROM stat_history WHERE recorded_at >= NOW() - INTERVAL {valid_intervals[interval]}'
        )

    result = cur.fetchone()
    cur.close()
    db.close()

    return jsonify(row_to_dict(result))


@app.route('/stats/<id>', methods=['GET'])
def fetch_stats(id: str):
    if not user_exists(id):
        return jsonify({'code': 400, 'message': 'Invalid user ID!'}), 400

    interval = request.args.get('interval')

    valid_intervals = {
        'today': '1 DAY',
        'weekly': '7 DAY',
        'monthly': '1 MONTH',
        'yearly': '1 YEAR',
    }

    if interval and interval not in valid_intervals:
        return jsonify({'code': 400, 'message': f'Invalid interval. Choose from: {", ".join(valid_intervals.keys())}'}), 400

    db = get_db()
    cur = db.cursor()

    if not interval:
        cur.execute('SELECT prompts, water, co2, power FROM stats WHERE id = %s', (id,))
    else:
        cur.execute(
            f'SELECT SUM(prompts), SUM(water), SUM(co2), SUM(power) FROM stat_history WHERE user_id = %s AND recorded_at >= NOW() - INTERVAL {valid_intervals[interval]}',
            (id,)
        )

    result = cur.fetchone()
    cur.close()
    db.close()

    if result is None:
        return jsonify({'code': 404, 'message': 'No stats found!'}), 404

    return jsonify(row_to_dict(result))