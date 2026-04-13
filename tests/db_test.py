import sqlite3
import os

_test_db = None


def init_test_db():
    global _test_db
    if _test_db is None:
        _test_db = sqlite3.connect(":memory:", check_same_thread=False)
        _test_db.row_factory = sqlite3.Row
        cur = _test_db.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS users (id CHAR(36) PRIMARY KEY, email TEXT, password TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS stats (id CHAR(36) PRIMARY KEY, prompts INT DEFAULT 0, water INT DEFAULT 0, co2 INT DEFAULT 0, power INT DEFAULT 0)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS stat_history (entry_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id CHAR(36), prompts INT DEFAULT 0, water INT DEFAULT 0, co2 INT DEFAULT 0, power INT DEFAULT 0, recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        _test_db.commit()
        cur.close()
    return _test_db


def reset_test_db():
    global _test_db
    if _test_db is None:
        init_test_db()
    try:
        cur = _test_db.cursor()
        cur.execute("DELETE FROM stat_history")
        cur.execute("DELETE FROM stats")
        cur.execute("DELETE FROM users")
        _test_db.commit()
        cur.close()
    except sqlite3.ProgrammingError:
        init_test_db()


def get_test_db():
    return init_test_db()
