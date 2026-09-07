import React, { useState, useEffect } from 'react';
import {
  Play,
  RefreshCw,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ArrowRight,
  Building2,
  Package,
  Heart,
  Info,
  TrendingUp,
  Clock,
  ShieldCheck,
  MapPin,
  Target
} from 'lucide-react';
import { runOptimization, getOptimizationSummary } from '../../services/api';
import { OptimizationMap } from '../map/OptimizationMap';


export const OptimizationDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [result, setResult] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState(null);

  // Fetch initial summary metrics on mount
  const fetchSummary = async () => {
    try {
      setLoadingSummary(true);
      setError(null);
      const data = await getOptimizationSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to fetch optimization summary:', err);
      setError('Unable to retrieve current optimization summary. Please verify backend connection.');
    } finally {
      setLoadingSummary(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  // Handle Run Optimization action
  const handleRunOptimization = async () => {
    if (optimizing) return; // Prevent duplicate concurrent executions

    try {
      setOptimizing(true);
      setError(null);
      const data = await runOptimization();
      setResult(data);
      setSummary({
        status: data.status,
        total_supply_available: data.total_supply_available,
        total_demand_requested: data.total_demand_requested,
        total_allocated: data.total_allocated,
        total_unallocated: data.total_unallocated,
        total_unmet_demand: data.total_unmet_demand,
        num_allocations: data.num_allocations,
        num_demands_fully_satisfied: data.num_demands_fully_satisfied,
        num_demands_partially_satisfied: data.num_demands_partially_satisfied,
        num_demands_unsatisfied: data.num_demands_unsatisfied,
        objective_value: data.objective_value,
        solver_wall_time_ms: data.solver_wall_time_ms,
        message: data.message,
      });
    } catch (err) {
      console.error('Error running allocation optimization:', err);
      setError('Optimization could not be completed. Please ensure valid surplus and demand data are available.');
    } finally {
      setOptimizing(false);
    }
  };

  // Status badge style helper
  const getStatusBadge = (status) => {
    switch (status) {
      case 'OPTIMAL':
        return {
          label: 'OPTIMAL SOLUTION',
          className: 'badge-available',
          icon: <CheckCircle2 size={14} />,
          desc: 'Global mathematical optimum reached by OR-Tools LP Solver',
        };
      case 'FEASIBLE':
        return {
          label: 'FEASIBLE SOLUTION',
          className: 'badge-simulated',
          icon: <Zap size={14} />,
          desc: 'Feasible allocation found within solver time limits',
        };
      case 'NO_DATA':
        return {
          label: 'NO ELIGIBLE DATA',
          className: 'badge-simulated',
          icon: <Info size={14} />,
          desc: 'No active surplus, open demand, or viable matches exist',
        };
      case 'INFEASIBLE':
        return {
          label: 'INFEASIBLE SPEC',
          className: 'badge-urgent',
          icon: <AlertTriangle size={14} />,
          desc: 'Constraints could not be satisfied simultaneously',
        };
      case 'UNAVAILABLE':
        return {
          label: 'SOLVER UNAVAILABLE',
          className: 'badge-urgent',
          icon: <AlertTriangle size={14} />,
          desc: 'OR-Tools optimizer library is not available on backend',
        };
      default:
        return {
          label: status || 'UNKNOWN',
          className: 'badge-simulated',
          icon: <Info size={14} />,
          desc: '',
        };
    }
  };

  const activeStatus = result?.status || summary?.status || 'IDLE';
  const statusBadge = getStatusBadge(activeStatus);
  const allocations = result?.allocations || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Dashboard Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
            <h1 style={{ fontSize: '2.25rem' }}>Multi-Point Allocation Optimization</h1>
            <span className={`badge ${statusBadge.className}`}>
              {statusBadge.icon} {statusBadge.label}
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem', maxWidth: '720px' }}>
            Global linear program solver determining optimal multi-supplier to multi-receiver resource redistribution while maximizing total food rescued and match quality.
          </p>
        </div>

        {/* Action Button */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            onClick={fetchSummary}
            disabled={loadingSummary || optimizing}
            className="glass-card"
            style={{
              padding: '10px 16px',
              color: 'var(--text-main)',
              cursor: (loadingSummary || optimizing) ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.9rem',
            }}
          >
            <RefreshCw size={16} className={loadingSummary ? 'spin' : ''} />
            Refresh Stats
          </button>

          <button
            onClick={handleRunOptimization}
            disabled={optimizing}
            className="btn-primary"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '1rem',
              padding: '12px 24px',
              cursor: optimizing ? 'not-allowed' : 'pointer',
              opacity: optimizing ? 0.75 : 1,
            }}
          >
            {optimizing ? (
              <>
                <RefreshCw size={18} style={{ animation: 'spin 1s linear infinite' }} />
                Optimizing Resource Allocation...
              </>
            ) : (
              <>
                <Play size={18} fill="currentColor" />
                Run Optimization
              </>
            )}
          </button>
        </div>
      </div>

      {/* Conceptual Allocation Pipeline Header Banner */}
      <div className="glass-card" style={{ padding: '1.25rem 1.75rem' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          fontSize: '0.85rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary-emerald)', fontWeight: 600 }}>
            <Package size={18} />
            <span>Available Surplus</span>
          </div>

          <ArrowRight size={16} style={{ color: 'var(--text-dim)' }} />

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-cyan)', fontWeight: 600 }}>
            <Target size={18} />
            <span>Smart Compatibility</span>
          </div>

          <ArrowRight size={16} style={{ color: 'var(--text-dim)' }} />

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-purple)', fontWeight: 600 }}>
            <Zap size={18} />
            <span>OR-Tools LP Solver</span>
          </div>

          <ArrowRight size={16} style={{ color: 'var(--text-dim)' }} />

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-amber)', fontWeight: 600 }}>
            <CheckCircle2 size={18} />
            <span>Global Best Allocation</span>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="glass-card" style={{ padding: '1.25rem', borderColor: 'rgba(239, 68, 68, 0.4)', background: 'rgba(239, 68, 68, 0.1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#f87171' }}>
            <AlertTriangle size={20} />
            <strong style={{ fontSize: '0.95rem' }}>Optimization Alert</strong>
          </div>
          <p style={{ marginTop: '6px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>{error}</p>
        </div>
      )}

      {/* Summary Cards Section */}
      <div>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={20} style={{ color: 'var(--primary-emerald)' }} />
          Optimization Summary Overview
        </h2>

        {loadingSummary && !summary ? (
          <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
            <p>Loading optimization summary...</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            {/* Supply Available */}
            <div className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Total Available Supply
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--primary-emerald)' }}>
                {(summary?.total_supply_available || 0).toLocaleString()} <span style={{ fontSize: '1rem', fontWeight: 500 }}>kg</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Surplus listings eligible
              </div>
            </div>

            {/* Total Demand */}
            <div className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Total Community Demand
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                {(summary?.total_demand_requested || 0).toLocaleString()} <span style={{ fontSize: '1rem', fontWeight: 500 }}>kg</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Active open requirements
              </div>
            </div>

            {/* Total Allocated */}
            <div className="glass-card" style={{ padding: '1.25rem', borderLeft: '3px solid var(--primary-emerald)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Total Food Allocated
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#fff' }}>
                {(summary?.total_allocated || 0).toLocaleString()} <span style={{ fontSize: '1rem', fontWeight: 500 }}>kg</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--primary-emerald)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={12} /> Maximized global redistribution
              </div>
            </div>

            {/* Unallocated Surplus */}
            <div className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Unallocated Surplus
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: (summary?.total_unallocated || 0) > 0 ? 'var(--accent-amber)' : 'var(--text-muted)' }}>
                {(summary?.total_unallocated || 0).toLocaleString()} <span style={{ fontSize: '1rem', fontWeight: 500 }}>kg</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Remaining unassigned surplus
              </div>
            </div>

            {/* Unmet Demand */}
            <div className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Unmet Demand
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: (summary?.total_unmet_demand || 0) > 0 ? '#f87171' : 'var(--text-muted)' }}>
                {(summary?.total_unmet_demand || 0).toLocaleString()} <span style={{ fontSize: '1rem', fontWeight: 500 }}>kg</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Outstanding shelter requirements
              </div>
            </div>

            {/* Demands Fully Satisfied */}
            <div className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Fully Satisfied Demands
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--primary-emerald)' }}>
                {summary?.num_demands_fully_satisfied || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                100% fulfilled requirements
              </div>
            </div>

            {/* Demands Partially Satisfied */}
            <div className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Partially Satisfied
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent-amber)' }}>
                {summary?.num_demands_partially_satisfied || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Partial quantity assigned
              </div>
            </div>

            {/* Demands Unsatisfied */}
            <div className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Unsatisfied Needs
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-dim)' }}>
                {summary?.num_demands_unsatisfied || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                No compatible surplus match
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Geographic Allocation Map */}
      <OptimizationMap allocations={allocations} />

      {/* Allocation Results Section */}

      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.3rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={20} style={{ color: 'var(--accent-cyan)' }} />
            Optimized Multi-Point Allocations ({allocations.length})
          </h2>

          {result?.solver_wall_time_ms !== undefined && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={14} /> Solved in {result.solver_wall_time_ms.toFixed(1)} ms
            </span>
          )}
        </div>

        {optimizing ? (
          <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
            <RefreshCw size={36} style={{ color: 'var(--primary-emerald)', animation: 'spin 1s linear infinite', marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Optimizing Resource Allocation...</h3>
            <p style={{ color: 'var(--text-muted)', maxWidth: '450px', margin: '0 auto', fontSize: '0.9rem' }}>
              Evaluating multi-supplier supply, shelter needs, compatibility criteria, and distance factors via Google OR-Tools.
            </p>
          </div>
        ) : activeStatus === 'NO_DATA' ? (
          <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
            <Info size={40} style={{ color: 'var(--accent-amber)', marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>No Eligible Data Currently Available</h3>
            <p style={{ color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto', fontSize: '0.9rem', lineHeight: 1.5 }}>
              No eligible surplus listings or open community demands were found, or no pairs satisfied Phase 3.3 compatibility rules.
              Add surplus resources or shelter needs to execute global optimization.
            </p>
          </div>
        ) : allocations.length === 0 ? (
          <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
            <Layers size={40} style={{ color: 'var(--text-dim)', marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>No Allocation Results Available Yet</h3>
            <p style={{ color: 'var(--text-muted)', maxWidth: '480px', margin: '0 auto', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Click the <strong>"Run Optimization"</strong> button above to calculate the optimal distribution plan across all suppliers and community partners.
            </p>
            <button onClick={handleRunOptimization} className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
              <Play size={16} fill="currentColor" /> Run Optimization Now
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {allocations.map((alloc, idx) => (
              <div key={`${alloc.surplus_id}-${alloc.demand_id}-${idx}`} className="glass-card" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      display: 'inline-flex',
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      backgroundColor: 'rgba(16, 185, 129, 0.15)',
                      color: 'var(--primary-emerald)',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '0.85rem'
                    }}>
                      #{idx + 1}
                    </span>

                    <div>
                      <h4 style={{ fontSize: '1.1rem', color: '#fff', margin: 0 }}>
                        {alloc.surplus_title || 'Surplus Listing'} → {alloc.demand_title || 'Demand Listing'}
                      </h4>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: '12px', marginTop: '2px' }}>
                        {alloc.category_name && <span>Category: <strong style={{ color: 'var(--text-main)' }}>{alloc.category_name}</strong></span>}
                        {alloc.distance_km !== null && alloc.distance_km !== undefined && (
                          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <MapPin size={12} style={{ color: 'var(--accent-cyan)' }} /> {alloc.distance_km.toFixed(1)} km
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`badge ${alloc.status === 'ALLOCATED' ? 'badge-available' : 'badge-simulated'}`}>
                      {alloc.status === 'ALLOCATED' ? 'FULLY ALLOCATED' : 'PARTIALLY ALLOCATED'}
                    </span>
                    <span className="badge" style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#22d3ee', border: '1px solid rgba(6, 182, 212, 0.3)' }}>
                      Match {Math.round(alloc.match_score)}%
                    </span>
                  </div>
                </div>

                {/* Allocation Transfer Flow Diagram */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '12px',
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  padding: '1rem 1.25rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  alignItems: 'center'
                }}>
                  {/* Supplier Box */}
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Building2 size={12} /> Provider (Supplier)
                    </div>
                    <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.95rem' }}>
                      {alloc.supplier_name || 'Resource Supplier'}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {alloc.surplus_title}
                    </div>
                  </div>

                  {/* Quantity Arrow Box */}
                  <div style={{ textAlign: 'center', padding: '0.5rem', borderLeft: '1px solid rgba(255, 255, 255, 0.08)', borderRight: '1px solid rgba(255, 255, 255, 0.08)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '2px' }}>
                      Allocated Amount
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-emerald)' }}>
                      {alloc.allocated_quantity} {alloc.surplus_unit || 'kg'}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '2px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                      <ArrowRight size={12} /> Global Optimum
                    </div>
                  </div>

                  {/* Receiver Box */}
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Heart size={12} style={{ color: 'var(--accent-cyan)' }} /> Partner (Receiver)
                    </div>
                    <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.95rem' }}>
                      {alloc.receiver_name || 'Community Receiver'}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {alloc.demand_title}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Explanatory Card: How ReSource Optimizes */}
      <div className="glass-card" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
          <Info size={22} style={{ color: 'var(--accent-cyan)' }} />
          <h3 style={{ fontSize: '1.15rem' }}>How ReSource Optimizes</h3>
        </div>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: 1.6, marginBottom: '1.25rem' }}>
          ReSource evaluates compatible resources and community needs, then uses global optimization to determine how available resources can be distributed while respecting supply, demand, compatibility, expiry, match quality, and distance constraints.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', fontSize: '0.85rem' }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ fontWeight: 600, color: '#fff', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ShieldCheck size={16} style={{ color: 'var(--primary-emerald)' }} /> Pre-Screened Viability
            </div>
            <div style={{ color: 'var(--text-muted)' }}>
              Only surplus and demand listings passing Phase 3.3 compatibility (category, storage, shelf-life) enter the optimization model.
            </div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ fontWeight: 600, color: '#fff', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Zap size={16} style={{ color: 'var(--accent-purple)' }} /> Multi-Point LP Solver
            </div>
            <div style={{ color: 'var(--text-muted)' }}>
              Google OR-Tools simultaneously solves distribution across all suppliers and shelters to maximize total food rescued.
            </div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ fontWeight: 600, color: '#fff', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Target size={16} style={{ color: 'var(--accent-cyan)' }} /> Quality & Proximity
            </div>
            <div style={{ color: 'var(--text-muted)' }}>
              Higher match scores receive allocation priority while travel distance penalty minimizes transit times and carbon footprint.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
