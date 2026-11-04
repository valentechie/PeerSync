import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { LoadingState } from './components/UIStates';

import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { FindPartners } from './pages/FindPartners';
import { PartnerProfile } from './pages/PartnerProfile';
import { MySessions } from './pages/MySessions';
import { StudyRoom } from './pages/StudyRoom';
import { SessionSummary } from './pages/SessionSummary';
import { MyProgress } from './pages/MyProgress';
import { MyProfile } from './pages/MyProfile';
import { Settings } from './pages/Settings';

const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) {
    return <LoadingState message="Recuperando tu sesión..." />;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
    </div>
  );
};

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes */}
          <Route path="/dashboard" element={<ProtectedLayout><Dashboard /></ProtectedLayout>} />
          <Route path="/find-partners" element={<ProtectedLayout><FindPartners /></ProtectedLayout>} />
          <Route path="/partner/:id" element={<ProtectedLayout><PartnerProfile /></ProtectedLayout>} />
          <Route path="/my-sessions" element={<ProtectedLayout><MySessions /></ProtectedLayout>} />
          <Route path="/study-room/:id" element={<ProtectedLayout><StudyRoom /></ProtectedLayout>} />
          <Route path="/session-summary/:id" element={<ProtectedLayout><SessionSummary /></ProtectedLayout>} />
          <Route path="/my-progress" element={<ProtectedLayout><MyProgress /></ProtectedLayout>} />
          <Route path="/my-profile" element={<ProtectedLayout><MyProfile /></ProtectedLayout>} />
          <Route path="/settings" element={<ProtectedLayout><Settings /></ProtectedLayout>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
