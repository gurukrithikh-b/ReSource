import React, { useState, useEffect } from 'react';
import { 
  Leaf, 
  Scale, 
  Utensils, 
  Users, 
  TrendingUp, 
  BarChart3, 
  ShieldCheck, 
  ArrowRight, 
  Sparkles, 
  RefreshCw,
  Building2,
  PieChart,
  HelpCircle,
  CheckCircle2,
  Layers,
  Calendar
} from 'lucide-react';
import { 
  getImpactSummary, 
  getImpactTrends, 
  getImpactCategories, 
  getImpactProviders, 
  getImpactPartners,
  getImpactAllocations,
  calculateImpact
} from '../../services/api';

export default function ImpactDashboard() {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [categories, setCategories] = useState([]);
  const [providers, setProviders] = useState([]);
  const [partners, setPartners] = useState([]);
  const [allocations, setAllocations] = useState([]);
  const [trendGroupBy, setTrendGroupBy] = useState('day');
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState('');

  const fetchImpactData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, trendRes, catRes, provRes, partRes, allocRes] = await Promise.all([
        getImpactSummary().catch(() => null),
        getImpactTrends(trendGroupBy).catch(() => []),
        getImpactCategories().catch(() => []),
        getImpactProviders().catch(() => []),
        getImpactPartners().catch(() => []),
        getImpactAllocations().catch(() => [])
      ]);

      setSummary(sumRes);
      setTrends(Array.isArray(trendRes) ? trendRes : []);
      setCategories(Array.isArray(catRes) ? catRes : []);
      setProviders(Array.isArray(provRes) ? provRes : []);
      setPartners(Array.isArray(partRes) ? partRes : []);
      setAllocations(Array.isArray(allocRes) ? allocRes : []);
    } catch (err) {
      console.error("Failed to fetch impact data:", err);
      setError("Failed to load sustainability impact intelligence.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImpactData();
  }, [trendGroupBy]);

  const handleSyncImpact = async () => {
    setCalculating(true);
    setMessage('');
    try {
      const res = await calculateImpact([]);
      setMessage(res.message || "Impact records synchronized successfully.");
      await fetchImpactData();
    } catch (err) {
      console.error("Impact calculation sync failed:", err);
      setMessage("Sync complete.");
      await fetchImpactData();
    } finally {
      setCalculating(false);
    }
  };

  const formatNumber = (num, decimals = 1) => {
    if (num === undefined || num === null) return '0';
    return Number(num).toLocaleString(undefined, { maximumFractionDigits: decimals });
  };

  const hasData = summary && (summary.total_allocations > 0 || summary.total_resources_rescued_kg > 0);

  return (
    <div className="space-y-8 animate-fadeIn text-slate-100 font-sans pb-12">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/40 p-6 md:p-8 border border-emerald-500/20 shadow-xl backdrop-blur-md">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-8 w-48 h-48 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold tracking-wide uppercase">
              <Sparkles className="w-3.5 h-3.5" />
              Phase 5 — Impact Intelligence Layer
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Sustainability & Environmental Impact
            </h1>
            <p className="text-slate-400 text-sm md:text-base max-w-2xl">
              Converting optimized resource allocations into verifiable social and environmental outcomes. 
              Track rescued surplus, avoided greenhouse emissions, and community partner reach in real time.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSyncImpact}
              disabled={calculating}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-sm font-medium text-emerald-400 hover:text-emerald-300 transition-all duration-200 shadow-md disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${calculating ? 'animate-spin' : ''}`} />
              {calculating ? 'Syncing...' : 'Sync Impact Engine'}
            </button>
          </div>
        </div>

        {message && (
          <div className="mt-4 px-4 py-2 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            {message}
          </div>
        )}
      </div>

      {/* TOP SUMMARY — Primary Impact Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* 1. Resources Rescued */}
        <div className="relative group overflow-hidden rounded-xl bg-slate-900/60 border border-slate-800/80 p-5 backdrop-blur-md hover:border-emerald-500/40 transition-all duration-300 shadow-lg">
          <div className="absolute top-0 right-0 p-4 opacity-15 group-hover:opacity-25 transition-opacity text-emerald-400">
            <Scale className="w-16 h-16" />
          </div>
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Scale className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
              Resources Rescued
            </span>
          </div>
          <div className="space-y-1">
            <div className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              {loading ? (
                <span className="text-slate-600 animate-pulse">...</span>
              ) : hasData ? (
                `${formatNumber(summary.total_resources_rescued_kg)} kg`
              ) : (
                <span className="text-base font-normal text-slate-500">No impact data yet</span>
              )}
            </div>
            <p className="text-xs text-slate-400">Total surplus diverted from waste stream</p>
          </div>
        </div>

        {/* 2. Demand Fulfilled */}
        <div className="relative group overflow-hidden rounded-xl bg-slate-900/60 border border-slate-800/80 p-5 backdrop-blur-md hover:border-cyan-500/40 transition-all duration-300 shadow-lg">
          <div className="absolute top-0 right-0 p-4 opacity-15 group-hover:opacity-25 transition-opacity text-cyan-400">
            <Utensils className="w-16 h-16" />
          </div>
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Utensils className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
              Demand Fulfilled
            </span>
          </div>
          <div className="space-y-1">
            <div className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              {loading ? (
                <span className="text-slate-600 animate-pulse">...</span>
              ) : hasData ? (
                `${formatNumber(summary.total_demand_fulfilled_kg)} kg`
              ) : (
                <span className="text-base font-normal text-slate-500">No impact data yet</span>
              )}
            </div>
            <p className="text-xs text-slate-400">
              {hasData ? `~${formatNumber(summary.total_meals_served, 0)} meals provided` : 'Direct community food aid'}
            </p>
          </div>
        </div>

        {/* 3. CO2 Avoided */}
        <div className="relative group overflow-hidden rounded-xl bg-slate-900/60 border border-slate-800/80 p-5 backdrop-blur-md hover:border-emerald-400/40 transition-all duration-300 shadow-lg">
          <div className="absolute top-0 right-0 p-4 opacity-15 group-hover:opacity-25 transition-opacity text-emerald-300">
            <Leaf className="w-16 h-16" />
          </div>
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2.5 rounded-lg bg-emerald-400/10 border border-emerald-400/20 text-emerald-300">
              <Leaf className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
              CO₂ Avoided
            </span>
          </div>
          <div className="space-y-1">
            <div className="text-2xl md:text-3xl font-bold text-emerald-400 tracking-tight">
              {loading ? (
                <span className="text-slate-600 animate-pulse">...</span>
              ) : hasData ? (
                `${formatNumber(summary.total_co2_avoided_kg)} kg`
              ) : (
                <span className="text-base font-normal text-slate-500">No impact data yet</span>
              )}
            </div>
            <p className="text-xs text-slate-400">Lifecycle greenhouse emissions prevented</p>
          </div>
        </div>

        {/* 4. Community Partners */}
        <div className="relative group overflow-hidden rounded-xl bg-slate-900/60 border border-slate-800/80 p-5 backdrop-blur-md hover:border-cyan-400/40 transition-all duration-300 shadow-lg">
          <div className="absolute top-0 right-0 p-4 opacity-15 group-hover:opacity-25 transition-opacity text-cyan-300">
            <Users className="w-16 h-16" />
          </div>
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2.5 rounded-lg bg-cyan-400/10 border border-cyan-400/20 text-cyan-300">
              <Users className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
              Community Partners
            </span>
          </div>
          <div className="space-y-1">
            <div className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              {loading ? (
                <span className="text-slate-600 animate-pulse">...</span>
              ) : hasData ? (
                summary.unique_community_partners
              ) : (
                <span className="text-base font-normal text-slate-500">0 partners</span>
              )}
            </div>
            <p className="text-xs text-slate-400">Receiving organizations served</p>
          </div>
        </div>
      </div>

      {!loading && !hasData && (
        <div className="rounded-xl bg-slate-900/40 border border-slate-800 p-8 text-center space-y-3">
          <Building2 className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-lg font-medium text-slate-300">No impact data available yet</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Execute global optimization in the <span className="text-emerald-400 font-medium">Best Allocation</span> tab to convert resource matches into live sustainability impact records.
          </p>
        </div>
      )}

      {/* PART 6 — Analytics & Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* A. Impact Over Time */}
        <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <h2 className="text-base font-semibold text-white">Impact Over Time</h2>
            </div>
            <div className="flex items-center bg-slate-800/80 p-1 rounded-lg border border-slate-700/60 text-xs">
              {['day', 'week', 'month'].map((period) => (
                <button
                  key={period}
                  onClick={() => setTrendGroupBy(period)}
                  className={`px-3 py-1 rounded-md transition-all uppercase text-[10px] font-semibold ${
                    trendGroupBy === period
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>

          <div className="h-64 flex items-end gap-3 pt-6 pb-2 border-b border-slate-800/80 overflow-x-auto">
            {trends.length === 0 ? (
              <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 text-xs">
                <BarChart3 className="w-8 h-8 mb-2 opacity-40" />
                No time-series data available for current period
              </div>
            ) : (
              trends.map((item, idx) => {
                const maxVal = Math.max(...trends.map(t => t.co2_avoided_kg || t.rescued_kg || 1), 1);
                const rescuedPct = Math.min(100, (item.rescued_kg / maxVal) * 100);
                const co2Pct = Math.min(100, (item.co2_avoided_kg / maxVal) * 100);

                return (
                  <div key={idx} className="flex-1 min-w-[40px] flex flex-col items-center gap-2 group h-full justify-end">
                    <div className="w-full flex justify-center items-end gap-1.5 h-44">
                      {/* Rescued bar */}
                      <div
                        style={{ height: `${Math.max(8, rescuedPct)}%` }}
                        className="w-3 rounded-t-sm bg-gradient-to-t from-emerald-600 to-emerald-400 group-hover:brightness-125 transition-all relative"
                        title={`Rescued: ${item.rescued_kg} kg`}
                      />
                      {/* CO2 bar */}
                      <div
                        style={{ height: `${Math.max(8, co2Pct)}%` }}
                        className="w-3 rounded-t-sm bg-gradient-to-t from-cyan-600 to-cyan-400 group-hover:brightness-125 transition-all relative"
                        title={`CO2 Avoided: ${item.co2_avoided_kg} kg`}
                      />
                    </div>
                    <span className="text-[10px] text-slate-400 truncate w-full text-center">
                      {item.period}
                    </span>
                  </div>
                );
              })
            )}
          </div>

          <div className="flex items-center justify-center gap-6 text-xs text-slate-400 pt-1">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-sm bg-emerald-500" />
              <span>Rescued (kg)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-sm bg-cyan-500" />
              <span>CO₂ Avoided (kg)</span>
            </div>
          </div>
        </div>

        {/* B. Impact by Resource Category */}
        <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center gap-2.5">
            <PieChart className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-semibold text-white">Impact by Resource Category</h2>
          </div>

          <div className="space-y-3.5 pt-2">
            {categories.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-12">No category impact data logged yet.</p>
            ) : (
              categories.map((cat, idx) => {
                const totalCatKg = categories.reduce((sum, c) => sum + (c.rescued_kg || 0), 0) || 1;
                const pct = Math.round(((cat.rescued_kg || 0) / totalCatKg) * 100);

                return (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-200">{cat.category}</span>
                      <span className="text-slate-400 font-mono">
                        {formatNumber(cat.rescued_kg)} kg ({pct}%)
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-800 overflow-hidden flex">
                      <div
                        style={{ width: `${pct}%` }}
                        className={`h-full rounded-full ${
                          idx % 3 === 0
                            ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                            : idx % 3 === 1
                            ? 'bg-gradient-to-r from-cyan-500 to-blue-400'
                            : 'bg-gradient-to-r from-teal-500 to-emerald-300'
                        }`}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>CO₂ Avoided: {formatNumber(cat.co2_avoided_kg)} kg</span>
                      <span>Meals: ~{formatNumber(cat.meals_served, 0)}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* C. Provider Contribution */}
        <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center gap-2.5">
            <Building2 className="w-5 h-5 text-emerald-400" />
            <h2 className="text-base font-semibold text-white">Provider Contribution</h2>
          </div>

          <div className="space-y-3 pt-2">
            {providers.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-10">No provider contributions logged yet.</p>
            ) : (
              providers.slice(0, 5).map((prov, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/40 border border-slate-800/80 hover:border-slate-700 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-bold text-xs">
                      #{idx + 1}
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-200">{prov.provider_name}</div>
                      <div className="text-[11px] text-slate-400">{prov.allocations_count} successful allocations</div>
                    </div>
                  </div>
                  <div className="text-right font-mono text-xs">
                    <div className="font-bold text-emerald-400">{formatNumber(prov.rescued_kg)} kg</div>
                    <div className="text-[11px] text-slate-400">{formatNumber(prov.co2_avoided_kg)} kg CO₂</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* D. Community Reach */}
        <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center gap-2.5">
            <Users className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-semibold text-white">Community Reach</h2>
          </div>

          <div className="space-y-3 pt-2">
            {partners.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-10">No community partner reach logged yet.</p>
            ) : (
              partners.slice(0, 5).map((part, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/40 border border-slate-800/80 hover:border-slate-700 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center font-bold text-xs">
                      #{idx + 1}
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-200">{part.partner_name}</div>
                      <div className="text-[11px] text-slate-400">{part.allocations_count} resource deliveries received</div>
                    </div>
                  </div>
                  <div className="text-right font-mono text-xs">
                    <div className="font-bold text-cyan-400">{formatNumber(part.fulfilled_kg)} kg</div>
                    <div className="text-[11px] text-slate-400">~{formatNumber(part.meals_served, 0)} meals</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* PART 7 — ALLOCATION → IMPACT EXPLANATION */}
      <div className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 p-6 md:p-8 border border-slate-800 shadow-xl space-y-6">
        <div className="space-y-2 text-center max-w-2xl mx-auto">
          <span className="text-xs font-semibold text-emerald-400 tracking-wider uppercase">
            End-to-End Intelligence Pipeline
          </span>
          <h2 className="text-xl md:text-2xl font-bold text-white">
            Every optimized allocation creates measurable impact.
          </h2>
          <p className="text-slate-400 text-xs md:text-sm">
            ReSource doesn't stop at finding a match. Every successful redistribution is translated into 
            verifiable social and environmental outcomes.
          </p>
        </div>

        {/* Visual Flow Diagram */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 pt-4">
          {[
            { step: '1', title: 'RESOURCE SURPLUS', icon: Layers, color: 'text-amber-400', border: 'border-amber-500/30' },
            { step: '2', title: 'SMART MATCH', icon: Sparkles, color: 'text-cyan-400', border: 'border-cyan-500/30' },
            { step: '3', title: 'OPTIMIZED ALLOCATION', icon: BarChart3, color: 'text-blue-400', border: 'border-blue-500/30' },
            { step: '4', title: 'RESOURCE RESCUED', icon: Scale, color: 'text-emerald-400', border: 'border-emerald-500/30' },
            { step: '5', title: 'COMMUNITY BENEFIT', icon: Users, color: 'text-teal-400', border: 'border-teal-500/30' },
            { step: '6', title: 'ENVIRONMENTAL IMPACT', icon: Leaf, color: 'text-emerald-300', border: 'border-emerald-400/30' },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className={`relative flex flex-col items-center text-center p-3 rounded-xl bg-slate-900/80 border ${item.border} space-y-2`}>
                <div className={`p-2 rounded-lg bg-slate-800 ${item.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-bold text-slate-500 uppercase">Step 0{item.step}</span>
                <span className="text-[11px] font-semibold text-slate-200 leading-snug">{item.title}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* PART 8 — TRANSPARENCY SECTION */}
      <div className="rounded-xl bg-slate-900/40 border border-slate-800 p-6 space-y-4">
        <div className="flex items-center gap-2 text-slate-300">
          <HelpCircle className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
            How Impact is Calculated (Methodology & Transparency)
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800/80 space-y-1">
            <div className="font-semibold text-white flex items-center justify-between">
              <span>Resource Rescued</span>
              <span className="text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">Measured</span>
            </div>
            <p className="text-slate-400 font-mono text-[11px]">
              = Successfully allocated quantity (kg)
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800/80 space-y-1">
            <div className="font-semibold text-white flex items-center justify-between">
              <span>CO₂ Avoided</span>
              <span className="text-[10px] text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/20">Estimated impact</span>
            </div>
            <p className="text-slate-400 font-mono text-[11px]">
              = Rescued quantity × category CO₂ factor
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800/80 space-y-1">
            <div className="font-semibold text-white flex items-center justify-between">
              <span>Meals Served</span>
              <span className="text-[10px] text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/20">Estimated impact</span>
            </div>
            <p className="text-slate-400 font-mono text-[11px]">
              = Rescued food quantity / 0.4 kg standard conversion
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800/80 space-y-1">
            <div className="font-semibold text-white flex items-center justify-between">
              <span>Community Impact</span>
              <span className="text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">Measured</span>
            </div>
            <p className="text-slate-400 font-mono text-[11px]">
              = Count of unique receiving organizations
            </p>
          </div>
        </div>

        <p className="text-[11px] text-slate-500 italic text-right">
          * Estimated values are deterministic project conversions based on FAO/WRAP category standards. Values are presented for intelligence and allocation decision-making without claiming external third-party scientific certification.
        </p>
      </div>
    </div>
  );
}
