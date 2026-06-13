"""
=============================================================
 flask-api/app.py
 Aplikasi Flask API utama untuk sistem klasifikasi batik
 Toko Margi Batik. Berfungsi sebagai jembatan antara
 PHP frontend dan Python AI engine.
=============================================================
"""

import os
import sys
import logging

# ─── Setup Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FLASK] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── Flask & Extensions ───────────────────────────────────
from flask import Flask, jsonify
from flask_cors import CORS

# ─── Import Blueprints ───────────────────────────────────
from routes.predict_routes import predict_bp
from routes.model_routes   import model_bp
from routes.dataset_routes import dataset_bp


def create_app() -> Flask:
    """
    Factory function untuk membuat dan mengkonfigurasi
    aplikasi Flask.

    Returns:
        Flask: Aplikasi Flask yang sudah dikonfigurasi
    """
    app = Flask(__name__)

    # ── Konfigurasi ───────────────────────────────────────
    app.config["SECRET_KEY"]              = os.environ.get(
        "SECRET_KEY", "margi-batik-secret-2024"
    )
    app.config["MAX_CONTENT_LENGTH"]      = 16 * 1024 * 1024   # Maks 16MB upload
    app.config["UPLOAD_FOLDER"]           = os.path.join(
        os.path.dirname(__file__), "uploads"
    )

    # Path ke AI Engine
    ai_engine_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "ai-engine"
    )
    app.config["AI_ENGINE_PATH"] = ai_engine_path

    # ── CORS: Izinkan permintaan dari PHP website ──────────
    CORS(app, resources={
        r"/api/*": {
            "origins" : ["http://localhost", "http://localhost:80",
                         "http://127.0.0.1", "http://127.0.0.1:80"],
            "methods" : ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # ── Buat folder upload jika belum ada ─────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Daftarkan Blueprints ──────────────────────────────
    app.register_blueprint(predict_bp, url_prefix="/api")    # /api/predict
    app.register_blueprint(model_bp,   url_prefix="/api")    # /api/model
    app.register_blueprint(dataset_bp, url_prefix="/api")    # /api/dataset

    # ── Route Health Check ────────────────────────────────
    @app.route("/", methods=["GET"])
    @app.route("/health", methods=["GET"])
    def health_check():
        """Endpoint untuk memeriksa apakah API berjalan"""
        return jsonify({
            "status"  : "ok",
            "service" : "Margi Batik AI API",
            "version" : "1.0.0",
            "message" : "API berjalan dengan normal"
        }), 200

    # ── Error Handlers ────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": "Request tidak valid"}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Endpoint tidak ditemukan"}), 404

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({"success": False, "error": "File terlalu besar (maks 16MB)"}), 413

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal Server Error: {error}")
        return jsonify({"success": False, "error": "Kesalahan internal server"}), 500

    logger.info("✅ Flask API Margi Batik berhasil dibuat")
    logger.info(f"   AI Engine Path: {ai_engine_path}")

    return app


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(
        host    = "0.0.0.0",
        port    = 5000,
        debug   = False,     # Matikan debug di production
        threaded = True      # Multi-thread untuk concurrent requests
    )
