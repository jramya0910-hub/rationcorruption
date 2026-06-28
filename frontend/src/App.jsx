import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext.jsx';
import LoginPage from './pages/LoginPage.jsx';
import BeneficiaryDashboard from './pages/beneficiary/BeneficiaryDashboard.jsx';
import ShopkeeperDashboard from './pages/shopkeeper/ShopkeeperDashboard.jsx';
import OfficerDashboard from './pages/officer/OfficerDashboard.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';

function ProtectedRoute({ children, role }) {
  const { auth } = useAuth();
  if (!auth) return <Navigate to="/login" replace />;
  if (role && auth.role !== role) return <Navigate to="/login" replace />;
  return children;
}

function RoleHome() {
  const { auth } = useAuth();
  if (!auth) return <Navigate to="/login" replace />;
  if (auth.role === 'beneficiary') return <Navigate to="/beneficiary" replace />;
  if (auth.role === 'shopkeeper')  return <Navigate to="/shopkeeper" replace />;
  if (auth.role === 'officer')     return <Navigate to="/officer" replace />;
  return <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"        element={<RoleHome />} />
        <Route path="/login"   element={<LoginPage />} />
        <Route
          path="/beneficiary"
          element={
            <ProtectedRoute role="beneficiary">
              <BeneficiaryDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/shopkeeper"
          element={
            <ProtectedRoute role="shopkeeper">
              <ShopkeeperDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/officer"
          element={
            <ProtectedRoute role="officer">
              <OfficerDashboard />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
