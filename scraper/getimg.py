import json,os,hashlib,concurrent.futures as cf,urllib.request,gzip,io
from PIL import Image
items=json.load(open('items.json'))
urls=sorted({i['image'] for i in items if i.get('image')})
print("unique images:",len(urls))
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def key(u): return hashlib.md5(u.encode()).hexdigest()
def opt(u):
    # ask CDNs for a reasonably sized render
    if 'cdn.shopify.com' in u:
        base,_,q=u.partition('?')
        for ext in ('.jpg','.jpeg','.png','.webp'):
            if base.lower().endswith(ext): return base[:-len(ext)]+'_600x'+ext+(('?'+q) if q else '')
    return u
def get(u):
    out=f"img/{key(u)}.png"
    if os.path.exists(out): return 'skip'
    for attempt in range(3):
        try:
            r=urllib.request.Request(opt(u) if attempt==0 else u,
                headers={'User-Agent':UA,'Accept':'image/avif,image/webp,image/*,*/*;q=0.8','Referer':'https://www.google.com/'})
            d=urllib.request.urlopen(r,timeout=45).read()
            im=Image.open(io.BytesIO(d)); im.load()
            if im.mode in ('RGBA','LA','P'):
                bg=Image.new('RGB',im.size,(255,255,255))
                im=im.convert('RGBA'); bg.paste(im,mask=im.split()[-1]); im=bg
            else: im=im.convert('RGB')
            im.thumbnail((300,300),Image.LANCZOS)
            canvas=Image.new('RGB',(300,300),(255,255,255))
            canvas.paste(im,((300-im.width)//2,(300-im.height)//2))
            canvas.save(out,'PNG',optimize=True)
            return 'ok'
        except Exception as e: err=str(e)[:50]
    return 'FAIL:'+err
with cf.ThreadPoolExecutor(12) as ex: res=list(ex.map(get,urls))
import collections;print(collections.Counter(r.split(':')[0] for r in res))
print([r for r in res if r.startswith('FAIL')][:3])
