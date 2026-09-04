import json,re,collections
rows=json.load(open('rows_raw.json'))

GEMS=[('lab diamond',  r'lab[\s\-]*(?:grown|created)?[\s\-]*diamonds?'),
      ('diamond',      r'\bdiamonds?\b'),
      ('moissanite',   r'moissanites?'),
      ('paraiba',      r'paraiba'), ('padparadscha',r'padparadscha'),
      ('moss agate',   r'moss\s*agate'), ('agate',r'\bagate\b'),
      ('sapphire',     r'sapphires?'), ('ruby',r'\brub(?:y|ies)\b'),
      ('emerald',      r'\bemeralds?\b(?!\s*cut)'),
      ('cz',           r'cubic\s*zirconias?|\bcz\b|zircon(?!ia)'),
      ('opal',r'\bopals?\b'),('pearl',r'\bpearls?\b'),('topaz',r'\btopaz\b'),
      ('amethyst',r'\bamethyst\b'),('aquamarine',r'\baquamarine\b'),
      ('morganite',r'\bmorganite\b'),('alexandrite',r'\balexandrite\b'),
      ('spinel',r'\bspinel\b'),('tourmaline',r'\btourmaline\b'),
      ('garnet',r'\bgarnet\b'),('peridot',r'\bperidot\b'),('citrine',r'\bcitrine\b'),
      ('turquoise',r'\bturquoise\b'),('onyx',r'\bonyx\b'),('tanzanite',r'\btanzanite\b'),
      ('kunzite',r'\bkunzite\b'),('moonstone',r'\bmoonstone\b'),('jade',r'\bjade\b'),
      ('malachite',r'\bmalachite\b'),('larimar',r'\blarimar\b'),
      ('gemstone',r'lab\s*gem\s*stones?|\bgem\s*stones?\b')]

def first_gem(text):
    best=None;bi=10**9
    for name,pat in GEMS:
        m=re.search(pat,text,re.I)
        if m and m.start()<bi: bi=m.start();best=name
    m=re.search(GEMS[0][1],text,re.I)          # 'lab diamond' wins ties vs 'diamond'
    if m and m.start()<=bi: best='lab diamond'
    return best

PLACEHOLDER=re.compile(r'other\s*(carat|color|size|weight)|or\s*other|custom(ize)?\b|contact\s*us|inquir',re.I)
STONE_SPEC=re.compile(r'stone\s*(?:type|spec|1)?\s*[:：]\s*([^|\n]{0,60})',re.I)

kept=[];drop=collections.Counter()
for r in rows:
    v=r['variant'] or ''
    if PLACEHOLDER.search(v) or r['price']>=250000:
        drop['placeholder / quote-only variant']+=1; continue
    if re.search(r'moissanite\s*(main|center)\s*stone',v,re.I):
        drop['moissanite is the main stone']+=1; continue

    # PRIORITY: the variant's own stone attribute is authoritative. Many listings
    # advertise every stone option in the title ("lab diamond/moissanite/lab gemstone")
    # while the selected variant decides the actual stone.
    g=None; origin=None
    sa=(r.get('stone_attr') or '').strip()
    if sa:
        g=first_gem(sa); origin='variant stone attribute'
    if g is None:
        g=first_gem(r['title']); origin='title'
    if g is None:
        m=STONE_SPEC.search(r['desc'])
        if m: g=first_gem(m.group(1)); origin='description'
    if g is None:
        g=first_gem(v); origin='variant text'
    if g not in ('lab diamond','diamond'):
        drop[('main stone = '+g) if g else 'stone type not identifiable']+=1; continue
    if g=='diamond' and not re.search(r'lab|created|grown|cvd|hpht',r['title']+' '+r['desc'],re.I):
        drop['natural / unspecified diamond']+=1; continue

    r['main_stone']='Lab Grown Diamond'; r['stone_src']=origin
    kept.append(r)

print("kept variant rows:",len(kept))
for k,v in drop.most_common(): print(f"   dropped {v:5d}  {k}")
json.dump(kept,open('rows_kept.json','w'))
print("\nby source:",dict(collections.Counter(r['source'] for r in kept)))
print("by metal:",dict(collections.Counter(r['metal'] for r in kept)))
print("distinct products:",len({(r['site'],r['title']) for r in kept}))
