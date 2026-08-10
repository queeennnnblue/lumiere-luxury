#!/usr/bin/env python3
"""
03 — صياغة محتوى المنتج بالعربي والإنجليزي حسب قواعد CLAUDE.md.
Generate LOMOND product copy (ar/en) from the raw supplier data.

يولّد لكل منتج:
  name_ar / name_en
  description_ar / description_en   (سطر افتتاحي + سطرين إحساس)
  specs                             (مهيكلة، والناقص MISSING)
  meta_title_ar/en · meta_description_ar/en
  category                          (من تصنيفات المتجر)

    python scripts/03_content.py --limit 3     # ٣ منتجات للمراجعة أولاً
    python scripts/03_content.py [--dry-run] [--force]
"""

from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    CATEGORIES,
    FINAL_DIR,
    RAW_DIR,
    SOURCES_FILE,
    ensure_dirs,
    guess_category,
    load_stage,
    log,
    make_sku,
    slugify_ar,
    step,
    warn,
    wants_dry_run,
    write_json,
)

MISSING = "MISSING"

# ---------------------------------------------------- قواعد صوت البراند
# عبارات تسويقية منفوخة، ممنوعة نصاً في CLAUDE.md
BANNED_PHRASES = [
    "تشكيلة فاخرة تجمع بين الأناقة والرقي",
    "لمسة ساحرة",
    "قطعة استثنائية تخطف الأنفاس",
    "تخطف الأنفاس",
    "لا مثيل لها",
    "تجمع بين الأناقة والرقي",
]

MAX_OPENING_WORDS = 15


def strip_em_dash(text: str) -> str:
    """ممنوع em dash في نصوص المنتجات."""
    text = (text or "").replace("—", "،").replace("–", "،")
    return re.sub(r"\s*،\s*،", "،", text).strip()


def check_voice(text: str) -> list[str]:
    issues = []
    for phrase in BANNED_PHRASES:
        if phrase in (text or ""):
            issues.append(f"عبارة ممنوعة: «{phrase}»")
    if "—" in (text or "") or "–" in (text or ""):
        issues.append("يحتوي em dash")
    return issues


# ------------------------------------------------------- تنظيف اسم المصدر
def supplier_terms() -> set[str]:
    """
    يبني قائمة الكلمات الممنوعة من نطاقات sources.txt.
    مثال: www.starsgemjewelry.com → starsgemjewelry, starsgem, stars gem
    """
    terms: set[str] = set()
    if not SOURCES_FILE.exists():
        return terms

    for line in SOURCES_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        host = urllib.parse.urlparse(line.split("|")[0].strip()).netloc
        host = host.replace("www.", "")
        label = host.split(".")[0]
        if not label:
            continue
        terms.add(label)
        terms.add(host)
        # نضيف الجذر بلا كلمة jewelry/gems ليغطي صيغ الاسم القصيرة
        for tail in ("jewelry", "jewellery", "gems", "gem"):
            if label.endswith(tail) and len(label) > len(tail) + 2:
                terms.add(label[: -len(tail)])
    return {t for t in terms if len(t) > 3}


def scrub_supplier(text: str, terms: set[str], extra: str = "") -> str:
    """يمسح أي ذكر لاسم المورّد أو نطاقه من النص."""
    if not text:
        return text
    cleaned = text
    blocklist = set(terms)
    if extra:
        blocklist.add(extra.lower())

    for term in sorted(blocklist, key=len, reverse=True):
        cleaned = re.sub(re.escape(term), "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"https?://\S+", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return re.sub(r"\s+([،.])", r"\1", cleaned).strip(" ،-|")


def find_leaks(text: str, terms: set[str]) -> list[str]:
    return [t for t in terms if t and re.search(re.escape(t), text or "", re.IGNORECASE)]


# ---------------------------------------------------------- المواصفات
# مفاتيح المواصفات المطلوبة حسب CLAUDE.md، مع مرادفات المصدر
SPEC_MAP = {
    "stone": (["stone", "gemstone", "diamond type", "نوع الحجر", "الحجر"], "نوع الحجر", "Stone"),
    "carat": (["carat", "ct", "total diamond weight", "diamond weight", "stone weight",
               "قيراط", "وزن الألماس", "وزن الحجر"], "القيراط", "Carat"),
    "clarity": (["clarity", "النقاء", "الصفاوة"], "النقاء", "Clarity"),
    "color": (["color", "colour", "color grade", "اللون"], "اللون", "Color"),
    "certificate": (["certificate", "certification", "igi", "gia", "الشهادة"], "الشهادة", "Certificate"),
    "metal": (["metal", "metal type", "gold purity", "material", "المعدن", "نوع المعدن", "عيار"], "المعدن", "Metal"),
    "size": (["size", "ring size", "length", "المقاس", "الطول", "الحجم"], "المقاس", "Size"),
    "weight": (["weight", "metal weight", "gold weight", "الوزن", "وزن المعدن"], "الوزن", "Weight"),
}


# مفاتيح مصدر تخصّ وزن الحجر، فلا تُحسب وزناً للمعدن
_STONE_WEIGHT_HINTS = ("diamond", "stone", "carat", "ألماس", "حجر", "قيراط")


def normalise_specs(raw_specs: dict, terms: set[str]) -> dict:
    """
    يطابق مواصفات المصدر مع المفاتيح المطلوبة.
    كل مفتاح مصدر يُستهلك مرة واحدة، فلا يُنسب وزن الألماس للمعدن مثلاً.
    الناقص يُكتب MISSING، ولا يُخترع أبداً.
    """
    lowered = {k.strip().lower(): str(v).strip() for k, v in (raw_specs or {}).items()}
    used: set[str] = set()
    specs = {}

    for key, (aliases, label_ar, label_en) in SPEC_MAP.items():
        value = MISSING
        for alias in aliases:
            for source_key, source_value in lowered.items():
                if source_key in used or not source_value or alias not in source_key:
                    continue
                # الوزن يعني وزن المعدن، لا وزن الحجر
                if key == "weight" and any(h in source_key for h in _STONE_WEIGHT_HINTS):
                    continue
                # «نوع الحجر» وصف، لا وزن. «Center Stone Weight» تخصّ القيراط
                if key == "stone" and any(h in source_key for h in ("weight", "carat", "وزن", "قيراط")):
                    continue
                value = scrub_supplier(source_value, terms) or MISSING
                if value != MISSING:
                    used.add(source_key)
                    break
            if value != MISSING:
                break
        specs[key] = {"label_ar": label_ar, "label_en": label_en, "value": value}

    return specs


def carat_number(value: str) -> str:
    """يستخرج الرقم من قيمة القيراط ليُضاف له وحدة واحدة فقط."""
    if not value or value == MISSING:
        return ""
    match = re.search(r"\d+(?:\.\d+)?", value)
    return match.group(0) if match else ""


def specs_html(specs: dict, lang: str) -> str:
    items = []
    for spec in specs.values():
        label = spec["label_ar"] if lang == "ar" else spec["label_en"]
        items.append(f"<li>{label}: {spec['value']}</li>")
    return "<ul>" + "".join(items) + "</ul>"


# ------------------------------------------------------------- الأسماء
# مفردات ترجمة الاسم إلى نمط لوموند الرسمي المختصر
SHAPE_AR = {
    "round": "دائري", "oval": "بيضاوي", "pear": "كمثري", "marquise": "ماركيز",
    "emerald": "زمردي", "cushion": "وسادة", "princess": "برنسس", "heart": "قلب",
    "radiant": "راديانت", "asscher": "آشر", "baguette": "باغيت",
}
TYPE_AR = {
    "ring": "خاتم", "band": "خاتم", "earring": "قرط", "earrings": "أقراط",
    "stud": "أقراط", "necklace": "عقد", "pendant": "قلادة", "bracelet": "أسورة",
    "bangle": "أسورة", "tennis": "تنس", "solitaire": "سوليتير", "halo": "هالو",
    "eternity": "إتيرنتي", "cluster": "عنقودي", "drop": "متدلي",
}
CATEGORY_NOUN_AR = {
    "rings": "خاتم", "earrings": "أقراط", "necklaces": "عقد", "bracelets": "أسورة",
}


def build_names(title_en: str, category: str | None, terms: set[str]) -> tuple[str, str]:
    """
    اسم رسمي مختصر بالعربي والإنجليزي.
    الإنجليزي يُنظَّف من اسم المورّد، والعربي يُبنى من مفردات النمط.
    """
    # ممنوع em dash في نصوص المنتجات، والاسم منها
    clean_en = strip_em_dash(scrub_supplier(title_en, terms))
    clean_en = re.sub(r"\s{2,}", " ", clean_en).strip(" -|،")
    words = re.findall(r"[A-Za-z]+", clean_en.lower())

    parts_ar = []
    noun = CATEGORY_NOUN_AR.get(category or "", "")
    if noun:
        parts_ar.append(noun)
    for word in words:
        if word in TYPE_AR and TYPE_AR[word] not in parts_ar:
            parts_ar.append(TYPE_AR[word])
        elif word in SHAPE_AR and SHAPE_AR[word] not in parts_ar:
            parts_ar.append(SHAPE_AR[word])

    name_ar = " ".join(dict.fromkeys(parts_ar))[:60] or MISSING
    name_en = " ".join(w.capitalize() for w in clean_en.split())[:60] or MISSING
    return name_ar, name_en


# ------------------------------------------------------------- الوصف
def build_description(name_ar: str, name_en: str, specs: dict, category: str | None) -> dict:
    """
    البنية من CLAUDE.md:
      ١. سطر افتتاحي واحد يصف القطعة، لا يزيد عن ١٥ كلمة
      ٢. سطران عن الإحساس أو مناسبة اللبس
    الإنجليزي مكتوب مستقلاً، لا ترجمة حرفية.
    """
    carat = specs["carat"]["value"]
    metal = specs["metal"]["value"]
    stone = specs["stone"]["value"]

    number = carat_number(carat)
    shape_ar = next((v for k, v in SHAPE_AR.items() if v in name_ar), "")
    carat_ar = f"{number} قيراط" if number else ""
    metal_ar = metal if metal != MISSING else ""

    bits_ar = [b for b in (shape_ar, carat_ar, metal_ar) if b]
    noun_ar = CATEGORY_NOUN_AR.get(category or "", "قطعة")
    opening_ar = f"{noun_ar} بحجر {'، '.join(bits_ar)}." if bits_ar else f"{noun_ar} من الألماس المزروع معملياً."

    # ضمان حد الـ ١٥ كلمة
    words = opening_ar.split()
    if len(words) > MAX_OPENING_WORDS:
        opening_ar = " ".join(words[:MAX_OPENING_WORDS])

    occasion_ar = {
        "rings": "يناسب اللبس اليومي، ويصلح خاتم مناسبة.\nمقاسه مريح ولا يعلق بالملابس.",
        "earrings": "خفيف على الأذن، تلبسينه من الصباح للسهرة.\nيمشي مع الشعر المرفوع والمنسدل.",
        "necklaces": "يستقر عند الترقوة، يبان مع الفتحات الواسعة والمقفلة.\nتلبسينه وحده أو فوق عقد ثاني.",
        "bracelets": "يلبس مع الساعة أو وحده.\nإغلاقه ثابت ويتحمل اللبس اليومي.",
    }.get(category or "", "قطعة تُلبس كل يوم.\nبسيطة وتناسب أغلب الإطلالات.")

    # الجمع يحتاج «A pair of»، والمفرد يحتاج «A»
    noun_en, article_en = {
        "rings": ("ring", "A"),
        "earrings": ("earrings", "A pair of"),
        "necklaces": ("necklace", "A"),
        "bracelets": ("bracelet", "A"),
    }.get(category or "", ("piece", "A"))

    bits_en = [b for b in (
        f"{number} ct" if number else "",
        metal if metal != MISSING else "",
    ) if b]
    opening_en = (
        f"{article_en} {noun_en} set with {', '.join(bits_en)}." if bits_en
        else f"{article_en} lab-grown diamond {noun_en}."
    )
    occasion_en = {
        "rings": "Easy enough for every day, dressed enough for an occasion.\nSits comfortably and never catches on fabric.",
        "earrings": "Light on the ear, from morning through the evening.\nWorks with hair up or down.",
        "necklaces": "Sits at the collarbone, visible with open and closed necklines.\nWear it alone or layered.",
        "bracelets": "Wear it beside a watch or on its own.\nThe clasp holds firm through daily wear.",
    }.get(category or "", "Made for everyday wear.\nSimple enough to suit most looks.")

    return {
        "description_ar": strip_em_dash(f"{opening_ar}\n{occasion_ar}"),
        "description_en": strip_em_dash(f"{opening_en}\n{occasion_en}"),
        "opening_ar": opening_ar,
        "opening_en": opening_en,
        "stone_note": stone,
    }


def html_paragraphs(text: str) -> str:
    lines = [line.strip() for line in (text or "").split("\n") if line.strip()]
    return "".join(f"<p>{line}</p>" for line in lines)


# ------------------------------------------------------------- التشغيل
def build_product(raw: dict, terms: set[str]) -> dict:
    vendor = raw.get("supplier_vendor", "")
    category = raw.get("category") or guess_category(raw.get("title", ""), raw.get("product_type", ""))

    name_ar, name_en = build_names(raw.get("title", ""), category, terms)
    specs = normalise_specs(raw.get("specs", {}), terms)
    desc = build_description(name_ar, name_en, specs, category)

    cat_ar, cat_en = CATEGORIES.get(category or "", ("", ""))

    meta_title_ar = f"{name_ar} | لوموند" if name_ar != MISSING else MISSING
    meta_title_en = f"{name_en} | LOMOND" if name_en != MISSING else MISSING
    meta_desc_ar = desc["opening_ar"][:155]
    meta_desc_en = desc["opening_en"][:155]

    product = {
        "sku": raw.get("sku") or make_sku(seed=raw.get("source_url", "")),
        "source_url": raw.get("source_url", ""),
        "category": category or MISSING,
        "categories_ar": cat_ar,
        "categories_en": cat_en,
        "name_ar": name_ar,
        "name_en": name_en,
        "description_ar": html_paragraphs(desc["description_ar"]),
        "description_en": html_paragraphs(desc["description_en"]),
        "short_description_ar": specs_html(specs, "ar"),
        "short_description_en": specs_html(specs, "en"),
        "meta_title_ar": meta_title_ar,
        "meta_title_en": meta_title_en,
        "meta_description_ar": meta_desc_ar,
        "meta_description_en": meta_desc_en,
        "product_page_url": slugify_ar(name_ar) if name_ar != MISSING else MISSING,
        "specs": specs,
        "purchase_usd": raw.get("price_usd"),
        "images_count": len(raw.get("images") or []),
    }

    # فحص التسريب والنبرة على كل الحقول النصية
    text_fields = " ".join(
        str(v) for k, v in product.items()
        if isinstance(v, str) and k not in ("source_url", "sku")
    )
    product["_leaks"] = find_leaks(text_fields, terms | ({vendor.lower()} if vendor else set()))
    product["_voice_issues"] = check_voice(text_fields)
    product["_missing"] = [k for k, s in specs.items() if s["value"] == MISSING]
    return product


def preview(product: dict) -> None:
    print("\n" + "─" * 70)
    print(f"  {product['name_ar']}   |   {product['name_en']}")
    print("─" * 70)
    print(f"  التصنيف : {product['categories_ar']} {product['categories_en']}")
    print(f"  الرابط  : {product['product_page_url']}")
    print(f"\n  الوصف عربي:\n    {product['description_ar']}")
    print(f"\n  الوصف إنجليزي:\n    {product['description_en']}")
    print(f"\n  المواصفات عربي:\n    {product['short_description_ar']}")
    print(f"\n  meta ar : {product['meta_title_ar']}")
    print(f"  meta en : {product['meta_title_en']}")
    if product["_missing"]:
        print(f"\n  ⚠ ناقص MISSING: {', '.join(product['_missing'])}")
    if product["_leaks"]:
        print(f"  ✗ تسريب اسم المصدر: {', '.join(product['_leaks'])}")
    if product["_voice_issues"]:
        print(f"  ✗ مخالفة نبرة: {'; '.join(product['_voice_issues'])}")


def main() -> int:
    ensure_dirs()
    dry = wants_dry_run()
    force = "--force" in sys.argv

    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    raws = load_stage(RAW_DIR)
    if not raws:
        warn("لا توجد بيانات خام — شغّل 01_scrape.py أولاً")
        return 1

    terms = supplier_terms()
    log(f"كلمات المصدر الممنوعة | scrub terms: {', '.join(sorted(terms)) or '—'}")

    if limit:
        raws = raws[:limit]
        step(f"وضع المراجعة: {len(raws)} منتج فقط | review mode")

    products = []
    for raw in raws:
        product = build_product(raw, terms)
        products.append(product)
        if limit:
            preview(product)
        if not dry:
            path = FINAL_DIR / f"{product['sku']}.json"
            if path.exists() and not force:
                continue
            write_json(path, product)

    missing_total = sum(len(p["_missing"]) for p in products)
    leaks_total = sum(len(p["_leaks"]) for p in products)
    voice_total = sum(len(p["_voice_issues"]) for p in products)

    step(f"تم | done — {len(products)} منتج")
    log(f"مواصفات ناقصة MISSING : {missing_total}")
    log(f"تسريب اسم المصدر      : {leaks_total}")
    log(f"مخالفات النبرة        : {voice_total}")

    if limit:
        print("\n  راجعي النبرة أعلاه. إذا ظبطت، شغّلي بلا --limit للباقي.")
    if dry:
        log("معاينة فقط، لم يُكتب أي ملف | dry run, nothing written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
