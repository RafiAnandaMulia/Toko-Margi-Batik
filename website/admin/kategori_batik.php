<?php
/**
 * =============================================================
 * website/admin/kategori_batik.php
 * Manajemen data kategori batik terintegrasi sistem klasifikasi CNN
 * =============================================================
 */
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/session.php';

// ─── Proses form POST ─────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    if (!validateCsrfToken($_POST['csrf_token'] ?? '')) {
        setFlash('error', 'Token tidak valid.');
        header('Location: kategori_batik.php');
        exit;
    }

    $action = $_POST['action'] ?? '';

    // =====================================================
    // 1. TAMBAH KATEGORI 
    // =====================================================
    if ($action === 'add') {
        $slug   = sanitize($_POST['slug'] ?? '');
        $name   = sanitize($_POST['name'] ?? '');
        $region = sanitize($_POST['origin_region'] ?? '');
        $desc   = sanitize($_POST['description'] ?? '');

        if (empty($slug) || empty($name)) {
            setFlash('error', 'Slug dan nama kategori wajib diisi.');
        } elseif (!preg_match('/^[a-z0-9_]+$/', $slug)) {
            setFlash('error', 'Slug hanya boleh huruf kecil, angka, dan underscore.');
        } else {
            $existing = dbQueryOne(
                "SELECT id FROM batik_categories WHERE slug = ?",
                [$slug]
            );

            if ($existing) {
                setFlash('error', "Slug '$slug' sudah digunakan.");
            } else {
                dbInsert(
                    "INSERT INTO batik_categories (slug, name, origin_region, description) VALUES (?, ?, ?, ?)",
                    [$slug, $name, $region, $desc]
                );
                setFlash('success', 'Kategori berhasil ditambahkan.');
            }
        }
    }

    // =====================================================
    // 2. EDIT KATEGORI 
    // =====================================================
    elseif ($action === 'edit') {
        $id     = (int)($_POST['id'] ?? 0);
        $name   = sanitize($_POST['name'] ?? '');
        $region = sanitize($_POST['origin_region'] ?? '');
        $desc   = sanitize($_POST['description'] ?? '');

        if (empty($name)) {
            setFlash('error', 'Nama kategori wajib diisi.');
        } else {
            $params = [$name, $region, $desc];
            $image_sql = '';

            // Fitur upload gambar
            if (isset($_FILES['image']) && $_FILES['image']['error'] === UPLOAD_ERR_OK) {
                $allowed = ['jpg', 'jpeg', 'png', 'webp'];
                $ext = strtolower(pathinfo($_FILES['image']['name'], PATHINFO_EXTENSION));

                if (in_array($ext, $allowed)) {
                    $filename = uniqid('batik_') . '.' . $ext;
                    $upload_dir = __DIR__ . '/../uploads/batik/';

                    if (!is_dir($upload_dir)) {
                        mkdir($upload_dir, 0777, true);
                    }

                    if (move_uploaded_file($_FILES['image']['tmp_name'], $upload_dir . $filename)) {
                        $image_sql = ', image_path = ?';
                        $params[] = $filename;
                    }
                }
            }

            $params[] = $id;

            dbExecute(
                "UPDATE batik_categories
                 SET name = ?,
                     origin_region = ?,
                     description = ?
                     $image_sql
                 WHERE id = ?",
                $params
            );

            setFlash('success', 'Kategori berhasil diperbarui.');
        }
    }

    // =====================================================
    // 3. HAPUS KATEGORI 
    // =====================================================
    elseif ($action === 'delete') {
        $id = (int)($_POST['id'] ?? 0);

        dbExecute("DELETE FROM batik_categories WHERE id = ?", [$id]);
        setFlash('success', 'Kategori berhasil dihapus.');
    }

    // Selesai memproses POST, langsung redirect
    header('Location: kategori_batik.php');
    exit;
}

// ─── AMBIL DATA UNTUK INTERFACE GET ────────
$categories = dbQuery(
    "SELECT bc.*, 
            COUNT(ch.id) AS total_predictions 
     FROM batik_categories bc
     LEFT JOIN classification_history ch ON bc.slug = ch.predicted_class
     GROUP BY bc.id
     ORDER BY bc.name ASC"
) ?? [];

$flash = getFlash() ?? []; 
$csrf  = generateCsrfToken(); 
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kategori Batik — Admin Margi Batik</title>
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/dashboard.css" rel="stylesheet">
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/kategori_batik.css" rel="stylesheet">
</head>
<body>
<div class="admin-wrapper">
    <?php include __DIR__ . '/../includes/sidebar_admin.php'; ?>
    <div class="sidebar-overlay" id="sidebarOverlay"></div>
    
    <div class="admin-main">
        <div class="admin-content">
            <div class="page-header">
                <div class="page-header-left">
                    <div>
                        <div class="breadcrumb">
                            <a href="dashboard.php">Dashboard</a>
                            <span>›</span>
                            <span>Kategori Batik</span>
                        </div>
                        <h1 class="page-title">Kategori Batik</h1>
                        <p class="page-subtitle"><?= count($categories) ?> kategori terdaftar dalam sistem</p>
                    </div>
                    <button type="button" id="openAddModal" class="btn-batik">
                        Tambah Kategori
                    </button>
                </div>
            </div>

            <?php foreach ($flash as $msg): ?>
            <div class="custom-alert <?= htmlspecialchars($msg['type']) ?>">
                <?= htmlspecialchars($msg['message']) ?>
                <button type="button" class="alert-close">✕</button>
            </div>
            <?php endforeach; ?>

            <div class="category-container">
                <div class="table-wrapper">
                    <table class="prediction-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Slug (ID Teknis)</th>
                                <th>Nama Tampilan</th>
                                <th>Asal Daerah</th>
                                <th>Prediksi</th>
                                <th style="text-align: center;">Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php if (!empty($categories)): ?>
                                <?php foreach ($categories as $i => $cat): ?>
                                <tr>
                                    <td style="color:#aaa; font-size:12px; width: 40px;"><?= $i + 1 ?></td>
                                    <td>
                                        <code class="slug-code"><?= htmlspecialchars($cat['slug']) ?></code>
                                    </td>
                                    <td>
                                        <div class="category-name"><?= htmlspecialchars($cat['name']) ?></div>
                                        <?php if ($cat['description']): ?>
                                        <div class="category-desc" title="<?= htmlspecialchars($cat['description']) ?>">
                                            <?= htmlspecialchars($cat['description']) ?>
                                        </div>
                                        <?php endif; ?>
                                    </td>
                                    <td><?= htmlspecialchars($cat['origin_region'] ?? '—') ?></td>
                                    <td>
                                        <span class="prediction-count">
                                            <?= number_format($cat['total_predictions']) ?>x
                                        </span>
                                    </td>
                                    <td>
                                        <div class="action-buttons">
                                            <button type="button" class="edit-button" 
                                                    data-id="<?= $cat['id'] ?>" 
                                                    data-name="<?= htmlspecialchars($cat['name']) ?>"
                                                    data-region="<?= htmlspecialchars($cat['origin_region'] ?? '') ?>"
                                                    data-description="<?= htmlspecialchars($cat['description'] ?? '') ?>">
                                                Edit Batik
                                            </button>

                                            <form method="POST" class="inline-form" onsubmit="return confirm('Hapus kategori ini? Pastikan tidak ada data terkait.')">
                                                <input type="hidden" name="csrf_token" value="<?= $csrf ?>">
                                                <input type="hidden" name="action" value="delete">
                                                <input type="hidden" name="id" value="<?= $cat['id'] ?>">
                                                <button type="submit" class="delete-button">Hapus Batik</button>
                                            </form>
                                        </div>
                                    </td> 
                                </tr>
                                <?php endforeach; ?>
                            <?php else: ?>
                                <tr>
                                    <td colspan="6" style="text-align: center; color: #888; font-style: italic; padding: 20px;">Belum ada data kategori batik.</td>
                                </tr>
                            <?php endif; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div> 
        <?php include __DIR__ . '/../includes/footer.php'; ?>
    </div> 
</div> 

<div id="editModal" class="custom-modal">
    <form method="POST" enctype="multipart/form-data" class="custom-modal-content">
        <div class="custom-modal-header">
            <h3>✏️ Edit Kategori Batik</h3>
            <button type="button" id="closeEditModal" class="modal-close">✕</button>
        </div>
        
        <div class="custom-modal-body">
            <input type="hidden" name="csrf_token" value="<?= $csrf ?>">
            <input type="hidden" name="action" value="edit">
            <input type="hidden" id="edit_id" name="id">

            <div class="form-group">
                <label>Nama Batik</label>
                <input type="text" id="edit_name" name="name" class="custom-input" required>
            </div>

            <div class="form-group">
                <label>Gambar Batik</label>
                <input type="file" name="image" class="custom-input" accept="image/*">
            </div>

            <div class="form-group">
                <label>Asal Daerah</label>
                <input type="text" id="edit_region" name="origin_region" class="custom-input">
            </div>

            <div class="form-group">
                <label>Deskripsi</label>
                <textarea id="edit_description" name="description" class="custom-textarea" rows="4"></textarea>
            </div>
        </div>
        
        <div class="custom-modal-footer">
            <button type="button" id="cancelEditModal" class="btn-cancel">Batal</button>
            <button type="submit" class="btn-save">💾 Update</button>
        </div>
    </form>
</div>

<div id="addModal" class="custom-modal">
    <form method="POST" class="custom-modal-content">
        <div class="custom-modal-header">
            <h3>➕ Tambah Kategori Batik</h3>
            <button type="button" id="closeAddModal" class="modal-close">✕</button>
        </div>
        
        <div class="custom-modal-body">
            <input type="hidden" name="csrf_token" value="<?= $csrf ?>">
            <input type="hidden" name="action" value="add">

            <div class="form-group">
                <label>Nama Tampilan *</label>
                <input type="text" name="name" id="add_name" class="custom-input" placeholder="cth: Batik Kawung" required maxlength="150">
            </div>
            <div class="form-group">
                <label>Slug *</label>
                <input type="text" name="slug" id="add_slug" class="custom-input" placeholder="cth: batik_kawung" required pattern="[a-z0-9_]+">
                <small>ID teknis — harus sama dengan nama folder dataset</small>
            </div>
            <div class="form-group">
                <label>Asal Daerah</label>
                <input type="text" name="origin_region" class="custom-input" placeholder="cth: Yogyakarta" maxlength="100">
            </div>
            <div class="form-group">
                <label>Deskripsi</label>
                <textarea name="description" class="custom-textarea" rows="4" placeholder="Deskripsi singkat tentang motif batik ini"></textarea>
            </div>
        </div>
        
        <div class="custom-modal-footer">
            <button type="button" id="cancelAddModal" class="btn-cancel">Batal</button>
            <button type="submit" class="btn-save">💾 Simpan</button>
        </div>
    </form>
</div>

<script>
// --- MODAL TAMBAH ---
document.getElementById('openAddModal')?.addEventListener('click', function() {
    document.getElementById('addModal').classList.add('show');
});
document.getElementById('closeAddModal')?.addEventListener('click', function() {
    document.getElementById('addModal').classList.remove('show');
});
document.getElementById('cancelAddModal')?.addEventListener('click', function() {
    document.getElementById('addModal').classList.remove('show');
});

// --- MODAL EDIT ---
document.querySelectorAll('.edit-button').forEach(button => {
    button.addEventListener('click', function() {
        document.getElementById('edit_id').value = this.dataset.id;
        document.getElementById('edit_name').value = this.dataset.name;
        document.getElementById('edit_region').value = this.dataset.region;
        document.getElementById('edit_description').value = this.dataset.description;
        
        document.getElementById('editModal').classList.add('show');
    });
});
document.getElementById('closeEditModal')?.addEventListener('click', function() {
    document.getElementById('editModal').classList.remove('show');
});
document.getElementById('cancelEditModal')?.addEventListener('click', function() {
    document.getElementById('editModal').classList.remove('show');
});

// --- TUTUP MODAL JIKA KLIK LUAR AREA ---
window.addEventListener('click', function(e) {
    const addModal = document.getElementById('addModal');
    const editModal = document.getElementById('editModal');
    if (e.target === addModal) addModal.classList.remove('show');
    if (e.target === editModal) editModal.classList.remove('show');
});

// --- GENERATOR OTOMATIS SLUG ---
document.getElementById('add_name')?.addEventListener('input', function() {
    const slugInput = document.getElementById('add_slug');
    if (!slugInput.dataset.manual) {
        slugInput.value = this.value
            .toLowerCase()
            .replace(/[^a-z0-9\s_]/g, '')
            .replace(/\s+/g, '_')
            .replace(/_+/g, '_')
            .replace(/^_+|_+$/g, '');
    }
});
document.getElementById('add_slug')?.addEventListener('input', function() {
    this.dataset.manual = '1';
});

// --- TOMBOL CLOSE ALERT ---
document.querySelectorAll('.alert-close').forEach(button => {
    button.addEventListener('click', function () {
        this.parentElement.remove();
    });
});
</script>
</body>
</html>