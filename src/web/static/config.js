// Inline edit
document.querySelectorAll('[data-field-row]').forEach(row => {
    const key = row.dataset.key;
    const view = row.querySelector('[data-view]');
    const input = row.querySelector('[data-edit]');
    const editBtn = row.querySelector('[data-edit-btn]');
    const saveBtn = row.querySelector('[data-save-btn]');
    const cancelBtn = row.querySelector('[data-cancel-btn]');

    function enterEdit() {
        input.value = input.defaultValue;
        view.classList.add('hidden');
        input.classList.remove('hidden');
        editBtn.classList.add('hidden');
        saveBtn.classList.remove('hidden');
        cancelBtn.classList.remove('hidden');
        input.focus();
    }

    function exitEdit(newValue) {
        if (newValue !== undefined) view.textContent = newValue.replace('T', ' ') || '—';
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
            input.defaultValue = value;
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
    modalFields.querySelectorAll('input').forEach(input => {
        input.addEventListener('input', () => {
            modalSave.disabled = true;
            showResult(null, 'Test required before saving', null);
        })
    })
    showResult(null, 'Test required before saving', null);
    modalSave.disabled = true;
    modal.showModal();
}

function collectFields() {
    const fields = {};
    modalFields.querySelectorAll('input').forEach(inp => fields[inp.name] = inp.value.trim());
    return fields;
}

function showResult(success, summary, detail) {
    modalResult.classList.remove('hidden');
    modalResult.innerHTML = '';

    const color = success === true ? 'text-emerald-400' : success === false ? 'text-rose-400' : 'text-zinc-400';
    const icon = success === true ? '✓' : success === false ? '✗' : '';

    const line = document.createElement('div');
    line.className = `${color} font-medium text-sm`;
    line.textContent = `${icon} ${summary}`;
    modalResult.appendChild(line);

    if (detail) {
        const details = document.createElement('details');
        details.className = 'mt-2';

        const summaryEl = document.createElement('summary');
        summaryEl.textContent = 'Show details';
        summaryEl.className = 'cursor-pointer text-[11px] text-zinc-500 hover:text-zinc-300 select-none';
        details.appendChild(summaryEl);

        const pre = document.createElement('pre');
        pre.textContent = detail;
        pre.className = 'mt-2 p-2 bg-zinc-950 rounded text-[10px] text-zinc-400 overflow-x-auto whitespace-pre-wrap break-all border border-zinc-800 font-mono';
        details.appendChild(pre);

        modalResult.appendChild(details);
    }
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
        showResult(false, 'Save failed', null);
    }
});

modalTest.addEventListener('click', async () => {
    showResult(null, 'Testing…', null);
    modalTest.disabled = true;
    const res = await fetch(`/config/test/${currentPlatform}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: collectFields() }),
    });
    const data = await res.json();
    showResult(data.success, data.summary, data.detail);
    modalSave.disabled = !data.success;
    modalTest.disabled = false;
});

document.querySelectorAll('[data-platform-card]').forEach(card => {
    card.addEventListener('click', () => openModal(card.dataset.platform));
});
