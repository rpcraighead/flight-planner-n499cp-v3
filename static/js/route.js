import { state } from './state.js';
import { qs, summaryItem, formatNum } from './utils.js';
import * as api from './api.js';
import { drawRoute, initPreviewMap } from './map.js';

export function initRoute() {
    qs('#btn-add-waypoint').addEventListener('click', addWaypoint);
    qs('#waypoint-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') addWaypoint();
    });
    qs('#btn-calculate').addEventListener('click', calculateRoute);
    qs('#btn-export-pdf').addEventListener('click', exportPdf);

    // Default departure time to next 30-min increment
    const depEl = qs('#departure-time');
    if (depEl && !depEl.value) {
        const now = new Date();
        now.setMinutes(Math.ceil(now.getMinutes() / 30) * 30, 0, 0);
        now.setHours(now.getHours() + 1);
        const pad = n => String(n).padStart(2, '0');
        depEl.value = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
    }
}

function addWaypoint() {
    const input = qs('#waypoint-input');
    const val = input.value.trim().toUpperCase();
    if (!val) return;
    state.waypoints.push(val);
    input.value = '';
    renderWaypoints();
}

function removeWaypoint(idx) {
    state.waypoints.splice(idx, 1);
    renderWaypoints();
}

function renderWaypoints() {
    const list = qs('#waypoint-list');
    list.innerHTML = '';
    state.waypoints.forEach((wp, i) => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="waypoint-tag">${wp}<span class="remove" data-idx="${i}">&times;</span></span>`;
        li.querySelector('.remove').addEventListener('click', () => removeWaypoint(i));
        list.appendChild(li);
    });
}

async function calculateRoute() {
    const btn = qs('#btn-calculate');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Calculating...';

    try {
        const data = {
            departure: qs('#departure').value.trim(),
            destination: qs('#destination').value.trim(),
            waypoints: state.waypoints,
            cruise_altitude: qs('#cruise-altitude').value,
            rpm: qs('#cruise-rpm').value,
            aircraft_id: state.currentAircraft?.id,
        };

        const result = await api.calculateRoute(data);

        if (!result.success) {
            alert(result.error || 'Route calculation failed');
            return;
        }

        state.currentRoute = result;
        displayResults(result);
        await initPreviewMap();
        drawRoute(result);
        qs('#route-results').classList.remove('hidden');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Calculate Route';
    }
}

function displayResults(data) {
    const t = data.totals;
    const c = data.cruise;

    // Summary
    qs('#route-summary').innerHTML = [
        summaryItem('Distance', `${formatNum(t.distance_nm, 1)} nm`),
        summaryItem('Time', `${formatNum(t.time_minutes)} min`),
        summaryItem('TAS', `${c.true_airspeed} kt`),
        summaryItem('Total Fuel', `${formatNum(t.total_fuel, 1)} gal`),
        summaryItem('Wind', `${data.winds_aloft.direction}° @ ${data.winds_aloft.speed} kt`),
    ].join('');

    // Segments table
    const tbody = qs('#segments-table tbody');
    tbody.innerHTML = '';
    data.segments.forEach(seg => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${seg.from}</td><td>${seg.to}</td>
            <td>${seg.distance_nm}</td><td>${seg.true_course}°</td>
            <td>${seg.wind_correction}°</td><td>${seg.magnetic_heading}°</td>
            <td>${seg.ground_speed}</td><td>${seg.time_minutes}</td>
            <td>${seg.fuel_gallons}</td>`;
        tbody.appendChild(tr);
    });

    // Fuel summary
    qs('#fuel-summary').innerHTML = [
        summaryItem('Taxi', `${t.taxi_fuel} gal`),
        summaryItem('Climb', `${data.climb.fuel_gallons} gal`),
        summaryItem('Cruise', `${t.cruise_fuel} gal`),
        summaryItem('Reserve (45m)', `${t.reserve_fuel} gal`),
        summaryItem('TOTAL', `${t.total_fuel} gal`),
    ].join('');
}

async function exportPdf() {
    if (!state.currentRoute) return;

    const btn = qs('#btn-export-pdf');
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
        const blob = await api.exportPdf({
            route_data: state.currentRoute,
            weather_data: state.currentWeather || {},
            wb_data: state.currentWB || {},
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'navlog.pdf';
        a.click();
        URL.revokeObjectURL(url);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Export PDF';
    }
}

export async function loadPlanIntoForm(plan) {
    qs('#departure').value = plan.departure_icao || '';
    qs('#destination').value = plan.destination_icao || '';
    state.waypoints = plan.waypoints || [];
    renderWaypoints();
    if (plan.cruise_altitude) qs('#cruise-altitude').value = plan.cruise_altitude;
    if (plan.cruise_rpm) qs('#cruise-rpm').value = plan.cruise_rpm;

    if (plan.route_data) {
        state.currentRoute = plan.route_data;
        displayResults(plan.route_data);
        await initPreviewMap();
        drawRoute(plan.route_data);
        qs('#route-results').classList.remove('hidden');
    }
}
