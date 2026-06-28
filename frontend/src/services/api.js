import axios from 'axios';

// In production (Vercel) the API is served from the same domain at /api
// In development it proxies to localhost:8000 via vite.config.js
const BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({ baseURL: BASE });

// Attach JWT on every request
api.interceptors.request.use((config) => {
  try {
    const auth = JSON.parse(localStorage.getItem('ration_auth') || 'null');
    if (auth?.access_token) {
      config.headers.Authorization = `Bearer ${auth.access_token}`;
    }
  } catch {}
  return config;
});

// ── Auth ───────────────────────────────────────────────────────────────────
export const login  = (username, password, role) =>
  api.post('/auth/login', { username, password, role });

export const logout = () => api.post('/auth/logout');

// ── Beneficiary ────────────────────────────────────────────────────────────
export const getEntitlement       = (id)     => api.get(`/beneficiary/${id}/entitlement`);
export const getReceipts          = (id)     => api.get(`/beneficiary/${id}/receipts`);
export const getStockAvailability = (id)     => api.get(`/beneficiary/${id}/stock-availability`);
export const submitComplaint      = (data)   => api.post('/beneficiary/complaint', data);
export const getBeneficiaryComplaints = (id) => api.get(`/beneficiary/${id}/complaints`);

// ── Shopkeeper ─────────────────────────────────────────────────────────────
export const updateStock      = (data)    => api.post('/shop/stock/update', data);
export const scanTransaction  = (data)    => api.post('/shop/transaction/scan', data);
export const getInventory     = (shopId)  => api.get(`/shop/${shopId}/inventory`);
export const getTransactions  = (shopId)  => api.get(`/shop/${shopId}/transactions`);

// ── Officer ────────────────────────────────────────────────────────────────
export const getDashboard     = ()           => api.get('/officer/dashboard');
export const getAlerts        = ()           => api.get('/officer/alerts');
export const getRiskShops     = ()           => api.get('/officer/shops/risk');
export const getAllComplaints  = (status)     => api.get('/officer/complaints', { params: status ? { status } : {} });
export const getPredictions   = ()           => api.get('/officer/predictions');
export const resolveComplaint = (id)         => api.post('/officer/complaints/resolve', { complaint_id: id });
export const exportReport     = (format)     => api.get('/officer/report/export', { params: { format }, responseType: 'blob' });

// ── AI ─────────────────────────────────────────────────────────────────────
export const runFraudDetection    = (shopId)    => api.post('/ai/fraud-detection/run', { shop_id: shopId });
export const getRiskScore         = (shopId)    => api.get(`/ai/risk-score/${shopId}`);
export const predictStock         = (data)      => api.post('/ai/predict-stock', data);
export const categorizeComplaint  = (description) => api.post('/ai/categorize-complaint', { description });

export default api;
