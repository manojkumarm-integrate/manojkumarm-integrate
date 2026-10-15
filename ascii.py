"""One-off: turn the avatar into ascii_dark.txt / ascii_light.txt.

Setup (Python 3.10+):  pip install "rembg[cpu]" pillow numpy opencv-python-headless
Run:                   python ascii.py avatar.png
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageOps

COLS = 92
CROP = (60, 15, 340, 345)       # head + shoulders in the 400x400 avatar
CELL = 4.2 / 8                  # char width / line height in the SVG (7px font, 8px lines)
RAMP = " .:-=+*#%@"


def main(src):
    try:
        im = Image.open("avatar_cutout.png")
    except FileNotFoundError:
        from rembg import remove
        im = remove(Image.open(src))
        im.save("avatar_cutout.png")
    im = im.convert("RGBA").crop(CROP)
    rows = round(COLS * im.size[1] / im.size[0] * CELL)

    gray = ImageOps.grayscale(im.convert("RGB"))
    g = cv2.createCLAHE(clipLimit=4, tileGridSize=(6, 6)).apply(np.asarray(gray)).astype(float)
    blur = np.asarray(gray.filter(ImageFilter.GaussianBlur(8)), float)
    g = np.clip(g + 0.8 * (g - blur), 0, 255)

    def shrink(a):
        return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((COLS, rows), Image.LANCZOS), float)

    g = shrink(g)
    subject = shrink(np.asarray(im.split()[-1], float)) > 0.4 * 255
    lo, hi = np.percentile(g[subject], [1, 99])
    bright = np.clip((g - lo) / (hi - lo), 0, 1)

    # dark theme: bright pixels get dense glyphs; light theme: dark pixels do
    for theme, density in (("dark", bright), ("light", 1 - bright)):
        idx = np.where(subject, 1 + np.round(density * (len(RAMP) - 2)), 0).astype(int)
        lines = ["".join(RAMP[i] for i in row).rstrip() for row in idx]
        with open(f"ascii_{theme}.txt", "w") as f:
            f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "avatar.png")
