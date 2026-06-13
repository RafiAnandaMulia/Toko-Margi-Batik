# 🎨 BATIK CLASSIFICATION SYSTEM
## Toko Margi Batik — Sistem Klasifikasi Citra Batik Berbasis AI

---

## 📋 Deskripsi

Sistem klasifikasi citra batik menggunakan **CNN MobileNetV2** dengan Transfer Learning.
Dibangun untuk **Toko Margi Batik** dengan antarmuka web PHP yang profesional.

---

## 🏗️ Teknologi

| Komponen      | Teknologi                           |
|---------------|-------------------------------------|
| AI Model      | MobileNetV2 + Transfer Learning     |
| Deep Learning | TensorFlow / Keras                  |
| API Bridge    | Flask (Python)                      |
| Frontend      | PHP Native + Bootstrap 5            |
| Database      | MySQL 8+                            |
| Komunikasi    | cURL (PHP → Flask)                  |

---

## 📁 Struktur Proyek

```
BATIK_CLASSIFICATION_SYSTEM/
├── ai-engine/          ← Model AI, preprocessing, training
├── flask-api/          ← REST API jembatan Python↔PHP
├── website/            ← Frontend PHP (admin + customer)
├── database/           ← Skema database MySQL
└── documentation/      ← Diagram & dokumentasi
```

---

## ⚡ Cara Instalasi

### 1. Persiapan Database
```sql
mysql -u root -p < database/batik_ai.sql
```

### 2. Instalasi Python Dependencies
```bash
cd ai-engine
pip install -r requirements.txt
```

### 3. Siapkan Dataset
```bash
# Letakkan original.zip di ai-engine/dataset/raw/
python app.py preprocess --zip dataset/raw/original.zip
```

### 4. Latih Model
```bash
python app.py train --epochs 50 --epochs2 20 --batch 32
```

### 5. Jalankan Flask API
```bash
cd flask-api
python app.py
# API berjalan di: http://localhost:5000
```

### 6. Konfigurasi PHP
- Letakkan folder `website/` di root server PHP (Apache/Nginx)
- Sesuaikan `website/config/database.php` dengan kredensial DB Anda
- Pastikan folder `website/uploads/` dapat ditulis (permission 755)

---

## 🤖 Fitur AI

| Fitur              | Detail                                      |
|--------------------|---------------------------------------------|
| Arsitektur         | MobileNetV2 (ImageNet pretrained)           |
| Input Size         | 224 × 224 × 3 (RGB)                        |
| Augmentasi         | Rotasi ±25°, Zoom 20%, Translasi 20%, Kecerahan 80-120% |
| Anti-Overfitting   | Dropout(0.4) + L2 Regularization(0.0001)   |
| Early Stopping     | ❌ TIDAK DIGUNAKAN                          |
| Resume Training    | ✅ Checkpoint setiap epoch                  |
| Training Phases    | Fase 1: Transfer Learning + Fase 2: Fine-Tuning |

---

## 🔐 Akun Default Admin

| Field    | Value                  |
|----------|------------------------|
| Email    | admin@margibatik.id    |
| Password | admin123               |

> ⚠️ **WAJIB** ganti password setelah instalasi pertama!

---

## 📡 Endpoint Flask API

| Method | Endpoint              | Fungsi                          |
|--------|-----------------------|---------------------------------|
| POST   | /api/dataset/process  | Memulai preprocessing dataset   |
| POST   | /api/model/train      | Memulai training baru           |
| POST   | /api/model/resume     | Resume dari checkpoint          |
| GET    | /api/model/status     | Status training real-time       |
| GET    | /api/model/history    | Riwayat training (CSV)          |
| POST   | /api/predict          | Prediksi gambar batik            |
| GET    | /api/model/info       | Info model yang aktif           |

---

## 📊 Kelas Batik yang Didukung (21 Kelas)

1. Bali Barong         8. Madura Mataketeran  15. Sogan
2. Cendrawasih         9. Megamendung         16. Solo Parang
3. Corak Insang       10. NTB Lumbung         17. Sumatera Barat Rumah Minang
4. Dayak              11. Papua Tifa           18. Sumatera Utara Boraspati
5. Jakarta Ondel-Ondel 12. Parang             19. Truntum
6. Jawa Barat Megamendung 13. Sasirangan     20. Yogyakarta Kawung
7. Kawung             14. Sekar               21. Yogyakarta Parang

---

## 📝 Lisensi

Dibuat khusus untuk **Toko Margi Batik** — Sistem AI Klasifikasi Batik Indonesia.
