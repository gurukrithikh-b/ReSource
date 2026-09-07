import React from 'react';
import { Globe } from 'lucide-react';

export const SdgSection = () => {
  const sdgs = [
    { num: 'SDG 1', title: 'No Poverty', desc: 'Supporting vulnerable communities with essential resources.', color: '#e5243b' },
    { num: 'SDG 2', title: 'Zero Hunger', desc: 'Redistributing surplus food to eliminate food insecurity.', color: '#dda63a' },
    { num: 'SDG 10', title: 'Reduced Inequalities', desc: 'Ensuring equitable access to excess commercial supply.', color: '#dd1367' },
    { num: 'SDG 11', title: 'Sustainable Cities', desc: 'Building circular, resilient urban resource networks.', color: '#fd9d24' },
    { num: 'SDG 12', title: 'Responsible Consumption', desc: 'Preventing organic waste and reducing carbon footprint.', color: '#bf8b2e' },
  ];

  return (
    <section style={{ padding: '3rem 0' }}>
      <div className="glass-card" style={{ padding: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.25rem' }}>
          <Globe size={22} style={{ color: 'var(--accent-cyan)' }} />
          <h3 style={{ fontSize: '1.2rem', color: '#fff' }}>Aligned with UN Sustainable Development Goals</h3>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
            gap: '1rem',
          }}
        >
          {sdgs.map((sdg) => (
            <div
              key={sdg.num}
              style={{
                backgroundColor: 'rgba(15, 23, 42, 0.6)',
                padding: '1rem',
                borderRadius: 'var(--radius-sm)',
                borderLeft: `3px solid ${sdg.color}`,
              }}
            >
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: sdg.color, letterSpacing: '0.5px' }}>
                {sdg.num}
              </div>
              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#fff', margin: '3px 0' }}>
                {sdg.title}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                {sdg.desc}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
