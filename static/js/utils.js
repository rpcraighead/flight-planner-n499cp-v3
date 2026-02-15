export const qs = (sel, parent = document) => parent.querySelector(sel);
export const qsa = (sel, parent = document) => parent.querySelectorAll(sel);

export function el(tag, attrs = {}, children = []) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
        if (k === 'text') e.textContent = v;
        else if (k === 'html') e.innerHTML = v;
        else if (k === 'className') e.className = v;
        else if (k === 'style' && typeof v === 'object') Object.assign(e.style, v);
        else if (k.startsWith('on')) e.addEventListener(k.slice(2).toLowerCase(), v);
        else e.setAttribute(k, v);
    }
    for (const child of children) {
        if (typeof child === 'string') e.appendChild(document.createTextNode(child));
        else if (child) e.appendChild(child);
    }
    return e;
}

export function summaryItem(label, value) {
    return `<div class="summary-item"><div class="label">${label}</div><div class="value">${value}</div></div>`;
}

export function fltcatBadge(cat) {
    const c = (cat || 'VFR').toUpperCase();
    return `<span class="badge badge-${c.toLowerCase()}">${c}</span>`;
}

export function showAlert(container, type, message) {
    container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}

export function formatNum(n, decimals = 0) {
    if (n == null) return '-';
    return Number(n).toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}
