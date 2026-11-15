"""Reads JSON lines from the microcontroller over USB serial and saves them.
Also sends queued commands (pump, fan, light) back, with safety limits.

    python logger.py --port /dev/ttyACM0     real hardware (UNTESTED on hardware so far)
    python logger.py --fake                  pretend sensors, for testing on a laptop

PROPOSED message, one line every few seconds (to agree with Timi, Kai and Jenn):
    {"temperature_c": 23.4, "humidity_pct": 64, "water_level_mm": 31}
"""
import argparse
import json
import random
import time

import db

MAX_PUMP_SECONDS = 10
FIELDS = ("temperature_c", "humidity_pct", "water_level_mm")


def parse_line(line):
    """Return a dict of the three readings, or None if the line is junk."""
    try:
        data = json.loads(line)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    if not all(isinstance(data.get(f), (int, float)) for f in FIELDS):
        return None
    return {f: float(data[f]) for f in FIELDS}


def fake_line():
    return json.dumps({"temperature_c": round(22 + random.uniform(-1, 1), 1),
                       "humidity_pct": round(62 + random.uniform(-5, 5)),
                       "water_level_mm": round(35 + random.uniform(-3, 3), 1)})


def send_commands(conn, ser):
    rows = conn.execute("SELECT * FROM commands WHERE status='pending'").fetchall()
    for row in rows:
        seconds = float(row["seconds"] or 0)
        if row["device"] == "pump":
            seconds = min(seconds, MAX_PUMP_SECONDS)   # never run the pump longer than this
        msg = {"cmd": row["device"], "action": row["action"], "seconds": seconds}
        ser.write((json.dumps(msg) + "\n").encode())
        conn.execute("UPDATE commands SET status='sent' WHERE id=?", (row["id"],))
        conn.commit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--every", type=float, default=60, help="seconds between saved readings")
    args = ap.parse_args()

    conn = db.connect()
    live = next((e["id"] for e in db.experiments(conn) if not e["is_reference"]), None)
    if live is None:
        live = db.add_experiment(conn, "Our chamber (live)", "white", "Live run")
    ser = None
    if not args.fake:
        import serial
        ser = serial.Serial(args.port, args.baud, timeout=1)

    last_saved = 0.0
    while True:
        line = fake_line() if args.fake else ser.readline().decode(errors="ignore")
        values = parse_line(line)
        if values and time.time() - last_saved >= args.every:
            db.add_reading(conn, live, **values)
            last_saved = time.time()
            print("saved", values)
        if ser:
            send_commands(conn, ser)
        if args.fake:
            time.sleep(1)


if __name__ == "__main__":
    main()
