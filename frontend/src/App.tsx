import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { MandatoryFeedback } from './components/MandatoryFeedback';
import { LoadingState } from './components/UIStates';

import { Login } from './pages/Login';
import { Rooms } from './pages/Rooms';
import { Room } from './pages/Room';
import { Classmates } from './pages/Classmates';
import { Friends } from './pages/Friends';
import { Learn } from './pages/Learn';
import { Practice } from './pages/Practice';
import { MyProfile } from './pages/MyProfile';

const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) {
    return <LoadingState message="Restoring your session..." />;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
      <MandatoryFeedback />
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

          {/* Protected Routes */}
          <Route path="/rooms" element={<ProtectedLayout><Rooms /></ProtectedLayout>} />
          <Route path="/rooms/:id" element={<ProtectedLayout><Room /></ProtectedLayout>} />
          <Route path="/classmates" element={<ProtectedLayout><Classmates /></ProtectedLayout>} />
          <Route path="/friends" element={<ProtectedLayout><Friends /></ProtectedLayout>} />
          <Route path="/learn" element={<ProtectedLayout><Learn /></ProtectedLayout>} />
          <Route path="/practice" element={<ProtectedLayout><Practice /></ProtectedLayout>} />
          <Route path="/my-profile" element={<ProtectedLayout><MyProfile /></ProtectedLayout>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/rooms" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
