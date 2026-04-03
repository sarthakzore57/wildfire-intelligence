import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../services/api';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    region_name: '',
    latitude: '',
    longitude: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((previous) => ({ ...previous, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (!formData.email || !formData.username || !formData.password) {
      setError('Please fill in all required fields.');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        email: formData.email,
        username: formData.username,
        password: formData.password,
      };

      if (formData.region_name) payload.region_name = formData.region_name;
      if (formData.latitude) payload.latitude = parseFloat(formData.latitude);
      if (formData.longitude) payload.longitude = parseFloat(formData.longitude);

      await register(payload);
      navigate('/login');
    } catch (requestError) {
      console.error('Registration error:', requestError);
      if (requestError.response?.data?.detail) {
        setError(requestError.response.data.detail);
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
          <p className="eyebrow">Create an operator account</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <span className="auth-badge">Regional watch setup</span>
            <span className="auth-badge">Alerts and thresholds</span>
            <span className="auth-badge">Cloud-backed profile</span>
          </div>
          <h1 className="section-title mt-4 text-5xl font-bold text-[#fff8ef]">
            Build your own wildfire monitoring profile and start tracking risk with a sharper interface.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-[#fdebd7]">
            Set a preferred region, keep alert thresholds under control, and use the same working backend with a fully refreshed product experience.
          </p>
          </div>
        </section>

        <section className="auth-form">
          <p className="eyebrow !text-brand-700">New operator</p>
          <h2 className="section-title mt-3 text-4xl font-bold text-[#231911]">Create your account</h2>
          <p className="mt-3 text-sm text-stone-600">
            Register once, then use the command center to review alerts, regions, and predictive mapping.
          </p>

          {error ? (
            <div className="mt-6 rounded-[1.25rem] border border-danger-500/25 bg-danger-100/70 px-4 py-3 text-sm text-danger-700">
              {error}
            </div>
          ) : null}

          <form onSubmit={handleSubmit} className="mt-8 grid gap-5">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="field">
                <span className="text-sm font-medium text-stone-700">Email</span>
                <input type="email" name="email" value={formData.email} onChange={handleChange} />
              </label>
              <label className="field">
                <span className="text-sm font-medium text-stone-700">Username</span>
                <input type="text" name="username" value={formData.username} onChange={handleChange} />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="field">
                <span className="text-sm font-medium text-stone-700">Password</span>
                <input type="password" name="password" value={formData.password} onChange={handleChange} />
              </label>
              <label className="field">
                <span className="text-sm font-medium text-stone-700">Confirm password</span>
                <input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} />
              </label>
            </div>

            <label className="field">
              <span className="text-sm font-medium text-stone-700">Preferred region</span>
              <input type="text" name="region_name" value={formData.region_name} onChange={handleChange} placeholder="Konkan coastal belt" />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="field">
                <span className="text-sm font-medium text-stone-700">Latitude</span>
                <input type="text" name="latitude" value={formData.latitude} onChange={handleChange} />
              </label>
              <label className="field">
                <span className="text-sm font-medium text-stone-700">Longitude</span>
                <input type="text" name="longitude" value={formData.longitude} onChange={handleChange} />
              </label>
            </div>

            <button type="submit" disabled={loading} className="primary-button w-full">
              {loading ? 'Creating account...' : 'Create operator account'}
            </button>
          </form>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
            <span className="text-stone-600">Already registered?</span>
            <Link to="/login" className="font-semibold text-brand-700 hover:text-brand-800">
              Sign in here
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Register;
