<?php
/**
 * =============================================================
 * website/admin/dashboard.php
 * Dashboard utama panel admin Toko Margi Batik
 * =============================================================
 */
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/session.php';
require_once __DIR__ . '/../api/flask_api.php';

requireAdmin();

// ─── Ambil statistik dari database ───────────────────────
$stats = dbQueryOne("SELECT * FROM v_dashboard_stats") ?? [];

$total_predictions = (int)($stats['total_predictions'] ?? 0);
$total_categories  = (int)($stats['total_categories'] ?? 0);
$avg_confidence    = (float)($stats['avg_confidence'] ?? 0);
$top_class         = $stats['most_predicted_class'] ?? '—';

// ─── 5 prediksi terbaru ───────────────────────────────────
$recent = dbQuery(
    "SELECT ch.id, ch.created_at, ch.predicted_class, ch.confidence,
            COALESCE(u.full_name, 'Pengunjung') AS customer_name,
            ch.image_filename
     FROM classification_history ch
     LEFT JOIN users u ON ch.user_id = u.id
     ORDER BY ch.created_at DESC
     LIMIT 5"
);
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard — Admin Margi Batik</title>
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/dashboard.css" rel="stylesheet">
</head>
<body>
<div class="admin-wrapper">

    <?php include __DIR__ . '/../includes/sidebar_admin.php'; ?>

    <main class="admin-main">
        
        <div class="admin-content">

            <div class="page-header">
                <h1 class="page-title">
                    <span class="page-icon">📊</span> Dashboard
                </h1>
                <p class="page-subtitle">
                    Selamat datang, <strong><?= htmlspecialchars($_SESSION['user_name']) ?></strong>! Berikut ringkasan sistem klasifikasi batik.
                </p>
            </div>

            <?php foreach (getFlash() as $msg): ?>
            <div class="custom-alert <?= $msg['type'] ?>">
                <span><?= htmlspecialchars($msg['message']) ?></span>
                <button class="alert-close" type="button">✕</button>
            </div>
            <?php endforeach; ?>

            <div class="stats-grid">
                <div class="stat-column">
                    <a href="riwayat_customer.php" class="stat-card no-decoration">
                        <div class="stat-icon brown"><span>🔍</span></div>
                        <div>
                            <div class="stat-value"><?= number_format($total_predictions) ?></div>
                            <div class="stat-label">Total Prediksi</div>
                        </div>
                    </a>
                </div>
                <div class="stat-column">
                    <a href="kategori_batik.php" class="stat-card no-decoration">
                        <div class="stat-icon gold"><span>🎨</span></div>
                        <div>
                            <div class="stat-value"><?= $total_categories ?></div>
                            <div class="stat-label">Kelas Batik</div>
                        </div>
                    </a>
                </div>
                <div class="stat-column">
                    <div class="stat-card">
                        <div class="stat-icon green"><span>🎯</span></div>
                        <div>
                            <div class="stat-value"><?= number_format($avg_confidence, 1) ?>%</div>
                            <div class="stat-label">Rata-rata Confidence</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="stat-column">
    <div class="stat-card">
        <div class="stat-icon blue"><span>🏆</span></div>
        <div>
            <div class="stat-value">
                <?= htmlspecialchars(str_replace('_', ' ', $top_class)) ?>
            </div>
            <div class="stat-label">Motif Terbanyak</div>
        </div>
    </div>
</div>

            <div class="content-grid">
                <div class="content-column">
                    <div class="card">         
                         <div class="card-header card-header-flex">
                            <span>Prediksi Terbaru</span>
                            <a href="riwayat_customer.php" class="btn-view-all">Lihat Semua</a>
                        </div>
                        <div class="card-body no-padding">
                            <div class="table-wrapper">
                                <table class="prediction-table">
                                    <thead>
                                        <tr>
                                            <th>Waktu</th>
                                            <th>Pengunjung</th>
                                            <th>Prediksi</th>
                                            <th>Confidence</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                    <?php if (empty($recent)): ?>
                                        <tr><td colspan="8" class="empty-data">Belum ada data prediksi.</td></tr>
                                    <?php else: ?>
                                        <?php foreach ($recent as $row): ?>
                                        <tr>
                                            <td style="white-space:nowrap; font-size:12px">
                                                <?= date('d/m/Y H:i', strtotime($row['created_at'])) ?>
                                            </td>
                                            <td><?= htmlspecialchars($row['customer_name']) ?></td>
                                            <td>
                                                <span class="prediction-badge">
                                                    <?= htmlspecialchars(str_replace('_', ' ', $row['predicted_class'])) ?>
                                                </span>
                                            </td>
                                            <td>
                                                <div class="confidence-wrapper">
                                                    <div style="width:60px;height:6px;background:#e8e0d8;border-radius:3px;overflow:hidden">
                                                        <div style="width:<?= $row['confidence'] ?>%;height:100%;background:linear-gradient(90deg,#7B3F00,#D4A017)"></div>
                                                    </div>
                                                    <span style="font-size:12px;font-weight:600"><?= number_format($row['confidence'], 1) ?>%</span>
                                                </div>
                                            </td>
                                        </tr>
                                        <?php endforeach; ?>
                                    <?php endif; ?>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

        </div><?php include __DIR__ . '/../includes/footer.php'; ?>

    </main>
</div>

<script>
// Handler tombol close alert
document.querySelectorAll('.alert-close').forEach(button => {
    button.addEventListener('click', function () {
        this.parentElement.remove();
    });
});
</script>
</body>
</html>