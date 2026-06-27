<?php
require_once __DIR__ . '/../config/session.php';
$current_page = basename($_SERVER['PHP_SELF']);
?>

<nav id="customerNavbar">
    <div class="navbar-container">
        <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/navbar_customer.css" rel="stylesheet">

        <a href="/BATIK_CLASSIFICATION_SYSTEM/website/customer/dashboard.php" class="navbar-brand-custom">
            <div class="brand-icon">
                <img src="/BATIK_CLASSIFICATION_SYSTEM/website/assets/images/logo.png" alt="Logo Margi Batik" class="brand-logo">
            </div>
            <div>
                <span class="brand-name-customer">Margi Batik</span>
                <span class="brand-tagline"></span>
            </div>
        </a>

        <button class="navbar-toggle" id="navbarToggle" aria-label="Toggle navigation">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
        </button>

        <ul class="navbar-menu" id="navbarMenu">
            <li>
                <a class="<?= $current_page === 'dashboard.php' ? 'active' : '' ?>" href="/BATIK_CLASSIFICATION_SYSTEM/website/customer/dashboard.php">Beranda</a>
            </li>
            <li>
                <a class="<?= $current_page === 'klasifikasi.php' ? 'active' : '' ?>" href="/BATIK_CLASSIFICATION_SYSTEM/website/customer/klasifikasi.php">Klasifikasi</a>
            </li>
            <li>
                <a class="<?= $current_page === 'margi.php' ? 'active' : '' ?>" href="/BATIK_CLASSIFICATION_SYSTEM/website/customer/margi.php">Gambar Batik</a>
            </li>
        </ul>
<div class="navbar-actions">
    <a href="/BATIK_CLASSIFICATION_SYSTEM/website/admin/login.php"
       class="btn-batik">
        Admin
    </a>
</div>

    </div>
</nav>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('navbarToggle');
    const navMenu = document.getElementById('navbarMenu');

    if (toggleBtn && navMenu) {
        toggleBtn.addEventListener('click', function() {
            toggleBtn.classList.toggle('active');
            navMenu.classList.toggle('show');
        });
    }
});
</script>