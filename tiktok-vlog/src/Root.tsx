import React from 'react';
import {Composition} from 'remotion';
import {GymVlog, TOTAL_FRAMES} from './GymVlog';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="GymVlog"
      component={GymVlog}
      durationInFrames={TOTAL_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};
