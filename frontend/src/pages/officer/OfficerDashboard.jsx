import React, { useEffect, useState, useCallback } from 'react';
import Navbar from '../../components/Navbar.jsx';
import AlertCard from '../../components/AlertCard.jsx';
import RiskBadge from '../../components/RiskBadge.jsx';
import BarChart from '../../components/Charts/BarChart.jsx';
import LineChart from '../../components/Charts/LineChart.jsx';
import PieChart from '../../components/Charts/PieChart.jsx';
import {
  getDashboard, getAlerts, getRiskShops,
  getAllComplaints, getPredictions,
  resolveComplaint, exportReport,
  runFraudDetection,
} from '../../services/api.js';

const STATUS_CLASS = { OPEN: 'badge-open', UNDER_REVIEW: 'badge-review', RESOLVED: 'badge-resolved' };

export default function OfficerDashboard() {
  const [summary, setSummary]         = useState(null);
  const [barData, setBarData]         = useState([]);
  const [trendData, setTrendData]     = useState([]);
  const [pieData, setPieData]         = useState([]);
  const [alerts, setAlerts]           = useState([]);
  const [shops, setShops]             = useState([]);
  const [complaints, setComplaints]   = useState([]);
  const [predictions, setPredictions] = useState([]);

  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');
  const [activeTab, setActiveTab]     = useState('overview');

  const [cmpFilter, setCmpFilter]     = useState('');
  const [aiLoading, setAiLoading]     = useState({});
  const [aiResult, setAiResult]       = useState({});
  const [exporting, setExporting]     = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [dash, alertsRes, riskRes, cmpRes, predRes] = await Promise.all([
        getDashboard(), getAlerts(), getRiskShops(), getAllComplaints(), getPredictions(),
      ]);
      const d = dash.data.data;
      setSummary(d.summary);
      setBarData(d.bar_chart || []);
      setTrendData(d.monthly_trend || []);
      setPieData((d.complaint_breakdown || []).map(x => ({ label: x.type, value: x.count })));
      setAlerts(alertsRes.data.data.alerts || []);
      setShops(riskRes.data.data.shops || []);
      setComplaints(cmpRes.data.data.complaints || []);
      setPredictions(predRes.data.data.predictions || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleResolve(id) {
    await resolveComplaint(id);
    load();
  }

  async function handleRunAI(shopId) {
    setAiLoading(p => ({ ...p, [shopId]: true }));
    try {
      const res = await runFraudDetection(shopId);
      setAiResult(p => ({ ...p, [shopId]: res.data.data }));
      load();
    } catch {}
    finally { setAiLoading(p => ({ ...p, [shopId]: false })); }
  }

  async function handleExport(fmt) {
    setExporting(true);
    try {
      const res = await exportReport(fmt);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a   = document.createElement('a');
      a.href  = url;
      a.download = `report.${fmt}`;
      a.click();
    } catch {}
    finally { setExporting(false); }
  }

  const filteredComplaints = complaints.filter(c => !cmpFilter || c.status === cmpFilter);

  const tabs = [
    { id: 'overview',     label: '📊 Overview' },
    { id: 'alerts',       label: `🚨 Alerts (${alerts.filter(a => !a.is_reviewed).length})` },
    { id: 'risk',         label: '⚠️ Risk Scores' },
    { id: 'complaints',   label: `📋 Complaints (${complaints.filter(c => c.status === 'OPEN').length})` },
    { id: 'predictions',  label: '🔮 Predictions' },
  ];

  if (loading) return (
    <>
      <Navbar title="Government Officer Dashboard" />
      <div className="spinner-overlay"><div className="spinner" /></div>
    </>
  );

  return (
    <>
      <Navbar title="Government Officer Dashboard" />
      <div className="main-content" style={{ maxWidth: 1200, margin: '0 auto' }}>
        {error && <div className="error-msg">{error}</div>}

        {/* Tab Nav */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '2px solid #e2e8f0', flexWrap: 'wrap' }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              padding: '10px 14px', border: 'none', background: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap',
              color: activeTab === t.id ? '#2563eb' : '#64748b',
              borderBottom: activeTab === t.id ? '2px solid #2563eb' : '2px solid transparent',
              marginBottom: -2,
            }}>
              {t.label}
            </button>
          ))}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center', paddingBottom: 6 }}>
            <button className="btn btn-ghost" style={{ fontSize: 12 }} disabled={exporting} onClick={() => handleExport('csv')}>
              ⬇ CSV
            </button>
            <button className="btn btn-ghost" style={{ fontSize: 12 }} disabled={exporting} onClick={() => handleExport('pdf')}>
              ⬇ PDF
            </button>
          </div>
        </div>

        {/* ── OVERVIEW TAB ─────────────────────────────────────────────── */}
        {activeTab === 'overview' && summary && (
          <>
            <div className="stat-grid">
              <div className="stat-card">
                <div className="label">Total Shops</div>
                <div className="value blue">{summary.total_shops}</div>
              </div>
              <div className="stat-card">
                <div className="label">Total Beneficiaries</div>
                <div className="value green">{summary.total_beneficiaries}</div>
              </div>
              <div className="stat-card">
                <div className="label">Active Alerts</div>
                <div className="value red">{summary.active_alerts}</div>
              </div>
              <div className="stat-card">
                <div className="label">Open Complaints</div>
                <div className="value yellow">{summary.open_complaints}</div>
              </div>
              <div className="stat-card">
                <div className="label">High Risk Shops</div>
                <div className="value red">{summary.high_risk_shops}</div>
              </div>
            </div>

            <div className="charts-grid">
              <div className="chart-card">
                <h3>Stock Distributed Per Shop (kg)</h3>
                <BarChart data={barData} title="Distributed (kg)" />
              </div>
              <div className="chart-card">
                <h3>Monthly Distribution Trend</h3>
                <LineChart data={trendData.map(t => ({ label: t.month, value: t.total_kg }))} title="kg Distributed" />
              </div>
              <div className="chart-card">
                <h3>Complaint Categories</h3>
                <PieChart data={pieData} />
              </div>
            </div>

            {/* Quick alert preview */}
            <div className="card">
              <p className="section-title">🚨 Recent Fraud Alerts</p>
              {alerts.slice(0, 3).map(a => <AlertCard key={a.alert_id} alert={a} />)}
              {alerts.length === 0 && <p style={{ color: '#94a3b8', fontSize: 13 }}>No alerts</p>}
            </div>
          </>
        )}

        {/* ── ALERTS TAB ───────────────────────────────────────────────── */}
        {activeTab === 'alerts' && (
          <div className="card">
            <p className="section-title">All Fraud Alerts</p>
            {alerts.length === 0 ? (
              <p style={{ color: '#94a3b8' }}>No alerts found</p>
            ) : alerts.map(a => <AlertCard key={a.alert_id} alert={a} />)}
          </div>
        )}

        {/* ── RISK SCORES TAB ──────────────────────────────────────────── */}
        {activeTab === 'risk' && (
          <div className="card">
            <p className="section-title">Shop Risk Scores</p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Shop</th><th>Owner</th><th>District</th><th>Risk Score</th><th>Level</th><th>AI Check</th></tr>
                </thead>
                <tbody>
                  {shops.map(s => (
                    <tr key={s.shop_id}>
                      <td style={{ fontWeight: 600 }}>{s.shop_name}</td>
                      <td>{s.owner_name}</td>
                      <td>{s.district}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ flex: 1, height: 6, background: '#e2e8f0', borderRadius: 3, maxWidth: 80 }}>
                            <div style={{
                              height: '100%', borderRadius: 3,
                              width: `${s.risk_score}%`,
                              background: s.risk_score > 70 ? '#dc2626' : s.risk_score > 40 ? '#d97706' : '#16a34a',
                            }} />
                          </div>
                          <span style={{ fontWeight: 700, fontSize: 13 }}>{s.risk_score}</span>
                        </div>
                      </td>
                      <td><RiskBadge level={s.risk_level} /></td>
                      <td>
                        <button className="btn btn-primary" style={{ fontSize: 11, padding: '4px 10px' }}
                          disabled={aiLoading[s.shop_id]}
                          onClick={() => handleRunAI(s.shop_id)}>
                          {aiLoading[s.shop_id] ? '…' : 'Run AI'}
                        </button>
                        {aiResult[s.shop_id] && (
                          <p style={{ fontSize: 10, color: aiResult[s.shop_id].is_fraud_suspected ? '#dc2626' : '#16a34a', marginTop: 3 }}>
                            {aiResult[s.shop_id].is_fraud_suspected ? '⚠ Fraud' : '✓ OK'}
                          </p>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── COMPLAINTS TAB ───────────────────────────────────────────── */}
        {activeTab === 'complaints' && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <p className="section-title" style={{ marginBottom: 0 }}>All Complaints</p>
              <select value={cmpFilter} onChange={e => setCmpFilter(e.target.value)}
                style={{ padding: '6px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 13 }}>
                <option value="">All Status</option>
                {['OPEN', 'UNDER_REVIEW', 'RESOLVED'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Date</th><th>Beneficiary</th><th>Shop</th><th>Type</th><th>AI Category</th><th>Status</th><th>Action</th></tr>
                </thead>
                <tbody>
                  {filteredComplaints.length === 0 ? (
                    <tr><td colSpan={7} style={{ textAlign: 'center', color: '#94a3b8' }}>No complaints</td></tr>
                  ) : filteredComplaints.map(c => (
                    <tr key={c.complaint_id}>
                      <td>{new Date(c.created_at).toLocaleDateString()}</td>
                      <td>{c.beneficiary_name}</td>
                      <td>{c.shop_name}</td>
                      <td>{c.complaint_type.replace('_', ' ')}</td>
                      <td><span className="badge badge-open">{c.ai_category || '—'}</span></td>
                      <td><span className={`badge ${STATUS_CLASS[c.status] || ''}`}>{c.status}</span></td>
                      <td>
                        {c.status !== 'RESOLVED' && (
                          <button className="btn btn-success" style={{ fontSize: 11, padding: '4px 10px' }}
                            onClick={() => handleResolve(c.complaint_id)}>
                            Resolve
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── PREDICTIONS TAB ──────────────────────────────────────────── */}
        {activeTab === 'predictions' && (
          <div className="card">
            <p className="section-title">Stock Demand Predictions</p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Shop</th><th>Grain</th><th>Predicted Demand (kg)</th><th>Month</th></tr>
                </thead>
                <tbody>
                  {predictions.length === 0 ? (
                    <tr><td colSpan={4} style={{ textAlign: 'center', color: '#94a3b8' }}>No predictions available</td></tr>
                  ) : predictions.map(p => (
                    <tr key={p.prediction_id}>
                      <td>{p.shop_name}</td>
                      <td>{p.grain_type}</td>
                      <td style={{ fontWeight: 700, color: '#2563eb' }}>{p.predicted_demand_kg}</td>
                      <td>{p.prediction_month ? p.prediction_month.substring(0, 7) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
