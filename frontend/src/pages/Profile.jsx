import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { getCurrentUser, updateCurrentUser } from '../services/api';

const Profile = () => {
  const { user: authUser, login } = useContext(AuthContext);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    region_name: '',
    latitude: '',
    longitude: '',
    alert_threshold: 0.7,
    email_alerts: true,
    sms_alerts: false,
    phone_number: '',
    newPassword: '',
    confirmPassword: '',
  });

  useEffect(() => {
    const fetchUserProfile = async () => {
      setLoading(true);
      try {
        const response = await getCurrentUser();
        const userData = response.data;
        setUser(userData);
        setFormData({
          username: userData.username || '',
          email: userData.email || '',
          region_name: userData.region_name || '',
          latitude: userData.latitude || '',
          longitude: userData.longitude || '',
          alert_threshold: userData.alert_threshold || 0.7,
          email_alerts: userData.email_alerts ?? true,
          sms_alerts: userData.sms_alerts ?? false,
          phone_number: userData.phone_number || '',
          newPassword: '',
          confirmPassword: '',
        });
      } catch (fetchError) {
        console.error('Error fetching user profile:', fetchError);
        setError('Unable to load profile details right now.');
      } finally {
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, []);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setFormData((previous) => ({
      ...previous,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSaveProfile = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const payload = {
        username: formData.username,
        region_name: formData.region_name,
        latitude: formData.latitude ? Number(formData.latitude) : null,
        longitude: formData.longitude ? Number(formData.longitude) : null,
        alert_threshold: Number(formData.alert_threshold),
        email_alerts: formData.email_alerts,
        sms_alerts: formData.sms_alerts,
        phone_number: formData.phone_number,
      };

      if (formData.newPassword) {
        if (formData.newPassword !== formData.confirmPassword) {
          throw new Error('Passwords do not match.');
        }
        payload.password = formData.newPassword;
      }

      const response = await updateCurrentUser(payload);
      const updatedUser = response.data;

      setUser(updatedUser);
      login({ ...authUser, ...updatedUser }, localStorage.getItem('token'));
      setFormData((previous) => ({
        ...previous,
        newPassword: '',
        confirmPassword: '',
      }));
      setSuccess('Profile settings updated successfully.');
    } catch (updateError) {
      console.error('Error updating profile:', updateError);
      setError(updateError.message || 'Unable to save profile changes.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !user) {
    return (
      <div className="panel rounded-[1.85rem] p-6 text-sm text-stone-300">
        Loading operator profile...
      </div>
    );
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.82fr_1.18fr]">
      <section className="space-y-6">
        <div className="hero-card rounded-[2rem] px-6 py-7">
          <div className="relative z-10">
            <p className="eyebrow">Operator identity</p>
            <h1 className="section-title mt-2 text-4xl font-bold text-brand-50">{user?.username || 'Field Operator'}</h1>
            <p className="mt-3 text-sm text-stone-200">{user?.email}</p>
            <div className="mt-6 grid gap-3">
              <div className="panel-soft rounded-[1.25rem] p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-stone-400">Monitored region</p>
                <p className="mt-2 text-lg font-semibold text-brand-50">{formData.region_name || 'Not set yet'}</p>
              </div>
              <div className="panel-soft rounded-[1.25rem] p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-stone-400">Alert threshold</p>
                <p className="mt-2 text-lg font-semibold text-brand-50">
                  {(Number(formData.alert_threshold) * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="panel rounded-[1.85rem] p-5 md:p-6">
          <p className="eyebrow">Added extra</p>
          <h2 className="section-title mt-2 text-2xl font-bold text-brand-100">Response preferences</h2>
          <div className="mt-5 space-y-3">
            <div className="panel-soft rounded-[1.2rem] p-4 text-sm text-stone-300">
              Email alerts are <span className="font-semibold text-brand-100">{formData.email_alerts ? 'enabled' : 'disabled'}</span>
            </div>
            <div className="panel-soft rounded-[1.2rem] p-4 text-sm text-stone-300">
              SMS alerts are <span className="font-semibold text-brand-100">{formData.sms_alerts ? 'enabled' : 'disabled'}</span>
            </div>
            <div className="panel-soft rounded-[1.2rem] p-4 text-sm text-stone-300">
              Preferred coordinates: {formData.latitude || '--'}, {formData.longitude || '--'}
            </div>
          </div>
        </div>
      </section>

      <section className="panel rounded-[1.85rem] p-5 md:p-6">
        <p className="eyebrow">Settings studio</p>
        <h2 className="section-title mt-2 text-3xl font-bold text-brand-100">Profile, thresholds, and password</h2>
        <p className="mt-3 text-sm text-stone-300">
          Keep your account data, target region, and alert controls aligned with how you monitor wildfire activity.
        </p>

        {error ? (
          <div className="mt-5 rounded-[1.3rem] border border-danger-500/30 bg-danger-500/10 p-4 text-sm text-danger-100">
            {error}
          </div>
        ) : null}

        {success ? (
          <div className="mt-5 rounded-[1.3rem] border border-pine-500/30 bg-pine-500/10 p-4 text-sm text-pine-100">
            {success}
          </div>
        ) : null}

        <form onSubmit={handleSaveProfile} className="mt-6 grid gap-5">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="field text-stone-200">
              <span className="text-sm text-stone-300">Username</span>
              <input name="username" value={formData.username} onChange={handleChange} />
            </label>
            <label className="field text-stone-200">
              <span className="text-sm text-stone-300">Email</span>
              <input name="email" value={formData.email} disabled />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <label className="field text-stone-200 md:col-span-1">
              <span className="text-sm text-stone-300">Region name</span>
              <input name="region_name" value={formData.region_name} onChange={handleChange} placeholder="Western Ghats sector" />
            </label>
            <label className="field text-stone-200">
              <span className="text-sm text-stone-300">Latitude</span>
              <input name="latitude" value={formData.latitude} onChange={handleChange} placeholder="18.52" />
            </label>
            <label className="field text-stone-200">
              <span className="text-sm text-stone-300">Longitude</span>
              <input name="longitude" value={formData.longitude} onChange={handleChange} placeholder="73.85" />
            </label>
          </div>

          <div className="panel-soft rounded-[1.35rem] p-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-brand-100">Alert threshold {(Number(formData.alert_threshold) * 100).toFixed(0)}%</p>
                <p className="mt-1 text-xs text-stone-400">Lower values alert more aggressively. Higher values focus only on major risk spikes.</p>
              </div>
              <div className="w-full max-w-md">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  name="alert_threshold"
                  value={formData.alert_threshold}
                  onChange={handleChange}
                  className="w-full"
                />
              </div>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <label className="panel-soft flex items-center gap-3 rounded-[1rem] p-4">
                <input type="checkbox" name="email_alerts" checked={formData.email_alerts} onChange={handleChange} />
                <span className="text-sm text-stone-200">Enable email alerts</span>
              </label>
              <label className="panel-soft flex items-center gap-3 rounded-[1rem] p-4">
                <input type="checkbox" name="sms_alerts" checked={formData.sms_alerts} onChange={handleChange} />
                <span className="text-sm text-stone-200">Enable SMS alerts</span>
              </label>
            </div>

            <label className="field mt-4 text-stone-200">
              <span className="text-sm text-stone-300">Phone number</span>
              <input name="phone_number" value={formData.phone_number} onChange={handleChange} placeholder="+91 98xxxxxx12" />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="field text-stone-200">
              <span className="text-sm text-stone-300">New password</span>
              <input type="password" name="newPassword" value={formData.newPassword} onChange={handleChange} />
            </label>
            <label className="field text-stone-200">
              <span className="text-sm text-stone-300">Confirm password</span>
              <input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} />
            </label>
          </div>

          <div className="flex justify-end">
            <button type="submit" className="primary-button" disabled={loading}>
              {loading ? 'Saving...' : 'Save operator profile'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
};

export default Profile;
