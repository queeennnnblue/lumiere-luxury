import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Img, staticFile, delayRender, continueRender} from 'remotion';

// LUMIÈRE brand palette (matches styles.css)
const GOLD = '#c9a55c';
const GOLD_DEEP = '#9a7b3a';
const INK = '#2a2420';
const MUTED = '#8a8178';

const SIZE = 4096;
const PANEL = 2530; // product window
const PANEL_TOP = 640;

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
  const sparkles = Array.from({length: 26}, (_, i) => {
    const margin = 380;
    const zone = i % 4; // top / bottom / left / right margins only
    const x =
      zone === 0 || zone === 1
        ? rnd() * (SIZE - 400) + 200
        : zone === 2
          ? rnd() * margin + 130
          : SIZE - 130 - margin + rnd() * margin;
    const y =
      zone === 0
        ? rnd() * (PANEL_TOP - 250) + 170
        : zone === 1
          ? PANEL_TOP + PANEL + 90 + rnd() * 280
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
          radial-gradient(circle at 18% 8%, rgba(255,214,140,0.55) 0%, rgba(255,214,140,0.18) 28%, transparent 55%),
          radial-gradient(circle at 85% 90%, rgba(201,165,92,0.22) 0%, transparent 45%),
          radial-gradient(circle at 50% 45%, rgba(255,253,247,0.9) 0%, transparent 60%),
          linear-gradient(158deg, #fdf9ef 0%, #f8f0dd 38%, #f1e3c6 72%, #e9d7b2 100%)`,
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
          background: 'radial-gradient(circle at 50% 50%, transparent 55%, rgba(154,123,58,0.13) 100%)',
        }}
      />

      {/* background sparkles (kept off the product window) */}
      {sparkles.map((sp, i) => (
        <Sparkle key={i} {...sp} />
      ))}

      {/* double gold hairline frame */}
      <div style={{position: 'absolute', inset: 96, border: `4px solid ${GOLD}`, opacity: 0.9}} />
      <div style={{position: 'absolute', inset: 132, border: `1.5px solid ${GOLD_DEEP}`, opacity: 0.55}} />

      {/* kick line */}
      <div
        style={{
          position: 'absolute',
          top: 250,
          width: '100%',
          textAlign: 'center',
          fontSize: 64,
          fontWeight: 500,
          letterSpacing: 30,
          color: GOLD_DEEP,
          textTransform: 'uppercase',
        }}
      >
        Fine Jewelry
      </div>
      {/* piece number */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          right: 210,
          fontSize: 52,
          fontWeight: 500,
          letterSpacing: 6,
          color: GOLD_DEEP,
          opacity: 0.85,
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
          boxShadow: '0 90px 180px rgba(42,36,32,0.30), 0 30px 70px rgba(42,36,32,0.20)',
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

      {/* wordmark */}
      <div style={{position: 'absolute', top: 3330, width: '100%', textAlign: 'center'}}>
        <div style={{fontSize: 210, fontWeight: 700, letterSpacing: 44, color: INK, marginLeft: 44}}>
          LUMI<span style={{color: GOLD}}>È</span>RE
        </div>
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 40, marginTop: 26}}>
          <div style={{width: 300, height: 3, background: `linear-gradient(90deg, transparent, ${GOLD})`}} />
          <div style={{color: GOLD, fontSize: 44, lineHeight: 1}}>◆</div>
          <div style={{width: 300, height: 3, background: `linear-gradient(90deg, ${GOLD}, transparent)`}} />
        </div>
        <div
          style={{
            fontSize: 58,
            fontWeight: 500,
            letterSpacing: 34,
            color: MUTED,
            textTransform: 'uppercase',
            marginTop: 30,
            marginLeft: 34,
          }}
        >
          Luxury Designs
        </div>
      </div>
    </AbsoluteFill>
  );
};
