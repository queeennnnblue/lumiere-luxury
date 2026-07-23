// Batch-renders every preprocessed product photo through the LUMIÈRE
// Remotion composition as a 4096x4096 still.
// Usage: node render.mjs [outDir]
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition, openBrowser} from '@remotion/renderer';
import {readdirSync, mkdirSync} from 'fs';
import path from 'path';

const outDir = process.argv[2] ?? '../store-assets/products-4k';
mkdirSync(outDir, {recursive: true});

const products = readdirSync('public/products')
  .filter((f) => f.startsWith('product_') && f.endsWith('.jpg'))
  .sort();

const browserExecutable = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';

const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const browser = await openBrowser('chrome', {browserExecutable});

const total = products.length;
for (const file of products) {
  const index = parseInt(file.match(/(\d+)/)[1], 10);
  const inputProps = {src: `products/${file}`, index, total};
  const composition = await selectComposition({
    serveUrl,
    id: 'ProductCard',
    inputProps,
    puppeteerInstance: browser,
    browserExecutable,
  });
  const output = path.join(outDir, `lomond_${String(index).padStart(2, '0')}.jpg`);
  await renderStill({
    composition,
    serveUrl,
    output,
    inputProps,
    imageFormat: 'jpeg',
    jpegQuality: 92,
    puppeteerInstance: browser,
    browserExecutable,
    chromiumOptions: {gl: 'swangle'},
    timeoutInMilliseconds: 120000,
  });
  console.log(`rendered ${output}`);
}

await browser.close({silent: true});
process.exit(0);
