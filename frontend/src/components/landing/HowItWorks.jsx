import React from 'react';
import { Sparkles, Brain, Target, Route } from 'lucide-react';

export const HowItWorks = () => {
  const steps = [
    {
      num: '01',
      title: 'Capture',
      desc: 'Providers and community partners describe available resources and needs in natural language.',
      icon: <Sparkles size={24} style={{ color: 'var(--accent-purple)' }} />,
    },
    {
      num: '02',
      title: 'Understand',
      desc: 'ReSource converts natural-language information into structured resource intelligence.',
      icon: <Brain size={24} style={{ color: 'var(--accent-cyan)' }} />,
    },
    {
      num: '03',
      title: 'Predict & Match',
      desc: 'AI/ML predicts supply and demand and identifies compatible matches.',
      icon: <Target size={24} style={{ color: 'var(--accent-amber)' }} />,
    },
    {
      num: '04',
      title: 'Optimize',
      desc: 'Global optimization determines how resources should be allocated efficiently.',
      icon: <Route size={24} style={{ color: 'var(--primary-emerald)' }} />,
    },
  ];

  return (
    <section id="how-it-works" style={{ padding: '4rem 0' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '2.25rem', marginBottom: '0.75rem' }}>How ReSource Works</h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: '640px', margin: '0 auto', fontSize: '1rem' }}>
          An end-to-end intelligent pipeline transforming unstructured food notes into verified, optimized community food transfers.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '1.5rem',
        }}
      >
        {steps.map((step) => (
          <div
            key={step.num}
            className="glass-card"
            style={{
              padding: '1.75rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              position: 'relative',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span
                style={{
                  fontSize: '1.8rem',
                  fontWeight: 800,
                  color: 'var(--text-dim)',
                  fontFamily: "'Outfit', sans-serif",
                }}
              >
                {step.num}
              </span>
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                {step.icon}
              </div>
            </div>

            <h3 style={{ fontSize: '1.2rem', color: '#fff' }}>{step.title}</h3>

            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              {step.desc}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
};
