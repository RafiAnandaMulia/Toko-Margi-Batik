"""
=============================================================
 flask-api/routes/predict_routes.py
 Blueprint Flask untuk endpoint prediksi gambar batik:
   POST /api/predict  — Upload gambar & dapatkan prediksi
=============================================================
"""

import os
import sys
import uuid
import logging
import datetime
import gc  # Ditambahkan untuk memaksa pembersihan memori pointer gambar

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

logger   = logging.getLogger(__name__)
predict_bp = Blueprint("predict", __name__)

# Ekstensi gambar yang diizinkan
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}


def allowed_file(filename: str) -> bool:
    """Periksa apakah ekstensi file diizinkan"""
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_ai_engine_path() -> str:
    return current_app.config.get(
        "AI_ENGINE_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ai-engine")
    )


# ════════════════════════════════════════════════════════════
# POST /api/predict
# ════════════════════════════════════════════════════════════
@predict_bp.route("/predict", methods=["POST"])
def predict():
    """
    Menerima upload gambar dan mengembalikan hasil prediksi batik.
    """
    # ── Validasi file ──────────────────────────────────────
    if "image" not in request.files:
        return jsonify({"success": False, "error": "Tidak ada file gambar yang dikirim."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Nama file kosong."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success" : False,
            "error"   : f"Format file tidak didukung. Gunakan: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400

    # ── Simpan file sementara ──────────────────────────────
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "/tmp")
    os.makedirs(upload_dir, exist_ok=True)

    # Gunakan UUID untuk menghindari konflik nama file
    unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    save_path   = os.path.join(upload_dir, unique_name)
    file.save(save_path)

    logger.info(f"📥 File diterima: {unique_name}")

    # ── Prediksi ──────────────────────────────────────────
    ai_engine_path = get_ai_engine_path()
    if ai_engine_path not in sys.path:
        sys.path.insert(0, ai_engine_path)

    try:
        from prediction.predict_image import predict_image
        
        # Menggunakan 17 kelas penuh sesuai matriks klasifikasi skripsi Anda
        result = predict_image(save_path, top_k=17, save_log=True)

        # Jalankan pembersihan sampah memori agar lock file gambar terlepas
        gc.collect()

        # Hapus file sementara di folder Flask agar tidak menumpuk memenuhi server
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError as e:
                logger.warning(f"Gagal menghapus file sementara (dikunci proses): {e}")

        return jsonify({
            "success"         : True,
            "predicted_class" : result["predicted_class"],
            "confidence"      : result["confidence"],
            "top_predictions" : result["top_predictions"],
            "model_used"      : result["model_used"],
            "timestamp"       : result["timestamp"]
        }), 200

    except FileNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        
        # Jalankan pembersihan sampah memori saat error terjadi
        gc.collect()
        
        # Hapus file sementara di folder Flask jika proses gagal di tengah jalan
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError:
                pass
        return jsonify({"success": False, "error": f"Prediksi gagal di AI Engine: {str(e)}"}), 500