import React, { useState, useEffect, useCallback } from 'react';
import {
  Target, Package, Heart, MapPin, Clock, AlertTriangle,
  ChevronDown, ChevronUp, Zap, CheckCircle, XCircle,
  ArrowRight, Layers, RefreshCw, Info
} from 'lucide-react';
import {
  matchSurplusAgainstDemands,
  matchDemandAgainstSurplus,
  getSurplusListings,
  getDemandListings,
} from '../../services/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const scoreColor = (score) => {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#06b6d4';
  if (score >= 40) return '#f59e0b';
  return '#ef4444';
};

const scoreLabel = (score) => {
  if (score >= 85) return 'Excellent';
  if (score >= 70) return 'Good';
  if (score >= 50) return 'Fair';
  if (score >= 30) return 'Weak';
  return 'Poor';
};

const urgencyColor = (u) => {
  const m = { CRITICAL: '#ef4444', HIGH: '#f59e0b', MEDIUM: '#06b6d4', LOW: '#6b7280' };
  return m[(u || 'MEDIUM').toUpperCase()] || '#6b7280';
};

const formatDate = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleString([], {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Animated score ring */
const ScoreRing = ({ score, size = 72 }) => {
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;
  const color = scoreColor(score);
  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="rgba(255,255,255,0.07)" strokeWidth={6} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth={6}
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.6s cubic-bezier(0.4,0,0.2,1)' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0, display: 'flex',
        flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
      }}>
        <span style={{ fontSize: size > 64 ? '1.1rem' : '0.85rem', fontWeight: 700, color }}>{score}%</span>
      </div>
    </div>
  );
};

/** Horizontal factor score bar */
const FactorBar = ({ label, score, weight }) => {
  const color = scoreColor(score);
  return (
    <div style={{ marginBottom: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
        <span style={{ color: 'var(--text-muted)' }}>
          {label} <span style={{ color: 'var(--text-dim)', fontSize: '0.65rem' }}>×{weight}</span>
        </span>
        <span style={{ fontWeight: 600, color }}>{Math.round(score)}</span>
      </div>
      <div style={{ height: '5px', borderRadius: '99px', background: 'rgba(255,255,255,0.06)' }}>
        <div style={{
          height: '100%', borderRadius: '99px',
          width: `${score}%`, background: color,
          transition: 'width 0.5s cubic-bezier(0.4,0,0.2,1)'
        }} />
      </div>
    </div>
  );
};

/** Chip / pill badge */
const Chip = ({ icon: Icon, label, color = 'var(--text-muted)', bg = 'rgba(255,255,255,0.05)' }) => (
  <span style={{
    display: 'inline-flex', alignItems: 'center', gap: '4px',
    padding: '3px 9px', borderRadius: '99px',
    background: bg, fontSize: '0.72rem', color, fontWeight: 500,
    border: `1px solid ${color}33`
  }}>
    {Icon && <Icon size={11} />}
    {label}
  </span>
);

/** Individual match card */
const MatchCard = ({ match, mode }) => {
  const [expanded, setExpanded] = useState(false);
  const isViable = match.is_viable;
  const score = match.overall_score;
  const color = scoreColor(score);

  const partnerName = mode === 'surplus'
    ? (match.receiver_name || match.demand_id.slice(0, 8) + '…')
    : (match.supplier_name || match.surplus_id.slice(0, 8) + '…');

  const listingTitle = mode === 'surplus'
    ? (match.demand_title || 'Community Need')
    : (match.surplus_title || 'Available Resource');

  const FACTOR_LABELS = [
    ['category', 'Category', 25],
    ['quantity',  'Quantity', 20],
    ['distance',  'Distance', 20],
    ['time',      'Time',     20],
    ['urgency',   'Urgency',  10],
    ['storage',   'Storage',   5],
  ];

  return (
    <div className="glass-card" style={{
      padding: '1.25rem',
      borderColor: isViable ? `${color}33` : 'rgba(255,255,255,0.05)',
      opacity: isViable ? 1 : 0.55,
      transition: 'all 0.2s ease',
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
        <ScoreRing score={score} size={68} />

        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Rank + viability */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)',
              textTransform: 'uppercase', letterSpacing: '1px' }}>
              #{match.rank}
            </span>
            {isViable ? (
              <Chip icon={CheckCircle} label={scoreLabel(score)} color={color} bg={`${color}18`} />
            ) : (
              <Chip icon={XCircle} label="Disqualified" color="#ef4444" bg="rgba(239,68,68,0.12)" />
            )}
            {match.demand_urgency && isViable && (
              <Chip label={match.demand_urgency} color={urgencyColor(match.demand_urgency)}
                bg={`${urgencyColor(match.demand_urgency)}18`} />
            )}
          </div>

          {/* Partner & listing names */}
          <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#fff',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {partnerName}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {listingTitle}
          </div>

          {/* Quick meta chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '10px' }}>
            {match.distance_km != null && (
              <Chip icon={MapPin} label={`${match.distance_km.toFixed(1)} km`}
                color="var(--accent-cyan)" bg="rgba(6,182,212,0.1)" />
            )}
            {match.distance_km == null && (
              <Chip icon={MapPin} label="Location N/A" color="var(--text-dim)" />
            )}
            {mode === 'surplus' && match.demand_requested_quantity != null && (
              <Chip icon={Heart} label={`${match.demand_requested_quantity} ${match.demand_unit || 'kg'} needed`}
                color="var(--accent-purple)" bg="rgba(139,92,246,0.1)" />
            )}
            {mode === 'demand' && match.surplus_quantity != null && (
              <Chip icon={Package} label={`${match.surplus_quantity} ${match.surplus_unit || 'kg'} available`}
                color="var(--primary-emerald)" bg="rgba(16,185,129,0.1)" />
            )}
            {match.surplus_expires_at && (
              <Chip icon={Clock} label={`Expires ${formatDate(match.surplus_expires_at)}`}
                color="var(--accent-amber)" bg="rgba(245,158,11,0.1)" />
            )}
            {match.demand_required_by && (
              <Chip icon={Clock} label={`Needed by ${formatDate(match.demand_required_by)}`}
                color="var(--text-muted)" />
            )}
          </div>
        </div>
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(e => !e)}
        style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          marginTop: '14px', background: 'none', border: 'none',
          color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.75rem',
          padding: '0', transition: 'color 0.2s'
        }}
        onMouseEnter={e => e.currentTarget.style.color = '#fff'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-dim)'}
      >
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {expanded ? 'Hide' : 'Show'} score breakdown
      </button>

      {expanded && (
        <div style={{
          marginTop: '14px', paddingTop: '14px',
          borderTop: '1px solid rgba(255,255,255,0.06)',
          animation: 'fadeIn 0.2s ease'
        }}>
          {/* Factor bars */}
          <div style={{ marginBottom: '14px' }}>
            {FACTOR_LABELS.map(([key, label, weight]) => (
              <FactorBar key={key} label={label} score={match.factor_scores[key]} weight={weight} />
            ))}
          </div>

          {/* Reasons */}
          {match.reasons.length > 0 && (
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)',
                textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>
                {isViable ? 'Match Explanation' : 'Disqualification Reasons'}
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {match.reasons.slice(0, 6).map((r, i) => (
                  <li key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: '8px',
                    fontSize: '0.78rem', color: isViable ? 'var(--text-muted)' : '#f87171'
                  }}>
                    <span style={{ flexShrink: 0, marginTop: '2px' }}>
                      {isViable
                        ? <CheckCircle size={12} color={scoreColor(match.factor_scores[Object.keys(match.factor_scores)[i]] ?? 70)} />
                        : <AlertTriangle size={12} color="#ef4444" />
                      }
                    </span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main MatchExplorer component
// ---------------------------------------------------------------------------
export const MatchExplorer = () => {
  const [mode, setMode] = useState('surplus'); // 'surplus' | 'demand'
  const [surplusListings, setSurplusListings] = useState([]);
  const [demandListings, setDemandListings]   = useState([]);
  const [selectedId, setSelectedId]           = useState('');
  const [matchResult, setMatchResult]         = useState(null);
  const [loading, setLoading]                 = useState(false);
  const [loadingListings, setLoadingListings] = useState(true);
  const [error, setError]                     = useState(null);
  const [showDisqualified, setShowDisqualified] = useState(false);

  // Load listing options on mount + mode change
  useEffect(() => {
    setLoadingListings(true);
    setSelectedId('');
    setMatchResult(null);
    setError(null);
    Promise.all([getSurplusListings().catch(() => []), getDemandListings().catch(() => [])])
      .then(([s, d]) => { setSurplusListings(s); setDemandListings(d); })
      .finally(() => setLoadingListings(false));
  }, []);

  const listings = mode === 'surplus' ? surplusListings : demandListings;

  const runMatch = useCallback(async (id) => {
    if (!id) return;
    setLoading(true);
    setError(null);
    setMatchResult(null);
    try {
      const result = mode === 'surplus'
        ? await matchSurplusAgainstDemands(id, showDisqualified)
        : await matchDemandAgainstSurplus(id, showDisqualified);
      setMatchResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Matching failed');
    } finally {
      setLoading(false);
    }
  }, [mode, showDisqualified]);

  const handleSelect = (id) => {
    setSelectedId(id);
    runMatch(id);
  };

  const handleRefresh = () => { if (selectedId) runMatch(selectedId); };

  const viableMatches     = matchResult?.matches?.filter(m => m.is_viable) ?? [];
  const disqualifiedCount = (matchResult?.matches?.length ?? 0) - viableMatches.length;

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Target style={{ color: 'var(--accent-cyan)' }} size={28} />
          Match Explorer
        </h1>
        <p style={{ color: 'var(--text-muted)', maxWidth: '640px' }}>
          Evaluate compatibility between available resources and community needs using transparent,
          explainable scoring across 6 factors — category, quantity, distance, time, urgency, and storage.
        </p>
      </div>

      {/* Mode toggle */}
      <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'flex-end' }}>

          {/* Direction selector */}
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: '8px',
              textTransform: 'uppercase', letterSpacing: '1px' }}>
              Match Direction
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              {[
                { key: 'surplus', icon: Package, label: 'Resource → Partners' },
                { key: 'demand',  icon: Heart,   label: 'Need → Resources' },
              ].map(({ key, icon: Icon, label }) => (
                <button key={key}
                  onClick={() => { setMode(key); setSelectedId(''); setMatchResult(null); setError(null); }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '8px',
                    padding: '8px 16px', borderRadius: '8px', cursor: 'pointer',
                    fontSize: '0.85rem', fontWeight: 500, transition: 'all 0.2s',
                    background: mode === key ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${mode === key ? 'var(--primary-emerald)' : 'rgba(255,255,255,0.08)'}`,
                    color: mode === key ? 'var(--primary-emerald)' : 'var(--text-muted)',
                  }}>
                  <Icon size={15} /> {label}
                </button>
              ))}
            </div>
          </div>

          {/* Listing selector */}
          <div style={{ flex: 1, minWidth: '240px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: '8px',
              textTransform: 'uppercase', letterSpacing: '1px' }}>
              {mode === 'surplus' ? 'Select a Resource Listing' : 'Select a Community Need'}
            </div>
            {loadingListings ? (
              <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>Loading listings…</div>
            ) : listings.length === 0 ? (
              <div style={{ color: 'var(--accent-amber)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Info size={14} />
                No {mode === 'surplus' ? 'surplus' : 'demand'} listings found. Add one via the{' '}
                {mode === 'surplus' ? 'Available Resources' : 'Resource Needs'} tab.
              </div>
            ) : (
              <select
                id="match-listing-select"
                value={selectedId}
                onChange={e => handleSelect(e.target.value)}
                style={{
                  width: '100%', padding: '9px 12px', borderRadius: '8px',
                  background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)',
                  color: '#fff', fontSize: '0.875rem', cursor: 'pointer',
                }}>
                <option value="" style={{ color: '#000000', backgroundColor: '#ffffff' }}>— choose a listing —</option>
                {listings.map(l => (
                  <option key={l.id} value={l.id} style={{ color: '#000000', backgroundColor: '#ffffff' }}>
                    {l.title || l.id.slice(0, 12)}
                    {l.quantity ? ` — ${l.quantity} ${l.unit || 'kg'}` : ''}
                    {l.requested_quantity ? ` — ${l.requested_quantity} ${l.unit || 'kg'}` : ''}
                  </option>
                ))}
              </select>

            )}
          </div>

          {/* Controls */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px',
              fontSize: '0.78rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showDisqualified}
                onChange={e => setShowDisqualified(e.target.checked)}
                style={{ accentColor: 'var(--primary-emerald)' }}
              />
              Show disqualified
            </label>
            {selectedId && (
              <button id="match-refresh-btn" onClick={handleRefresh}
                title="Re-run matching"
                style={{
                  background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px', padding: '8px', cursor: 'pointer', color: 'var(--text-muted)',
                  display: 'flex', alignItems: 'center', transition: 'all 0.2s'
                }}>
                <RefreshCw size={15} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Summary stats */}
      {matchResult && !loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: '12px', marginBottom: '1.5rem' }}>
          {[
            { label: 'Candidates Evaluated', value: matchResult.total_candidates, color: 'var(--text-main)' },
            { label: 'Viable Matches',        value: matchResult.viable_count,     color: 'var(--primary-emerald)' },
            { label: 'Disqualified',          value: matchResult.total_candidates - matchResult.viable_count, color: '#f87171' },
            {
              label: 'Top Score',
              value: viableMatches.length > 0 ? `${viableMatches[0].overall_score}%` : '—',
              color: viableMatches.length > 0 ? scoreColor(viableMatches[0].overall_score) : 'var(--text-dim)'
            },
          ].map(({ label, value, color }) => (
            <div key={label} className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color }}>{value}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '4px',
                textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Scoring legend */}
      {!selectedId && !loading && (
        <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '0.9rem', color: 'var(--text-dim)', marginBottom: '1rem',
            textTransform: 'uppercase', letterSpacing: '1px' }}>
            How Matching Scores Are Calculated
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            {[
              { name: 'Category',  weight: 25, icon: Layers,       desc: 'Exact or related resource type', color: 'var(--accent-purple)' },
              { name: 'Quantity',  weight: 20, icon: Package,      desc: 'Surplus covers demand need',      color: 'var(--primary-emerald)' },
              { name: 'Distance',  weight: 20, icon: MapPin,       desc: 'Proximity via haversine km',      color: 'var(--accent-cyan)' },
              { name: 'Time',      weight: 20, icon: Clock,        desc: 'Expiry vs. required-by window',   color: 'var(--accent-amber)' },
              { name: 'Urgency',   weight: 10, icon: Zap,          desc: 'Demand priority level boost',     color: '#f87171' },
              { name: 'Storage',   weight:  5, icon: CheckCircle,  desc: 'Temperature/storage compatibility', color: '#a78bfa' },
            ].map(({ name, weight, icon: Icon, desc, color }) => (
              <div key={name} style={{
                display: 'flex', alignItems: 'flex-start', gap: '10px',
                padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.03)'
              }}>
                <Icon size={18} style={{ color, flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {name}
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)',
                      background: 'rgba(255,255,255,0.06)', padding: '1px 6px',
                      borderRadius: '99px' }}>×{weight}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.73rem', color: 'var(--text-dim)', marginTop: '3px' }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '14px', fontSize: '0.73rem', color: 'var(--text-dim)',
            padding: '8px 12px', borderRadius: '6px', background: 'rgba(255,255,255,0.03)',
            borderLeft: '3px solid rgba(16,185,129,0.4)' }}>
            <strong style={{ color: 'var(--primary-emerald)' }}>Hard disqualifiers</strong>{' '}
            (score forced to 0): expired surplus · fully-fulfilled demand ·
            incompatible storage (e.g. FROZEN → AMBIENT) · category mismatch
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '50%', margin: '0 auto 1rem',
            border: '3px solid rgba(255,255,255,0.1)',
            borderTopColor: 'var(--primary-emerald)',
            animation: 'spin 0.8s linear infinite'
          }} />
          <p style={{ color: 'var(--text-muted)' }}>Running compatibility analysis…</p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="glass-card" style={{
          padding: '1.5rem', borderColor: 'rgba(239,68,68,0.3)',
          background: 'rgba(239,68,68,0.06)', textAlign: 'center'
        }}>
          <AlertTriangle size={24} style={{ color: '#ef4444', marginBottom: '8px' }} />
          <p style={{ color: '#f87171', fontSize: '0.9rem' }}>{error}</p>
        </div>
      )}

      {/* Match cards */}
      {matchResult && !loading && !error && (
        <>
          {/* Direction label */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.1rem' }}>
              {mode === 'surplus' ? 'Recommended Community Partners' : 'Matching Available Resources'}
            </h2>
            <ArrowRight size={16} style={{ color: 'var(--text-dim)' }} />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              Ranked by compatibility score (highest first)
            </span>
          </div>

          {matchResult.matches.length === 0 ? (
            <div className="glass-card" style={{ padding: '2.5rem', textAlign: 'center' }}>
              <Target size={32} style={{ color: 'var(--text-dim)', marginBottom: '1rem' }} />
              <p style={{ color: 'var(--text-muted)' }}>
                No {mode === 'surplus' ? 'demand' : 'surplus'} listings available to match against.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* Viable matches */}
              {viableMatches.map(m => (
                <MatchCard key={m.demand_id + m.surplus_id} match={m} mode={mode} />
              ))}

              {/* Divider for disqualified */}
              {showDisqualified && disqualifiedCount > 0 && (
                <>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: '12px',
                    padding: '8px 0', color: 'var(--text-dim)', fontSize: '0.78rem'
                  }}>
                    <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.06)' }} />
                    <XCircle size={14} color="#ef4444" />
                    <span>{disqualifiedCount} Disqualified (shown for transparency)</span>
                    <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.06)' }} />
                  </div>
                  {matchResult.matches.filter(m => !m.is_viable).map(m => (
                    <MatchCard key={m.demand_id + m.surplus_id} match={m} mode={mode} />
                  ))}
                </>
              )}
            </div>
          )}
        </>
      )}

      {/* Keyframes injection */}
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
};

export default MatchExplorer;
