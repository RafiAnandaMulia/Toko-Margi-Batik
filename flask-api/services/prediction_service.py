"""
=============================================================
 flask-api/services/prediction_service.py
 Layer service untuk logika prediksi gambar batik.
 Mengintegrasikan Core AI Engine dengan Flask Application.
=============================================================
"""

import os
import sys
import logging
import datetime
import gc  # Ditambahkan untuk memaksa pembersihan memori pointer gambar setelah prediksi

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Service class yang membungkus logika prediksi AI engine.
    Memisahkan business logic dari layer route (Blueprint).
    """

    def __init__(self, ai_engine_path: str):
        """
        Inisialisasi service dengan path AI engine.

        Args:
            ai_engine_path: Path absolut ke folder ai-engine
        """
        self.ai_engine_path = ai_engine_path
        if ai_engine_path not in sys.path:
            sys.path.insert(0, ai_engine_path)

    def predict(self, image_path: str, top_k: int = 17) -> dict:
        """
        Melakukan prediksi klasifikasi pada gambar.

        Args:
            image_path: Path ke file gambar yang sudah disimpan sementara
            top_k     : Jumlah prediksi teratas (Default: 17 untuk seluruh motif skripsi)

        Returns:
            dict: Hasil prediksi lengkap dari core AI engine

        Raises:
            FileNotFoundError: Jika model atau gambar tidak ada
            RuntimeError     : Jika prediksi gagal
        """
        try:
            from prediction.predict_image import predict_image
            
            # Memanggil fungsi core prediction dengan mengekspos 17 kelas penuh
            result = predict_image(image_path, top_k=top_k, save_log=True)
            
            # Paksa Python untuk membersihkan memori garbage collection 
            # agar file gambar tidak dikunci (locked) oleh TensorFlow setelah prediksi selesai
            gc.collect()
            
            return result
            
        except FileNotFoundError:
            # Paksa pelepasan memori jika terjadi error file tidak ditemukan
            gc.collect()
            raise
        except Exception as e:
            logger.error(f"PredictionService error: {e}")
            # Paksa pelepasan memori jika terjadi crash di dalam AI Engine
            gc.collect()
            raise RuntimeError(f"Prediksi gagal di layer service: {str(e)}")

    def get_available_classes(self) -> list:
        """
        Mendapatkan daftar kelas batik yang tersedia dari file konfigurasi label.

        Returns:
            list: Nama-nama kelas batik
        """
        labels_file = os.path.join(self.ai_engine_path, "models", "labels.txt")
        if not os.path.exists(labels_file):
            return []
        try:
            with open(labels_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Gagal membaca labels.txt: {e}")
            return []

    def is_model_ready(self) -> bool:
        """
        Memeriksa apakah file bobot model (.h5) sudah tersedia di folder arsitektur.

        Returns:
            bool: True jika model siap digunakan
        """
        models_dir = os.path.join(self.ai_engine_path, "models")
        candidates = ["best_model.h5", "mobilenet_model.h5"]
        for name in candidates:
            if os.path.exists(os.path.join(models_dir, name)):
                return True
        return False