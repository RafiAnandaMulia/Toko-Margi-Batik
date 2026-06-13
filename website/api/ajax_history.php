<?php
/**
 * =============================================================
 * website/api/ajax_history.php
 * Proxy AJAX: PHP → Flask GET /api/model/history
 * Mengembalikan data CSV training untuk grafik dan tabel
 * =============================================================
 */
require_once __DIR__ . '/../config/session.php';
require_once __DIR__ . '/../api/flask_api.php';

if (!isAdmin()) {
    http_response_code(403);
    echo json_encode(['success' => false, 'error' => 'Unauthorized']);
    exit;
}

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-cache, no-store, must-revalidate');

$limit  = min(200, max(10, (int)($_GET['limit'] ?? 100)));
$result = flaskGet("/api/model/history?limit={$limit}");

echo json_encode($result['success'] ? $result['data'] : [
    'success' => false, 'data' => [], 'total_epochs' => 0
]);
