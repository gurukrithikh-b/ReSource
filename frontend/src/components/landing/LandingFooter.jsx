import React from 'react';
import { BrandLogo } from '../common/BrandLogo';

export const LandingFooter = ({ onEnterApp }) => {
  return (
    <footer
      style={{
        borderTop: '1px solid var(--border-color)',
        padding: '3rem 0 2rem 0',
        color: 'var(--text-dim)',
        fontSize: '0.85rem',
      }}
    >
      <div className="container" style={{ padding: 0 }}>
        <div
          style={{
            display: 'flex',
            justify: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1.5rem',
            marginBottom: '2rem',
          }}
        >
          <BrandLogo size="md" showTagline={true} />

          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <a
              href="#how-it-works"
              style={{ color: 'var(--text-muted)', textDecoration: 'none' }}
              onClick={(e) => {
                e.preventDefault();
                document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              How It Works
            </a>
            <a
              href="#impact"
              style={{ color: 'var(--text-muted)', textDecoration: 'none' }}
              onClick={(e) => {
                e.preventDefault();
                document.getElementById('impact')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Impact
            </a>
            <a
              href="#about"
              style={{ color: 'var(--text-muted)', textDecoration: 'none' }}
              onClick={(e) => {
                e.preventDefault();
                document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              About
            </a>
            <button
              onClick={onEnterApp}
              style={{ background: 'none', border: 'none', color: 'var(--primary-emerald)', fontWeight: 600, cursor: 'pointer' }}
            >
              Enter Application &rarr;
            </button>
          </div>
        </div>

        <div
          style={{
            textAlign: 'center',
            borderTop: '1px solid rgba(255, 255, 255, 0.05)',
            paddingTop: '1.5rem',
            fontSize: '0.8rem',
          }}
        >
          ReSource Network &mdash; Predict. Match. Redistribute. Sustain. Built for Software-Only Circular Resource Intelligence.
        </div>
      </div>
    </footer>
  );
};
