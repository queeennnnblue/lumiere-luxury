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

COLS=[('#',6),('Photo',24),('Product Name',42),('Category',17),('Description',48),
      ('Metal',19),('Stone',16),('Weight (ct)',10),('Weight / Size (as stated)',21),
      ('Stone Spec',26),('Listed Price (USD)\nretail on the site',16),
      ('Your Cost (USD)\nafter wholesale discount',17),
      ('Landed Cost (SAR)\nincl. shipping, customs, fees',19),
      ('FINAL PRICE (SAR)',19),('Profit (SAR)',13),
      ('Product Link',15),('Source',15),('Image URL',14),('Variants Merged',14)]

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
          price,None,None,None,None,
          'View Product',it['source'],'Open Image',
          it['n_variants_collapsed']]
    for c,v in enumerate(vals,1):
        cell=ws.cell(r,c,v); cell.border=border
        cell.alignment=Alignment(vertical='center',wrap_text=(c in (3,5,10)),
            horizontal='center' if c in (1,4,6,7,8,9,16,17,18,19) else 'left')
        if r%2==0: cell.fill=PatternFill('solid',fgColor=ZEBRA)
    # ---- cost / price model, all driven by the editable cells on the Pricing sheet ----
    P="Pricing"
    ws.cell(r,11).number_format='"$"#,##0.00'
    c=ws.cell(r,12,f'=K{r}*(1-{P}!$B$4)'); c.number_format='"$"#,##0.00'
    c.border=border; c.alignment=Alignment(horizontal='center',vertical='center')
    c=ws.cell(r,13,f'=L{r}*{P}!$B$9*(1+{P}!$B$6+{P}!$B$7)+{P}!$B$5')
    c.number_format='#,##0" SAR"'; c.border=border
    c.alignment=Alignment(horizontal='center',vertical='center')
    f=ws.cell(r,14,f'=M{r}*(1+{P}!$B$8)')
    f.number_format='#,##0" SAR"'; f.font=Font(bold=True,color='FF006100')
    f.fill=PatternFill('solid',fgColor='FFE2EFDA'); f.border=border
    f.alignment=Alignment(horizontal='center',vertical='center')
    c=ws.cell(r,15,f'=N{r}-M{r}'); c.number_format='#,##0" SAR"'
    c.font=Font(color='FF1F3864'); c.border=border
    c.alignment=Alignment(horizontal='center',vertical='center')
    ws.cell(r,8).number_format='0.00'
    # links
    for col,url in ((16,it['link']),(18,it.get('image'))):
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
sp.column_dimensions['A'].width=42; sp.column_dimensions['B'].width=16
sp.column_dimensions['C'].width=66
YEL=PatternFill('solid',fgColor='FFFFF2CC')
sp.merge_cells('A1:C1')
c=sp.cell(1,1,'PRICING MODEL — edit the yellow cells only')
c.font=Font(bold=True,size=14,color='FFFFFFFF'); c.fill=PatternFill('solid',fgColor=NAVY)
c.alignment=Alignment(horizontal='center',vertical='center'); sp.row_dimensions[1].height=26

def ctl(row,label,value,fmt,note):
    a=sp.cell(row,1,label); a.font=Font(bold=True,size=10)
    a.alignment=Alignment(vertical='center')
    b=sp.cell(row,2,value); b.number_format=fmt; b.fill=YEL
    b.font=Font(bold=True,size=12,color='FF006100')
    b.alignment=Alignment(horizontal='center',vertical='center')
    b.border=Border(left=Side(style='medium',color='FFBF8F00'),right=Side(style='medium',color='FFBF8F00'),
                    top=Side(style='medium',color='FFBF8F00'),bottom=Side(style='medium',color='FFBF8F00'))
    n=sp.cell(row,3,note); n.font=Font(size=9,italic=True,color='FF595959')
    n.alignment=Alignment(wrap_text=True,vertical='center')
    sp.row_dimensions[row].height=30

sp.cell(3,1,'WHAT YOU PAY').font=Font(bold=True,size=11,color='FF1F3864')
ctl(4,'Wholesale discount off the listed price',0.0,'0%',
    'THE MAIN LEVER. The listed prices are the sites\u2019 RETAIL prices. Ask each supplier for their '
    'wholesale / OEM rate and enter it here (e.g. 40% means you pay 60% of the listed price). '
    'At 0% you are paying full retail and cannot price competitively.')
ctl(5,'Shipping & insurance per piece (SAR)',0,'#,##0" SAR"','A flat amount added to every piece.')
ctl(6,'Customs, duty & VAT',0.0,'0%','Percentage added on the landed value.')
ctl(7,'Payment / bank / platform fees',0.0,'0%','Card, transfer or marketplace fees.')

ctl(8,'Profit margin',0.10,'0%',
    'Your profit as a percentage ON TOP OF your landed cost (mark-up). 10% here = 9.1% of the selling price.')
ctl(9,'USD \u2192 SAR exchange rate',3.75,'0.0000','Official Saudi riyal peg.')

# NOTE: control rows are referenced by the data sheet as B4..B9 in this order:
#   B4 wholesale discount | B5 shipping | B6 customs | B7 fees | B8 profit | B9 fx


r0=12
sp.merge_cells(start_row=r0,start_column=1,end_row=r0,end_column=3)
c=sp.cell(r0,1,'HOW EACH PRICE IS BUILT'); c.font=Font(bold=True,size=12,color='FFFFFFFF')
c.fill=PatternFill('solid',fgColor=NAVY); sp.row_dimensions[r0].height=22
steps=[('1. Your Cost (USD)','Listed Price \u00d7 (1 \u2212 wholesale discount)'),
       ('2. Landed Cost (SAR)','Your Cost \u00d7 exchange rate \u00d7 (1 + customs + fees) + shipping'),
       ('3. FINAL PRICE (SAR)','Landed Cost \u00d7 (1 + profit margin)'),
       ('4. Profit (SAR)','Final Price \u2212 Landed Cost')]
for i,(k,v) in enumerate(steps):
    a=sp.cell(r0+1+i,1,k); a.font=Font(bold=True,size=10)
    b=sp.cell(r0+1+i,2,''); 
    n=sp.cell(r0+1+i,3,v); n.font=Font(size=10)
sp.merge_cells(start_row=r0+6,start_column=1,end_row=r0+6,end_column=3)
w=sp.cell(r0+6,1,'\u26a0  The listed prices are RETAIL prices published on consumer websites, not wholesale. '
                 'Selling at a 5\u201310% margin on top of full retail is not viable \u2014 the number you need is the '
                 'wholesale discount in cell B4. All three suppliers run B2B / OEM programmes '
                 '(Provence Gems is itself the manufacturer), and StarsGem prices by quotation only, which is why '
                 'it carries no public prices at all.')
w.font=Font(size=10,color='FF9C0006'); w.fill=PatternFill('solid',fgColor='FFFFC7CE')
w.alignment=Alignment(wrap_text=True,vertical='center'); sp.row_dimensions[r0+6].height=70

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
