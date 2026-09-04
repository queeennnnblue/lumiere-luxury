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

COLS=[('#',6),('Photo',24),('Product Name',40),('Category',16),('Description',40),
      ('Metal',18),('Stone',15),('Weight (ct)',10),('Weight / Size (as stated)',20),
      ('Stone Spec',24),
      ('Listed Price (USD)\nretail on the site',15),
      ('Your Buy Price (USD)\nafter wholesale discount',16),
      ('Purchase (SAR)',13),
      ('Overhead (SAR)\nshipping, customs, fixed share',17),
      ('TOTAL COST (SAR)',15),
      ('Price before VAT',15),('VAT 15%',12),
      ('FINAL PRICE (SAR)\nincl. VAT',18),
      ('Net Profit (SAR)',14),('Final Price / carat',15),
      ('Discount needed\nto match supplier retail',17),
      ('Viable?',11),
      ('Product Link',14),('Source',15),('Image URL',13),('Variants Merged',13)]

# title row
ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=len(COLS))
t=ws.cell(1,1,'LAB DIAMOND JEWELRY — 18K GOLD & 925 STERLING SILVER')
t.font=Font(size=16,bold=True,color='FFFFFFFF'); t.fill=PatternFill('solid',fgColor=NAVY)
t.alignment=Alignment(horizontal='center',vertical='center'); ws.row_dimensions[1].height=30
ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=len(COLS))
s=ws.cell(2,1,'Cheapest option kept per design · Listed prices are the sites\u2019 RETAIL prices · Set your wholesale discount, costs and profit % on the Pricing sheet — every figure below recalculates')
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
          it['carat'],it['weight_display'],short(it['stone_spec'] or it['variant'],90),
          price]+[None]*11+[
          'View Product',it['source'],'Open Image',
          it['n_variants_collapsed']]
    for c,v in enumerate(vals,1):
        cell=ws.cell(r,c,v); cell.border=border
        cell.alignment=Alignment(vertical='center',wrap_text=(c in (3,5,10)),
            horizontal='center' if c in (1,4,6,7,8,9,22,23,24,25,26) else 'left')
        if r%2==0: cell.fill=PatternFill('solid',fgColor=ZEBRA)
    # ---- LOMOND cost & price model — every input lives on the Pricing sheet ----
    P="Pricing"
    OVH=f"({P}!$B$6+{P}!$B$7+{P}!$B$8+{P}!$B$9+{P}!$B$10+{P}!$B$11+{P}!$B$12+{P}!$B$13)"
    RATE=f"(1-{P}!$B$15-{P}!$B$16-{P}!$B$17)"
    ws.cell(r,11).number_format='"$"#,##0.00'
    def put(col,formula,fmt,**kw):
        c=ws.cell(r,col,formula); c.number_format=fmt; c.border=border
        c.alignment=Alignment(horizontal='center',vertical='center')
        if kw.get('bold'): c.font=Font(bold=True,color=kw.get('color','FF000000'))
        if kw.get('fill'): c.fill=PatternFill('solid',fgColor=kw['fill'])
        return c
    put(12,f'=K{r}*(1-{P}!$B$4)','"$"#,##0.00')
    put(13,f'=L{r}*{P}!$B$3','#,##0')
    put(14,f'={OVH}','#,##0')
    put(15,f'=M{r}+N{r}','#,##0',bold=True)
    put(16,f'=O{r}/{RATE}','#,##0')
    put(17,f'=P{r}*{P}!$B$18','#,##0')
    put(18,f'=P{r}+Q{r}','#,##0',bold=True,color='FF006100',fill='FFE2EFDA')
    put(19,f'=P{r}*{P}!$B$17','#,##0',bold=True,color='FF1F3864')
    put(20,(f'=IF(H{r}="","",R{r}/H{r})') if True else '','#,##0')
    put(21,f'=MAX(0,1-((K{r}*{P}!$B$3*{RATE}/(1+{P}!$B$18))-{OVH})/(K{r}*{P}!$B$3))','0%')
    c=ws.cell(r,22,f'=IF({P}!$B$4>=U{r},"YES","needs "&TEXT(U{r},"0%"))')
    c.border=border; c.alignment=Alignment(horizontal='center',vertical='center')
    c.font=Font(size=9)
    ws.cell(r,8).number_format='0.00'
    # links
    for col,url in ((23,it['link']),(25,it.get('image'))):
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


# ================= PRICING CONTROL SHEET =================
sp=wb.create_sheet('Pricing'); sp.sheet_view.showGridLines=False
sp.column_dimensions['A'].width=44; sp.column_dimensions['B'].width=15
sp.column_dimensions['C'].width=62
YEL=PatternFill('solid',fgColor='FFFFF2CC')
BOR=Border(left=Side(style='medium',color='FFBF8F00'),right=Side(style='medium',color='FFBF8F00'),
           top=Side(style='medium',color='FFBF8F00'),bottom=Side(style='medium',color='FFBF8F00'))
sp.merge_cells('A1:C1')
c=sp.cell(1,1,'PRICING MODEL — from your LOMOND cost sheet · edit the yellow cells only')
c.font=Font(bold=True,size=13,color='FFFFFFFF'); c.fill=PatternFill('solid',fgColor=NAVY)
c.alignment=Alignment(horizontal='center',vertical='center'); sp.row_dimensions[1].height=26

def ctl(row,label,value,fmt,note):
    a=sp.cell(row,1,label); a.font=Font(bold=True,size=10); a.alignment=Alignment(vertical='center')
    b=sp.cell(row,2,value); b.number_format=fmt; b.fill=YEL; b.border=BOR
    b.font=Font(bold=True,size=11,color='FF006100')
    b.alignment=Alignment(horizontal='center',vertical='center')
    n=sp.cell(row,3,note); n.font=Font(size=9,italic=True,color='FF595959')
    n.alignment=Alignment(wrap_text=True,vertical='center')
    sp.row_dimensions[row].height=26
def sec(row,txt):
    sp.merge_cells(start_row=row,start_column=1,end_row=row,end_column=3)
    c=sp.cell(row,1,txt); c.font=Font(bold=True,size=11,color='FFFFFFFF')
    c.fill=PatternFill('solid',fgColor='FF2E5C9A'); sp.row_dimensions[row].height=20

sec(2,'PURCHASE')
ctl(3,'USD → SAR exchange rate',3.75,'0.0000','From your settings sheet.')
ctl(4,'Wholesale discount off the listed price',0.40,'0%',
    '★ ASSUMPTION — replace with the rate you actually negotiate. The listed prices are the '
    'suppliers\u2019 RETAIL prices; your three purchases (P-001/2/3) match catalogue items almost '
    'exactly, so you are currently paying full retail. Column U shows the discount each piece needs.')
sec(5,'COST PER PIECE (SAR) — taken from your cost statement')
ctl(6,'Bank transfer fee',47.50,'#,##0.00','$38 per shipment ÷ 3 pieces × 3.75.')
ctl(7,'Import shipping',131.25,'#,##0.00','$35 per shipment × 3.75 ÷ pieces per shipment.')
ctl(8,'Customs / duty',21.00,'#,##0.00','Per imported piece.')
ctl(9,'Delivery to the customer',30.00,'#,##0.00','')
ctl(10,'Share of one-off set-up costs',211.43,'#,##0.00','10,571.44 ÷ 50 pieces.')
ctl(11,'Packaging, cards, box per piece',51.08,'#,##0.00','')
ctl(12,'Share of monthly running costs',53.18,'#,##0.00','2,659 ÷ 50 pieces.')
ctl(13,'Logo engraving',3.40,'#,##0.00','170 ÷ 50 pieces.')
sec(14,'FEES, MARGIN AND TAX')
ctl(15,'Processing fees',0.08,'0%','From your settings sheet.')
ctl(16,'Payment gateway fees',0.038,'0%','From your settings sheet.')
ctl(17,'NET PROFIT MARGIN',0.08,'0%',
    '★ Your net profit as a share of the pre-VAT price — the same basis your own sheet uses. '
    'Set to 8%, above the 5% floor you asked for.')
ctl(18,'VAT',0.15,'0%','Collected on behalf of ZATCA — not profit.')

r0=20
sp.merge_cells(start_row=r0,start_column=1,end_row=r0,end_column=3)
c=sp.cell(r0,1,'HOW EACH PRICE IS BUILT'); c.font=Font(bold=True,size=12,color='FFFFFFFF')
c.fill=PatternFill('solid',fgColor=NAVY); sp.row_dimensions[r0].height=22
for i,(k,v) in enumerate([
    ('Your Buy Price (USD)','Listed Price × (1 − wholesale discount)'),
    ('Purchase (SAR)','Buy Price × exchange rate'),
    ('Overhead (SAR)','sum of the eight cost rows above'),
    ('TOTAL COST (SAR)','Purchase + Overhead'),
    ('Price before VAT','Total Cost ÷ (1 − processing − gateway − margin)'),
    ('FINAL PRICE (SAR)','Price before VAT × 1.15'),
    ('Net Profit (SAR)','Price before VAT × margin'),
    ('Discount needed (col U)','the wholesale discount at which your price equals the supplier\u2019s own retail price'),
]):
    a=sp.cell(r0+1+i,1,k); a.font=Font(bold=True,size=10)
    n=sp.cell(r0+1+i,3,v); n.font=Font(size=10); n.alignment=Alignment(wrap_text=True)

w0=r0+10
sp.merge_cells(start_row=w0,start_column=1,end_row=w0,end_column=3)
w=sp.cell(w0,1,
  '\u26a0  WHY THE PRICES LOOKED TOO HIGH\n'
  'Your overhead is about 549 SAR on every single piece, and fees + margin + VAT multiply the cost by '
  'roughly 1.43. So at full retail your price lands about 1.5× the supplier\u2019s own website price — no '
  'customer would pay that. Cutting the margin does not fix it: even at 0% profit the median piece still '
  'comes out around 7,976 SAR, because the base price is already retail.\n'
  'The lever is the wholesale discount (B4). At an 8% margin the median piece needs about 37% off, and '
  'cheaper pieces need far more because the 549 SAR overhead is fixed: a 2,000 SAR piece needs ~58%, a '
  '1,000 SAR piece ~85%. Two practical consequences: negotiate OEM/wholesale rates with the suppliers '
  '(all three run B2B programmes and Provence Gems is itself the factory), and concentrate on higher-value '
  'pieces until volume brings the fixed share per piece down.')
w.font=Font(size=10,color='FF9C0006'); w.fill=PatternFill('solid',fgColor='FFFFC7CE')
w.alignment=Alignment(wrap_text=True,vertical='top'); sp.row_dimensions[w0].height=140

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
