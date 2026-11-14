"""PLACEHOLDER image analysis.

Replace analyse_image() with Jenn and Emmanuel's OpenCV script, keeping the same
input (a photo path) and output (coverage %, greenness 0-1) so nothing else changes.
"""
import cv2
import numpy as np


def dish_mask(shape):
    """Circle in the middle of the photo that counts as 'the dish'. Placeholder:
    the real script should detect the dish boundary (as on slide 9 of the stakeholder deck)."""
    h, w = shape[:2]
    mask = np.zeros((h, w), np.uint8)
    cv2.circle(mask, (w // 2, h // 2), int(min(h, w) * 0.45), 255, -1)
    return mask


def analyse_image(path):
    """Return (coverage_pct, greenness) for a photo of the dish."""
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(path)
    dish = dish_mask(img.shape)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255)) & dish   # OpenCV hue is 0-179
    green_px = int(np.count_nonzero(green))
    if green_px == 0:
        return 0.0, 0.0
    coverage = 100.0 * green_px / int(np.count_nonzero(dish))
    b, g, r = (img[..., i][green > 0].astype(float) for i in range(3))
    greenness = float(np.mean(g / (r + g + b + 1e-6)))
    return round(coverage, 1), round(greenness, 3)
