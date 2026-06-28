import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext.jsx';
import Navbar from '../../components/Navbar.jsx';
import {
  getInventory, getTransactions, updateStock, scanTransaction,
} from '../../services/api.js';

const GRAINS = ['RICE', 'WHEAT', 'SUGAR', 'OIL'];

export default function ShopkeeperDashboard() {
  const { auth } = useAuth();
  const shopId = auth?.user_id;

  const [inventory, setInventory]     = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');

  const [stockForm, setStockForm] = useState({ grain_type: 'RICE', stock_received_kg: '', stock_distributed_kg: '' });
  const [stockMsg, setStockMsg]   = useState('');

  const [txnForm, setTxnForm] = useState({ beneficiary_id: '', grain_type: 'RICE', quantity_given_kg: '', qr_scan_verified: true });
  const [txnMsg, setTxnMsg]   = useState('');
  const [txnLoading, setTxnLoading] = useState(false);
  const [stockLoading, setStockLoading] = useState(false);

  const [activeTab, setActiveTab] = useState('inventory');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [inv, txns] = await Promise.all([
        getInventory(shopId),
        getTransactions(shopId),
      ]);
      setInventory(inv.data.data.inventory || []);
      setTransactions(txns.data.data.transactions || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [shopId]);

  useEffect(() => { load(); }, [load]);

  async function handleStockUpdate(e) {
    e.preventDefault();
    setStockLoading(true); setStockMsg('');
    try {
      const payload = { grain_type: stockForm.grain_type };
      if (stockForm.stock_received_kg)    payload.stock_received_kg    = parseFloat(stockForm.stock_received_kg);
      if (stockForm.stock_distributed_kg) payload.stock_distributed_kg = parseFloat(stockForm.stock_distributed_kg);
      await updateStock(payload);
      setStockMsg('Stock updated successfully!');
      setStockForm({ grain_type: 'RICE', stock_received_kg: '', stock_distributed_kg: '' });
      load();
    } catch (err) {
      setStockMsg(err.response?.data?.detail || 'Update failed');
    } finally {
      setStockLoading(false);
    }
  }

  async function handleScan(e) {
    e.preventDefault();
    setTxnLoading(true); setTxnMsg('');
    try {
      await scanTransaction({
        beneficiary_id: txnForm.beneficiary_id,
        grain_type: txnForm.grain_type,
        quantity_given_kg: parseFloat(txnForm.quantity_given_kg),
        qr_scan_verified: txnForm.qr_scan_verified,
      });
      setTxnMsg('Transaction recorded!');
      setTxnForm({ beneficiary_id: '', grain_type: 'RICE', quantity_given_kg: '', qr_scan_verified: true });
      load();
    } catch (err) {
      setTxnMsg(err.response?.data?.detail || 'Transaction failed');
    } finally {
      setTxnLoading(false);
    }
  }

  const tabs = [
    { id: 'inventory',    label: '📦 Inventory' },
    { id: 'update-stock', label: '➕ Update Stock' },
    { id: 'scan-txn',     label: '📲 Record Transaction' },
    { id: 'history',      label: '📋 Transaction History' },
  ];

  if (loading) return (
    <>
      <Navbar title="Shopkeeper Portal" />
      <div className="spinner-overlay"><div className="spinner" /></div>
    </>
  );

  return (
    <>
      <Navbar title="Shopkeeper Portal" />
      <div className="main-content" style={{ maxWidth: 1000, margin: '0 auto' }}>
        {error && <div className="error-msg">{error}</div>}

        {/* Tab Nav */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '2px solid #e2e8f0', paddingBottom: 0 }}>
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              style={{
                padding: '10px 16px', border: 'none', background: 'none',
                cursor: 'pointer', fontSize: 13, fontWeight: 600,
                color: activeTab === t.id ? '#2563eb' : '#64748b',
                borderBottom: activeTab === t.id ? '2px solid #2563eb' : '2px solid transparent',
                marginBottom: -2,
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Inventory Tab */}
        {activeTab === 'inventory' && (
          <div>
            {inventory.some(i => i.low_stock_alert) && (
              <div className="error-msg" style={{ marginBottom: 16 }}>
                ⚠️ Low stock alert for: {inventory.filter(i => i.low_stock_alert).map(i => i.grain_type).join(', ')}
              </div>
            )}
            <div className="stat-grid" style={{ marginBottom: 20 }}>
              {inventory.map(i => (
                <div key={i.grain_type} className="stat-card" style={{ borderLeft: `4px solid ${i.low_stock_alert ? '#dc2626' : '#16a34a'}` }}>
                  <div className="label">{i.grain_type} {i.low_stock_alert ? '🔴' : '🟢'}</div>
                  <div className="value blue">{i.remaining_stock_kg.toFixed(1)} kg</div>
                  <p style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                    Received: {i.stock_received_kg} kg · Distributed: {i.stock_distributed_kg} kg
                  </p>
                </div>
              ))}
            </div>
            <div className="card">
              <p className="section-title">Inventory Details</p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Grain</th><th>Received (kg)</th><th>Distributed (kg)</th><th>Remaining (kg)</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {inventory.map(i => (
                      <tr key={i.grain_type}>
                        <td style={{ fontWeight: 600 }}>{i.grain_type}</td>
                        <td>{i.stock_received_kg}</td>
                        <td>{i.stock_distributed_kg}</td>
                        <td style={{ fontWeight: 700, color: i.low_stock_alert ? '#dc2626' : '#16a34a' }}>
                          {i.remaining_stock_kg.toFixed(1)}
                        </td>
                        <td>
                          <span className={`badge ${i.low_stock_alert ? 'badge-high' : 'badge-low'}`}>
                            {i.low_stock_alert ? 'LOW STOCK' : 'OK'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Update Stock Tab */}
        {activeTab === 'update-stock' && (
          <div className="card" style={{ maxWidth: 480 }}>
            <p className="section-title">Update Stock</p>
            {stockMsg && <div className={stockMsg.includes('success') ? 'success-msg' : 'error-msg'}>{stockMsg}</div>}
            <form onSubmit={handleStockUpdate}>
              <div className="form-group">
                <label>Grain Type</label>
                <select value={stockForm.grain_type} onChange={e => setStockForm(p => ({ ...p, grain_type: e.target.value }))}>
                  {GRAINS.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Stock Received (kg) — add to existing</label>
                <input type="number" step="0.1" min="0" value={stockForm.stock_received_kg}
                  onChange={e => setStockForm(p => ({ ...p, stock_received_kg: e.target.value }))}
                  placeholder="e.g. 100" />
              </div>
              <div className="form-group">
                <label>Stock Distributed (kg) — add to existing</label>
                <input type="number" step="0.1" min="0" value={stockForm.stock_distributed_kg}
                  onChange={e => setStockForm(p => ({ ...p, stock_distributed_kg: e.target.value }))}
                  placeholder="e.g. 25" />
              </div>
              <button className="btn btn-primary" type="submit" disabled={stockLoading}>
                {stockLoading ? 'Updating…' : 'Update Stock'}
              </button>
            </form>
          </div>
        )}

        {/* Scan Transaction Tab */}
        {activeTab === 'scan-txn' && (
          <div className="card" style={{ maxWidth: 480 }}>
            <p className="section-title">Record Transaction</p>
            {txnMsg && <div className={txnMsg.includes('recorded') ? 'success-msg' : 'error-msg'}>{txnMsg}</div>}
            <form onSubmit={handleScan}>
              <div className="form-group">
                <label>Beneficiary ID (UUID from QR scan)</label>
                <input type="text" value={txnForm.beneficiary_id} onChange={e => setTxnForm(p => ({ ...p, beneficiary_id: e.target.value }))}
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" required />
              </div>
              <div className="form-group">
                <label>Grain Type</label>
                <select value={txnForm.grain_type} onChange={e => setTxnForm(p => ({ ...p, grain_type: e.target.value }))}>
                  {GRAINS.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Quantity Distributed (kg)</label>
                <input type="number" step="0.1" min="0.1" value={txnForm.quantity_given_kg}
                  onChange={e => setTxnForm(p => ({ ...p, quantity_given_kg: e.target.value }))}
                  placeholder="e.g. 5" required />
              </div>
              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input type="checkbox" checked={txnForm.qr_scan_verified}
                    onChange={e => setTxnForm(p => ({ ...p, qr_scan_verified: e.target.checked }))}
                    style={{ width: 'auto' }} />
                  QR Code Verified
                </label>
              </div>
              <button className="btn btn-primary" type="submit" disabled={txnLoading}>
                {txnLoading ? 'Recording…' : 'Record Transaction'}
              </button>
            </form>
          </div>
        )}

        {/* Transaction History Tab */}
        {activeTab === 'history' && (
          <div className="card">
            <p className="section-title">Transaction History ({transactions.length})</p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Date</th><th>Beneficiary</th><th>Ration Card</th><th>Grain</th><th>Qty (kg)</th><th>QR</th></tr>
                </thead>
                <tbody>
                  {transactions.length === 0 ? (
                    <tr><td colSpan={6} style={{ textAlign: 'center', color: '#94a3b8' }}>No transactions</td></tr>
                  ) : transactions.map(t => (
                    <tr key={t.transaction_id}>
                      <td>{new Date(t.transaction_date).toLocaleDateString()}</td>
                      <td>{t.beneficiary_name}</td>
                      <td style={{ fontSize: 12, color: '#64748b' }}>{t.ration_card_number}</td>
                      <td>{t.grain_type}</td>
                      <td style={{ fontWeight: 600 }}>{t.quantity_given_kg}</td>
                      <td>{t.qr_scan_verified ? '✅' : '❌'}</td>
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
