"""
=============================================================
 flask-api/services/model_service.py
 Layer service untuk manajemen model training.
=============================================================
"""

import os, sys, json, logging, datetime
logger = logging.getLogger(__name__)


class ModelService:
    def __init__(self, ai_engine_path: str):
        self.ai_engine_path = ai_engine_path
        self._status_file   = os.path.join(
            ai_engine_path, "logs", "training_logs", "training_status.json"
        )

    def get_status(self) -> dict:
        """Baca status training dari file JSON"""
        if not os.path.exists(self._status_file):
            return {"status": "idle", "current_epoch": 0, "total_epochs": 0, "percentage": 0}
        with open(self._status_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def model_exists(self) -> bool:
        """Periksa apakah model sudah ada"""
        models_dir = os.path.join(self.ai_engine_path, "models")
        return any(
            os.path.exists(os.path.join(models_dir, f))
            for f in ["best_model.h5", "mobilenet_model.h5"]
        )

    def get_model_size_mb(self) -> float:
        """Dapatkan ukuran file model dalam MB"""
        for name in ["best_model.h5", "mobilenet_model.h5"]:
            p = os.path.join(self.ai_engine_path, "models", name)
            if os.path.exists(p):
                return round(os.path.getsize(p) / (1024 * 1024), 2)
        return 0.0
