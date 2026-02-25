from time import time
import uuid
from flask import Flask, abort, request, jsonify
import mysql.connector
from _mysql_connector import Error
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv('.env')

def get_db(retries=3):
    for _ in range(retries):
        try:
            return mysql.connector.connect(
                host=os.getenv('MYSQLHOST'),
                port=int(os.getenv('MYSQLPORT', 3306)),
                user=os.getenv('MYSQLUSER'),
                password=os.getenv('MYSQLPASSWORD'),
                database=os.getenv('MYSQLDATABASE'),
                connection_timeout=5
            )
        except Error as e:
            last_error = e
            time.sleep(1)

def createTables():
    db = get_db()
    cur = db.cursor()

    cur.execute(
        'CREATE TABLE IF NOT EXISTS users (id CHAR(36), email TEXT, password TEXT, PRIMARY KEY (id))'
    )
    cur.execute(
        'CREATE TABLE IF NOT EXISTS stats (id CHAR(36), water INT, co2 INT, power INT, PRIMARY KEY (id), FOREIGN KEY (id) REFERENCES users(id))'
    )
    cur.execute(
        'CREATE TABLE IF NOT EXISTS saved_stats (id CHAR(36), water INT, co2 INT, power INT, PRIMARY KEY (id), FOREIGN KEY (id) REFERENCES users(id))'
    )

    db.commit()
    cur.close()
    db.close()

    return

createTables()

def user_exists(id: str) -> bool:
    db = get_db()
    cur = db.cursor()

    cur.execute('SELECT 1 FROM users WHERE id = %s', (id,))
    row = cur.fetchone()

    # not sure if i can call #close() before checking result
    cur.close()
    db.close()

    return row is not None


@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')

    # User exists already
    randomId = str(uuid.uuid4())
    if user_exists(randomId):
        abort(404)

    db = get_db()
    cur = db.cursor()
    cur.execute(
        'INSERT INTO users (id, email, password) VALUES (%s, %s, %s)',
        (randomId, email, password)
    )
    db.commit()
    cur.close()
    db.close()

    # return the id so we can save it in local storage
    return jsonify(randomId)


@app.route('/login', methods=['POST'])
def login() -> str:
    email = request.json.get('email')
    password = request.json.get('password')

    db = get_db()
    cur = db.cursor()
    cur.execute(
        'SELECT id FROM users WHERE password = %s AND email = %s',
        (password, email)
    )

    row = cur.fetchone()
    cur.close()
    db.close()

    if row is None:
        abort(404)

    return jsonify(row[0])


@app.route('/stats/<id>', methods=['GET'])
def fetch_stats(id: str):

    if not user_exists(id):
        abort(404)

    db = get_db()
    cur = db.cursor()
    cur.execute(
        'SELECT water, power, co2 FROM stats WHERE id = %s',
        (id,)
    )
    result = cur.fetchone()

    cur.close()
    db.close()

    while result is not None:
        return {
            "water": result[0],
            "power": result[1],
            "co2": result[2]
        }