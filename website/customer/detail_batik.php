<?php
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/session.php';
$id  = (int)($_GET['id'] ?? 0);
$cat = $id ? dbQueryOne("SELECT * FROM batik_categories WHERE id=? AND is_active=1",[$id]) : null;
if (!$cat) { header('Location: dashboard.php'); exit; }
?>
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><?= htmlspecialchars($cat['name']) ?> — Margi Batik</title>
<link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/customer.css" rel="stylesheet">
</head>
<body style="background:#F8F4F0;min-height:100vh;display:flex;flex-direction:column">
<?php include __DIR__ . '/../includes/navbar_customer.php'; ?>
<main class="container py-5 flex-grow-1">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card" style="border-radius:20px;border:1px solid #e8d8c0">
                <div class="card-body p-4">
                    <nav aria-label="breadcrumb"><ol class="breadcrumb mb-3">
                        <li class="breadcrumb-item"><a href="dashboard.php" style="color:#7B3F00">Beranda</a></li>
                        <li class="breadcrumb-item active"><?= htmlspecialchars($cat['name']) ?></li>
                    </ol></nav>
                    <h2 class="fw-800 mb-2" style="color:#5C2D00"><?= htmlspecialchars($cat['name']) ?></h2>
                    <?php if ($cat['origin_region']): ?>
                    <span class="badge mb-3" style="background:#FFF3E0;color:#7B3F00;font-size:13px;padding:6px 14px">
                        <i class="bi bi-geo-alt me-1"></i><?= htmlspecialchars($cat['origin_region']) ?>
                    </span>
                    <?php endif; ?>
                    <?php if ($cat['description']): ?>
                    <p style="font-size:15px;color:#555;line-height:1.7"><?= htmlspecialchars($cat['description']) ?></p>
                    <?php endif; ?>
                    <?php if ($cat['cultural_notes']): ?>
                    <div class="alert alert-info mt-3"><i class="bi bi-info-circle me-2"></i><?= htmlspecialchars($cat['cultural_notes']) ?></div>
                    <?php endif; ?>
                    <div class="mt-4">
                        <a href="klasifikasi.php" class="btn btn-batik">
                            <i class="bi bi-search me-2"></i>Klasifikasi Batik Ini
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</main>
<?php include __DIR__ . '/../includes/footer.php'; ?>
<script>
document.addEventListener("DOMContentLoaded", function() {

    const menuBtn = document.getElementById("menuBtn");
    const mobileMenu = document.getElementById("mobileMenu");

    if(menuBtn && mobileMenu){
        menuBtn.addEventListener("click", function(){
            mobileMenu.classList.toggle("show");
        });
    }

});
</script>
</body></html>
