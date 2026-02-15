import { state } from './state.js';
import { qs, fltcatBadge } from './utils.js';
import * as api from './api.js';
import { drawTfrs } from './map.js';

export function initBriefing() {
    qs('#btn-get-briefing').addEventListener('click', getBriefing);
}

async function getBriefing() {
    if (!state.currentRoute) {
        qs('#briefing-content').innerHTML = '<div class="alert alert-warning">Calculate a route first.</div>';
        return;
    }

    const btn = qs('#btn-get-briefing');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Fetching...';

    try {
        const pts = state.currentRoute.route_points;
        const depTimeEl = qs('#departure-time');
        const depTime = depTimeEl ? depTimeEl.value : '';

        const result = await api.getWeatherBriefing({
            departure: pts[0]?.identifier || '',
            destination: pts[pts.length - 1]?.identifier || '',
            waypoints: pts.slice(1, -1).map(p => p.identifier),
            departure_time: depTime,
        });

        if (!result.success) {
            qs('#briefing-content').innerHTML = `<div class="alert alert-danger">${escapeHtml(result.error)}</div>`;
            return;
        }

        state.currentWeather = result;
        displayBriefing(result.briefing);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Get Briefing';
    }
}

function displayBriefing(b) {
    const container = qs('#briefing-content');
    let html = '';

    const depTimeStr = b.departure_time && b.departure_time !== 'Now'
        ? b.departure_time : 'Now';
    html += `<div class="alert alert-info" style="margin-bottom:var(--space-md)">
        <strong>Route:</strong> ${escapeHtml(b.route)} &nbsp;|&nbsp;
        <strong>Departure:</strong> ${escapeHtml(depTimeStr)} &nbsp;|&nbsp;
        <strong>Generated:</strong> ${escapeHtml(b.generated_at)}
    </div>`;

    // TFRs first — safety critical
    html += renderTfrs(b.tfrs);

    // AIRMETs / SIGMETs
    html += renderAirmetsSigmets(b.airmets_sigmets);

    // PIREPs
    html += renderPireps(b.pireps);

    // METARs
    html += renderMetars(b.metars);

    // TAFs
    html += renderTafs(b.tafs);

    // Winds aloft
    html += renderWinds(b.winds_aloft);

    // NOTAMs
    html += renderNotams(b.notams);

    container.innerHTML = html;

    // Draw TFRs on map if available
    if (b.tfrs && b.tfrs.length) {
        drawTfrs(b.tfrs);
    }
}

// ---------------------------------------------------------------------------
// TFRs
// ---------------------------------------------------------------------------

function renderTfrs(tfrs) {
    if (!tfrs || !tfrs.length) return '';

    let html = `<h3 style="margin:var(--space-md) 0 var(--space-sm);color:var(--color-danger)">
        &#9888; Temporary Flight Restrictions</h3>`;

    for (const t of tfrs) {
        const isInfo = t.type === 'INFO' || t.notam_id === 'ADVISORY';
        const bgColor = isInfo
            ? 'var(--color-bg)'
            : 'rgba(191,10,48,0.08)';
        const borderColor = isInfo
            ? 'var(--color-border)'
            : 'var(--color-danger)';

        html += `<div style="margin-bottom:var(--space-sm);padding:var(--space-sm);background:${bgColor};border-left:3px solid ${borderColor};border-radius:var(--radius)">`;

        // Header row
        html += `<div style="display:flex;gap:var(--space-sm);align-items:center;flex-wrap:wrap;margin-bottom:4px">`;
        if (t.notam_id && t.notam_id !== 'INFO' && t.notam_id !== 'ADVISORY') {
            html += `<strong>${escapeHtml(t.notam_id)}</strong>`;
        }
        if (t.type && t.type !== 'INFO') {
            html += `<span class="badge" style="background:var(--color-danger);color:white">${escapeHtml(t.type)}</span>`;
        }
        html += `</div>`;

        // Description
        html += `<div style="font-size:0.85rem;margin-bottom:4px">${escapeHtml(t.description)}</div>`;

        // Dates
        if (t.effective || t.expires) {
            html += `<div style="font-size:0.8rem;color:var(--color-text-muted)">`;
            if (t.effective) html += `Effective: ${escapeHtml(t.effective)} `;
            if (t.expires) html += `Expires: ${escapeHtml(t.expires)}`;
            html += `</div>`;
        }

        // Detail link (from scrape fallback)
        if (t.detail_url) {
            html += `<div style="margin-top:4px"><a href="${escapeHtml(t.detail_url)}" target="_blank" rel="noopener" style="font-size:0.8rem">View TFR Details &rarr;</a></div>`;
        }

        html += `</div>`;
    }

    return html;
}

// ---------------------------------------------------------------------------
// AIRMETs / SIGMETs
// ---------------------------------------------------------------------------

function renderAirmetsSigmets(items) {
    if (!items || !items.length) return '';

    let html = `<h3 style="margin:var(--space-md) 0 var(--space-sm)">AIRMETs / SIGMETs</h3>`;

    for (const item of items) {
        const isSigmet = item.type && item.type.toUpperCase().includes('SIGMET');
        const borderColor = isSigmet ? 'var(--color-danger)' : 'var(--color-warning)';
        const bgColor = isSigmet ? 'rgba(191,10,48,0.06)' : 'rgba(255,193,7,0.08)';

        html += `<div style="margin-bottom:var(--space-sm);padding:var(--space-sm);background:${bgColor};border-left:3px solid ${borderColor};border-radius:var(--radius)">`;

        // Header
        html += `<div style="display:flex;gap:var(--space-sm);align-items:center;flex-wrap:wrap;margin-bottom:4px">`;
        html += `<span class="badge" style="background:${borderColor};color:white">${escapeHtml(item.type || 'AIRMET')}</span>`;
        if (item.hazard) {
            html += `<strong>${escapeHtml(item.hazard)}</strong>`;
        }
        if (item.severity) {
            html += `<span style="font-size:0.8rem;color:var(--color-text-muted)">${escapeHtml(item.severity)}</span>`;
        }
        html += `</div>`;

        // Raw text
        if (item.raw) {
            html += `<code style="font-size:0.8rem;word-break:break-all;display:block;margin-bottom:4px">${escapeHtml(item.raw)}</code>`;
        }

        // Altitude and validity
        let details = [];
        if (item.altitude_low || item.altitude_high) {
            details.push(`Alt: ${item.altitude_low || 'SFC'} - ${item.altitude_high || 'UNL'}`);
        }
        if (item.valid_from || item.valid_to) {
            details.push(`Valid: ${item.valid_from || '?'} to ${item.valid_to || '?'}`);
        }
        if (details.length) {
            html += `<div style="font-size:0.8rem;color:var(--color-text-muted)">${escapeHtml(details.join(' | '))}</div>`;
        }

        html += `</div>`;
    }

    return html;
}

// ---------------------------------------------------------------------------
// PIREPs
// ---------------------------------------------------------------------------

function renderPireps(pireps) {
    if (!pireps || !pireps.length) return '';

    let html = `<h3 style="margin:var(--space-md) 0 var(--space-sm)">Pilot Reports (PIREPs)</h3>`;

    for (const p of pireps) {
        const isUrgent = p.type === 'UUA';
        const bgColor = isUrgent ? 'rgba(191,10,48,0.06)' : 'var(--color-bg)';
        const borderColor = isUrgent ? 'var(--color-danger)' : 'var(--color-border)';

        html += `<div style="margin-bottom:var(--space-sm);padding:var(--space-sm);background:${bgColor};border-left:3px solid ${borderColor};border-radius:var(--radius)">`;

        // Header
        html += `<div style="display:flex;gap:var(--space-sm);align-items:center;flex-wrap:wrap;margin-bottom:4px">`;
        if (isUrgent) {
            html += `<span class="badge" style="background:var(--color-danger);color:white">URGENT</span>`;
        } else {
            html += `<span class="badge" style="background:var(--color-primary);color:white">PIREP</span>`;
        }
        html += `<strong>${escapeHtml(p.station || '')}</strong>`;
        if (p.altitude) {
            html += `<span style="font-size:0.8rem">FL${escapeHtml(String(p.altitude))}</span>`;
        }
        if (p.aircraft) {
            html += `<span style="font-size:0.8rem;color:var(--color-text-muted)">${escapeHtml(p.aircraft)}</span>`;
        }
        html += `</div>`;

        // Raw text
        html += `<code style="font-size:0.8rem;word-break:break-all;display:block;margin-bottom:4px">${escapeHtml(p.rawOb || '')}</code>`;

        // Turbulence and icing highlights
        let highlights = [];
        if (p.turbulence) {
            highlights.push(`<span style="color:var(--color-warning);font-weight:600">Turb: ${escapeHtml(p.turbulence)}</span>`);
        }
        if (p.icing) {
            highlights.push(`<span style="color:var(--color-info);font-weight:600">Ice: ${escapeHtml(p.icing)}</span>`);
        }
        if (highlights.length) {
            html += `<div style="font-size:0.85rem;display:flex;gap:var(--space-md)">${highlights.join('')}</div>`;
        }

        html += `</div>`;
    }

    return html;
}

// ---------------------------------------------------------------------------
// METARs
// ---------------------------------------------------------------------------

function renderMetars(metars) {
    if (!metars || !metars.length) return '';

    let html = `<h3 style="margin:var(--space-md) 0 var(--space-sm)">METARs</h3>`;
    for (const m of metars) {
        const sim = m.simulated ? '<span class="badge badge-sim">SIM</span> ' : '';
        html += `<div style="margin-bottom:var(--space-sm);padding:var(--space-sm);background:var(--color-bg);border-radius:var(--radius)">
            <div style="display:flex;gap:var(--space-sm);align-items:center;margin-bottom:4px">
                <strong>${escapeHtml(m.icaoId || '')}</strong> ${fltcatBadge(m.fltcat)} ${sim}
            </div>
            <code style="font-size:0.8rem;word-break:break-all">${escapeHtml(m.rawOb || '')}</code>
        </div>`;
    }
    return html;
}

// ---------------------------------------------------------------------------
// TAFs
// ---------------------------------------------------------------------------

function renderTafs(tafs) {
    if (!tafs || !tafs.length) return '';

    let html = `<h3 style="margin:var(--space-md) 0 var(--space-sm)">TAFs</h3>`;
    for (const t of tafs) {
        const sim = t.simulated ? '<span class="badge badge-sim">SIM</span> ' : '';
        html += `<div style="margin-bottom:var(--space-sm);padding:var(--space-sm);background:var(--color-bg);border-radius:var(--radius)">
            <strong>${escapeHtml(t.icaoId || '')}</strong> ${sim}<br>
            <code style="font-size:0.8rem;word-break:break-all">${escapeHtml(t.rawTAF || '')}</code>
        </div>`;
    }
    return html;
}

// ---------------------------------------------------------------------------
// Winds Aloft
// ---------------------------------------------------------------------------

function renderWinds(winds) {
    if (!winds || !winds.levels) return '';

    let html = `<h3 style="margin:var(--space-md) 0 var(--space-sm)">Winds Aloft (Estimated)</h3>`;
    html += `<table class="data-table"><thead><tr><th>Altitude</th><th>Direction</th><th>Speed</th><th>Temp</th></tr></thead><tbody>`;
    for (const [alt, data] of Object.entries(winds.levels)) {
        html += `<tr><td>${Number(alt).toLocaleString()} ft</td><td>${data.direction}&deg;</td><td>${data.speed} kt</td><td>${data.temp}&deg;C</td></tr>`;
    }
    html += `</tbody></table>`;
    return html;
}

// ---------------------------------------------------------------------------
// NOTAMs
// ---------------------------------------------------------------------------

function renderNotams(notams) {
    if (!notams || !notams.length) return '';

    let html = `<h3 style="margin:var(--space-md) 0 var(--space-sm)">NOTAMs</h3>`;

    // Group by airport
    const grouped = {};
    for (const n of notams) {
        const apt = n.airport || 'UNKNOWN';
        if (!grouped[apt]) grouped[apt] = [];
        grouped[apt].push(n);
    }

    for (const [airport, items] of Object.entries(grouped)) {
        html += `<div style="margin-bottom:var(--space-md)">`;
        html += `<h4 style="margin:0 0 var(--space-xs);font-size:0.9rem">${escapeHtml(airport)}</h4>`;

        for (const n of items) {
            const isSimulated = n.simulated;
            const bgColor = isSimulated ? 'var(--color-bg)' : 'var(--color-bg)';

            html += `<div style="margin-bottom:var(--space-xs);padding:var(--space-sm);background:${bgColor};border-radius:var(--radius);font-size:0.85rem">`;

            // Header with NOTAM ID and classification
            html += `<div style="display:flex;gap:var(--space-sm);align-items:center;flex-wrap:wrap;margin-bottom:2px">`;
            if (n.notam_id) {
                html += `<strong style="font-size:0.8rem">${escapeHtml(n.notam_id)}</strong>`;
            }
            if (n.classification && n.classification !== 'NONE') {
                const clsBg = n.classification === 'ERROR' ? 'var(--color-danger)'
                    : n.classification === 'INFO' ? 'var(--color-info)'
                    : 'var(--color-text-muted)';
                html += `<span class="badge" style="background:${clsBg};color:white;font-size:0.7rem">${escapeHtml(n.classification)}</span>`;
            }
            if (n.simulated) {
                html += `<span class="badge badge-sim">NO API KEY</span>`;
            }
            html += `</div>`;

            // NOTAM text - make URLs clickable
            const text = escapeHtml(n.text || '').replace(
                /(https?:\/\/[^\s<]+)/g,
                '<a href="$1" target="_blank" rel="noopener">$1</a>'
            );
            html += `<div>${text}</div>`;

            // Effective dates
            if (n.effective || n.expires) {
                html += `<div style="font-size:0.75rem;color:var(--color-text-muted);margin-top:2px">`;
                if (n.effective) html += `Eff: ${escapeHtml(n.effective)} `;
                if (n.expires) html += `Exp: ${escapeHtml(n.expires)}`;
                html += `</div>`;
            }

            html += `</div>`;
        }

        html += `</div>`;
    }

    return html;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
