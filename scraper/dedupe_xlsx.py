"""Deduplicate identical embedded images inside an .xlsx.

openpyxl writes one copy of a picture per anchor, so a gallery that repeats the
same photo across rows bloats the file. This rewrites the drawing relationships
to point every duplicate at a single canonical media part and drops the rest.
"""
import zipfile,hashlib,re,shutil,sys,os

def dedupe(path):
    src=zipfile.ZipFile(path)
    names=src.namelist()
    media=[n for n in names if n.startswith('xl/media/')]
    canon={}; remap={}
    for n in sorted(media):
        h=hashlib.sha1(src.read(n)).hexdigest()
        if h in canon: remap[n]=canon[h]
        else: canon[h]=n
    keep=set(canon.values())
    if not remap:
        src.close(); return 0,len(media),len(keep)
    base={os.path.basename(k):os.path.basename(v) for k,v in remap.items()}
    tmp=path+'.tmp'
    out=zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=9)
    for item in src.infolist():
        n=item.filename
        if n.startswith('xl/media/') and n not in keep: continue
        data=src.read(n)
        if n.endswith('.rels') and b'media/' in data:
            t=data.decode('utf-8')
            def sub(m):
                prefix,f=m.group(1),m.group(2)
                return 'Target="'+prefix+base.get(f,f)+'"'
            t=re.sub(r'Target="((?:\.\./|/xl/)media/)([^"]+)"',sub,t)
            data=t.encode('utf-8')
        out.writestr(item,data)
    out.close(); src.close()
    shutil.move(tmp,path)
    return len(remap),len(media),len(keep)

if __name__=='__main__':
    for p in sys.argv[1:]:
        before=os.path.getsize(p)
        r,tot,kept=dedupe(p)
        after=os.path.getsize(p)
        print(f"{p}: {tot} media -> {kept} kept ({r} duplicates removed) | "
              f"{before/1e6:.1f} MB -> {after/1e6:.1f} MB")
