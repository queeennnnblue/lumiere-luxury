import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const FPS = 30;

// مقاطع مختارة من الفيديو الأصلي (بالثواني)
type Clip = {
  from: number; // بداية المقطع في المصدر
  duration: number; // مدة المقطع
  caption: string;
  sub?: string;
};

export const CLIPS: Clip[] = [
  {from: 1.5, duration: 5, caption: 'يوم عفوي في الجيم 🖤', sub: 'GYM DIARY'},
  {from: 7.0, duration: 4, caption: 'وطبعًا الألماس معي ✨'},
  {from: 36.0, duration: 5, caption: 'سوار التنس ما يفارق معصمي 💎'},
  {from: 44.5, duration: 5, caption: 'لمعة تثبت معك مهما تحرّكت'},
  {from: 60.0, duration: 5, caption: 'قطع مصمّمة تتحمّل يومك كله 💪'},
  {from: 83.5, duration: 4.5, caption: 'عفوية… وفخامة 🤍', sub: 'LUMIÈRE'},
];

export const TOTAL_FRAMES = Math.round(
  CLIPS.reduce((sum, c) => sum + c.duration, 0) * FPS
);

const fontCss = `
@font-face {
  font-family: 'Cairo';
  font-weight: 700;
  src: url('${staticFile('Cairo-Bold.ttf')}') format('truetype');
}
@font-face {
  font-family: 'Cairo';
  font-weight: 400;
  src: url('${staticFile('Cairo-Regular.ttf')}') format('truetype');
}
@font-face {
  font-family: 'Marhey';
  font-weight: 700;
  src: url('${staticFile('Marhey-Bold.ttf')}') format('truetype');
}
`;

const Caption: React.FC<{text: string; sub?: string}> = ({text, sub}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 14, mass: 0.7}});
  const y = interpolate(pop, [0, 1], [40, 0]);
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 420,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 18,
        opacity: pop,
        transform: `translateY(${y}px)`,
      }}
    >
      {sub ? (
        <div
          style={{
            fontFamily: 'Marhey, Cairo, sans-serif',
            fontWeight: 700,
            fontSize: 34,
            letterSpacing: 14,
            color: '#e8c87a',
            textShadow: '0 2px 18px rgba(0,0,0,0.9)',
          }}
        >
          {sub}
        </div>
      ) : null}
      <div
        dir="rtl"
        style={{
          fontFamily: 'Cairo, sans-serif',
          fontWeight: 700,
          fontSize: 62,
          lineHeight: 1.5,
          color: '#ffffff',
          background: 'rgba(0,0,0,0.42)',
          borderRadius: 28,
          padding: '10px 44px',
          maxWidth: 940,
          textAlign: 'center',
          textShadow: '0 3px 22px rgba(0,0,0,0.85)',
          backdropFilter: 'blur(6px)',
        }}
      >
        {text}
      </div>
    </div>
  );
};

const Watermark: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [20, 50], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        position: 'absolute',
        top: 120,
        left: 0,
        right: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 4,
        opacity,
      }}
    >
      <div
        style={{
          fontFamily: 'Marhey, Cairo, sans-serif',
          fontWeight: 700,
          fontSize: 44,
          letterSpacing: 18,
          color: '#f5e6c4',
          textShadow: '0 2px 16px rgba(0,0,0,0.9)',
        }}
      >
        LUMIÈRE
      </div>
      <div
        style={{
          fontFamily: 'Cairo, sans-serif',
          fontWeight: 400,
          fontSize: 26,
          letterSpacing: 6,
          color: 'rgba(255,255,255,0.75)',
          textShadow: '0 2px 12px rgba(0,0,0,0.9)',
        }}
      >
        لوميـير
      </div>
    </div>
  );
};

const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)',
      pointerEvents: 'none',
    }}
  />
);

const ClipSegment: React.FC<{clip: Clip; isLast: boolean}> = ({
  clip,
  isLast,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const fadeIn = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const fadeOut = isLast
    ? interpolate(frame, [durationInFrames - 20, durationInFrames - 1], [1, 0], {
        extrapolateLeft: 'clamp',
      })
    : 1;
  // حركة تقريب خفيفة تعطي إحساس المونتاج الحي
  const scale = interpolate(frame, [0, durationInFrames], [1.04, 1.1]);
  return (
    <AbsoluteFill style={{opacity: fadeIn * fadeOut, backgroundColor: 'black'}}>
      <AbsoluteFill style={{transform: `scale(${scale})`}}>
        <OffthreadVideo
          src={staticFile('vlog.mp4')}
          trimBefore={Math.round(clip.from * FPS)}
          trimAfter={Math.round((clip.from + clip.duration) * FPS) + 10}
          volume={(f) =>
            isLast
              ? interpolate(
                  f,
                  [0, durationInFrames - 25, durationInFrames - 1],
                  [0.9, 0.9, 0],
                  {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
                )
              : 0.9
          }
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>
      <Vignette />
      <Caption text={clip.caption} sub={clip.sub} />
    </AbsoluteFill>
  );
};

export const GymVlog: React.FC = () => {
  let cursor = 0;
  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      <style>{fontCss}</style>
      {CLIPS.map((clip, i) => {
        const start = cursor;
        const dur = Math.round(clip.duration * FPS);
        cursor += dur;
        return (
          <Sequence key={i} from={start} durationInFrames={dur}>
            <ClipSegment clip={clip} isLast={i === CLIPS.length - 1} />
          </Sequence>
        );
      })}
      <Watermark />
    </AbsoluteFill>
  );
};
