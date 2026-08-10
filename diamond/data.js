/* ============================================================
   لوميير | Lumière — بيانات المتجر
   Store data: pricing settings, catalogue, translations, tracking.
   Loaded before the inline script in index.html.
   ============================================================ */

/* ---------- 1. إعدادات التسعير | Pricing settings ----------
   القيم مأخوذة من آلة حساب الأسعار (calculator.html) في جذر المشروع.
   Values mirror calculator.html at the repo root — keep them in sync. */
const settings = {
    // 1 USD = 3.75 SAR (السعر المربوط)
    exchangeRate: 3.75,

    // النفقات العامة، تُوزَّع بالتساوي على عدد المنتجات
    overheadFixed: 2112,     // إجمالي النفقات الثابتة
    overheadMonthly: 1200,   // إجمالي النفقات الشهرية
    productCount: 10,        // عدد القطع التي توزَّع عليها النفقات

    processingFee: 6.0,      // رسوم المعالجة %
    profitMargin: 6.0,       // هامش الربح المستهدف %
    customShipping: 45,      // الشحن والتغليف لكل قطعة (ر.س)

    // رسوم بوابات الدفع %
    cashFee: 0.0,            // كاش / تحويل بنكي
    appleFee: 2.5,           // Apple Pay
    tabbyFee: 7.0            // تابي / تمارا (الدفع الآجل)
};

/* ---------- 2. التشكيلة | Catalogue ----------
   priceStarsGem / priceProvence = تكلفة المورّد بالدولار (USD).
   يُختار الأرخص تلقائياً في calculatePrices(). */
const products = [
    {
        id: 1,
        category: 'ring',
        name: { ar: 'خاتم سوليتير كلاسيك', en: 'Classic Solitaire Ring' },
        carats: 1.0,
        cut: 'Round',
        color: { ar: 'ذهب أبيض 18 قيراط', en: '18K White Gold' },
        desc: {
            ar: 'الخاتم الذي لا يخطئ أبداً. حجر مستدير بقصّة مثالية على طوق ذهب أبيض نحيل، يترك الضوء يفعل كل شيء. شهادة IGI مرفقة.',
            en: 'The ring that never misses. An ideal-cut round stone on a slim white-gold band that lets the light do all the talking. IGI certified.'
        },
        img: 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 420,
        priceProvence: 445
    },
    {
        id: 2,
        category: 'ring',
        name: { ar: 'خاتم أوفال هالو', en: 'Oval Halo Ring' },
        carats: 1.5,
        cut: 'Oval',
        color: { ar: 'ذهب وردي 18 قيراط', en: '18K Rose Gold' },
        desc: {
            ar: 'حجر بيضاوي يطيل الإصبع، محاط بهالة من الأحجار الصغيرة تضاعف اللمعان. الذهب الوردي يمنحه دفئاً لا تجده في الأبيض.',
            en: 'An oval centre stone that elongates the finger, ringed by a halo that doubles the sparkle. Rose gold gives it a warmth white gold cannot.'
        },
        img: 'https://images.unsplash.com/photo-1603561591411-07134e71a2a9?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 690,
        priceProvence: 655
    },
    {
        id: 3,
        category: 'ring',
        name: { ar: 'خاتم إمرالد كت', en: 'Emerald Cut Ring' },
        carats: 2.0,
        cut: 'Emerald',
        color: { ar: 'ذهب أبيض 18 قيراط', en: '18K White Gold' },
        desc: {
            ar: 'قصّة الزمرد للنقاء العالي فقط — أسطحها الواسعة لا تخفي شيئاً. قطعتان قيراط من الوضوح الصريح.',
            en: 'Emerald cut is for high clarity only — its wide facets hide nothing. Two carats of unapologetic clarity.'
        },
        img: 'https://images.unsplash.com/photo-1598560917505-59a3ad559071?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 980,
        priceProvence: 1020
    },
    {
        id: 4,
        category: 'ring',
        name: { ar: 'خاتم إتيرنتي', en: 'Eternity Band' },
        carats: 1.2,
        cut: 'Round',
        color: { ar: 'ذهب أبيض 14 قيراط', en: '14K White Gold' },
        desc: {
            ar: 'دائرة كاملة من الأحجار المتساوية، بلا بداية ولا نهاية. يُلبس وحده أو فوق خاتم الخطوبة.',
            en: 'A full circle of matched stones, no beginning and no end. Wear it alone or stacked above an engagement ring.'
        },
        img: 'https://images.unsplash.com/photo-1611652022419-a9419f74343d?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 560,
        priceProvence: 540
    },
    {
        id: 5,
        category: 'necklace',
        name: { ar: 'قلادة سوليتير', en: 'Solitaire Pendant' },
        carats: 0.75,
        cut: 'Round',
        color: { ar: 'ذهب أبيض 18 قيراط', en: '18K White Gold' },
        desc: {
            ar: 'حجر واحد معلّق على سلسلة رفيعة، يستقر تماماً عند منتصف عظمة الترقوة. القطعة التي تُلبس كل يوم ولا تُخلع.',
            en: 'A single stone on a fine chain, resting exactly at the collarbone. The piece you put on daily and never take off.'
        },
        img: 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 310,
        priceProvence: 335
    },
    {
        id: 6,
        category: 'necklace',
        name: { ar: 'قلادة تينيس', en: 'Tennis Necklace' },
        carats: 3.0,
        cut: 'Round',
        color: { ar: 'ذهب أبيض 14 قيراط', en: '14K White Gold' },
        desc: {
            ar: 'خط متصل من الماس حول العنق. ثلاثة قراريط موزّعة بعناية — حضور كامل دون مبالغة.',
            en: 'An unbroken line of diamonds around the neck. Three carats carefully distributed — full presence, no shouting.'
        },
        img: 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 1450,
        priceProvence: 1380
    },
    {
        id: 7,
        category: 'earrings',
        name: { ar: 'أقراط ستد', en: 'Diamond Studs' },
        carats: 1.0,
        cut: 'Round',
        color: { ar: 'ذهب أبيض 18 قيراط', en: '18K White Gold' },
        desc: {
            ar: 'نصف قيراط لكل أذن، بقصّة مثالية ومسند مقاوم للانزلاق. أول قطعة ماس تُشترى، وآخر قطعة تُستغنى عنها.',
            en: 'Half a carat per ear, ideal cut, secure backs. The first diamond you buy and the last one you would part with.'
        },
        img: 'https://images.unsplash.com/photo-1635767798638-3e25273a8236?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 395,
        priceProvence: 410
    },
    {
        id: 8,
        category: 'earrings',
        name: { ar: 'أقراط دروب بير', en: 'Pear Drop Earrings' },
        carats: 1.6,
        cut: 'Pear',
        color: { ar: 'ذهب أصفر 18 قيراط', en: '18K Yellow Gold' },
        desc: {
            ar: 'حجران على شكل دمعة يتحركان مع كل التفاتة. للمناسبات التي تستحق أن يُلتفت إليكِ فيها.',
            en: 'Two teardrop stones that move with every turn of the head. For the occasions that deserve to be noticed.'
        },
        img: 'https://images.unsplash.com/photo-1630019852942-f89202989a59?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 720,
        priceProvence: 760
    },
    {
        id: 9,
        category: 'bracelet',
        name: { ar: 'إسورة تينيس', en: 'Tennis Bracelet' },
        carats: 2.5,
        cut: 'Round',
        color: { ar: 'ذهب أبيض 14 قيراط', en: '14K White Gold' },
        desc: {
            ar: 'الإسورة التي لا تخرج من الموضة أبداً. أحجار متطابقة بإغلاق مزدوج آمن — تُلبس مع الساعة أو وحدها.',
            en: 'The bracelet that never leaves fashion. Matched stones with a double safety clasp — wear it with a watch or on its own.'
        },
        img: 'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 1180,
        priceProvence: 1240
    },
    {
        id: 10,
        category: 'bracelet',
        name: { ar: 'إسورة بانغل ماسية', en: 'Diamond Bangle' },
        carats: 0.9,
        cut: 'Round',
        color: { ar: 'ذهب وردي 18 قيراط', en: '18K Rose Gold' },
        desc: {
            ar: 'بانغل صلبة بخط ماسي على الوجه الأمامي فقط. بسيطة من زاوية، لامعة من أخرى.',
            en: 'A solid bangle with a diamond line across the face only. Plain from one angle, brilliant from another.'
        },
        img: 'https://images.unsplash.com/photo-1573408301185-9146fe634ad0?auto=format&fit=crop&w=800&q=80',
        priceStarsGem: 640,
        priceProvence: 615
    }
];

/* ---------- 3. الترجمات | Translations ---------- */
const translations = {
    ar: {
        nav_collection: 'التشكيلة',
        nav_why: 'لماذا نحن',
        nav_custom: 'صمّمي قطعتك',

        hero_title: 'ألماس الحلم، بسعر الحقيقة',
        hero_subtitle: 'مجوهرات الماس المخبري الفاخر • شهادة IGI معتمدة • توفير يصل إلى 70%',
        btn_discover: 'اكتشفي التشكيلة',

        about_title: 'عن الماس المخبري',
        about_desc: 'الماس المخبري له نفس التركيب الكيميائي للماس الطبيعي، لكنه يتكون في المختبر بدلاً من باطن الأرض. النتيجة: ماس أنقى، أكبر، وأقل سعراً. بدون تعدين ضار، بدون وسطاء، بدون هوامش علامات تجارية كبرى.',

        collection_title: 'التشكيلة الحصرية',
        filter_all: 'الكل',
        filter_rings: 'خواتم',
        filter_necklaces: 'قلائد',
        filter_earrings: 'أقراط',
        filter_bracelets: 'أساور',

        why_title: 'لماذا تنتقلين إلينا؟',
        why_1_title: 'ماس أفضل، سعر أقل',
        why_1_text: 'الماس المخبري متطابق كيميائياً مع الطبيعي، لكنه يتكون في بيئة مراقبة. تحصلين على ماس أنقى، خالٍ من الشوائب، بجزء من ثمن الماس الطبيعي. بلا تعدين ضار، بلا استخراج من باطن الأرض.',
        why_2_title: 'سعر مباشر بلا وسطاء',
        why_2_text: 'نشتري مباشرة من أفضل الموردين العالميين، ونبيع مباشرة إليكِ. بلا هوامش علامات تجارية كبرى، بلا تسييج أسعار، بلا تضخيم اصطناعي. توفيرٌ يصل إلى 70% مقارنة بمتاجر المجوهرات التقليدية.',
        why_3_title: 'تخصيص + شهادة معتمدة',
        why_3_text: 'كل قطعة تأتي مع شهادة IGI معتمدة دولياً، تثبت الخصائص والقيراط والنقاء. ولم تجدي ما يناسبكِ؟ نصمّمه لكِ. قطعتك الفريدة التي تشبهك تماماً.',

        custom_title: 'صمّمي قطعتك الخاصة',
        custom_subtitle: 'لم تجدي ما يناسبكِ في التشكيلة؟ نصمّمه لكِ تماماً كما تتخيلينه',
        custom_metal: 'نوع المعدن',
        metal_18k: 'ذهب عيار 18',
        metal_14k: 'ذهب عيار 14 (الأفضل قيمة)',
        metal_silver: 'فضة',
        custom_color: 'اللون',
        color_white: 'فضي',
        color_yellow: 'ذهبي',
        color_rose: 'روز قولد',
        custom_cut: 'قصة الألماس',
        cut_round: 'دائري',
        cut_oval: 'بيضاوي',
        cut_pear: 'كمثري',
        cut_marquise: 'ماركيز',
        cut_emerald: 'زمردي',
        cut_cushion: 'وسادة',
        cut_princess: 'أميرة',
        cut_heart: 'قلب',
        cut_radiant: 'راديانت',
        cut_asscher: 'آشر',
        custom_details: 'ملاحظات إضافية (اختياري)',
        custom_phone: 'رقم الجوال *',
        btn_send: 'إرسال الطلب',
        custom_success: 'سيتم التواصل معكِ خلال 48 ساعة بالسعر النهائي',
        quote: 'كما يحتاج الفحم إلى زمنٍ وضغطٍ ليصير ماسة،<br>تستحق قطعتكِ الفريدة لحظةً من الصبر لتولد كاملة.',
        btn_whatsapp: 'إرسال عبر واتساب',

        footer_desc: 'كل قطعة بشهادة IGI معتمدة • شحن آمن داخل المملكة',

        // مفاتيح تُستخدم داخل السكربت
        from: 'يبدأ من',
        currency: 'ر.س',
        carat: 'القيراط',
        cut: 'القصة',
        color: 'المعدن',
        cash_payment: 'كاش / تحويل بنكي',
        tabby_payment: 'تابي / تمارا',
        market_compare: 'مقارنة السوق',
        savings_text: 'سعرنا أوفر بـ',
        savings_suffix: 'من متاجر المجوهرات التقليدية',
        contact_whatsapp: 'تواصلي عبر واتساب',
        lang_switch: 'English'
    },

    en: {
        nav_collection: 'Collection',
        nav_why: 'Why Us',
        nav_custom: 'Custom Design',

        hero_title: 'Dream diamonds, honest prices',
        hero_subtitle: 'Fine lab-grown diamond jewellery • IGI certified • Save up to 70%',
        btn_discover: 'Explore the collection',

        about_title: 'About lab-grown diamonds',
        about_desc: 'A lab-grown diamond has the identical chemical composition of a mined diamond — it simply forms in a laboratory instead of underground. The result: a purer, larger stone for a fraction of the price. No destructive mining, no middlemen, no luxury-house markup.',

        collection_title: 'The Collection',
        filter_all: 'All',
        filter_rings: 'Rings',
        filter_necklaces: 'Necklaces',
        filter_earrings: 'Earrings',
        filter_bracelets: 'Bracelets',

        why_title: 'Why switch to us?',
        why_1_title: 'Better stone, lower price',
        why_1_text: 'Lab-grown diamonds are chemically identical to mined ones, but formed in a controlled environment. You get a purer, cleaner stone for a fraction of the price of a mined diamond — with no destructive mining involved.',
        why_2_title: 'Direct pricing, no middlemen',
        why_2_text: 'We buy directly from the best global suppliers and sell directly to you. No luxury-house margins, no price fixing, no artificial inflation. Savings of up to 70% compared to traditional jewellers.',
        why_3_title: 'Custom design + certification',
        why_3_text: 'Every piece ships with an internationally recognised IGI certificate documenting its carat, cut and clarity. Did not find what you wanted? We will design it for you — a piece that is entirely yours.',

        custom_title: 'Design your own piece',
        custom_subtitle: 'Nothing in the collection quite right? We will make it exactly as you imagine it',
        custom_metal: 'Metal type',
        metal_18k: '18K Gold',
        metal_14k: '14K Gold (best value)',
        metal_silver: 'Silver',
        custom_color: 'Colour',
        color_white: 'White',
        color_yellow: 'Yellow',
        color_rose: 'Rose gold',
        custom_cut: 'Diamond cut',
        cut_round: 'Round',
        cut_oval: 'Oval',
        cut_pear: 'Pear',
        cut_marquise: 'Marquise',
        cut_emerald: 'Emerald',
        cut_cushion: 'Cushion',
        cut_princess: 'Princess',
        cut_heart: 'Heart',
        cut_radiant: 'Radiant',
        cut_asscher: 'Asscher',
        custom_details: 'Additional notes (optional)',
        custom_phone: 'Mobile number *',
        btn_send: 'Send request',
        custom_success: 'We will contact you within 48 hours with the final price',
        quote: 'As coal needs time and pressure to become a diamond,<br>your one-of-a-kind piece deserves a moment of patience to be born complete.',
        btn_whatsapp: 'Send via WhatsApp',

        footer_desc: 'Every piece IGI certified • Insured shipping across the Kingdom',

        // Keys used inside the script
        from: 'From',
        currency: 'SAR',
        carat: 'Carat',
        cut: 'Cut',
        color: 'Metal',
        cash_payment: 'Cash / bank transfer',
        tabby_payment: 'Tabby / Tamara',
        market_compare: 'Market comparison',
        savings_text: 'Our price is',
        savings_suffix: 'lower than traditional jewellers',
        contact_whatsapp: 'Contact us on WhatsApp',
        lang_switch: 'العربية'
    }
};

/* ---------- 4. التتبّع | Lightweight local analytics ----------
   يُخزَّن في متصفح الزائر فقط (localStorage). لا يُرسل لأي خادم.
   Stored in the visitor's own browser only — nothing is sent anywhere.
   لوحة الإدارة admin.html تقرأ هذه البيانات. */
const STORE_KEYS = {
    views: 'lumiere_product_views',
    requests: 'lumiere_custom_requests'
};

function readStore(key, fallback) {
    try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
        return fallback;
    }
}

function writeStore(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        /* التخزين ممتلئ أو محظور — نتجاهل بهدوء */
    }
}

function trackProductView(productId) {
    const views = readStore(STORE_KEYS.views, {});
    views[productId] = (views[productId] || 0) + 1;
    writeStore(STORE_KEYS.views, views);
}

function trackCustomRequest(request) {
    const requests = readStore(STORE_KEYS.requests, []);
    requests.push(request);
    writeStore(STORE_KEYS.requests, requests);
}
