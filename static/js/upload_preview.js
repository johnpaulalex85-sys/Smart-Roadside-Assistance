/* upload_preview.js — Drag & drop file upload with preview */

document.addEventListener('DOMContentLoaded', () => {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('mediaInput');
    const preview = document.getElementById('previewContainer');
    if (!zone || !input) return;

    // Click on zone opens file picker
    zone.addEventListener('click', () => input.click());

    // Drag & Drop
    ['dragenter', 'dragover'].forEach(evt =>
        zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.add('dragover'); })
    );
    ['dragleave', 'drop'].forEach(evt =>
        zone.addEventListener(evt, () => zone.classList.remove('dragover'))
    );
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    input.addEventListener('change', () => handleFiles(input.files));

    const ALLOWED = ['image/jpeg', 'image/jpg', 'image/png', 'video/mp4'];
    const MAX_SIZE = 50 * 1024 * 1024; // 50 MB
    let selectedFiles = [];

    function handleFiles(fileList) {
        Array.from(fileList).forEach(file => {
            if (!ALLOWED.includes(file.type)) {
                alert(`File type not allowed: ${file.name}. Use jpg, png or mp4.`);
                return;
            }
            if (file.size > MAX_SIZE) {
                alert(`File too large: ${file.name}. Max 50 MB.`);
                return;
            }
            selectedFiles.push(file);
            renderPreview(file, selectedFiles.length - 1);
        });
        updateInputFiles();
    }

    function renderPreview(file, idx) {
        const wrapper = document.createElement('div');
        wrapper.className = 'rr-preview-item';
        wrapper.dataset.index = idx;

        if (file.type.startsWith('video/')) {
            const v = document.createElement('video');
            v.src = URL.createObjectURL(file);
            v.className = 'rr-preview-img';
            v.muted = true;
            wrapper.appendChild(v);
        } else {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.className = 'rr-preview-img';
            img.alt = file.name;
            wrapper.appendChild(img);
        }

        const nameTag = document.createElement('div');
        nameTag.style.cssText = 'font-size:0.65rem;color:#94a3b8;margin-top:4px;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center;';
        nameTag.textContent = file.name;
        wrapper.appendChild(nameTag);

        const removeBtn = document.createElement('button');
        removeBtn.className = 'rr-preview-remove';
        removeBtn.innerHTML = '✕';
        removeBtn.title = 'Remove';
        removeBtn.addEventListener('click', e => {
            e.stopPropagation();
            selectedFiles.splice(parseInt(wrapper.dataset.index), 1);
            preview.innerHTML = '';
            selectedFiles.forEach((f, i) => renderPreview(f, i));
            updateInputFiles();
        });
        wrapper.appendChild(removeBtn);
        preview.appendChild(wrapper);
    }

    function updateInputFiles() {
        const dt = new DataTransfer();
        selectedFiles.forEach(f => dt.items.add(f));
        input.files = dt.files;
    }
});
