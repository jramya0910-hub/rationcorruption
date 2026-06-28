import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext.jsx';
import Navbar from '../../components/Navbar.jsx';
import {
  getEntitlement, getReceipts, getStockAvailability,
  submitComplaint, getBeneficiaryComplaints,
} from '../../services/api.js';
import { QRCodeSVG } from 'qrcode.react';

const STATUS_CLASS = { OPEN: 'badge-open', UNDER_REVIEW: 'badge-review', RESOLVED: 'badge-resolved' };

export default function BeneficiaryDashboard() {
  const { auth } = useAuth();
  const id = auth?.user_id;

  const [entitlement, setEntitlement] = useState(null);
  const [receipts, setReceipts]       = useState([]);
  const [stock, setStock]             = useState([]);
  const [complaints, setComplaints]   = useState([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');

  const [complaint, setComplaint] = useState({ shop_id: '', complaint_type: 'UNDERWEIGHT', description: '' });
  const [submitting, setSubmitting] = useState(false);
  const [submitMsg, setSubmitMsg]   = useState('');

  const [showQR, setShowQR] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [e, r, s, c] = await Promise.all([
        getEntitlement(id),
        getReceipts(id),
        getStockAvailability(id),
        getBeneficiaryComplaints(id),
      ]);
      setEntitlement(e.data.data);
      setReceipts(r.data.data.receipts || []);
      setStock(s.data.data.stock_availability || []);
      setComplaints(c.data.data.complaints || []);
      if (e.data.data?.assigned_shop_id) {
        setComplaint(prev => ({ ...prev, shop_id: e.data.data.assigned_shop_id }));
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  async function handleComplaintSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setSubmitMsg('');
    try {
      await submitComplaint(complaint);
      setSubmitMsg('Complaint submitted successfully!');
      setComplaint(prev => ({ ...prev, description: '', complaint_type: 'UNDERWEIGHT' }));
      load();
    } catch (err) {
      setSubmitMsg(err.response?.data?.detail || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return (
    <>
      <Navbar title="Beneficiary Portal" />
      <div className="spinner-overlay"><div className="spinner" /></div>
    </>
  );

  return (
    <>
      <Navbar title="Beneficiary Portal" />
      <div className="main-content" style={{ maxWidth: 960, margin: '0 auto' }}>
        {error && <div className="error-msg">{error}</div>}

        {/* Profile + QR ─────────────────────────────────────────────────── */}
        <div className="card" style={{ marginBottom: 20, display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <div style={{ flex: 1, minWidth: 220 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>👤 {entitlement?.name}</h2>
            <table style={{ fontSize: 13, borderCollapse: 'collapse' }}>
              <tbody>
                {[
                  ['Ration Card', entitlement?.ration_card_number],
                  ['Family Members', entitlement?.family_members],
                  ['Monthly Entitlement', `${entitlement?.monthly_entitlement_kg} kg`],
                  ['Assigned Shop', entitlement?.shop_name || 'N/A'],
                  ['Shop Location', entitlement?.shop_location || '—'],
                ].map(([k, v]) => (
                  <tr key={k}>
                    <td style={{ color: '#64748b', paddingRight: 16, paddingBottom: 6 }}>{k}</td>
                    <td style={{ fontWeight: 600, paddingBottom: 6 }}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ textAlign: 'center' }}>
            <button className="btn btn-ghost" style={{ marginBottom: 10, fontSize: 12 }} onClick={() => setShowQR(!showQR)}>
              {showQR ? 'Hide QR Code' : '📲 Show My QR Code'}
            </button>
            {showQR && (
              <div style={{ padding: 12, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, display: 'inline-block' }}>
                <QRCodeSVG value={JSON.stringify({ id, rc: entitlement?.ration_card_number })} size={140} />
                <p style={{ fontSize: 10, color: '#94a3b8', marginTop: 6 }}>{entitlement?.ration_card_number}</p>
              </div>
            )}
          </div>
        </div>

        {/* Stock Availability ────────────────────────────────────────────── */}
        <div className="card" style={{ marginBottom: 20 }}>
          <p className="section-title">📦 Stock Availability at Your Shop</p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {stock.map(s => (
              <div key={s.grain_type} style={{
                padding: '12px 20px', borderRadius: 8,
                background: s.available ? '#f0fdf4' : '#fef2f2',
                border: `1px solid ${s.available ? '#86efac' : '#fca5a5'}`,
                minWidth: 130, textAlign: 'center',
              }}>
                <span className={`stock-dot ${s.available ? 'available' : 'unavailable'}`} />
                <span style={{ fontWeight: 700, fontSize: 14 }}>{s.grain_type}</span>
                <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{s.remaining_stock_kg.toFixed(1)} kg remaining</p>
              </div>
            ))}
          </div>
        </div>

        {/* Receipts ──────────────────────────────────────────────────────── */}
        <div className="card" style={{ marginBottom: 20 }}>
          <p className="section-title">🧾 Recent Transaction Receipts</p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Grain</th><th>Quantity</th><th>QR Verified</th></tr></thead>
              <tbody>
                {receipts.length === 0 ? (
                  <tr><td colSpan={4} style={{ color: '#94a3b8', textAlign: 'center' }}>No transactions yet</td></tr>
                ) : receipts.map(r => (
                  <tr key={r.transaction_id}>
                    <td>{new Date(r.transaction_date).toLocaleDateString()}</td>
                    <td>{r.grain_type}</td>
                    <td>{r.quantity_given_kg} kg</td>
                    <td>{r.qr_scan_verified ? '✅ Yes' : '❌ No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Complaint Form ────────────────────────────────────────────────── */}
        <div className="card" style={{ marginBottom: 20 }}>
          <p className="section-title">📝 Submit a Complaint</p>
          {submitMsg && (
            <div className={submitMsg.includes('success') ? 'success-msg' : 'error-msg'}>{submitMsg}</div>
          )}
          <form onSubmit={handleComplaintSubmit}>
            <div className="form-group">
              <label>Complaint Type</label>
              <select value={complaint.complaint_type} onChange={e => setComplaint(p => ({ ...p, complaint_type: e.target.value }))}>
                {['UNDERWEIGHT', 'POOR_QUALITY', 'OVERCHARGING', 'NOT_AVAILABLE', 'OTHER'].map(t => (
                  <option key={t} value={t}>{t.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea rows={3} value={complaint.description} onChange={e => setComplaint(p => ({ ...p, description: e.target.value }))} placeholder="Describe the issue…" required />
            </div>
            <button className="btn btn-primary" type="submit" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit Complaint'}
            </button>
          </form>
        </div>

        {/* Complaint History ─────────────────────────────────────────────── */}
        <div className="card">
          <p className="section-title">📋 Complaint History</p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Shop</th><th>Type</th><th>AI Category</th><th>Status</th></tr></thead>
              <tbody>
                {complaints.length === 0 ? (
                  <tr><td colSpan={5} style={{ color: '#94a3b8', textAlign: 'center' }}>No complaints filed</td></tr>
                ) : complaints.map(c => (
                  <tr key={c.complaint_id}>
                    <td>{new Date(c.created_at).toLocaleDateString()}</td>
                    <td>{c.shop_name}</td>
                    <td>{c.complaint_type.replace('_', ' ')}</td>
                    <td><span className="badge badge-open">{c.ai_category || '—'}</span></td>
                    <td><span className={`badge ${STATUS_CLASS[c.status] || ''}`}>{c.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
