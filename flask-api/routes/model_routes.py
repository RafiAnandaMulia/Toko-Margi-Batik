"""
=============================================================
 flask-api/routes/model_routes.py
 Blueprint Flask untuk endpoint manajemen model:
   POST /api/model/train   — Memulai training baru
   POST /api/model/resume  — Melanjutkan dari checkpoint
   GET  /api/model/status  — Mengambil status training
   GET  /api/model/history — Riwayat training dari CSV
   POST /api/model/evaluate— Evaluasi model pada test set
=============================================================
"""

import os
import sys
import json
import csv
import logging
import threading
import datetime

from flask import Blueprint, request, jsonify, current_app

# ─── Logging ──────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ─── Blueprint ────────────────────────────────────────────
model_bp = Blueprint("model", __name__)

# ─── State Training Global ────────────────────────────────
# Digunakan untuk mencegah dua proses training berjalan bersamaan
_training_thread = None
_training_lock   = threading.Lock()


def get_ai_engine_path() -> str:
    """Mendapatkan path folder ai-engine dari konfigurasi Flask"""
    return current_app.config.get(
        "AI_ENGINE_PATH",
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "ai-engine"
        )
    )


def get_status_file() -> str:
    """Mendapatkan path file status training"""
    ai_path = get_ai_engine_path()
    return os.path.join(ai_path, "logs", "training_logs", "training_status.json")


def get_csv_log_file() -> str:
    """Mendapatkan path file CSV log training"""
    ai_path = get_ai_engine_path()
    return os.path.join(ai_path, "logs", "training_logs", "training_history.csv")


def read_training_status() -> dict:
    """
    Membaca status training dari file JSON.
    File ini di-update oleh callback training setiap epoch.

    Returns:
        dict: Status training saat ini
    """
    status_file = get_status_file()

    default_status = {
        "status"          : "idle",
        "current_epoch"   : 0,
        "total_epochs"    : 0,
        "percentage"      : 0,
        "metrics"         : {},
        "message"         : "Tidak ada proses training aktif",
        "timestamp"       : datetime.datetime.now().isoformat()
    }

    if not os.path.exists(status_file):
        return default_status

    try:
        with open(status_file, "r", encoding="utf-8") as f:
            status = json.load(f)
        return status
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error baca status file: {e}")
        return default_status


def read_csv_history(max_rows: int = 200) -> list:
    """
    Membaca riwayat training dari file CSV.

    Args:
        max_rows: Jumlah baris terakhir yang dibaca

    Returns:
        list: Daftar data per epoch
    """
    csv_path = get_csv_log_file()

    if not os.path.exists(csv_path):
        return []

    rows = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Konversi nilai string ke float
                formatted = {
                    "epoch"         : int(float(row.get("epoch", 0))) + 1,
                    "loss"          : round(float(row.get("loss", 0)), 5),
                    "accuracy"      : round(float(row.get("accuracy", 0)) * 100, 2),
                    "val_loss"      : round(float(row.get("val_loss", 0)), 5),
                    "val_accuracy"  : round(float(row.get("val_accuracy", 0)) * 100, 2),
                }
                rows.append(formatted)

        # Ambil N baris terakhir
        return rows[-max_rows:]

    except Exception as e:
        logger.error(f"Error baca CSV: {e}")
        return []


# ════════════════════════════════════════════════════════════
# ENDPOINT: POST /api/model/train
# ════════════════════════════════════════════════════════════
@model_bp.route("/model/train", methods=["POST"])
def start_training():
    """
    Memulai proses training baru dari awal (asynchronous).
    Training dijalankan di background thread agar API tetap responsif.

    Request Body (JSON):
        epochs_phase1 (int)  : Epoch untuk transfer learning (default: 50)
        epochs_phase2 (int)  : Epoch untuk fine-tuning (default: 20)
        batch_size    (int)  : Ukuran batch (default: 32)

    Returns:
        JSON: { success, message, status }
    """
    global _training_thread

    # ── Cek apakah training sudah berjalan ────────────────
    with _training_lock:
        if _training_thread and _training_thread.is_alive():
            return jsonify({
                "success" : False,
                "error"   : "Training sedang berjalan. Gunakan /api/model/status untuk memantau."
            }), 409  # Conflict

    # ── Ambil parameter dari request ──────────────────────
    data           = request.get_json(silent=True) or {}
    epochs_phase1  = int(data.get("epochs_phase1", 50))
    epochs_phase2  = int(data.get("epochs_phase2", 20))
    batch_size     = int(data.get("batch_size",    32))

    # ── Validasi ──────────────────────────────────────────
    if epochs_phase1 < 1 or epochs_phase1 > 300:
        return jsonify({
            "success" : False,
            "error"   : "epochs_phase1 harus antara 1 dan 300"
        }), 400

    ai_engine_path = get_ai_engine_path()

    # ── Tambahkan ai-engine ke sys.path ───────────────────
    if ai_engine_path not in sys.path:
        sys.path.insert(0, ai_engine_path)

    def run_training():
        """Fungsi yang dijalankan di background thread"""
        try:
            logger.info(f"🚀 Thread training dimulai (phase1={epochs_phase1}, phase2={epochs_phase2})")
            from training.train_model import train_model
            train_model(
                epochs_phase1 = epochs_phase1,
                epochs_phase2 = epochs_phase2,
                batch_size    = batch_size
            )
            logger.info("✅ Thread training selesai")
        except Exception as e:
            logger.error(f"❌ Error di thread training: {e}", exc_info=True)
            # Update status ke error
            status_file = get_status_file()
            os.makedirs(os.path.dirname(status_file), exist_ok=True)
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump({
                    "status"    : "error",
                    "message"   : str(e),
                    "timestamp" : datetime.datetime.now().isoformat()
                }, f, indent=2)

    # ── Jalankan di background thread ────────────────────
    with _training_lock:
        _training_thread = threading.Thread(
            target=run_training,
            name  ="TrainingThread",
            daemon=True    # Thread berhenti jika proses utama berhenti
        )
        _training_thread.start()

    logger.info(f"▶️  Training dimulai: {epochs_phase1}+{epochs_phase2} epoch")

    return jsonify({
        "success"       : True,
        "message"       : f"Training dimulai ({epochs_phase1} + {epochs_phase2} epoch)",
        "status"        : "running",
        "total_epochs"  : epochs_phase1 + epochs_phase2,
        "batch_size"    : batch_size
    }), 200


# ════════════════════════════════════════════════════════════
# ENDPOINT: POST /api/model/resume
# ════════════════════════════════════════════════════════════
@model_bp.route("/model/resume", methods=["POST"])
def resume_training():
    """
    Melanjutkan training dari checkpoint terakhir (asynchronous).

    Request Body (JSON):
        target_epochs (int): Total epoch target (default: dari config)
        batch_size    (int): Ukuran batch (default: 32)

    Returns:
        JSON: { success, message, from_epoch, target_epochs }
    """
    global _training_thread

    # Cek apakah training sudah berjalan
    with _training_lock:
        if _training_thread and _training_thread.is_alive():
            return jsonify({
                "success" : False,
                "error"   : "Training sedang berjalan, tidak perlu resume."
            }), 409

    data          = request.get_json(silent=True) or {}
    target_epochs = data.get("target_epochs", None)
    batch_size    = int(data.get("batch_size", 32))

    ai_engine_path = get_ai_engine_path()
    if ai_engine_path not in sys.path:
        sys.path.insert(0, ai_engine_path)

    def run_resume():
        """Fungsi resume yang dijalankan di background thread"""
        try:
            logger.info("🔄 Thread resume training dimulai")
            from training.resume_training import resume_training as do_resume
            do_resume(
                target_epochs = target_epochs,
                batch_size    = batch_size
            )
            logger.info("✅ Thread resume selesai")
        except Exception as e:
            logger.error(f"❌ Error di thread resume: {e}", exc_info=True)
            status_file = get_status_file()
            os.makedirs(os.path.dirname(status_file), exist_ok=True)
            with open(status_file, "w") as f:
                json.dump({
                    "status"  : "error",
                    "message" : str(e),
                    "timestamp": datetime.datetime.now().isoformat()
                }, f)

    with _training_lock:
        _training_thread = threading.Thread(
            target=run_resume,
            name  ="ResumeThread",
            daemon=True
        )
        _training_thread.start()

    logger.info("▶️  Resume training dimulai di background thread")

    return jsonify({
        "success"      : True,
        "message"      : "Resume training dimulai dari checkpoint terakhir",
        "status"       : "running",
        "target_epochs": target_epochs
    }), 200


# ════════════════════════════════════════════════════════════
# ENDPOINT: GET /api/model/status
# ════════════════════════════════════════════════════════════
@model_bp.route("/model/status", methods=["GET"])
def get_training_status():
    """
    Mengambil status training saat ini dari file JSON.
    Dipanggil oleh PHP setiap 3 detik untuk polling real-time.

    Returns:
        JSON: {
            status, current_epoch, total_epochs,
            percentage, metrics, message, timestamp
        }
    """
    status = read_training_status()

    # Tambahkan info apakah thread masih berjalan
    status["thread_alive"] = (
        _training_thread is not None and _training_thread.is_alive()
    )

    return jsonify(status), 200


# ════════════════════════════════════════════════════════════
# ENDPOINT: GET /api/model/history
# ════════════════════════════════════════════════════════════
@model_bp.route("/model/history", methods=["GET"])
def get_training_history():
    """
    Mengambil riwayat training dari file CSV log.
    Digunakan untuk menampilkan grafik akurasi dan loss.

    Query params:
        limit (int): Jumlah epoch terakhir (default: 100)

    Returns:
        JSON: { success, data: [{epoch, loss, accuracy, ...}] }
    """
    limit   = int(request.args.get("limit", 100))
    history = read_csv_history(max_rows=limit)

    return jsonify({
        "success"     : True,
        "data"        : history,
        "total_epochs": len(history)
    }), 200


# ════════════════════════════════════════════════════════════
# ENDPOINT: POST /api/model/evaluate
# ════════════════════════════════════════════════════════════
@model_bp.route("/model/evaluate", methods=["POST"])
def evaluate_model():
    """
    Menjalankan evaluasi model pada data test set.

    Returns:
        JSON: { success, metrics: {loss, accuracy, top3} }
    """
    ai_engine_path = get_ai_engine_path()
    if ai_engine_path not in sys.path:
        sys.path.insert(0, ai_engine_path)

    try:
        from evaluation.evaluate_model import evaluate_model as do_evaluate
        results = do_evaluate()

        return jsonify({
            "success" : True,
            "metrics" : results
        }), 200

    except FileNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"Evaluate error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ════════════════════════════════════════════════════════════
# ENDPOINT: GET /api/model/info
# ════════════════════════════════════════════════════════════
@model_bp.route("/model/info", methods=["GET"])
def get_model_info():
    """
    Mendapatkan informasi model yang aktif (ukuran file, tanggal, kelas).

    Returns:
        JSON: { success, model_info }
    """
    ai_engine_path = get_ai_engine_path()
    models_dir     = os.path.join(ai_engine_path, "models")
    labels_file    = os.path.join(models_dir, "labels.txt")
    best_model     = os.path.join(models_dir, "best_model.h5")

    info = {
        "model_exists"  : os.path.exists(best_model),
        "model_path"    : best_model,
        "model_size_mb" : 0,
        "last_modified" : None,
        "num_classes"   : 0,
        "class_names"   : []
    }

    if os.path.exists(best_model):
        stat = os.stat(best_model)
        info["model_size_mb"]  = round(stat.st_size / (1024 * 1024), 2)
        info["last_modified"]  = datetime.datetime.fromtimestamp(
            stat.st_mtime
        ).isoformat()

    if os.path.exists(labels_file):
        with open(labels_file, "r", encoding="utf-8") as f:
            classes = [line.strip() for line in f if line.strip()]
        info["num_classes"]  = len(classes)
        info["class_names"]  = classes

    return jsonify({"success": True, "model_info": info}), 200
