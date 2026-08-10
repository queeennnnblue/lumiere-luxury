"""
ثوابت تسعير لوموند. لا تُكتب داخل الكود، تُقرأ من هنا فقط.
LOMOND pricing constants. Never inline these in the scripts.

القيم مضبوطة يدوياً من المالكة. لا يُعدَّل أي رقم هنا بلا إذن صريح.
"""

FX = 3.75                  # ريال لكل دولار
TRANSFER_FEE_USD = 38      # رسوم التحويل البنكي لكل شحنة
IMPORT_SHIP_USD = 35       # شحن الواردات لكل شحنة
CUSTOMS_SAR = 21           # جمارك لكل قطعة
DELIVERY_SAR = 30          # شحن التوصيل للعميلة
FIXED_ONETIME_SAR = 10396.44   # تكاليف التأسيس الكلية
ALLOC_QTY = 50             # عدد القطع اللي توزّع عليها الثابتة والشهرية
PER_PIECE_FIXED_SAR = 45.08    # علب + كاردز + عدسات + بزنس كارد + مناديل
MONTHLY_SAR = 1059         # التكاليف الشهرية
ENGRAVING_SAR = 170        # حفر اللوقو، يوزّع على ALLOC_QTY
PROCESSING_RATE = 0.08     # رسوم المعالجة
PAYMENT_RATE = 0.038       # متوسط رسوم بوابات الدفع
TARGET_MARGIN = 0.10       # الربح الصافي المستهدف
VAT_RATE = 0.15

# التقريب: لأعلى لأقرب مضاعف من هذا الرقم
ROUND_TO_SAR = 5

# ---------------------------------------------------------------- الاختبار
# اختبار إلزامي من المالكة. أي تعديل هنا يحتاج إذناً صريحاً.
REFERENCE_CASE = {
    "purchase_usd": 929,
    "shipment_qty": 1,
    "expected": {
        "total_cost": 3943.59,
        "price_ex_vat": 5042.95,
        "final_price": 5799.40,
    },
}
