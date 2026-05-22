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
        saveBtn.disabled = true;
        view.classList.add('hidden');
        input.classList.remove('hidden');
        editBtn.classList.add('hidden');
        saveBtn.classList.remove('hidden');
        cancelBtn.classList.remove('hidden');
        input.focus();
    }

    input.addEventListener('input', () => {
        saveBtn.disabled = !input.value.trim() || input.value.trim() === input.defaultValue.trim();
    })

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
const modalIcon = modal.querySelector('[data-modal-icon]');
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
    modalIcon.className = `fa-brands fa-${platform} text-lg text-sky-400`;
    modalFields.innerHTML = data.fields.map(f => `
        <div>
            <label class="block text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1.5">${f.label}</label>
            <input type="${f.type}" name="${f.key}" value="${data.values[f.key] || ''}"
                ${f.type === 'password' ? 'placeholder="Enter to update"' : ''}
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
    const icon = success === true ? '<i class="fa-solid fa-circle-check text-emerald-400"></i>' : success === false ? '<i class="fa-solid fa-circle-xmark text-rose-400"></i>' : '';

    const line = document.createElement('div');
    line.className = `${color} font-medium text-sm`;
    line.innerHTML = icon ? `${icon} ` : '';
    line.appendChild(document.createTextNode(summary));
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

// Template modal
const templateModal = document.getElementById('template-modal');
const templateCard = document.getElementById('template-card');
const templateFile = document.getElementById('template-file');
const templateUploadBtn = document.getElementById('template-upload-btn');
const templateResult = document.getElementById('template-result');

templateCard.addEventListener('click', () => templateModal.showModal());
templateModal.querySelectorAll('[data-template-close]').forEach(b =>
    b.addEventListener('click', () => templateModal.close())
);

function showTemplateResult(success, message) {
    templateResult.classList.remove('hidden');
    const color = success === true ? 'text-emerald-400' : success === false ? 'text-rose-400' : 'text-zinc-400';
    const icon = success === true
        ? '<i class="fa-solid fa-circle-check"></i> '
        : success === false ? '<i class="fa-solid fa-circle-xmark"></i> ' : '';
    templateResult.className = `text-xs ${color} font-medium`;
    templateResult.innerHTML = icon;
    templateResult.appendChild(document.createTextNode(message));
}

templateFile.addEventListener('change', () => {
    templateUploadBtn.disabled = !templateFile.files.length;
    templateResult.classList.add('hidden');
});

// Color palette copy
document.querySelectorAll('[data-copy-color]').forEach(btn => {
    btn.addEventListener('click', async () => {
        const hex = btn.dataset.copyColor;
        const icon = btn.querySelector('i');
        try {
            await navigator.clipboard.writeText(hex);
            const prev = icon.className;
            icon.className = 'fa-solid fa-check text-[10px] text-emerald-400';
            setTimeout(() => { icon.className = prev; }, 1000);
        } catch (e) {
            alert(`Copy failed: ${e.message}`);
        }
    });
});

// ntfy
(() => {
    const card = document.getElementById('ntfy-card');
    if (!card) return;
    const modal = document.getElementById('ntfy-modal');
    const toggle = document.getElementById('ntfy-toggle');
    const topicInput = document.getElementById('ntfy-topic-input');
    const regenBtn = document.getElementById('ntfy-regenerate-btn');
    const testBtn = document.getElementById('ntfy-test-btn');
    const saveBtn = document.getElementById('ntfy-save-btn');
    const subscribeUrl = document.getElementById('ntfy-subscribe-url');
    const result = document.getElementById('ntfy-result');
    const server = JSON.parse(document.getElementById('ntfy-server-data').textContent);

    function updateSubscribeUrl() {
        const t = topicInput.value.trim();
        const url = `${server}/${t}`;
        subscribeUrl.textContent = url;
        subscribeUrl.href = url;
    }

    function showResult(success, summary, detail) {
        result.classList.remove('hidden');
        result.innerHTML = '';
        const color = success === true ? 'text-emerald-400'
            : success === false ? 'text-rose-400'
                : 'text-zinc-400';
        const icon = success === true ? '<i class="fa-solid fa-circle-check"></i> '
            : success === false ? '<i class="fa-solid fa-circle-xmark"></i> '
                : '';
        const line = document.createElement('div');
        line.className = `${color} font-medium text-sm`;
        line.innerHTML = icon;
        line.appendChild(document.createTextNode(summary));
        result.appendChild(line);
        if (detail) {
            const det = document.createElement('details');
            det.className = 'mt-2';
            const sumEl = document.createElement('summary');
            sumEl.textContent = 'Show details';
            sumEl.className = 'cursor-pointer text-[11px] text-zinc-500 hover:text-zinc-300 select-none';
            det.appendChild(sumEl);
            const pre = document.createElement('pre');
            pre.textContent = detail;
            pre.className = 'mt-2 p-2 bg-zinc-950 rounded text-[10px] text-zinc-400 overflow-x-auto whitespace-pre-wrap break-all border border-zinc-800 font-mono';
            det.appendChild(pre);
            result.appendChild(det);
        }
    }

    card.addEventListener('click', () => {
        topicInput.dataset.original = topicInput.value;
        saveBtn.disabled = true;
        result.classList.add('hidden');
        updateSubscribeUrl();
        modal.showModal();
    });
    modal.querySelectorAll('[data-ntfy-close]').forEach(b =>
        b.addEventListener('click', () => modal.close())
    );

    topicInput.addEventListener('input', () => {
        updateSubscribeUrl();
        const v = topicInput.value.trim();
        saveBtn.disabled = !v || v === (topicInput.dataset.original || '');
    });

    regenBtn.addEventListener('click', async () => {
        regenBtn.disabled = true;
        try {
            const res = await fetch('/config/ntfy/regenerate', { method: 'POST' });
            const data = await res.json().catch(() => ({}));
            if (res.ok) {
                topicInput.value = data.topic;
                updateSubscribeUrl();
                saveBtn.disabled = topicInput.value.trim() === (topicInput.dataset.original || '');
                showResult(null, 'Candidate generated. Click Save to apply.', null);
            } else {
                showResult(false, data.detail || `Failed (${res.status})`, null);
            }
        } finally {
            regenBtn.disabled = false;
        }
    });

    saveBtn.addEventListener('click', async () => {
        const v = topicInput.value.trim();
        const res = await fetch('/config/ntfy/topic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'ntfy_topic', value: v }),
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok) {
            topicInput.dataset.original = v;
            saveBtn.disabled = true;
            showResult(true, 'Topic saved', null);
        } else {
            showResult(false, data.detail || `Save failed (${res.status})`, null);
        }
    });

    testBtn.addEventListener('click', async () => {
        testBtn.disabled = true;
        showResult(null, 'Sending test…', null);
        try {
            const res = await fetch('/config/ntfy/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: 'ntfy_topic', value: topicInput.value.trim() }),
            });
            const data = await res.json().catch(() => ({}));
            showResult(data.success, data.summary || 'No response', data.detail || null);
        } catch (e) {
            showResult(false, e.message, null);
        } finally {
            testBtn.disabled = false;
        }
    });

    toggle.addEventListener('change', async e => {
        const enabled = e.target.checked;
        const res = await fetch('/config/ntfy/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled }),
        });
        if (!res.ok) {
            e.target.checked = !enabled;
            const err = await res.json().catch(() => ({}));
            alert(err.detail || `Toggle failed (${res.status})`);
        }
    });
})();

templateUploadBtn.addEventListener('click', async () => {
    if (!templateFile.files.length) return;
    const formData = new FormData();
    formData.append('uploaded_file', templateFile.files[0]);

    showTemplateResult(null, 'Uploading…');
    templateUploadBtn.disabled = true;

    try {
        const res = await fetch('/config/template', { method: 'POST', body: formData });
        if (res.ok) {
            showTemplateResult(true, 'Uploaded successfully. Reloading…');
            setTimeout(() => location.reload(), 800);
        } else {
            const text = await res.text();
            showTemplateResult(false, text || `Upload failed (${res.status})`);
            templateUploadBtn.disabled = false;
        }
    } catch (e) {
        showTemplateResult(false, `Upload failed: ${e.message}`);
        templateUploadBtn.disabled = false;
    }
});
