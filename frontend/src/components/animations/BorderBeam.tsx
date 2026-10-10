import React from 'react';

interface BorderBeamProps {
  className?: string;
  size?: number;
  duration?: number;
  delay?: number;
  borderWidth?: number;
  colorFrom?: string;
  colorTo?: string;
}

/**
 * BorderBeam Component (Inspired by Vengeance UI & 21st.dev)
 * Generates an animated glowing beam that travels along a container's border.
 */
export const BorderBeam: React.FC<BorderBeamProps> = ({
  className = '',
  size = 200,
  duration = 8,
  delay = 0,
  borderWidth = 1.5,
  colorFrom = '#D7F36B',
  colorTo = '#184436',
}) => {
  return (
    <div
      style={
        {
          '--size': `${size}px`,
          '--duration': `${duration}s`,
          '--border-width': `${borderWidth}px`,
          '--color-from': colorFrom,
          '--color-to': colorTo,
        } as React.CSSProperties
      }
      className={`pointer-events-none absolute inset-0 rounded-[inherit] border border-transparent [mask-clip:padding-box,border-box] [mask-composite:intersect] [mask-image:linear-gradient(transparent,transparent),linear-gradient(#000,#000)] ${className}`}
    >
      <div
        className="absolute aspect-square animate-border-beam bg-gradient-to-l from-[var(--color-from)] via-[var(--color-to)] to-transparent"
        style={{
          width: 'var(--size)',
          offsetPath: 'rect(0 auto auto 0 round calc(var(--size) / 2))',
          animationDuration: 'var(--duration)',
        }}
      />
    </div>
  );
};
