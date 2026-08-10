# دليل التشغيل المحلي | Local setup

خط استيراد منتجات لوموند من مواقع الموردين إلى متجر زد.

القواعد والهوية في [`CLAUDE.md`](CLAUDE.md) — يُقرأ تلقائياً في كل جلسة.

---

## ١. التجهيز، مرة واحدة

### المتطلبات

- Python 3.10 أو أحدث
- Git

تأكدي من الإصدار:

```bash
python3 --version
```

### إنزال المشروع

```bash
git clone https://github.com/queeennnnblue/lumiere-luxury.git
cd lumiere-luxury
git checkout claude/lgg-jewelry-website-ryplko
cd lomond-import
```

### البيئة والتبعيات

```bash
python3 -m venv .venv
source .venv/bin/activate        # على ويندوز: .venv\Scripts\activate
pip install -r requirements.txt
```

> بعد أول مرة، يكفي `source .venv/bin/activate` في كل جلسة جديدة.

### ملف المفاتيح

```bash
cp .env.example .env
```

افتحي `.env` وعبّي القيم. **لا تُرسل في أي رسالة، ولا تُرفع للريبو** — محمية بـ `.gitignore`.

للرفع إلى زد تحتاجين:

```
ZID_STORE_ID=
ZID_ACCESS_TOKEN=
ZID_MANAGER_TOKEN=
```

### روابط الموردين

افتحي `sources.txt` وحطّي روابط المنتجات أو الأقسام، رابط في كل سطر.
لتثبيت التصنيف يدوياً:

```
https://example.com/products/oval-ring  | category=rings
```

التصنيفات: `rings` · `earrings` · `necklaces` · `bracelets`

---

## ٢. التشغيل، مرحلة مرحلة

**لا تقفزي مراحل، وابدئي كل مرحلة بـ ٣ عناصر.**

### قبل أي سحب: افحصي المواقع

```bash
python scripts/01_scrape.py --inspect
```

يطبع لكل موقع: هل `robots.txt` يسمح، ووجود `products.json` و`sitemap.xml`،
وعدد كتل JSON-LD. لو موقع منع السحب، يوقف عنده ويبلّغك.

### المرحلة ١ — السحب

```bash
python scripts/01_scrape.py --limit 3      # تجربة
python scripts/01_scrape.py                # الكل
```

المخرج: `data/raw/*.json` + جدول (نجح / فشل / حقول ناقصة).
لو انقطع، أعيدي الأمر نفسه — يكمل من حيث وقف. `--force` يعيد السحب من الصفر.

### المرحلة ٢ — الصور

```bash
python scripts/02_images.py --limit 3
python scripts/02_images.py
```

الأصل في `images/original/`، والمعالَج في `images/processed/` بمقاس
٢٠٠٠×٢٠٠٠ وخلفية بيضاء، والتسمية `lomond-{sku}-{01}.jpg` بلا EXIF.
يطبع جدول أبعاد قبل وبعد، ويعلّم الصور الأقل من ١٢٠٠ بكسل.

للترقية (اختياري، محلي فقط، يحتاج `realesrgan-ncnn-vulkan` مثبّتاً):

```bash
python scripts/02_images.py --upscale
```

> الترقية تكبّر وتنعّم، ولا تضيف تفاصيل غير موجودة. الحل الصحيح لصور
> ضعيفة هو طلب ملفات أعلى دقة من المورّد.

### المرحلة ٣ — المحتوى

```bash
python scripts/03_content.py --limit 3     # راجعي النبرة أولاً
python scripts/03_content.py               # الباقي بعد الموافقة
```

المخرج: `data/final/*.json` فيها الاسم والوصف والمواصفات والميتا والتصنيف
بالعربي والإنجليزي. المواصفة الناقصة تُكتب `MISSING` ولا تُخترع.
أسماء الموردين تُمسح من كل الحقول تلقائياً.

### المرحلة ٤ — التسعير

```bash
python scripts/04_pricing.py --self-test           # الاختبار المرجعي
python scripts/04_pricing.py --shipment-qty 10     # حسب عدد قطع الشحنة
```

الثوابت في `scripts/config.py` **فقط**. لو الاختبار المرجعي ما طابق،
السكربت يوقف ولا يسعّر شيئاً.

### المرحلة ٥ — بناء ملف الرفع

```bash
python scripts/05_build_csv.py --sample 3    # ملف تجريبي بـ ٣ منتجات
python scripts/05_build_csv.py               # الملف الكامل
```

المخرج: `output/lomond_products.csv` بنفس أعمدة زد الـ٨٢ وترميز UTF-8 with BOM،
مع تقرير `output/review_report.md`.

يرفض الكتابة لو فيه حقل إلزامي فاضي، أو `MISSING`، أو أثر لاسم مورّد.
راجعي التقرير وصلّحي المصدر. `--allow-issues` يتجاوز الحاجز عند الضرورة.

### المرحلة ٦ — الرفع إلى زد

```bash
python scripts/06_upload_zid.py --check              # فحص الاتصال
python scripts/06_upload_zid.py --limit 3            # معاينة بلا رفع
python scripts/06_upload_zid.py --limit 3 --confirm  # رفع ٣ منتجات
```

المنتجات تُرفع **غير منشورة**. راجعيها في لوحة تحكم زد وانشريها يدوياً.

> ⚠ مسار الـ API وأسماء الترويسات لم يُتحقّق منها من توثيق زد الرسمي.
> شغّلي `--check` أولاً، وعدّلي `ZID_API_BASE` في `.env` لو احتاج.

---

## ٣. عقبة الصور

عمود `images` في زد يحتاج **روابط** لا ملفات. بعد المرحلة ٢، الصور على
قرصك ولسّه بلا روابط، ولهذا المرحلة ٥ و٦ تحجبان المنتجات.

الحل: ارفعي `images/processed/` على استضافة، ثم ضيفي الروابط لكل منتج
في `data/final/{sku}.json`:

```json
"image_urls": [
  "https://.../lomond-Z.123-01.jpg",
  "https://.../lomond-Z.123-02.jpg"
]
```

ثم أعيدي المرحلة ٥.

---

## ٤. الأمان

- `.env` و`data/` و`images/original/` و`output/` كلها في `.gitignore`.
- المفاتيح تُقرأ من `.env` ولا تُطبع في أي مخرجات.
- لا كتابة على متجر زد بلا `--confirm` صريحة.
- كل سكربت يقبل `--dry-run` للمعاينة بلا كتابة.

---

## ٥. حل المشاكل

| العَرَض | السبب والحل |
|---|---|
| `Pillow missing` | `pip install -r requirements.txt` داخل البيئة المفعّلة |
| `fetch failed` لكل الروابط | تحقّقي من الإنترنت، أو أن الموقع يحجب الطلبات الآلية |
| `robots.txt disallow` | الموقع يمنع السحب. توقّفي وتواصلي مع المورّد |
| الاختبار المرجعي فشل | لا تعدّلي `config.py`. راجعي الفرق المطبوع أولاً |
| `05` يرفض الكتابة | افتحي `output/review_report.md`، فيه سبب كل منتج |
| `06 --check` يرجع 401 | راجعي `ZID_ACCESS_TOKEN` و`ZID_MANAGER_TOKEN` في `.env` |
| `06 --check` يرجع 404 | عدّلي `ZID_API_BASE` حسب توثيق زد |
