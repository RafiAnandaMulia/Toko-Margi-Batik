<?php
/**
 * =============================================================
 * website/customer/klasifikasi.php
 * Halaman klasifikasi batik untuk customer (Sistem 17 Motif Lengkap)
 * =============================================================
 */
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/session.php';
require_once __DIR__ . '/../api/flask_api.php';

$result_data  = null;
$upload_error = null;
$saved_image  = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['batik_image'])) {
    $file = $_FILES['batik_image'];
    $allowed_ext  = ['jpg', 'jpeg', 'png', 'webp', 'bmp'];
    $allowed_mime = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp'];

    if ($file['error'] !== UPLOAD_ERR_OK) {
        $upload_error = 'Upload gagal. Coba lagi.';
    } elseif ($file['size'] > 10 * 1024 * 1024) {
        $upload_error = 'Ukuran file terlalu besar (maksimal 10MB).';
    } else {
        $finfo    = finfo_open(FILEINFO_MIME_TYPE);
        $mimetype = finfo_file($finfo, $file['tmp_name']);
        finfo_close($finfo);
        $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));

        if (!in_array($mimetype, $allowed_mime) || !in_array($ext, $allowed_ext)) {
            $upload_error = 'Format file tidak didukung. Gunakan JPG, PNG, atau WEBP.';
        } else {
            // KODE BARU (Lebih Pasti):
$upload_dir = $_SERVER['DOCUMENT_ROOT'] . '/BATIK_CLASSIFICATION_SYSTEM/website/uploads/klasifikasi/';
            if (!is_dir($upload_dir)) mkdir($upload_dir, 0755, true);

            $new_filename = 'klasifikasi_' . uniqid() . '.' . $ext;
            $dest_path    = $upload_dir . $new_filename;

            if (move_uploaded_file($file['tmp_name'], $dest_path)) {
                $api_result = flaskPredictImage($dest_path);

                if ($api_result['success']) {
                    $result_data = $api_result['data'];
                    $saved_image = $new_filename;

                    $user_id    = isLoggedIn() ? (int)$_SESSION['user_id'] : null;
                    $session_id = session_id();

                    dbExecute(
                        "INSERT INTO classification_history
                         (user_id, session_id, image_filename, image_path,
                          predicted_class, confidence, top_predictions,
                          model_version, ip_address)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        [
                            $user_id, $session_id, $new_filename, 'klasifikasi/' . $new_filename,
                            $result_data['predicted_class'], $result_data['confidence'],
                            json_encode($result_data['top_predictions'] ?? []),
                            $result_data['model_used'] ?? 'unknown', $_SERVER['REMOTE_ADDR'] ?? null
                        ]
                    );

                    $category_info = dbQueryOne(
                        "SELECT * FROM batik_categories WHERE slug = ? AND is_active = 1",
                        [$result_data['predicted_class']]
                    );
                    $result_data['category_info'] = $category_info;

                    // Evaluasi batas tingkat keyakinan (Confidence threshold < 60%)
                    $confidence = (float)($result_data['confidence'] ?? 0);
                    $is_low_confidence = $confidence < 60;
                } else {
                    $upload_error = $api_result['data']['error'] ?? 'Prediksi gagal. Pastikan model sudah dilatih.';
                    @unlink($dest_path);
                }
            } else {
                $upload_error = 'Gagal menyimpan file. Periksa permission folder.';
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Klasifikasi Batik — Margi Batik</title>
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/klasifikasi.css" rel="stylesheet">
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .pure-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }
        /* Pembungkus utama seluruh area prediksi */
        .extended-predictions {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .extended-predictions.open {
            max-height: 3000px; /* Kapasitas tinggi menampung ke-17 baris */
        }
        .btn-toggle-view {
            display: block;
            width: 100%;
            background: #fff;
            color: #7B3F00;
            border: 2px dashed #7B3F00;
            padding: 15px;
            font-size: 15px;
            font-weight: 700;
            border-radius: 12px;
            cursor: pointer;
            text-align: center;
            margin-top: 5px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }
        .btn-toggle-view:hover {
            background: #7B3F00;
            color: #fff;
            border-style: solid;
        }
    </style>
</head>
<body style="background:#F8F4F0; min-height:100vh; display:flex; flex-direction:column; margin:0; padding:0; font-family:sans-serif;">

    <?php include __DIR__ . '/../includes/navbar_customer.php'; ?>

    <section class="hero-section" style="padding: 40px 0; text-align:center;">
        <div class="hero-container-center">
            <h1 class="hero-title" style="font-size:28px; margin-bottom:10px;">Klasifikasi Batik AI</h1>
            <p class="hero-subtitle" style="margin:0; color:#7f8c8d;">Upload foto batik Anda dan biarkan AI kami mengidentifikasinya dalam hitungan detik</p>
        </div>
    </section>

    <main class="page-container" style="flex-grow:1; padding: 20px; box-sizing:border-box;">
        <div class="content-wrapper" style="max-width:800px; margin:0 auto;">

            <?php if ($upload_error): ?>
            <div class="error-box" style="background:#fee2e2; border:1px solid #fca5a5; color:#b91c1c; padding:15px; border-radius:8px; margin-bottom:20px; font-size:14px;">
                 <?= htmlspecialchars($upload_error) ?>
            </div>
            <?php endif; ?>

            <?php if ($result_data === null): ?>
            <div class="upload-card" style="background:#ffffff; border-radius:16px; padding:40px; box-shadow:0 10px 30px rgba(0,0,0,0.05); border:1px solid #eae0d5; box-sizing:border-box;">
                <h4 style="color:#5C2D00; text-align:center; font-size:18px; margin-top:0; margin-bottom:20px; font-weight:800;">
                    Upload Gambar Batik
                </h4>
                <form method="POST" enctype="multipart/form-data" id="classifyForm" style="text-align:center;">
                    
                    <div class="dropzone-area" id="dropZone" style="border:2px dashed #cbd5e1; padding:40px 20px; border-radius:12px; background:#fafafa; cursor:pointer; margin-bottom:25px; position:relative;">
                        <span style="font-size:48px; display:block; margin-bottom:15px;">🖼️</span>
                        <div style="font-weight:600; font-size:15px; color:#334155; margin-bottom:5px;">Klik atau seret gambar ke sini</div>
                        <div style="font-size:12px; color:#64748b;">JPG, PNG, WEBP — Maksimal 10MB</div>
                        <input type="file" name="batik_image" id="imageInput" accept="image/jpeg,image/png,image/webp,image/bmp" required style="position:absolute; top:0; left:0; width:100%; height:100%; opacity:0; cursor:pointer;">
                    </div>

                    <div id="previewBox" style="display:none; margin-top:16px; text-align:center;">
                        <img id="previewImg" src="" alt="Preview" style="max-width:100%; max-height:280px; border-radius:12px; object-fit:contain; border:2px solid #e8d8c0;">
                        <div id="previewName" style="font-size:12px; color:#888; margin-top:6px;"></div>
                    </div>

                    <button type="submit" class="btn-primary-custom" id="submitBtn" style="width:100%; padding:14px; font-size:16px; border:none; cursor:pointer; font-weight:700; border-radius:12px;">
                        Klasifikasikan Sekarang
                    </button>
                </form>
            </div>

            <?php else: ?>
            <div class="result-card" style="background:#fff; border:1px solid #e8d8c0; border-radius:16px; padding:30px; margin-bottom:25px; box-shadow:0 4px 20px rgba(0,0,0,0.03); box-sizing:border-box;">
                <div class="result-layout" style="display:flex; gap:25px; flex-wrap:wrap; align-items:center;">
                    
                    <div class="result-image" style="flex:0 0 auto;">
                        <img src="/BATIK_CLASSIFICATION_SYSTEM/website/uploads/klasifikasi/<?= htmlspecialchars($saved_image) ?>" alt="Gambar batik" style="width:160px; height:160px; border-radius:12px; object-fit:cover; box-shadow:0 4px 16px rgba(0,0,0,0.15);">
                    </div>

                    <div class="result-content" style="flex:1; min-width:250px;">
                        <div style="font-size:13px; color:#16a34a; font-weight:600; margin-bottom:6px;">
                            ✓ Prediksi Selesai
                        </div>
                        <div style="font-size:22px; font-weight:800; color:#5C2D00; margin-bottom:10px;">
    <?= htmlspecialchars($result_data['category_info']['nama_kategori'] ?? str_replace('_', ' ', ucwords($result_data['predicted_class']))) ?>
</div>
                        
                        <?php if ($is_low_confidence): ?>
                        <div style="background:#fff7ed; color:#c2410c; border:1px solid #fdba74; padding:12px; border-radius:10px; margin-bottom:15px; font-size:14px; font-weight:600; line-height:1.4;">
                             Sistem kurang yakin dengan hasil ini (Akurasi di bawah 60%). Silakan klik tombol di bawah untuk meninjau kecocokan probabilitas motif alternatif lainnya.
                        </div>
                        <?php endif; ?>

                        <?php if (!$is_low_confidence): ?>
                            <p style="font-size:14px; color:#555; margin:0 0 12px 0; line-height:1.5;">
                                <?= htmlspecialchars($result_data['category_info']['description'] ?? 'Deskripsi informasi karakteristik motif batik.') ?>
                            </p>
                            <?php if (!empty($result_data['category_info']['origin_region'])): ?>
                            <div style="display:inline-block; background:#f0fdf4; color:#166534; font-size:12px; padding:6px 12px; border-radius:20px; font-weight:600; margin-bottom:15px;">
                                📍 Asal: <?= htmlspecialchars($result_data['category_info']['origin_region']) ?>
                            </div>
                            <?php endif; ?>
                        <?php endif; ?>

                        <div style="font-size:13px; font-weight:600; color:#5C2D00; margin-bottom:6px;">
                            Tingkat Keyakinan Utama: <?= number_format($result_data['confidence'] ?? 0, 2) ?>%
                        </div>
                        <div style="background:#e2e8f0; height:10px; border-radius:5px; overflow:hidden; width:100%;">
                            <div style="background:<?= $is_low_confidence ? '#d97706' : '#7B3F00' ?>; height:100%; width:<?= min(100, $result_data['confidence'] ?? 0) ?>%;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <?php if (!empty($result_data['top_predictions'])): ?>
            <div style="margin-bottom:25px;">
                
                <button type="button" id="toggleBtn" class="btn-toggle-view" onclick="toggleExtendedPredictions()">
                     Tampilkan Analisis Probabilitas Matriks AI (Lihat Sisa Kelas Motif)
                </button>

                <div id="morePredictions" class="extended-predictions" style="background:#fff; border:1px solid #e8d8c0; border-top:none; border-radius:0 0 16px 16px; overflow:hidden;">
                    <div style="padding:20px;">
                        
                        <?php 
                        $counter = 0;
                        foreach ($result_data['top_predictions'] as $pred): 
                            $counter++;
                        ?>

                        <div style="display:flex; align-items:center; gap:15px; margin-bottom:15px;">
                            <div style="width:24px; height:24px; background:#f1f5f9; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; color:#475569;">
                                <?= $counter ?>
                            </div>
                            <div style="flex:1;">
                                <div style="font-weight:600; font-size:14px; color:#1e293b;">
                                    <?= htmlspecialchars(str_replace('_', ' ', ucwords($pred['class_name'], '_'))) ?>
                                </div>
                                <div style="background:#f1f5f9; height:6px; border-radius:3px; overflow:hidden; margin-top:4px; width:100%;">
                                    <div style="background:#a16207; height:100%; width:<?= $pred['confidence'] ?>%;"></div>
                                </div>
                            </div>
                            <div style="font-weight:700; color:#7B3F00; font-size:14px; text-align:right; min-width:55px;">
                                <?= number_format($pred['confidence'], 2) ?>%
                            </div>
                        </div>

                        <?php endforeach; ?>

                    </div>
                </div>
            </div>
            <?php endif; ?>

            <div style="display:flex; gap:15px; justify-content:center; flex-wrap:wrap; margin-top:20px;">
                <a href="klasifikasi.php" class="btn-primary-custom" style="text-decoration:none; padding:10px 24px;">Klasifikasi Lagi</a>
            </div>
            <?php endif; ?>

        </div>
    </main>

    <?php include __DIR__ . '/../includes/footer.php'; ?>

    <script>
    function toggleExtendedPredictions() {
        const container = document.getElementById('morePredictions');
        const btn = document.getElementById('toggleBtn');
        
        if (container.classList.contains('open')) {
            container.classList.remove('open');
            btn.style.borderRadius = "12px"; 
            btn.innerHTML = ' Tampilkan Analisis Probabilitas Matriks AI (Lihat Sisa Kelas Motif)';
        } else {
            container.classList.add('open');
            btn.style.borderRadius = "12px 12px 0 0"; 
            btn.innerHTML = ' Analisis Probabilitas Matriks AI';
        }
    }

    const imageInput = document.getElementById('imageInput');
    const previewBox = document.getElementById('previewBox');
    const previewImg = document.getElementById('previewImg');
    const previewName= document.getElementById('previewName');
    const dropZone   = document.getElementById('dropZone');
    const submitBtn  = document.getElementById('submitBtn');

    if (imageInput) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = e => {
                previewImg.src = e.target.result;
                previewName.textContent = file.name + ' (' + (file.size/1024/1024).toFixed(2) + ' MB)';
                previewBox.style.display = 'block';
                dropZone.style.borderColor = '#7B3F00';
            };
            reader.readAsDataURL(file);
        });
    }

    if (dropZone) {
        dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.background = '#f1f5f9'; });
        dropZone.addEventListener('dragleave', () => dropZone.style.background = '#fafafa');
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.style.background = '#fafafa';
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                const dt = new DataTransfer();
                dt.items.add(file);
                imageInput.files = dt.files;
                imageInput.input.dispatchEvent(new Event('change'));
            }
        });
    }

    document.getElementById('classifyForm')?.addEventListener('submit', function() {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="pure-spinner"></span>Sedang menganalisis citra…';
        }
    });
    </script>
</body>
</html>