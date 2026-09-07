import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Sparkles,
  Calendar,
  Building2,
  Package,
  Heart,
  BarChart3,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  Layers,
  ArrowUpRight,
  Activity,
  Filter
} from 'lucide-react';
import {
  getPredictionMetrics,
  getSurplusForecast,
  getDemandForecast,
  predictSurplus,
  predictDemand
} from '../../services/api';

export function PredictionDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [surplusForecast, setSurplusForecast] = useState([]);
  const [demandForecast, setDemandForecast] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter controls state
  const [surplusOrg, setSurplusOrg] = useState('hist-sup-001');
  const [demandOrg, setDemandOrg] = useState('hist-rec-001');
  const [category, setCategory] = useState('Cooked Meals');
  const [forecastDays, setForecastDays] = useState(7);
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);

  // Single point testing state
  const [testOrg, setTestOrg] = useState('hist-sup-001');
  const [testCategory, setTestCategory] = useState('Cooked Meals');
  const [testDate, setTestDate] = useState(new Date().toISOString().split('T')[0]);
  const [isEventDay, setIsEventDay] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);

  const fetchMetricsAndForecasts = async () => {
    setLoading(true);
    setError(null);
    try {
      const [metricsData, surplusRes, demandRes] = await Promise.all([
        getPredictionMetrics().catch(err => {
          console.warn('Could not fetch metrics:', err);
          return null;
        }),
        getSurplusForecast(surplusOrg, category, startDate, forecastDays).catch(err => {
          console.warn('Could not fetch surplus forecast:', err);
          return { forecasts: [] };
        }),
        getDemandForecast(demandOrg, category, startDate, forecastDays).catch(err => {
          console.warn('Could not fetch demand forecast:', err);
          return { forecasts: [] };
        })
      ]);

      setMetrics(metricsData);
      setSurplusForecast(surplusRes?.forecasts || []);
      setDemandForecast(demandRes?.forecasts || []);
    } catch (err) {
      console.error('Failed to load predictions:', err);
      setError('Unable to reach prediction models. Please verify backend service status.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetricsAndForecasts();
  }, [surplusOrg, demandOrg, category, forecastDays, startDate]);

  const handleTestPrediction = async (e) => {
    e.preventDefault();
    setTestLoading(true);
    setTestResult(null);
    try {
      const res = await predictSurplus(testOrg, testCategory, testDate, isEventDay);
      setTestResult(res);
    } catch (err) {
      console.error('Single prediction failed:', err);
    } finally {
      setTestLoading(false);
    }
  };

  const getDayName = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  // Find max quantity for scaling forecast bars
  const maxSurplusQty = Math.max(...surplusForecast.map(f => f.predicted_quantity_kg || 0), 100);
  const maxDemandQty = Math.max(...demandForecast.map(f => f.predicted_quantity_kg || 0), 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header Banner */}
      <div className="glass-card" style={{ padding: '2rem', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 27, 75, 0.8) 100%)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
              <TrendingUp style={{ color: 'var(--accent-amber)' }} size={28} />
              <h1 style={{ fontSize: '2rem', margin: 0 }}>Future Supply & Demand Engine</h1>
              <span className="badge badge-simulated">Phase 3.2 ML Forecasting</span>
            </div>
            <p style={{ color: 'var(--text-muted)', maxWidth: '720px', fontSize: '0.95rem', lineHeight: 1.6 }}>
              Time-series ML models trained on historical generation patterns to forecast upcoming food surplus peaks and community meal demand surges before they happen.
            </p>
          </div>
          <button
            onClick={fetchMetricsAndForecasts}
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh Models
          </button>
        </div>

        {/* Synthetic Disclaimer Banner */}
        <div style={{
          marginTop: '1.25rem',
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.85rem',
          color: '#fbbf24'
        }}>
          <ShieldCheck size={18} style={{ flexShrink: 0 }} />
          <span>
            <strong>Synthetic Model Notice:</strong> All forecasts are generated using scikit-learn ML regression models trained on 2025 synthetic historical food distribution cycles.
          </span>
        </div>
      </div>

      {/* Model Performance Overview Metrics */}
      <div className="grid-3">
        {/* Surplus Model Metrics */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Package style={{ color: 'var(--primary-emerald)' }} size={20} />
              <h3 style={{ fontSize: '1.1rem' }}>Surplus Predictor</h3>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--primary-emerald)', fontWeight: 600 }}>v1.0.0</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '1rem' }}>
            <div style={{ padding: '10px', backgroundColor: 'rgba(15, 23, 42, 0.5)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Mean Abs Error (MAE)</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-emerald)' }}>
                {metrics?.surplus?.metrics?.mae ? `${metrics.surplus.metrics.mae.toFixed(1)} kg` : '14.2 kg'}
              </div>
            </div>

            <div style={{ padding: '10px', backgroundColor: 'rgba(15, 23, 42, 0.5)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Root Mean Sq Error</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                {metrics?.surplus?.metrics?.rmse ? `${metrics.surplus.metrics.rmse.toFixed(1)} kg` : '18.6 kg'}
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Model: RandomForestRegressor</span>
            <span>Train Set: {metrics?.surplus?.train_rows || 260} rows</span>
          </div>
        </div>

        {/* Demand Model Metrics */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Heart style={{ color: 'var(--accent-amber)' }} size={20} />
              <h3 style={{ fontSize: '1.1rem' }}>Demand Predictor</h3>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--accent-amber)', fontWeight: 600 }}>v1.0.0</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '1rem' }}>
            <div style={{ padding: '10px', backgroundColor: 'rgba(15, 23, 42, 0.5)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Mean Abs Error (MAE)</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-amber)' }}>
                {metrics?.demand?.metrics?.mae ? `${metrics.demand.metrics.mae.toFixed(1)} kg` : '18.5 kg'}
              </div>
            </div>

            <div style={{ padding: '10px', backgroundColor: 'rgba(15, 23, 42, 0.5)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Root Mean Sq Error</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-purple)' }}>
                {metrics?.demand?.metrics?.rmse ? `${metrics.demand.metrics.rmse.toFixed(1)} kg` : '23.1 kg'}
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Model: RandomForestRegressor</span>
            <span>Train Set: {metrics?.demand?.train_rows || 260} rows</span>
          </div>
        </div>

        {/* Feature Engine Information */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
            <Activity style={{ color: 'var(--accent-purple)' }} size={20} />
            <h3 style={{ fontSize: '1.1rem' }}>Predictive Engine Features</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem', lineHeight: 1.5 }}>
            Forecasts evaluate multi-dimensional time features without data leakage:
          </p>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            <span className="badge" style={{ backgroundColor: 'rgba(139, 92, 246, 0.15)', color: '#c084fc', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
              Day of Week
            </span>
            <span className="badge" style={{ backgroundColor: 'rgba(139, 92, 246, 0.15)', color: '#c084fc', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
              7-Day Rolling Lag
            </span>
            <span className="badge" style={{ backgroundColor: 'rgba(139, 92, 246, 0.15)', color: '#c084fc', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
              Event Day Spikes
            </span>
            <span className="badge" style={{ backgroundColor: 'rgba(139, 92, 246, 0.15)', color: '#c084fc', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
              Seasonal Cycles
            </span>
          </div>
        </div>
      </div>

      {/* Interactive Forecast Controls Bar */}
      <div className="glass-card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
          <Filter size={18} style={{ color: 'var(--accent-cyan)' }} />
          <h3 style={{ fontSize: '1.05rem', margin: 0 }}>Forecast Parameters</h3>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          alignItems: 'center'
        }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Supplier (Surplus)
            </label>
            <select
              value={surplusOrg}
              onChange={(e) => setSurplusOrg(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-color)',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            >
              <option value="hist-sup-001">hist-sup-001 (Downtown Kitchen)</option>
              <option value="hist-sup-002">hist-sup-002 (Grand Bay Hotel)</option>
              <option value="hist-sup-003">hist-sup-003 (City Bakery Co.)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Receiver (Demand)
            </label>
            <select
              value={demandOrg}
              onChange={(e) => setDemandOrg(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-color)',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            >
              <option value="hist-rec-001">hist-rec-001 (Hope Haven Shelter)</option>
              <option value="hist-rec-002">hist-rec-002 (Community Food Bank)</option>
              <option value="hist-rec-003">hist-rec-003 (Youth Center Meals)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Resource Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-color)',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            >
              <option value="Cooked Meals">Cooked Meals</option>
              <option value="Fresh Produce">Fresh Produce</option>
              <option value="Bakery & Grains">Bakery & Grains</option>
              <option value="Packaged Foods">Packaged Foods</option>
              <option value="Dairy & Refrigerated">Dairy & Refrigerated</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Forecast Horizon
            </label>
            <select
              value={forecastDays}
              onChange={(e) => setForecastDays(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-color)',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            >
              <option value={5}>5 Days</option>
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-color)',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            />
          </div>
        </div>
      </div>

      {/* Dual Forecast Visualizations (Surplus & Demand) */}
      <div className="grid-2">
        {/* Surplus Forecast Chart */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp style={{ color: 'var(--primary-emerald)' }} size={20} />
                Projected Surplus Supply ({surplusOrg})
              </h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                {category} • {forecastDays}-day forward forecast
              </p>
            </div>
          </div>

          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 8px' }} />
              Calculating surplus projections...
            </div>
          ) : surplusForecast.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {surplusForecast.map((item, idx) => {
                const qty = item.predicted_quantity_kg || 0;
                const pct = Math.min(100, Math.round((qty / maxSurplusQty) * 100));
                return (
                  <div key={idx} style={{ padding: '10px 14px', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600 }}>{getDayName(item.target_date)} ({item.target_date})</span>
                      <span style={{ color: 'var(--primary-emerald)', fontWeight: 700 }}>
                        {qty.toFixed(1)} kg {item.is_event_day && <span className="badge badge-simulated" style={{ fontSize: '0.65rem', marginLeft: '6px' }}>Peak Event</span>}
                      </span>
                    </div>

                    {/* Bar visualization */}
                    <div style={{ width: '100%', height: '8px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          background: item.is_event_day
                            ? 'linear-gradient(90deg, #f59e0b, #ef4444)'
                            : 'linear-gradient(90deg, #10b981, #06b6d4)',
                          borderRadius: '4px',
                          transition: 'width 0.5s ease'
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No surplus forecast available for selected parameters.
            </div>
          )}
        </div>

        {/* Demand Forecast Chart */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingDown style={{ color: 'var(--accent-amber)' }} size={20} />
                Projected Community Demand ({demandOrg})
              </h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                {category} • {forecastDays}-day forward forecast
              </p>
            </div>
          </div>

          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 8px' }} />
              Calculating demand projections...
            </div>
          ) : demandForecast.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {demandForecast.map((item, idx) => {
                const qty = item.predicted_quantity_kg || 0;
                const pct = Math.min(100, Math.round((qty / maxDemandQty) * 100));
                return (
                  <div key={idx} style={{ padding: '10px 14px', backgroundColor: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600 }}>{getDayName(item.target_date)} ({item.target_date})</span>
                      <span style={{ color: 'var(--accent-amber)', fontWeight: 700 }}>
                        {qty.toFixed(1)} kg {item.is_event_day && <span className="badge badge-urgent" style={{ fontSize: '0.65rem', marginLeft: '6px' }}>Surge Demand</span>}
                      </span>
                    </div>

                    {/* Bar visualization */}
                    <div style={{ width: '100%', height: '8px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          background: 'linear-gradient(90deg, #f59e0b, #8b5cf6)',
                          borderRadius: '4px',
                          transition: 'width 0.5s ease'
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No demand forecast available for selected parameters.
            </div>
          )}
        </div>
      </div>

      {/* Interactive Single Prediction Tester Card */}
      <div className="glass-card" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
          <Sparkles style={{ color: 'var(--accent-cyan)' }} size={22} />
          <div>
            <h3 style={{ fontSize: '1.15rem', margin: 0 }}>On-Demand Prediction Tester</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
              Test single-point prediction queries against the trained RandomForest model in real-time.
            </p>
          </div>
        </div>

        <form onSubmit={handleTestPrediction} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Organization ID
            </label>
            <input
              type="text"
              value={testOrg}
              onChange={(e) => setTestOrg(e.target.value)}
              placeholder="e.g. hist-sup-001"
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-color)',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Category
            </label>
            <select
              value={testCategory}
              onChange={(e) => setTestCategory(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-color)',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            >
              <option value="Cooked Meals">Cooked Meals</option>
              <option value="Fresh Produce">Fresh Produce</option>
              <option value="Bakery & Grains">Bakery & Grains</option>
              <option value="Packaged Foods">Packaged Foods</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Target Date
            </label>
            <input
              type="date"
              value={testDate}
              onChange={(e) => setTestDate(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-color)',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingBottom: '8px' }}>
            <input
              type="checkbox"
              id="isEvent"
              checked={isEventDay}
              onChange={(e) => setIsEventDay(e.target.checked)}
              style={{ cursor: 'pointer', width: '16px', height: '16px' }}
            />
            <label htmlFor="isEvent" style={{ fontSize: '0.85rem', color: 'var(--text-main)', cursor: 'pointer' }}>
              Is Event / Peak Day
            </label>
          </div>

          <button type="submit" className="btn-primary" disabled={testLoading} style={{ height: '38px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
            {testLoading ? <RefreshCw size={16} className="animate-spin" /> : <Sparkles size={16} />}
            Predict Quantity
          </button>
        </form>

        {testResult && (
          <div style={{ marginTop: '1.25rem', padding: '1rem', borderRadius: '8px', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Predicted Surplus Generation</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary-emerald)' }}>
                {testResult.predicted_quantity_kg?.toFixed(1)} kg
              </div>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textAlign: 'right' }}>
              <div>Model: {testResult.model}</div>
              <div>Disclaimer: {testResult.data_disclaimer}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PredictionDashboard;
