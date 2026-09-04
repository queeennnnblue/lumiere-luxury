# Lab Diamond Jewelry Scraper

Extracts lab-grown-diamond jewelry in **18K gold** or **925 sterling silver**
from three suppliers and produces `output/Lab_Diamond_Jewelry_18K_925.xlsx`.

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
build_xlsx.py   # render the workbook
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
- **Final price**: `Price x 2.10` (original + 110%), written as a live Excel formula.
