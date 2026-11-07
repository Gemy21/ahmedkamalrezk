#!/usr/bin/env python3
"""
Prepare the profile photo for clean ASCII conversion:

  1. cut the subject out of the background (rembg) when it is installed, so the
     portrait floats on the dark terminal instead of showing the photo backdrop
  2. crop a square around the head
  3. smooth away photo texture with a median + slight blur
  4. normalise contrast over the subject only
  5. save a grayscale PNG consumed by make_ascii_svg.py.

rembg is optional and opt-in (USE_REMBG=1) because its first run downloads a
large model. Without it the crop is simply grayscaled; the ASCII script also
applies an elliptical vignette so the edges still fade out.

    python scripts/prep_photo.py <input.png> [output.png]
"""
import os
import sys

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

remove = None
if os.getenv("USE_REMBG") == "1":
    try:
        from rembg import new_session, remove
    except ImportError:  # optional dependency
        print("USE_REMBG=1 but rembg is not installed; continuing without it")

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

# square crop expressed in fractions of the source width:
#   (left, top, side) -- tweak these if you swap the photo
CROP = (0.10, 0.03, 0.84)
CONTRAST = 1.12
BRIGHTNESS = 1.04


im = Image.open(INP).convert("RGBA")
w, h = im.size

left = int(w * CROP[0])
top = int(h * CROP[1])
side = int(w * CROP[2])
im = im.crop((left, top, left + side, top + side))

if remove is not None:
    session = new_session(os.getenv("REMBG_MODEL", "u2netp"))
    im = remove(im, session=session)
    alpha = im.split()[-1]
    gray = im.convert("L")
    # flatten onto white so the background maps to blank characters
    gray = Image.composite(gray, Image.new("L", gray.size, 255), alpha)
    # tone stretch over the subject only
    subject = alpha.point(lambda a: 255 if a > 128 else 0)
    box = subject.getbbox()
    if box:
        hist = gray.crop(box).histogram()
        total = sum(hist)
        acc = 0
        lo = hi = 0
        for value, count in enumerate(hist):
            acc += count
            if acc >= total * 0.02:
                lo = value
                break
        acc = 0
        for value, count in enumerate(hist):
            acc += count
            if acc >= total * 0.92:
                hi = value
                break
        if hi > lo:
            gray = gray.point(lambda p: max(0, min(255, int((p - lo) * 255 / (hi - lo)))))
    im = gray
else:
    im = im.convert("L")

# tame the background texture before it turns into ascii noise
im = im.filter(ImageFilter.MedianFilter(3))
im = im.filter(ImageFilter.GaussianBlur(1.0))
im = ImageOps.autocontrast(im, cutoff=1)
im = ImageEnhance.Contrast(im).enhance(CONTRAST)
im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)

im.save(OUT)
print("wrote", OUT, im.size, "(rembg on)" if remove else "(rembg off)")
