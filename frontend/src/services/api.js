import axios from 'axios';

export const defaultApiBaseUrl = (() => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  if (typeof window !== 'undefined') {
    const isLocalhost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    return isLocalhost
      ? 'http://localhost:8000/api/v1'
      : `${window.location.origin}/_/backend/api/v1`;
  }

  return 'http://localhost:8000/api/v1';
})();

// Create an axios instance with base URL
const api = axios.create({
  baseURL: defaultApiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth endpoints
export const login = (email, password) => 
  api.post('/auth/login/access-token', 
    new URLSearchParams({
      username: email, // Backend expects username field for email
      password,
    }).toString(),
    {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    }
  );

export const register = (userData) => 
  api.post('/users/', userData);

export const getCurrentUser = () => 
  api.get('/users/me');

export const updateCurrentUser = (userData) =>
  api.put('/users/me', userData);

// Fire risk endpoints
export const getFireRiskZones = (params) => 
  api.get('/fire-risk/zones', { params });

export const getFireRiskZoneById = (id) => 
  api.get(`/fire-risk/zones/${id}`);

export const getFireRiskByCoordinates = (latitude, longitude, tolerance = 0.01) => 
  api.get('/fire-risk/zones/by-coordinates', { 
    params: { latitude, longitude, tolerance } 
  });

export const predictFireRisk = (latitude, longitude, data = {}) => 
  api.post('/predictions/fire-risk/zones', { ...data, latitude, longitude });

export const predictFireSpread = (zoneId, hoursAhead = 24) => 
  api.post('/predictions/fire-spread', { zone_id: zoneId, hours_ahead: hoursAhead });

// Fire incidents endpoints
export const getFireIncidents = (params) => 
  api.get('/fire-incidents/', { params });

export const getFireIncidentById = (id) => 
  api.get(`/fire-incidents/${id}`);

// Saved regions endpoints
export const getSavedRegions = () => 
  api.get('/fire-risk/regions/saved');

export const saveRegion = (regionData) => 
  api.post('/fire-risk/regions/saved', regionData);

export const deleteSavedRegion = (regionId) => 
  api.delete(`/fire-risk/regions/saved/${regionId}`);

// Alert endpoints
export const getAlerts = (params) => 
  api.get('/alerts/', { params });

export const getAlertById = (id) => 
  api.get(`/alerts/${id}`);

export const updateAlert = (id, data) => 
  api.put(`/alerts/${id}`, data);

export const markAllAlertsRead = () => 
  api.post('/alerts/mark-all-read');

export default api; 
