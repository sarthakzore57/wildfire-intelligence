import React, { useEffect, useMemo, useState } from 'react';
import { CircleMarker, MapContainer, Marker, Popup, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { getFireRiskZones, predictFireRisk, predictFireSpread } from '../../services/api';

const tileUrl = import.meta.env.VITE_LEAFLET_TILE_URL || 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const tileAttribution =
  import.meta.env.VITE_LEAFLET_ATTRIBUTION ||
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

const riskMarkerIcon = (riskLevel) => {
  const color = riskLevel > 0.7 ? '#df5338' : riskLevel > 0.4 ? '#d99419' : '#29935a';
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background:${color};width:20px;height:20px;border-radius:999px;border:3px solid rgba(255,248,239,0.95);box-shadow:0 0 20px ${color};"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

const FocusOnSelection = ({ coords }) => {
  const map = useMap();

  useEffect(() => {
    if (coords) {
      map.flyTo(coords, 8, { duration: 1 });
    }
  }, [coords, map]);

  return null;
};

const ClickHandler = ({ onClick }) => {
  useMapEvents({
    click: onClick,
  });

  return null;
};

const FireRiskMap = ({ onSelectRegion }) => {
  const [riskZones, setRiskZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [spreadPoints, setSpreadPoints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mapCenter, setMapCenter] = useState([37.7749, -122.4194]);
  const [clickedCoords, setClickedCoords] = useState(null);

  useEffect(() => {
    const fetchZones = async () => {
      setLoading(true);
      try {
        const response = await getFireRiskZones({ limit: 100 });
        setRiskZones(response.data);
        if (response.data.length) {
          const firstZone = response.data[0];
          setMapCenter([firstZone.latitude, firstZone.longitude]);
          setSelectedZone(firstZone);
          onSelectRegion?.(firstZone);
        }
      } catch (fetchError) {
        console.error('Error fetching fire risk zones:', fetchError);
        setError('Unable to load map risk zones.');
      } finally {
        setLoading(false);
      }
    };

    fetchZones();
  }, [onSelectRegion]);

  const handleSelectZone = (zone) => {
    setSelectedZone(zone);
    setMapCenter([zone.latitude, zone.longitude]);
    setSpreadPoints([]);
    onSelectRegion?.(zone);
  };

  const handleMapClick = async (event) => {
    const { lat, lng } = event.latlng;
    setClickedCoords([lat, lng]);
    setError('');
    setLoading(true);

    try {
      const response = await predictFireRisk(lat, lng);
      const nextZone = response.data;
      setRiskZones((previous) => {
        const duplicate = previous.some(
          (zone) =>
            Math.abs(zone.latitude - nextZone.latitude) < 0.01 &&
            Math.abs(zone.longitude - nextZone.longitude) < 0.01
        );
        return duplicate ? previous : [nextZone, ...previous];
      });
      handleSelectZone(nextZone);
    } catch (fetchError) {
      console.error('Error predicting fire risk:', fetchError);
      setError('Prediction failed for this location. Please try another point.');
    } finally {
      setLoading(false);
    }
  };

  const handlePredictSpread = async (zoneId) => {
    setLoading(true);
    setError('');
    try {
      const response = await predictFireSpread(zoneId);
      setSpreadPoints(response.data.spread_points || []);
    } catch (fetchError) {
      console.error('Error predicting fire spread:', fetchError);
      setError('Spread simulation could not be generated.');
    } finally {
      setLoading(false);
    }
  };

  const summary = useMemo(() => {
    if (!selectedZone) return null;

    return {
      level:
        selectedZone.risk_level > 0.7
          ? 'High'
          : selectedZone.risk_level > 0.4
            ? 'Medium'
            : 'Low',
      color:
        selectedZone.risk_level > 0.7
          ? '#df5338'
          : selectedZone.risk_level > 0.4
            ? '#d99419'
            : '#29935a',
    };
  }, [selectedZone]);

  return (
    <div className="relative h-full overflow-hidden rounded-[1.6rem]">
      {loading ? (
        <div className="absolute left-4 top-4 z-[999] rounded-full bg-brand-500 px-4 py-2 text-xs font-semibold text-white shadow-lg">
          Updating map intelligence...
        </div>
      ) : null}

      {error ? (
        <div className="absolute left-4 top-16 z-[999] rounded-2xl border border-danger-500/30 bg-danger-500/20 px-4 py-3 text-xs text-danger-100">
          {error}
        </div>
      ) : null}

      {selectedZone ? (
        <div className="absolute bottom-4 left-4 z-[999] max-w-sm rounded-[1.35rem] border border-white/10 bg-[rgba(17,14,11,0.88)] p-4 text-sm text-stone-200 shadow-2xl backdrop-blur-xl">
          <p className="eyebrow">Selected zone</p>
          <h3 className="section-title mt-2 text-xl font-bold text-brand-100">{selectedZone.region_name}</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="metric-chip" style={{ background: `${summary?.color}22`, color: summary?.color }}>
              {summary?.level} risk {(selectedZone.risk_level * 100).toFixed(0)}%
            </span>
            {selectedZone.temperature ? (
              <span className="metric-chip bg-white/7 text-stone-200">{selectedZone.temperature.toFixed(1)} C</span>
            ) : null}
            {selectedZone.wind_speed ? (
              <span className="metric-chip bg-white/7 text-stone-200">{selectedZone.wind_speed.toFixed(1)} km/h wind</span>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => handlePredictSpread(selectedZone.id)}
            className="primary-button mt-4 w-full"
          >
            Simulate spread
          </button>
        </div>
      ) : null}

      <MapContainer center={mapCenter} zoom={6} style={{ height: '100%', width: '100%' }}>
        <TileLayer attribution={tileAttribution} url={tileUrl} />
        <ClickHandler onClick={handleMapClick} />
        <FocusOnSelection coords={mapCenter} />

        {riskZones.map((zone) => (
          <Marker
            key={zone.id || `${zone.latitude}-${zone.longitude}`}
            position={[zone.latitude, zone.longitude]}
            icon={riskMarkerIcon(zone.risk_level)}
            eventHandlers={{ click: () => handleSelectZone(zone) }}
          >
            <Popup>
              <div className="min-w-[220px] text-[#231911]">
                <h3 className="text-base font-bold">{zone.region_name}</h3>
                <p className="mt-2 text-sm">Risk: {(zone.risk_level * 100).toFixed(0)}%</p>
                <p className="text-sm">Category: {zone.risk_category}</p>
                {zone.temperature ? <p className="text-sm">Temperature: {zone.temperature.toFixed(1)} C</p> : null}
                {zone.humidity ? <p className="text-sm">Humidity: {zone.humidity.toFixed(0)}%</p> : null}
                {zone.wind_speed ? <p className="text-sm">Wind: {zone.wind_speed.toFixed(1)} km/h</p> : null}
                <button
                  type="button"
                  className="mt-3 rounded-full bg-brand-500 px-3 py-2 text-sm font-semibold text-white"
                  onClick={() => handlePredictSpread(zone.id)}
                >
                  Predict spread
                </button>
              </div>
            </Popup>
          </Marker>
        ))}

        {spreadPoints.map((point, index) => (
          <CircleMarker
            key={`spread-${index}`}
            center={[point.latitude, point.longitude]}
            radius={6}
            pathOptions={{
              fillColor: point.risk_level > 0.7 ? '#df5338' : point.risk_level > 0.4 ? '#d99419' : '#29935a',
              fillOpacity: 0.55,
              color: '#fff8ef',
              weight: 1.4,
            }}
          >
            <Popup>
              <div className="text-[#231911]">
                <p className="font-semibold">Predicted spread point</p>
                <p className="text-sm">{new Date(point.timestamp).toLocaleString()}</p>
                <p className="text-sm">Risk {(point.risk_level * 100).toFixed(0)}%</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {clickedCoords ? (
          <CircleMarker
            center={clickedCoords}
            radius={12}
            pathOptions={{
              color: '#8aa5ff',
              fillColor: '#617fff',
              fillOpacity: 0.18,
              weight: 2,
            }}
          />
        ) : null}
      </MapContainer>
    </div>
  );
};

export default FireRiskMap;
