<?php
/**
 * =============================================================
 * website/config/session.php
 * Konfigurasi dan manajemen sesi PHP yang aman.
 * =============================================================
 */

// ─── Konfigurasi Sesi yang Aman ──────────────────────────
ini_set('session.cookie_httponly',  '1');    // Cegah akses cookie via JavaScript (Mitigasi XSS)
ini_set('session.cookie_secure',    '0');    // Set ke '1' jika sudah menggunakan HTTPS
ini_set('session.use_strict_mode',  '1');    // Tolak session ID yang tidak valid
ini_set('session.cookie_samesite', 'Lax');  // Proteksi CSRF tambahan pada cookie
ini_set('session.gc_maxlifetime',  '7200'); // Sesi berlaku 2 jam

define('FLASK_API_URL', 'http://localhost:5000'); // URL Flask API untuk model CNN MobileNetV2

// Mulai sesi jika belum aktif
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// ─── Regenerasi Session ID untuk keamanan ────────────────
// Regenerasi setiap 30 menit untuk mencegah session fixation
if (!isset($_SESSION['last_regenerate'])) {
    $_SESSION['last_regenerate'] = time();
} elseif (time() - $_SESSION['last_regenerate'] > 1800) {
    session_regenerate_id(true);  // true = hapus file session lama di server
    $_SESSION['last_regenerate'] = time();
}

/**
 * Memeriksa apakah user sudah login.
 *
 * @return bool True jika sudah login
 */
function isLoggedIn(): bool {
    return isset($_SESSION['user_id']) && !empty($_SESSION['user_id']);
}

/**
 * Memeriksa apakah user yang login adalah admin.
 *
 * @return bool True jika admin
 */
function isAdmin(): bool {
    return isLoggedIn() && ($_SESSION['user_role'] ?? '') === 'admin';
}

/**
 * Memaksa redirect ke halaman login jika belum login.
 * Simpan URL yang dituju agar bisa dikembalikan setelah login.
 *
 * @param string $redirect_to Path halaman login
 */
function requireLogin(string $redirect_to = '/website/admin/login.php'): void {
    if (!isLoggedIn()) {
        $_SESSION['redirect_after_login'] = $_SERVER['REQUEST_URI'] ?? '';
        header('Location: ' . $redirect_to);
        exit;
    }
}

/**
 * Memaksa redirect jika bukan admin.
 */
function requireAdmin(): void {
    requireLogin();
    if (!isAdmin()) {
        header('Location: /website/customer/dashboard.php');
        exit;
    }
}

/**
 * Menyimpan data user ke sesi setelah login berhasil.
 *
 * @param array $user Data user dari database
 */
function setUserSession(array $user): void {
    // Regenerasi session ID saat login untuk mencegah session fixation
    session_regenerate_id(true);

    $_SESSION['user_id']       = (int)$user['id'];
    $_SESSION['user_name']     = htmlspecialchars($user['full_name'],  ENT_QUOTES, 'UTF-8');
    $_SESSION['user_email']    = htmlspecialchars($user['email'],      ENT_QUOTES, 'UTF-8');
    $_SESSION['user_role']     = $user['role'];
    $_SESSION['user_username'] = htmlspecialchars($user['username'],   ENT_QUOTES, 'UTF-8');
    $_SESSION['login_time']    = time();
    $_SESSION['last_regenerate'] = time();
}

/**
 * Menghapus semua data sesi (logout).
 */
function destroySession(): void {
    $_SESSION = [];
    if (ini_get('session.use_cookies')) {
        $params = session_get_cookie_params();
        setcookie(
            session_name(), '', time() - 42000,
            $params['path'], $params['domain'],
            $params['secure'], $params['httponly']
        );
    }
    session_destroy();
}

/**
 * Membuat dan menyimpan token CSRF untuk form.
 *
 * @return string Token CSRF (hex string 32 karakter)
 */
function generateCsrfToken(): string {
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

/**
 * Memvalidasi token CSRF dari form menggunakan hash_equals (Aman dari Timing Attack).
 *
 * @param string $token Token yang dikirim dari form
 * @return bool True jika valid
 */
function validateCsrfToken(string $token): bool {
    return isset($_SESSION['csrf_token']) &&
           hash_equals($_SESSION['csrf_token'], $token);
}

/**
 * Melakukan sanitasi input untuk mencegah XSS.
 *
 * @param mixed $input Input mentah dari user
 * @return string|array Input yang sudah di-sanitasi
 */
function sanitize($input) {
    if (is_array($input)) {
        return array_map('sanitize', $input);
    }
    return htmlspecialchars(trim((string)$input), ENT_QUOTES, 'UTF-8');
}

/**
 * Menyimpan pesan flash ke sesi (Disinkronkan ke halaman admin).
 *
 * @param string $type    Tipe pesan: 'success', 'error', 'warning', 'info'
 * @param string $message Isi pesan
 */
function setFlash(string $type, string $message): void {
    $_SESSION['flash_messages'][] = [
        'type'    => $type,
        'message' => sanitize($message)
    ];
}

/**
 * Mengambil dan menghapus semua pesan flash dari sesi (Disinkronkan ke halaman admin).
 *
 * @return array Daftar pesan flash
 */
function getFlash(): array {
    $messages = $_SESSION['flash_messages'] ?? [];
    unset($_SESSION['flash_messages']);
    return $messages;
}