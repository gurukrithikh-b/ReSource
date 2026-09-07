import React from 'react';
import { TrendingUp, Target, Zap, Activity } from 'lucide-react';

export const ValueStrip = () => {
  const cards = [
    {
      title: 'PREDICT',
      desc: 'Anticipate future surplus and demand.',
      icon: <TrendingUp size={22} style={{ color: 'var(--accent-amber)' }} />,
      borderColor: 'rgba(245, 158, 11, 0.3)',
    },
    {
      title: 'MATCH',
      desc: 'Identify compatible resource needs.',
      icon: <Target size={22} style={{ color: 'var(--accent-cyan)' }} />,
      borderColor: 'rgba(6, 182, 212, 0.3)',
    },
    {
      title: 'OPTIMIZE',
      desc: 'Find the best multi-point allocation.',
      icon: <Zap size={22} style={{ color: 'var(--primary-emerald)' }} />,
      borderColor: 'rgba(16, 185, 129, 0.3)',
    },
    {
      title: 'MEASURE',
      desc: 'Quantify social and environmental impact.',
      icon: <Activity size={22} style={{ color: 'var(--accent-purple)' }} />,
      borderColor: 'rgba(139, 92, 246, 0.3)',
    },
  ];

  return (
    <section style={{ margin: '2rem 0 4rem 0' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1.25rem',
        }}
      >
        {cards.map((item, i) => (
          <div
            key={item.title}
            className="glass-card"
            style={{
              padding: '1.5rem',
              borderTop: `2px solid ${item.borderColor}`,
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
              transition: 'transform 0.2s ease, border-color 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span
                style={{
                  fontSize: '0.85rem',
                  fontWeight: 800,
                  letterSpacing: '0.1em',
                  color: '#fff',
                }}
              >
                {item.title}
              </span>
              {item.icon}
            </div>

            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              {item.desc}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
};
