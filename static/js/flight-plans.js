import { state } from './state.js';
import { qs } from './utils.js';
import * as api from './api.js';
import { loadPlanIntoForm } from './route.js';

export async function initFlightPlans() {
    await refreshPlansList();
    qs('#btn-load-plan').addEventListener('click', loadSelectedPlan);
    qs('#btn-delete-plan').addEventListener('click', deleteSelectedPlan);
    qs('#btn-save-plan').addEventListener('click', showSaveModal);
    qs('#btn-cancel-save').addEventListener('click', hideSaveModal);
    qs('#btn-confirm-save').addEventListener('click', confirmSave);
}

export async function refreshPlansList() {
    const result = await api.listFlightPlans();
    if (!result.success) return;
    state.flightPlans = result.plans;

    const sel = qs('#saved-plans-select');
    sel.innerHTML = '<option value="">-- New Flight Plan --</option>';
    result.plans.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.name} (${p.departure_icao}-${p.destination_icao})`;
        sel.appendChild(opt);
    });
}

async function loadSelectedPlan() {
    const id = qs('#saved-plans-select').value;
    if (!id) return;

    const result = await api.loadFlightPlan(id);
    if (!result.success) return;

    // Switch aircraft if different
    if (result.plan.aircraft_id) {
        const acSel = qs('#aircraft-selector');
        acSel.value = result.plan.aircraft_id;
        acSel.dispatchEvent(new Event('change'));
    }

    await loadPlanIntoForm(result.plan);
}

async function deleteSelectedPlan() {
    const id = qs('#saved-plans-select').value;
    if (!id) return;
    if (!confirm('Delete this flight plan?')) return;

    await api.deleteFlightPlan(id);
    await refreshPlansList();
}

function showSaveModal() {
    if (!state.currentRoute) {
        alert('Calculate a route first');
        return;
    }
    qs('#save-modal').classList.remove('hidden');
    qs('#plan-name-input').focus();
}

function hideSaveModal() {
    qs('#save-modal').classList.add('hidden');
}

async function confirmSave() {
    const name = qs('#plan-name-input').value.trim();
    if (!name) {
        alert('Enter a plan name');
        return;
    }

    const data = {
        name,
        aircraft_id: state.currentAircraft?.id || 1,
        departure_icao: qs('#departure').value.trim().toUpperCase(),
        destination_icao: qs('#destination').value.trim().toUpperCase(),
        cruise_altitude: parseInt(qs('#cruise-altitude').value),
        cruise_rpm: parseInt(qs('#cruise-rpm').value),
        waypoints: state.waypoints,
        route_data: state.currentRoute,
        weather_data: state.currentWeather?.briefing || null,
    };

    await api.saveFlightPlan(data);
    hideSaveModal();
    qs('#plan-name-input').value = '';
    await refreshPlansList();
}
