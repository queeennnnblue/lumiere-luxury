#!/usr/bin/env python3
"""
04 — معادلة تسعير لوموند، مطبّقة حرفياً كما وردت.
LOMOND pricing formula, applied literally. Constants live in config.py.

المدخل لكل قطعة: purchase_usd
المدخل على مستوى الشحنة: shipment_qty

    python scripts/04_pricing.py --self-test        # الاختبار الإلزامي فقط
    python scripts/04_pricing.py [--dry-run] [--shipment-qty N]
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
from common import (  # noqa: E402
    FINAL_DIR,
    ensure_dirs,
    log,
    step,
    warn,
    wants_dry_run,
    write_json,
)

TOLERANCE = 0.01  # ريال


# ------------------------------------------------------------- المعادلة
def price_piece(purchase_usd: float, shipment_qty: int) -> dict:
    """
    الخطوات ١..٩ بالترتيب المنصوص عليه، ثم الرسوم والضريبة والتقريب.
    كل بند يُرجَع منفصلاً ليظهر في جدول المقارنة.
    """
    if shipment_qty < 1:
        raise ValueError("shipment_qty لازم يكون ١ أو أكثر")

    purchase_sar = purchase_usd * config.FX                            # 1
    transfer_sar = (config.TRANSFER_FEE_USD / shipment_qty) * config.FX  # 2
    import_ship = (config.IMPORT_SHIP_USD / shipment_qty) * config.FX    # 3
    customs = config.CUSTOMS_SAR                                        # 4
    delivery = config.DELIVERY_SAR                                      # 5
    fixed_share = config.FIXED_ONETIME_SAR / config.ALLOC_QTY           # 6
    per_piece = config.PER_PIECE_FIXED_SAR                              # 7
    monthly_share = config.MONTHLY_SAR / config.ALLOC_QTY               # 8
    engraving = config.ENGRAVING_SAR / config.ALLOC_QTY                 # 9

    total_cost = (
        purchase_sar + transfer_sar + import_ship + customs + delivery
        + fixed_share + per_piece + monthly_share + engraving
    )

    fee_rate = config.PROCESSING_RATE + config.PAYMENT_RATE + config.TARGET_MARGIN
    price_ex_vat = total_cost / (1 - fee_rate)
    vat = price_ex_vat * config.VAT_RATE
    final_price = price_ex_vat + vat

    # التقريب لأعلى لأقرب ٥ ريال، ثم إعادة اشتقاق ما قبل الضريبة ليظل متسقاً
    final_rounded = math.ceil(final_price / config.ROUND_TO_SAR) * config.ROUND_TO_SAR
    price_ex_vat_final = final_rounded / (1 + config.VAT_RATE)
    vat_final = final_rounded - price_ex_vat_final
    net_profit = price_ex_vat_final * config.TARGET_MARGIN

    return {
        "purchase_usd": round(purchase_usd, 2),
        "shipment_qty": shipment_qty,
        "breakdown": {
            "1_purchase_sar": round(purchase_sar, 2),
            "2_transfer_sar": round(transfer_sar, 2),
            "3_import_ship": round(import_ship, 2),
            "4_customs": round(customs, 2),
            "5_delivery": round(delivery, 2),
            "6_fixed_share": round(fixed_share, 2),
            "7_per_piece": round(per_piece, 2),
            "8_monthly_share": round(monthly_share, 2),
            "9_engraving": round(engraving, 2),
        },
        "total_cost": round(total_cost, 2),
        "price_ex_vat_raw": round(price_ex_vat, 2),
        "final_price_raw": round(final_price, 2),
        "final_price": round(final_rounded, 2),
        "price_ex_vat": round(price_ex_vat_final, 2),
        "vat": round(vat_final, 2),
        "net_profit": round(net_profit, 2),
    }


# ------------------------------------------------------ الاختبار الإلزامي
def self_test() -> bool:
    case = config.REFERENCE_CASE
    got = price_piece(case["purchase_usd"], case["shipment_qty"])
    expected = case["expected"]

    step("الاختبار الإلزامي | mandatory reference test")
    log(f"purchase_usd = {case['purchase_usd']}، shipment_qty = {case['shipment_qty']}")
    print()
    print(f"  {'البند | item':22} {'المتوقع':>12} {'الناتج':>12} {'الفرق':>12}")
    print("  " + "─" * 62)

    # المقارنة على القيم قبل التقريب، لأن الأرقام المرجعية غير مقرّبة
    actual = {
        "total_cost": got["total_cost"],
        "price_ex_vat": got["price_ex_vat_raw"],
        "final_price": got["final_price_raw"],
    }

    ok = True
    for key in ("total_cost", "price_ex_vat", "final_price"):
        diff = actual[key] - expected[key]
        if abs(diff) > TOLERANCE:
            ok = False
        mark = "✓" if abs(diff) <= TOLERANCE else "✗"
        print(f"  {mark} {key:20} {expected[key]:>12,.2f} {actual[key]:>12,.2f} {diff:>+12,.2f}")

    print("  " + "─" * 62)
    print("\n  تفصيل البنود | cost breakdown")
    for name, value in got["breakdown"].items():
        print(f"    {name:20} {value:>12,.2f}")
    print(f"    {'total_cost':20} {got['total_cost']:>12,.2f}")

    if ok:
        print("\n  ✓ طابق الاختبار | reference test passed\n")
    else:
        print("\n  ✗ لم يطابق الاختبار | reference test FAILED")
        print("    توقّف التنفيذ. لم تُعدَّل أي ثوابت.")
        print("    Stopping. No constants were modified.\n")
    return ok


# ------------------------------------------------------------- التشغيل
def main() -> int:
    ensure_dirs()

    if "--self-test" in sys.argv:
        return 0 if self_test() else 1

    if not self_test():
        warn("الاختبار الإلزامي لم يطابق — لن يُسعَّر أي منتج")
        return 1

    dry = wants_dry_run()
    shipment_qty = 1
    if "--shipment-qty" in sys.argv:
        shipment_qty = int(sys.argv[sys.argv.index("--shipment-qty") + 1])

    paths = sorted(FINAL_DIR.glob("*.json"))
    if not paths:
        warn("لا توجد منتجات في data/final — شغّل 03_content.py أولاً")
        return 1

    import json

    rows = []
    for path in paths:
        product = json.loads(path.read_text(encoding="utf-8"))
        purchase_usd = product.get("purchase_usd")
        # الصفر ليس تكلفة، هو سعر محجوب عند المورّد. تسعيره يعني اختراع رقم.
        if purchase_usd in (None, "", "MISSING") or float(purchase_usd or 0) <= 0:
            warn(f"بلا سعر شراء | no purchase_usd: {path.name}")
            product.pop("pricing", None)
            for field in ("cost", "price_ex_vat", "vat", "final_price", "net_profit"):
                product.pop(field, None)
            if not dry:
                write_json(path, product)
            continue

        pricing = price_piece(float(purchase_usd), shipment_qty)
        product["pricing"] = pricing
        product["cost"] = pricing["total_cost"]
        product["price_ex_vat"] = pricing["price_ex_vat"]
        product["vat"] = pricing["vat"]
        product["final_price"] = pricing["final_price"]
        product["net_profit"] = pricing["net_profit"]

        if not dry:
            write_json(path, product)
        rows.append((product.get("name_ar") or path.stem, pricing))

    step(f"جدول الأسعار | pricing table ({len(rows)} منتج، shipment_qty={shipment_qty})")
    print()
    print(f"  {'المنتج | product':30} {'شراء $':>9} {'تكلفة':>10} {'قبل الضريبة':>12} {'ضريبة':>9} {'النهائي':>10} {'ربح صافي':>10}")
    print("  " + "─" * 94)
    for name, p in rows:
        print(
            f"  {name[:30]:30} {p['purchase_usd']:>9,.0f} {p['total_cost']:>10,.2f} "
            f"{p['price_ex_vat']:>12,.2f} {p['vat']:>9,.2f} {p['final_price']:>10,.2f} {p['net_profit']:>10,.2f}"
        )
    print("  " + "─" * 94)

    if dry:
        log("معاينة فقط، لم يُكتب أي ملف | dry run, nothing written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
