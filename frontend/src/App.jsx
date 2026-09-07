import React, { useState, useEffect } from 'react';
import { LandingPage } from './pages/LandingPage';
import { Navbar } from './components/common/Navbar';
import { SimulatedBanner } from './components/common/SimulatedBanner';
import { SurplusIntakeForm } from './components/forms/SurplusIntakeForm';
import { DemandIntakeForm } from './components/forms/DemandIntakeForm';
import { MatchExplorer } from './components/matching/MatchExplorer';
import { OptimizationDashboard } from './components/optimization/OptimizationDashboard';
import ImpactDashboard from './components/impact/ImpactDashboard';
import PredictionDashboard from './components/prediction/PredictionDashboard';
import { getHealthStatus, getSurplusListings, getDemandListings } from './services/api';

import {
  Sparkles,
  TrendingUp,
  Target,
  Route,
  Leaf,
  Users,
  Package,
  Heart,
  Clock,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

export function App() {
  const getInitialView = () => {
    const path = window.location.pathname;
    const hash = window.location.hash;
    if (path === '/app' || hash === '#app') return 'app';
    return 'landing';
  };

  const [currentView, setCurrentView] = useState(getInitialView);
  const [activeTab, setActiveTab] = useState('architecture');
  const [healthStatus, setHealthStatus] = useState(null);
  const [surplusListings, setSurplusListings] = useState([]);
  const [demandListings, setDemandListings] = useState([]);
  const [loading, setLoading] = useState(true);

  const handleNavigateToApp = (tab = 'architecture') => {
    if (tab) setActiveTab(tab);
    setCurrentView('app');
    window.history.pushState({}, '', '/app');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateToLanding = () => {
    setCurrentView('landing');
    window.history.pushState({}, '', '/');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      const hash = window.location.hash;
      if (path === '/app' || hash === '#app') {
        setCurrentView('app');
      } else {
        setCurrentView('landing');
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [health, surplus, demand] = await Promise.all([
        getHealthStatus().catch(err => ({ status: 'standby', error: err.message })),
        getSurplusListings().catch(() => []),
        getDemandListings().catch(() => [])
      ]);
      setHealthStatus(health);
      setSurplusListings(surplus);
      setDemandListings(demand);
    } catch (err) {
      console.error('Error fetching ReSource data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentView === 'app') {
      fetchData();
    }
  }, [currentView]);

  const handleSurplusCreated = (newSurplus) => {
    setSurplusListings(prev => [newSurplus, ...prev]);
  };

  const handleDemandCreated = (newDemand) => {
    setDemandListings(prev => [newDemand, ...prev]);
  };

  if (currentView === 'landing') {
    return <LandingPage onEnterApp={(tab) => handleNavigateToApp(tab || 'architecture')} />;
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        healthStatus={healthStatus}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onGoToLanding={handleNavigateToLanding}
      />


      <main className="container" style={{ flex: 1 }}>
        <SimulatedBanner />

        {activeTab === 'architecture' && (
          <div>
            <div style={{ marginBottom: '2.5rem', textAlign: 'center' }}>
              <h1 style={{ fontSize: '2.25rem', marginBottom: '0.75rem' }}>Predictive Circular Resource Intelligence</h1>
              <p style={{ color: 'var(--text-muted)', maxWidth: '680px', margin: '0 auto', fontSize: '1rem', lineHeight: 1.6 }}>
                ReSource connects commercial surplus food providers with verified community partners to reduce waste, anticipate shortages, and optimize distribution.
              </p>
            </div>

            {/* Conceptual Circular Workflow Banner */}
            <div className="glass-card" style={{ padding: '1.75rem', marginBottom: '2.5rem' }}>
              <h3 style={{ fontSize: '1rem', color: 'var(--text-dim)', marginBottom: '1.25rem', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '1px' }}>
                End-to-End Circular Workflow
              </h3>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                gap: '12px',
                alignItems: 'center',
                textAlign: 'center'
              }}>
                <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(15, 23, 42, 0.6)' }}>
                  <Package style={{ color: 'var(--primary-emerald)', margin: '0 auto 6px' }} size={22} />
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Resources Available</div>
                </div>

                <div style={{ color: 'var(--text-dim)', fontSize: '1.2rem', display: 'flex', justifyContent: 'center' }}>
                  <ArrowRight size={18} />
                </div>

                <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(15, 23, 42, 0.6)' }}>
                  <Sparkles style={{ color: 'var(--accent-purple)', margin: '0 auto 6px' }} size={22} />
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Smart Understanding</div>
                </div>

                <div style={{ color: 'var(--text-dim)', fontSize: '1.2rem', display: 'flex', justifyContent: 'center' }}>
                  <ArrowRight size={18} />
                </div>

                <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(15, 23, 42, 0.6)' }}>
                  <TrendingUp style={{ color: 'var(--accent-amber)', margin: '0 auto 6px' }} size={22} />
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Future Forecast</div>
                </div>

                <div style={{ color: 'var(--text-dim)', fontSize: '1.2rem', display: 'flex', justifyContent: 'center' }}>
                  <ArrowRight size={18} />
                </div>

                <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(15, 23, 42, 0.6)' }}>
                  <Target style={{ color: 'var(--accent-cyan)', margin: '0 auto 6px' }} size={22} />
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Smart Matching</div>
                </div>

                <div style={{ color: 'var(--text-dim)', fontSize: '1.2rem', display: 'flex', justifyContent: 'center' }}>
                  <ArrowRight size={18} />
                </div>

                <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(15, 23, 42, 0.6)' }}>
                  <Route style={{ color: 'var(--primary-emerald)', margin: '0 auto 6px' }} size={22} />
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Best Allocation</div>
                </div>

                <div style={{ color: 'var(--text-dim)', fontSize: '1.2rem', display: 'flex', justifyContent: 'center' }}>
                  <ArrowRight size={18} />
                </div>

                <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(15, 23, 42, 0.6)' }}>
                  <Leaf style={{ color: '#34d399', margin: '0 auto 6px' }} size={22} />
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Measurable Impact</div>
                </div>
              </div>
            </div>

            {/* Core Capability Cards Grid */}
            <div className="grid-3" style={{ marginBottom: '2rem' }}>
              <div className="glass-card" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1rem' }}>
                  <Sparkles style={{ color: 'var(--accent-purple)' }} size={24} />
                  <h3 style={{ fontSize: '1.1rem' }}>Smart Resource Entry</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.5 }}>
                  Turn plain text notes into structured resource listings automatically recognizing quantities, storage, and deadlines.
                </p>
                <div style={{ fontSize: '0.8rem', color: 'var(--primary-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={14} /> Active & Ready
                </div>
              </div>

              <div className="glass-card" style={{ padding: '1.5rem', cursor: 'pointer' }} onClick={() => setActiveTab('prediction')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1rem' }}>
                  <TrendingUp style={{ color: 'var(--accent-amber)' }} size={24} />
                  <h3 style={{ fontSize: '1.1rem' }}>Future Supply & Demand</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.5 }}>
                  Forecast upcoming surplus patterns and community meal demands based on day-of-week and event cycles.
                </p>
                <div style={{ fontSize: '0.8rem', color: 'var(--accent-amber)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={14} /> Active & Ready (Click to Open)
                </div>
              </div>

              <div className="glass-card" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1rem' }}>
                  <Target style={{ color: 'var(--accent-cyan)' }} size={24} />
                  <h3 style={{ fontSize: '1.1rem' }}>Smart Matches</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.5 }}>
                  Instantly evaluate compatibility scores between available surplus and open community requests based on proximity and urgency.
                </p>
                <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>
                  Compatibility Engine Ready
                </div>
              </div>

              <div className="glass-card" style={{ padding: '1.5rem', cursor: 'pointer' }} onClick={() => setActiveTab('optimization')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1rem' }}>
                  <Route style={{ color: 'var(--primary-emerald)' }} size={24} />
                  <h3 style={{ fontSize: '1.1rem' }}>Best Allocation</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.5 }}>
                  Calculate optimal multi-point distribution plans respecting transit distance, expiry limits, and shelter storage capacities.
                </p>
                <div style={{ fontSize: '0.8rem', color: 'var(--primary-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={14} /> Active & Ready (Click to Open)
                </div>
              </div>


              <div className="glass-card" style={{ padding: '1.5rem', cursor: 'pointer' }} onClick={() => setActiveTab('impact')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1rem' }}>
                  <Leaf style={{ color: '#34d399' }} size={24} />
                  <h3 style={{ fontSize: '1.1rem' }}>Sustainability Impact</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.5 }}>
                  Measure food rescued in kilograms, meal equivalents served, and environmental savings created.
                </p>
                <div style={{ fontSize: '0.8rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={14} /> Active & Ready (Click to Open)
                </div>
              </div>

              <div className="glass-card" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1rem' }}>
                  <Users style={{ color: 'var(--accent-cyan)' }} size={24} />
                  <h3 style={{ fontSize: '1.1rem' }}>Partners & Community</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.5 }}>
                  Connect verified resource providers (hotels, restaurants) with verified community partners (shelters, food banks).
                </p>
                <div style={{ fontSize: '0.8rem', color: 'var(--primary-emerald)' }}>
                  Verified Network Active
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'surplus' && (
          <div>
            <div style={{ marginBottom: '2rem' }}>
              <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Available Resources (Resource Providers)</h1>
              <p style={{ color: 'var(--text-muted)' }}>
                Add new surplus listings using natural language or explore active resources available for redistribution.
              </p>
            </div>

            {/* Interactive Supplier Intake Form */}
            <SurplusIntakeForm onListingCreated={handleSurplusCreated} />

            <h2 style={{ fontSize: '1.3rem', marginBottom: '1rem' }}>Active Available Resources ({surplusListings.length})</h2>

            <div className="grid-2">
              {surplusListings.length > 0 ? (
                surplusListings.map(item => (
                  <div key={item.id} className="glass-card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                      <div>
                        <h3 style={{ fontSize: '1.15rem', color: '#fff', marginBottom: '4px' }}>{item.title}</h3>
                        <span className="badge badge-simulated">{item.is_simulated ? 'Sample Listing' : 'Live Submission'}</span>
                      </div>
                      <span className="badge badge-available">{item.status}</span>
                    </div>

                    <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem', fontStyle: 'italic' }}>
                      "{item.raw_nlp_text}"
                    </p>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.85rem' }}>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Quantity: </span>
                        <strong style={{ color: 'var(--primary-emerald)' }}>{item.quantity} {item.unit}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Storage Needed: </span>
                        <strong>{item.storage_condition}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Shelf-Life: </span>
                        <strong>{item.perishability_hours} hrs</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Available Until: </span>
                        <strong style={{ color: '#f59e0b' }}>
                          {new Date(item.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </strong>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', gridColumn: '1 / -1' }}>
                  <Package size={32} style={{ color: 'var(--text-dim)', marginBottom: '1rem' }} />
                  <p style={{ color: 'var(--text-muted)' }}>No resources found. Use the intake form above to add an available resource.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'demand' && (
          <div>
            <div style={{ marginBottom: '2rem' }}>
              <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Resource Needs (Community Partners)</h1>
              <p style={{ color: 'var(--text-muted)' }}>
                Submit resource requests or view current food needs from verified community shelters and food banks.
              </p>
            </div>

            {/* Interactive Receiver Intake Form */}
            <DemandIntakeForm onListingCreated={handleDemandCreated} />

            <h2 style={{ fontSize: '1.3rem', marginBottom: '1rem' }}>Active Resource Needs ({demandListings.length})</h2>

            <div className="grid-2">
              {demandListings.length > 0 ? (
                demandListings.map(item => (
                  <div key={item.id} className="glass-card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                      <div>
                        <h3 style={{ fontSize: '1.15rem', color: '#fff', marginBottom: '4px' }}>{item.title}</h3>
                        <span className="badge badge-simulated">{item.is_simulated ? 'Sample Need' : 'Live Request'}</span>
                      </div>
                      <span className="badge badge-urgent">{item.urgency_level} URGENCY</span>
                    </div>

                    <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem', fontStyle: 'italic' }}>
                      "{item.raw_nlp_text}"
                    </p>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.85rem' }}>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Requested: </span>
                        <strong style={{ color: 'var(--accent-cyan)' }}>{item.requested_quantity} {item.unit}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Fulfilled: </span>
                        <strong>{item.fulfilled_quantity} {item.unit}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Required By: </span>
                        <strong style={{ color: '#f59e0b' }}>
                          {new Date(item.required_by).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Storage Available: </span>
                        <strong>{item.storage_capacity}</strong>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', gridColumn: '1 / -1' }}>
                  <Package size={32} style={{ color: 'var(--text-dim)', marginBottom: '1rem' }} />
                  <p style={{ color: 'var(--text-muted)' }}>No resource needs found. Use the intake form above to submit a request.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'prediction' && (
          <PredictionDashboard />
        )}

        {activeTab === 'matches' && (
          <MatchExplorer />
        )}

        {activeTab === 'optimization' && (
          <OptimizationDashboard />
        )}

        {activeTab === 'impact' && (
          <ImpactDashboard />
        )}
      </main>


      <footer style={{
        textAlign: 'center',
        padding: '1.5rem',
        borderTop: '1px solid var(--border-color)',
        color: 'var(--text-dim)',
        fontSize: '0.8rem'
      }}>
        ReSource Network — Predict. Match. Redistribute. Sustain. Built for Software-Only Circular Resource Intelligence.
      </footer>
    </div>
  );
}

export default App;
