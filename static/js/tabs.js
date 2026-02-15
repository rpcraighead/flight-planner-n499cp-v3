import { qs, qsa } from './utils.js';

export function initTabs(onTabChange) {
    const buttons = qsa('.tab-btn');
    const panels = qsa('.tab-panel');

    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;

            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            panels.forEach(p => p.classList.remove('active'));
            qs(`#tab-${tabId}`).classList.add('active');

            if (onTabChange) onTabChange(tabId);
        });
    });
}
