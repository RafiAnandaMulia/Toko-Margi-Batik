<?php
/**
 * =============================================================
 * website/api/flask_api.php
 * Helper untuk komunikasi antara PHP dan Flask API
 * menggunakan cURL. Semua request ke AI engine melalui file ini.
 * =============================================================
 */

require_once __DIR__ . '/../config/session.php';

// ─── Konstanta URL Flask ──────────────────────────────────
if (!defined('FLASK_API_URL')) {
    define('FLASK_API_URL', 'http://localhost:5000');
}
define('FLASK_TIMEOUT',     60);   // Timeout umum (detik)
define('FLASK_TRAIN_TIMEOUT', 30); // Timeout untuk panggilan training (async)

/**
 * Mengirim request GET ke Flask API menggunakan cURL.
 *
 * @param string $endpoint  Path endpoint, contoh: '/api/model/status'
 * @param int    $timeout   Timeout dalam detik
 * @return array ['success' => bool, 'data' => array, 'http_code' => int]
 */
function flaskGet(string $endpoint, int $timeout = FLASK_TIMEOUT): array {
    $url = FLASK_API_URL . $endpoint;
    $ch  = curl_init();

    curl_setopt_array($ch, [
        CURLOPT_URL            => $url,
        CURLOPT_RETURNTRANSFER => true,    // Kembalikan response sebagai string
        CURLOPT_TIMEOUT        => $timeout,
        CURLOPT_CONNECTTIMEOUT => 10,      // Timeout koneksi 10 detik
        CURLOPT_HTTPHEADER     => ['Accept: application/json'],
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_SSL_VERIFYPEER => false,   // Nonaktifkan untuk development
    ]);

    $response  = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_err  = curl_error($ch);
    curl_close($ch);

    // Tangani error cURL (Flask tidak berjalan)
    if ($response === false || !empty($curl_err)) {
        error_log("Flask GET error [{$endpoint}]: {$curl_err}");
        return [
            'success'   => false,
            'data'      => ['error' => 'Tidak dapat terhubung ke AI Engine. Pastikan Flask berjalan.'],
            'http_code' => 0
        ];
    }

    // Decode JSON response
    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return [
            'success'   => false,
            'data'      => ['error' => 'Response dari server tidak valid (bukan JSON).'],
            'http_code' => $http_code
        ];
    }

    return [
        'success'   => ($http_code >= 200 && $http_code < 300),
        'data'      => $data,
        'http_code' => $http_code
    ];
}

/**
 * Mengirim request POST JSON ke Flask API.
 *
 * @param string $endpoint  Path endpoint
 * @param array  $payload   Data yang dikirim sebagai JSON body
 * @param int    $timeout   Timeout dalam detik
 * @return array ['success' => bool, 'data' => array, 'http_code' => int]
 */
function flaskPost(string $endpoint, array $payload = [], int $timeout = FLASK_TIMEOUT): array {
    $url      = FLASK_API_URL . $endpoint;
    $jsonBody = json_encode($payload, JSON_UNESCAPED_UNICODE);
    $ch       = curl_init();

    curl_setopt_array($ch, [
        CURLOPT_URL            => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $jsonBody,
        CURLOPT_TIMEOUT        => $timeout,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'Accept: application/json',
            'Content-Length: ' . strlen($jsonBody)
        ],
        CURLOPT_SSL_VERIFYPEER => false,
    ]);

    $response  = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_err  = curl_error($ch);
    curl_close($ch);

    if ($response === false || !empty($curl_err)) {
        error_log("Flask POST error [{$endpoint}]: {$curl_err}");
        return [
            'success'   => false,
            'data'      => ['error' => 'Tidak dapat terhubung ke AI Engine.'],
            'http_code' => 0
        ];
    }

    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return [
            'success'   => false,
            'data'      => ['error' => 'Response tidak valid.'],
            'http_code' => $http_code
        ];
    }

    return [
        'success'   => ($http_code >= 200 && $http_code < 300),
        'data'      => $data,
        'http_code' => $http_code
    ];
}

/**
 * Mengunggah gambar ke Flask API untuk prediksi.
 * Menggunakan multipart/form-data.
 *
 * @param string $image_path Path file gambar di server PHP
 * @return array Hasil prediksi dari Flask
 */
function flaskPredictImage(string $image_path): array {
    if (!file_exists($image_path)) {
        return ['success' => false, 'data' => ['error' => 'File gambar tidak ditemukan.']];
    }

    $url = FLASK_API_URL . '/api/predict';
    $ch  = curl_init();

    // Buat CURLFile untuk upload multipart
    $cfile = new CURLFile(
        $image_path,
        mime_content_type($image_path) ?: 'image/jpeg',
        basename($image_path)
    );

    curl_setopt_array($ch, [
        CURLOPT_URL            => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => ['image' => $cfile],
        CURLOPT_TIMEOUT        => 60,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);

    $response  = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_err  = curl_error($ch);
    curl_close($ch);

    if ($response === false || !empty($curl_err)) {
        error_log("Flask Predict error: {$curl_err}");
        return ['success' => false, 'data' => ['error' => 'Prediksi gagal: ' . $curl_err]];
    }

    $data = json_decode($response, true);
    return [
        'success'   => ($http_code === 200 && !empty($data['success'])),
        'data'      => $data ?? [],
        'http_code' => $http_code
    ];
}

/**
 * Memeriksa apakah Flask API sedang berjalan (health check).
 *
 * @return bool True jika Flask merespons
 */
function isFlaskRunning(): bool {
    $result = flaskGet('/health', timeout: 5);
    return $result['success'] && ($result['data']['status'] ?? '') === 'ok';
}

/**
 * Mengambil status training saat ini dari Flask.
 *
 * @return array Status training
 */
function getTrainingStatus(): array {
    $result = flaskGet('/api/model/status');
    return $result['success'] ? $result['data'] : [
        'status'        => 'unknown',
        'current_epoch' => 0,
        'total_epochs'  => 0,
        'percentage'    => 0,
        'message'       => 'Tidak dapat mengambil status training.'
    ];
}

/**
 * Memulai training baru melalui Flask.
 *
 * @param int $epochs_phase1 Epoch fase Transfer Learning
 * @param int $epochs_phase2 Epoch fase Fine-Tuning
 * @param int $batch_size    Ukuran batch
 * @return array Response dari Flask
 */
function startTraining(int $epochs_phase1 = 50, int $epochs_phase2 = 20, int $batch_size = 32): array {
    return flaskPost('/api/model/train', [
        'epochs_phase1' => $epochs_phase1,
        'epochs_phase2' => $epochs_phase2,
        'batch_size'    => $batch_size,
    ], FLASK_TRAIN_TIMEOUT);
}

/**
 * Resume training dari checkpoint terakhir.
 *
 * @param int|null $target_epochs Total epoch yang diinginkan
 * @return array Response dari Flask
 */
function resumeTraining(?int $target_epochs = null): array {
    $payload = ['batch_size' => 32];
    if ($target_epochs !== null) {
        $payload['target_epochs'] = $target_epochs;
    }
    return flaskPost('/api/model/resume', $payload, FLASK_TRAIN_TIMEOUT);
}

/**
 * Mengambil riwayat training (data CSV) dari Flask.
 *
 * @param int $limit Jumlah epoch terakhir yang diambil
 * @return array Data riwayat training
 */
function getTrainingHistory(int $limit = 100): array {
    $result = flaskGet("/api/model/history?limit={$limit}");
    return $result['success'] ? ($result['data']['data'] ?? []) : [];
}
