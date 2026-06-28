import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function BarChart({ data, title }) {
  if (!data || data.length === 0) return <p style={{ color: '#64748b', fontSize: 13 }}>No data</p>;

  const chartData = {
    labels: data.map(d => d.label || d.shop_name),
    datasets: [{
      label: title || 'Value',
      data: data.map(d => d.value || d.distributed_kg),
      backgroundColor: '#2563eb',
      borderRadius: 4,
    }],
  };

  return (
    <Bar
      data={chartData}
      options={{
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      }}
    />
  );
}
