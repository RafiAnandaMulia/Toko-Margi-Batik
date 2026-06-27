<?php
/**
 * =============================================================
 * website/customer/dashboard.php
 * Landing Page Customer — Fokus Edukasi & Mitra Penelitian Margi Batik
 * =============================================================
 */
require_once __DIR__ . '/../config/session.php';
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Margi Batik — Kenali Batik Nusantara</title>
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/customer.css" rel="stylesheet">
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/responsive.css" rel="stylesheet">
    <style>
        .dropzone-area {
            border: 2px dashed #cbd5e1;
            padding: 40px 20px;
            border-radius: 12px;
            background: #fafafa;
            cursor: pointer;
            margin-bottom: 25px;
            transition: all 0.3s ease;
            position: relative;
        }
        .dropzone-area.dragover {
            border-color: #5C2D00;
            background: #f5ebe0;
        }
        .preview-container {
            display: none;
            margin-top: 15px;
            text-align: center;
        }
        .preview-image {
            max-width: 200px;
            max-height: 200px;
            object-fit: cover;
            border-radius: 8px;
            border: 2px solid #eae0d5;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        /* Style Tambahan Edukasi & Mitra */
        .mitra-badge {
            display: inline-block;
            background: #f5ebe0;
            color: #5C2D00;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 15px;
            border: 1px solid #eae0d5;
        }
        .edu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        .edu-card {
            background: #ffffff;
            border: 1px solid #eae0d5;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(92, 45, 0, 0.02);
        }
        .edu-card h3 {
            color: #5C2D00;
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 18px;
        }
        .edu-card p {
            color: #475569;
            font-size: 14px;
            line-height: 1.6;
            margin: 0;
        }
    </style>
</head>
<body style="background:#F8F4F0; min-height:100vh; display:flex; flex-direction:column; margin:0; padding:0; font-family:sans-serif;">

    <?php include __DIR__ . '/../includes/navbar_customer.php'; ?>

    <section id="beranda" class="hero-section" style="padding: 60px 0;">
        <div class="page-container" style="max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 40px; box-sizing: border-box;">
            <div class="hero-content" style="flex: 1; min-width: 300px;">
                <span class="mitra-badge"> Mitra Resmi Penelitian</span>
                <h1 class="hero-title" style="font-size: 36px; color: #5C2D00; margin-top: 0; margin-bottom: 20px; font-weight: 800; line-height: 1.2;">
                    Klasifikasi Batik Nusantara<br>Bersama Margi Batik
                </h1>
                <p class="hero-subtitle" style="color: #475569; font-size: 15px; line-height: 1.6; margin-bottom: 30px;">
                    Sistem ini dibangun khusus untuk melestarikan warisan budaya Indonesia dengan mengintegrasikan kecerdasan buatan. Melalui arsitektur Deep Learning <strong>MobileNetV2</strong>, sistem mampu mengidentifikasi karakteristik visual dan pola geometri kain batik secara instan dan akurat.
                </p>
            </div>
            <div class="hero-image" style="flex: 0 0 auto; text-align: center; margin: 0 auto;">
                <img src="/BATIK_CLASSIFICATION_SYSTEM/website/assets/images/logo.png" alt="Logo Margi Batik" class="hero-logo" style="width: 280px; max-width: 100%; height: auto;">
            </div>
        </div>
    </section>

    <section id="tentang-mitra" class="section-block" style="background:#ffffff; padding: 80px 0; border-top: 1px solid #eae0d5; border-bottom: 1px solid #eae0d5;">
        <div class="page-container" style="max-width: 1000px; margin: 0 auto; padding: 0 20px; box-sizing: border-box;">
            <div style="text-align: center; max-width: 700px; margin: 0 auto 50px auto;">
                <h2 class="section-title" style="color:#5C2D00; font-size:26px; margin-bottom:15px; font-weight:800;">Edukasi Budaya & Mitra Penelitian</h2>
                <p style="color:#64748b; font-size:14px; line-height:1.6; margin:0;">
                    Pelaksanaan penelitian klasifikasi citra ini didukung penuh oleh data pengetahuan kain tradisional nusantara serta koleksi motif otentik.
                </p>
            </div>

            <div class="edu-grid">
                <div class="edu-card">
                    <h3>Atas Nama Margi Batik</h3>
                    <p>
                        Margi Batik merupakan galeri dan rumah produksi batik lokal yang berkomitmen mempertahankan keaslian teknik membatik tradisional. Sebagai mitra utama dalam penelitian ini, Margi Batik berkontribusi dalam penyediaan validasi data latih (dataset) citra kain serta pengetahuan mendalam mengenai filosofi di balik sehelai kain batik.
                    </p>
                </div>

                <div class="edu-card">
                    <h3>Pelestarian Nilai Nusantara</h3>
                    <p>
                        Batik Nusantara bukan sekadar lembaran tekstil bermotif, melainkan sebuah dokumen sejarah yang memuat untaian doa, status sosial, dan representasi geografis daerah asalnya. Melalui sistem klasifikasi digital ini, khazanah kekayaan visual nusantara dapat terdokumentasi dengan baik agar terus dikenali oleh generasi muda.
                    </p>
                </div>

                <div class="edu-card">
                    <h3>Sinergi Seni & Deep Learning</h3>
                    <p>
                        Pendekatan model <em>Convolutional Neural Network (CNN)</em> bertindak mengenali pola-pola rumit seperti garis lengkung, repetisi geometris, hingga koordinasi warna khas. Penggabungan komputasi dan kesenian tradisional ini membuktikan bahwa teknologi mampu menjadi instrumen pelestari kebudayaan.
                    </p>
                </div>
            </div>
        </div>
    </section>

    <section id="alamat-toko" class="section-block" style="padding: 80px 0; background:#F8F4F0;">
        <div class="page-container" style="max-width: 1100px; margin: 0 auto; padding: 0 20px; box-sizing: border-box;">
            <h2 class="section-title" style="text-align:center; color:#5C2D00; font-size:26px; font-weight:800; margin-bottom:10px;"> Lokasi Toko Margi Batik</h2>
            <p style="text-align:center; color:#7f8c8d; font-size:14px; margin-bottom:40px; line-height:1.5;">
                Silakan kunjungi Toko Margi Batik kami untuk melihat langsung koleksi kain batik tulis dan cap otentik.
            </p>
            
            <div class="maps-container-grid" style="display: flex; flex-wrap: wrap; gap: 30px; background: #ffffff; border-radius: 16px; padding: 30px; box-shadow: 0 10px 30px rgba(92,45,0,0.04); border: 1px solid #eae0d5;">
                
                <div class="address-details" style="flex: 1; min-width: 300px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                        <span style="font-size: 36px;"></span>
                        <div>
                            <h3 style="color:#5C2D00; margin:0; font-size:20px; font-weight:700;">Toko Margi Batik</h3>
                            <p style="color:#64748b; font-size:13px; margin: 2px 0 0 0;">Menjual Koleksi Batik</p>
                        </div>
                    </div>
                    
                    <p style="font-size:15px; color:#475569; line-height:1.6; margin: 0 0 25px 0;">
                        <strong>Alamat:</strong><br>
                         Bl. M Square, Jl. Melawai 5 No.001, RT.4/RW.1, Melawai, Kec. Kby. Baru, Kota Jakarta Selatan, Daerah Khusus Ibukota Jakarta 12160<br>
                        <span style="color: #7f8c8d; font-size: 13px;">Blok M Square, LT GF Blok B No. No 128-129</span>
                    </p>

                    <div style="border-top: 1px solid #eae0d5; border-bottom: 1px solid #eae0d5; padding: 20px 0; margin-bottom: 25px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div style="font-size:14px; color:#475569;">
                            <strong>🕒 Jam Operasional:</strong><br>
                            <span style="color:#64748b; font-size:13px;">Setiap Hari<br>08.00 - 17.00 WIB</span>
                        </div>
                        <div style="font-size:14px; color:#475569;">
                            <strong>📞 Kontak / WA:</strong><br>
                            <span style="color:#64748b; font-size:13px;">+62 0822-9981-9199<br></span>
                        </div>
                    </div>

                    <a href="https://maps.app.goo.gl/a6bwWBp5qRcS9smg9" target="_blank" class="btn-primary-custom" style="text-align: center; text-decoration:none; padding:14px; font-size:15px; font-weight:700; border-radius:10px; background:#7B3F00; color:#fff; box-shadow: 0 4px 12px rgba(123,63,0,0.15); transition: background 0.3s;">
                        Petunjuk Arah (Buka di Aplikasi Maps)
                    </a>
                </div>
                
                <div class="address-map" style="flex: 1.2; min-width: 320px; height: 380px; border-radius: 12px; overflow: hidden; border: 1px solid #cbd5e1;">
    <iframe 
        src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3955.123456789!2d110.812345!3d-7.56789!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zN8KwMzQnMDQuNCJTIDExMMKwNDgnNDQuNCJF!5e0!3m2!1sid!2sid!4v1234567890" 
        width="100%" 
        height="100%" 
        style="border:0;" 
        allowfullscreen="" 
        loading="lazy" 
        referrerpolicy="no-referrer-when-downgrade">
    </iframe>
</div>
            </div>
        </div>
    </section>

    <?php include __DIR__ . '/../includes/footer.php'; ?>

    <script>
    // 1. Smooth Scroll untuk Navigasi Internal Anchor
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // 2. Logika Drag, Drop, dan Image Preview
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('batik_image');
    const dropzoneText = document.getElementById('dropzone-text');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');

    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            fileInput.files = files;
            handleFilePreview(files[0]);
        }
    });

    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFilePreview(this.files[0]);
        }
    });

    function handleFilePreview(file) {
        if (!file.type.startsWith('image/')) {
            alert('Harap unggah berkas citra berupa gambar (PNG/JPG/JPEG/WEBP).');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            previewContainer.style.display = 'block';
            dropzoneText.innerHTML = `Berkas terpilih: <strong style="color:#5C2D00;">${file.name}</strong>`;
        }
        reader.readAsDataURL(file);
    }
    </script>
</body>
</html>