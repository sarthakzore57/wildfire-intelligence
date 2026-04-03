import React, { useContext, useMemo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../context/AuthContext';

const pageCopy = {
  '/': {
    label: 'Operational View',
    title: 'Wildfire command center',
    summary: 'Track live risk, active incidents, and user-facing alerts from one modern surface.',
  },
  '/map': {
    label: 'Geospatial View',
    title: 'Risk mapping and spread simulation',
    summary: 'Inspect zones, generate fresh predictions, and build a watchlist directly from the map.',
  },
  '/historical': {
    label: 'Historical View',
    title: 'Incident history and trend analysis',
    summary: 'Review patterns, severity distribution, and historical timing for incident planning.',
  },
  '/alerts': {
    label: 'Notification View',
    title: 'Alert feed and action queue',
    summary: 'Triage unread risk notifications and keep critical updates from being missed.',
  },
  '/profile': {
    label: 'Operator Settings',
    title: 'Profile, thresholds, and response preferences',
    summary: 'Keep account details and alert channels aligned with how you want to monitor regions.',
  },
};

const Header = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

  const currentPage = useMemo(
    () => pageCopy[location.pathname] || pageCopy['/'],
    [location.pathname]
  );

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 border-b border-white/8 bg-[rgba(20,15,13,0.78)] backdrop-blur-xl">
      <div className="shell-container flex flex-wrap items-center justify-between gap-5 px-4 py-4 md:px-6">
        <div className="min-w-0">
          <Link to="/" className="inline-flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-pine-500 text-[#fff8ef] shadow-lg shadow-brand-900/25">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M14.18 3.14c-.39-.41-1.05-.24-1.23.3l-.31.9c-.55 1.64-1.29 3.21-2.22 4.67-.66 1.03-1.64 2.32-2.75 3.1A5.16 5.16 0 0 0 5.5 16.4C5.5 19.49 7.96 22 11 22s5.5-2.51 5.5-5.6c0-1.82-.81-3.1-1.87-4.42-.91-1.12-1.82-2.27-2.09-4.14l-.33-2.2c-.08-.56.57-.93 1.04-.59 1.06.78 1.97 1.76 2.72 2.87.24.36.74.33.94-.05.46-.86.69-1.82.69-2.9 0-2.17-1.01-4.07-2.42-5.43Z" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="eyebrow">Forest Sentinel</p>
              <h1 className="section-title truncate text-xl font-bold text-brand-100">{currentPage.title}</h1>
            </div>
          </Link>
          <p className="mt-2 max-w-3xl text-sm text-stone-300">{currentPage.summary}</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="panel-soft hidden rounded-full px-4 py-2 text-sm text-brand-50 md:flex md:items-center md:gap-3">
            <span className="eyebrow !text-[0.62rem] !tracking-[0.18em]">{currentPage.label}</span>
            <span className="status-dot bg-pine-400 shadow-[0_0_12px_rgba(72,186,130,0.85)]" />
            <span className="text-stone-200">Backend healthy</span>
          </div>

          <div className="panel-soft hidden rounded-full px-4 py-2 text-sm text-stone-200 xl:flex xl:items-center xl:gap-3">
            <span className="eyebrow !text-[0.62rem] !tracking-[0.18em]">Monitoring</span>
            <span>{user?.region_name || 'No primary region set'}</span>
          </div>

          <div className="panel-soft flex items-center gap-3 rounded-full px-3 py-2">
            <div className="grid h-11 w-11 place-items-center rounded-full bg-gradient-to-br from-night-500 to-brand-500 text-sm font-extrabold text-white">
              {(user?.username || user?.email || 'U').charAt(0).toUpperCase()}
            </div>
            <div className="hidden text-right sm:block">
              <p className="text-sm font-semibold text-brand-50">{user?.username || 'Field Operator'}</p>
              <p className="text-xs text-stone-400">{user?.email}</p>
            </div>
            <Link to="/profile" className="secondary-button hidden sm:inline-flex">
              Profile
            </Link>
            <button onClick={handleLogout} className="secondary-button">
              Sign out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
