import React, { useState } from 'react';
import { parseDemandText, createDemandListing } from '../../services/api';
import { Sparkles, Send, CheckCircle2, AlertCircle, RefreshCw, Clock } from 'lucide-react';

export const DemandIntakeForm = ({ onListingCreated }) => {
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
      const res = await parseDemandText(rawText);
      setParsedPreview(res);
      setFeedback({ type: 'success', message: 'Resource request details recognized!' });
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
          ? `${parsedPreview.food_subtype.toUpperCase()} Request (${parsedPreview.quantity || 15} ${parsedPreview.unit || 'kg'})`
          : undefined,
        requested_quantity: parsedPreview?.quantity || undefined,
        unit: parsedPreview?.unit || 'kg',
        urgency_level: parsedPreview?.urgency_level || undefined,
        storage_capacity: parsedPreview?.storage_condition || 'AMBIENT',
        is_simulated: true
      };

      const created = await createDemandListing(payload);
      setFeedback({ type: 'success', message: `Resource request "${created.title}" successfully submitted!` });
      setRawText('');
      setParsedPreview(null);
      if (onListingCreated) {
        onListingCreated(created);
      }
    } catch (err) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || err.message || 'Failed to submit request.' });
    } finally {
      setSubmitting(false);
      setParsing(false);
    }
  };

  return (
    <div className="glass-card" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
        <Sparkles style={{ color: 'var(--accent-cyan)' }} size={24} />
        <div>
          <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Smart Resource Request (Community Partner)</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
            Submit resource needs in plain text. ReSource detects quantity, urgency, and deadline automatically.
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
            Resource Request Description
          </label>
          <textarea
            rows={3}
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="e.g. NGO needs 150 cooked vegetarian meals by 8 PM today."
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
              border: '1px solid var(--accent-cyan)',
              backgroundColor: 'rgba(56, 189, 248, 0.2)',
              color: '#bae6fd',
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
              backgroundColor: 'var(--accent-cyan)',
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
            {submitting ? 'Submitting...' : 'Submit Request'}
          </button>
        </div>
      </form>

      {/* Parsed Result Preview Card */}
      {parsedPreview && (
        <div style={{
          padding: '1.25rem',
          borderRadius: '10px',
          backgroundColor: 'rgba(15, 23, 42, 0.8)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          marginTop: '1rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#bae6fd', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={16} /> Recognized Details
            </h4>
            <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.2)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.4)' }}>
              Confidence: {Math.round(parsedPreview.confidence * 100)}%
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Resource Category:</span>
              <strong style={{ color: '#fff' }}>{parsedPreview.resource_type || 'Food Request'}</strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Requested Quantity:</span>
              <strong style={{ color: 'var(--accent-cyan)' }}>
                {parsedPreview.quantity !== null ? `${parsedPreview.quantity} ${parsedPreview.unit}` : 'Not specified'}
              </strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Required By:</span>
              <strong style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} />
                {parsedPreview.deadline_display || (parsedPreview.required_by ? new Date(parsedPreview.required_by).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Flexible')}
              </strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Urgency Level:</span>
              <strong style={{ color: parsedPreview.urgency_level === 'HIGH' || parsedPreview.urgency_level === 'CRITICAL' ? '#f87171' : '#f59e0b' }}>
                {parsedPreview.urgency_level || 'MEDIUM'}
              </strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>Storage Capacity:</span>
              <strong style={{ color: '#cbd5e1' }}>{parsedPreview.storage_condition || 'Ambient'}</strong>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
