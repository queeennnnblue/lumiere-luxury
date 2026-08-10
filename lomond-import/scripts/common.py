"""
أدوات مشتركة بين سكربتات خط الاستيراد.
Shared helpers for the LOMOND import pipeline: paths, config, JSON I/O, Zid schema.
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- المسارات
ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = ROOT / "data" / "raw"
FINAL_DIR = ROOT / "data" / "final"
IMG_ORIGINAL = ROOT / "images" / "original"
IMG_PROCESSED = ROOT / "images" / "processed"
OUTPUT_DIR = ROOT / "output"
SOURCES_FILE = ROOT / "sources.txt"
SAMPLE_CSV = ROOT / "zid_sample.csv"
OUTPUT_CSV = OUTPUT_DIR / "lomond_products.csv"


def ensure_dirs() -> None:
    for d in (RAW_DIR, FINAL_DIR, IMG_ORIGINAL, IMG_PROCESSED, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- الإعدادات
def _load_dotenv() -> None:
    """قارئ .env بسيط بلا اعتماديات خارجية. Minimal .env reader, no dependencies."""
    for name in (".env", ".env.example"):
        path = ROOT / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            # قيم .env تسبق .env.example ولا تُدهس متغيرات البيئة الحقيقية
            os.environ.setdefault(key.strip(), value.strip())
        if name == ".env":
            break


_load_dotenv()


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, "") or default)
    except ValueError:
        return default


def env_int(key: str, default: int) -> int:
    try:
        return int(float(os.environ.get(key, "") or default))
    except ValueError:
        return default


# ---------------------------------------------------------------- الإدخال والإخراج
def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_stage(directory: Path) -> list[dict]:
    """يقرأ كل ملفات JSON في مجلد مرحلة، مرتّبة باسم الملف."""
    return [read_json(p) for p in sorted(directory.glob("*.json"))]


def log(msg: str) -> None:
    print(f"  {msg}", flush=True)


def step(msg: str) -> None:
    print(f"\n▸ {msg}", flush=True)


def warn(msg: str) -> None:
    print(f"  ⚠ {msg}", file=sys.stderr, flush=True)


def polite_sleep() -> None:
    """تأخير بين الطلبات احتراماً لخوادم الموردين."""
    base = env_float("SCRAPE_DELAY", 2.0)
    time.sleep(base + random.uniform(0, base * 0.4))


# ---------------------------------------------------------------- نصوص
_SLUG_STRIP = re.compile(r"[^\w؀-ۿ\s-]", re.UNICODE)


def slugify_ar(text: str) -> str:
    """رابط صفحة المنتج: الاسم العربي بشرطات بدل المسافات (كما في تصدير زد)."""
    text = unicodedata.normalize("NFKC", text or "").strip()
    text = _SLUG_STRIP.sub("", text)
    return re.sub(r"[\s_-]+", "-", text).strip("-")


def make_sku(seed: str | None = None) -> str:
    """معرّف بصيغة زد: Z. متبوعة بـ 17 رقماً."""
    rng = random.Random(seed) if seed else random
    return "Z." + "".join(str(rng.randint(0, 9)) for _ in range(17))


# ---------------------------------------------------------------- التصنيفات
CATEGORIES = {
    "rings": ("[الخواتم]", "[Diamond Ring]"),
    "earrings": ("[الأقراط]", "[Diamond Earrings]"),
    "necklaces": ("[العقود]", "[Diamond Necklace]"),
    "bracelets": ("[الأساور]", "[Diamond Bracelet]"),
}

# كلمات دلالية لتخمين التصنيف من اسم المنتج
_CATEGORY_HINTS = {
    "rings": ("ring", "خاتم", "خواتم"),
    "earrings": ("earring", "stud", "climber", "قرط", "أقراط", "اقراط", "حلق"),
    "necklaces": ("necklace", "pendant", "عقد", "قلادة", "سلسال"),
    "bracelets": ("bracelet", "bangle", "أسورة", "اسورة", "أساور", "اسوارة"),
}


def guess_category(*texts: str) -> str | None:
    haystack = " ".join(t for t in texts if t).lower()
    for key, hints in _CATEGORY_HINTS.items():
        if any(h in haystack for h in hints):
            return key
    return None


# ---------------------------------------------------------------- مخطط زد
# ترتيب الأعمدة مأخوذ حرفياً من تصدير زد الحقيقي (zid_sample.csv).
# لا يُضاف عمود ولا يُحذف ولا يُعاد ترتيبه.
ZID_COLUMNS = [
    "sku",
    "barcode",
    "has_variants",
    "name_ar",
    "name_en",
    "description_ar",
    "description_en",
    "short_description_ar",
    "short_description_en",
    "product_page_title_ar",
    "product_page_title_en",
    "product_page_description_ar",
    "product_page_description_en",
    "product_page_url",
    "quantity",
    "categories_ar",
    "categories_en",
    "categories_description_ar",
    "categories_description_en",
    "categories_images",
    "keywords",
    "weight",
    "weight_unit",
    "published",
    "option1_name_ar",
    "option1_name_en",
    "option1_value_ar",
    "option1_value_en",
    "option2_name_ar",
    "option2_name_en",
    "option2_value_ar",
    "option2_value_en",
    "option3_name_ar",
    "option3_name_en",
    "option3_value_ar",
    "option3_value_en",
    "price",
    "sale_price",
    "cost",
    "images",
    "images_alt_text_ar",
    "images_alt_text_en",
    "has_dropdown",
    "is_dropdown_required",
    "dropdown_name_ar",
    "dropdown_name_en",
    "dropdown_choice1_ar",
    "dropdown_choice1_en",
    "dropdown_choice1_price",
    "dropdown_choice2_ar",
    "dropdown_choice2_en",
    "dropdown_choice2_price",
    "has_multiple_options",
    "is_multiple_options_required",
    "multiple_options_name_ar",
    "multiple_options_name_en",
    "has_text_input",
    "is_text_input_required",
    "text_input_name_ar",
    "text_input_name_en",
    "text_input_price",
    "has_numerical_input",
    "is_numerical_input_required",
    "numerical_input_name_ar",
    "numerical_input_name_en",
    "numerical_input_price",
    "has_date",
    "is_date_required",
    "date_name_ar",
    "date_name_en",
    "has_time",
    "is_time_required",
    "time_name_ar",
    "time_name_en",
    "has_image_upload",
    "is_image_upload_required",
    "image_upload_name_ar",
    "image_upload_name_en",
    "has_file_upload",
    "is_file_upload_required",
    "file_upload_name_ar",
    "file_upload_name_en",
]


def blank_row() -> dict:
    """صف زد فارغ بكل الأعمدة — نقطة البداية لأي منتج."""
    return {col: "" for col in ZID_COLUMNS}


# ---------------------------------------------------------------- CLI
def wants_dry_run(argv: list[str] | None = None) -> bool:
    argv = argv if argv is not None else sys.argv[1:]
    return "--dry-run" in argv or "-n" in argv
