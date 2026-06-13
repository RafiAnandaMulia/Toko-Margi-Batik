-- =============================================================
-- database/batik_ai.sql
-- Skema Database MySQL untuk Sistem Klasifikasi Batik
-- Toko Margi Batik — AI Classification System
-- =============================================================
-- Penggunaan:
--   mysql -u root -p < batik_ai.sql
-- =============================================================

-- ─── Buat & Pilih Database ────────────────────────────────
CREATE DATABASE IF NOT EXISTS batik_ai
    CHARACTER SET  utf8mb4
    COLLATE        utf8mb4_unicode_ci;

USE batik_ai;

-- ─── Hapus tabel lama jika ada (urutan penting: FK dulu) ──
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS classification_history;
DROP TABLE IF EXISTS training_logs;
DROP TABLE IF EXISTS batik_images;
DROP TABLE IF EXISTS batik_categories;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================
-- TABEL: users
-- Menyimpan data pengguna (admin dan customer)
-- =============================================================
CREATE TABLE users (
    id            INT          UNSIGNED NOT NULL AUTO_INCREMENT,
    username      VARCHAR(50)  NOT NULL,
    email         VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,           -- Bcrypt hash, BUKAN plain text
    full_name     VARCHAR(100) NOT NULL DEFAULT '',
    role          ENUM('admin','customer')
                               NOT NULL DEFAULT 'customer',
    avatar        VARCHAR(255)          DEFAULT NULL,  -- Nama file avatar
    is_active     TINYINT(1)  NOT NULL DEFAULT 1,      -- 1=aktif, 0=nonaktif
    last_login    DATETIME             DEFAULT NULL,
    created_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email    (email),
    UNIQUE KEY uq_users_username (username),
    KEY        idx_users_role    (role),
    KEY        idx_users_active  (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Data pengguna sistem (admin dan customer)';

-- =============================================================
-- TABEL: batik_categories
-- Menyimpan kategori/kelas batik yang dikenali model
-- =============================================================
CREATE TABLE batik_categories (
    id             INT          UNSIGNED NOT NULL AUTO_INCREMENT,
    slug           VARCHAR(100) NOT NULL,          -- Nama teknis dari labels.txt
    name           VARCHAR(150) NOT NULL,          -- Nama tampilan yang ramah
    description    TEXT                 DEFAULT NULL, -- Deskripsi batik
    origin_region  VARCHAR(100)         DEFAULT NULL, -- Asal daerah
    cultural_notes TEXT                 DEFAULT NULL, -- Catatan budaya
    thumbnail      VARCHAR(255)         DEFAULT NULL, -- Gambar representatif
    is_active      TINYINT(1)  NOT NULL DEFAULT 1,
    created_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_categories_slug (slug),
    KEY        idx_categories_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Kategori/kelas batik yang dikenali model AI';

-- =============================================================
-- TABEL: batik_images
-- Galeri gambar untuk setiap kategori batik
-- =============================================================
CREATE TABLE batik_images (
    id           INT          UNSIGNED NOT NULL AUTO_INCREMENT,
    category_id  INT          UNSIGNED NOT NULL,
    filename     VARCHAR(255) NOT NULL,            -- Nama file gambar
    filepath     VARCHAR(500) NOT NULL,            -- Relative path dari uploads/
    caption      VARCHAR(255)         DEFAULT NULL,
    is_primary   TINYINT(1)  NOT NULL DEFAULT 0,  -- 1 = gambar utama kategori
    upload_by    INT          UNSIGNED DEFAULT NULL,
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_images_category (category_id),
    KEY idx_images_primary  (is_primary),
    CONSTRAINT fk_images_category FOREIGN KEY (category_id)
        REFERENCES batik_categories (id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_images_uploader  FOREIGN KEY (upload_by)
        REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Galeri gambar contoh batik per kategori';

-- =============================================================
-- TABEL: classification_history
-- Riwayat setiap prediksi/klasifikasi yang dilakukan
-- =============================================================
CREATE TABLE classification_history (
    id               INT          UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id          INT          UNSIGNED DEFAULT NULL,  -- NULL jika guest
    session_id       VARCHAR(128)          DEFAULT NULL,  -- Session PHP untuk guest
    image_filename   VARCHAR(255) NOT NULL,               -- Nama file yang diunggah
    image_path       VARCHAR(500) NOT NULL,               -- Path file yang disimpan
    predicted_class  VARCHAR(150) NOT NULL,               -- Kelas yang diprediksi
    confidence       DECIMAL(6,2) NOT NULL DEFAULT 0.00, -- Persentase keyakinan (0-100)
    top_predictions  JSON                  DEFAULT NULL,  -- Top-5 prediksi dalam JSON
    model_version    VARCHAR(50)           DEFAULT NULL,  -- Versi/nama file model
    processing_time  DECIMAL(8,4)         DEFAULT NULL,  -- Waktu proses (detik)
    is_correct       TINYINT(1)           DEFAULT NULL,  -- Feedback user: 1=benar, 0=salah, NULL=belum
    user_feedback    VARCHAR(255)          DEFAULT NULL,  -- Komentar feedback user
    ip_address       VARCHAR(45)           DEFAULT NULL,  -- IPv4/IPv6 client
    created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_classify_user      (user_id),
    KEY idx_classify_session   (session_id),
    KEY idx_classify_class     (predicted_class),
    KEY idx_classify_date      (created_at),
    KEY idx_classify_confidence(confidence),
    CONSTRAINT fk_classify_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Riwayat semua prediksi klasifikasi batik';

-- =============================================================
-- TABEL: training_logs
-- Mencatat setiap sesi pelatihan model AI
-- =============================================================
CREATE TABLE training_logs (
    id                INT          UNSIGNED NOT NULL AUTO_INCREMENT,
    session_id        VARCHAR(64)  NOT NULL,            -- UUID unik per sesi training
    started_by        INT          UNSIGNED DEFAULT NULL, -- Admin yang memulai
    status            ENUM('pending','running','completed','error','stopped')
                                   NOT NULL DEFAULT 'pending',
    total_epochs      SMALLINT     UNSIGNED NOT NULL DEFAULT 0,
    current_epoch     SMALLINT     UNSIGNED NOT NULL DEFAULT 0,
    best_val_accuracy DECIMAL(7,5)          DEFAULT NULL, -- Akurasi validasi terbaik
    final_accuracy    DECIMAL(7,5)          DEFAULT NULL, -- Akurasi akhir (test set)
    final_loss        DECIMAL(10,7)         DEFAULT NULL,
    model_path        VARCHAR(500)          DEFAULT NULL, -- Path model yang dihasilkan
    hyperparams       JSON                  DEFAULT NULL, -- Hyperparameter sebagai JSON
    error_message     TEXT                  DEFAULT NULL, -- Pesan error jika gagal
    started_at        DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at       DATETIME             DEFAULT NULL,
    duration_seconds  INT         UNSIGNED DEFAULT NULL, -- Durasi training (detik)
    updated_at        DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                          ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_training_session (session_id),
    KEY        idx_training_status (status),
    KEY        idx_training_date   (started_at),
    CONSTRAINT fk_training_admin FOREIGN KEY (started_by)
        REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Log setiap sesi pelatihan model AI batik';

-- =============================================================
-- TABEL: training_epoch_logs
-- Detail akurasi dan loss per epoch (dari CSV, di-sync ke DB)
-- =============================================================
CREATE TABLE training_epoch_logs (
    id              INT      UNSIGNED NOT NULL AUTO_INCREMENT,
    training_id     INT      UNSIGNED NOT NULL,   -- FK ke training_logs
    epoch           SMALLINT UNSIGNED NOT NULL,
    loss            DECIMAL(10,7)     DEFAULT NULL,
    accuracy        DECIMAL(7,5)      DEFAULT NULL,
    val_loss        DECIMAL(10,7)     DEFAULT NULL,
    val_accuracy    DECIMAL(7,5)      DEFAULT NULL,
    learning_rate   DECIMAL(12,10)    DEFAULT NULL,
    logged_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_epoch_per_session (training_id, epoch),
    KEY        idx_epoch_training   (training_id),
    CONSTRAINT fk_epoch_training FOREIGN KEY (training_id)
        REFERENCES training_logs (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Detail metrik per epoch untuk setiap sesi training';

-- =============================================================
-- DATA AWAL (SEED DATA)
-- =============================================================

-- ─── Admin default ────────────────────────────────────────
-- Password: admin123 (bcrypt hash — GANTI di production!)
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
(
    'admin',
    'admin@margibatik.id',
    '$2y$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uElKlFpKm',
    'Administrator Margi Batik',
    'admin'
);

-- ─── Kategori batik (21 kelas sesuai dataset) ─────────────
INSERT INTO batik_categories (slug, name, origin_region, description) VALUES
('bali_barong',                 'Batik Bali Barong',               'Bali',           'Motif barong khas Bali dengan detail ornamen Bali yang kaya.'),
('cendrawasih',                 'Batik Cendrawasih',               'Papua',          'Motif burung cendrawasih khas Papua, melambangkan keindahan alam.'),
('corak_insang',                'Batik Corak Insang',              'Kalimantan Barat','Motif insang ikan khas Kalimantan Barat dengan pola geometris.'),
('dayak',                       'Batik Dayak',                     'Kalimantan',     'Motif suku Dayak dengan ornamen khas budaya Kalimantan.'),
('jakarta_ondel_ondel',         'Batik Jakarta Ondel-Ondel',       'DKI Jakarta',    'Motif ondel-ondel ikon budaya Betawi Jakarta.'),
('jawa_barat_megamendung',      'Batik Jawa Barat Megamendung',    'Jawa Barat',     'Motif awan mendung khas Cirebon dengan gradasi warna indah.'),
('kawung',                      'Batik Kawung',                    'Yogyakarta',     'Motif klasik berbentuk lingkaran mirip buah aren (kawung).'),
('madura_mataketeran',          'Batik Madura Mataketeran',        'Madura',         'Motif khas Madura dengan warna cerah dan pola ekspresif.'),
('megamendung',                 'Batik Megamendung',               'Cirebon',        'Motif awan megamendung ikonik dari Cirebon dengan warna biru.'),
('ntb_lumbung',                 'Batik NTB Lumbung',               'Nusa Tenggara Barat','Motif lumbung padi khas NTB melambangkan kemakmuran.'),
('papua_tifa',                  'Batik Papua Tifa',                'Papua',          'Motif alat musik tifa khas Papua dengan ornamen etnik.'),
('parang',                      'Batik Parang',                    'Jawa',           'Motif diagonal berulang menyerupai ombak laut, motif tertua Jawa.'),
('sasirangan',                  'Batik Sasirangan',                'Kalimantan Selatan','Motif khas Banjar dengan teknik ikat celup warna-warni.'),
('sekar',                       'Batik Sekar',                     'Jawa',           'Motif bunga (sekar) dengan ragam hias flora nusantara.'),
('sogan',                       'Batik Sogan',                     'Solo/Yogyakarta','Batik klasik dengan warna cokelat sogan khas keraton.'),
('solo_parang',                 'Batik Solo Parang',               'Solo',           'Motif parang khas Solo dengan goresan elegan dan halus.'),
('sumatera_barat_rumah_minang', 'Batik Sumatera Barat Rumah Minang','Sumatera Barat','Motif rumah gadang dan ornamen khas Minangkabau.'),
('sumatera_utara_boraspati',    'Batik Sumatera Utara Boraspati',  'Sumatera Utara', 'Motif cicak (boraspati) khas budaya Batak Sumatera Utara.'),
('truntum',                     'Batik Truntum',                   'Solo',           'Motif bintang bertaburan, melambangkan cinta yang tumbuh kembali.'),
('yogyakarta_kawung',           'Batik Yogyakarta Kawung',         'Yogyakarta',     'Motif kawung versi Yogyakarta dengan kehalusan khas keraton.'),
('yogyakarta_parang',           'Batik Yogyakarta Parang',         'Yogyakarta',     'Motif parang khas Yogyakarta, bersejarah dari tradisi keraton.');

-- =============================================================
-- VIEW: Statistik cepat untuk dashboard admin
-- =============================================================
CREATE OR REPLACE VIEW v_dashboard_stats AS
SELECT
    (SELECT COUNT(*) FROM users WHERE role = 'customer') AS total_customers,
    (SELECT COUNT(*) FROM classification_history)        AS total_predictions,
    (SELECT COUNT(*) FROM batik_categories WHERE is_active = 1) AS total_categories,
    (SELECT COUNT(*) FROM training_logs WHERE status = 'completed') AS total_trainings,
    (SELECT ROUND(AVG(confidence), 2) FROM classification_history) AS avg_confidence,
    (SELECT predicted_class FROM classification_history
     GROUP BY predicted_class ORDER BY COUNT(*) DESC LIMIT 1)      AS most_predicted_class;

-- =============================================================
-- VIEW: Riwayat prediksi dengan nama lengkap
-- =============================================================
CREATE OR REPLACE VIEW v_classification_history AS
SELECT
    ch.id,
    ch.created_at,
    COALESCE(u.full_name, 'Tamu')   AS customer_name,
    COALESCE(u.email, '-')          AS customer_email,
    ch.predicted_class,
    bc.name                         AS category_display_name,
    ch.confidence,
    ch.image_filename,
    ch.is_correct
FROM classification_history ch
LEFT JOIN users             u  ON ch.user_id     = u.id
LEFT JOIN batik_categories  bc ON ch.predicted_class = bc.slug
ORDER BY ch.created_at DESC;

-- =============================================================
-- STORED PROCEDURE: Simpan hasil prediksi dari PHP
-- =============================================================
DELIMITER $$

CREATE PROCEDURE sp_save_prediction(
    IN  p_user_id        INT UNSIGNED,
    IN  p_session_id     VARCHAR(128),
    IN  p_image_filename VARCHAR(255),
    IN  p_image_path     VARCHAR(500),
    IN  p_predicted_class VARCHAR(150),
    IN  p_confidence     DECIMAL(6,2),
    IN  p_top_predictions JSON,
    IN  p_model_version  VARCHAR(50),
    IN  p_ip_address     VARCHAR(45),
    OUT p_new_id         INT UNSIGNED
)
BEGIN
    -- Validasi confidence 0-100
    IF p_confidence < 0 THEN
        SET p_confidence = 0;
    END IF;
    IF p_confidence > 100 THEN
        SET p_confidence = 100;
    END IF;

    -- Simpan ke tabel
    INSERT INTO classification_history (
        user_id, session_id, image_filename, image_path,
        predicted_class, confidence, top_predictions,
        model_version, ip_address
    ) VALUES (
        p_user_id, p_session_id, p_image_filename, p_image_path,
        p_predicted_class, p_confidence, p_top_predictions,
        p_model_version, p_ip_address
    );

    SET p_new_id = LAST_INSERT_ID();
END$$

DELIMITER ;

-- =============================================================
-- INDEX TAMBAHAN untuk performa query
-- =============================================================
-- Index komposit untuk query riwayat per user + tanggal
ALTER TABLE classification_history
    ADD INDEX idx_classify_user_date (user_id, created_at DESC);

-- Index untuk statistik per kelas
ALTER TABLE classification_history
    ADD INDEX idx_classify_class_date (predicted_class, created_at DESC);

-- =============================================================
-- VERIFIKASI
-- =============================================================
SELECT
    TABLE_NAME                                                AS `Tabel`,
    TABLE_ROWS                                                AS `Estimasi Baris`,
    ROUND(DATA_LENGTH / 1024, 2)                              AS `Data (KB)`,
    TABLE_COMMENT                                             AS `Keterangan`
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'batik_ai'
ORDER BY TABLE_NAME;
