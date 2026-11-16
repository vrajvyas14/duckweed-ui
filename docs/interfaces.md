# Interfaces between subsystems (DRAFT, to agree at Meeting 8)

## 1. Microcontroller -> Pi (Kai, Timi)
One JSON object per line over USB serial, 115200 baud, every few seconds:

    {"temperature_c": 23.4, "humidity_pct": 64, "water_level_mm": 31}

Questions for Kai/Timi:
- Pico 2 or ESP32? (either works over USB serial)
- Are these the three values you will actually have, and in these units?
- Is water level in mm from the sensor, or a raw value we convert?
- Pi -> microcontroller: `{"cmd": "pump", "action": "run", "seconds": 3}`.
  The logger caps pump time at 10 s. Will the microcontroller enforce its own limit too?
- What should the microcontroller do if it hears nothing from the Pi?

## 2. Camera/OpenCV -> database (Jenn, Emmanuel)
`vision.analyse_image(path)` takes a photo path and returns `(coverage_pct, greenness)`.
- coverage_pct: 0-100, % of the dish area that is duckweed
- greenness: 0-1, our proposed colour/health number (placeholder: mean g/(r+g+b) of green pixels)

Questions for Jenn/Emmanuel:
- Can your script keep this signature? Anything else it needs (dish position, lighting)?
- What colour metric do you think shows plant health best?
- Photo size, format and how often (hourly?).

## 3. Kid usability (my part)
Student mode: Look / Experiment (predict, watch, explain) / Help.
Predictions are saved with a nickname only.

## 4. Before any testing with children
Ask the facilitator/convenor whether the module needs ethics approval, and what consent
is needed. Until then, use the app with classmates only.
