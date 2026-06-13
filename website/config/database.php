<?php
/**
 * =============================================================
 * website/config/database.php
 * Konfigurasi koneksi database MySQL menggunakan PDO.
 * Murni untuk manajemen query database.
 * =============================================================
 */
define('BASE_URL', '/BATIK_CLASSIFICATION_SYSTEM/website');

// ─── Konfigurasi Database ────────────────────────────────
define('DB_HOST',     'localhost');
define('DB_PORT',     '3306');
define('DB_NAME',     'batik_ai');
define('DB_USER',     'root');          
define('DB_PASS',     '');              
define('DB_CHARSET', 'utf8mb4');

/**
 * Mendapatkan koneksi PDO ke database (Singleton Pattern).
 */
function getDB(): PDO {
    static $pdo = null;

    if ($pdo === null) {
        $dsn = sprintf(
            'mysql:host=%s;port=%s;dbname=%s;charset=%s',
            DB_HOST, DB_PORT, DB_NAME, DB_CHARSET
        );

        $options = [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,   
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,         
            PDO::ATTR_EMULATE_PREPARES   => false,                     
            PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"
        ];

        try {
            $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            die(json_encode([
                'success' => false,
                'error'   => 'Koneksi database gagal. Hubungi administrator.'
            ]));
        }
    }

    return $pdo;
}

/**
 * Menjalankan query SELECT dan mengembalikan semua baris.
 */
function dbQuery(string $sql, array $params = []): array {
    $stmt = getDB()->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll();
}

/**
 * Menjalankan query SELECT dan mengembalikan satu baris.
 */
function dbQueryOne(string $sql, array $params = []): ?array {
    $stmt = getDB()->prepare($sql);
    $stmt->execute($params);
    $row = $stmt->fetch();
    return $row !== false ? $row : null;
}

/**
 * Menjalankan query INSERT/UPDATE/DELETE.
 */
function dbExecute(string $sql, array $params = []): int {
    $stmt = getDB()->prepare($sql);
    $stmt->execute($params);
    return $stmt->rowCount();
}

/**
 * Menjalankan INSERT dan mengembalikan ID yang baru dibuat.
 */
function dbInsert(string $sql, array $params = []): string {
    $stmt = getDB()->prepare($sql);
    $stmt->execute($params);
    return getDB()->lastInsertId();
}