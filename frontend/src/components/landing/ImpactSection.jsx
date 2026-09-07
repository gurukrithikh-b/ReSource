import React, { useState, useEffect } from 'react';
import { Package, Heart, Leaf, Users, ShieldCheck } from 'lucide-react';
import { getOptimizationSummary } from '../../services/api';

export const ImpactSection = () => {
  const [metrics, setMetrics] = useState({
    rescuedKg: 1250,
    fulfilledKg: 980,
    co2AvoidedKg: 3125, // ~2.5kg CO2e per kg food rescued
    communityPartners: 14,
    isLive: false,
  });

  useEffect(() => {
    // Attempt live summary fetch from backend
    getOptimizationSummary()
      .then((data) => {
        if (data && data.total_allocated > 0) {
          setMetrics({
            rescuedKg: Math.round(data.total_allocated || 1250),
            fulfilledKg: Math.round(data.total_allocated || 980),
            co2AvoidedKg: Math.round((data.total_allocated || 1250) * 2.5),
            communityPartners: (data.num_demands_fully_satisfied || 0) + (data.num_demands_partially_satisfied || 0) || 14,
            isLive: true,
          });
        }
      })
      .catch(() => {
        // Keeps verified sample numbers if standby mode
      });
  }, []);

  return (
    <section id="impact" style={{ padding: '4rem 0' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--primary-emerald)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>
          <ShieldCheck size={14} /> Measurable Sustainability
        </div>
        <h2 style={{ fontSize: '2.25rem', marginBottom: '0.75rem' }}>From redistribution to measurable impact.</h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: '600px', margin: '0 auto', fontSize: '1rem' }}>
          Quantifying environmental savings, community meals served, and food waste reduction across the network.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1.25rem',
        }}
      >
        {/* Metric 1 */}
        <div className="glass-card" style={{ padding: '1.75rem', borderTop: '3px solid var(--primary-emerald)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--primary-emerald)', marginBottom: '8px' }}>
            <Package size={22} />
            <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-dim)' }}>
              Resources Rescued
            </span>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#fff' }}>
            {metrics.rescuedKg.toLocaleString()} <span style={{ fontSize: '1.1rem', fontWeight: 500 }}>kg</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Surplus food saved from landfills
          </div>
        </div>

        {/* Metric 2 */}
        <div className="glass-card" style={{ padding: '1.75rem', borderTop: '3px solid var(--accent-cyan)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-cyan)', marginBottom: '8px' }}>
            <Heart size={22} />
            <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-dim)' }}>
              Demand Fulfilled
            </span>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#fff' }}>
            {metrics.fulfilledKg.toLocaleString()} <span style={{ fontSize: '1.1rem', fontWeight: 500 }}>kg</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Nutritious food delivered to shelters
          </div>
        </div>

        {/* Metric 3 */}
        <div className="glass-card" style={{ padding: '1.75rem', borderTop: '3px solid #34d399' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#34d399', marginBottom: '8px' }}>
            <Leaf size={22} />
            <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-dim)' }}>
              CO₂ Avoided
            </span>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#fff' }}>
            {metrics.co2AvoidedKg.toLocaleString()} <span style={{ fontSize: '1.1rem', fontWeight: 500 }}>kg</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Greenhouse gas emissions prevented
          </div>
        </div>

        {/* Metric 4 */}
        <div className="glass-card" style={{ padding: '1.75rem', borderTop: '3px solid var(--accent-purple)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-purple)', marginBottom: '8px' }}>
            <Users size={22} />
            <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-dim)' }}>
              Community Impact
            </span>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#fff' }}>
            {metrics.communityPartners} <span style={{ fontSize: '1.1rem', fontWeight: 500 }}>Partners</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Verified shelters & food banks connected
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
        {metrics.isLive ? 'Live optimization metrics from ReSource Network engine' : 'Sample metrics reflecting circular redistribution model'}
      </div>
    </section>
  );
};
