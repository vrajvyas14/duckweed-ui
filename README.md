# Duckweed chamber UI (starter)

Three small programs that share one SQLite file (`data/duckweed.db`):

| Program | Job |
|---|---|
| `logger.py` | Reads JSON lines from the microcontroller, saves them, sends queued commands back (pump capped at 10 s) |
| `camera_job.py` | Takes a photo, measures % green, saves a row (run hourly) |
| `app.py` | Streamlit dashboard, Student and Teacher modes. Reads the database only |

## Run on a laptop (no hardware)
    pip install -r requirements.txt
    streamlit run app.py          # first start creates MADE-UP demo data and photos
    python logger.py --fake       # optional: pretend sensors
    python camera_job.py --image data/photos/exp1_05.png

## Still to agree with the group
- `vision.py` is a placeholder. Swap in Jenn and Emmanuel's script (photo path in, coverage % and greenness out).
- Serial message from the microcontroller: `{"temperature_c": 23.4, "humidity_pct": 64, "water_level_mm": 31}`
- `LOW_WATER_MM = 25` and the health rules in `app.py` are placeholders.
- `logger.py` and `camera_job.py` are untested on real hardware.
- Check ethics rules before testing with real children.
