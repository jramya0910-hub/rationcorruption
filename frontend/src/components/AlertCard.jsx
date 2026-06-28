import React from 'react';

export default function AlertCard({ alert }) {
  const severityColors = {
    LOW:      { bg: '#f0fdf4', border: '#86efac', text: '#166534' },
    MEDIUM:   { bg: '#fefce8', border: '#fde047', text: '#854d0e' },
    HIGH:     { bg: '#fff7ed', border: '#fdba74', text: '#9a3412' },
    CRITICAL: { bg: '#fdf2f8', border: '#f0abfc', text: '#86198f' },
  };
  const colors = severityColors[alert.severity] || severityColors.LOW;

  return (
    <div style={{
      background: colors.bg,
      border: `1px solid ${colors.border}`,
      borderRadius: 8,
      padding: '14px 16px',
      marginBottom: 10,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div>
          <span style={{ fontWeight: 700, fontSize: 13, color: colors.text }}>
            [{alert.severity}] {alert.alert_type}
          </span>
          <p style={{ fontSize: 13, color: '#374151', marginTop: 4 }}>{alert.description}</p>
          <p style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>
            {alert.shop_name} · {new Date(alert.created_at).toLocaleDateString()}
          </p>
        </div>
        {alert.is_reviewed && (
          <span style={{ fontSize: 11, background: '#dcfce7', color: '#166534', padding: '2px 8px', borderRadius: 12, whiteSpace: 'nowrap' }}>
            Reviewed
          </span>
        )}
      </div>
    </div>
  );
}
