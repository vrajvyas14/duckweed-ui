"""Made-up demo data and pretend dish photos, so the app runs before the hardware exists.
None of these numbers are real results."""
import math
import random
from datetime import datetime, timedelta

import cv2
import numpy as np

import db
import vision

# name, light, growth rate, ceiling (%)  -- invented for the demo
RUNS = [("White light", "white", 0.75, 80),
        ("Blue light", "blue", 0.55, 65),
        ("Red light", "red", 0.90, 85)]


def make_photo(path, target_pct, rng, size=320):
    """Draw a grey dish with green dots until about target_pct is covered."""
    img = np.full((size, size, 3), (45, 50, 48), np.uint8)
    dish = vision.dish_mask(img.shape)
    img[dish > 0] = (225, 228, 230)
    green = np.zeros((size, size), np.uint8)
    dish_px = np.count_nonzero(dish)
    reach = int(size * 0.45) - 6
    while np.count_nonzero(green & dish) / dish_px * 100 < target_pct:
        for _ in range(25):
            ang, rad = rng.uniform(0, 6.283), reach * math.sqrt(rng.random())
            c = (int(size / 2 + rad * math.cos(ang)), int(size / 2 + rad * math.sin(ang)))
            r, shade = rng.randint(4, 6), rng.randint(-15, 15)
            cv2.circle(green, c, r, 255, -1)
            cv2.circle(img, c, r, (60 + shade, 165 + shade, 70 + shade), -1)
    cv2.imwrite(str(path), img)


def fill_run(conn, exp_id, start, rate, cap, steps, step_hours, rng):
    for k in range(steps):
        day = k * step_hours / 24
        target = 4 + (cap - 4) / (1 + math.exp(-rate * (day - 3.5))) + rng.uniform(-2, 2)
        photo = db.PHOTO_DIR / f"exp{exp_id}_{k:02d}.png"
        make_photo(photo, max(1, min(target, 95)), rng)
        coverage, greenness = vision.analyse_image(photo)   # same path the real photos take
        db.add_reading(
            conn, exp_id, ts=(start + timedelta(hours=k * step_hours)).isoformat(timespec="seconds"),
            temperature_c=round(22 + rng.uniform(-0.6, 0.6), 1),
            humidity_pct=round(62 + rng.uniform(-4, 4)),
            water_level_mm=round(38 - (k % 5) * 2.5, 1),
            coverage_pct=coverage, greenness=greenness, photo_path=str(photo))


def seed(conn, days=8, step_hours=12):
    if conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]:
        return
    rng = random.Random(7)
    steps = int(days * 24 / step_hours)
    start = datetime.now() - timedelta(days=days)
    for name, light, rate, cap in RUNS:
        eid = db.add_experiment(conn, name, light, f"Example run under {light} light (demo data)",
                                True, start.isoformat(timespec="seconds"))
        fill_run(conn, eid, start, rate, cap, steps, step_hours, rng)
    live_start = datetime.now() - timedelta(days=4.5)
    live = db.add_experiment(conn, "Our chamber (live demo)", "white", "Pretend live run (demo data)",
                             False, live_start.isoformat(timespec="seconds"))
    fill_run(conn, live, live_start, 0.75, 80, 10, step_hours, rng)


if __name__ == "__main__":
    seed(db.connect())
    print("Demo data ready.")
