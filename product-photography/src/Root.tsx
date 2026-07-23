import React from 'react';
import {Composition} from 'remotion';
import {ProductCard} from './ProductCard';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ProductCard"
      component={ProductCard}
      width={4096}
      height={4096}
      fps={1}
      durationInFrames={1}
      defaultProps={{src: 'products/product_01.jpg', index: 1, total: 50}}
    />
  );
};
