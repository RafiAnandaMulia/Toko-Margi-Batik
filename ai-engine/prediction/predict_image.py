"""
=============================================================
 prediction/predict_image.py
 Melakukan prediksi klasifikasi citra batik menggunakan
 model MobileNetV2 yang sudah dilatih.
=============================================================
"""
from evaluation.utils import load_model_safe
import os
import sys
import json
import logging
import datetime
import numpy as np
from PIL import Image, UnidentifiedImageError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PREDICT] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    MODELS_DIR, LABELS_FILE, IMG_SIZE, PREDICTIONS
)


def load_model_and_labels():
    """
    Memuat model terbaik dan daftar kelas.

    Returns:
        tuple: (model, class_names, model_path_used)
    """

    model_candidates = [
        os.path.join(MODELS_DIR, "best_model.h5"),
        os.path.join(MODELS_DIR, "mobilenet_model.h5"),
    ]

    model = None
    model_path = None

    for candidate in model_candidates:

        if not os.path.exists(candidate):
            continue

        try:
            logger.info(
                f"📥 Mencoba memuat model: "
                f"{os.path.basename(candidate)}"
            )

            model = load_model_safe(candidate)

            model_path = candidate

            logger.info(
                f"✅ Model berhasil dimuat: "
                f"{os.path.basename(candidate)}"
            )

            break

        except Exception as e:

            logger.warning(
                f"❌ Gagal load {candidate}: {e}"
            )

    if model is None:
        raise FileNotFoundError(
            "Tidak ada model yang valid ditemukan.\n"
            "Periksa best_model.h5 atau mobilenet_model.h5"
        )

    # =====================================================
    # LOAD LABELS
    # =====================================================

    if not os.path.exists(LABELS_FILE):
        raise FileNotFoundError(
            f"labels.txt tidak ditemukan: "
            f"{LABELS_FILE}"
        )

    with open(
        LABELS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        class_names = [
            line.strip()
            for line in f
            if line.strip()
        ]

    logger.info(
        f"✅ {len(class_names)} kelas dimuat"
    )

    return (
        model,
        class_names,
        model_path
    )

def preprocess_image(image_path: str, img_size: tuple = IMG_SIZE) -> np.ndarray:
    """
    Preprocessing gambar untuk input model:
    1. Baca gambar dan konversi ke RGB
    2. Resize ke ukuran model (224x224)
    3. Normalisasi piksel ke [0, 1]
    4. Tambah dimensi batch

    Args:
        image_path: Path ke file gambar
        img_size  : Ukuran target

    Returns:
        np.ndarray: Array gambar siap prediksi (1, 224, 224, 3)
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Gambar tidak ditemukan: {image_path}")

    with Image.open(image_path) as img:
        # Konversi ke RGB (menangani RGBA, grayscale, dll)
        img_rgb     = img.convert("RGB")

        # Resize ke ukuran model
        img_resized = img_rgb.resize(img_size, Image.LANCZOS)

        # Konversi ke array dan normalisasi
        img_array   = np.array(img_resized, dtype=np.float32) / 255.0

        # Tambah dimensi batch: (224, 224, 3) → (1, 224, 224, 3)
        img_batch   = np.expand_dims(img_array, axis=0)

    return img_batch


def predict_image(
    image_path:  str,
    top_k:       int  = 3,
    save_log:    bool = True
) -> dict:
    """
    Melakukan prediksi klasifikasi pada satu gambar.

    Args:
        image_path : Path ke file gambar yang akan diprediksi
        top_k      : Jumlah prediksi teratas yang dikembalikan
        save_log   : Apakah menyimpan log prediksi ke file

    Returns:
        dict: {
            "predicted_class": nama kelas terprediksi,
            "confidence"     : persentase keyakinan (0-100),
            "top_predictions": list [(kelas, confidence), ...],
            "model_used"     : nama model yang dipakai,
            "timestamp"      : waktu prediksi
        }
    """
    # Muat model dan labels
    model, class_names, model_path = load_model_and_labels()

    # Preprocessing gambar
    logger.info(f"🖼️  Memproses gambar: {os.path.basename(image_path)}")
    img_batch = preprocess_image(image_path)

    # ── Prediksi ──────────────────────────────────────────
    predictions = model.predict(img_batch, verbose=0)[0]  # Shape: (num_classes,)

    # Ambil indeks dengan probabilitas tertinggi
    predicted_idx    = int(np.argmax(predictions))
    predicted_class  = class_names[predicted_idx]
    confidence       = float(predictions[predicted_idx]) * 100

    # Ambil top-K prediksi
    top_k_actual = min(top_k, len(class_names))
    top_indices  = np.argsort(predictions)[::-1][:top_k_actual]

    top_predictions = [
        {
            "rank"       : i + 1,
            "class_name" : class_names[idx],
            "confidence" : round(float(predictions[idx]) * 100, 2)
        }
        for i, idx in enumerate(top_indices)
    ]

    # ── Format Hasil ──────────────────────────────────────
    result = {
        "predicted_class"  : predicted_class,
        "confidence"       : round(confidence, 2),
        "top_predictions"  : top_predictions,
        "model_used"       : os.path.basename(model_path),
        "image_path"       : image_path,
        "timestamp"        : datetime.datetime.now().isoformat(),
        "num_classes"      : len(class_names),
    }

    logger.info(f"✅ Prediksi: '{predicted_class}' ({confidence:.2f}% keyakinan)")
    for pred in top_predictions[:3]:
        logger.info(
            f"   #{pred['rank']} {pred['class_name']:<35} : {pred['confidence']:.2f}%"
        )

    # ── Simpan Log Prediksi ───────────────────────────────
    if save_log:
        os.makedirs(PREDICTIONS, exist_ok=True)
        log_filename = f"pred_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_path     = os.path.join(PREDICTIONS, log_filename)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def batch_predict(image_dir: str, output_file: str = None) -> list:
    """
    Melakukan prediksi pada seluruh gambar dalam satu folder.
    Berguna untuk evaluasi batch atau demo.

    Args:
        image_dir  : Folder berisi gambar yang akan diprediksi
        output_file: Path file JSON untuk menyimpan semua hasil

    Returns:
        list: Daftar hasil prediksi untuk setiap gambar
    """
    valid_ext = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    results   = []

    image_files = [
        f for f in os.listdir(image_dir)
        if os.path.splitext(f)[1].lower() in valid_ext
    ]

    logger.info(f"🗂️  Batch prediksi: {len(image_files)} gambar di '{image_dir}'")

    for filename in sorted(image_files):
        img_path = os.path.join(image_dir, filename)
        try:
            result = predict_image(img_path, top_k=3, save_log=False)
            results.append({
                "filename"      : filename,
                "predicted"     : result["predicted_class"],
                "confidence"    : result["confidence"],
                "top3"          : result["top_predictions"][:3]
            })
        except Exception as e:
            logger.error(f"  ❌ Gagal prediksi {filename}: {e}")
            results.append({
                "filename" : filename,
                "error"    : str(e)
            })

    # Simpan hasil ke JSON jika path diberikan
    if output_file:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Hasil batch disimpan: {output_file}")

    return results


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    """
    Jalankan: python predict_image.py <path_gambar>
    """
    import sys
    if len(sys.argv) < 2:
        print("Penggunaan: python predict_image.py <path_gambar>")
        sys.exit(1)

    img_path = sys.argv[1]
    result   = predict_image(img_path, top_k=5)

    print(f"\n🎨 Hasil Prediksi Batik:")
    print(f"   Kelas      : {result['predicted_class']}")
    print(f"   Keyakinan  : {result['confidence']:.2f}%")
    print(f"\n   Top Prediksi:")
    for pred in result["top_predictions"]:
        bar = "█" * int(pred["confidence"] / 5)
        print(f"   #{pred['rank']} {pred['class_name']:<30} {pred['confidence']:6.2f}% {bar}")
