import React, { useState, useEffect } from 'react';
import { BrandLogo } from '../common/BrandLogo';

export const IntroAnimation = ({ onComplete }) => {
  const [stage, setStage] = useState(1); // 1: Logo Entrance, 2: Network Formation, 3: Brand Statement, 4: Fade Transition

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      const timer = setTimeout(() => {
        if (onComplete) onComplete();
      }, 350);
      return () => clearTimeout(timer);
    }

    // STAGE 1: Logo Entrance (0ms -> 1400ms)
    const t1 = setTimeout(() => {
      setStage(2); // STAGE 2: Resource network formation
    }, 1400);

    // STAGE 2 -> STAGE 3: Brand Statement (2400ms)
    const t2 = setTimeout(() => {
      setStage(3);
    }, 2400);

    // STAGE 3 -> STAGE 4: Smooth Transition (3200ms)
    const t3 = setTimeout(() => {
      setStage(4);
    }, 3200);

    // End Intro & Unmount (3700ms)
    const t4 = setTimeout(() => {
      if (onComplete) onComplete();
    }, 3700);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [onComplete]);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: '#0a0f1d',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        opacity: stage === 4 ? 0 : 1,
        transition: 'opacity 0.5s ease-out',
        pointerEvents: stage === 4 ? 'none' : 'auto',
        overflow: 'hidden',
      }}
    >
      {/* Background Radial Glow */}
      <div
        style={{
          position: 'absolute',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.05) 50%, transparent 70%)',
          transform: `scale(${stage >= 2 ? 1.2 : 0.85})`,
          transition: 'transform 1s ease-out, opacity 0.8s ease',
          opacity: stage >= 1 ? 1 : 0,
        }}
      />

      {/* STAGE 2: Resource Network Formation SVG */}
      <svg
        style={{
          position: 'absolute',
          width: '420px',
          height: '420px',
          pointerEvents: 'none',
          opacity: stage >= 2 ? 1 : 0,
          transition: 'opacity 0.7s ease-in-out',
        }}
        viewBox="0 0 400 400"
      >
        {/* Network Connection Lines */}
        <g stroke="rgba(16, 185, 129, 0.35)" strokeWidth="1.5" strokeDasharray="4, 4">
          <line x1="200" y1="200" x2="80" y2="120" style={{ transition: 'all 0.8s ease-out' }} />
          <line x1="200" y1="200" x2="320" y2="110" style={{ transition: 'all 0.8s ease-out' }} />
          <line x1="200" y1="200" x2="90" y2="290" style={{ transition: 'all 0.8s ease-out' }} />
          <line x1="200" y1="200" x2="310" y2="280" style={{ transition: 'all 0.8s ease-out' }} />
        </g>

        {/* Floating Glowing Nodes */}
        <circle cx="80" cy="120" r="5" fill="#10b981" className="pulse-node" />
        <text x="75" y="100" fill="#9ca3af" fontSize="10" fontFamily="'Inter', sans-serif">Surplus Provider</text>

        <circle cx="320" cy="110" r="5" fill="#06b6d4" className="pulse-node" />
        <text x="300" y="90" fill="#9ca3af" fontSize="10" fontFamily="'Inter', sans-serif">Community Shelter</text>

        <circle cx="90" cy="290" r="5" fill="#f59e0b" className="pulse-node" />
        <text x="65" y="312" fill="#9ca3af" fontSize="10" fontFamily="'Inter', sans-serif">AI Prediction</text>

        <circle cx="310" cy="280" r="5" fill="#10b981" className="pulse-node" />
        <text x="290" y="302" fill="#9ca3af" fontSize="10" fontFamily="'Inter', sans-serif">Best Allocation</text>
      </svg>

      {/* Main ReSource Logo Container (STAGE 1: Entrance & Scale) */}
      <div
        style={{
          transform: stage === 1 ? 'scale(0.92)' : 'scale(1)',
          opacity: 1,
          transition: 'transform 1s cubic-bezier(0.16, 1, 0.3, 1)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '14px',
          zIndex: 10,
        }}
      >
        <BrandLogo size="xl" />

        {/* STAGE 3: Brand Statement */}
        <div
          style={{
            opacity: stage >= 3 ? 1 : 0,
            transform: `translateY(${stage >= 3 ? 0 : 8}px)`,
            transition: 'all 0.6s ease-out',
            fontSize: '1rem',
            color: 'var(--primary-emerald)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            fontWeight: 600,
            marginTop: '8px',
          }}
        >
          Predict. Match. Redistribute. Sustain.
        </div>
      </div>
    </div>
  );
};

export default IntroAnimation;
