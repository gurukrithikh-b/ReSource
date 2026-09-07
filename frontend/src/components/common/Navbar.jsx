import React from 'react';
import { Layers, Activity, Package, Heart, TrendingUp, Target, Route, Leaf } from 'lucide-react';

export const Navbar = ({ healthStatus, activeTab, setActiveTab, onGoToLanding }) => {
  return (
    <header className="navbar">
      <div
        className="brand-logo"
        onClick={onGoToLanding}
        style={{ cursor: onGoToLanding ? 'pointer' : 'default' }}
      >
        <Layers className="brand-accent" size={28} />
        <div>
          <span>Re<span className="brand-accent">Source</span></span>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 400 }}>
            Predict. Match. Redistribute. Sustain.
          </p>
        </div>
      </div>


      <nav>
        <ul className="nav-links">
          <li>
            <button
              className={`nav-btn ${activeTab === 'architecture' ? 'active' : ''}`}
              onClick={() => setActiveTab('architecture')}
            >
              <Activity size={16} /> How ReSource Works
            </button>
          </li>
          <li>
            <button
              className={`nav-btn ${activeTab === 'surplus' ? 'active' : ''}`}
              onClick={() => setActiveTab('surplus')}
            >
              <Package size={16} /> Available Resources
            </button>
          </li>
          <li>
            <button
              className={`nav-btn ${activeTab === 'demand' ? 'active' : ''}`}
              onClick={() => setActiveTab('demand')}
            >
              <Heart size={16} /> Resource Needs
            </button>
          </li>
          <li>
            <button
              className={`nav-btn ${activeTab === 'prediction' ? 'active' : ''}`}
              onClick={() => setActiveTab('prediction')}
            >
              <TrendingUp size={16} /> Future Supply & Demand
            </button>
          </li>
          <li>
            <button
              className={`nav-btn ${activeTab === 'matches' ? 'active' : ''}`}
              onClick={() => setActiveTab('matches')}
            >
              <Target size={16} /> Smart Matches
            </button>
          </li>
          <li>
            <button
              className={`nav-btn ${activeTab === 'optimization' ? 'active' : ''}`}
              onClick={() => setActiveTab('optimization')}
            >
              <Route size={16} /> Best Allocation
            </button>
          </li>
          <li>
            <button
              className={`nav-btn ${activeTab === 'impact' ? 'active' : ''}`}
              onClick={() => setActiveTab('impact')}
            >
              <Leaf size={16} /> Sustainability Impact
            </button>
          </li>
        </ul>
      </nav>


      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span className="badge badge-simulated">Circular Intelligence Network</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: healthStatus?.status === 'online' ? '#10b981' : '#f59e0b',
            display: 'inline-block'
          }}></span>
          {healthStatus?.status === 'online' ? 'System Online' : 'System Standby'}
        </div>
      </div>
    </header>
  );
};
