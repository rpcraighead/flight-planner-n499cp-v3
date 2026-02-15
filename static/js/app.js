import { state } from './state.js';
import { qs } from './utils.js';
import { initTabs } from './tabs.js';
import { initMainMap, initMapControls } from './map.js';
import { initRoute } from './route.js';
import { initBriefing } from './briefing.js';
import { initPerformance } from './performance.js';
import { initAircraft, updateReference } from './aircraft.js';
import { initFlightPlans } from './flight-plans.js';
import * as api from './api.js';

async function init() {
    // Initialize tab switching
    initTabs(onTabChange);

    // Initialize aircraft first (loads list, sets selector)
    await initAircraft();

    // Initialize all feature modules
    initRoute();
    initBriefing();
    initPerformance();
    initMapControls();
    await initFlightPlans();

    // Load reference for default aircraft
    await updateReference();

    // Check database status
    await checkDbStatus();

    // Database update button
    qs('#btn-update-db').addEventListener('click', async () => {
        const btn = qs('#btn-update-db');
        btn.disabled = true;
        btn.textContent = 'Updating...';
        await api.updateDatabase();
        pollDbStatus();
    });
}

function onTabChange(tabId) {
    if (tabId === 'map') {
        // Initialize map on first visit (lazy load)
        setTimeout(async () => {
            await initMainMap();
            state.mainMap.invalidateSize();
        }, 100);
    }
}

async function checkDbStatus() {
    try {
        const status = await api.getDataStatus();
        updateDbIndicator(status);
        if (status.in_progress) {
            pollDbStatus();
        }
    } catch (e) {
        qs('#db-label').textContent = 'Offline';
        qs('#db-dot').classList.add('empty');
    }
}

function pollDbStatus() {
    const interval = setInterval(async () => {
        const status = await api.getDataStatus();
        updateDbIndicator(status);
        if (!status.in_progress) {
            clearInterval(interval);
            qs('#btn-update-db').disabled = false;
            qs('#btn-update-db').textContent = 'Update DB';
        }
    }, 2000);
}

function updateDbIndicator(status) {
    const dot = qs('#db-dot');
    const label = qs('#db-label');

    if (status.in_progress) {
        dot.classList.add('empty');
        label.textContent = status.message || 'Updating...';
    } else if (status.airports > 0) {
        dot.classList.remove('empty');
        label.textContent = `${status.airports.toLocaleString()} airports`;
    } else {
        dot.classList.add('empty');
        label.textContent = 'No data - click Update DB';
    }
}

// Boot
document.addEventListener('DOMContentLoaded', init);
