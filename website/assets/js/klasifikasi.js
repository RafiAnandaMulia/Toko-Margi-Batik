// ─────────────────────────────────────────
// Preview gambar sebelum upload
// ─────────────────────────────────────────

const imageInput = document.getElementById('imageInput');
const previewBox = document.getElementById('previewBox');
const previewImg = document.getElementById('previewImg');
const previewName = document.getElementById('previewName');
const dropZone = document.getElementById('dropZone');
const submitBtn = document.getElementById('submitBtn');

if (imageInput) {

    imageInput.addEventListener('change', function () {

        const file = this.files[0];

        if (!file) return;

        const reader = new FileReader();

        reader.onload = function (e) {

            previewImg.src = e.target.result;

            previewName.textContent =
                file.name +
                ' (' +
                (file.size / 1024 / 1024).toFixed(2) +
                ' MB)';

            previewBox.style.display = 'block';

            dropZone.style.borderColor = '#7B3F00';

        };

        reader.readAsDataURL(file);

    });

}

// ─────────────────────────────────────────
// Drag & Drop Upload
// ─────────────────────────────────────────

if (dropZone) {

    dropZone.addEventListener('dragover', function (e) {

        e.preventDefault();

        dropZone.classList.add('dragover');

    });

    dropZone.addEventListener('dragleave', function () {

        dropZone.classList.remove('dragover');

    });

    dropZone.addEventListener('drop', function (e) {

        e.preventDefault();

        dropZone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];

        if (file && file.type.startsWith('image/')) {

            const dt = new DataTransfer();

            dt.items.add(file);

            imageInput.files = dt.files;

            imageInput.dispatchEvent(
                new Event('change')
            );

        }

    });

}

// ─────────────────────────────────────────
// Loading saat submit
// ─────────────────────────────────────────

const classifyForm =
    document.getElementById('classifyForm');

if (classifyForm) {

    classifyForm.addEventListener(
        'submit',
        function () {

            if (submitBtn) {

                submitBtn.disabled = true;

                submitBtn.innerHTML =
                    'Sedang menganalisis...';

            }

        }
    );

}