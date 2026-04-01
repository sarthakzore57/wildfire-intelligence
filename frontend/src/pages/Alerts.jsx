import React, { useEffect, useMemo, useState } from 'react';
import { format } from 'date-fns';
import { getAlerts, markAllAlertsRead, updateAlert } from '../services/api';

const formatDate = (dateString) => format(new Date(dateString), 'MMM d, yyyy h:mm a');

const toneForRisk = (riskLevel) => {
  if (riskLevel >= 0.7) return 'risk-band-high';
  if (riskLevel >= 0.4) return 'risk-band-medium';
  return 'risk-band-low';
};

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAlerts = async () => {
      setLoading(true);
      setError('');
      try {
        const params = {};
        if (filter === 'unread') params.is_read = false;
        if (filter === 'read') params.is_read = true;
        const response = await getAlerts(params);
        setAlerts(response.data);
      } catch (fetchError) {
        console.error('Error fetching alerts:', fetchError);
        setError('Unable to load the alert feed right now.');
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, [filter]);

  const unreadCount = useMemo(() => alerts.filter((alert) => !alert.is_read).length, [alerts]);

  const handleMarkRead = async (alertId) => {
    try {
      await updateAlert(alertId, { is_read: true });
      setAlerts((previous) =>
        previous.map((alert) => (alert.id === alertId ? { ...alert, is_read: true } : alert))
      );
    } catch (updateError) {
      console.error('Error marking alert as read:', updateError);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllAlertsRead();
      setAlerts((previous) => previous.map((alert) => ({ ...alert, is_read: true })));
    } catch (updateError) {
      console.error('Error marking all alerts as read:', updateError);
    }
  };

  return (
    <div className="space-y-6">
      <section className="hero-card rounded-[2rem] px-6 py-7 md:px-8">
        <div className="relative z-10 flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="eyebrow">Alert operations</p>
            <h1 className="section-title mt-2 text-4xl font-bold text-brand-50">Notification queue and response feed</h1>
            <p className="mt-3 max-w-2xl text-sm text-stone-200">
              Stay ahead of changing fire conditions, triage unread risk notifications, and keep your monitoring workflow clean.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <div className="panel-soft rounded-[1.2rem] px-4 py-3 text-sm text-stone-200">
              Unread alerts <span className="ml-2 font-bold text-brand-100">{unreadCount}</span>
            </div>
            <button onClick={handleMarkAllRead} className="primary-button" disabled={!unreadCount}>
              Mark all read
            </button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {[
          { label: 'All alerts', value: alerts.length, note: 'Total records in the active filter set' },
          { label: 'Unread', value: unreadCount, note: 'Items still waiting for acknowledgment' },
          {
            label: 'Read',
            value: alerts.length - unreadCount,
            note: 'Alerts already reviewed by the operator',
          },
        ].map((item) => (
          <div key={item.label} className="panel rounded-[1.65rem] p-5">
            <p className="eyebrow">{item.label}</p>
            <p className="mt-4 text-4xl font-bold text-brand-50">{item.value}</p>
            <p className="mt-3 text-sm text-stone-300">{item.note}</p>
          </div>
        ))}
      </section>

      <section className="panel rounded-[1.85rem] p-5 md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="eyebrow">Feed controls</p>
            <h2 className="section-title mt-2 text-2xl font-bold text-brand-100">Filter the queue</h2>
          </div>
          <div className="flex gap-2">
            {['all', 'unread', 'read'].map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setFilter(item)}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                  filter === item
                    ? 'bg-brand-500 text-white'
                    : 'bg-white/6 text-stone-300 hover:bg-white/10'
                }`}
              >
                {item.charAt(0).toUpperCase() + item.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {error ? (
          <div className="mt-5 rounded-[1.4rem] border border-danger-500/30 bg-danger-500/10 p-4 text-sm text-danger-100">
            {error}
          </div>
        ) : null}

        {loading ? (
          <div className="mt-5 text-sm text-stone-300">Loading alert feed...</div>
        ) : alerts.length === 0 ? (
          <div className="mt-5 panel-soft rounded-[1.5rem] p-5 text-sm text-stone-300">
            No alerts match the selected filter right now.
          </div>
        ) : (
          <div className="mt-5 space-y-3">
            {alerts.map((alert) => (
              <article key={alert.id} className="panel-soft rounded-[1.45rem] p-4 md:p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`metric-chip ${toneForRisk(alert.risk_level)}`}>
                        {(alert.risk_level * 100).toFixed(0)}% risk
                      </span>
                      {!alert.is_read ? (
                        <span className="metric-chip bg-night-500/25 text-night-200">Unread</span>
                      ) : (
                        <span className="metric-chip bg-white/8 text-stone-300">Reviewed</span>
                      )}
                    </div>
                    <p className="mt-3 text-base font-semibold text-brand-50">{alert.message}</p>
                    <p className="mt-2 text-sm text-stone-400">{formatDate(alert.alert_time)}</p>
                  </div>

                  {!alert.is_read ? (
                    <button onClick={() => handleMarkRead(alert.id)} className="secondary-button">
                      Mark read
                    </button>
                  ) : null}
                </div>

                <div className="mt-4 flex flex-wrap gap-2 text-xs text-stone-300">
                  <span className="metric-chip bg-white/6 text-stone-200">
                    Channel {alert.is_sent_email ? 'Email' : 'In-app'}
                  </span>
                  <span className="metric-chip bg-white/6 text-stone-200">
                    Zone ID {alert.risk_zone_id}
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default Alerts;
