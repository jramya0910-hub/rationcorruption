import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function LineChart({ data, title }) {
  if (!data || data.length === 0) return <p style={{ color: '#64748b', fontSize: 13 }}>No data</p>;

  const chartData = {
    labels: data.map(d => d.label || d.month),
    datasets: [{
      label: title || 'Trend',
      data: data.map(d => d.value || d.total_kg),
      borderColor: '#7c3aed',
      backgroundColor: 'rgba(124,58,237,.1)',
      tension: 0.4,
      fill: true,
    }],
  };

  return (
    <Line
      data={chartData}
      options={{
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      }}
    />
  );
}
