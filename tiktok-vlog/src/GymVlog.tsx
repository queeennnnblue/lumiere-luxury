import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const FPS = 30;

// مقاطع مختارة من الفيديو الأصلي (بالثواني) — هوك سريع ثم لقطات أطول للفويس أوفر
type Clip = {
  from: number;
  duration: number;
  hook?: boolean;
};

export const CLIPS: Clip[] = [
  // الهوك: 3 لقطات خاطفة
  {from: 7.5, duration: 0.8, hook: true},
  {from: 37.0, duration: 0.8, hook: true},
  {from: 84.5, duration: 0.8, hook: true},
  // المقطع الأساسي
  {from: 1.5, duration: 4.5},
  {from: 8.5, duration: 3.5},
  {from: 38.5, duration: 4},
  {from: 45.0, duration: 4},
  {from: 60.5, duration: 4.5},
  {from: 70.0, duration: 3.5},
  {from: 84.0, duration: 4},
];

export const TOTAL_FRAMES = Math.round(
  CLIPS.reduce((sum, c) => sum + c.duration, 0) * FPS
);

const fontCss = `
@font-face {
  font-family: 'Marhey';
  font-weight: 700;
  src: url('${staticFile('Marhey-Bold.ttf')}') format('truetype');
}
`;

const Watermark: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [15, 45], [0, 0.9], {
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
        justifyContent: 'center',
        opacity,
      }}
    >
      <div
        style={{
          fontFamily: 'Marhey, sans-serif',
          fontWeight: 700,
          fontSize: 44,
          letterSpacing: 18,
          color: '#f5e6c4',
          textShadow: '0 2px 16px rgba(0,0,0,0.9)',
        }}
      >
        LOMOND
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
  const fadeIn = interpolate(frame, [0, clip.hook ? 2 : 5], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const fadeOut = isLast
    ? interpolate(frame, [durationInFrames - 20, durationInFrames - 1], [1, 0], {
        extrapolateLeft: 'clamp',
      })
    : 1;
  // اللقطات الخاطفة تبدأ مقرّبة أكثر لإحساس أسرع
  const scale = clip.hook
    ? interpolate(frame, [0, durationInFrames], [1.15, 1.08])
    : interpolate(frame, [0, durationInFrames], [1.04, 1.1]);
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
                  [0.5, 0.5, 0],
                  {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
                )
              : 0.5
          }
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>
      <Vignette />
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
