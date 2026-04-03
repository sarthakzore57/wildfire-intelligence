import React, { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import { getCurrentUser } from './services/api';
import Alerts from './pages/Alerts';
import Dashboard from './pages/Dashboard';
import FireRiskMap from './pages/FireRiskMap';
import HistoricalData from './pages/HistoricalData';
import Login from './pages/Login';
import Profile from './pages/Profile';
import Register from './pages/Register';
import { AuthContext } from './context/AuthContext';

const FullScreenLoader = () => (
  <div className="app-shell flex min-h-screen items-center justify-center px-6">
    <div className="panel rounded-[2rem] px-8 py-7 text-center">
      <p className="eyebrow mb-3">Command Center</p>
      <h1 className="section-title text-3xl font-bold text-brand-100">Restoring your session</h1>
      <p className="mt-3 text-sm text-stone-300">Syncing alerts, watchlists, and your latest field context.</p>
    </div>
  </div>
);

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      const cachedUser = localStorage.getItem('user');

      if (!token) {
        setLoading(false);
        return;
      }

      if (cachedUser) {
        try {
          setUser(JSON.parse(cachedUser));
        } catch (error) {
          console.error('Error reading cached user:', error);
        }
      }

      try {
        const response = await getCurrentUser();
        const userData = response.data;
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      } catch (error) {
        console.error('Error validating token:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = (userData, token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const PrivateRoute = ({ element }) => {
    if (loading) return <FullScreenLoader />;
    return user ? element : <Navigate to="/login" replace />;
  };

  const AppLayout = ({ children }) => (
    <div className="app-shell">
      <Header />
      <div className="shell-container app-grid">
        <Sidebar />
        <main className="min-w-0 px-4 py-4 md:px-6 md:py-6">
          <div className="content-stack">{children}</div>
        </main>
      </div>
    </div>
  );

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={<PrivateRoute element={<AppLayout><Dashboard /></AppLayout>} />}
        />
        <Route
          path="/map"
          element={<PrivateRoute element={<AppLayout><FireRiskMap /></AppLayout>} />}
        />
        <Route
          path="/historical"
          element={<PrivateRoute element={<AppLayout><HistoricalData /></AppLayout>} />}
        />
        <Route
          path="/alerts"
          element={<PrivateRoute element={<AppLayout><Alerts /></AppLayout>} />}
        />
        <Route
          path="/profile"
          element={<PrivateRoute element={<AppLayout><Profile /></AppLayout>} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthContext.Provider>
  );
}

export default App;
