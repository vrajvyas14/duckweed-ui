"""Hourly job: take a photo, measure coverage, save a row. Run it from cron or systemd on the Pi.

    python camera_job.py                 uses the Pi camera (picamera2)  -- UNTESTED on hardware so far
    python camera_job.py --image x.png   analyses an existing photo (for testing on a laptop)

On the Pi: sudo apt install python3-picamera2   (and make the venv with --system-site-packages)
"""
import argparse
import time
from pathlib import Path

import db
import vision


def take_photo(path):
    from picamera2 import Picamera2
    cam = Picamera2()
    cam.configure(cam.create_still_configuration())
    cam.start()
    time.sleep(2)                       # let exposure settle
    cam.capture_file(str(path))
    cam.stop()
    cam.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    args = ap.parse_args()

    conn = db.connect()
    live = next((e["id"] for e in db.experiments(conn) if not e["is_reference"]), None)
    if live is None:
        live = db.add_experiment(conn, "Our chamber (live)", "white", "Live run")

    if args.image:
        path = Path(args.image)
    else:
        path = db.PHOTO_DIR / f"live_{int(time.time())}.jpg"
        take_photo(path)

    coverage, greenness = vision.analyse_image(path)
    sensors = conn.execute(
        "SELECT temperature_c, humidity_pct, water_level_mm FROM readings "
        "WHERE experiment_id=? AND temperature_c IS NOT NULL ORDER BY ts DESC LIMIT 1",
        (live,)).fetchone()
    db.add_reading(conn, live, coverage_pct=coverage, greenness=greenness, photo_path=str(path),
                   **(dict(sensors) if sensors else {}))
    print(f"saved: coverage {coverage}%, greenness {greenness}")


if __name__ == "__main__":
    main()
