<?php
/**
 * =============================================================
 * website/api/ajax_status.php
 * Proxy AJAX: PHP → Flask GET /api/model/status
 * Dipanggil oleh JavaScript di train_model.php setiap 3 detik
 * =============================================================
 */
require_once __DIR__ . '/../config/session.php';
require_once __DIR__ . '/../api/flask_api.php';

// Hanya boleh diakses oleh admin yang sudah login
if (!isAdmin()) {
    http_response_code(403);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

// Set header JSON
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-cache, no-store, must-revalidate');

// Ambil status dari Flask dan teruskan ke browser
$status = getTrainingStatus();
echo json_encode($status);
