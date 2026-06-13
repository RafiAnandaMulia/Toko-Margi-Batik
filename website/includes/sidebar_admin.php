<?php
/**
 * =============================================================
 * website/includes/sidebar_admin.php
 * Sidebar navigasi untuk semua halaman admin
 * =============================================================
 */
$current_page = basename($_SERVER['PHP_SELF']);
$sections = [
    'overview' => [
        'label' => 'Overview',
        'items' => [
            ['url' => 'dashboard.php', 'icon' => '📊', 'label' => 'Dashboard'],
            ['url' => 'statistik.php', 'icon' => '📈', 'label' => 'Statistik'],
        ]
    ],
    'catalog' => [
        'label' => 'Katalog',
        'items' => [
            ['url' => 'kategori_batik.php', 'icon' => '🎨', 'label' => 'Kategori Batik'],
            ['url' => 'gambar_batik.php', 'icon' => '🖼️', 'label' => 'Galeri Gambar'],
        ]
    ],
    'customers' => [
        'label' => 'Customer',
        'items' => [
            ['url' => 'riwayat_customer.php', 'icon' => '🕒', 'label' => 'Riwayat Klasifikasi'],
        ]
    ],
];
?>

<button id="menuToggleOpen" class="floating-menu-btn" type="button" title="Buka Menu">☰</button>

<div class="sidebar-overlay" id="sidebarOverlay"></div>

<aside class="admin-sidebar" id="adminSidebar">

    <div class="sidebar-brand">
        <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/sidebar_admin.css" rel="stylesheet">
        <img src="/BATIK_CLASSIFICATION_SYSTEM/website/assets/images/logo.png" class="sidebar-img" alt="Logo Margi Batik">
        <div style="flex: 1;">
            <div class="sidebar-brand-name">Margi Batik</div>
            <div class="sidebar-brand-sub">Sistem Klasifikasi</div>
        </div>
        
        <button id="menuToggleClose" class="sidebar-close-btn" type="button">✕</button>
    </div>

    <nav class="sidebar-nav">
        <?php foreach ($sections as $key => $section): ?>
        <div class="sidebar-section">
            <div class="sidebar-section-label"><?= $section['label'] ?></div>
            <?php foreach ($section['items'] as $item): ?>
            <a href="/BATIK_CLASSIFICATION_SYSTEM/website/admin/<?= $item['url'] ?>"
               class="sidebar-link <?= $current_page === $item['url'] ? 'active' : '' ?>">
                <span class="sidebar-icon"><?= $item['icon'] ?></span>
                <span><?= $item['label'] ?></span>
            </a>
            <?php endforeach; ?>
        </div>
        <?php endforeach; ?>
    </nav>

    <div class="sidebar-footer">
        <div class="sidebar-user">
            <div class="avatar-circle-sm">
                <?= strtoupper(substr($_SESSION['user_name'] ?? 'A', 0, 1)) ?>
            </div>
            <div class="sidebar-user-info">
                <div class="sidebar-user-name"><?= htmlspecialchars($_SESSION['user_name'] ?? 'Admin') ?></div>
                <div class="sidebar-user-role">Administrator</div>
            </div>
        </div>
        <a href="/BATIK_CLASSIFICATION_SYSTEM/website/admin/logout.php"
           class="sidebar-logout"
           onclick="return confirm('Yakin ingin keluar?')"
           title="Logout">
            <span class="logout-icon">🚪</span>
        </a>
    </div>
</aside>

<script>
document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("adminSidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const btnOpen = document.getElementById("menuToggleOpen");
    const btnClose = document.getElementById("menuToggleClose");

    // Klik tombol hamburger melayang untuk MEMBUKA sidebar di HP
    if (btnOpen && sidebar && overlay) {
        btnOpen.addEventListener("click", function () {
            sidebar.classList.add("open");
            overlay.classList.add("show");
        });
    }

    // Klik tombol silang (X) di dalam sidebar untuk MENUTUP
    if (btnClose && sidebar && overlay) {
        btnClose.addEventListener("click", function () {
            sidebar.classList.remove("open");
            overlay.classList.remove("show");
        });
    }

    // Klik area background buram untuk MENUTUP sidebar
    if (overlay && sidebar) {
        overlay.addEventListener("click", function () {
            sidebar.classList.remove("open");
            overlay.classList.remove("show");
        });
    }
});
</script>