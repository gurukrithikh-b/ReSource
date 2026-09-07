import React, { useState } from 'react';
import { parseSurplusText, createSurplusListing } from '../../services/api';
import { Sparkles, Send, CheckCircle2, AlertCircle, RefreshCw, Clock } from 'lucide-react';

export const SurplusIntakeForm = ({ onListingCreated }) => {
  const [rawText, setRawText] = useState('');
  const [parsedPreview, setParsedPreview] = useState(null);
  const [parsing, setParsing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const handleParse = async () => {
    if (!rawText.trim()) {
      setFeedback({ type: 'error', message: 'Please enter a description first.' });
      return;
    }
    try {
      setParsing(true);
      setFeedback(null);
      const res = await parseSurplusText(rawText);
      setParsedPreview(res);
      setFeedback({ type: 'success', message: 'Resource details successfully recognized!' });
    } catch (err) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || err.message || 'Failed to process text. Is the backend server running?' });
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!rawText.trim()) {
      setFeedback({ type: 'error', message: 'Description cannot be empty.' });
      return;
    }
    try {
      setSubmitting(true);
      setFeedback(null);

      const payload = {
        raw_nlp_text: rawText,
        title: parsedPreview?.food_subtype
          ? `${parsedPreview.food_subtype.toUpperCase()} (${parsedPreview.quantity || 10} ${parsedPreview.unit || 'kg'})`
          : undefined,
        quantity: parsedPreview?.quantity || undefined,
        unit: parsedPreview?.unit || 'kg',
        storage_condition: parsedPreview?.storage_condition || undefined,
        perishability_hours: parsedPreview?.perishability_hours || undefined,
        is_simulated: true
      };

      const created = await createSurplusListing(payload);
      setFeedback({ type: 'success', message: `Resource listing "${created.title}" successfully added!` });
      setRawText('');
      setParsedPreview(null);
      if (onListingCreated) {
        onListingCreated(created);
      }
    } catch (err) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || err.message || 'Failed to add resource listing.' });
    } finally {
      setSubmitting(false);
      setParsing(false);
    }
  };

  return (
    <div className="glass-card" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
        <Sparkles style={{ color: 'var(--accent-purple)' }} size={24} />
        <div>
          <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Smart Resource Entry (Resource Provider)</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
            Describe your surplus in plain text. ReSource automatically detects quantity, storage, and deadline.
          </p>
        </div>
      </div>

      {feedback && (
        <div style={{
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          marginBottom: '1rem',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: feedback.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          border: `1px solid ${feedback.type === 'success' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
          color: feedback.type === 'success' ? '#34d399' : '#f87171'
        }}>
          {feedback.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{feedback.message}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-dim)', marginBottom: '6px' }}>
            Surplus Description
          </label>
          <textarea
            rows={3}
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="e.g. We have 200 packed vegetarian meals available until 9 PM today. They need refrigeration."
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid var(--border-color)',
              color: '#fff',
              fontSize: '0.9rem',
              resize: 'vertical',
              outline: 'none',
              fontFamily: 'inherit'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '12px', marginBottom: '1.5rem' }}>
          <button
            type="button"
            onClick={handleParse}
            disabled={parsing || !rawText.trim()}
            style={{
              padding: '0.6rem 1.2rem',
              borderRadius: '6px',
              border: '1px solid var(--accent-purple)',
              backgroundColor: 'rgba(168, 85, 247, 0.2)',
              color: '#e9d5ff',
              cursor: parsing || !rawText.trim() ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.85rem',
              fontWeight: 500,
              opacity: parsing || !rawText.trim() ? 0.6 : 1
            }}
          >
            {parsing ? <RefreshCw size={16} className="spin" /> : <Sparkles size={16} />}
            {parsing ? 'Understanding text...' : 'Smart Parse'}
          </button>

          <button
            type="submit"
            disabled={submitting || !rawText.trim()}
            style={{
              padding: '0.6rem 1.4rem',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: 'var(--primary-emerald)',
              color: '#0f172a',
              cursor: submitting || !rawText.trim() ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.85rem',
              fontWeight: 600,
              opacity: submitting || !rawText.trim() ? 0.6 : 1
            }}
          >
            <Send size={16} />
            {submitting ? 'Adding...' : 'Add Available Resource'}
          </button>
        </div>
      </form>

      {/* Parsed Result Preview Card */}
      {parsedPreview && (
        <div style={{
          padding: '1.25rem',
          borderRadius: '10px',
          backgroundColor: 'rgba(15, 23, 42, 0.8)',
          border: '1px solid rgba(168, 85, 247, 0.3)',
          marginTop: '1rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#e9d5ff', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={16} /> Recognized Details
            </h4>
            <span className="badge" style={{ backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.4)' }}>
              Confidence: {Math.round(parsedPreview.confidence * 100)}%
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Resource Category:</span>
              <strong style={{ color: '#fff' }}>{parsedPreview.resource_type || 'Food Surplus'}</strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Quantity:</span>
              <strong style={{ color: 'var(--primary-emerald)' }}>
                {parsedPreview.quantity !== null ? `${parsedPreview.quantity} ${parsedPreview.unit}` : 'Not specified'}
              </strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Expiry / Available Until:</span>
              <strong style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} />
                {parsedPreview.deadline_display || (parsedPreview.expires_at ? new Date(parsedPreview.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Flexible')}
              </strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Usable Shelf-Life:</span>
              <strong style={{ color: '#bae6fd' }}>
                {parsedPreview.perishability_hours ? `approximately ${parsedPreview.perishability_hours} hours` : 'Standard'}
              </strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Type:</span>
              <strong style={{ color: 'var(--accent-cyan)' }}>{parsedPreview.food_subtype || 'General'}</strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Storage Needed:</span>
              <strong style={{ color: parsedPreview.storage_condition === 'REFRIGERATED' ? '#38bdf8' : '#cbd5e1' }}>
                {parsedPreview.storage_condition || 'Ambient (Room Temp)'}
              </strong>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
