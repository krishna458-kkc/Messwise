import React, { useEffect, useRef } from 'react';
import { useInView, useMotionValue, useSpring } from 'framer-motion';

interface CountUpProps {
  to: number;
  from?: number;
  direction?: 'up' | 'down';
  delay?: number;
  duration?: number;
  className?: string;
  decimals?: number;
  separator?: string;
  suffix?: string;
  prefix?: string;
}

/**
 * CountUp Component (Inspired by React Bits)
 * High-performance smooth numerical spring counter with visibility trigger.
 */
export const CountUp: React.FC<CountUpProps> = ({
  to,
  from = 0,
  direction = 'up',
  delay = 0,
  duration = 1.6,
  className = '',
  decimals = 0,
  separator = ',',
  suffix = '',
  prefix = '',
}) => {
  const ref = useRef<HTMLSpanElement>(null);
  const motionVal = useMotionValue(direction === 'down' ? to : from);

  const damping = 20 + 40 * (1 / duration);
  const stiffness = 100 * (1 / duration);

  const springVal = useSpring(motionVal, {
    damping,
    stiffness,
  });

  const isInView = useInView(ref, { once: true, margin: '0px' });

  useEffect(() => {
    if (isInView) {
      const timer = setTimeout(() => {
        motionVal.set(direction === 'down' ? from : to);
      }, delay * 1000);
      return () => clearTimeout(timer);
    }
  }, [isInView, delay, to, from, direction, motionVal]);

  useEffect(() => {
    const unsubscribe = springVal.on('change', (latest) => {
      if (ref.current) {
        const formatted = Number(latest).toFixed(decimals);
        const parts = formatted.split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, separator);
        ref.current.textContent = `${prefix}${parts.join('.')}${suffix}`;
      }
    });
    return () => unsubscribe();
  }, [springVal, decimals, separator, suffix, prefix]);

  return (
    <span ref={ref} className={`tabular-nums ${className}`}>
      {prefix}
      {from.toFixed(decimals)}
      {suffix}
    </span>
  );
};
