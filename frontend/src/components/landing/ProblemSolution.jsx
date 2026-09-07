import React from 'react';
import { AlertTriangle, CheckCircle2, ArrowRight, Package, Cpu, Heart } from 'lucide-react';

export const ProblemSolution = () => {
  return (
    <section id="about" style={{ padding: '4rem 0' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '2rem',
        }}
      >
        {/* Left: The Problem */}
        <div
          className="glass-card"
          style={{
            padding: '2.25rem',
            borderLeft: '4px solid #f87171',
            background: 'rgba(239, 68, 68, 0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem', color: '#f87171' }}>
            <AlertTriangle size={24} />
            <h3 style={{ fontSize: '1.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>The Problem</h3>
          </div>

          <p style={{ fontSize: '1.05rem', color: 'var(--text-main)', lineHeight: 1.6, marginBottom: '1.5rem' }}>
            Resources often exist in one place while people who need them are somewhere else. Without timely coordination, usable resources become waste while community needs remain unmet.
          </p>

          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div>&bull; High commercial food surplus going to landfills</div>
            <div>&bull; Manual, fragmented communication between suppliers and shelters</div>
            <div>&bull; Perishability window missed due to lack of predictive coordination</div>
          </div>
        </div>

        {/* Right: The ReSource Approach */}
        <div
          className="glass-card"
          style={{
            padding: '2.25rem',
            borderLeft: '4px solid var(--primary-emerald)',
            background: 'rgba(16, 185, 129, 0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem', color: 'var(--primary-emerald)' }}>
            <CheckCircle2 size={24} />
            <h3 style={{ fontSize: '1.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>The ReSource Approach</h3>
          </div>

          <p style={{ fontSize: '1.05rem', color: 'var(--text-main)', lineHeight: 1.6, marginBottom: '1.5rem' }}>
            ReSource connects the two sides through prediction, intelligent matching and optimized redistribution.
          </p>

          {/* Visual Flow Banner */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'rgba(15, 23, 42, 0.7)',
              padding: '1rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              fontSize: '0.85rem',
              fontWeight: 600,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-amber)' }}>
              <Package size={16} /> SURPLUS
            </div>
            <ArrowRight size={16} style={{ color: 'var(--text-dim)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--primary-emerald)' }}>
              <Cpu size={16} /> INTELLIGENCE
            </div>
            <ArrowRight size={16} style={{ color: 'var(--text-dim)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-cyan)' }}>
              <Heart size={16} /> IMPACT
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
