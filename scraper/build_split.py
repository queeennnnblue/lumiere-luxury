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
          ('Metal',19),('Listed Price (USD)',14),('Total Cost (SAR)',14),('FINAL PRICE (SAR)\nincl. VAT',17),('Net Profit (SAR)',13),('Discount needed',13),('Source',16),('Photos',8)]
    NI=len(INFO); TOTAL=NI+MAXP

    ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=TOTAL)
    t=ws.cell(1,1,f'LAB DIAMOND JEWELRY — 18K GOLD & 925 SILVER — FULL PHOTO GALLERY — {label}')
    t.font=Font(size=16,bold=True,color='FFFFFFFF'); t.fill=PatternFill('solid',fgColor=NAVY)
    t.alignment=Alignment(horizontal='center',vertical='center'); ws.row_dimensions[1].height=30
    ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=TOTAL)
    s=ws.cell(2,1,'Every photo published for each piece · Listed prices are the sites’ RETAIL prices · '
                  'Set your wholesale discount, costs and profit % on the Pricing sheet · no links in this file')
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
              it['metal_detail'] or it['metal'],round(it['price'],2),None,None,None,None,
              it['source'],len(it['gallery'])]
        for c,v in enumerate(vals,1):
            cell=ws.cell(r,c,v); cell.border=border
            cell.alignment=Alignment(vertical='center',wrap_text=(c in (2,3)),
                horizontal='center' if c in (1,4,5,11,12) else 'left')
            if r%2==0: cell.fill=PatternFill('solid',fgColor=ZEBRA)
        ws.cell(r,6).number_format='"$"#,##0.00'
        OVH="(Pricing!$B$6+Pricing!$B$7+Pricing!$B$8+Pricing!$B$9+Pricing!$B$10+Pricing!$B$11+Pricing!$B$12+Pricing!$B$13)"
        RATE="(1-Pricing!$B$15-Pricing!$B$16-Pricing!$B$17)"
        def put(col,formula,fmt,**kw):
            c=ws.cell(r,col,formula); c.number_format=fmt; c.border=border
            c.alignment=Alignment(horizontal='center',vertical='center')
            if kw.get('bold'): c.font=Font(bold=True,color=kw.get('color','FF000000'))
            if kw.get('fill'): c.fill=PatternFill('solid',fgColor=kw['fill'])
        put(7,f"=F{r}*(1-Pricing!$B$4)*Pricing!$B$3+{OVH}",'#,##0')
        put(8,f"=G{r}/{RATE}*(1+Pricing!$B$18)",'#,##0',bold=True,color='FF006100',fill=GREEN)
        put(9,f"=G{r}/{RATE}*Pricing!$B$17",'#,##0',bold=True,color='FF1F3864')
        put(10,f"=MAX(0,1-((F{r}*Pricing!$B$3*{RATE}/(1+Pricing!$B$18))-{OVH})/(F{r}*Pricing!$B$3))",'0%')
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


    s2=wb.create_sheet('Summary'); s2.sheet_view.showGridLines=False
    s2.column_dimensions['A'].width=36; s2.column_dimensions['B'].width=74
    s2.merge_cells('A1:B1')
    c=s2.cell(1,1,f'FULL PHOTO GALLERY — {label}')
    c.font=Font(bold=True,size=13,color='FFFFFFFF'); c.fill=PatternFill('solid',fgColor=NAVY)
    c.alignment=Alignment(horizontal='center',vertical='center'); s2.row_dimensions[1].height=24
    # ---- editable pricing controls (referenced by every FINAL PRICE cell) ----
    s2.cell(3,1,'All pricing controls live on the Pricing sheet.').font=Font(italic=True,size=10)
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
    kv('Final price','Built on the Pricing sheet: listed price → wholesale discount → landed cost → profit %')
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
