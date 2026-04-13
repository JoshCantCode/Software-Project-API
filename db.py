import sqlite3
from flask import current_app, has_app_context
from time import sleep
import uuid
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(".env")

_testing_mode = False


def set_testing_mode(val):
    global _testing_mode
    _testing_mode = val


def is_testing():
    try:
        return current_app.config.get("TESTING", False)
    except RuntimeError:
        return _testing_mode


def get_db(retries=3):
    if is_testing():
        from tests import db_test

        return db_test.get_test_db()

    last_error = None
    for i in range(retries):
        try:
            return mysql.connector.connect(
                host=os.getenv("MYSQLHOST"),
                port=int(os.getenv("MYSQLPORT", 3306)),
                user=os.getenv("MYSQLUSER"),
                password=os.getenv("MYSQLPASSWORD"),
                database=os.getenv("MYSQLDATABASE"),
                connection_timeout=5,
            )
        except Exception as e:
            last_error = e
            print(f"Couldn't connect to Database. Attempt {i + 1}/{retries}: {e}")
            sleep(1)
    raise RuntimeError(
        f"Failed to connect to database after {retries} attempts: {last_error}"
    )


def close_db(db_conn):
    if db_conn is not None and not is_testing():
        db_conn.close()


def create_tables(db_conn):
    cur = db_conn.cursor()
    if is_testing():
        cur.execute(
            "CREATE TABLE IF NOT EXISTS users (id CHAR(36) PRIMARY KEY, email TEXT, password TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS stats (id CHAR(36) PRIMARY KEY, prompts INT DEFAULT 0, water INT DEFAULT 0, co2 INT DEFAULT 0, power INT DEFAULT 0)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS stat_history (entry_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id CHAR(36), prompts INT DEFAULT 0, water INT DEFAULT 0, co2 INT DEFAULT 0, power INT DEFAULT 0, recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
    else:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS users (id CHAR(36) PRIMARY KEY, email TEXT, password TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS stats (id CHAR(36) PRIMARY KEY, prompts INT DEFAULT 0, water INT DEFAULT 0, co2 INT DEFAULT 0, power INT DEFAULT 0, FOREIGN KEY (id) REFERENCES users(id))"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS stat_history (entry_id INT AUTO_INCREMENT PRIMARY KEY, user_id CHAR(36), prompts INT DEFAULT 0, water INT DEFAULT 0, co2 INT DEFAULT 0, power INT DEFAULT 0, recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))"
        )
    db_conn.commit()
    cur.close()


def user_exists(db_conn, id: str) -> bool:
    cur = db_conn.cursor()
    if is_testing():
        cur.execute("SELECT 1 FROM users WHERE id = ?", (id,))
    else:
        cur.execute("SELECT 1 FROM users WHERE id = %s", (id,))
    row = cur.fetchone()
    cur.close()
    return row is not None


def email_in_use(db_conn, email: str) -> bool:
    cur = db_conn.cursor()
    if is_testing():
        cur.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    else:
        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    return row is not None


def row_to_dict(row):
    if not row or row[0] is None:
        return {"prompts": 0, "water": 0, "co2": 0, "power": 0}
    return {"prompts": row[0], "water": row[1], "co2": row[2], "power": row[3]}
