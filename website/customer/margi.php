<?php
/**
 * =============================================================
 * website/customer/margi.php (Landing Page Toko Margi Batik)
 * Menampilkan katalog dinamis terintegrasi dengan database admin
 * =============================================================
 */
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/session.php';

// Ambil data kategori batik langsung dari database
$categories = dbQuery(
    "SELECT bc.*, 
            COUNT(ch.id) AS total_predictions 
     FROM batik_categories bc
     LEFT JOIN classification_history ch ON bc.slug = ch.predicted_class
     GROUP BY bc.id
     ORDER BY bc.name ASC"
) ?? [];
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Toko Margi Batik — Keindahan Warisan Nusantara</title>
    
    <link rel="stylesheet" href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/riwayat.css">
</head>
<body>
        <?php include __DIR__ . '/../includes/navbar_customer.php'; ?>
    <main class="container">
        <h2 class="section-title"> Karakteristik Batik</h2>
        
        <div class="batik-grid">
            <?php if (!empty($categories)): ?>
                <?php foreach ($categories as $cat): ?>
                    <div class="batik-card">
                        <?php 
                            // --- SOLUSI ERROR 404 ---
                            // Jika ada file gambar dinamis hasil upload admin, gunakan folder uploads.
                            // Jika tidak ada, fallback ke gambar statis aset lokal berdasarkan slug.
                            if (!empty($cat['image_path'])) {
                                $imagePath = BASE_URL . "/uploads/batik/" . $cat['image_path'];
                            } else {
                                $imagePath = BASE_URL . "/assets/img/koleksi/" . htmlspecialchars($cat['slug']) . ".jpg";
                            }
                        ?>
                        
                        <img class="batik-image" 
                             src="<?= $imagePath ?>" 
                             alt="Gambar <?= htmlspecialchars($cat['name']) ?>" 
                             onerror="this.onerror=null; this.src='https://placehold.co/600x400?text=Foto+'.concat('<?= urlencode($cat['name']) ?>');">
                        
                        <div class="batik-content">
                            <h3 class="batik-name"><?= htmlspecialchars($cat['name']) ?></h3>
                            <span class="batik-region">📍 Asal: <?= htmlspecialchars($cat['origin_region'] ?? 'Indonesia') ?></span>
                            
                            <p class="batik-description">
                                <?= nl2br(htmlspecialchars($cat['description'] ?? 'Belum ada deskripsi umum.')) ?>
                            </p>
                        </div>
                    </div>
                <?php endforeach; ?>
            <?php else: ?>
                <p style="text-align: center; grid-column: 1/-1; color: #888; font-style: italic;">Belum ada kategori batik yang diinput oleh admin.</p>
            <?php endif; ?>
        </div>
    </main>

    <footer>
        <div class="footer-content">
            <div class="footer-info">
                <h3>Toko Margi Batik</h3>
                <p>Pusat pelestarian dan edukasi batik nusantara berbasis teknologi kecerdasan buatan.</p>
            </div>
            <div class="footer-info">
                <h3>Hubungi & Kunjungi Kami</h3>
                <p><strong>Alamat Kantor & Workshop:</strong></p>
                <p>Jl. Margi Batik No. 45, Kompleks Sentra Kerajinan Batik, Jawa Tengah, Indonesia</p>
                <p><strong>WhatsApp / Telepon:</strong> +62 812-3456-7890</p>
                <p><strong> Email:</strong> info@margibatik.com</p>
            </div>
        </div>
        <div class="footer-bottom">
            &copy; <?= date('Y') ?> Margi Batik — BATIK CLASSIFICATION SYSTEM. All Rights Reserved.
        </div>
    </footer>

</body>
</html>