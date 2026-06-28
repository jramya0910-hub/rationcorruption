import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { logout as apiLogout } from '../services/api.js';

export default function Navbar({ title }) {
  const { auth, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    try { await apiLogout(); } catch {}
    logout();
    navigate('/login');
  }

  return (
    <nav style={styles.nav}>
      <div style={styles.left}>
        <span style={styles.logo}>🌾</span>
        <span style={styles.title}>{title || 'Smart Ration Guardian'}</span>
      </div>
      <div style={styles.right}>
        {auth && (
          <>
            <span style={styles.user}>{auth.name}</span>
            <button className="btn btn-ghost" onClick={handleLogout} style={{ fontSize: 12, padding: '5px 12px' }}>
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
}

const styles = {
  nav:   { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', height: 56, background: '#1e3a5f', color: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,.2)', position: 'sticky', top: 0, zIndex: 100 },
  left:  { display: 'flex', alignItems: 'center', gap: 10 },
  logo:  { fontSize: 22 },
  title: { fontWeight: 700, fontSize: 16, letterSpacing: '.01em' },
  right: { display: 'flex', alignItems: 'center', gap: 12 },
  user:  { fontSize: 13, color: '#cbd5e1' },
};
