#!/usr/bin/env python3
"""
LOMOND — studio background replacement.

Removes the original background from jewelry-only shots (flat lays, catalog
pages, clean surfaces) and re-shoots them on a seamless studio backdrop with
a softbox-style gradient and a realistic grounding shadow.

Method: classical color-distance keying + closed-form alpha matting
(pymatting). Fully deterministic — the jewelry pixels are never generated
or re-rendered, only masked and composited.

Usage: python3 studio.py [--color cream|burgundy] [nums...]
"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter
from pymatting import estimate_alpha_cf, estimate_foreground_ml

SRC_DIR = 'public/products'
OUT_ROOT = '../store-assets/products-studio'
CANVAS = 4096
WORK = 1400          # matting resolution (memory-bound), upsampled after

# Pieces where the jewelry is the isolated subject on a keyable background.
#   lo/hi : color-distance thresholds (fraction of max) for bg / fg
#   dark  : background is darker than the piece
# crop = (left, top, right, bottom) fractions trimmed from the source before
# keying — removes catalog panel borders / caption strips that would key as fg.
CANDIDATES = {
    21: dict(lo=0.06, hi=0.20),                                  # bracelet, white
    27: dict(lo=0.08, hi=0.25, crop=(0, 0, 0, 0.06)),            # gold huggies, cream panel
    28: dict(lo=0.08, hi=0.22, crop=(0.03, 0.14, 0.03, 0.10)),   # gold bracelet, white
    29: dict(lo=0.06, hi=0.20, crop=(0, 0.03, 0.05, 0.18)),      # pearl bracelet, white
    31: dict(lo=0.06, hi=0.20, crop=(0.04, 0.04, 0.10, 0.14)),   # snowflake pendant
    32: dict(lo=0.06, hi=0.20, crop=(0.10, 0.16, 0.14, 0.18)),   # gold pendant
    33: dict(lo=0.08, hi=0.22, crop=(0, 0, 0, 0.08)),                                  # pear earrings
}

BACKDROPS = {
    'cream':    dict(top=(247,240,232), mid=(238,228,218), bot=(223,210,194),
                     glow=(255,255,255,110), shadow_op=115),
    'burgundy': dict(top=(107,32,39),  mid=(77,14,19),  bot=(56,9,13),
                     glow=(255,222,200,46), shadow_op=150, alpha_boost=1.45),
}

def estimate_bg(im_arr):
    """Median color of the image border ring."""
    b = 24
    ring = np.concatenate([
        im_arr[:b].reshape(-1,3), im_arr[-b:].reshape(-1,3),
        im_arr[:, :b].reshape(-1,3), im_arr[:, -b:].reshape(-1,3)])
    return np.median(ring, axis=0)

def cutout(path, lo, hi, crop=None):
    im = Image.open(path).convert('RGB')
    if crop:
        l, t, r, b = crop
        im = im.crop((int(im.width*l), int(im.height*t),
                      int(im.width*(1-r)), int(im.height*(1-b))))
    W, H = im.size
    scale = WORK / max(W, H)
    w2, h2 = int(W*scale), int(H*scale)
    im_small = im.resize((w2, h2), Image.LANCZOS)
    a = np.asarray(im_small).astype(np.float64)
    bg = estimate_bg(a)
    dist = np.linalg.norm(a - bg, axis=2) / 441.7
    # build trimap: 0 = bg, 1 = fg, 0.5 = unknown
    fg_mask = Image.fromarray(((dist > hi) * 255).astype(np.uint8))
    bg_mask = Image.fromarray(((dist < lo) * 255).astype(np.uint8))
    fg_core = fg_mask.filter(ImageFilter.MinFilter(5))    # erode
    bg_core = bg_mask.filter(ImageFilter.MinFilter(9))
    trimap = np.full((h2, w2), 0.5)
    trimap[np.asarray(bg_core) > 128] = 0.0
    trimap[np.asarray(fg_core) > 128] = 1.0
    alpha = estimate_alpha_cf(a / 255.0, trimap)
    fg = estimate_foreground_ml(a / 255.0, alpha)
    # upsample alpha+fg back to native res, use native pixels where alpha≈1
    native = np.asarray(im).astype(np.float64) / 255.0
    alpha_full = np.asarray(Image.fromarray((alpha*255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(np.float64)/255.0
    fg_full = np.asarray(Image.fromarray((np.clip(fg,0,1)*255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(np.float64)/255.0
    solid = alpha_full > 0.97
    out = fg_full.copy()
    out[solid] = native[solid]          # untouched original pixels inside the piece
    rgba = np.dstack([np.clip(out,0,1)*255, alpha_full*255]).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')

def make_backdrop(spec):
    top, mid, bot = np.array(spec['top']), np.array(spec['mid']), np.array(spec['bot'])
    ys = np.linspace(0, 1, CANVAS)
    col = np.where(ys[:, None] < 0.5,
                   top + (mid-top) * np.clip(ys[:, None]*2, 0, 1),
                   mid + (bot-mid) * np.clip(ys[:, None]*2-1, 0, 1))
    grad = np.repeat(col[:, None, :], CANVAS, axis=1)
    # soft studio light from top-left (very broad gaussian brightness field)
    yy, xx = np.mgrid[0:CANVAS, 0:CANVAS] / CANVAS
    light = np.exp(-(((xx-0.30)**2 + (yy-0.18)**2) / 0.55))
    vign  = np.exp(-(((xx-0.5)**2 + (yy-0.55)**2) / 1.4))
    field = (0.92 + 0.10*light) * (0.94 + 0.06*vign)
    grad = np.clip(grad * field[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(grad).convert('RGBA')

def compose(piece, spec):
    bgim = make_backdrop(spec)
    # scale piece so its longest side spans 66% of the canvas
    target = int(CANVAS * 0.66)
    s = target / max(piece.size)
    p = piece.resize((int(piece.width*s), int(piece.height*s)), Image.LANCZOS)
    boost = spec.get('alpha_boost', 1.0)
    if boost != 1.0:
        ch = list(p.split())
        ch[3] = ch[3].point(lambda v: min(255, int(v*boost)))
        p = Image.merge('RGBA', ch)
    target_w = p.width
    a = np.asarray(p.split()[3])
    ys, xs = np.where(a > 10)
    if len(ys) == 0:
        return None
    px = CANVAS//2 - (xs.min()+xs.max())//2
    py = int(CANVAS*0.47) - (ys.min()+ys.max())//2   # optical centre slightly high
    px = max(-xs.min(), min(px, CANVAS - xs.max() - 1))
    py = max(-ys.min(), min(py, CANVAS - ys.max() - 200))
    bottom = py + ys.max()
    # grounding shadow from the alpha silhouette (light: top-left → shadow: bottom-right)
    sil = Image.fromarray(a)
    for squash, blur, op_mul, dx, dy in [(0.16, 90, 1.0, 70, 0), (0.06, 30, 1.35, 30, 0)]:
        sh_h = max(1, int(target_w*squash))
        sh = sil.resize((target_w, sh_h)).filter(ImageFilter.GaussianBlur(blur))
        sh_arr = (np.asarray(sh).astype(np.float64) * (spec['shadow_op']*op_mul/255.0)).astype(np.uint8)
        shadow = Image.new('RGBA', (CANVAS, CANVAS), (0,0,0,0))
        black = Image.new('RGBA', (target_w, sh_h), (10, 5, 5, 255))
        shadow.paste(black, (px+dx, bottom - sh_h//2 + dy), Image.fromarray(sh_arr))
        bgim = Image.alpha_composite(bgim, shadow)
    bgim.paste(p, (px, py), p)
    return bgim.convert('RGB')

def main():
    args = sys.argv[1:]
    color = 'cream'
    if '--color' in args:
        i = args.index('--color'); color = args[i+1]; args = args[:i]+args[i+2:]
    nums = [int(x) for x in args] if args else sorted(CANDIDATES)
    spec = BACKDROPS[color]
    out_dir = os.path.join(OUT_ROOT, color)
    os.makedirs(out_dir, exist_ok=True)
    for n in nums:
        p = CANDIDATES[n]
        piece = cutout(os.path.join(SRC_DIR, f'product_{n:02d}.jpg'), p['lo'], p['hi'], p.get('crop'))
        img = compose(piece, spec)
        out = os.path.join(out_dir, f'lomond_studio_{n:02d}.jpg')
        img.save(out, quality=94)
        print(out)

if __name__ == '__main__':
    main()
