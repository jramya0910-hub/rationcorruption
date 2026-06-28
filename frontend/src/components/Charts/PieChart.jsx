import React from 'react';
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
} from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

const COLORS = ['#2563eb', '#7c3aed', '#16a34a', '#d97706', '#dc2626'];

export default function PieChart({ data, title }) {
  if (!data || data.length === 0) return <p style={{ color: '#64748b', fontSize: 13 }}>No data</p>;

  const chartData = {
    labels: data.map(d => d.label || d.type),
    datasets: [{
      data: data.map(d => d.value || d.count),
      backgroundColor: COLORS.slice(0, data.length),
      borderWidth: 2,
      borderColor: '#fff',
    }],
  };

  return (
    <div style={{ maxWidth: 280, margin: '0 auto' }}>
      <Pie
        data={chartData}
        options={{
          responsive: true,
          plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } },
        }}
      />
    </div>
  );
}
