import json,re
items=json.load(open('items.json'))

def mm_all(*texts):
    for t in texts:
        if not t: continue
        m=re.search(r'(\d+(?:\.\d+)?)\s*[x*×]\s*(\d+(?:\.\d+)?)\s*mm',t,re.I)
        if m: return f"{m.group(1)}×{m.group(2)}mm"
        m=re.search(r'(\d+(?:\.\d+)?)\s*mm',t,re.I)
        if m: return f"{m.group(1)}mm"
    return ''

def stone_spec(v,desc):
    """Human-readable stone spec when no carat weight is published."""
    if v:
        s=re.sub(r'^\s*(18k[^/]*|s?925[^/]*|silver[^/]*)\s*/\s*','',v,flags=re.I).strip()
        s=re.sub(r'\s*/\s*(us\s*)?\d+(\.\d+)?\s*$','',s,flags=re.I).strip()   # trailing ring size
        if s and not re.fullmatch(r'(default title|18k gold|s925|silver)',s,re.I): return s[:60]
    m=re.search(r'stone\s*spec\s*[:：]\s*([^|]{3,60})',desc or '',re.I)
    return m.group(1).strip() if m else ''

def clean_desc(d,metal_detail):
    if not d: return ''
    d=re.sub(r'\b(ITEM\s*DETAILS|Item Details|Product Specifications)\b\s*[:：]?','',d,flags=re.I)
    # drop contradictory metal statements - the Metal column is authoritative (variant-level)
    d=re.sub(r'\bMetal(?:\s*Material)?\s*[:：]\s*[^|]{0,40}?(?=(Stone|Band|Please|Diamond|Setting|Main|Product|$))','',d,flags=re.I)
    d=re.sub(r'\s{2,}',' ',d).strip(' .,|')
    return d

nm=ns=0
for i in items:
    if not i['mm']:
        got=mm_all(i['variant'],i['title'],i['desc'])
        if got: i['mm']=got; nm+=1
    i['stone_spec']=stone_spec(i['variant'],i['desc'])
    # unified weight/size display
    if i['carat']: i['weight_display']=f"{i['carat']:g} ct"
    elif i['mm']:  i['weight_display']=i['mm']+(' (per stone)' if i['mm'] else '')
    else:          i['weight_display']=i['stone_spec'] or 'not stated'
    if not i['carat'] and not i['mm'] and not i['stone_spec']: ns+=1
    i['desc']=clean_desc(i['desc'],i['metal_detail'])

json.dump(items,open('items.json','w'))
print("mm recovered:",nm,"| rows with no weight info at all:",ns)
print("carat:",sum(1 for i in items if i['carat']),"/",len(items))
print("mm:",sum(1 for i in items if i['mm']))
print("\nsamples:")
for i in items[:3]+items[600:602]:
    print(f"  {i['weight_display']:22s} | {i['title'][:50]}")
    print(f"      desc: {i['desc'][:100]}")
