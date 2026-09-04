import json,os,hashlib,re,collections,sys
from openpyxl import Workbook
from openpyxl.styles import Font,Alignment,PatternFill,Border,Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
import dedupe_xlsx

IMGDIR=os.environ.get('IMGDIR','galx')
IMGPX=int(os.environ.get('IMGPX','96'))
MARKUP=2.10; SAR=3.75

items=json.load(open('items.json'))
PARTS=[('Part 1 — Fiorese Jewelry','Lab_Diamond_Jewelry_ALL_PHOTOS_Part1_Fiorese.xlsx',
        lambda i:i['source']=='Fiorese Jewelry'),
       ('Part 2 — Provence Gems & LGG Jewelry','Lab_Diamond_Jewelry_ALL_PHOTOS_Part2_Provence_LGG.xlsx',
        lambda i:i['source']!='Fiorese Jewelry')]

NAVY='FF1F3864'; ACCENT='FFD9E2F3'; ZEBRA='FFF7F9FC'; GREEN='FFE2EFDA'
thin=Side(style='thin',color='FFBFBFBF'); border=Border(left=thin,right=thin,top=thin,bottom=thin)
def key(u): return hashlib.md5(u.encode()).hexdigest()
def short(t,n):
    t=re.sub(r'\s+',' ',t or '').strip()
    return t if len(t)<=n else t[:n-1].rsplit(' ',1)[0]+'…'

for label,fname,pred in PARTS:
    rows=sorted([i for i in items if pred(i)],key=lambda x:(x['source'],x['kind'],x['price']))
    MAXP=max(len(i['gallery']) for i in rows)
    wb=Workbook(); ws=wb.active; ws.title='All Photos'

    INFO=[('#',6),('Product Name',40),('Description',50),('Weight',17),
          ('Metal',19),('Price (USD)',13),('FINAL PRICE (SAR)',20),('Source',16),('Photos',8)]
    NI=len(INFO); TOTAL=NI+MAXP

    ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=TOTAL)
    t=ws.cell(1,1,f'LAB DIAMOND JEWELRY — 18K GOLD & 925 SILVER — FULL PHOTO GALLERY — {label}')
    t.font=Font(size=16,bold=True,color='FFFFFFFF'); t.fill=PatternFill('solid',fgColor=NAVY)
    t.alignment=Alignment(horizontal='center',vertical='center'); ws.row_dimensions[1].height=30
    ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=TOTAL)
    s=ws.cell(2,1,'Every photo published for each piece · FINAL PRICE (SAR) = Price (USD) × 2.10 × 3.75 '
                  '— markup and exchange rate are editable on the Summary sheet · no links in this file')
    s.font=Font(size=10,italic=True,color=NAVY); s.fill=PatternFill('solid',fgColor=ACCENT)
    s.alignment=Alignment(horizontal='center',vertical='center'); ws.row_dimensions[2].height=18

    HR=3
    for c,(n,w) in enumerate(INFO,1):
        cell=ws.cell(HR,c,n); cell.font=Font(bold=True,color='FFFFFFFF',size=10)
        cell.fill=PatternFill('solid',fgColor=NAVY); cell.border=border
        cell.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
        ws.column_dimensions[get_column_letter(c)].width=w
    for k in range(MAXP):
        c=NI+1+k; cell=ws.cell(HR,c,f'Photo {k+1}')
        cell.font=Font(bold=True,color='FFFFFFFF',size=9)
        cell.fill=PatternFill('solid',fgColor='FF2E5C9A'); cell.border=border
        cell.alignment=Alignment(horizontal='center',vertical='center')
        ws.column_dimensions[get_column_letter(c)].width=round(IMGPX/7.0,1)
    ws.row_dimensions[HR].height=30

    r=HR+1; placed=0; missing=0
    for n,it in enumerate(rows,1):
        ws.row_dimensions[r].height=round(IMGPX*0.75+4)
        vals=[n,it['title'],short(it['desc'],500),it['weight_display'],
              it['metal_detail'] or it['metal'],round(it['price'],2),None,
              it['source'],len(it['gallery'])]
        for c,v in enumerate(vals,1):
            cell=ws.cell(r,c,v); cell.border=border
            cell.alignment=Alignment(vertical='center',wrap_text=(c in (2,3)),
                horizontal='center' if c in (1,4,5,8,9) else 'left')
            if r%2==0: cell.fill=PatternFill('solid',fgColor=ZEBRA)
        ws.cell(r,6).number_format='"$"#,##0.00'
        f=ws.cell(r,7,f"=F{r}*Summary!$B$3*Summary!$B$4")
        f.number_format='#,##0.00" SAR"'; f.font=Font(bold=True,color='FF006100')
        f.fill=PatternFill('solid',fgColor=GREEN); f.border=border
        f.alignment=Alignment(horizontal='center',vertical='center')
        for k,u in enumerate(it['gallery']):
            c=NI+1+k; cell=ws.cell(r,c); cell.border=border
            if r%2==0: cell.fill=PatternFill('solid',fgColor=ZEBRA)
            p=f'{IMGDIR}/{key(u)}.jpg'
            if os.path.exists(p):
                im=XLImage(p); im.width=im.height=IMGPX
                im.anchor=f'{get_column_letter(c)}{r}'; ws.add_image(im); placed+=1
            else: missing+=1
        r+=1
    ws.freeze_panes=f'{get_column_letter(NI+1)}{HR+1}'
    ws.auto_filter.ref=f'A{HR}:{get_column_letter(NI)}{r-1}'
    ws.sheet_view.showGridLines=False

    s2=wb.create_sheet('Summary'); s2.sheet_view.showGridLines=False
    s2.column_dimensions['A'].width=36; s2.column_dimensions['B'].width=74
    s2.merge_cells('A1:B1')
    c=s2.cell(1,1,f'FULL PHOTO GALLERY — {label}')
    c.font=Font(bold=True,size=13,color='FFFFFFFF'); c.fill=PatternFill('solid',fgColor=NAVY)
    c.alignment=Alignment(horizontal='center',vertical='center'); s2.row_dimensions[1].height=24
    # ---- editable pricing controls (referenced by every FINAL PRICE cell) ----
    lab=s2.cell(3,1,'Markup multiplier  (price + 110%)'); lab.font=Font(bold=True,size=10)
    v=s2.cell(3,2,MARKUP); v.number_format='0.00'; v.font=Font(bold=True,size=11,color='FF006100')
    v.fill=PatternFill('solid',fgColor='FFFFF2CC')
    lab=s2.cell(4,1,'USD → SAR exchange rate'); lab.font=Font(bold=True,size=10)
    v=s2.cell(4,2,SAR); v.number_format='0.0000'; v.font=Font(bold=True,size=11,color='FF006100')
    v.fill=PatternFill('solid',fgColor='FFFFF2CC')
    s2.cell(5,1,'Edit either yellow cell and every FINAL PRICE (SAR) recalculates.').font=Font(italic=True,size=9)
    row=7
    def hdr(txt):
        global row
        s2.merge_cells(start_row=row,start_column=1,end_row=row,end_column=2)
        c=s2.cell(row,1,txt); c.font=Font(bold=True,size=12,color='FFFFFFFF')
        c.fill=PatternFill('solid',fgColor=NAVY); s2.row_dimensions[row].height=22; row+=1
    def kv(k,v):
        global row
        a=s2.cell(row,1,k); a.font=Font(bold=True,size=10); a.alignment=Alignment(vertical='top')
        b=s2.cell(row,2,str(v)); b.alignment=Alignment(wrap_text=True,vertical='top'); row+=1
    hdr('CONTENTS')
    kv('Items in this file',len(rows))
    kv('Photos embedded',placed)
    kv('Photos per item','average %.1f · maximum %d'%(sum(len(i['gallery']) for i in rows)/len(rows),MAXP))
    kv('Price range (USD)','${:,.2f} – ${:,.2f}'.format(min(i['price'] for i in rows),max(i['price'] for i in rows)))
    kv('Final price range (SAR)','{:,.0f} – {:,.0f} SAR'.format(min(i['price'] for i in rows)*MARKUP*SAR,
                                                                max(i['price'] for i in rows)*MARKUP*SAR))
    kv('Links','Omitted by request — product and image links are in the main workbook.')
    row+=1
    hdr('SOURCES')
    for k,v in collections.Counter(i['source'] for i in rows).most_common(): kv(k,f'{v} items')
    row+=1
    hdr('BY METAL')
    for k,v in collections.Counter(i['metal_detail'] for i in rows).most_common(): kv(k,f'{v} items')
    row+=1
    hdr('BY CATEGORY')
    for k,v in collections.Counter(i['kind'] for i in rows).most_common(): kv(k,f'{v} items')

    wb.save(fname)
    dedupe_xlsx.dedupe(fname)
    print(f"{fname}: {len(rows)} items | {placed} photos | missing {missing} | "
          f"{os.path.getsize(fname)/1e6:.1f} MB")
