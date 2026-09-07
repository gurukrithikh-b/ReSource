import React from 'react';

export const BrandLogo = ({
  size = 'md',
  showTagline = false,
  onClick,
  style = {},
}) => {
  const iconSizes = {
    sm: 24,
    md: 32,
    lg: 48,
    xl: 64,
  };

  const fontSizes = {
    sm: '1.2rem',
    md: '1.5rem',
    lg: '2.2rem',
    xl: '3rem',
  };

  const currentIconSize = iconSizes[size] || 32;
  const currentFontSize = fontSizes[size] || '1.5rem';

  return (
    <div
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '12px',
        cursor: onClick ? 'pointer' : 'default',
        userSelect: 'none',
        ...style,
      }}
    >
      {/* Icon Mark */}
      <svg
        width={currentIconSize}
        height={currentIconSize}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ flexShrink: 0 }}
      >
        <g stroke="#10b981" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round">
          <path d="M50 18 L82 34 L50 50 L18 34 Z" />
          <path d="M18 52 L50 68 L82 52" />
          <path d="M18 70 L50 86 L82 70" />
        </g>
      </svg>

      {/* Wordmark & optional Tagline */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: currentFontSize,
            fontWeight: 800,
            lineHeight: 1,
            letterSpacing: '-0.02em',
          }}
        >
          <span style={{ color: '#ffffff' }}>Re</span>
          <span style={{ color: '#10b981' }}>Source</span>
        </span>

        {showTagline && (
          <span
            style={{
              fontSize: size === 'xl' ? '0.9rem' : '0.72rem',
              color: 'var(--text-muted)',
              fontWeight: 400,
              marginTop: '4px',
              letterSpacing: '0.02em',
            }}
          >
            Predict. Match. Redistribute. Sustain.
          </span>
        )}
      </div>
    </div>
  );
};
