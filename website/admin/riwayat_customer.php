<?php
/**
 * =============================================================
 * website/admin/riwayat_customer.php
 * Riwayat semua prediksi klasifikasi oleh customer
 * =============================================================
 */
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/session.php';

requireAdmin();

// ─── Pagination & Filter ──────────────────────────────────
$page      = max(1, (int)($_GET['page']    ?? 1));
$per_page  = 20;
$offset    = ($page - 1) * $per_page;
$search    = sanitize($_GET['search']  ?? '');
$filter_class = sanitize($_GET['class'] ?? '');

// ─── WHERE clause ─────────────────────────────────────────
$where  = "WHERE 1=1";
$params = [];
if ($search !== '') {
    $where  .= " AND (u.full_name LIKE ? OR ch.predicted_class LIKE ? OR ch.image_filename LIKE ?)";
    $params  = array_merge($params, ["%$search%", "%$search%", "%$search%"]);
}
if ($filter_class !== '') {
    $where  .= " AND ch.predicted_class = ?";
    $params[] = $filter_class;
}

// ─── Total records ────────────────────────────────────────
$total_rows = (int)(dbQueryOne(
    "SELECT COUNT(*) AS cnt
     FROM classification_history ch
     LEFT JOIN users u ON ch.user_id = u.id
     $where",
    $params
)['cnt'] ?? 0);

$total_pages = max(1, (int)ceil($total_rows / $per_page));

// ─── Data ─────────────────────────────────────────────────
$rows = dbQuery(
    "SELECT ch.id, ch.created_at, ch.image_filename, ch.predicted_class,
            ch.confidence, ch.is_correct, ch.ip_address,
            COALESCE(u.full_name, 'Tamu') AS customer_name,
            COALESCE(u.email, '-')        AS customer_email,
            bc.name                       AS category_name
     FROM   classification_history ch
     LEFT JOIN users            u  ON ch.user_id      = u.id
     LEFT JOIN batik_categories bc ON ch.predicted_class = bc.slug
     $where
     ORDER BY ch.created_at DESC
     LIMIT $per_page OFFSET $offset",
    $params
);

// ─── Daftar kelas untuk filter dropdown ──────────────────
$all_classes = dbQuery(
    "SELECT DISTINCT predicted_class FROM classification_history ORDER BY predicted_class"
);
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Riwayat Customer — Admin Margi Batik</title>
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/riwayat_customer.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
</head>
<body>
<div class="admin-wrapper">
    <?php include __DIR__ . '/../includes/sidebar_admin.php'; ?>
    <div class="sidebar-overlay" id="sidebarOverlay"></div>
    
    <div class="admin-main">
        
        <div class="admin-content">

            <div class="page-header-container">
                <div class="page-header-left">
                    <nav class="custom-breadcrumb">
                        <a href="dashboard.php">Dashboard</a>
                        <span class="divider">/</span>
                        <span class="active">Riwayat Customer</span>
                    </nav>
                    <h1 class="page-title"><i class="bi bi-clock-history"></i> Riwayat Klasifikasi</h1>
                    <p class="page-subtitle">
                        Total <strong><?= number_format($total_rows) ?></strong> prediksi tercatat
                    </p>
                </div>
            </div>

            <form method="GET" class="admin-card filter-card">
                <div class="card-body-custom">
                    <div class="filter-grid">
                        <div class="filter-col-search">
                            <label class="custom-form-label">Cari</label>
                            <div class="custom-input-group">
                                <span class="input-group-icon"><i class="bi bi-search"></i></span>
                                <input type="text" name="search" class="custom-form-control"
                                       placeholder="Nama, kelas, atau file…"
                                       value="<?= htmlspecialchars($search) ?>">
                            </div>
                        </div>
                        
                        <div class="filter-col-class">
                            <label class="custom-form-label">Filter Kelas</label>
                            <select name="class" class="custom-form-select">
                                <option value="">— Semua Kelas —</option>
                                <?php foreach ($all_classes as $c): ?>
                                <option value="<?= htmlspecialchars($c['predicted_class']) ?>"
                                    <?= $filter_class === $c['predicted_class'] ? 'selected' : '' ?>>
                                    <?= htmlspecialchars(str_replace('_',' ', ucfirst($c['predicted_class']))) ?>
                                </option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        
                        <div class="filter-col-buttons">
                            <button type="submit" class="btn-custom btn-primary-custom">
                                <i class="bi bi-filter"></i> Filter
                            </button>
                            <a href="riwayat_customer.php" class="btn-custom btn-outline-custom" title="Reset">
                                <i class="bi bi-x-lg"></i>
                            </a>
                        </div>
                    </div>
                </div>
            </form>

            <div class="admin-card">
                <div class="table-responsive-wrapper">
                    <table class="custom-table">
                        <thead>
                            <tr>
                                <th style="width: 50px;">#</th>
                                <th style="width: 120px;">Waktu</th>
                                <th>Customer</th>
                                <th>Gambar</th>
                                <th>Prediksi</th>
                                <th style="width: 160px;">Confidence</th>
                                <th style="width: 110px;">Feedback</th>
                            </tr>
                        </thead>
                        <tbody>
                        <?php if (empty($rows)): ?>
                            <tr>
                                <td colspan="7" class="table-empty-state">
                                    <i class="bi bi-inbox-fill"></i>
                                    <p>Tidak ada data yang ditemukan.</p>
                                </td>
                            </tr>
                        <?php else: ?>
                            <?php foreach ($rows as $i => $row): ?>
                            <tr>
                                <td class="col-number">
                                    <?= $offset + $i + 1 ?>
                                </td>
                                <td class="col-datetime">
                                    <span class="date-text"><?= date('d/m/Y', strtotime($row['created_at'])) ?></span>
                                    <span class="time-text"><?= date('H:i:s', strtotime($row['created_at'])) ?></span>
                                </td>
                                <td>
                                    <div class="cust-name"><?= htmlspecialchars($row['customer_name']) ?></div>
                                    <div class="cust-email"><?= htmlspecialchars($row['customer_email']) ?></div>
                                </td>
                                <td>
                                    <?php $img_path = '/BATIK_CLASSIFICATION_SYSTEM/website/uploads/klasifikasi/' . $row['image_filename']; ?>
                                    <div class="image-preview-box">
                                        <div class="img-thumbnail-container">
                                            <img src="<?= htmlspecialchars($img_path) ?>"
                                             alt="Batik">
                                        </div>
                                        <span class="filename-text" title="<?= htmlspecialchars($row['image_filename']) ?>">
                                            <?= htmlspecialchars($row['image_filename']) ?>
                                        </span>
                                    </div>
                                </td>
                                <td>
                                    <span class="badge-custom badge-predicted">
                                        <?= htmlspecialchars(str_replace('_',' ', ucfirst($row['predicted_class']))) ?>
                                    </span>
                                    <?php if ($row['category_name']): ?>
                                    <div class="category-subtext"><?= htmlspecialchars($row['category_name']) ?></div>
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <div class="confidence-wrapper">
                                        <div class="confidence-bar-bg">
                                            <div class="confidence-bar-fill" style="width: <?= $row['confidence'] ?>%;"></div>
                                        </div>
                                        <span class="confidence-number">
                                            <?= number_format($row['confidence'], 1) ?>%
                                        </span>
                                    </div>
                                </td>
                                <td>
                                    <?php if ($row['is_correct'] === null): ?>
                                        <span class="badge-custom badge-status-null">Belum</span>
                                    <?php elseif ($row['is_correct'] == 1): ?>
                                        <span class="badge-custom badge-status-true">
                                            <i class="bi bi-check-circle-fill"></i> Benar
                                        </span>
                                    <?php else: ?>
                                        <span class="badge-custom badge-status-false">
                                            <i class="bi bi-x-circle-fill"></i> Salah
                                        </span>
                                    <?php endif; ?>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        <?php endif; ?>
                        </tbody>
                    </table>
                </div>

                <?php if ($total_pages > 1): ?>
                <div class="pagination-container">
                    <ul class="custom-pagination">
                        <li class="page-item-custom <?= $page <= 1 ? 'disabled' : '' ?>">
                            <?php if($page <= 1): ?>
                                <span><i class="bi bi-chevron-left"></i></span>
                            <?php else: ?>
                                <a href="?page=<?= $page-1 ?>&search=<?= urlencode($search) ?>&class=<?= urlencode($filter_class) ?>">
                                    <i class="bi bi-chevron-left"></i>
                                </a>
                            <?php endif; ?>
                        </li>
                        
                        <?php for ($p = max(1,$page-2); $p <= min($total_pages,$page+2); $p++): ?>
                        <li class="page-item-custom <?= $p === $page ? 'active' : '' ?>">
                            <a href="?page=<?= $p ?>&search=<?= urlencode($search) ?>&class=<?= urlencode($filter_class) ?>"><?= $p ?></a>
                        </li>
                        <?php endfor; ?>
                        
                        <li class="page-item-custom <?= $page >= $total_pages ? 'disabled' : '' ?>">
                            <?php if($page >= $total_pages): ?>
                                <span><i class="bi bi-chevron-right"></i></span>
                            <?php else: ?>
                                <a href="?page=<?= $page+1 ?>&search=<?= urlencode($search) ?>&class=<?= urlencode($filter_class) ?>">
                                    <i class="bi bi-chevron-right"></i>
                                </a>
                            <?php endif; ?>
                        </li>
                    </ul>
                    <div class="pagination-info">
                        Halaman <?= $page ?> dari <?= $total_pages ?> (Total <?= number_format($total_rows) ?> data)
                    </div>
                </div>
                <?php endif; ?>
            </div>

        </div> <?php include __DIR__ . '/../includes/footer.php'; ?>
    </div> </div> </body>
</html>