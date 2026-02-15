import { state } from './state.js';
import { qs } from './utils.js';
import * as api from './api.js';

let tileLayers = {};

function createTileLayers(sources) {
    tileLayers = {
        'VFR Sectional': L.tileLayer(sources.vfr, { maxZoom: 12, minZoom: 5, attribution: 'FAA / ArcGIS' }),
        'IFR Low Enroute': L.tileLayer(sources.ifr_low, { maxZoom: 11, minZoom: 5, attribution: 'FAA / ArcGIS' }),
        'IFR High Enroute': L.tileLayer(sources.ifr_high, { maxZoom: 11, minZoom: 5, attribution: 'FAA / ArcGIS' }),
        'Satellite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18, attribution: 'Esri' }),
        'Street': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: 'OSM' }),
    };
    return tileLayers;
}

async function ensureTileSources() {
    if (!state.tileSources) {
        state.tileSources = await api.getTileSources();
    }
    return state.tileSources;
}

export async function initMainMap() {
    if (state.mainMap) return;

    const sources = await ensureTileSources();
    const layers = createTileLayers(sources);

    state.mainMap = L.map('main-map', {
        center: [33.0, -117.0],
        zoom: 8,
        layers: [layers['VFR Sectional']],
    });

    L.control.layers(layers, {}, { position: 'topright' }).addTo(state.mainMap);
    state.routeLayer = L.layerGroup().addTo(state.mainMap);

    // Draw existing route if one was calculated before map tab was opened
    if (state.currentRoute) {
        drawRoute(state.currentRoute);
    }

    // Draw pending TFRs if weather was fetched before map tab was opened
    if (state.pendingTfrs) {
        drawTfrs(state.pendingTfrs);
        state.pendingTfrs = null;
    }
}

export async function initPreviewMap() {
    if (state.previewMap) return;

    const sources = await ensureTileSources();
    const layers = createTileLayers(sources);

    state.previewMap = L.map('route-preview-map', {
        center: [33.0, -117.0],
        zoom: 8,
        layers: [layers['VFR Sectional']],
        zoomControl: false,
        attributionControl: false,
    });
    state.previewRouteLayer = L.layerGroup().addTo(state.previewMap);
}

export function drawRoute(routeData) {
    if (!routeData || !routeData.route_points) return;

    const pts = routeData.route_points;
    const latLngs = pts.map(p => [p.latitude, p.longitude]);

    // Draw on main map (may not exist yet — initMainMap will handle it)
    if (state.routeLayer) {
        state.routeLayer.clearLayers();
        drawRouteOnLayer(state.routeLayer, pts, latLngs, routeData.segments);
    }

    // Draw on preview map
    if (state.previewRouteLayer) {
        state.previewRouteLayer.clearLayers();
        drawRouteOnLayer(state.previewRouteLayer, pts, latLngs, routeData.segments);
    }

    // Fit bounds
    if (latLngs.length > 1) {
        const bounds = L.latLngBounds(latLngs).pad(0.15);
        if (state.mainMap) state.mainMap.fitBounds(bounds);
        if (state.previewMap) {
            setTimeout(() => {
                state.previewMap.invalidateSize();
                state.previewMap.fitBounds(bounds);
            }, 100);
        }
    }
}

function drawRouteOnLayer(layer, pts, latLngs, segments) {
    // White outline
    L.polyline(latLngs, { color: 'white', weight: 6, opacity: 0.8 }).addTo(layer);
    // Colored line
    L.polyline(latLngs, { color: '#bf0a30', weight: 3, opacity: 0.9 }).addTo(layer);

    // Waypoint markers
    pts.forEach((pt, i) => {
        const isFirst = i === 0;
        const isLast = i === pts.length - 1;
        const color = isFirst ? '#28a745' : isLast ? '#bf0a30' : '#1e3a5f';
        const radius = (isFirst || isLast) ? 8 : 6;

        const marker = L.circleMarker([pt.latitude, pt.longitude], {
            radius: radius,
            fillColor: color,
            color: 'white',
            weight: 2,
            fillOpacity: 0.9,
        }).addTo(layer);

        let popupHtml = `<div class="popup-title">${pt.identifier}</div>`;
        if (pt.data) {
            if (pt.data.name) popupHtml += `<div class="popup-detail">${pt.data.name}</div>`;
            if (pt.data.elevation != null) popupHtml += `<div class="popup-detail">Elev: ${pt.data.elevation} ft</div>`;
        }
        if (segments && i < segments.length) {
            const seg = segments[i];
            popupHtml += `<div class="popup-detail" style="margin-top:4px">`;
            popupHtml += `To ${seg.to}: ${seg.distance_nm} nm, MH ${seg.magnetic_heading}°, ${seg.time_minutes} min`;
            popupHtml += `</div>`;
        }
        marker.bindPopup(popupHtml);

        // Permanent label
        L.marker([pt.latitude, pt.longitude], {
            icon: L.divIcon({
                className: '',
                html: `<div style="font-size:11px;font-weight:600;color:${color};text-shadow:1px 1px 2px white,-1px -1px 2px white,1px -1px 2px white,-1px 1px 2px white;white-space:nowrap">${pt.identifier}</div>`,
                iconAnchor: [-8, 4],
            }),
        }).addTo(layer);
    });
}

export function drawTfrs(tfrs) {
    // If map isn't ready yet, store for later
    if (!state.mainMap) {
        state.pendingTfrs = tfrs;
        return;
    }

    // Clear existing TFR layer
    if (state.tfrLayer) {
        state.tfrLayer.clearLayers();
    } else {
        state.tfrLayer = L.layerGroup().addTo(state.mainMap);
    }

    for (const tfr of tfrs) {
        if (tfr.type === 'INFO' || tfr.notam_id === 'ADVISORY') continue;

        const tfrStyle = {
            color: '#bf0a30',
            weight: 2,
            opacity: 0.8,
            fillColor: '#bf0a30',
            fillOpacity: 0.15,
            dashArray: '5,5',
        };

        const popupHtml = `<div class="popup-title">TFR: ${tfr.notam_id || ''}</div>
            <div class="popup-detail">${tfr.type || 'TFR'}</div>
            <div class="popup-detail" style="max-width:250px;font-size:0.8rem">${(tfr.description || '').slice(0, 200)}</div>
            ${tfr.effective ? `<div class="popup-detail">Eff: ${tfr.effective}</div>` : ''}
            ${tfr.expires ? `<div class="popup-detail">Exp: ${tfr.expires}</div>` : ''}`;

        // Circle TFR (has center_lat/center_lon and radius_nm from known TFRs)
        if (tfr.center_lat != null && tfr.center_lon != null) {
            const radiusMeters = (tfr.radius_nm || 3) * 1852;
            const circle = L.circle([tfr.center_lat, tfr.center_lon], {
                radius: radiusMeters,
                ...tfrStyle,
            });
            circle.bindPopup(popupHtml);
            circle.addTo(state.tfrLayer);
            continue;
        }

        if (!tfr.coords || !tfr.coords.length) continue;

        if (tfr.coords.length === 1) {
            // Point TFR — draw as circle (default 3nm radius)
            const coord = tfr.coords[0];
            if (Array.isArray(coord) && coord.length >= 2) {
                const circle = L.circle([coord[1], coord[0]], {
                    radius: 5556, // ~3nm in meters
                    ...tfrStyle,
                });
                circle.bindPopup(popupHtml);
                circle.addTo(state.tfrLayer);
            }
        } else if (tfr.coords.length > 2) {
            // Polygon TFR — GeoJSON coords are [lon, lat]
            const latLngs = tfr.coords
                .filter(c => Array.isArray(c) && c.length >= 2)
                .map(c => [c[1], c[0]]);
            if (latLngs.length > 2) {
                const polygon = L.polygon(latLngs, tfrStyle);
                polygon.bindPopup(popupHtml);
                polygon.addTo(state.tfrLayer);
            }
        }
    }
}

export function centerOnRoute() {
    if (!state.currentRoute || !state.mainMap) return;
    const pts = state.currentRoute.route_points;
    if (pts.length > 0) {
        const bounds = L.latLngBounds(pts.map(p => [p.latitude, p.longitude])).pad(0.15);
        state.mainMap.fitBounds(bounds);
    }
}

export function initMapControls() {
    const centerBtn = qs('#btn-center-route');
    if (centerBtn) centerBtn.addEventListener('click', centerOnRoute);

    const editBtn = qs('#btn-toggle-edit-mode');
    if (editBtn) {
        editBtn.addEventListener('click', () => {
            state.editMode = !state.editMode;
            editBtn.textContent = state.editMode ? 'Done Editing' : 'Edit Route on Map';
            editBtn.classList.toggle('btn-primary', state.editMode);
            editBtn.classList.toggle('btn-outline', !state.editMode);
        });
    }
}
