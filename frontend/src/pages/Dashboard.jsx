import React, { useContext, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { getAlerts, getFireIncidents, getFireRiskZones, getSavedRegions } from '../services/api';

const riskTone = (riskLevel) => {
  if (riskLevel >= 0.7) return 'risk-band-high';
  if (riskLevel >= 0.4) return 'risk-band-medium';
  return 'risk-band-low';
};

const severityColor = {
  High: 'text-danger-500',
  Medium: 'text-warning-500',
  Low: 'text-success-500',
};

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [zones, setZones] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [savedRegions, setSavedRegions] = useState([]);

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      try {
        const [zoneResponse, incidentResponse, alertResponse, savedRegionResponse] = await Promise.all([
          getFireRiskZones({ limit: 8 }),
          getFireIncidents({ limit: 8 }),
          getAlerts({ limit: 8 }),
          getSavedRegions(),
        ]);

        setZones(zoneResponse.data);
        setIncidents(incidentResponse.data);
        setAlerts(alertResponse.data);
        setSavedRegions(savedRegionResponse.data);
      } catch (fetchError) {
        console.error('Error loading dashboard:', fetchError);
        setError('Unable to load the command center right now. Please refresh and try again.');
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  const stats = useMemo(() => {
    const activeIncidents = incidents.filter((incident) => incident.status === 'Active').length;
    const unreadAlerts = alerts.filter((alert) => !alert.is_read).length;
    const highRiskZones = zones.filter((zone) => zone.risk_level >= 0.7).length;
    const averageRisk = zones.length
      ? zones.reduce((sum, zone) => sum + zone.risk_level, 0) / zones.length
      : 0;

    return {
      activeIncidents,
      unreadAlerts,
      highRiskZones,
      averageRisk,
    };
  }, [alerts, incidents, zones]);

  const briefing = useMemo(() => {
    if (!zones.length) {
      return 'No risk zones are loaded yet. Use the map to generate your first estimate.';
    }

    const topZone = [...zones].sort((a, b) => b.risk_level - a.risk_level)[0];
    const unreadAlerts = alerts.filter((alert) => !alert.is_read).length;

    return `${topZone.region_name} is the highest-risk monitored zone at ${(topZone.risk_level * 100).toFixed(0)}%. You have ${unreadAlerts} unread alerts and ${savedRegions.length} saved regions.`;
  }, [alerts, savedRegions.length, zones]);

  const recentHighRiskZones = useMemo(
    () => zones.filter((zone) => zone.risk_level >= 0.55).slice(0, 5),
    [zones]
  );

  if (loading) {
    return (
      <div className="panel rounded-[2rem] p-8">
        <p className="eyebrow">Loading</p>
        <h2 className="section-title mt-2 text-3xl font-bold text-brand-100">Building the command center</h2>
        <p className="mt-3 text-stone-300">Loading alerts, incidents, and watchlist state.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-[1.75rem] border border-danger-500/35 bg-danger-500/10 p-5 text-danger-100">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="hero-card rounded-[2.1rem] px-6 py-7 md:px-8 md:py-8">
        <div className="relative z-10 grid gap-8 lg:grid-cols-[1.25fr_0.85fr]">
          <div>
            <p className="eyebrow">Live wildfire intelligence</p>
            <h2 className="section-title mt-3 max-w-3xl text-4xl font-bold text-brand-50 md:text-5xl">
              Monitor risk, incidents, and alerts from one operational view.
            </h2>
            <p className="mt-4 max-w-2xl text-base leading-7 text-stone-200">
              {briefing}
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/map" className="primary-button">
                Open risk map
              </Link>
              <Link to="/historical" className="secondary-button">
                Review history
              </Link>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="metric-card">
              <p className="eyebrow !text-[0.64rem]">Average risk</p>
              <p className="mt-4 text-4xl font-bold text-brand-50">{(stats.averageRisk * 100).toFixed(0)}%</p>
              <p className="mt-3 text-sm text-stone-300">Average estimated risk across loaded zones.</p>
            </div>
            <div className="metric-card">
              <p className="eyebrow !text-[0.64rem]">Watch coverage</p>
              <p className="mt-4 text-4xl font-bold text-brand-50">{savedRegions.length}</p>
              <p className="mt-3 text-sm text-stone-300">Saved regions available for quick revisit.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: 'High-risk zones',
            value: stats.highRiskZones,
            note: 'Priority areas above the elevated warning band',
            tone: 'brand',
          },
          {
            label: 'Active incidents',
            value: stats.activeIncidents,
            note: 'Current active fire events in the incident feed',
            tone: 'danger',
          },
          {
            label: 'Unread alerts',
            value: stats.unreadAlerts,
            note: 'Notifications still waiting for acknowledgment',
            tone: 'night',
          },
          {
            label: 'Saved regions',
            value: savedRegions.length,
            note: 'Persistent watchlist locations linked to this account',
            tone: 'pine',
          },
        ].map((item) => (
          <div key={item.label} className="panel rounded-[1.75rem] p-5">
            <p className="eyebrow">{item.label}</p>
            <p className="mt-4 text-4xl font-bold text-brand-50">{item.value}</p>
            <p className="mt-3 text-sm text-stone-300">{item.note}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="panel rounded-[1.85rem] p-5 md:p-6">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="eyebrow">Priority queue</p>
              <h3 className="section-title mt-2 text-2xl font-bold text-brand-100">Highest-risk monitored zones</h3>
            </div>
            <Link to="/map" className="secondary-button">
              Explore map
            </Link>
          </div>

          <div className="mt-5 space-y-3">
            {recentHighRiskZones.length === 0 ? (
              <div className="panel-soft rounded-[1.5rem] p-4 text-sm text-stone-300">
                No elevated zones yet. Use the map to generate fresh estimates.
              </div>
            ) : (
              recentHighRiskZones.map((zone) => (
                <div key={zone.id} className="panel-soft flex flex-wrap items-center justify-between gap-4 rounded-[1.4rem] p-4">
                  <div>
                    <p className="text-base font-semibold text-brand-50">{zone.region_name}</p>
                    <p className="mt-1 text-sm text-stone-400">
                      {Number(zone.latitude).toFixed(2)}, {Number(zone.longitude).toFixed(2)}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`metric-chip ${riskTone(zone.risk_level)}`}>
                      {(zone.risk_level * 100).toFixed(0)}% risk
                    </span>
                    <span className="metric-chip bg-white/6 text-stone-200">
                      {zone.temperature ? `${zone.temperature.toFixed(1)} C` : 'No temp'}
                    </span>
                    <span className="metric-chip bg-white/6 text-stone-200">
                      {zone.wind_speed ? `${zone.wind_speed.toFixed(1)} km/h wind` : 'No wind'}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div>
          <div className="panel rounded-[1.85rem] p-5 md:p-6">
            <p className="eyebrow">Unread feed</p>
            <h3 className="section-title mt-2 text-2xl font-bold text-brand-100">Recent alerts</h3>
            <div className="mt-5 space-y-3">
              {alerts.slice(0, 4).map((alert) => (
                <div key={alert.id} className="panel-soft rounded-[1.35rem] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className={`metric-chip ${riskTone(alert.risk_level)}`}>
                      {(alert.risk_level * 100).toFixed(0)}% risk
                    </span>
                    <span className="text-xs text-stone-400">
                      {new Date(alert.alert_time).toLocaleString()}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-stone-200">{alert.message}</p>
                </div>
              ))}
              {!alerts.length && <p className="text-sm text-stone-400">No alert activity yet.</p>}
            </div>
          </div>
        </div>
      </section>

      <section className="panel rounded-[1.85rem] p-5 md:p-6">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Incident stream</p>
            <h3 className="section-title mt-2 text-2xl font-bold text-brand-100">Recent fire incidents</h3>
          </div>
          <Link to="/alerts" className="secondary-button">
            Review alert queue
          </Link>
        </div>

        <div className="mt-5 overflow-x-auto">
          <table className="data-table min-w-full">
            <thead>
              <tr>
                <th>Location</th>
                <th>Status</th>
                <th>Severity</th>
                <th>Started</th>
                <th>Area</th>
              </tr>
            </thead>
            <tbody>
              {incidents.slice(0, 6).map((incident) => (
                <tr key={incident.id}>
                  <td className="text-sm text-brand-50">
                    {Number(incident.latitude).toFixed(2)}, {Number(incident.longitude).toFixed(2)}
                  </td>
                  <td className="text-sm text-stone-300">{incident.status}</td>
                  <td className={`text-sm font-semibold ${severityColor[incident.severity] || 'text-stone-300'}`}>
                    {incident.severity}
                  </td>
                  <td className="text-sm text-stone-300">
                    {new Date(incident.start_date).toLocaleDateString()}
                  </td>
                  <td className="text-sm text-stone-300">
                    {incident.area_affected ? `${Number(incident.area_affected).toFixed(1)} km²` : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {!incidents.length && <p className="mt-4 text-sm text-stone-400">No incident data available yet.</p>}
      </section>
    </div>
  );
};

export default Dashboard;
