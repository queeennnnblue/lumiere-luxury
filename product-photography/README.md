# LUMIÈRE — Uniform Product Photography Pipeline

Turns mixed raw product photos (clean shots, phone screenshots, catalog pages)
into a uniform, on-brand set of **4096×4096 (4K)** store visuals. The jewelry
itself is never altered or regenerated — photos are only cropped, cleaned of
app UI, gently sharpened and placed on the LUMIÈRE brand background.

## The look

- Warm cream **golden-hour** background with soft light rays and vignette
  (`#faf7f0` / `#e8ddc8` family)
- Double gold hairline frame (`#c9a55c` / `#9a7b3a`)
- Product window with gold gradient border and soft shadow
- Subtle gold/ivory sparkles kept off the jewelry
- `LUMIÈRE` wordmark in Cormorant Garamond + `N° xx / 50` piece numbering

## Usage

```bash
# 1. Clean + crop the raw photos into uniform squares
python3 preprocess.py <raw_photos_dir> public/products

# 2. Render all 4K cards with Remotion
npm install
node render.mjs ../store-assets/products-4k
```

Per-photo crop tuning (removing status bars, app banners, captions,
watermarks) lives in the `TUNE` table at the top of `preprocess.py`.

`render.mjs` uses the pre-installed Playwright Chromium headless shell; set
`CHROMIUM_PATH` to override the browser binary.

## Output

- `../store-assets/products-4k/` — 4096×4096 JPEG masters (print / zoom)
- `../store-assets/products-web/` — 1600×1600 web versions used by the store
