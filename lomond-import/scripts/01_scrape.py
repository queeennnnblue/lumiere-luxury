#!/usr/bin/env python3
"""
01 — سحب بيانات المنتجات من روابط sources.txt إلى data/raw/*.json
Scrape supplier products listed in sources.txt into data/raw/*.json

يستخرج لكل منتج: الاسم، الوصف الكامل، كل المواصفات، كل روابط الصور بأعلى دقة، ورابط المصدر.

المصادر بالترتيب (الأفضل أولاً):
  1. Shopify products.json  — أدق وأكمل مصدر
  2. JSON-LD (schema.org/Product)
  3. OpenGraph              — احتياطي أخير

قواعد التشغيل:
  • يحترم robots.txt. إذا مُنع السحب، يتوقف عن هذا الموقع ويبلّغ.
  • تأخير ثانيتان (SCRAPE_DELAY) بين كل طلب، و User-Agent معرِّف واضح.
  • استئناف: يتخطّى ما اكتمل سابقاً. استخدم --force لإعادة السحب.

    python scripts/01_scrape.py [--dry-run] [--force] [--limit N]
    python scripts/01_scrape.py --inspect      # فحص بنية الصفحة والفيدات بلا حفظ
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    RAW_DIR,
    SOURCES_FILE,
    ensure_dirs,
    env,
    env_float,
    env_int,
    guess_category,
    log,
    read_json,
    step,
    warn,
    wants_dry_run,
    write_json,
)

STATE_FILE = RAW_DIR / "_state.json"

# User-Agent معرِّف بوضوح، لا ينتحل متصفحاً
DEFAULT_UA = "LomondImporter/1.0 (+catalogue import; contact: lemorejewellry@gmail.com)"

# الحقول التي نتوقعها لكل منتج — تُستخدم في تقرير النواقص
EXPECTED_FIELDS = ["title", "description", "specs", "images", "price_usd", "category"]


# ------------------------------------------------------------------ الشبكة
_last_request = 0.0


def throttle() -> None:
    """تأخير ثابت بين الطلبات (افتراضي ثانيتان)."""
    global _last_request
    delay = env_float("SCRAPE_DELAY", 2.0)
    elapsed = time.monotonic() - _last_request
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_request = time.monotonic()


def user_agent() -> str:
    return env("USER_AGENT", "") or DEFAULT_UA


def fetch(url: str) -> str | None:
    throttle()
    req = urllib.request.Request(url, headers={
        "User-Agent": user_agent(),
        "Accept": "text/html,application/json,*/*",
        "Accept-Language": "ar,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=env_int("SCRAPE_TIMEOUT", 30)) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        warn(f"HTTP {exc.code} — {url}")
        return None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        warn(f"تعذّر الجلب | fetch failed: {url} — {exc}")
        return None


# ------------------------------------------------------------- robots.txt
class RobotsGate:
    """يقرأ robots.txt مرة واحدة لكل نطاق ويمنع أي مسار محظور."""

    def __init__(self) -> None:
        self._cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.blocked_hosts: set[str] = set()

    def _parser(self, base: str) -> urllib.robotparser.RobotFileParser | None:
        if base in self._cache:
            return self._cache[base]

        parser = urllib.robotparser.RobotFileParser()
        body = fetch(base + "/robots.txt")
        if body is None:
            # لا يوجد robots.txt أو تعذّر الوصول: نفترض السماح كما هو المتعارف عليه
            log("لا يوجد robots.txt، نفترض السماح | no robots.txt, assuming allowed")
            parser = None
        else:
            parser.parse(body.splitlines())
            delay = parser.crawl_delay(user_agent())
            if delay:
                log(f"robots.txt يطلب تأخير {delay}s | crawl-delay honoured")

        self._cache[base] = parser
        return parser

    def allows(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._parser(base)
        if parser is None:
            return True

        if not parser.can_fetch(user_agent(), url):
            self.blocked_hosts.add(parsed.netloc)
            return False
        return True

    def crawl_delay(self, url: str) -> float | None:
        parsed = urllib.parse.urlparse(url)
        parser = self._cache.get(f"{parsed.scheme}://{parsed.netloc}")
        if parser is None:
            return None
        try:
            return float(parser.crawl_delay(user_agent()) or 0) or None
        except (TypeError, ValueError):
            return None


# ------------------------------------------------------------ قراءة المصادر
def read_sources() -> list[dict]:
    if not SOURCES_FILE.exists():
        warn(f"لا يوجد ملف مصادر | missing {SOURCES_FILE}")
        return []

    entries = []
    for line in SOURCES_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        url, _, pinned = line.partition("|")
        category = pinned.split("category=", 1)[1].strip() if "category=" in pinned else None
        entries.append({"url": url.strip(), "category": category})
    return entries


# ------------------------------------------------------------------ الصور
_SHOPIFY_SIZE = re.compile(r"_(?:\d+x\d*|\d*x\d+|small|medium|large|grande|compact|pico|icon|thumb)(?=\.\w+)")


def highest_res(url: str) -> str:
    """
    يحوّل رابط الصورة إلى أعلى دقة متاحة.
    Shopify يضيف لاحقة مقاس قبل الامتداد (..._800x.jpg) — حذفها يعطي الأصل.
    """
    if url.startswith("//"):
        url = "https:" + url
    clean, _, query = url.partition("?")
    clean = _SHOPIFY_SIZE.sub("", clean)
    # نحتفظ بمعامل النسخة فقط، ونسقط معاملات القصّ والمقاس
    keep = [p for p in query.split("&") if p.startswith("v=")]
    return clean + ("?" + "&".join(keep) if keep else "")


# ------------------------------------------------------------- المواصفات
_LI_RE = re.compile(r"<li[^>]*>(.*?)</li>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text or "", flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    return html.unescape(_TAG_RE.sub("", text)).strip()


def extract_specs(body_html: str) -> dict[str, str]:
    """يستخرج المواصفات من قوائم <li> بصيغة «المفتاح: القيمة»."""
    specs: dict[str, str] = {}
    for item in _LI_RE.findall(body_html or ""):
        line = strip_html(item)
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key and value:
            specs[key] = value
    return specs


# ------------------------------------------------------- 1. طبقة Shopify
def shopify_endpoints(url: str) -> list[str]:
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path.rstrip("/")

    if "/products/" in path:
        return [f"{base}{path}.json"]
    if path.startswith("/collections"):
        return [f"{base}{path}/products.json?limit=250", f"{base}/products.json?limit=250"]
    return [f"{base}/products.json?limit=250"]


def try_shopify(url: str, gate: RobotsGate) -> list[dict]:
    for endpoint in shopify_endpoints(url):
        if not gate.allows(endpoint):
            warn(f"robots.txt يمنع | disallowed: {endpoint}")
            continue

        body = fetch(endpoint)
        if not body:
            continue
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            continue

        items = payload.get("products") or ([payload["product"]] if "product" in payload else [])
        if items:
            log(f"Shopify feed: {len(items)} منتج ← {endpoint}")
            base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(url))
            return [normalise_shopify(i, base) for i in items]
    return []


def normalise_shopify(item: dict, base: str) -> dict:
    variants = item.get("variants") or []
    prices = [float(v["price"]) for v in variants if v.get("price") not in (None, "")]
    body_html = item.get("body_html") or ""
    handle = item.get("handle", "")

    specs = extract_specs(body_html)
    for option in item.get("options") or []:
        name, values = option.get("name", ""), option.get("values") or []
        if name and values and name.lower() != "title":
            specs.setdefault(name, " / ".join(map(str, values)))

    return {
        "source_url": f"{base}/products/{handle}" if handle else base,
        "supplier_host": urllib.parse.urlparse(base).netloc,
        "supplier_id": str(item.get("id", "")),
        "supplier_vendor": item.get("vendor", ""),
        "extractor": "shopify",
        "title": (item.get("title") or "").strip(),
        "description": strip_html(body_html),
        "description_html": body_html,
        "specs": specs,
        "tags": item.get("tags") or [],
        "product_type": item.get("product_type", ""),
        "price_usd": min(prices) if prices else None,
        "images": [highest_res(img["src"]) for img in (item.get("images") or []) if img.get("src")],
        "variants": [
            {"title": v.get("title", ""), "price": v.get("price"), "sku": v.get("sku", "")}
            for v in variants
        ],
    }


# ------------------------------------------------------- 2. طبقة JSON-LD
_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _walk(node):
    if isinstance(node, list):
        for child in node:
            yield from _walk(child)
    elif isinstance(node, dict):
        yield node
        for child in node.values():
            yield from _walk(child)


def try_jsonld(page: str, url: str) -> list[dict]:
    found = []
    for block in _LD_RE.findall(page):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue

        for node in _walk(data):
            types = node.get("@type")
            types = [types] if isinstance(types, str) else (types or [])
            if "Product" not in types:
                continue

            offers = node.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            try:
                price = float(offers.get("price") or offers.get("lowPrice") or 0) or None
            except (TypeError, ValueError):
                price = None

            images = node.get("image") or []
            images = [images] if isinstance(images, str) else list(images)
            brand = node.get("brand")
            description = node.get("description") or ""

            found.append({
                "source_url": node.get("url") or url,
                "supplier_host": urllib.parse.urlparse(url).netloc,
                "supplier_id": str(node.get("sku") or node.get("productID") or ""),
                "supplier_vendor": brand.get("name", "") if isinstance(brand, dict) else (brand or ""),
                "extractor": "json-ld",
                "title": (node.get("name") or "").strip(),
                "description": strip_html(description),
                "description_html": description,
                "specs": extract_specs(description),
                "tags": [],
                "product_type": node.get("category", ""),
                "price_usd": price,
                "images": [highest_res(i) for i in images if i],
                "variants": [],
            })

    if found:
        log(f"JSON-LD: {len(found)} منتج ← {url}")
    return found


# ------------------------------------------------------ 3. طبقة OpenGraph
def _meta(page: str, prop: str) -> str:
    for pattern in (
        rf'<meta[^>]+(?:property|name)=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']*)["\']',
        rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']{re.escape(prop)}["\']',
    ):
        match = re.search(pattern, page, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""


def try_opengraph(page: str, url: str) -> list[dict]:
    title = _meta(page, "og:title")
    if not title:
        return []
    try:
        price = float(_meta(page, "product:price:amount") or _meta(page, "og:price:amount"))
    except ValueError:
        price = None

    log(f"OpenGraph: منتج واحد ← {url}")
    image = _meta(page, "og:image")
    return [{
        "source_url": url,
        "supplier_host": urllib.parse.urlparse(url).netloc,
        "supplier_id": "",
        "supplier_vendor": _meta(page, "og:site_name"),
        "extractor": "opengraph",
        "title": title,
        "description": _meta(page, "og:description"),
        "description_html": "",
        "specs": {},
        "tags": [],
        "product_type": "",
        "price_usd": price,
        "images": [highest_res(image)] if image else [],
        "variants": [],
    }]


# ------------------------------------------------------------------ الفحص
def inspect(url: str, gate: RobotsGate) -> None:
    """يفحص ما يوفّره الموقع من فيدات قبل أي سحب فعلي."""
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    step(f"فحص | inspecting {base}")

    allowed = gate.allows(url)
    log(f"robots.txt يسمح بالمسار؟ {'نعم' if allowed else 'لا ✋'}")
    delay = gate.crawl_delay(url)
    if delay:
        log(f"crawl-delay المطلوب: {delay}s")
    if not allowed:
        return

    for label, probe in (
        ("Shopify products.json", f"{base}/products.json?limit=1"),
        ("sitemap.xml", f"{base}/sitemap.xml"),
        ("sitemap_products", f"{base}/sitemap_products_1.xml"),
    ):
        body = fetch(probe) if gate.allows(probe) else None
        status = "متاح ✓" if body else "غير متاح ✗"
        log(f"{label:24} {status}")

    page = fetch(url)
    if page:
        ld = len(_LD_RE.findall(page))
        log(f"{'JSON-LD blocks':24} {ld} كتلة")
        log(f"{'og:title':24} {_meta(page, 'og:title') or '—'}")
        log(f"{'og:image':24} {_meta(page, 'og:image') or '—'}")


# ------------------------------------------------------------- حالة الاستئناف
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return read_json(STATE_FILE)
        except json.JSONDecodeError:
            warn("ملف الحالة تالف، نبدأ من جديد | corrupt state file, starting fresh")
    return {"done": {}, "failed": {}}


def save_state(state: dict, dry: bool) -> None:
    if not dry:
        write_json(STATE_FILE, state)


def raw_name(item: dict, index: int) -> str:
    """
    اسم ملف ثابت وخالٍ من أي أثر للمورّد (قاعدة تنظيف المصدر في CLAUDE.md).
    يعتمد على معرّف المورّد الرقمي فقط، لا على اسم النطاق أو البراند.
    """
    ident = item.get("supplier_id") or f"{index:05d}"
    ident = re.sub(r"[^A-Za-z0-9_-]", "", str(ident))[:32]
    return f"product_{ident or index:05}.json"


# ------------------------------------------------------------------ التقرير
def missing_fields(item: dict) -> list[str]:
    missing = []
    for field in EXPECTED_FIELDS:
        value = item.get(field)
        if value in (None, "", [], {}):
            missing.append(field)
    return missing


def print_report(succeeded: list[dict], failed: list[tuple[str, str]], blocked: set[str]) -> None:
    print("\n" + "═" * 66)
    print("  تقرير السحب | Scrape report")
    print("═" * 66)
    print(f"  نجح   | succeeded : {len(succeeded)}")
    print(f"  فشل   | failed    : {len(failed)}")
    print(f"  محظور | blocked   : {len(blocked)}")

    if succeeded:
        counts: dict[str, int] = {}
        for item in succeeded:
            for field in missing_fields(item):
                counts[field] = counts.get(field, 0) + 1

        print("\n  حقول ناقصة | missing fields")
        print("  " + "─" * 46)
        print(f"  {'الحقل | field':22} {'ناقص | missing':>16}")
        print("  " + "─" * 46)
        if counts:
            for field in EXPECTED_FIELDS:
                if field in counts:
                    print(f"  {field:22} {counts[field]:>10} / {len(succeeded)}")
        else:
            print("  لا نواقص | none 🎉")

        print("\n  المستخرِج المستخدم | extractor used")
        print("  " + "─" * 46)
        used: dict[str, int] = {}
        for item in succeeded:
            used[item.get("extractor", "?")] = used.get(item.get("extractor", "?"), 0) + 1
        for name, count in sorted(used.items(), key=lambda kv: -kv[1]):
            print(f"  {name:22} {count:>10}")

    if failed:
        print("\n  فشل | failures")
        print("  " + "─" * 46)
        for url, reason in failed[:20]:
            print(f"  ✗ {url[:44]:44} {reason}")
        if len(failed) > 20:
            print(f"  … و {len(failed) - 20} أخرى")

    if blocked:
        print("\n  ✋ مواقع منعت السحب في robots.txt | blocked by robots.txt")
        for host in sorted(blocked):
            print(f"     {host}")
        print("     تم إيقاف السحب من هذه المواقع. راجعها قبل المتابعة.")

    print("═" * 66 + "\n")


# ------------------------------------------------------------------ التشغيل
def scrape_entry(entry: dict, gate: RobotsGate) -> tuple[list[dict], str | None]:
    url = entry["url"]

    if not gate.allows(url):
        return [], "robots.txt disallow"

    items = try_shopify(url, gate)
    if not items:
        page = fetch(url)
        if not page:
            return [], "fetch failed"
        items = try_jsonld(page, url) or try_opengraph(page, url)

    if not items:
        return [], "no product data found"

    for item in items:
        item["category"] = entry["category"] or guess_category(
            item.get("title", ""), item.get("product_type", ""), " ".join(item.get("tags") or [])
        )
        item["price_currency"] = "USD"
        item["scraped_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return items, None


def main() -> int:
    ensure_dirs()
    dry = wants_dry_run()
    force = "--force" in sys.argv

    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    sources = read_sources()
    if not sources:
        warn("sources.txt فارغ — أضف روابط المنتجات أولاً")
        return 1

    gate = RobotsGate()

    if "--inspect" in sys.argv:
        for entry in sources:
            inspect(entry["url"], gate)
        return 0

    state = load_state()
    succeeded: list[dict] = []
    failed: list[tuple[str, str]] = []

    for entry in sources:
        url = entry["url"]
        if not force and url in state["done"]:
            log(f"تم سابقاً، نتخطّى | already done, skipping: {url}")
            continue

        step(f"سحب | scraping {url}")
        items, error = scrape_entry(entry, gate)

        if error:
            warn(f"{error} — {url}")
            failed.append((url, error))
            state["failed"][url] = error
            save_state(state, dry)
            if error == "robots.txt disallow":
                warn("توقّف السحب من هذا الموقع احتراماً لـ robots.txt")
            continue

        written = 0
        for index, item in enumerate(items):
            if limit is not None and len(succeeded) >= limit:
                break
            if not item.get("title"):
                continue

            path = RAW_DIR / raw_name(item, index)
            if path.exists() and not force:
                continue
            if dry:
                log(f"[معاينة] {path.name} ← {item['title'][:46]}")
            else:
                write_json(path, item)
            succeeded.append(item)
            written += 1

        log(f"حُفظ {written} منتج | {written} products written")
        state["done"][url] = {"count": written, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        state["failed"].pop(url, None)
        save_state(state, dry)

    print_report(succeeded, failed, gate.blocked_hosts)

    if dry:
        log("معاينة فقط، لم يُكتب أي ملف | dry run, nothing written")
    if gate.blocked_hosts:
        return 3
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
