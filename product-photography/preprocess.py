#!/usr/bin/env python3
"""
LUMIÈRE — product photo preprocessing.

Takes the raw uploaded photos (mixed clean shots / phone screenshots /
catalog pages), removes UI chrome and letterbox bars, crops a square
window centred on the jewelry and upscales it to a uniform size with
Lanczos + a gentle unsharp mask. The jewelry pixels themselves are never
regenerated or altered — only cropped, resized and lightly sharpened.

Usage: python3 preprocess.py <input_dir> <output_dir>
"""
import sys, glob, os
from PIL import Image, ImageFilter, ImageOps

TARGET = 2530  # square size of the product window inside the 4096 canvas

# Per-photo tuning. Keys are photo numbers.
#   top/bottom : extra pixels to cut AFTER the auto bar-trim (UI banners, captions)
#   fx/fy      : focus point of the square crop as a fraction of the trimmed image
#   mode       : 'cover' (default, crop to square) or 'contain' (fit whole image,
#                pad with blurred edge extension — for wide bracelets etc.)
TUNE = {
    2:  dict(fy=0.42),
    3:  dict(top=260, fy=0.45),
    4:  dict(fy=0.40),
    7:  dict(fy=0.45),
    8:  dict(fy=0.35),
    9:  dict(fx=0.44, fy=0.42),
    11: dict(fx=0.44),
    21: dict(mode='contain'),
    22: dict(fx=0.55, fy=0.42),
    24: dict(top=185, fy=0.55),
    25: dict(top=175, fy=0.38),
    26: dict(top=120, bottom=160, fy=0.30, zoom=1.1),
    27: dict(top=170, fy=0.50, zoom=1.42),
    28: dict(fy=0.50),
    29: dict(top=230, fy=0.45),
    30: dict(top=130, bottom=140, fy=0.48, fx=0.50, zoom=1.5),
    31: dict(top=150, fy=0.55, fx=0.45, zoom=1.45),
    32: dict(fy=0.52),
    33: dict(top=180, bottom=260, fy=0.45, zoom=1.3),
    34: dict(top=160, fy=0.50),
    35: dict(top=100, fy=0.62),
    36: dict(top=100, fy=0.45),
    37: dict(top=100),
    38: dict(top=175, fy=0.45),
    39: dict(top=100, fy=0.60),
    40: dict(top=100, fy=0.42, fx=0.45, zoom=1.05),
    41: dict(top=60, fy=0.32),
    42: dict(top=80, fy=0.34),
    43: dict(top=100, fy=0.48),
    44: dict(top=230, fy=0.45),
    45: dict(top=430, fy=0.55, bottom=190, fx=0.60, zoom=1.25),
    46: dict(top=100, fy=0.45),
    47: dict(top=100, fy=0.58),
    49: dict(top=100, fy=0.36, fx=0.42, zoom=1.25),
    50: dict(top=60, zoom=1.05),
}

def trim_bars(im, thresh_dark=28, thresh_light=248, min_run=8):
    """Trim near-black or near-white letterbox bars from top/bottom/left/right."""
    g = im.convert('L')
    w, h = g.size
    px = g.load()

    def row_uniform(y):
        vals = [px[x, y] for x in range(0, w, max(1, w // 60))]
        avg = sum(vals) / len(vals)
        spread = max(vals) - min(vals)
        return (avg < thresh_dark or avg > thresh_light) and spread < 24

    def col_uniform(x):
        vals = [px[x, y] for y in range(0, h, max(1, h // 60))]
        avg = sum(vals) / len(vals)
        spread = max(vals) - min(vals)
        return (avg < thresh_dark or avg > thresh_light) and spread < 24

    top = 0
    while top < h * 0.45 and row_uniform(top):
        top += 1
    bot = h - 1
    while bot > h * 0.55 and row_uniform(bot):
        bot -= 1
    left = 0
    while left < w * 0.3 and col_uniform(left):
        left += 1
    right = w - 1
    while right > w * 0.7 and col_uniform(right):
        right -= 1
    if top < min_run: top = 0
    if h - 1 - bot < min_run: bot = h - 1
    if left < min_run: left = 0
    if w - 1 - right < min_run: right = w - 1
    return im.crop((left, top, right + 1, bot + 1))

def square_cover(im, fx, fy, zoom=1.0):
    w, h = im.size
    side = int(min(w, h) / zoom)
    cx, cy = int(w * fx), int(h * fy)
    x0 = max(0, min(w - side, cx - side // 2))
    y0 = max(0, min(h - side, cy - side // 2))
    return im.crop((x0, y0, x0 + side, y0 + side))

def square_contain(im):
    """Fit the whole image on a square canvas extended with a blurred,
    brightened copy of itself so the padding blends with the photo."""
    w, h = im.size
    side = max(w, h)
    bg = im.resize((side, side), Image.LANCZOS).filter(ImageFilter.GaussianBlur(60))
    canvas = bg.copy()
    canvas.paste(im, ((side - w) // 2, (side - h) // 2))
    return canvas

def process(path, num, out_dir):
    im = Image.open(path).convert('RGB')
    im = ImageOps.exif_transpose(im)
    t = TUNE.get(num, {})
    im = trim_bars(im)
    top, bottom = t.get('top', 0), t.get('bottom', 0)
    if top or bottom:
        im = im.crop((0, top, im.width, im.height - bottom))
    if t.get('mode') == 'contain':
        sq = square_contain(im)
    else:
        sq = square_cover(im, t.get('fx', 0.5), t.get('fy', 0.45), t.get('zoom', 1.0))
    sq = sq.resize((TARGET, TARGET), Image.LANCZOS)
    sq = sq.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))
    out = os.path.join(out_dir, f"product_{num:02d}.jpg")
    sq.save(out, quality=95)
    return out

def main():
    in_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(in_dir, 'photo_*.jpg')),
                   key=lambda f: int(os.path.basename(f).split('_')[1]))
    for f in files:
        num = int(os.path.basename(f).split('_')[1])
        out = process(f, num, out_dir)
        print(f"{os.path.basename(f)} -> {os.path.basename(out)}")

if __name__ == '__main__':
    main()
