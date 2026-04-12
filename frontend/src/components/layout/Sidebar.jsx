import React, { useContext, useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AuthContext } from '../../context/AuthContext';
import { getAlerts, getSavedRegions } from '../../services/api';

const navItems = [
  {
    path: '/',
    name: 'Overview',
    caption: 'Status and key metrics',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h4A2.5 2.5 0 0 1 13 5.5v4A2.5 2.5 0 0 1 10.5 12h-4A2.5 2.5 0 0 1 4 9.5v-4ZM15 5.5A2.5 2.5 0 0 1 17.5 3h.5A3 3 0 0 1 21 6v3.5a2.5 2.5 0 0 1-2.5 2.5h-1A2.5 2.5 0 0 1 15 9.5v-4ZM4 16.5A2.5 2.5 0 0 1 6.5 14h1A2.5 2.5 0 0 1 10 16.5v4A2.5 2.5 0 0 1 7.5 23h-1A2.5 2.5 0 0 1 4 20.5v-4ZM12 16.5a2.5 2.5 0 0 1 2.5-2.5H18a3 3 0 0 1 3 3v3.5a2.5 2.5 0 0 1-2.5 2.5h-4A2.5 2.5 0 0 1 12 20.5v-4Z" />
      </svg>
    ),
  },
  {
    path: '/map',
    name: 'Risk Map',
    caption: 'Map estimates and watchlist',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="m15 4 5 2v14l-5-2-6 2-5-2V4l5 2 6-2Zm-5 3.17-3-1.2v10.86l3 1.2V7.17Zm2 10.86 2-0.67V6.5l-2 .67v10.86Z" />
      </svg>
    ),
  },
  {
    path: '/historical',
    name: 'History Lab',
    caption: 'Incident charts and ledger',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 3a9 9 0 1 0 8.95 10h-2.04A7 7 0 1 1 12 5v3l4-4-4-4v3Zm-1 5v5.41l3.3 3.3 1.4-1.42-2.7-2.7V8H11Z" />
      </svg>
    ),
  },
  {
    path: '/alerts',
    name: 'Alerts',
    caption: 'Unread queue and review',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2a6 6 0 0 1 6 6v3.28c0 .53.21 1.04.59 1.41l1.72 1.72A1 1 0 0 1 19.6 16H4.4a1 1 0 0 1-.71-1.71l1.72-1.72A2 2 0 0 0 6 11.28V8a6 6 0 0 1 6-6Zm0 20a3 3 0 0 1-2.82-2h5.64A3 3 0 0 1 12 22Z" />
      </svg>
    ),
  },
  {
    path: '/profile',
    name: 'Profile',
    caption: 'Thresholds and account',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5Z" />
      </svg>
    ),
  },
];

const Sidebar = () => {
  const location = useLocation();
  const { user } = useContext(AuthContext);
  const [unreadAlerts, setUnreadAlerts] = useState(0);
  const [savedRegions, setSavedRegions] = useState([]);

  useEffect(() => {
    if (!user) return undefined;

    const loadSidebarData = async () => {
      try {
        const [alertResponse, savedRegionsResponse] = await Promise.all([
          getAlerts({ is_read: false }),
          getSavedRegions(),
        ]);
        setUnreadAlerts(alertResponse.data.length);
        setSavedRegions(savedRegionsResponse.data.slice(0, 3));
      } catch (error) {
        console.error('Error loading sidebar data:', error);
      }
    };

    loadSidebarData();
    const intervalId = setInterval(loadSidebarData, 60000);
    return () => clearInterval(intervalId);
  }, [user]);

  const locationSnapshot = useMemo(() => {
    if (!user) return 'No watch location saved yet';
    if (user.region_name) return user.region_name;
    if (user.latitude && user.longitude) return `${Number(user.latitude).toFixed(2)}, ${Number(user.longitude).toFixed(2)}`;
    return 'No watch location saved yet';
  }, [user]);

  return (
    <>
      <div className="mobile-nav panel rounded-[1.5rem] p-2 lg:hidden">
        {navItems.map((item) => {
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center gap-2 rounded-[1.15rem] px-2 py-3 text-center transition ${
                active
                  ? 'bg-gradient-to-b from-brand-500/32 to-pine-500/18 text-brand-50'
                  : 'text-stone-300 hover:bg-white/6 hover:text-brand-50'
              }`}
            >
              <span className={`rounded-2xl p-2 ${active ? 'bg-white/12' : 'bg-white/5'}`}>{item.icon}</span>
              <span className="text-[0.68rem] font-semibold leading-4">{item.name}</span>
            </Link>
          );
        })}
      </div>

      <aside className="hidden border-r border-white/8 bg-[rgba(16,12,10,0.54)] px-4 py-5 backdrop-blur-xl lg:block">
        <div className="space-y-5">
        <div className="panel rounded-[1.8rem] p-5">
          <p className="eyebrow">Operator</p>
          <h2 className="section-title mt-3 text-2xl font-bold text-brand-100">
            {user?.username || 'Field Operator'}
          </h2>
          <p className="mt-2 text-sm text-stone-300">{locationSnapshot}</p>

          <div className="mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-white/5 p-3">
              <p className="text-xs uppercase tracking-[0.18em] text-stone-400">Unread</p>
              <p className="mt-2 text-2xl font-bold text-brand-50">{unreadAlerts}</p>
            </div>
            <div className="rounded-2xl bg-white/5 p-3">
              <p className="text-xs uppercase tracking-[0.18em] text-stone-400">Watchlist</p>
              <p className="mt-2 text-2xl font-bold text-brand-50">{savedRegions.length}</p>
            </div>
          </div>
        </div>

        <nav className="panel rounded-[1.8rem] p-3">
          <div className="space-y-1">
            {navItems.map((item) => {
              const active = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-start gap-3 rounded-2xl px-3 py-3 transition ${
                    active
                      ? 'bg-gradient-to-r from-brand-500/28 to-pine-500/18 text-brand-50'
                      : 'text-stone-300 hover:bg-white/6 hover:text-brand-50'
                  }`}
                >
                  <span className={`mt-0.5 rounded-2xl p-2 ${active ? 'bg-white/12' : 'bg-white/5'}`}>{item.icon}</span>
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold">{item.name}</span>
                    <span className="block text-xs text-stone-400">{item.caption}</span>
                  </span>
                  {item.path === '/alerts' && unreadAlerts > 0 ? (
                    <span className="ml-auto rounded-full bg-danger-500 px-2 py-0.5 text-xs font-bold text-white">
                      {unreadAlerts}
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </div>
        </nav>

        <div className="panel rounded-[1.8rem] p-5">
          <p className="eyebrow">Saved Regions</p>
          <div className="mt-4 space-y-3">
            {savedRegions.length === 0 ? (
              <p className="text-sm text-stone-400">Saved regions from the map appear here.</p>
            ) : (
              savedRegions.map((region) => (
                <div key={region.id} className="rounded-2xl bg-white/5 p-3">
                  <p className="text-sm font-semibold text-brand-50">{region.region_name}</p>
                  <p className="mt-1 text-xs text-stone-400">
                    {Number(region.latitude).toFixed(2)}, {Number(region.longitude).toFixed(2)}
                  </p>
                  <p className="mt-2 text-xs text-brand-200">
                    Alert threshold {(region.alert_threshold * 100).toFixed(0)}%
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
