#!/usr/bin/env python3
"""
02 — تنزيل صور المنتجات ومعالجتها لمقاس زد الموحّد.
Download supplier images and normalise them for Zid.

  • الأصل ينزّل كما هو إلى images/original/ ولا يُعدَّل
  • التسمية: lomond-{sku}-{01}.jpg — ممنوع أي أثر لاسم المصدر
  • تُمسح كل بيانات EXIF
  • المقاس 2000×2000 مربع، خلفية بيضاء نظيفة، مع الحفاظ على النسبة
  • الترقية: Real-ESRGAN محلياً فقط، وللصور الأقل من 1200px، وبطلب صريح

    python scripts/02_images.py --limit 3          # ٣ منتجات تجريبية أولاً
    python scripts/02_images.py [--dry-run] [--force] [--upscale]
"""

from __future__ import annotations

import shutil
import subprocess
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
    env_int,
    load_stage,
    log,
    step,
    warn,
    wants_dry_run,
)

try:
    from PIL import Image, ImageChops, ImageOps
except ImportError:
    Image = None

UPSCALE_THRESHOLD = 1200  # أقل من هذا يُرشَّح للترقية
CANVAS_BG = (255, 255, 255)  # خلفية بيضاء نظيفة


# ------------------------------------------------------------------ التنزيل
def download(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    req = urllib.request.Request(url, headers={
        "User-Agent": env("USER_AGENT", "LomondImporter/1.0"),
    })
    try:
        with urllib.request.urlopen(req, timeout=env_int("SCRAPE_TIMEOUT", 30)) as resp:
            dest.write_bytes(resp.read())
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        warn(f"تعذّر تنزيل الصورة | download failed: {url[:60]} — {exc}")
        return False


# ------------------------------------------------------------------ الترقية
def upscale(src: Path, scale: int = 2) -> Path:
    """
    Real-ESRGAN محلياً فقط. إن لم يكن مثبّتاً نتخطّى بصمت ونُبقي الأصل.
    ملاحظة: الترقية لا تضيف تفاصيل غير موجودة، تكبّر وتنعّم فقط.
    """
    binary = shutil.which("realesrgan-ncnn-vulkan")
    if not binary:
        warn("Real-ESRGAN غير مثبّت، نكمل بالأصل | not installed, using original")
        return src

    out = src.with_name(src.stem + f"_x{scale}.png")
    if out.exists():
        return out
    try:
        subprocess.run(
            [binary, "-i", str(src), "-o", str(out), "-s", str(scale), "-n", "realesrgan-x4plus"],
            check=True, capture_output=True, timeout=300,
        )
        return out
    except (subprocess.SubprocessError, OSError) as exc:
        warn(f"فشلت الترقية | upscale failed: {src.name} — {exc}")
        return src


# ------------------------------------------------------------------ المعالجة
def process(src: Path, dest: Path, size: int, quality: int) -> tuple[int, int] | None:
    """
    يقصّ الهوامش البيضاء، يحافظ على نسبة القطعة، ويضعها وسط مربع size×size أبيض.
    الحفظ عبر لوحة جديدة يعني أن الناتج بلا أي EXIF.
    """
    try:
        with Image.open(src) as img:
            img = ImageOps.exif_transpose(img)  # يطبّق دوران EXIF ثم نتخلّص منه

            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                flat = Image.new("RGB", img.size, CANVAS_BG)
                flat.paste(img, mask=img.split()[-1])
                img = flat
            else:
                img = img.convert("RGB")

            # قصّ الهامش الأبيض حتى تحيط الحدود بالقطعة فقط
            mask = ImageChops.difference(img, Image.new("RGB", img.size, CANVAS_BG)).convert("L")
            bbox = mask.point(lambda p: 255 if p > 12 else 0).getbbox()
            if bbox:
                img = img.crop(bbox)

            # thumbnail يحافظ على النسبة الأصلية بلا تشويه
            img.thumbnail((size, size), Image.LANCZOS)

            canvas = Image.new("RGB", (size, size), CANVAS_BG)
            canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
            canvas.save(dest, "JPEG", quality=quality, optimize=True, subsampling=0)
        return (size, size)
    except OSError as exc:
        warn(f"تعذّرت المعالجة | processing failed: {src.name} — {exc}")
        return None


def dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with Image.open(path) as img:
            return img.size
    except OSError:
        return None


# ------------------------------------------------------------------ التقرير
def print_table(rows: list[dict]) -> None:
    print("\n" + "═" * 84)
    print("  جدول الصور | image table")
    print("═" * 84)
    print(f"  {'الملف | file':30} {'قبل | before':>14} {'بعد | after':>14} {'ترقية':>8} {'الحالة':>10}")
    print("  " + "─" * 80)
    for row in rows:
        before = f"{row['before'][0]}×{row['before'][1]}" if row["before"] else "—"
        after = f"{row['after'][0]}×{row['after'][1]}" if row["after"] else "—"
        flag = "نعم" if row["upscaled"] else ("مرشّح" if row["low_res"] else "—")
        print(f"  {row['name'][:30]:30} {before:>14} {after:>14} {flag:>8} {row['status']:>10}")
    print("  " + "─" * 80)

    low = [r for r in rows if r["low_res"] and not r["upscaled"]]
    if low:
        print(f"\n  ⚠ {len(low)} صورة أقل من {UPSCALE_THRESHOLD}px:")
        for row in low[:10]:
            print(f"     {row['name']}  ({row['before'][0]}×{row['before'][1]})")
        print("\n  الترقية تكبّر وتنعّم، لا تضيف تفاصيل. الحل الصحيح طلب ملفات")
        print("  أعلى دقة من المورّد بدل الترقية.")
    print("═" * 84 + "\n")


# ------------------------------------------------------------------ التشغيل
def main() -> int:
    ensure_dirs()
    dry = wants_dry_run()
    force = "--force" in sys.argv
    do_upscale = "--upscale" in sys.argv

    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    if Image is None and not dry:
        warn("Pillow غير مثبّت | Pillow missing — pip install -r requirements.txt")
        return 1

    size = env_int("IMAGE_SIZE", 2000)
    quality = env_int("IMAGE_QUALITY", 90)

    products = load_stage(RAW_DIR)
    if not products:
        warn("لا توجد بيانات خام — شغّل 01_scrape.py أولاً")
        return 1

    if limit:
        products = products[:limit]
        log(f"وضع تجريبي: {len(products)} منتج فقط | trial run")

    rows: list[dict] = []
    failed = 0

    for product in products:
        sku = product.get("sku") or product.get("supplier_id") or "nosku"
        urls = product.get("images") or []
        if not urls:
            warn(f"بلا صور | no images: {product.get('title', '')[:40]}")
            continue

        step(f"{product.get('title', '')[:46]} — {len(urls)} صورة")

        for n, url in enumerate(urls, start=1):
            # اسم الملف لا يحمل أي أثر للمورّد
            stem = f"lomond-{sku}-{n:02d}"
            suffix = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
            original = IMG_ORIGINAL / f"{stem}{suffix}"
            final = IMG_PROCESSED / f"{stem}.jpg"

            row = {"name": final.name, "before": None, "after": None,
                   "upscaled": False, "low_res": False, "status": ""}

            if final.exists() and not force:
                row["before"] = dimensions(original)
                row["after"] = dimensions(final)
                row["status"] = "موجود"
                rows.append(row)
                continue

            if dry:
                row["status"] = "معاينة"
                rows.append(row)
                continue

            if not download(url, original):
                row["status"] = "فشل ✗"
                failed += 1
                rows.append(row)
                continue

            before = dimensions(original)
            row["before"] = before
            row["low_res"] = bool(before and min(before) < UPSCALE_THRESHOLD)

            source = original
            if row["low_res"] and do_upscale:
                source = upscale(original)
                row["upscaled"] = source != original

            after = process(source, final, size, quality)
            row["after"] = after
            row["status"] = "تم ✓" if after else "فشل ✗"
            if not after:
                failed += 1
            rows.append(row)

    print_table(rows)

    if dry:
        log("معاينة فقط، لم يُكتب أي ملف | dry run, nothing written")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
