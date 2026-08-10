#!/usr/bin/env python3
"""
05 — بناء ملف الرفع إلى زد.
Build output/lomond_products.csv with exactly the zid_sample.csv columns.

  • الأعمدة والترتيب من zid_sample.csv حرفياً
  • الترميز UTF-8 with BOM
  • تحقّق قبل الحفظ: لا حقل إلزامي فاضي، لا MISSING، لا أثر لاسم المصدر
  • تقرير output/review_report.md بكل مشكلة

    python scripts/05_build_csv.py --sample 3    # ملف تجريبي بـ ٣ منتجات
    python scripts/05_build_csv.py [--dry-run] [--allow-issues]
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    FINAL_DIR,
    OUTPUT_CSV,
    OUTPUT_DIR,
    SAMPLE_CSV,
    ZID_COLUMNS,
    blank_row,
    ensure_dirs,
    load_stage,
    log,
    step,
    warn,
    wants_dry_run,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module  # noqa: E402

_content = import_module("03_content")
MISSING = _content.MISSING
supplier_terms = _content.supplier_terms
find_leaks = _content.find_leaks
check_voice = _content.check_voice

REVIEW_REPORT = OUTPUT_DIR / "review_report.md"

# الحقول التي لا يقبل زد فراغها (مستنتجة من العيّنة الحقيقية)
REQUIRED = [
    "sku", "has_variants", "name_ar", "name_en", "product_page_url",
    "quantity", "weight_unit", "published", "price", "cost",
    "images", "images_alt_text_ar", "images_alt_text_en",
]


def verify_schema() -> bool:
    """يتأكد أن أعمدتنا مطابقة تماماً لعيّنة زد."""
    if not SAMPLE_CSV.exists():
        warn("zid_sample.csv غير موجود، نعتمد ZID_COLUMNS")
        return True
    with open(SAMPLE_CSV, encoding="utf-8-sig", newline="") as fh:
        sample_cols = next(csv.reader(fh))
    if sample_cols != ZID_COLUMNS:
        warn("أعمدة ZID_COLUMNS لا تطابق zid_sample.csv")
        extra = set(ZID_COLUMNS) - set(sample_cols)
        missing = set(sample_cols) - set(ZID_COLUMNS)
        if extra:
            warn(f"زائد: {sorted(extra)}")
        if missing:
            warn(f"ناقص: {sorted(missing)}")
        return False
    return True


def image_urls(product: dict) -> str:
    """روابط الصور المرفوعة. تبقى فارغة حتى تُرفع الصور المعالجة إلى استضافة."""
    return ", ".join(product.get("image_urls") or [])


def to_row(product: dict) -> dict:
    row = blank_row()
    specs = product.get("specs") or {}

    def spec(key: str) -> str:
        return (specs.get(key) or {}).get("value", MISSING)

    row.update({
        "sku": product.get("sku", ""),
        "has_variants": "No",
        "name_ar": product.get("name_ar", ""),
        "name_en": product.get("name_en", ""),
        "description_ar": product.get("description_ar", ""),
        "description_en": product.get("description_en", ""),
        "short_description_ar": product.get("short_description_ar", ""),
        "short_description_en": product.get("short_description_en", ""),
        "product_page_title_ar": product.get("meta_title_ar", ""),
        "product_page_title_en": product.get("meta_title_en", ""),
        "product_page_description_ar": product.get("meta_description_ar", ""),
        "product_page_description_en": product.get("meta_description_en", ""),
        "product_page_url": product.get("product_page_url", ""),
        "quantity": product.get("quantity", "Infinite"),
        "categories_ar": product.get("categories_ar", ""),
        "categories_en": product.get("categories_en", ""),
        "categories_description_ar": "[]",
        "categories_description_en": "[]",
        "weight": spec("weight") if spec("weight") != MISSING else "",
        "weight_unit": product.get("weight_unit", "g"),
        "published": product.get("published", "No"),
        "price": f"{product.get('final_price', '')}",
        "cost": f"{product.get('cost', '')}",
        "images": image_urls(product),
    })

    count = len(product.get("image_urls") or [])
    if count:
        alt_ar = product.get("name_ar", "")
        alt_en = product.get("name_en", "")
        row["images_alt_text_ar"] = ", ".join([alt_ar] * count)
        row["images_alt_text_en"] = ", ".join([alt_en] * count)

    return row


# ------------------------------------------------------------------ التحقق
def validate(rows: list[dict], terms: set[str]) -> list[dict]:
    issues = []
    for index, row in enumerate(rows, start=1):
        label = row.get("name_ar") or row.get("sku") or f"صف {index}"

        for column in REQUIRED:
            if not (row.get(column) or "").strip():
                issues.append({"row": index, "product": label, "column": column,
                               "kind": "حقل إلزامي فاضي", "detail": ""})

        for column, value in row.items():
            value = value or ""
            if MISSING in value:
                issues.append({"row": index, "product": label, "column": column,
                               "kind": "قيمة MISSING", "detail": value[:60]})

            leaks = find_leaks(value, terms)
            if leaks:
                issues.append({"row": index, "product": label, "column": column,
                               "kind": "أثر لاسم المصدر", "detail": ", ".join(leaks)})

            for problem in check_voice(value):
                issues.append({"row": index, "product": label, "column": column,
                               "kind": "مخالفة نبرة", "detail": problem})
    return issues


def write_report(rows: list[dict], issues: list[dict], dry: bool) -> None:
    lines = [
        "# تقرير المراجعة | Review report",
        "",
        f"- عدد المنتجات: **{len(rows)}**",
        f"- عدد الأعمدة: **{len(ZID_COLUMNS)}**",
        f"- عدد المشاكل: **{len(issues)}**",
        "",
    ]

    if not issues:
        lines += ["## ✅ لا مشاكل", "", "الملف جاهز للرفع إلى زد.", ""]
    else:
        by_kind: dict[str, list[dict]] = {}
        for issue in issues:
            by_kind.setdefault(issue["kind"], []).append(issue)

        lines += ["## ملخّص حسب النوع", "", "| النوع | العدد |", "|---|---|"]
        for kind, group in sorted(by_kind.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"| {kind} | {len(group)} |")
        lines += ["", "## التفاصيل", "",
                  "| # | المنتج | العمود | النوع | التفصيل |", "|---|---|---|---|---|"]
        for issue in issues:
            detail = (issue["detail"] or "").replace("|", "\\|")[:60]
            lines.append(
                f"| {issue['row']} | {issue['product']} | `{issue['column']}` "
                f"| {issue['kind']} | {detail} |"
            )
        lines.append("")

    if not dry:
        REVIEW_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(rows: list[dict], path: Path) -> None:
    # UTF-8 with BOM — زد يتطلبها لقراءة العربية في Excel
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ZID_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


# ------------------------------------------------------------------ التشغيل
def main() -> int:
    ensure_dirs()
    dry = wants_dry_run()
    allow_issues = "--allow-issues" in sys.argv

    sample_size = None
    if "--sample" in sys.argv:
        sample_size = int(sys.argv[sys.argv.index("--sample") + 1])

    if not verify_schema():
        warn("توقّف: مخطط الأعمدة لا يطابق العيّنة")
        return 1

    products = load_stage(FINAL_DIR)
    if not products:
        warn("لا توجد منتجات في data/final — شغّل 03_content.py ثم 04_pricing.py")
        return 1

    if sample_size:
        products = products[:sample_size]
        step(f"ملف تجريبي: {len(products)} منتج | trial file")

    rows = [to_row(p) for p in products]
    terms = supplier_terms()
    issues = validate(rows, terms)

    target = OUTPUT_DIR / (f"lomond_products_sample{sample_size}.csv" if sample_size else OUTPUT_CSV.name)

    step("نتيجة التحقق | validation")
    if issues:
        by_kind: dict[str, int] = {}
        for issue in issues:
            by_kind[issue["kind"]] = by_kind.get(issue["kind"], 0) + 1
        for kind, count in sorted(by_kind.items(), key=lambda kv: -kv[1]):
            warn(f"{kind}: {count}")
    else:
        log("لا مشاكل ✓")

    write_report(rows, issues, dry)

    blocking = [i for i in issues if i["kind"] in ("حقل إلزامي فاضي", "قيمة MISSING", "أثر لاسم المصدر")]
    if blocking and not allow_issues:
        warn(f"لم يُكتب CSV: {len(blocking)} مشكلة حاجزة")
        warn(f"راجعي {REVIEW_REPORT.name}، أو استخدمي --allow-issues للكتابة رغم ذلك")
        return 2

    if dry:
        log(f"معاينة فقط، لم يُكتب {target.name} | dry run")
        return 0

    write_csv(rows, target)
    step(f"تم | done — {target}")
    log(f"{len(rows)} منتج × {len(ZID_COLUMNS)} عمود، UTF-8 with BOM")
    log(f"التقرير: {REVIEW_REPORT}")

    if not sample_size:
        print("\n  جرّبي ملف الـ ٣ منتجات في زد أولاً:")
        print("    python scripts/05_build_csv.py --sample 3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
