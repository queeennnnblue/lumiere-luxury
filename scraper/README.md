# Lab Diamond Jewelry Scraper

Extracts lab-grown-diamond jewelry in **18K gold** or **925 sterling silver**
from three suppliers and produces two workbooks in `output/`:

- **`Lab_Diamond_Jewelry_18K_925.xlsx`** — main file: one photo per piece, full detail,
  product and image **links**.
- **`Lab_Diamond_Jewelry_ALL_PHOTOS_Part1_Fiorese.xlsx`** and
  **`..._Part2_Provence_LGG.xlsx`** — gallery files: **every** photo published for each
  piece (up to 20 per row) at 320 px, with description, weight, price, final price and
  source. Split in two to stay under the upload limit at higher image quality.
  Deliberately contain **no links**.

### Pricing model

Every workbook carries a **Pricing** sheet built from the client's own LOMOND cost
statement. Yellow cells are the only inputs; all price columns are live formulas.

| Cell | Control | Value |
|---|---|---|
| `B3` | USD to SAR | 3.75 |
| `B4` | Wholesale discount off the listed price | 0.40 *(assumption)* |
| `B6`-`B13` | Bank transfer, import shipping, customs, delivery, set-up share, packaging, monthly share, engraving | 548.84 total |
| `B15` `B16` | Processing 8%, payment gateway 3.8% | |
| `B17` | Net profit margin | 8% |
| `B18` | VAT | 15% |

```
Buy Price (USD)   = Listed Price x (1 - B4)
Total Cost (SAR)  = Buy Price x B3 + overhead
Price before VAT  = Total Cost / (1 - B15 - B16 - B17)
FINAL PRICE (SAR) = Price before VAT x (1 + B18)
Net Profit (SAR)  = Price before VAT x B17
Discount needed   = the wholesale rate at which the final price equals supplier retail
```

This reproduces the client's own worked example to the fourth decimal.

**Important:** the scraped prices are the suppliers' **retail** prices. At full retail the
final price lands ~1.5x the supplier's own website price, so a viable margin depends
entirely on `B4` carrying a real negotiated wholesale rate.

## Sources

| Source | Platform | Access |
|---|---|---|
| [Fiorese Jewelry](https://fioresejewelry.com/) | Shopify | `products.json` |
| [LGG Jewelry](https://www.lggjewelry.com/) | Shopify | `products.json` |
| [Provence Gems](https://provencegems.com/) | WooCommerce | Store API + per-product variation JSON |
| ~~StarsGem~~ | custom | **excluded — publishes no prices (quote-only B2B)** |

## Pipeline

```
fetch_prov.py   # download Provence product pages (variant-level prices)
extract.py      # parse all sources -> rows_raw.json   (variant-level rows)
refine.py       # stone / metal filtering -> rows_kept.json
dedupe.py       # group duplicates, keep cheapest -> items.json
polish.py       # weight display + description cleanup
getimg.py       # download & normalise product photos
build_xlsx.py   # render the main workbook
getgal.py       # download every product photo (full galleries)
getgalhq.py     # same, at higher resolution (440 px masters)
build_gallery.py# render a single all-photos workbook
build_split.py  # render the two-part all-photos workbooks
dedupe_xlsx.py  # collapse duplicate embedded images inside a saved .xlsx
```

## Rules applied

- **Metal**: solid 18K (white/yellow/rose) or 925 sterling silver only. 10K, 14K, platinum/PT950 excluded.
- **Stone**: the *main* stone must be a lab-grown diamond. The variant's own stone
  attribute wins over the title, because several listings advertise every option
  ("lab diamond/moissanite/lab gemstone") in the title while the variant selects the
  actual stone. Moissanite, CZ and lab sapphire/ruby/emerald/paraiba/padparadscha pieces
  are excluded, including pieces where a lab diamond is only a side stone.
- **Duplicates**: grouped by design + metal + carat; ring sizes, chain lengths and gold
  colours collapse into one row and the **cheapest** option is kept.
- **Final price**: driven by the Pricing sheet (see above) as live Excel formulas, so the
  whole catalogue reprices when a cost assumption changes.
- **Image dedup**: openpyxl writes one copy of a picture per anchor, so `dedupe_xlsx.py`
  rewrites the drawing relationships to share a single copy of each distinct photo. This
  cut roughly 28% of the gallery files' size and paid for the higher image quality.
