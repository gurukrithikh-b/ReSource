import React from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';
import { BrandLogo } from '../common/BrandLogo';

export const FinalCta = ({ onEnterApp }) => {
  return (
    <section style={{ padding: '4rem 0 2rem 0' }}>
      <div
        className="glass-card"
        style={{
          padding: '3.5rem 2rem',
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          background: 'radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.15) 0%, rgba(18, 26, 47, 0.8) 70%)',
        }}
      >
        <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'center' }}>
          <BrandLogo size="lg" />
        </div>

        <h2 style={{ fontSize: '2.4rem', fontWeight: 800, marginBottom: '1rem', color: '#fff' }}>
          Ready to put surplus to work?
        </h2>

        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', maxWidth: '580px', margin: '0 auto 2rem auto', lineHeight: 1.6 }}>
          Explore how ReSource predicts, matches and optimizes resource redistribution.
        </p>

        <button
          onClick={onEnterApp}
          className="btn-primary"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '10px',
            padding: '16px 36px',
            fontSize: '1.05rem',
            borderRadius: 'var(--radius-full)',
          }}
        >
          Launch ReSource <ArrowRight size={20} />
        </button>
      </div>
    </section>
  );
};
