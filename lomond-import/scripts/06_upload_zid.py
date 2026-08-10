#!/usr/bin/env python3
"""
06 — رفع المنتجات إلى متجر زد عبر الـ API.
Upload finished products to the Zid store via the Merchant API.

⚠ لم يُتحقّق من شكل الـ endpoint والترويسات مقابل توثيق زد الرسمي.
   كلها قابلة للضبط من .env. شغّلي --check أولاً وصحّحي أي اختلاف
   قبل أي رفع حقيقي.

قواعد الأمان المطبّقة هنا:
  • المفاتيح تُقرأ من .env فقط، ولا تُطبع أبداً (تُحجب في كل المخرجات)
  • لا كتابة على المتجر بلا --confirm صريحة
  • الوضع الافتراضي معاينة، والرفع يبدأ بـ ٣ منتجات
  • idempotent: ما يعيد رفع منتج له zid_product_id مسجّل

    python scripts/06_upload_zid.py --check              # فحص الاتصال فقط
    python scripts/06_upload_zid.py --limit 3            # معاينة ٣ منتجات
    python scripts/06_upload_zid.py --limit 3 --confirm  # رفع فعلي لـ ٣
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    FINAL_DIR,
    OUTPUT_DIR,
    ensure_dirs,
    env,
    env_int,
    log,
    read_json,
    step,
    warn,
    write_json,
)

UPLOAD_LOG = OUTPUT_DIR / "upload_log.json"
TRIAL_SIZE = 3


# ------------------------------------------------------------- الاعتماد
def credentials() -> dict | None:
    """يقرأ المفاتيح من .env. لا تُطبع أبداً."""
    creds = {
        "base": env("ZID_API_BASE", "https://api.zid.sa/v1").rstrip("/"),
        "store_id": env("ZID_STORE_ID", ""),
        "access_token": env("ZID_ACCESS_TOKEN", ""),
        "manager_token": env("ZID_MANAGER_TOKEN", ""),
    }
    missing = [k for k in ("store_id", "access_token") if not creds[k]]
    if missing:
        warn(f"مفاتيح ناقصة في .env: {', '.join('ZID_' + m.upper() for m in missing)}")
        warn("حطّيها في .env ولا ترسليها في أي رسالة")
        return None
    return creds


def redact(text: str, creds: dict) -> str:
    """يحجب أي مفتاح قد يظهر في رسالة خطأ أو استجابة."""
    for key in ("access_token", "manager_token", "store_id"):
        value = creds.get(key) or ""
        if len(value) > 4:
            text = text.replace(value, f"<{key} محجوب>")
    return text


def headers(creds: dict) -> dict:
    """
    ترويسات زد. الأسماء قابلة للضبط لأنها لم تُتحقّق من التوثيق الرسمي.
    """
    result = {
        "Authorization": f"Bearer {creds['access_token']}",
        "Store-Id": creds["store_id"],
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Language": "ar",
    }
    if creds["manager_token"]:
        result["X-Manager-Token"] = creds["manager_token"]
        result["Role"] = "Manager"
    return result


def request(method: str, url: str, creds: dict, payload: dict | None = None) -> tuple[int, dict | str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers=headers(creds))
    try:
        with urllib.request.urlopen(req, timeout=env_int("SCRAPE_TIMEOUT", 30)) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(text)
            except json.JSONDecodeError:
                return resp.status, text
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        return exc.code, redact(detail, creds)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, redact(str(exc), creds)


# ------------------------------------------------------------- الفحص
def check(creds: dict) -> bool:
    step("فحص الاتصال بزد | connection check")
    log(f"الـ base : {creds['base']}")
    log(f"store_id : {'مضبوط ✓' if creds['store_id'] else 'ناقص ✗'} (محجوب)")
    log(f"token    : {'مضبوط ✓' if creds['access_token'] else 'ناقص ✗'} (محجوب)")

    status, body = request("GET", f"{creds['base']}/products/?page=1&page_size=1", creds)
    if status == 200:
        log("الاتصال شغّال ✓ | authenticated")
        return True

    warn(f"فشل الفحص، الحالة {status}")
    if status in (401, 403):
        warn("المفاتيح مرفوضة. راجعي ZID_ACCESS_TOKEN و ZID_MANAGER_TOKEN في .env")
    elif status == 404:
        warn("المسار غير موجود. عدّلي ZID_API_BASE أو مسار المنتجات حسب توثيق زد")
    elif status == 0:
        warn("ما وصلنا للخادم أصلاً. تأكدي أن zid.sa و api.zid.sa مسموحان في سياسة الشبكة")
    log(f"رد الخادم: {str(body)[:300]}")
    return False


# ------------------------------------------------------------- التحويل
def to_payload(product: dict) -> dict:
    """
    يحوّل منتج data/final إلى جسم طلب زد.
    أسماء الحقول مبنية على أعمدة تصدير زد، وقد تحتاج ضبطاً مقابل التوثيق.
    """
    specs = product.get("specs") or {}
    html_specs_ar = product.get("short_description_ar", "")
    html_specs_en = product.get("short_description_en", "")

    return {
        "sku": product.get("sku", ""),
        "name": {"ar": product.get("name_ar", ""), "en": product.get("name_en", "")},
        "description": {
            "ar": product.get("description_ar", "") + html_specs_ar,
            "en": product.get("description_en", "") + html_specs_en,
        },
        "short_description": {"ar": html_specs_ar, "en": html_specs_en},
        "seo": {
            "title": {"ar": product.get("meta_title_ar", ""), "en": product.get("meta_title_en", "")},
            "description": {
                "ar": product.get("meta_description_ar", ""),
                "en": product.get("meta_description_en", ""),
            },
        },
        "price": product.get("final_price"),
        "cost": product.get("cost"),
        "quantity": product.get("quantity", "Infinite"),
        "is_published": False,  # يُنشر يدوياً بعد المراجعة في لوحة التحكم
        "images": product.get("image_urls") or [],
        "attributes": {
            key: spec.get("value")
            for key, spec in specs.items()
            if spec.get("value") and spec.get("value") != "MISSING"
        },
    }


def blocking_issues(product: dict) -> list[str]:
    issues = []
    if not product.get("final_price"):
        issues.append("بلا سعر — شغّلي 04_pricing.py")
    if not (product.get("image_urls") or []):
        issues.append("بلا روابط صور مستضافة")
    missing = [k for k, s in (product.get("specs") or {}).items() if s.get("value") == "MISSING"]
    if missing:
        issues.append(f"مواصفات MISSING: {', '.join(missing)}")
    if product.get("_leaks"):
        issues.append(f"أثر لاسم المصدر: {', '.join(product['_leaks'])}")
    return issues


# ------------------------------------------------------------- التشغيل
def load_log() -> dict:
    if UPLOAD_LOG.exists():
        try:
            return read_json(UPLOAD_LOG)
        except json.JSONDecodeError:
            warn("سجل الرفع تالف، نبدأ سجلاً جديداً")
    return {"uploaded": {}}


def main() -> int:
    ensure_dirs()
    creds = credentials()
    if not creds:
        return 1

    if "--check" in sys.argv:
        return 0 if check(creds) else 1

    confirm = "--confirm" in sys.argv
    limit = TRIAL_SIZE
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if "--all" in sys.argv:
        limit = None

    products = [read_json(p) for p in sorted(FINAL_DIR.glob("*.json"))]
    if not products:
        warn("لا توجد منتجات في data/final — شغّلي 03_content.py ثم 04_pricing.py")
        return 1

    upload_log = load_log()
    pending = [p for p in products if p.get("sku") not in upload_log["uploaded"]]
    skipped = len(products) - len(pending)
    if skipped:
        log(f"مرفوع سابقاً، نتخطّاه | already uploaded: {skipped}")

    if limit is not None:
        pending = pending[:limit]

    if not confirm:
        step(f"معاينة | preview — {len(pending)} منتج (بلا رفع)")
    else:
        step(f"رفع فعلي | live upload — {len(pending)} منتج")

    ok = failed = blocked = 0
    for product in pending:
        name = product.get("name_ar") or product.get("sku", "")
        issues = blocking_issues(product)

        if issues:
            warn(f"✗ {name}: {'؛ '.join(issues)}")
            blocked += 1
            continue

        if not confirm:
            log(f"✓ جاهز للرفع | ready: {name}")
            ok += 1
            continue

        status, body = request("POST", f"{creds['base']}/products/", creds, to_payload(product))
        if status in (200, 201):
            product_id = (body or {}).get("id") if isinstance(body, dict) else None
            upload_log["uploaded"][product["sku"]] = {"id": product_id, "name": name}
            write_json(UPLOAD_LOG, upload_log)
            log(f"✓ رُفع | uploaded: {name}  (id={product_id})")
            ok += 1
        else:
            warn(f"✗ فشل {status} | {name}: {str(body)[:200]}")
            failed += 1

    step("الخلاصة | summary")
    log(f"جاهز/مرفوع : {ok}")
    log(f"محجوب      : {blocked}")
    log(f"فشل        : {failed}")

    if not confirm:
        print("\n  هذي معاينة فقط. للرفع الفعلي أضيفي --confirm")
        print("  ابدئي بـ ٣ منتجات، وراجعيها في لوحة تحكم زد قبل الباقي.")
    else:
        print("\n  المنتجات تُرفع غير منشورة (is_published=false).")
        print("  راجعيها في لوحة التحكم وانشريها يدوياً.")

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
