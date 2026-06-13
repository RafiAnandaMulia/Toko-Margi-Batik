"""
=============================================================
 flask-api/routes/dataset_routes.py
 Blueprint Flask untuk manajemen dataset:
   POST /api/dataset/process — Ekstrak zip & preprocessing
   GET  /api/dataset/info    — Info dataset yang ada
   GET  /api/dataset/classes — Daftar kelas batik
=============================================================
"""

import os
import sys
import json
import logging
import threading

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

logger     = logging.getLogger(__name__)
dataset_bp = Blueprint("dataset", __name__)

_process_thread = None
_process_lock   = threading.Lock()


def get_ai_engine_path() -> str:
    return current_app.config.get(
        "AI_ENGINE_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ai-engine")
    )


# ════════════════════════════════════════════════════════════
# POST /api/dataset/process
# ════════════════════════════════════════════════════════════
@dataset_bp.route("/dataset/process", methods=["POST"])
def process_dataset():
    """
    Memproses dataset: ekstrak zip, cleaning, resize,
    normalisasi, dan split train/val/test.

    Form Data:
        zip_file (file, opsional): Upload file zip baru

    Returns:
        JSON: { success, message, stats }
    """
    global _process_thread

    with _process_lock:
        if _process_thread and _process_thread.is_alive():
            return jsonify({
                "success": False,
                "error"  : "Preprocessing sedang berjalan."
            }), 409

    ai_engine_path = get_ai_engine_path()
    raw_dir        = os.path.join(ai_engine_path, "dataset", "raw")
    os.makedirs(raw_dir, exist_ok=True)

    # Jika ada file zip yang diupload, simpan ke raw/
    uploaded_zip = None
    if "zip_file" in request.files:
        f = request.files["zip_file"]
        if f and f.filename.endswith(".zip"):
            zip_name     = secure_filename(f.filename)
            uploaded_zip = os.path.join(raw_dir, zip_name)
            f.save(uploaded_zip)
            logger.info(f"📦 Zip diupload: {zip_name}")

    if ai_engine_path not in sys.path:
        sys.path.insert(0, ai_engine_path)

    def run_preprocessing():
        """Menjalankan seluruh pipeline preprocessing"""
        try:
            from preprocessing.dataset_cleaning import extract_and_clean_zip
            from preprocessing.resize            import resize_dataset
            from preprocessing.normalization     import normalize_dataset
            from preprocessing.split_dataset     import split_dataset

            logger.info("🔄 [1/4] Cleaning dataset...")
            extract_and_clean_zip(zip_path=uploaded_zip)

            logger.info("🔄 [2/4] Resize gambar...")
            resize_dataset()

            logger.info("🔄 [3/4] Normalisasi...")
            normalize_dataset()

            logger.info("🔄 [4/4] Split dataset...")
            split_dataset()

            logger.info("✅ Preprocessing selesai!")
        except Exception as e:
            logger.error(f"❌ Preprocessing error: {e}", exc_info=True)

    with _process_lock:
        _process_thread = threading.Thread(
            target=run_preprocessing, daemon=True
        )
        _process_thread.start()

    return jsonify({
        "success" : True,
        "message" : "Preprocessing dimulai di background.",
        "zip_used": os.path.basename(uploaded_zip) if uploaded_zip else "existing"
    }), 200


# ════════════════════════════════════════════════════════════
# GET /api/dataset/info
# ════════════════════════════════════════════════════════════
@dataset_bp.route("/dataset/info", methods=["GET"])
def dataset_info():
    """
    Mendapatkan informasi dataset yang sudah diproses.

    Returns:
        JSON: { success, info: {train, val, test, classes} }
    """
    ai_engine_path = get_ai_engine_path()
    split_dir      = os.path.join(ai_engine_path, "dataset", "split")
    labels_file    = os.path.join(ai_engine_path, "models", "labels.txt")
    stats_file     = os.path.join(split_dir, "split_stats.json")

    info = {
        "train_count" : 0,
        "val_count"   : 0,
        "test_count"  : 0,
        "num_classes" : 0,
        "classes"     : []
    }

    # Baca dari stats file jika ada
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f)
            summary = stats.get("_summary", {})
            info.update({
                "train_count" : summary.get("total_train", 0),
                "val_count"   : summary.get("total_val",   0),
                "test_count"  : summary.get("total_test",  0),
                "num_classes" : summary.get("n_classes",   0),
                "classes"     : summary.get("classes",     [])
            })
        except Exception:
            pass

    # Baca labels dari file
    if os.path.exists(labels_file):
        with open(labels_file, "r", encoding="utf-8") as f:
            classes = [line.strip() for line in f if line.strip()]
        info["num_classes"] = len(classes)
        info["classes"]     = classes

    return jsonify({"success": True, "info": info}), 200


# ════════════════════════════════════════════════════════════
# GET /api/dataset/classes
# ════════════════════════════════════════════════════════════
@dataset_bp.route("/dataset/classes", methods=["GET"])
def get_classes():
    """
    Mengembalikan daftar kelas batik yang tersedia.

    Returns:
        JSON: { success, classes: [str, ...] }
    """
    ai_engine_path = get_ai_engine_path()
    labels_file    = os.path.join(ai_engine_path, "models", "labels.txt")

    if not os.path.exists(labels_file):
        return jsonify({
            "success" : False,
            "error"   : "labels.txt belum tersedia. Jalankan preprocessing dulu."
        }), 404

    with open(labels_file, "r", encoding="utf-8") as f:
        classes = [line.strip() for line in f if line.strip()]

    return jsonify({
        "success" : True,
        "classes" : classes,
        "count"   : len(classes)
    }), 200
