import React from 'react';
import { motion } from 'framer-motion';

interface SplitTextProps {
  text: string;
  className?: string;
  delay?: number;
  wordDelay?: number;
}

/**
 * SplitText Component (Inspired by React Bits & Vengeance UI)
 * Word-by-word animated headline reveal with spring easing.
 */
export const SplitText: React.FC<SplitTextProps> = ({
  text,
  className = '',
  delay = 0,
  wordDelay = 0.08,
}) => {
  const words = text.split(' ');

  return (
    <span className={`inline-block ${className}`}>
      {words.map((word, i) => (
        <span key={i} className="inline-block whitespace-nowrap mr-[0.25em]">
          <motion.span
            initial={{ opacity: 0.95, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.35,
              delay: delay + i * wordDelay,
              ease: [0.16, 1, 0.3, 1],
            }}
            className="inline-block"
          >
            {word}
          </motion.span>
        </span>
      ))}
    </span>
  );
};
