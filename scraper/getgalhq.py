import json,os,hashlib,io,concurrent.futures as cf,urllib.request,collections
from PIL import Image
urls=json.load(open('gallery_urls.json'))
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def key(u): return hashlib.md5(u.encode()).hexdigest()
def opt(u):
    if 'cdn.shopify.com' in u:
        b,_,q=u.partition('?')
        for e in ('.jpg','.jpeg','.png','.webp'):
            if b.lower().endswith(e): return b[:-len(e)]+'_600x'+e+(('?'+q) if q else '')
    return u
def get(u):
    out='galhq/'+key(u)+'.jpg'
    if os.path.exists(out): return 'skip'
    for a in range(3):
        try:
            r=urllib.request.Request(opt(u) if a==0 else u,
              headers={'User-Agent':UA,'Accept':'image/avif,image/webp,image/*,*/*;q=0.8'})
            d=urllib.request.urlopen(r,timeout=45).read()
            im=Image.open(io.BytesIO(d)); im.load()
            if im.mode in ('RGBA','LA','P'):
                bg=Image.new('RGB',im.size,(255,255,255)); im=im.convert('RGBA')
                bg.paste(im,mask=im.split()[-1]); im=bg
            else: im=im.convert('RGB')
            im.thumbnail((440,440),Image.LANCZOS)
            c=Image.new('RGB',(440,440),(255,255,255))
            c.paste(im,((200-im.width)//2,(200-im.height)//2))
            c.save(out,'JPEG',quality=88,optimize=True,progressive=True)
            return 'ok'
        except Exception as e: err=str(e)[:40]
    return 'FAIL'
with cf.ThreadPoolExecutor(16) as ex: res=list(ex.map(get,urls))
print(collections.Counter(res))
