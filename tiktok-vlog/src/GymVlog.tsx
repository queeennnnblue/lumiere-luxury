import React from 'react';
import {
  AbsoluteFill,
  Img,
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
const BURGUNDY = '#4D0E13';
const CREME = '#EEE4DA';
const DUSTY_PINK = '#C8A49F';

type Clip = {
  from: number;
  duration: number;
  caption?: string;
  emojis?: string[]; // أكواد إيموجي آيفون (صور)
  hook?: boolean;
};

// الهوك: لقطات لمعة خاطفة مع فلاش أبيض، ثم لقطات أطول للفويس أوفر
export const CLIPS: Clip[] = [
  {from: 8.8, duration: 0.7, hook: true},
  {from: 37.5, duration: 0.7, hook: true},
  {from: 45.5, duration: 0.7, hook: true},
  {from: 84.5, duration: 0.9, hook: true},
  {from: 1.5, duration: 4.5, caption: 'مبالغة؟ ممكن… بس شوفوا اللمعة', emojis: ['2728']},
  {from: 8.5, duration: 3.5, caption: 'اللمعة هذي مو فلتر', emojis: ['1f48e']},
  {from: 38.5, duration: 4, caption: 'يقولون الألماس للمناسبات بس…'},
  {from: 45.0, duration: 4, caption: 'وأنا أقول: الألماس لكل يوم', emojis: ['1f60c']},
  {from: 60.5, duration: 4.5, caption: 'حديد × ألماس… ولا خدشة', emojis: ['1f4aa']},
  {from: 70.0, duration: 3.5, caption: 'اللمعة باقية مهما سوّيت'},
  {from: 84.0, duration: 4, caption: 'مبالغة ولا ستايل؟ احكموا', emojis: ['1f447']},
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
`;

const Emoji: React.FC<{code: string; size: number}> = ({code, size}) => (
  <Img
    src={staticFile(`emoji-${code}.png`)}
    style={{width: size, height: size, margin: '0 6px', verticalAlign: 'middle'}}
  />
);

// اللوقو الرسمي — ظاهر طول الفيديو
const Watermark: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      top: 110,
      left: 0,
      right: 0,
      display: 'flex',
      justifyContent: 'center',
    }}
  >
    <div
      style={{
        background: BURGUNDY,
        borderRadius: 20,
        padding: '18px 34px',
        boxShadow: '0 4px 24px rgba(0,0,0,0.55)',
      }}
    >
      <Img
        src={staticFile('lomond-mark.png')}
        style={{width: 220, display: 'block'}}
      />
    </div>
  </div>
);

const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)',
      pointerEvents: 'none',
    }}
  />
);

const Caption: React.FC<{text: string; emojis?: string[]}> = ({
  text,
  emojis,
}) => {
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
          color: CREME,
          background: 'rgba(77,14,19,0.72)',
          border: `2px solid ${DUSTY_PINK}55`,
          borderRadius: 26,
          padding: '10px 42px',
          maxWidth: 940,
          textAlign: 'center',
          textShadow: '0 3px 22px rgba(0,0,0,0.85)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          flexWrap: 'wrap',
          justifyContent: 'center',
        }}
      >
        <span>{text}</span>
        {emojis?.map((code) => (
          <Emoji key={code} code={code} size={56} />
        ))}
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
          color: CREME,
          background: BURGUNDY,
          borderRadius: 34,
          padding: '8px 52px',
          textAlign: 'center',
          boxShadow: '0 6px 40px rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <span>ألماس… في الجيم؟!</span>
        <Emoji code="1f633" size={80} />
        <Emoji code="1f48e" size={80} />
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
      {clip.caption ? (
        <Caption text={clip.caption} emojis={clip.emojis} />
      ) : null}
      <AbsoluteFill style={{backgroundColor: 'white', opacity: flash}} />
    </AbsoluteFill>
  );
};

// كرت ختامي بهوية لوموند: اللوقو الرسمي على خلفية عنابية
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
        backgroundColor: BURGUNDY,
        opacity: fadeIn,
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
        gap: 44,
      }}
    >
      <Img
        src={staticFile('lomond-mark.png')}
        style={{
          width: 640,
          transform: `scale(${interpolate(pop, [0, 1], [0.7, 1])})`,
        }}
      />
      <div
        dir="rtl"
        style={{
          fontFamily: 'Cairo, sans-serif',
          fontWeight: 700,
          fontSize: 44,
          color: CREME,
          display: 'flex',
          alignItems: 'center',
          opacity: interpolate(frame, [12, 26], [0, 0.9], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
        }}
      >
        <span>ألماس يعيش يومك</span>
        <Emoji code="2728" size={42} />
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
      {/* اللوقو ظاهر من البداية حتى نهاية اللقطات */}
      <Sequence from={0} durationInFrames={CLIPS_FRAMES}>
        <Watermark />
      </Sequence>
      <Sequence from={CLIPS_FRAMES} durationInFrames={ENDCARD_FRAMES}>
        <EndCard />
      </Sequence>
    </AbsoluteFill>
  );
};
