const BASE = '/api';

async function request(url, options = {}) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    return res.json();
}

function post(url, data) {
    return request(url, { method: 'POST', body: JSON.stringify(data) });
}

// Aircraft
export const getAircraftList = () => request(`${BASE}/aircraft`);
export const getAircraft = (id) => request(`${BASE}/aircraft/${id}`);
export const createAircraft = (data) => post(`${BASE}/aircraft`, data);
export const updateAircraft = (id, data) =>
    request(`${BASE}/aircraft/${id}`, { method: 'PUT', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } });
export const deleteAircraft = (id) =>
    request(`${BASE}/aircraft/${id}`, { method: 'DELETE' });

// Airports
export const getAirportInfo = (icao) => request(`${BASE}/airports/${icao}`);
export const searchAirports = (q) => request(`${BASE}/airports/search?q=${encodeURIComponent(q)}`);

// Route
export const calculateRoute = (data) => post(`${BASE}/routes/calculate`, data);

// Flight plans
export const listFlightPlans = () => request(`${BASE}/routes`);
export const saveFlightPlan = (data) => post(`${BASE}/routes`, data);
export const loadFlightPlan = (id) => request(`${BASE}/routes/${id}`);
export const updateFlightPlan = (id, data) =>
    request(`${BASE}/routes/${id}`, { method: 'PUT', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } });
export const deleteFlightPlan = (id) =>
    request(`${BASE}/routes/${id}`, { method: 'DELETE' });

// Weather
export const getWeatherBriefing = (data) => post(`${BASE}/weather/briefing`, data);

// Performance
export const calcTakeoff = (data) => post(`${BASE}/performance/takeoff`, data);
export const calcLanding = (data) => post(`${BASE}/performance/landing`, data);
export const calcWeightBalance = (data) => post(`${BASE}/performance/weight-balance`, data);

// Export
export async function exportPdf(data) {
    const res = await fetch(`${BASE}/export/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    return res.blob();
}

// Data
export const updateDatabase = () =>
    request(`${BASE}/data/update`, { method: 'POST' });
export const getDataStatus = () => request(`${BASE}/data/status`);
export const getTileSources = () => request(`${BASE}/data/tile-sources`);
