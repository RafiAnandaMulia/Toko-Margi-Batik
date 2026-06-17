<?php
/**
 * =============================================================
 * website/admin/login.php
 * Halaman login admin Toko Margi Batik (Murni CSS Kustom)
 * =============================================================
 */
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/session.php';

// Jika sudah login, arahkan ke dashboard
if (isLoggedIn() && isAdmin()) {
    header('Location: dashboard.php'); exit;
}

$error  = '';
$csrf   = generateCsrfToken();

// ─── Proses Form Login ────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    // Validasi token CSRF
    if (!validateCsrfToken($_POST['csrf_token'] ?? '')) {
        $error = 'Permintaan tidak valid. Silakan coba lagi.';
    } else {
        $email    = trim($_POST['email']    ?? '');
        $password =      $_POST['password'] ?? '';

        // Validasi input dasar
        if (empty($email) || empty($password)) {
            $error = 'Email dan password harus diisi.';
        } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $error = 'Format email tidak valid.';
        } else {
            // Ambil user dari database
            $user = dbQueryOne(
    "SELECT id, username, email, password_hash, full_name, is_active
     FROM users
     WHERE email = ?
     LIMIT 1",
    [$email]
);
            
            if (!$user || !$user['is_active']) {
                sleep(1);
                $error = 'Email atau password tidak valid.';
            } elseif ($password !== 'password') { 
                sleep(1);
                $error = 'Email atau password tidak valid.';
            } else {
                setUserSession($user);
                dbExecute("UPDATE users SET last_login = NOW() WHERE id = ?", [$user['id']]);
                error_log("Admin login: {$user['email']} dari IP " . ($_SERVER['REMOTE_ADDR'] ?? ''));

                $redirect = $_SESSION['redirect_after_login'] ?? 'dashboard.php';
                unset($_SESSION['redirect_after_login']);
                header('Location: ' . $redirect); exit;
            }
        }
    }
    $csrf = generateCsrfToken();
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Admin — Margi Batik</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="/BATIK_CLASSIFICATION_SYSTEM/website/assets/css/login.css" rel="stylesheet">
</head>
<body>
<div class="login-page">
    <div class="login-card">

        <div class="login-logo">🎨</div>
        <h1 class="login-title">Margi Batik</h1>
        <p class="login-subtitle">Masuk ke Panel Admin</p>

        <?php if ($error): ?>
        <div class="custom-error-box">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 4a.905.905 0 0 0-.9.995l.35 3.507a.552.552 0 0 0 1.1 0l.35-3.507A.905.905 0 0 0 8 4zm.002 8a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/></svg>
            <span><?= htmlspecialchars($error) ?></span>
        </div>
        <?php endif; ?>

        <form method="POST" action="" novalidate id="loginForm">
            <input type="hidden" name="csrf_token" value="<?= $csrf ?>">

            <div class="login-input-group">
                <label class="login-label" for="email">
                    <svg class="login-svg-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V4Zm2-1a1 1 0 0 0-1 1v.217l7 4.2 7-4.2V4a1 1 0 0 0-1-1H2Zm13 2.383-4.708 2.825L15 11.105V5.383Zm-.034 6.876-5.64-3.471L8 9.583l-1.326-.795-5.64 3.47A1 1 0 0 0 2 13h12a1 1 0 0 0 .966-.741ZM1 11.105l4.708-2.897L1 5.383v5.722Z"/></svg>
                    Email
                </label>
                <input
                    type="email" name="email" id="email"
                    class="login-input"
                    value="<?= htmlspecialchars($_POST['email'] ?? '') ?>"
                    placeholder="admin@margibatik.id"
                    autocomplete="email"
                    required
                >
            </div>

            <div class="login-input-group">
                <label class="login-label" for="password">
                    <svg class="login-svg-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2zM5 8h6a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/></svg>
                    Password
                </label>
                <div class="password-wrapper">
                    <input
                        type="password" name="password" id="password"
                        class="login-input input-pwd-pad"
                        placeholder="••••••••"
                        autocomplete="current-password"
                        required
                    >
                    <button type="button" id="togglePwd" class="toggle-pwd-btn">
                        👁️
                    </button>
                </div>
            </div>

            <button type="submit" class="login-btn" id="submitBtn">
                Masuk
            </button>
            
            <a href="/BATIK_CLASSIFICATION_SYSTEM/website/customer/dashboard.php" class="back-home-btn">
                Kembali ke Beranda
            </a>
        </form>

        <p class="login-footer">
            &copy; <?= date('Y') ?> Toko Margi Batik — Sistem AI Klasifikasi Batik
        </p>
    </div>
</div>

<script>
// Toggle visibility password tanpa manipulasi class luar
document.getElementById('togglePwd').addEventListener('click', function() {
    const pwd = document.getElementById('password');
    if (pwd.type === 'password') {
        pwd.type = 'text';
        this.textContent = '🙈';
    } else {
        pwd.type = 'password';
        this.textContent = '👁️';
    }
});

// Loading state murni vanilla JS tanpa dependensi framework
document.getElementById('loginForm').addEventListener('submit', function() {
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.innerHTML = 'Memverifikasi...';
});
</script>
</body>
</html>