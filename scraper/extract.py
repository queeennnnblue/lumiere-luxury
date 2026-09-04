import json,glob,re,html,os,collections

def clean(t):
    if not t: return ''
    t=re.sub(r'<(script|style)[^>]*>.*?</\1>',' ',t,flags=re.S|re.I)
    t=re.sub(r'<[^>]+>',' ',t)
    return re.sub(r'\s+',' ',html.unescape(t)).strip()

# ---------- metal classification ----------
def metal_of(text):
    """Return '18K Gold' / '925 Silver' / None for a variant/metal string."""
    if not text: return None
    t=text.lower()
    if re.search(r'\b(925|s925|sterling)\b',t) or re.search(r'\bsilver\b',t): 
        # gold-plated silver is still a silver base item
        return '925 Silver'
    if re.search(r'\b18\s*k(t)?\b',t) or '18karat' in t:
        return '18K Gold'
    return None

def metal_detail(text):
    t=text or ''
    for pat,lab in [(r'18k\s*white',   '18K White Gold'),
                    (r'18k\s*yellow',  '18K Yellow Gold'),
                    (r'18k\s*rose',    '18K Rose Gold'),
                    (r'18k',           '18K Gold'),
                    (r's?925|sterling',      '925 Sterling Silver'),
                    (r'silver',        '925 Sterling Silver')]:
        if re.search(pat,t,re.I): return lab
    return ''

# ---------- lab diamond detection ----------
LAB_POS=re.compile(r'lab[\s\-_]*(grown|created|made)?[\s\-_]*diamond|lgd\b|cvd\s*diamond|hpht',re.I)
BAD=re.compile(r'moissanite|cubic\s*zirconia|\bcz\b|zircon|sapphire|ruby|emerald(?!\s*cut)|opal|pearl|topaz|amethyst|aquamarine|morganite|alexandrite|spinel|tourmaline|garnet|peridot|citrine|turquoise|onyx|agate|crystal',re.I)

def is_lab_diamond(strong, weak):
    """strong = title/stone-attribute text (authoritative); weak = description."""
    if LAB_POS.search(strong): return True
    if BAD.search(strong): return False
    if LAB_POS.search(weak or ''):
        # description says lab diamond and title doesn't contradict
        return not BAD.search(strong)
    return False

# ---------- carat weight ----------
def carat(*texts):
    for t in texts:
        if not t: continue
        m=re.search(r'(\d+(?:\.\d+)?)\s*(?:ct|carat)s?\s*(?:tw|t\.w\.|total)?',t,re.I)
        if m:
            v=float(m.group(1))
            if 0.005<=v<=30: return v
    return None

def mm_size(*texts):
    for t in texts:
        if not t: continue
        m=re.search(r'(\d+(?:\.\d+)?)\s*[x*×]\s*(\d+(?:\.\d+)?)\s*mm',t,re.I)
        if m: return f"{m.group(1)}×{m.group(2)}mm"
        m=re.search(r'(\d+(?:\.\d+)?)\s*mm',t,re.I)
        if m: return f"{m.group(1)}mm"
    return ''

def kind_of(t):
    t=(t or '').lower()
    for pat,lab in [(r'engagement ring|bridal set',  'Engagement Ring'),
                    (r'wedding band|wedding ring|eternity','Wedding/Eternity Band'),
                    (r'tennis bracelet','Tennis Bracelet'),
                    (r'bracelet|bangle','Bracelet'),
                    (r'tennis necklace','Tennis Necklace'),
                    (r'necklace|chain','Necklace'),
                    (r'pendant','Pendant'),
                    (r'stud','Stud Earrings'),
                    (r'hoop|huggie','Hoop Earrings'),
                    (r'earring','Earrings'),
                    (r'\bring\b','Ring'),
                    (r'\bset\b','Jewelry Set'),
                    (r'cufflink','Cufflinks'),
                    (r'watch','Watch'),
                    (r'grill|teeth','Grillz')]:
        if re.search(pat,t): return lab
    return 'Jewelry'

# is this finished jewelry (not a loose stone)?
LOOSE=re.compile(r'loose|melee|parcel|per\s*carat|rough|\bstone only\b',re.I)
JEWEL=re.compile(r'ring|earring|necklace|pendant|bracelet|bangle|chain|stud|hoop|huggie|cufflink|charm|anklet|brooch|grill|band|set\b',re.I)

rows=[]

# ================= SHOPIFY (lgg + fiorese) =================
SHOPS={'lggjewelry':('LGG Jewelry','https://www.lggjewelry.com'),
       'fioresejewelry':('Fiorese Jewelry','https://fioresejewelry.com')}
for key,(label,base) in SHOPS.items():
    for f in sorted(glob.glob(f'raw/{key}_p*.json')):
        for p in json.load(open(f))['products']:
            title=p['title']; body=clean(p.get('body_html'))
            tags=' '.join(p.get('tags') or []); ptype=p.get('product_type') or ''
            head=' | '.join([title,ptype,tags])
            if LOOSE.search(title) or not JEWEL.search(head): continue
            opt_names=[o['name'] for o in p.get('options',[])]
            # index of the metal option
            mi=next((i for i,n in enumerate(opt_names) if re.search(r'metal|material',n,re.I)),None)
            side_i=[i for i,n in enumerate(opt_names) if re.search(r'side\s*stone',n,re.I)]
            stone_opt_i=[i for i,n in enumerate(opt_names)
                         if re.search(r'stone|diamond',n,re.I) and i not in side_i]
            link=f"{base}/products/{p['handle']}"
            imgs={im['id']:im['src'] for im in p.get('images',[])}
            main_img=p['images'][0]['src'] if p.get('images') else ''
            for v in p['variants']:
                opts=[v.get('option1'),v.get('option2'),v.get('option3')]
                vt=v.get('title') or ''
                mtext = opts[mi] if (mi is not None and mi<len(opts)) else vt
                metal=metal_of(mtext) or (metal_of(head) if mi is None else None)
                if not metal: continue
                # stone signal from variant options + option NAMES + title
                stone_text=' '.join([opts[i] or '' for i in stone_opt_i]).strip()
                if not stone_text and any(re.search(r'lab\s*diamond',n,re.I) for n in opt_names):
                    stone_text='lab diamond'
                strong=' '.join([title,ptype,tags,stone_text])
                if not is_lab_diamond(strong,body): continue
                try: price=float(v['price'])
                except: continue
                if price<=0: continue
                ct=carat(stone_text,vt,title,body)
                img=imgs.get((v.get('featured_image') or {}).get('id')) if v.get('featured_image') else None
                rows.append(dict(source=label,site=key,title=title,variant=vt,
                    metal=metal,metal_detail=metal_detail(mtext) or metal_detail(head),
                    kind=kind_of(head),carat=ct,mm=mm_size(stone_text,title),
                    grams=(v.get('grams') or 0)/1000 or None, stone_attr=stone_text,
                    price=price,link=link,image=img or main_img,desc=body,sku=v.get('sku') or ''))

# ================= PROVENCEGEMS =================
AJAX_PENDING=[]
prov={}
for f in glob.glob('raw/provence_p*.json'):
    for p in json.load(open(f)): prov[p['id']]=p
for path in glob.glob('pages/prov_*.html'):
    pid=int(re.search(r'prov_(\d+)',path).group(1))
    p=prov.get(pid)
    if not p: continue
    h=open(path,encoding='utf-8',errors='ignore').read()
    m=re.search(r'data-product_variations="(.*?)"\s*(?:>|data-)',h,re.S)
    if not m: continue
    try: variations=json.loads(html.unescape(m.group(1)))
    except Exception: continue
    if not isinstance(variations,list):
        AJAX_PENDING.append(pid); continue
    title=clean(p['name']); body=clean(p.get('short_description') or p.get('description'))
    if LOOSE.search(title) or not JEWEL.search(title): continue
    main_img=p['images'][0]['src'] if p.get('images') else ''
    for v in variations:
        at=v.get('attributes') or {}
        mtext=' '.join(str(x) for k,x in at.items() if re.search(r'metal',k,re.I) and x)
        stext=' '.join(str(x) for k,x in at.items() if re.search(r'stone',k,re.I) and x)
        metal=metal_of(mtext)
        if not metal: continue
        strong=' '.join([title,stext.replace('-',' ')])
        if not is_lab_diamond(strong,body): continue
        pr=v.get('display_price')
        if pr in (None,'',0): continue
        price=float(pr)
        vlabel=', '.join(str(x).replace('-',' ').title() for x in at.values() if x)
        rows.append(dict(source='Provence Gems',site='provencegems',title=title,variant=vlabel,
            metal=metal,metal_detail=metal_detail(mtext),kind=kind_of(title),
            carat=carat(title,stext,body),mm=mm_size(title,body),grams=None,
            price=price,link=p['permalink'],image=(v.get('image') or {}).get('src') or main_img,
            stone_attr=stext.replace('-',' '),
            desc=body,sku=v.get('sku') or ''))

json.dump(AJAX_PENDING,open("prov_ajax_pending.json","w"))
json.dump(rows,open('rows_raw.json','w'))
print("qualifying variant rows:",len(rows))
print(collections.Counter(r['source'] for r in rows))
print(collections.Counter(r['metal'] for r in rows))
print("with carat:",sum(1 for r in rows if r['carat']))
