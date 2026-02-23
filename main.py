import uuid
from flask import Flask, abort, request
import mysql.connector
import os
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv('.env')
db = mysql.connector.connect(
    host=os.getenv('MYSQLHOST'),
    port=int(os.getenv('MYSQLPORT', 3306)),
    user=os.getenv('MYSQLUSER'),
    password=os.getenv('MYSQLPASSWORD'),
    database=os.getenv('MYSQLDATABASE')
)

def createTables():
    cur = db.cursor()

    cur.execute(f'CREATE TABLE IF NOT EXISTS users (id INT, email TEXT, password TEXT, PRIMARY KEY (id))')
    cur.execute(f'CREATE TABLE IF NOT EXISTS stats (id INT water INT, co2 INT, power INT, PRIMARY KEY (id), FOREIGN KEY (id) REFERENCES users(id)')

    db.commit()
    cur.close()

    return


@app.route('/register', methods=['POST'])
def register():
    email = request.args.get('email')
    password = request.args.get('password')

    # User exists already
    if user_exists(id):
        abort(404)

    randomId = uuid.uuid4()

    cur = db.cursor()
    cur.execute(f'INSERT INTO users (id, email, password) VALUES ({randomId}, {email}, {password})')
    db.commit()
    cur.close()

    # return the id so we can save it in local storage 
    return randomId

@app.route('/login', methods=['POST'])
def login() -> str:
    email = request.args.get('email')
    password = request.args.get('password')

    cur = db.cursor()
    cur.execute(f'SELECT id FROM users WHERE password="{password}" AND email="{email}"')
    

    for (id) in cur:
        cur.close()
        return id

def user_exists(id: str) -> bool:
    cur = db.cursor()

    cur.execute(f'SELECT * FROM users WHERE id={id}')
    row = cur.fetchone()
    
    # not sure if i can call #close() before checking result
    while row is not None:
        cur.close()
        return True

    cur.close()
    return False


@app.route('/stats/<id>', methods=['GET'])
def fetch_stats(id: str):

    if not user_exists(id):
        abort(404)
    
    cur = db.cursor()
    cur.execute(f"SELECT water, power, co2 FROM stats WHERE id = {id}")
    result = cur.fetchone()

    while result is not None:
        cur.close()
        return {
            "water": result[0],
            "power": result[1],
            "co2": result[2]
        }
