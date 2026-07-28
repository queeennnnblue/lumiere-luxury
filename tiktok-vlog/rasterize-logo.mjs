import {getDocument} from 'pdfjs-dist/legacy/build/pdf.mjs';
import {createCanvas} from '@napi-rs/canvas';
import fs from 'fs';

const data = new Uint8Array(
  fs.readFileSync(
    '/root/.claude/uploads/770a5d1b-5fc6-58a5-a08d-d2f189929b7d/2e77051b-logo_lomond_1.pdf'
  )
);
const doc = await getDocument({data, disableFontFace: false}).promise;
const page = await doc.getPage(1);
const scale = 6;
const viewport = page.getViewport({scale});
const canvas = createCanvas(Math.ceil(viewport.width), Math.ceil(viewport.height));
const ctx = canvas.getContext('2d');
// خلفية شفافة — بدون تعبئة
await page.render({canvasContext: ctx, viewport, background: 'rgba(0,0,0,0)'}).promise;
fs.writeFileSync('public/lomond-logo.png', canvas.toBuffer('image/png'));
console.log('size:', Math.ceil(viewport.width), 'x', Math.ceil(viewport.height));
