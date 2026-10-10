import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

interface StaggerTextProps {
  text: string;
  className?: string;
  delay?: number;
  staggerDuration?: number;
  as?: 'h1' | 'h2' | 'h3' | 'p' | 'span';
}

export const StaggerText: React.FC<StaggerTextProps> = ({
  text,
  className = '',
  delay = 0,
  staggerDuration = 0.05,
  as: Component = 'span',
}) => {
  const shouldReduceMotion = useReducedMotion();
  const words = text.split(' ');

  if (shouldReduceMotion) {
    return <Component className={className}>{text}</Component>;
  }

  const container = {
    hidden: { opacity: 0 },
    visible: (i = 1) => ({
      opacity: 1,
      transition: { staggerChildren: staggerDuration, delayChildren: delay * i },
    }),
  };

  const child = {
    visible: {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      transition: {
        type: 'spring' as const,
        damping: 15,
        stiffness: 100,
      },
    },
    hidden: {
      opacity: 0,
      y: 12,
      filter: 'blur(4px)',
    },
  };

  return (
    <motion.span
      className={`inline-block flex-wrap gap-x-1.5 ${className}`}
      variants={container}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
    >
      {words.map((word, index) => (
        <motion.span
          key={`${word}-${index}`}
          className="inline-block mr-1.5 last:mr-0"
          variants={child}
        >
          {word}
        </motion.span>
      ))}
    </motion.span>
  );
};
