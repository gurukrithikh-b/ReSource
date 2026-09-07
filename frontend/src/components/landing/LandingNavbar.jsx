import React from 'react';
import { BrandLogo } from '../common/BrandLogo';
import { ArrowRight } from 'lucide-react';

export const LandingNavbar = ({ onEnterApp }) => {
  const handleNav = (tab) => {
    if (onEnterApp) {
      onEnterApp(tab || 'architecture');
    }
  };

  return (
    <header className="navbar" style={{ background: 'rgba(10, 15, 29, 0.9)', backdropFilter: 'blur(16px)', padding: '0.75rem 2rem' }}>
      {/* Brand Logo */}
      <BrandLogo
        size="md"
      />

      {/* Navigation Links */}
      <nav className="desktop-nav">
        <ul className="nav-links" style={{ gap: '2rem' }}>
          <li>
            <button
              className="nav-btn"
              onClick={() => handleNav('architecture')}
              style={{ fontSize: '0.9rem' }}
            >
              How It Works
            </button>
          </li>
          <li>
            <button
              className="nav-btn"
              onClick={() => handleNav('matches')}
              style={{ fontSize: '0.9rem' }}
            >
              Impact
            </button>
          </li>
          <li>
            <button
              className="nav-btn"
              onClick={() => handleNav('architecture')}
              style={{ fontSize: '0.9rem' }}
            >
              About
            </button>
          </li>
        </ul>
      </nav>

      {/* Primary CTA */}
      <div>
        <button
          onClick={() => handleNav('architecture')}
          className="btn-primary"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 18px',
            fontSize: '0.88rem',
            borderRadius: 'var(--radius-full)',
          }}
        >
          Enter ReSource <ArrowRight size={16} />
        </button>
      </div>
    </header>
  );
};
