import json,glob,re,os,concurrent.futures as cf,urllib.request,gzip,io
prods=[]
for f in glob.glob('raw/provence_p*.json'): prods+=json.load(open(f))
def terms(p,pat):
    out=[]
    for a in p.get('attributes',[]):
        if re.search(pat,a['name'],re.I): out+=[t['name'] for t in a['terms']]
    return out
cand=[p for p in prods
      if any(re.search(r'lab.*diamond',s,re.I) for s in terms(p,'stone'))
      and any(re.search(r'18k|925|silver',m,re.I) for m in terms(p,'metal'))]
json.dump([p['id'] for p in cand],open('prov_cand_ids.json','w'))
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(p):
    out=f"pages/prov_{p['id']}.html"
    if os.path.exists(out) and os.path.getsize(out)>50000: return 'skip'
    url=p['permalink']+('&' if '?' in p['permalink'] else '?')+'wmc-currency=USD'
    for a in range(3):
        try:
            r=urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Encoding':'gzip','Accept-Language':'en-US,en;q=0.9'})
            d=urllib.request.urlopen(r,timeout=60).read()
            if d[:2]==b'\x1f\x8b': d=gzip.decompress(d)
            open(out,'wb').write(d); return 'ok'
        except Exception as e:
            err=str(e)[:60]
    return 'FAIL '+err
with cf.ThreadPoolExecutor(8) as ex:
    res=list(ex.map(get,cand))
import collections; print(collections.Counter(r.split()[0] for r in res))
print([r for r in res if r.startswith('FAIL')][:3])
