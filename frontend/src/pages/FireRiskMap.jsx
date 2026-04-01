import React, { useContext, useEffect, useMemo, useState } from 'react';
import MapComponent from '../components/map/FireRiskMap';
import { AuthContext } from '../context/AuthContext';
import { deleteSavedRegion, getSavedRegions, saveRegion } from '../services/api';

const FireRiskMapPage = () => {
  const { user } = useContext(AuthContext);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [savedRegions, setSavedRegions] = useState([]);
  const [feedback, setFeedback] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const loadSavedRegions = async () => {
      try {
        const response = await getSavedRegions();
        setSavedRegions(response.data);
      } catch (error) {
        console.error('Error loading saved regions:', error);
      }
    };

    loadSavedRegions();
  }, []);

  const alreadySaved = useMemo(() => {
    if (!selectedRegion) return false;
    return savedRegions.some(
      (region) =>
        Math.abs(region.latitude - selectedRegion.latitude) < 0.01 &&
        Math.abs(region.longitude - selectedRegion.longitude) < 0.01
    );
  }, [savedRegions, selectedRegion]);

  const handleSaveRegion = async () => {
    if (!selectedRegion || !user?.id || alreadySaved) return;

    setSaving(true);
    setFeedback('');
    try {
      const response = await saveRegion({
        user_id: user.id,
        region_name: selectedRegion.region_name,
        latitude: selectedRegion.latitude,
        longitude: selectedRegion.longitude,
        alert_threshold: user.alert_threshold || 0.7,
      });
      setSavedRegions((previous) => [response.data, ...previous]);
      setFeedback('Region saved to your watchlist.');
    } catch (error) {
      console.error('Error saving region:', error);
      setFeedback('Unable to save this region right now.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteRegion = async (regionId) => {
    try {
      await deleteSavedRegion(regionId);
      setSavedRegions((previous) => previous.filter((region) => region.id !== regionId));
    } catch (error) {
      console.error('Error deleting saved region:', error);
    }
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <section className="panel rounded-[1.85rem] p-4 md:p-5">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Geospatial control room</p>
            <h1 className="section-title mt-2 text-3xl font-bold text-brand-100">Risk map and live prediction</h1>
            <p className="mt-2 max-w-2xl text-sm text-stone-300">
              Click anywhere on the map to generate a fresh fire-risk estimate, then simulate spread and save the region.
            </p>
          </div>
          <div className="panel-soft rounded-full px-4 py-2 text-sm text-stone-200">
            Watchlist size: <span className="font-semibold text-brand-100">{savedRegions.length}</span>
          </div>
        </div>

        <div className="h-[68vh] min-h-[620px]">
          <MapComponent onSelectRegion={setSelectedRegion} />
        </div>
      </section>

      <section className="space-y-6">
        <div className="panel rounded-[1.85rem] p-5 md:p-6">
          <p className="eyebrow">Selected region</p>
          {selectedRegion ? (
            <>
              <h2 className="section-title mt-2 text-2xl font-bold text-brand-100">{selectedRegion.region_name}</h2>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="panel-soft rounded-[1.2rem] p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-stone-400">Risk</p>
                  <p className="mt-2 text-3xl font-bold text-brand-50">{(selectedRegion.risk_level * 100).toFixed(0)}%</p>
                </div>
                <div className="panel-soft rounded-[1.2rem] p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-stone-400">Category</p>
                  <p className="mt-2 text-3xl font-bold text-brand-50">{selectedRegion.risk_category}</p>
                </div>
              </div>

              <div className="mt-4 grid gap-3 text-sm text-stone-300 sm:grid-cols-2">
                <div className="panel-soft rounded-[1.2rem] p-4">
                  Temperature: {selectedRegion.temperature ? `${selectedRegion.temperature.toFixed(1)} C` : 'N/A'}
                </div>
                <div className="panel-soft rounded-[1.2rem] p-4">
                  Humidity: {selectedRegion.humidity ? `${selectedRegion.humidity.toFixed(0)}%` : 'N/A'}
                </div>
                <div className="panel-soft rounded-[1.2rem] p-4">
                  Wind: {selectedRegion.wind_speed ? `${selectedRegion.wind_speed.toFixed(1)} km/h` : 'N/A'}
                </div>
                <div className="panel-soft rounded-[1.2rem] p-4">
                  Coordinates: {Number(selectedRegion.latitude).toFixed(2)}, {Number(selectedRegion.longitude).toFixed(2)}
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleSaveRegion}
                  disabled={saving || alreadySaved}
                  className="primary-button"
                >
                  {alreadySaved ? 'Already in watchlist' : saving ? 'Saving...' : 'Save to watchlist'}
                </button>
              </div>

              {feedback ? <p className="mt-3 text-sm text-brand-200">{feedback}</p> : null}
            </>
          ) : (
            <p className="mt-3 text-sm text-stone-400">Select a zone or click on the map to create a prediction.</p>
          )}
        </div>

        <div className="panel rounded-[1.85rem] p-5 md:p-6">
          <div className="flex items-end justify-between gap-3">
            <div>
              <p className="eyebrow">Extra feature</p>
              <h2 className="section-title mt-2 text-2xl font-bold text-brand-100">Saved watchlist</h2>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            {savedRegions.length === 0 ? (
              <p className="text-sm text-stone-400">No saved regions yet. Save important zones from the map to revisit them faster.</p>
            ) : (
              savedRegions.map((region) => (
                <div key={region.id} className="panel-soft rounded-[1.3rem] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-brand-50">{region.region_name}</p>
                      <p className="mt-1 text-xs text-stone-400">
                        {Number(region.latitude).toFixed(2)}, {Number(region.longitude).toFixed(2)}
                      </p>
                      <p className="mt-2 text-xs text-brand-200">
                        Alert threshold {(region.alert_threshold * 100).toFixed(0)}%
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteRegion(region.id)}
                      className="secondary-button"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default FireRiskMapPage;
