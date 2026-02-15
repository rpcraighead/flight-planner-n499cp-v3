import { state } from './state.js';
import { qs, summaryItem } from './utils.js';
import * as api from './api.js';

export function initPerformance() {
    qs('#btn-calc-takeoff').addEventListener('click', calcTakeoff);
    qs('#btn-calc-landing').addEventListener('click', calcLanding);
    qs('#btn-calc-wb').addEventListener('click', calcWB);
}

async function calcTakeoff() {
    const btn = qs('#btn-calc-takeoff');
    btn.disabled = true;

    try {
        const result = await api.calcTakeoff({
            weight: qs('#to-weight').value,
            pressure_altitude: qs('#to-altitude').value,
            temperature: qs('#to-temp').value,
            headwind: qs('#to-headwind').value,
            aircraft_id: state.currentAircraft?.id,
        });

        qs('#takeoff-summary').innerHTML = [
            summaryItem('Ground Roll', `${result.ground_roll} ft`),
            summaryItem('Over 50ft Obstacle', `${result.total_over_50ft} ft`),
        ].join('');
        qs('#takeoff-results').classList.remove('hidden');
    } finally {
        btn.disabled = false;
    }
}

async function calcLanding() {
    const btn = qs('#btn-calc-landing');
    btn.disabled = true;

    try {
        const result = await api.calcLanding({
            pressure_altitude: qs('#ld-altitude').value,
            temperature: qs('#ld-temp').value,
            headwind: qs('#ld-headwind').value,
            aircraft_id: state.currentAircraft?.id,
        });

        qs('#landing-summary').innerHTML = [
            summaryItem('Ground Roll', `${result.ground_roll} ft`),
            summaryItem('Over 50ft Obstacle', `${result.total_over_50ft} ft`),
        ].join('');
        qs('#landing-results').classList.remove('hidden');
    } finally {
        btn.disabled = false;
    }
}

async function calcWB() {
    const btn = qs('#btn-calc-wb');
    btn.disabled = true;

    try {
        const result = await api.calcWeightBalance({
            pilot_weight: qs('#wb-pilot').value,
            front_passenger_weight: qs('#wb-front-pax').value,
            rear_passenger_weight: qs('#wb-rear-pax').value,
            baggage_weight: qs('#wb-baggage').value,
            fuel_gallons: qs('#wb-fuel').value,
            aircraft_id: state.currentAircraft?.id,
        });

        state.currentWB = result;

        const status = result.within_all_limits
            ? '<div class="alert alert-success">WITHIN LIMITS</div>'
            : '<div class="alert alert-danger">OUT OF LIMITS - Check weight and CG</div>';
        qs('#wb-status').innerHTML = status;

        qs('#wb-summary').innerHTML = [
            summaryItem('Total Weight', `${result.total_weight} lbs`),
            summaryItem('Max Weight', `${result.max_weight} lbs`),
            summaryItem('Margin', `${result.weight_margin} lbs`),
            summaryItem('CG', `${result.cg} in`),
            summaryItem('CG Limits', `${result.cg_forward_limit} - ${result.cg_aft_limit} in`),
            summaryItem('Moment', `${result.moment_1000}`),
        ].join('');
        qs('#wb-results').classList.remove('hidden');
    } finally {
        btn.disabled = false;
    }
}
