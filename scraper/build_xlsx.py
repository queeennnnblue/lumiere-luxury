import json,os,hashlib,re,collections
from openpyxl import Workbook
from openpyxl.styles import Font,Alignment,PatternFill,Border,Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from openpyxl.worksheet.hyperlink import Hyperlink

items=json.load(open('items.json'))
MARKUP=2.10   # price + 110%
SAR=3.75      # USD -> SAR (official peg)
SREF="'Summary & Method'"

def key(u): return hashlib.md5(u.encode()).hexdigest()
def short(t,n):
    t=re.sub(r'\s+',' ',t or '').strip()
    return t if len(t)<=n else t[:n-1].rsplit(' ',1)[0]+'…'

# ---- sort: source, category, price ----
items.sort(key=lambda x:(x['source'],x['kind'],x['price']))

wb=Workbook(); ws=wb.active; ws.title='Lab Diamond Jewelry'

NAVY='FF1F3864'; ACCENT='FFD9E2F3'; ZEBRA='FFF7F9FC'
thin=Side(style='thin',color='FFBFBFBF')
border=Border(left=thin,right=thin,top=thin,bottom=thin)

COLS=[('#',6),('Photo',24),('Product Name',44),('Category',18),('Description',54),
      ('Metal',20),('Stone',17),('Weight (ct)',11),('Weight / Size (as stated)',22),
      ('Stone Spec',30),('Price (USD)',14),('FINAL PRICE (SAR)',21),
      ('Product Link',16),('Source',16),('Image URL',16),('Variants Merged',15)]

# title row
ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=len(COLS))
t=ws.cell(1,1,'LAB DIAMOND JEWELRY — 18K GOLD & 925 STERLING SILVER')
t.font=Font(size=16,bold=True,color='FFFFFFFF'); t.fill=PatternFill('solid',fgColor=NAVY)
t.alignment=Alignment(horizontal='center',vertical='center'); ws.row_dimensions[1].height=30
ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=len(COLS))
s=ws.cell(2,1,'Cheapest option kept per design · Supplier price in USD · FINAL PRICE (SAR) = Price × 2.10 × 3.75 — markup and exchange rate are editable on the Summary sheet')
s.font=Font(size=10,italic=True,color=NAVY); s.fill=PatternFill('solid',fgColor=ACCENT)
s.alignment=Alignment(horizontal='center',vertical='center'); ws.row_dimensions[2].height=18

HR=3
for c,(name,w) in enumerate(COLS,1):
    cell=ws.cell(HR,c,name)
    cell.font=Font(bold=True,color='FFFFFFFF',size=10)
    cell.fill=PatternFill('solid',fgColor=NAVY)
    cell.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
    cell.border=border
    ws.column_dimensions[get_column_letter(c)].width=w
ws.row_dimensions[HR].height=32

r=HR+1
missing=0
for n,it in enumerate(items,1):
    price=round(it['price'],2)
    ws.row_dimensions[r].height=95
    vals=[n,None,it['title'],it['kind'],short(it['desc'],600),
          it['metal_detail'] or it['metal'],'Lab Grown Diamond',
          it['carat'],it['weight_display'],short(it['stone_spec'] or it['variant'],90),price,None,
          'View Product',it['source'],'Open Image',
          it['n_variants_collapsed']]
    for c,v in enumerate(vals,1):
        cell=ws.cell(r,c,v); cell.border=border
        cell.alignment=Alignment(vertical='center',wrap_text=(c in (3,5,10)),
            horizontal='center' if c in (1,4,6,7,8,9,13,14,15,16) else 'left')
        if r%2==0: cell.fill=PatternFill('solid',fgColor=ZEBRA)
    # price + final price formula
    ws.cell(r,11).number_format='"$"#,##0.00'
    f=ws.cell(r,12,f'=K{r}*{SREF}!$B$3*{SREF}!$B$4')
    f.number_format='#,##0.00" SAR"'; f.font=Font(bold=True,color='FF006100')
    f.fill=PatternFill('solid',fgColor='FFE2EFDA'); f.border=border
    f.alignment=Alignment(horizontal='center',vertical='center')
    ws.cell(r,8).number_format='0.00'
    # links
    for col,url in ((13,it['link']),(15,it.get('image'))):
        if url:
            cl=ws.cell(r,col); cl.hyperlink=url
            cl.font=Font(color='FF0563C1',underline='single',size=9)
    # photo
    p=('imgj/'+key(it['image'])+'.jpg') if it.get('image') else None
    if p and os.path.exists(p):
        im=XLImage(p); im.width=im.height=118
        im.anchor=f'B{r}'; ws.add_image(im)
    else: 
        missing+=1
        ws.cell(r,2,'no image').alignment=Alignment(horizontal='center',vertical='center')
    r+=1

ws.freeze_panes=f'C{HR+1}'
ws.auto_filter.ref=f'A{HR}:{get_column_letter(len(COLS))}{r-1}'
ws.sheet_view.showGridLines=False

# ================= SUMMARY SHEET =================
s2=wb.create_sheet('Summary & Method')
s2.sheet_view.showGridLines=False
s2.column_dimensions['A'].width=38; s2.column_dimensions['B'].width=72
def hdr(row,txt):
    s2.merge_cells(start_row=row,start_column=1,end_row=row,end_column=2)
    c=s2.cell(row,1,txt); c.font=Font(bold=True,size=12,color='FFFFFFFF')
    c.fill=PatternFill('solid',fgColor=NAVY); c.alignment=Alignment(vertical='center')
    s2.row_dimensions[row].height=22
def kv(row,k,v):
    a=s2.cell(row,1,k); a.font=Font(bold=True,size=10)
    b=s2.cell(row,2,str(v)); b.alignment=Alignment(wrap_text=True,vertical='top')
    a.alignment=Alignment(vertical='top')

by_src=collections.Counter(i['source'] for i in items)
by_metal=collections.Counter(i['metal'] for i in items)
by_kind=collections.Counter(i['kind'] for i in items)
tot=sum(i['price'] for i in items)

row=1
hdr(row,'LAB DIAMOND JEWELRY — EXTRACTION SUMMARY')
from openpyxl.styles import PatternFill as PF
a=s2.cell(3,1,'Markup multiplier  (price + 110%)'); a.font=Font(bold=True,size=10)
b=s2.cell(3,2,MARKUP); b.number_format='0.00'; b.font=Font(bold=True,size=11,color='FF006100')
b.fill=PF('solid',fgColor='FFFFF2CC')
a=s2.cell(4,1,'USD → SAR exchange rate'); a.font=Font(bold=True,size=10)
b=s2.cell(4,2,SAR); b.number_format='0.0000'; b.font=Font(bold=True,size=11,color='FF006100')
b.fill=PF('solid',fgColor='FFFFF2CC')
s2.cell(5,1,'Edit either yellow cell and every FINAL PRICE (SAR) recalculates.').font=Font(italic=True,size=9)
row=7
kv(row,'Unique items listed',len(items)); row+=1
kv(row,'Price range (USD)','${:,.2f} – ${:,.2f}'.format(min(i['price'] for i in items),max(i['price'] for i in items))); row+=1
kv(row,'Average price','${:,.2f}'.format(tot/len(items))); row+=1
kv(row,'Final price','FINAL PRICE (SAR) = Price (USD) × 2.10 × 3.75  — cost + 110%, converted at the official Saudi riyal peg'); row+=1
kv(row,'Final price range','{:,.0f} – {:,.0f} SAR'.format(min(i['price'] for i in items)*MARKUP*SAR,max(i['price'] for i in items)*MARKUP*SAR)); row+=2

hdr(row,'SOURCES'); row+=1
SRC={'Provence Gems':'https://provencegems.com/','LGG Jewelry':'https://www.lggjewelry.com/','Fiorese Jewelry':'https://fioresejewelry.com/'}
for k,v in by_src.most_common():
    kv(row,k,f'{v} items   ·   {SRC[k]}'); row+=1
kv(row,'StarsGem  (EXCLUDED)','https://www.starsgem.com/ — removed: the site is quote-only and publishes no prices, so price and final-price columns could not be filled.')
s2.cell(row,2).font=Font(color='FFC00000',size=10); row+=2

hdr(row,'BREAKDOWN BY METAL'); row+=1
for k,v in by_metal.most_common(): kv(row,k,f'{v} items'); row+=1
row+=1
hdr(row,'BREAKDOWN BY CATEGORY'); row+=1
for k,v in by_kind.most_common(): kv(row,k,f'{v} items'); row+=1
row+=1
hdr(row,'FILTERS & METHOD'); row+=1
for k,v in [
 ('Metal filter','Only solid 18K gold (white / yellow / rose) or 925 sterling silver. 10K, 14K, platinum and PT950 options were excluded.'),
 ('Stone filter','Only jewelry whose MAIN / centre stone is a lab-grown diamond. Moissanite, cubic zirconia, lab sapphire / ruby / emerald / paraiba / padparadscha, moss agate and other gemstones were excluded, including pieces where a lab diamond appears only as a side stone.'),
 ('Scope','Finished jewelry only — loose stones, melee and per-carat parcels excluded.'),
 ('Duplicate handling','Items were grouped by design + metal + carat weight. Ring sizes, chain lengths and gold colours collapse into one row and the CHEAPEST qualifying option is the one listed. "Variants Merged" shows how many options were collapsed.'),
 ('18K vs 925','Where a design is offered in both 18K gold and 925 silver, both appear as separate rows — they are different products at different prices, not duplicates.'),
 ('Weight','"Weight (ct)" is the total lab-diamond carat weight taken from the product option or title. Blank where the seller does not state it. "Stone Size" gives the stone dimensions in mm where quoted instead.'),
 ('Price basis','Lowest listed price of the qualifying option, in USD, as published at extraction time. Excludes shipping, duties and any customisation surcharge.'),
 ('Quote-only variants','Variants priced as placeholders (e.g. "other carat weight", custom orders) were removed.'),
 ('Extracted','2026-09-04'),
]:
    kv(row,k,v); s2.row_dimensions[row].height=max(15,14*(len(v)//85+1)); row+=1

wb.save('Lab_Diamond_Jewelry_18K_925.xlsx')
print("rows:",len(items),"| images missing:",missing)
print("size: %.1f MB"%(os.path.getsize('Lab_Diamond_Jewelry_18K_925.xlsx')/1e6))
