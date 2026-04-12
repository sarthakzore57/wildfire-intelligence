import React, { useEffect, useMemo, useState } from 'react';
import { format } from 'date-fns';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { getFireIncidents } from '../services/api';

const severityColors = {
  High: '#df5338',
  Medium: '#d99419',
  Low: '#29935a',
};

const statusColors = {
  Active: '#df5338',
  Contained: '#d99419',
  Controlled: '#7f86ff',
  Extinguished: '#29935a',
};

const HistoricalData = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
    startDateFrom: '',
    startDateTo: '',
  });

  useEffect(() => {
    const fetchIncidents = async () => {
      setLoading(true);
      setError('');

      try {
        const params = {};
        if (filters.status) params.status = filters.status;
        if (filters.severity) params.severity = filters.severity;
        if (filters.startDateFrom) params.start_date_from = filters.startDateFrom;
        if (filters.startDateTo) params.start_date_to = filters.startDateTo;

        const response = await getFireIncidents(params);
        setIncidents(response.data);
      } catch (fetchError) {
        console.error('Error fetching incidents:', fetchError);
        setError('Historical incident data could not be loaded.');
      } finally {
        setLoading(false);
      }
    };

    fetchIncidents();
  }, [filters]);

  const severityData = useMemo(() => {
    const counts = { High: 0, Medium: 0, Low: 0 };
    incidents.forEach((incident) => {
      if (counts[incident.severity] !== undefined) counts[incident.severity] += 1;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value, color: severityColors[name] }));
  }, [incidents]);

  const statusData = useMemo(() => {
    const counts = { Active: 0, Contained: 0, Controlled: 0, Extinguished: 0 };
    incidents.forEach((incident) => {
      if (counts[incident.status] !== undefined) counts[incident.status] += 1;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value, color: statusColors[name] }));
  }, [incidents]);

  const monthlyData = useMemo(() => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const grouped = {};

    incidents.forEach((incident) => {
      const date = new Date(incident.start_date);
      const label = `${months[date.getMonth()]} ${date.getFullYear()}`;
      if (!grouped[label]) {
        grouped[label] = { month: label, High: 0, Medium: 0, Low: 0 };
      }
      grouped[label][incident.severity] = (grouped[label][incident.severity] || 0) + 1;
    });

    return Object.values(grouped).sort((left, right) => new Date(`1 ${left.month}`) - new Date(`1 ${right.month}`));
  }, [incidents]);

  const summary = useMemo(() => {
    const totalArea = incidents.reduce((sum, incident) => sum + (Number(incident.area_affected) || 0), 0);
    const active = incidents.filter((incident) => incident.status === 'Active').length;
    const highSeverity = incidents.filter((incident) => incident.severity === 'High').length;
    return { totalArea, active, highSeverity };
  }, [incidents]);

  const hasActiveFilters = Boolean(
    filters.status || filters.severity || filters.startDateFrom || filters.startDateTo
  );

  const clearFilters = () => {
    setFilters({
      status: '',
      severity: '',
      startDateFrom: '',
      startDateTo: '',
    });
  };

  return (
    <div className="space-y-6">
      <section className="hero-card rounded-[2rem] px-6 py-7 md:px-8">
        <div className="relative z-10 flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="eyebrow">Historical intelligence</p>
            <h1 className="section-title mt-2 text-4xl font-bold text-brand-50">Incident history and trend analysis</h1>
            <p className="mt-3 max-w-2xl text-sm text-stone-200">
              Explore severity mix, status patterns, and month-over-month shifts across recorded incidents.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="panel-soft rounded-[1.2rem] px-4 py-3">
              <p className="eyebrow !tracking-[0.16em]">Incidents</p>
              <p className="mt-2 text-3xl font-bold text-brand-50">{incidents.length}</p>
            </div>
            <div className="panel-soft rounded-[1.2rem] px-4 py-3">
              <p className="eyebrow !tracking-[0.16em]">Active</p>
              <p className="mt-2 text-3xl font-bold text-brand-50">{summary.active}</p>
            </div>
            <div className="panel-soft rounded-[1.2rem] px-4 py-3">
              <p className="eyebrow !tracking-[0.16em]">Area</p>
              <p className="mt-2 text-3xl font-bold text-brand-50">{summary.totalArea.toFixed(0)}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="panel rounded-[1.85rem] p-5 md:p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Filters</p>
            <h2 className="section-title mt-2 text-2xl font-bold text-brand-100">Shape the timeline</h2>
          </div>
          {hasActiveFilters ? (
            <button type="button" onClick={clearFilters} className="secondary-button">
              Clear filters
            </button>
          ) : null}
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="field text-stone-200">
            <span className="text-sm text-stone-300">Status</span>
            <select value={filters.status} onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}>
              <option value="">All statuses</option>
              <option value="Active">Active</option>
              <option value="Contained">Contained</option>
              <option value="Controlled">Controlled</option>
              <option value="Extinguished">Extinguished</option>
            </select>
          </label>

          <label className="field text-stone-200">
            <span className="text-sm text-stone-300">Severity</span>
            <select value={filters.severity} onChange={(event) => setFilters((prev) => ({ ...prev, severity: event.target.value }))}>
              <option value="">All severities</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </label>

          <label className="field text-stone-200">
            <span className="text-sm text-stone-300">Start date from</span>
            <input
              type="date"
              value={filters.startDateFrom}
              onChange={(event) => setFilters((prev) => ({ ...prev, startDateFrom: event.target.value }))}
            />
          </label>

          <label className="field text-stone-200">
            <span className="text-sm text-stone-300">Start date to</span>
            <input
              type="date"
              value={filters.startDateTo}
              onChange={(event) => setFilters((prev) => ({ ...prev, startDateTo: event.target.value }))}
            />
          </label>
        </div>
      </section>

      {error ? (
        <div className="rounded-[1.5rem] border border-danger-500/30 bg-danger-500/10 p-4 text-sm text-danger-100">
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="panel rounded-[1.85rem] p-6 text-sm text-stone-300">Loading historical views...</div>
      ) : (
        <>
          <section className="grid gap-6 lg:grid-cols-2">
            <div className="panel rounded-[1.85rem] p-5 md:p-6">
              <p className="eyebrow">Severity breakdown</p>
              <h3 className="section-title mt-2 text-2xl font-bold text-brand-100">Incidents by severity</h3>
              <div className="mt-5 h-72">
                {incidents.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={severityData} dataKey="value" cx="50%" cy="50%" outerRadius={90} innerRadius={42}>
                        {severityData.map((entry) => (
                          <Cell key={entry.name} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="grid h-full place-items-center rounded-[1.4rem] border border-white/8 bg-white/3 text-center text-sm text-stone-400">
                    <p>No incidents match the current filters.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="panel rounded-[1.85rem] p-5 md:p-6">
              <p className="eyebrow">Status breakdown</p>
              <h3 className="section-title mt-2 text-2xl font-bold text-brand-100">Incidents by status</h3>
              <div className="mt-5 h-72">
                {incidents.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={statusData} dataKey="value" cx="50%" cy="50%" outerRadius={90} innerRadius={42}>
                        {statusData.map((entry) => (
                          <Cell key={entry.name} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="grid h-full place-items-center rounded-[1.4rem] border border-white/8 bg-white/3 text-center text-sm text-stone-400">
                    <p>No incidents match the current filters.</p>
                  </div>
                )}
              </div>
            </div>
          </section>

          <section className="panel rounded-[1.85rem] p-5 md:p-6">
            <p className="eyebrow">Timeline</p>
            <h3 className="section-title mt-2 text-2xl font-bold text-brand-100">Monthly incident flow</h3>
            <div className="mt-5 h-80">
              {monthlyData.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="month" stroke="rgba(248,240,228,0.6)" />
                    <YAxis stroke="rgba(248,240,228,0.6)" />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="High" stackId="a" fill={severityColors.High} />
                    <Bar dataKey="Medium" stackId="a" fill={severityColors.Medium} />
                    <Bar dataKey="Low" stackId="a" fill={severityColors.Low} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="grid h-full place-items-center rounded-[1.4rem] border border-white/8 bg-white/3 text-center text-sm text-stone-400">
                  <p>No timeline data is available for the current filters.</p>
                </div>
              )}
            </div>
          </section>

          <section className="panel rounded-[1.85rem] p-5 md:p-6">
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="eyebrow">Records</p>
                <h3 className="section-title mt-2 text-2xl font-bold text-brand-100">Incident ledger</h3>
              </div>
              <div className="text-sm text-stone-300">{summary.highSeverity} high-severity incidents in current view</div>
            </div>

            <div className="mt-5 overflow-x-auto">
              {incidents.length ? (
                <table className="data-table min-w-full">
                  <thead>
                    <tr>
                      <th>Coordinates</th>
                      <th>Status</th>
                      <th>Severity</th>
                      <th>Start</th>
                      <th>Area</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incidents.map((incident) => (
                      <tr key={incident.id}>
                        <td className="text-sm text-brand-50">
                          {Number(incident.latitude).toFixed(3)}, {Number(incident.longitude).toFixed(3)}
                        </td>
                        <td className="text-sm text-stone-300">{incident.status}</td>
                        <td className="text-sm font-semibold" style={{ color: severityColors[incident.severity] || '#f8f0e4' }}>
                          {incident.severity}
                        </td>
                        <td className="text-sm text-stone-300">{format(new Date(incident.start_date), 'MMM d, yyyy')}</td>
                        <td className="text-sm text-stone-300">
                          {incident.area_affected ? `${Number(incident.area_affected).toFixed(1)} km^2` : 'N/A'}
                        </td>
                        <td className="text-sm text-stone-300">{incident.source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="rounded-[1.4rem] border border-white/8 bg-white/3 p-5 text-sm text-stone-400">
                  No incident records match the current filters.
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default HistoricalData;
