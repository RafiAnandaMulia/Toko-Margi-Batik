<?php
/**
 * =============================================================
 * website/admin/statistik.php
 * Statistik dan analitik sistem klasifikasi batik (17 Kelas)
 * =============================================================
 */
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/session.php';

requireAdmin();

// ─── Statistik per kelas (Mengambil seluruh 17 kelas dari riwayat) ────────────────────────
$per_class = dbQuery(
    "SELECT predicted_class,
            COUNT(*) AS total,
            ROUND(IFNULL(AVG(confidence), 0), 2) AS avg_conf,
            SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) AS correct_count
     FROM classification_history
     GROUP BY predicted_class
     ORDER BY total DESC"
) ?? [];

// ─── Prediksi per hari (30 hari terakhir) ────────────────
$daily = dbQuery(
    "SELECT DATE(created_at) AS date, COUNT(*) AS total
     FROM   classification_history
     WHERE  created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
     GROUP  BY DATE(created_at)
     ORDER  BY date ASC"
) ?? [];

// ─── Ringkasan global ─────────────────────────────────────
$summary = dbQueryOne(
    "SELECT
        COUNT(*)                                       AS total_predictions,
        ROUND(IFNULL(AVG(confidence), 0), 2)           AS avg_confidence,
        COUNT(DISTINCT predicted_class)                AS unique_classes,
        SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) AS total_correct,
        SUM(CASE WHEN is_correct IS NOT NULL THEN 1 ELSE 0 END) AS total_feedback
     FROM classification_history"
) ?? [];

$accuracy_rate = ($summary['total_feedback'] ?? 0) > 0
    ? round($summary['total_correct'] / $summary['total_feedback'] * 100, 1)
    : 0;

// Menghitung grand total untuk kebutuhan proporsi persentase di tabel
$grand_total = !empty($per_class) ? array_sum(array_column($per_class, 'total')) : 0;

// Encode JSON dengan proteksi array kosong agar Chart.js tidak error saat inisialisasi awal
$chart_labels     = json_encode(!empty($per_class) ? array_column($per_class, 'predicted_class') : []);
$chart_totals     = json_encode(!empty($per_class) ? array_map('intval', array_column($per_class, 'total')) : []);
$chart_conf       = json_encode(!empty($per_class) ? array_map('floatval', array_column($per_class, 'avg_conf')) : []);
$daily_labels     = json_encode(!empty($daily) ? array_column($daily, 'date') : []);
$daily_totals     = json_encode(!empty($daily) ? array_map('intval', array_column($daily, 'total')) : []);
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Statistik — Admin Margi Batik</title>
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/dashboard.css" rel="stylesheet">
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/statistik.css" rel="stylesheet">
</head>
<body>
<div class="admin-wrapper">
    
    <?php include __DIR__ . '/../includes/sidebar_admin.php'; ?>
    <div class="sidebar-overlay" id="sidebarOverlay"></div>

    <main class="admin-main">
        <div class="admin-content">

            <div class="page-breadcrumb" style="margin-bottom: 8px; font-size: 0.8rem; color: #757575;">
                <a href="dashboard.php" style="color: #7B3F00; text-decoration: none; font-weight: 500;">Dashboard</a>
                <span style="margin: 0 4px;">›</span>
                <span style="color: #5C2D00;">Statistik</span>
            </div>

            <div class="page-header">
                <h1 class="page-title">
                    <span class="page-icon"></span> Statistik Sistem
                </h1>
                <p class="page-subtitle">Analitik penggunaan dan performa klasifikasi batik MobileNetV2</p>
            </div>

            <div class="stats-grid">
                <?php
                $summary_cards = [
                    [
                        'val'   => number_format($summary['total_predictions'] ?? 0),
                        'label' => 'Total Prediksi',
                        'icon'  => '',
                        'color' => ''
                    ],
                    [
                        'val'   => ($summary['avg_confidence'] ?? 0) . '%',
                        'label' => 'Rata-rata Confidence',
                        'icon'  => '',
                        'color' => ''
                    ],
                    [
                        'val'   => $summary['unique_classes'] ?? 0,
                        'label' => 'Kelas Terpakai',
                        'icon'  => '',
                        'color' => ''
                    ],
                ];
                foreach ($summary_cards as $c):
                ?>
                <div class="stat-column">
                    <div class="stat-card">
                        <div class="stat-icon <?= $c['color'] ?>">
                            <?= $c['icon'] ?>
                        </div>
                        <div>
                            <div class="stat-value"><?= $c['val'] ?></div>
                            <div class="stat-label"><?= $c['label'] ?></div>
                        </div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>

            <div class="content-grid" style="display: flex; flex-direction: column; gap: 16px;">

                <div class="charts-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
                    <div class="card">
                        <div class="card-header">
                            <span>Prediksi Harian (30 Hari Terakhir)</span>
                        </div>
                        <div class="card-body">
                            <div style="height:280px; position: relative;">
                                <canvas id="dailyChart"></canvas>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <span>Penyebaran 17 Kelas Batik</span>
                        </div>
                        <div class="card-body">
                            <div style="height:280px; position: relative;">
                                <canvas id="classChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="content-column">
                    <div class="card">
                        <div class="card-header">
                            <span>Detail Statistik Performa Motif Batik (Semua Kelas)</span>
                        </div>
                        <div class="card-body no-padding">
                            <div class="table-wrapper">
                                <table class="prediction-table">
                                    <thead>
                                        <tr>
                                            <th>Rank</th>
                                            <th>Kelas Batik</th>
                                            <th>Total Prediksi</th>
                                            <th>Rata-rata Confidence</th>
                                            <th>Akurasi Feedback (Benar/Total)</th>
                                            <th>Proporsi Data</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                    <?php
                                    foreach ($per_class as $i => $row):
                                        $pct = $grand_total > 0 ? round($row['total'] / $grand_total * 100, 1) : 0;
                                    ?>
                                    <tr>
                                        <td>
                                            <?php if ($i === 0): ?>
                                                <span style="font-size:16px; font-weight:bold; color:#D4A017;">🥇 1</span>
                                            <?php elseif ($i === 1): ?>
                                                <span style="font-size:16px; font-weight:bold; color:#9E9E9E;">🥈 2</span>
                                            <?php elseif ($i === 2): ?>
                                                <span style="font-size:16px; font-weight:bold; color:#CD7F32;">🥉 3</span>
                                            <?php else: ?>
                                                <span style="color:#aaa; font-weight: 600; padding-left: 4px;"><?= $i+1 ?></span>
                                            <?php endif; ?>
                                        </td>
                                        <td>
                                            <span class="prediction-badge">
                                                <?= htmlspecialchars(str_replace('_',' ',ucfirst($row['predicted_class']))) ?>
                                            </span>
                                        </td>
                                        <td><strong><?= number_format($row['total']) ?></strong></td>
                                        <td>
                                            <div class="confidence-wrapper">
                                                <div style="width:60px;height:6px;background:#e8e0d8;border-radius:3px;overflow:hidden">
                                                    <div style="width:<?= $row['avg_conf'] ?>%;height:100%;background:linear-gradient(90deg,#7B3F00,#D4A017)"></div>
                                                </div>
                                                <span style="font-size:12px;font-weight:600"><?= $row['avg_conf'] ?>%</span>
                                            </div>
                                        </td>
                                        <td>
                                            <?= $row['correct_count'] ?>
                                            <span style="color:#aaa;font-size:11px">/ <?= $row['total'] ?></span>
                                        </td>
                                        <td>
                                            <div class="confidence-wrapper">
                                                <div style="width:80px;height:6px;background:#e8e0d8;border-radius:3px;overflow:hidden">
                                                    <div style="width:<?= $pct ?>%;height:100%;background:#7B3F00"></div>
                                                </div>
                                                <span style="font-size:11px; font-weight: 600; color: #5C2D00;"><?= $pct ?>%</span>
                                            </div>
                                        </td>
                                    </tr>
                                    <?php endforeach; ?>
                                    
                                    <?php if (empty($per_class)): ?>
                                    <tr>
                                        <td colspan="6" class="empty-data">Belum ada data analitik kelas batik di database.</td>
                                    </tr>
                                    <?php endif; ?>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
        <?php include __DIR__ . '/../includes/footer.php'; ?>
    </main>

</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
// ── Grafik Harian (Bar Chart) ─────────────────────────────
new Chart(document.getElementById('dailyChart'), {
    type: 'bar',
    data: {
        labels: <?= $daily_labels ?>,
        datasets: [{
            label: 'Jumlah Prediksi',
            data: Guild = <?= $daily_totals ?>,
            backgroundColor: 'rgba(123, 63, 0, 0.7)',
            borderColor: '#7B3F00',
            borderWidth: 1,
            borderRadius: 4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { grid: { display: false } },
            y: { beginAtZero: true }
        }
    }
});

// ── Grafik per Kelas (Doughnut Chart) ──────────────────────
// Palet warna diperluas menjadi 20 warna warm earth/batik agar menampung ke-17 kelas dengan baik
const colors = [
    '#7B3F00', '#A0522D', '#D4A017', '#5C2D00', '#CD853F',
    '#8B4513', '#F5C382', '#D2691E', '#A92F2F', '#7DC733', 
    '#1E9CD2', '#C65D69', '#D22A1E', '#661ED2', '#8B5A2B',
    '#B8860B', '#BC8F8F', '#DEB887', '#E9967A', '#9ACD32'
];

new Chart(document.getElementById('classChart'), {
    type: 'doughnut',
    data: {
        labels: <?= $chart_labels ?>.map(l => l.replace(/_/g, ' ')),
        datasets: [{
            data: <?= $chart_totals ?>,
            backgroundColor: colors,
            borderColor: '#ffffff',
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
                labels: { 
                    boxWidth: 10, 
                    font: { size: 10 },
                    padding: 6 
                }
            }
        }
    }
});
</script>
</body>
</html>