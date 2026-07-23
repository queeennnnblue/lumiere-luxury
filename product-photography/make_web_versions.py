#!/usr/bin/env python3
"""Create 1600x1600 web-optimized versions of the 4K masters for the store."""
import glob, os, sys
from PIL import Image

src_dir = sys.argv[1] if len(sys.argv) > 1 else '../store-assets/products-4k'
out_dir = sys.argv[2] if len(sys.argv) > 2 else '../store-assets/products-web'
os.makedirs(out_dir, exist_ok=True)
for f in sorted(glob.glob(os.path.join(src_dir, 'lomond_*.jpg'))):
    im = Image.open(f)
    im = im.resize((1600, 1600), Image.LANCZOS)
    out = os.path.join(out_dir, os.path.basename(f))
    im.save(out, quality=84, optimize=True, progressive=True)
    print(os.path.basename(out))
