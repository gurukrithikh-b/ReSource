import React, { useState } from 'react';
import { Sparkles, ArrowRight, Building2, Heart, ShieldCheck, CheckCircle2 } from 'lucide-react';

export const LandingHero = ({ onEnterApp }) => {
  const [selectedRole, setSelectedRole] = useState('provider'); // 'provider' | 'partner'

  const handleContinue = () => {
    if (onEnterApp) {
      if (selectedRole === 'provider') {
        onEnterApp('surplus');
      } else {
        onEnterApp('demand');
      }
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '1.75rem',
        width: '100%',
        margin: '0 auto',
      }}
    >
      {/* 2-Column Product Pitch & Role Entry Gateway */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '2.5rem',
          alignItems: 'center',
        }}
      >
        {/* Left Column: Core Product Positioning */}
        <div>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '5px 14px',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              color: 'var(--primary-emerald)',
              fontSize: '0.8rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '1.25rem',
            }}
          >
            <Sparkles size={14} /> Circular Resource Intelligence Network
          </div>

          <h1
            style={{
              fontSize: 'clamp(2.2rem, 4.2vw, 3.4rem)',
              fontWeight: 800,
              lineHeight: 1.15,
              marginBottom: '1.25rem',
              letterSpacing: '-0.02em',
            }}
          >
            Predict surplus.<br />
            Match real needs.<br />
            <span style={{ color: 'var(--primary-emerald)' }}>Redistribute smarter.</span>
          </h1>

          <p
            style={{
              fontSize: '1.05rem',
              color: 'var(--text-muted)',
              lineHeight: 1.6,
              marginBottom: '1.5rem',
              maxWidth: '540px',
            }}
          >
            ReSource predicts surplus and community demand, intelligently matches them, and optimizes redistribution to reduce waste and improve resource access.
          </p>

          <div
            style={{
              fontSize: '0.85rem',
              fontWeight: 600,
              color: 'var(--primary-emerald)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <ShieldCheck size={16} /> Predict. Match. Redistribute. Sustain.
          </div>
        </div>

        {/* Right Column: Compact Glassmorphic Entry Card */}
        <div>
          <div
            className="glass-card"
            style={{
              padding: '2rem',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5), 0 0 30px rgba(16, 185, 129, 0.1)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem',
            }}
          >
            <div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', marginBottom: '4px' }}>
                Enter ReSource
              </h2>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
                Connect surplus resources with real community needs.
              </p>
            </div>

            {/* Role Selection Options */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {/* Option 1: Resource Provider */}
              <div
                onClick={() => setSelectedRole('provider')}
                style={{
                  padding: '1rem 1.15rem',
                  borderRadius: 'var(--radius-md)',
                  border: selectedRole === 'provider'
                    ? '1.5px solid var(--primary-emerald)'
                    : '1px solid rgba(255, 255, 255, 0.1)',
                  backgroundColor: selectedRole === 'provider'
                    ? 'rgba(16, 185, 129, 0.12)'
                    : 'rgba(15, 23, 42, 0.6)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      backgroundColor: selectedRole === 'provider' ? 'var(--primary-emerald)' : 'rgba(255, 255, 255, 0.08)',
                      color: selectedRole === 'provider' ? '#000' : 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                    }}
                  >
                    <Building2 size={18} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
                      Resource Provider
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      Share available surplus
                    </div>
                  </div>
                </div>

                {selectedRole === 'provider' && (
                  <CheckCircle2 size={20} style={{ color: 'var(--primary-emerald)' }} />
                )}
              </div>

              {/* Option 2: Community Partner */}
              <div
                onClick={() => setSelectedRole('partner')}
                style={{
                  padding: '1rem 1.15rem',
                  borderRadius: 'var(--radius-md)',
                  border: selectedRole === 'partner'
                    ? '1.5px solid var(--accent-cyan)'
                    : '1px solid rgba(255, 255, 255, 0.1)',
                  backgroundColor: selectedRole === 'partner'
                    ? 'rgba(6, 182, 212, 0.12)'
                    : 'rgba(15, 23, 42, 0.6)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      backgroundColor: selectedRole === 'partner' ? 'var(--accent-cyan)' : 'rgba(255, 255, 255, 0.08)',
                      color: selectedRole === 'partner' ? '#000' : 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                    }}
                  >
                    <Heart size={18} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
                      Community Partner
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      Share resource needs
                    </div>
                  </div>
                </div>

                {selectedRole === 'partner' && (
                  <CheckCircle2 size={20} style={{ color: 'var(--accent-cyan)' }} />
                )}
              </div>
            </div>

            {/* Continue Action Button */}
            <button
              onClick={handleContinue}
              className="btn-primary"
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '14px',
                fontSize: '1rem',
                borderRadius: 'var(--radius-md)',
                marginTop: '0.25rem',
              }}
            >
              Continue <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Technology & Value Strip */}
      <div
        style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          paddingTop: '1.25rem',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        <div
          style={{
            fontSize: '0.85rem',
            fontWeight: 600,
            color: 'var(--text-muted)',
            letterSpacing: '0.04em',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            flexWrap: 'wrap',
          }}
        >
          <span>Predictive AI</span>
          <span style={{ color: 'var(--primary-emerald)' }}>&bull;</span>
          <span>Smart Matching</span>
          <span style={{ color: 'var(--primary-emerald)' }}>&bull;</span>
          <span>Global Optimization</span>
          <span style={{ color: 'var(--primary-emerald)' }}>&bull;</span>
          <span>Measurable Impact</span>
        </div>

        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
          Turning surplus into measurable community impact.
        </div>
      </div>
    </div>
  );
};

export default LandingHero;
