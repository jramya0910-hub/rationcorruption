import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { login as apiLogin } from '../services/api.js';

const ROLE_LABELS = { beneficiary: 'Beneficiary', shopkeeper: 'Shopkeeper', officer: 'Government Officer' };

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [role, setRole]         = useState('beneficiary');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  const placeholders = {
    beneficiary: 'Ration Card Number (e.g. TN-CHN-001001)',
    shopkeeper:  'Shop Name',
    officer:     'Officer Email',
  };

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await apiLogin(username, password, role);
      const data = res.data.data;
      login(data);
      if (data.role === 'beneficiary') navigate('/beneficiary');
      else if (data.role === 'shopkeeper') navigate('/shopkeeper');
      else navigate('/officer');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.logo}>🌾</div>
          <h1 style={styles.title}>Smart Ration Guardian</h1>
          <p style={styles.subtitle}>AI-Powered Public Distribution Monitoring</p>
        </div>

        {/* Role Tabs */}
        <div style={styles.tabs}>
          {Object.entries(ROLE_LABELS).map(([key, label]) => (
            <button
              key={key}
              style={{ ...styles.tab, ...(role === key ? styles.tabActive : {}) }}
              onClick={() => { setRole(key); setError(''); }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={styles.form}>
          {error && <div className="error-msg">{error}</div>}

          <div className="form-group">
            <label>{role === 'officer' ? 'Email' : role === 'shopkeeper' ? 'Shop Name' : 'Ration Card Number'}</label>
            <input
              type={role === 'officer' ? 'email' : 'text'}
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder={placeholders[role]}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: '100%', justifyContent: 'center', padding: '11px' }}>
            {loading ? <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> : `Sign In as ${ROLE_LABELS[role]}`}
          </button>
        </form>

        <p style={styles.hint}>
          Demo: Beneficiary → <code>TN-CHN-001001</code> / <code>ben123</code>
          <br />Officer → <code>officer@tnration.gov.in</code> / <code>officer123</code>
        </p>
      </div>
    </div>
  );
}

const styles = {
  page:     { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)', padding: 16 },
  card:     { background: '#fff', borderRadius: 12, padding: '40px 36px', width: '100%', maxWidth: 420, boxShadow: '0 20px 60px rgba(0,0,0,.2)' },
  header:   { textAlign: 'center', marginBottom: 28 },
  logo:     { fontSize: 48, marginBottom: 8 },
  title:    { fontSize: 22, fontWeight: 800, color: '#1e2533', marginBottom: 4 },
  subtitle: { fontSize: 13, color: '#64748b' },
  tabs:     { display: 'flex', gap: 4, marginBottom: 24, background: '#f1f5f9', borderRadius: 8, padding: 4 },
  tab:      { flex: 1, padding: '7px 4px', border: 'none', background: 'transparent', borderRadius: 6, cursor: 'pointer', fontSize: 12, fontWeight: 500, color: '#64748b', transition: 'all .15s' },
  tabActive:{ background: '#fff', color: '#2563eb', fontWeight: 700, boxShadow: '0 1px 3px rgba(0,0,0,.1)' },
  form:     { marginBottom: 16 },
  hint:     { fontSize: 11.5, color: '#94a3b8', textAlign: 'center', lineHeight: 1.8 },
};
