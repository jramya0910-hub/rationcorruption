import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', gap: 16 }}>
      <div style={{ fontSize: 64 }}>🌾</div>
      <h1 style={{ fontSize: 32, fontWeight: 800 }}>404</h1>
      <p style={{ color: '#64748b' }}>Page not found.</p>
      <Link className="btn btn-primary" to="/login">Go to Login</Link>
    </div>
  );
}
