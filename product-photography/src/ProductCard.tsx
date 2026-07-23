import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Img, staticFile, delayRender, continueRender} from 'remotion';

// LOMOND brand palette (sampled from the logo PDF)
const BURGUNDY = '#4d0c11';
const BURGUNDY_SOFT = 'rgba(77,12,17,0.55)';
const GOLD = '#c9a55c';
const GOLD_DEEP = '#9a7b3a';

const SIZE = 4096;
const PANEL = 2620; // product window — generous, the jewelry is the hero
const PANEL_TOP = 560;

// Deterministic pseudo-random for sparkle placement (stable per product)
const rand = (seed: number) => {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
};

const Sparkle: React.FC<{x: number; y: number; s: number; o: number; c: string; r: number}> = ({x, y, s, o, c, r}) => (
  <svg
    width={s}
    height={s}
    viewBox="0 0 100 100"
    style={{position: 'absolute', left: x, top: y, opacity: o, transform: `rotate(${r}deg)`}}
  >
    <path
      d="M50 0 C54 32 68 46 100 50 C68 54 54 68 50 100 C46 68 32 54 0 50 C32 46 46 32 50 0 Z"
      fill={c}
    />
  </svg>
);

export const ProductCard: React.FC<{src: string; index: number; total: number}> = ({src, index, total}) => {
  const [handle] = useState(() => delayRender('load-fonts'));
  useEffect(() => {
    const med = new FontFace('CormorantG', `url(${staticFile('fonts/CormorantGaramond-Medium.ttf')})`, {weight: '500'});
    const bold = new FontFace('CormorantG', `url(${staticFile('fonts/CormorantGaramond-Bold.ttf')})`, {weight: '700'});
    Promise.all([med.load(), bold.load()]).then((fonts) => {
      fonts.forEach((f) => document.fonts.add(f));
      continueRender(handle);
    });
  }, [handle]);

  const rnd = rand(index * 7919 + 13);
  const sparkles = Array.from({length: 28}, (_, i) => {
    const margin = 340;
    const zone = i % 4; // top / bottom / left / right margins only
    const x =
      zone === 0 || zone === 1
        ? rnd() * (SIZE - 400) + 200
        : zone === 2
          ? rnd() * margin + 130
          : SIZE - 130 - margin + rnd() * margin;
    const y =
      zone === 0
        ? rnd() * (PANEL_TOP - 250) + 150
        : zone === 1
          ? PANEL_TOP + PANEL + 90 + rnd() * 260
          : PANEL_TOP + rnd() * PANEL;
    const s = 18 + rnd() * 54;
    return {x, y, s, o: 0.18 + rnd() * 0.5, c: rnd() > 0.35 ? GOLD : '#fffdf5', r: rnd() * 90};
  });

  const num = String(index).padStart(2, '0');

  return (
    <AbsoluteFill
      style={{
        fontFamily: 'CormorantG, serif',
        background: `
          radial-gradient(circle at 18% 8%, rgba(255,214,140,0.5) 0%, rgba(255,214,140,0.16) 28%, transparent 55%),
          radial-gradient(circle at 85% 90%, rgba(77,12,17,0.10) 0%, transparent 45%),
          radial-gradient(circle at 50% 45%, rgba(255,252,246,0.9) 0%, transparent 60%),
          linear-gradient(158deg, #faf4ea 0%, #f2e8d8 40%, #efe4db 70%, #e3d2bd 100%)`,
      }}
    >
      {/* golden-hour light rays from top-left */}
      <AbsoluteFill
        style={{
          background:
            'repeating-linear-gradient(115deg, transparent 0px, transparent 340px, rgba(255,220,150,0.10) 480px, transparent 640px)',
        }}
      />
      {/* soft vignette */}
      <AbsoluteFill
        style={{
          background: 'radial-gradient(circle at 50% 50%, transparent 55%, rgba(77,12,17,0.10) 100%)',
        }}
      />

      {/* background sparkles (kept off the product window) */}
      {sparkles.map((sp, i) => (
        <Sparkle key={i} {...sp} />
      ))}

      {/* double hairline frame — gold outside, burgundy inside */}
      <div style={{position: 'absolute', inset: 96, border: `4px solid ${GOLD}`, opacity: 0.9}} />
      <div style={{position: 'absolute', inset: 132, border: `1.5px solid ${BURGUNDY}`, opacity: 0.45}} />

      {/* kick line */}
      <div
        style={{
          position: 'absolute',
          top: 236,
          width: '100%',
          textAlign: 'center',
          fontSize: 64,
          fontWeight: 500,
          letterSpacing: 30,
          color: BURGUNDY,
          textTransform: 'uppercase',
          opacity: 0.85,
        }}
      >
        Fine Jewelry
      </div>
      {/* piece number */}
      <div
        style={{
          position: 'absolute',
          top: 186,
          right: 210,
          fontSize: 52,
          fontWeight: 500,
          letterSpacing: 6,
          color: BURGUNDY,
          opacity: 0.8,
        }}
      >
        N° {num} / {total}
      </div>

      {/* product window */}
      <div
        style={{
          position: 'absolute',
          top: PANEL_TOP,
          left: (SIZE - PANEL) / 2,
          width: PANEL,
          height: PANEL,
          borderRadius: 34,
          padding: 10,
          background: `linear-gradient(135deg, ${GOLD} 0%, #e8d5a8 30%, ${GOLD} 55%, ${GOLD_DEEP} 100%)`,
          boxShadow: '0 90px 180px rgba(77,12,17,0.28), 0 30px 70px rgba(77,12,17,0.18)',
        }}
      >
        <div style={{position: 'relative', width: '100%', height: '100%', borderRadius: 26, overflow: 'hidden'}}>
          <Img
            src={staticFile(src)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              // gentle golden-hour grade — enhances sparkle, never redraws the piece
              filter: 'brightness(1.045) contrast(1.06) saturate(1.08)',
            }}
          />
          {/* warm sunlight wash + diagonal light streak */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'linear-gradient(125deg, rgba(255,205,125,0.14) 0%, transparent 40%), linear-gradient(115deg, transparent 32%, rgba(255,242,214,0.13) 46%, rgba(255,255,255,0.17) 51%, rgba(255,242,214,0.13) 56%, transparent 72%)',
            }}
          />
          {/* inner hairline */}
          <div style={{position: 'absolute', inset: 0, borderRadius: 26, border: '2px solid rgba(255,253,249,0.55)'}} />
        </div>
      </div>

      {/* LOMOND logo lockup */}
      <div style={{position: 'absolute', top: 3360, width: '100%', textAlign: 'center'}}>
        <Img
          src={staticFile('brand/lomond_logo.png')}
          style={{width: 1150, display: 'inline-block'}}
        />
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 40, marginTop: 60}}>
          <div style={{width: 300, height: 3, background: `linear-gradient(90deg, transparent, ${GOLD})`}} />
          <div style={{color: BURGUNDY_SOFT, fontSize: 44, lineHeight: 1}}>◆</div>
          <div style={{width: 300, height: 3, background: `linear-gradient(90deg, ${GOLD}, transparent)`}} />
        </div>
        <div
          style={{
            fontSize: 56,
            fontWeight: 500,
            letterSpacing: 32,
            color: BURGUNDY,
            textTransform: 'uppercase',
            marginTop: 28,
            marginLeft: 32,
            opacity: 0.75,
          }}
        >
          Fine Jewelry House
        </div>
      </div>
    </AbsoluteFill>
  );
};
