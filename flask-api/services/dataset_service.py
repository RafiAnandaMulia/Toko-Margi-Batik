"""
=============================================================
 flask-api/services/dataset_service.py
 Layer service untuk manajemen dataset batik.
=============================================================
"""

import os, sys, json, logging
logger = logging.getLogger(__name__)


class DatasetService:
    def __init__(self, ai_engine_path: str):
        self.ai_engine_path = ai_engine_path

    def get_split_stats(self) -> dict:
        """Baca statistik split dataset dari JSON"""
        stats_file = os.path.join(
            self.ai_engine_path, "dataset", "split", "split_stats.json"
        )
        if not os.path.exists(stats_file):
            return {}
        with open(stats_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def count_raw_images(self) -> int:
        """Hitung total gambar di folder raw/"""
        raw_dir = os.path.join(self.ai_engine_path, "dataset", "raw")
        count   = 0
        valid   = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        for root, _, files in os.walk(raw_dir):
            count += sum(1 for f in files if os.path.splitext(f)[1].lower() in valid)
        return count

    def is_dataset_ready(self) -> bool:
        """Periksa apakah dataset sudah diproses"""
        train_dir = os.path.join(self.ai_engine_path, "dataset", "split", "train")
        return os.path.exists(train_dir) and bool(os.listdir(train_dir))
