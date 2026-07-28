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

// ألوان هوية لوموند
const MAROON = '#5D131F';
const CREAM = '#EDE3D5';

type Clip = {
  from: number;
  duration: number;
  caption?: string;
  hook?: boolean;
};

// الهوك: لقطات لمعة خاطفة مع فلاش أبيض، ثم لقطات أطول للفويس أوفر
export const CLIPS: Clip[] = [
  {from: 8.8, duration: 0.7, hook: true},
  {from: 37.5, duration: 0.7, hook: true},
  {from: 45.5, duration: 0.7, hook: true},
  {from: 84.5, duration: 0.9, hook: true},
  {from: 1.5, duration: 4.5, caption: 'مبالغة؟ ممكن… بس شوفوا اللمعة ✨'},
  {from: 8.5, duration: 3.5, caption: 'اللمعة هذي مو فلتر 💎'},
  {from: 38.5, duration: 4, caption: 'يقولون الألماس للمناسبات بس…'},
  {from: 45.0, duration: 4, caption: 'وأنا أقول: الألماس لكل يوم 😌'},
  {from: 60.5, duration: 4.5, caption: 'حديد × ألماس… ولا خدشة 💪'},
  {from: 70.0, duration: 3.5, caption: 'اللمعة باقية مهما سوّيت'},
  {from: 84.0, duration: 4, caption: 'مبالغة ولا ستايل؟ احكموا 👇'},
];

const HOOK_FRAMES = Math.round(
  CLIPS.filter((c) => c.hook).reduce((s, c) => s + c.duration, 0) * FPS
);
const CLIPS_FRAMES = Math.round(
  CLIPS.reduce((sum, c) => sum + c.duration, 0) * FPS
);
const ENDCARD_FRAMES = 55;
export const TOTAL_FRAMES = CLIPS_FRAMES + ENDCARD_FRAMES;

const fontCss = `
@font-face {
  font-family: 'Cairo';
  font-weight: 700;
  src: url('${staticFile('Cairo-Bold.ttf')}') format('truetype');
}
@font-face {
  font-family: 'Shrikhand';
  font-weight: 400;
  src: url('${staticFile('Shrikhand.ttf')}') format('truetype');
}
`;

// شعار لوموند: بادج عنابي بخط كريمي مموّج
const LomondBadge: React.FC<{size?: number}> = ({size = 40}) => (
  <div
    style={{
      background: MAROON,
      borderRadius: size * 0.45,
      padding: `${size * 0.28}px ${size * 0.85}px ${size * 0.42}px`,
      boxShadow: '0 4px 24px rgba(0,0,0,0.55)',
    }}
  >
    <div
      style={{
        fontFamily: 'Shrikhand, serif',
        fontSize: size,
        letterSpacing: size * 0.06,
        color: CREAM,
        lineHeight: 1,
      }}
    >
      LOMOND
    </div>
  </div>
);

const Watermark: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [10, 35], [0, 0.95], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        position: 'absolute',
        top: 110,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        opacity,
      }}
    >
      <LomondBadge size={38} />
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

const Caption: React.FC<{text: string}> = ({text}) => {
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
        bottom: 430,
        display: 'flex',
        justifyContent: 'center',
        opacity: pop,
        transform: `translateY(${y}px)`,
      }}
    >
      <div
        dir="rtl"
        style={{
          fontFamily: 'Cairo, sans-serif',
          fontWeight: 700,
          fontSize: 58,
          lineHeight: 1.5,
          color: CREAM,
          background: 'rgba(35,6,12,0.55)',
          border: `2px solid rgba(237,227,213,0.25)`,
          borderRadius: 26,
          padding: '8px 42px',
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

// كابشن الهوك الكبير فوق اللقطات الخاطفة
const HookTitle: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 10, mass: 0.6}});
  const shake = Math.sin(frame * 1.4) * interpolate(pop, [0, 1], [0, 2.5]);
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 500,
        display: 'flex',
        justifyContent: 'center',
        transform: `scale(${interpolate(pop, [0, 1], [1.6, 1])}) rotate(${shake}deg)`,
        opacity: pop,
      }}
    >
      <div
        dir="rtl"
        style={{
          fontFamily: 'Cairo, sans-serif',
          fontWeight: 700,
          fontSize: 84,
          color: CREAM,
          background: MAROON,
          borderRadius: 34,
          padding: '6px 52px',
          textAlign: 'center',
          boxShadow: '0 6px 40px rgba(0,0,0,0.7)',
        }}
      >
        ألماس… في الجيم؟! 😳💎
      </div>
    </div>
  );
};

const ClipSegment: React.FC<{clip: Clip; isLast: boolean}> = ({
  clip,
  isLast,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const fadeIn = clip.hook
    ? 1
    : interpolate(frame, [0, 5], [0, 1], {extrapolateRight: 'clamp'});
  // فلاش أبيض قصير مع بداية كل لقطة هوك
  const flash = clip.hook
    ? interpolate(frame, [0, 3], [0.9, 0], {
        extrapolateRight: 'clamp',
        extrapolateLeft: 'clamp',
      })
    : 0;
  // بانش زوم للهوك، وزوم بطيء للباقي
  const scale = clip.hook
    ? interpolate(frame, [0, durationInFrames], [1.3, 1.12])
    : interpolate(frame, [0, durationInFrames], [1.04, 1.1]);
  const fadeOut = isLast
    ? interpolate(frame, [durationInFrames - 12, durationInFrames - 1], [1, 0], {
        extrapolateLeft: 'clamp',
      })
    : 1;
  return (
    <AbsoluteFill style={{opacity: fadeIn * fadeOut, backgroundColor: 'black'}}>
      <AbsoluteFill style={{transform: `scale(${scale})`}}>
        <OffthreadVideo
          src={staticFile('vlog.mp4')}
          muted
          trimBefore={Math.round(clip.from * FPS)}
          trimAfter={Math.round((clip.from + clip.duration) * FPS) + 10}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>
      <Vignette />
      {clip.caption ? <Caption text={clip.caption} /> : null}
      <AbsoluteFill style={{backgroundColor: 'white', opacity: flash}} />
    </AbsoluteFill>
  );
};

// كرت ختامي بهوية لوموند
const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 13, mass: 0.8}});
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: MAROON,
        opacity: fadeIn,
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
        gap: 30,
      }}
    >
      <div
        style={{
          fontFamily: 'Shrikhand, serif',
          fontSize: 150,
          color: CREAM,
          letterSpacing: 6,
          transform: `scale(${interpolate(pop, [0, 1], [0.7, 1])})`,
        }}
      >
        LOMOND
      </div>
      <div
        dir="rtl"
        style={{
          fontFamily: 'Cairo, sans-serif',
          fontWeight: 700,
          fontSize: 44,
          color: CREAM,
          opacity: interpolate(frame, [12, 26], [0, 0.85], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
        }}
      >
        ألماس يعيش يومك ✨
      </div>
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
      <Sequence from={0} durationInFrames={HOOK_FRAMES}>
        <HookTitle />
      </Sequence>
      <Sequence from={HOOK_FRAMES} durationInFrames={CLIPS_FRAMES - HOOK_FRAMES}>
        <Watermark />
      </Sequence>
      <Sequence from={CLIPS_FRAMES} durationInFrames={ENDCARD_FRAMES}>
        <EndCard />
      </Sequence>
    </AbsoluteFill>
  );
};
