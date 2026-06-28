import React from 'react';

export default function RiskBadge({ level }) {
  const map = {
    LOW:      'badge badge-low',
    MEDIUM:   'badge badge-medium',
    HIGH:     'badge badge-high',
    CRITICAL: 'badge badge-critical',
  };
  return <span className={map[level] || 'badge'}>{level}</span>;
}
