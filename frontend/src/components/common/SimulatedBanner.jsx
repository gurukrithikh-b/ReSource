import React from 'react';
import { Info } from 'lucide-react';

export const SimulatedBanner = () => {
  return (
    <div style={{
      background: 'rgba(245, 158, 11, 0.08)',
      border: '1px solid rgba(245, 158, 11, 0.25)',
      borderRadius: 'var(--radius-md)',
      padding: '12px 18px',
      marginBottom: '1.5rem',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      fontSize: '0.85rem',
      color: '#fcd34d'
    }}>
      <Info size={20} style={{ flexShrink: 0, color: '#f59e0b' }} />
      <div>
        <strong>Demonstration Mode:</strong> Sample resource listings are displayed and clearly tagged for platform demonstration and testing.
      </div>
    </div>
  );
};
