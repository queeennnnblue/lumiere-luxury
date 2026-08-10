#!/usr/bin/env python3
"""
02 — تنزيل صور المنتجات ومعالجتها إلى مقاس زد الموحّد
Download supplier images and normalise them for Zid.

الأصل يُحفظ كما هو في images/original/ ولا يُعدَّل.
المعالَج في images/processed/: 2000×2000، خلفية موحّدة، القطعة تملأ ~85%.

    python scripts/02_images.py [--dry-run] [--force]
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    IMG_ORIGINAL,
    IMG_PROCESSED,
    RAW_DIR,
    ensure_dirs,
    env,
    env_float,
    env_int,
    load_stage,
    log,
    step,
    warn,
    wants_dry_run,
)

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = (value or "#FFFFFF").lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def download(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    req = urllib.request.Request(url, headers={"User-Agent": env("USER_AGENT", "Mozilla/5.0")})
    try:
        with urllib.request.urlopen(req, timeout=env_int("SCRAPE_TIMEOUT", 30)) as resp:
            dest.write_bytes(resp.read())
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        warn(f"تعذّر تنزيل الصورة | image download failed: {url} — {exc}")
        return False


def process(src: Path, dest: Path, size: int, bg: tuple[int, int, int], fill: float, quality: int) -> bool:
    """يقصّ الهوامش الفارغة، يوحّد الخلفية، ويضع القطعة في مربّع size×size."""
    try:
        with Image.open(src) as img:
            img = ImageOps.exif_transpose(img)

            # الشفافية تُدمج على الخلفية الموحّدة قبل أي قصّ
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                flat = Image.new("RGB", img.size, bg)
                flat.paste(img, mask=img.split()[-1])
                img = flat
            else:
                img = img.convert("RGB")

            # قصّ الهوامش المطابقة للخلفية حتى تحيط الحدود بالقطعة فقط
            flat_bg = Image.new("RGB", img.size, bg)
            mask = ImageChops.difference(img, flat_bg).convert("L")
            bbox = mask.point(lambda p: 255 if p > 12 else 0).getbbox()
            if bbox:
                img = img.crop(bbox)

            # تصغير القطعة لتملأ النسبة المطلوبة من الإطار
            target = int(size * fill)
            img.thumbnail((target, target), Image.LANCZOS)

            canvas = Image.new("RGB", (size, size), bg)
            canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
            # الحفظ بلا EXIF — Image.new لا يحمل أي بيانات وصفية
            canvas.save(dest, "JPEG", quality=quality, optimize=True, subsampling=0)
        return True
    except OSError as exc:
        warn(f"تعذّرت معالجة الصورة | processing failed: {src.name} — {exc}")
        return False


def main() -> int:
    ensure_dirs()
    dry = wants_dry_run()
    force = "--force" in sys.argv

    if Image is None and not dry:
        warn("Pillow غير مثبّت | Pillow missing — pip install -r requirements.txt")
        return 1

    size = env_int("IMAGE_SIZE", 2000)
    quality = env_int("IMAGE_QUALITY", 90)
    fill = env_float("IMAGE_FILL", 0.85)
    bg = hex_to_rgb(env("IMAGE_BG", "#FFFFFF"))

    products = load_stage(RAW_DIR)
    if not products:
        warn("لا توجد بيانات خام — شغّل 01_scrape.py أولاً")
        return 1

    downloaded = processed = reused = failed = 0

    for product in products:
        sku = product.get("sku") or product.get("supplier_id") or ""
        title = product.get("title", "")[:40]
        urls = product.get("images") or []
        if not urls:
            warn(f"بلا صور | no images: {title}")
            continue

        step(f"{title} — {len(urls)} صورة")
        for n, url in enumerate(urls, start=1):
            suffix = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
            stem = f"{sku or 'noskus'}_{n}"
            original = IMG_ORIGINAL / f"{stem}{suffix}"
            final = IMG_PROCESSED / f"{stem}.jpg"

            if final.exists() and not force:
                reused += 1
                continue

            if dry:
                log(f"[معاينة] {url[:60]}… → {final.name}")
                continue

            if not download(url, original):
                failed += 1
                continue
            downloaded += 1

            if process(original, final, size, bg, fill, quality):
                processed += 1
                log(f"{final.name}  ({size}×{size})")
            else:
                failed += 1

    step(
        f"تم | done — نُزّل {downloaded}، عولج {processed}، "
        f"موجود مسبقاً {reused}، فشل {failed}"
    )
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
