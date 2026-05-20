// Inline edit
document.querySelectorAll('[data-field-row]').forEach(row => {
    const key = row.dataset.key;
    const view = row.querySelector('[data-view]');
    const input = row.querySelector('[data-edit]');
    const editBtn = row.querySelector('[data-edit-btn]');
    const saveBtn = row.querySelector('[data-save-btn]');
    const cancelBtn = row.querySelector('[data-cancel-btn]');

    function enterEdit() {
        input.value = view.textContent.trim() === '—' ? '' : view.textContent.trim();
        view.classList.add('hidden');
        input.classList.remove('hidden');
        editBtn.classList.add('hidden');
        saveBtn.classList.remove('hidden');
        cancelBtn.classList.remove('hidden');
        input.focus();
    }

    function exitEdit(newValue) {
        if (newValue !== undefined) view.textContent = newValue || '—';
        view.classList.remove('hidden');
        input.classList.add('hidden');
        editBtn.classList.remove('hidden');
        saveBtn.classList.add('hidden');
        cancelBtn.classList.add('hidden');
    }

    editBtn.addEventListener('click', enterEdit);
    cancelBtn.addEventListener('click', () => exitEdit());
    saveBtn.addEventListener('click', async () => {
        const value = input.value.trim();
        const res = await fetch('/config/field', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, value }),
        });
        if (res.ok) {
            exitEdit(value);
        } else {
            const err = await res.json().catch(() => ({}));
            alert(`Save failed: ${err.detail || res.status}`);
        }
    });
});

// Platform toggle 
document.querySelectorAll('[data-platform-toggle]').forEach(toggle => {
    toggle.addEventListener('change', async (e) => {
        const platform = e.target.dataset.platform;
        const enabled = e.target.checked;
        const res = await fetch(`/config/platform/${platform}/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled }),
        });
        if (!res.ok) {
            e.target.checked = !enabled; // revert on failure
            const err = await res.json().catch(() => ({}));
            alert(err.detail || `Toggle failed (${res.status})`);
        }
    });
});

//  Modal
const modal = document.getElementById('platform-modal');
const modalTitle = modal.querySelector('[data-modal-title]');
const modalFields = modal.querySelector('[data-modal-fields]');
const modalResult = modal.querySelector('[data-modal-result]');
const modalSave = modal.querySelector('[data-modal-save]');
const modalTest = modal.querySelector('[data-modal-test]');
modal.querySelectorAll('[data-modal-close]').forEach(b => b.addEventListener('click', () => modal.close()));

const platformsData = JSON.parse(document.getElementById('platform-fields-data').textContent);
let currentPlatform = null;

function openModal(platform) {
    currentPlatform = platform;
    const data = platformsData[platform];
    modalTitle.textContent = data.name;
    modalFields.innerHTML = data.fields.map(f => `
        <div>
            <label class="block text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1.5">${f.label}</label>
            <input type="${f.type}" name="${f.key}" value="${data.values[f.key] || ''}"
                class="block w-full rounded-md bg-zinc-950 border border-zinc-800 text-zinc-100 px-3 py-1.5 text-sm
                       focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 focus:outline-none transition" />
        </div>
    `).join('');
    modalResult.classList.add('hidden');
    modal.showModal();
}

function collectFields() {
    const fields = {};
    modalFields.querySelectorAll('input').forEach(inp => fields[inp.name] = inp.value.trim());
    return fields;
}

function showResult(ok, msg) {
    modalResult.classList.remove('hidden', 'text-emerald-400', 'text-rose-400');
    modalResult.classList.add(ok ? 'text-emerald-400' : 'text-rose-400');
    modalResult.textContent = msg;
}

modalSave.addEventListener('click', async () => {
    const res = await fetch(`/config/platform/${currentPlatform}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: collectFields() }),
    });
    if (res.ok) {
        location.reload();
    } else {
        showResult(false, 'Save failed');
    }
});

modalTest.addEventListener('click', async () => {
    showResult(true, 'Testing…');
    const res = await fetch(`/config/test/${currentPlatform}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: collectFields() }),
    });
    const data = await res.json();
    showResult(data.ok, data.message);
});

document.querySelectorAll('[data-platform-card]').forEach(card => {
    card.addEventListener('click', () => openModal(card.dataset.platform));
});
