import { state } from './state.js';
import { qs } from './utils.js';
import * as api from './api.js';

export async function initAircraft() {
    await loadAircraftList();
    qs('#btn-new-aircraft').addEventListener('click', () => showDetail(null));
    qs('#btn-save-aircraft').addEventListener('click', saveAircraft);
    qs('#btn-cancel-aircraft').addEventListener('click', hideDetail);

    qs('#aircraft-selector').addEventListener('change', (e) => {
        const id = parseInt(e.target.value);
        state.currentAircraft = state.aircraftList.find(a => a.id === id) || null;
        updateReference();
    });
}

export async function loadAircraftList() {
    const result = await api.getAircraftList();
    if (!result.success) return;

    state.aircraftList = result.aircraft;
    renderSelector();
    renderList();

    const def = state.aircraftList.find(a => a.is_default) || state.aircraftList[0];
    if (def) {
        state.currentAircraft = def;
        qs('#aircraft-selector').value = def.id;
    }
}

function renderSelector() {
    const sel = qs('#aircraft-selector');
    sel.innerHTML = '';
    state.aircraftList.forEach(ac => {
        const opt = document.createElement('option');
        opt.value = ac.id;
        opt.textContent = `${ac.tail_number} - ${ac.type_model}`;
        sel.appendChild(opt);
    });
}

function renderList() {
    const container = qs('#aircraft-list');
    if (state.aircraftList.length === 0) {
        container.innerHTML = '<p class="text-secondary">No aircraft configured.</p>';
        return;
    }

    let html = '<table class="data-table"><thead><tr>';
    html += '<th>Tail #</th><th>Type</th><th>Empty Wt</th><th>Max Wt</th><th>Fuel</th><th>Default</th><th>Actions</th>';
    html += '</tr></thead><tbody>';

    state.aircraftList.forEach(ac => {
        html += `<tr>
            <td style="font-weight:600">${ac.tail_number}</td>
            <td>${ac.type_model}</td>
            <td>${ac.empty_weight} lbs</td>
            <td>${ac.max_takeoff_weight} lbs</td>
            <td>${ac.usable_fuel} gal</td>
            <td>${ac.is_default ? '<span class="badge badge-success">Default</span>' : ''}</td>
            <td>
                <button class="btn btn-sm btn-outline ac-edit" data-id="${ac.id}">Edit</button>
                <button class="btn btn-sm btn-outline ac-delete" data-id="${ac.id}">Del</button>
            </td>
        </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;

    container.querySelectorAll('.ac-edit').forEach(btn => {
        btn.addEventListener('click', () => showDetail(parseInt(btn.dataset.id)));
    });
    container.querySelectorAll('.ac-delete').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (confirm('Delete this aircraft?')) {
                await api.deleteAircraft(parseInt(btn.dataset.id));
                await loadAircraftList();
            }
        });
    });
}

async function showDetail(id) {
    state.editingAircraftId = id;
    const detail = qs('#aircraft-detail');
    detail.classList.remove('hidden');

    if (id) {
        const result = await api.getAircraft(id);
        if (!result.success) return;
        const ac = result.aircraft;
        qs('#aircraft-detail-title').textContent = `Edit: ${ac.tail_number}`;
        qs('#ac-tail').value = ac.tail_number;
        qs('#ac-type').value = ac.type_model;
        qs('#ac-empty-weight').value = ac.empty_weight;
        qs('#ac-empty-moment').value = ac.empty_weight_moment;
        qs('#ac-max-weight').value = ac.max_takeoff_weight;
        qs('#ac-fuel').value = ac.usable_fuel;
        qs('#ac-fuel-arm').value = ac.fuel_arm;
        qs('#ac-taxi-fuel').value = ac.taxi_fuel;
        qs('#ac-cg-fwd').value = ac.cg_forward_limit;
        qs('#ac-cg-aft').value = ac.cg_aft_limit;
        qs('#ac-perf-json').value = JSON.stringify({
            cruise_performance: ac.cruise_performance,
            climb_performance: ac.climb_performance,
            takeoff_distance: ac.takeoff_distance,
            landing_distance: ac.landing_distance,
            v_speeds: ac.v_speeds,
            weight_limits: ac.weight_limits,
        }, null, 2);
    } else {
        qs('#aircraft-detail-title').textContent = 'New Aircraft';
        qs('#ac-tail').value = '';
        qs('#ac-type').value = '';
        qs('#ac-empty-weight').value = '';
        qs('#ac-empty-moment').value = '';
        qs('#ac-max-weight').value = '';
        qs('#ac-fuel').value = '';
        qs('#ac-fuel-arm').value = '';
        qs('#ac-taxi-fuel').value = '1.4';
        qs('#ac-cg-fwd').value = '';
        qs('#ac-cg-aft').value = '';
        qs('#ac-perf-json').value = '';
    }
}

function hideDetail() {
    qs('#aircraft-detail').classList.add('hidden');
    state.editingAircraftId = null;
}

async function saveAircraft() {
    let perfData = {};
    try {
        perfData = JSON.parse(qs('#ac-perf-json').value || '{}');
    } catch (e) {
        alert('Invalid JSON in performance data');
        return;
    }

    const data = {
        tail_number: qs('#ac-tail').value.trim(),
        type_model: qs('#ac-type').value.trim(),
        empty_weight: parseFloat(qs('#ac-empty-weight').value),
        empty_weight_moment: parseFloat(qs('#ac-empty-moment').value),
        max_takeoff_weight: parseFloat(qs('#ac-max-weight').value),
        usable_fuel: parseFloat(qs('#ac-fuel').value),
        fuel_arm: parseFloat(qs('#ac-fuel-arm').value),
        taxi_fuel: parseFloat(qs('#ac-taxi-fuel').value),
        cg_forward_limit: parseFloat(qs('#ac-cg-fwd').value),
        cg_aft_limit: parseFloat(qs('#ac-cg-aft').value),
        ...perfData,
    };

    if (state.editingAircraftId) {
        await api.updateAircraft(state.editingAircraftId, data);
    } else {
        await api.createAircraft(data);
    }

    hideDetail();
    await loadAircraftList();
}

export async function updateReference() {
    if (!state.currentAircraft) return;
    const result = await api.getAircraft(state.currentAircraft.id);
    if (!result.success) return;
    const ac = result.aircraft;

    qs('#ref-title').textContent = `Quick Reference - ${ac.tail_number} ${ac.type_model}`;

    // V-Speeds
    const vspeeds = ac.v_speeds || {};
    const tbody = qs('#vspeeds-table tbody');
    tbody.innerHTML = '';
    for (const [name, val] of Object.entries(vspeeds)) {
        tbody.innerHTML += `<tr><td style="font-weight:600">${name}</td><td>${val} kt</td></tr>`;
    }

    // Weight limits
    const wl = ac.weight_limits || {};
    const wtbody = qs('#weights-table tbody');
    wtbody.innerHTML = '';
    const labels = {
        max_ramp_weight: 'Max Ramp Weight',
        max_takeoff_weight: 'Max Takeoff Weight',
        max_landing_weight: 'Max Landing Weight',
        max_baggage_area1: 'Max Baggage (Area 1)',
        max_baggage_area2: 'Max Baggage (Area 2)',
        fuel_capacity_gal: 'Fuel Capacity',
        usable_fuel_gal: 'Usable Fuel',
    };
    for (const [key, label] of Object.entries(labels)) {
        if (wl[key] != null) {
            const unit = key.includes('fuel') || key.includes('gal') ? ' gal' : ' lbs';
            wtbody.innerHTML += `<tr><td>${label}</td><td>${wl[key]}${unit}</td></tr>`;
        }
    }
}
