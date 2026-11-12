"""Everything the app shows lives in one SQLite file (data/duckweed.db)."""
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "duckweed.db"
PHOTO_DIR = DATA_DIR / "photos"

SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY, name TEXT, light TEXT, description TEXT,
    is_reference INTEGER DEFAULT 0, started_at TEXT);
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY, experiment_id INTEGER, ts TEXT,
    temperature_c REAL, humidity_pct REAL, water_level_mm REAL,
    coverage_pct REAL, greenness REAL, photo_path TEXT);
CREATE TABLE IF NOT EXISTS commands (
    id INTEGER PRIMARY KEY, ts TEXT, device TEXT, action TEXT,
    seconds REAL, status TEXT DEFAULT 'pending');
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY, ts TEXT, nickname TEXT, guess TEXT, reason TEXT,
    reflection TEXT, was_right INTEGER);
"""

READING_COLS = ["temperature_c", "humidity_pct", "water_level_mm",
                "coverage_pct", "greenness", "photo_path"]


def connect():
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # logger and app can use the file at once
    conn.executescript(SCHEMA)
    return conn


def now():
    return datetime.now().isoformat(timespec="seconds")


def add_experiment(conn, name, light, description, is_reference=False, started_at=None):
    cur = conn.execute(
        "INSERT INTO experiments (name, light, description, is_reference, started_at) "
        "VALUES (?,?,?,?,?)",
        (name, light, description, int(is_reference), started_at or now()))
    conn.commit()
    return cur.lastrowid


def add_reading(conn, experiment_id, ts=None, **values):
    marks = ",".join("?" * len(READING_COLS))
    conn.execute(
        f"INSERT INTO readings (experiment_id, ts, {', '.join(READING_COLS)}) VALUES (?,?,{marks})",
        (experiment_id, ts or now(), *[values.get(c) for c in READING_COLS]))
    conn.commit()


def experiments(conn):
    return conn.execute("SELECT * FROM experiments ORDER BY is_reference DESC, id").fetchall()


def readings_df(conn, experiment_id):
    df = pd.read_sql_query("SELECT * FROM readings WHERE experiment_id=? ORDER BY ts",
                           conn, params=(experiment_id,))
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df["ts"])
    df["hours"] = (df["ts"] - df["ts"].min()).dt.total_seconds() / 3600
    df["day"] = (df["hours"] / 24).round(1)
    return df


def queue_command(conn, device, action, seconds=0):
    conn.execute("INSERT INTO commands (ts, device, action, seconds) VALUES (?,?,?,?)",
                 (now(), device, action, seconds))
    conn.commit()


def recent_commands(conn, n=8):
    return pd.read_sql_query("SELECT ts, device, action, seconds, status FROM commands "
                             "ORDER BY id DESC LIMIT ?", conn, params=(n,))


def add_prediction(conn, nickname, guess, reason, reflection, was_right):
    """Nickname only. Never store real names for children."""
    conn.execute("INSERT INTO predictions (ts, nickname, guess, reason, reflection, was_right) "
                 "VALUES (?,?,?,?,?,?)", (now(), nickname, guess, reason, reflection, int(was_right)))
    conn.commit()


def predictions_df(conn):
    return pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
