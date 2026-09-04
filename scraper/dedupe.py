import json,re,collections
rows=json.load(open('rows_kept.json'))

STOP=set("""the a an and or of for with in on at to by from your our new hot sale best
gift gifts women womens men mens ladies her him style styles classic elegant stunning
luxury luxurious beautiful gorgeous exquisite fine solid real genuine quality copy
group order promotion cut shape jewelry jewellery piece pcs set""".split())
NOISE=re.compile(r'\((?:copy|copy \d+)\)|\[[^\]]*\]|\bcopy\b|[®™©*]',re.I)

def norm_tokens(t):
    t=NOISE.sub(' ',t.lower())
    t=re.sub(r'\d+(?:\.\d+)?\s*(?:ct|carat)s?\s*(?:tw|t\.w\.)?',' ',t)   # carat handled separately
    t=re.sub(r'[^a-z0-9 ]',' ',t)
    toks=[w for w in t.split() if w not in STOP and len(w)>2 and not w.isdigit()]
    return tuple(sorted(set(toks)))

def sig(r):
    ct=r['carat']
    ctb=round(ct,2) if ct else None
    return (norm_tokens(r['title']), r['metal'], ctb, r['kind'])

groups=collections.defaultdict(list)
for r in rows: groups[sig(r)].append(r)

items=[]
for k,g in groups.items():
    g.sort(key=lambda x:(x['price'], x['source']))
    best=dict(g[0])
    best['dup_count']=len(g)
    best['all_sources']=sorted({x['source'] for x in g})
    best['cross_source']=len(best['all_sources'])>1
    prices={x['source']:min(y['price'] for y in g if y['source']==x['source']) for x in g}
    best['price_by_source']=prices
    best['max_price']=max(x['price'] for x in g)
    best['n_variants_collapsed']=len(g)
    items.append(best)

items.sort(key=lambda x:(x['source'],x['kind'],x['price']))
json.dump(items,open('items.json','w'))
print("unique items:",len(items))
print("collapsed from:",len(rows),"variant rows")
cs=[i for i in items if i['cross_source']]
print("cross-source duplicate groups:",len(cs))
for i in cs[:10]:
    print("   ",i['all_sources'],"->",i['price_by_source'],"|",i['title'][:60])
print("\nby source (winner):",dict(collections.Counter(i['source'] for i in items)))
print("by metal:",dict(collections.Counter(i['metal'] for i in items)))
print("by kind:",dict(collections.Counter(i['kind'] for i in items).most_common()))
print("multi-variant groups:",sum(1 for i in items if i['dup_count']>1))
