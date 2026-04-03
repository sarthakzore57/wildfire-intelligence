import React, { useContext, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { getCurrentUser, login } from '../services/api';

const Login = () => {
  const navigate = useNavigate();
  const { login: loginUser } = useContext(AuthContext);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setLoading(true);

    try {
      const response = await login(email, password);
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);

      const userResponse = await getCurrentUser();
      const userData = userResponse.data;
      loginUser(userData, access_token);
      navigate('/');
    } catch (requestError) {
      console.error('Login error:', requestError);
      localStorage.removeItem('token');

      if (requestError.response?.status === 400) {
        setError('Invalid email or password.');
      } else if (requestError.response?.status === 401) {
        setError('Login succeeded, but loading the profile failed. Please try again.');
      } else if (!requestError.response) {
        setError('Backend is not reachable on http://localhost:8000.');
      } else {
        setError('Something went wrong. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <section className="auth-hero">
          <div className="auth-orb auth-orb-one" />
          <div className="auth-orb auth-orb-two" />
          <div className="relative z-10">
          <p className="eyebrow">Forest Sentinel Platform</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <span className="auth-badge">Live risk intelligence</span>
            <span className="auth-badge">Map-first operations</span>
            <span className="auth-badge">Early warning workflow</span>
          </div>
          <h1 className="section-title mt-4 text-5xl font-bold text-[#fff8ef]">
            Modern wildfire intelligence, built to feel original and production-ready.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-[#fdebd7]">
            Sign in to monitor risk zones, run spread simulations, manage alert thresholds, and operate the refreshed command center.
          </p>

          <div className="mt-10 grid gap-4 sm:grid-cols-2">
            {[
              ['Risk map', 'Generate live fire-risk predictions directly from the map.'],
              ['Incident history', 'Review patterns, severity mix, and historical fire activity.'],
              ['Alert desk', 'Track unread notifications and operator response flow.'],
              ['Watchlist', 'Save critical regions and monitor them continuously.'],
            ].map(([title, copy]) => (
              <div key={title} className="panel-soft rounded-[1.5rem] p-4">
                <p className="text-lg font-semibold text-[#fff8ef]">{title}</p>
                <p className="mt-2 text-sm text-[#f7e8d5]">{copy}</p>
              </div>
            ))}
          </div>
          </div>
        </section>

        <section className="auth-form">
          <p className="eyebrow !text-brand-700">Welcome back</p>
          <h2 className="section-title mt-3 text-4xl font-bold text-[#231911]">Sign in to your account</h2>
          <p className="mt-3 text-sm text-stone-600">
            Access the latest operational view for fire risk, incidents, alerts, and personal watch settings.
          </p>

          {error ? (
            <div className="mt-6 rounded-[1.25rem] border border-danger-500/25 bg-danger-100/70 px-4 py-3 text-sm text-danger-700">
              {error}
            </div>
          ) : null}

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <label className="field">
              <span className="text-sm font-medium text-stone-700">Email address</span>
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
              />
            </label>

            <label className="field">
              <span className="text-sm font-medium text-stone-700">Password</span>
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
              />
            </label>

            <button type="submit" disabled={loading} className="primary-button w-full">
              {loading ? 'Signing in...' : 'Enter command center'}
            </button>
          </form>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
            <span className="text-stone-600">Need a new account?</span>
            <Link to="/register" className="font-semibold text-brand-700 hover:text-brand-800">
              Register here
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Login;
