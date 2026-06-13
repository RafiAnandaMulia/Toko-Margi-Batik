"""
=============================================================
 preprocessing/normalization.py
 Normalisasi nilai piksel gambar dari rentang [0, 255]
 menjadi [0.0, 1.0] dan menyimpan metadata normalisasi.
=============================================================
"""

import os
import sys
import json
import logging
import numpy as np
from PIL import Image

# ─── Setup Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [NORMALIZE] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── Tambahkan path root ──────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RESIZED_DIR, NORMALIZED_DIR, IMG_SIZE


def normalize_dataset(
    source_dir: str = RESIZED_DIR,
    dest_dir:   str = NORMALIZED_DIR,
    save_stats: bool = True
) -> dict:
    """
    Melakukan normalisasi Min-Max (÷255) pada semua gambar.
    Gambar disimpan kembali sebagai PNG untuk menjaga presisi.
    Statistik normalisasi disimpan ke file JSON.

    CATATAN: Normalisasi /255 sama persis dengan yang dilakukan
    oleh tf.keras.applications.mobilenet_v2.preprocess_input()
    saat model di-load. File ini adalah langkah verifikasi visual.

    Args:
        source_dir: Direktori sumber gambar yang sudah diresize
        dest_dir:   Direktori tujuan gambar ternormalisasi
        save_stats: Jika True, simpan statistik ke file JSON

    Returns:
        dict: Statistik normalisasi
    """
    os.makedirs(dest_dir, exist_ok=True)

    stats = {
        "total"          : 0,    # Total gambar diproses
        "success"        : 0,    # Gambar berhasil
        "failed"         : 0,    # Gambar gagal
        "global_mean"    : [],   # Rata-rata piksel semua gambar
        "global_std"     : []    # Standar deviasi piksel
    }

    valid_ext = {".jpg", ".jpeg", ".png"}

    logger.info(f"Memulai normalisasi dari '{source_dir}' → '{dest_dir}'")
    logger.info("Metode: Min-Max Scaling (nilai piksel ÷ 255)")

    # ── Proses setiap kelas ──────────────────────────────
    for class_name in sorted(os.listdir(source_dir)):
        class_src  = os.path.join(source_dir, class_name)

        # Lewati bukan folder
        if not os.path.isdir(class_src):
            continue

        class_dest = os.path.join(dest_dir, class_name)
        os.makedirs(class_dest, exist_ok=True)

        image_files = [
            f for f in os.listdir(class_src)
            if os.path.splitext(f)[1].lower() in valid_ext
        ]

        logger.info(f"  Kelas '{class_name}': {len(image_files)} gambar")
        class_means = []  # Kumpulkan mean per gambar untuk statistik

        for filename in image_files:
            stats["total"] += 1
            src_path  = os.path.join(class_src, filename)
            base_name = os.path.splitext(filename)[0]
            dest_path = os.path.join(class_dest, f"{base_name}.png")   # PNG = lossless

            try:
                # Baca gambar dan konversi ke array numpy float32
                with Image.open(src_path) as img:
                    img_array = np.array(img.convert("RGB"), dtype=np.float32)

                # ── Normalisasi Min-Max: x / 255.0 ────────
                img_norm = img_array / 255.0                # Rentang: [0.0, 1.0]

                # Kumpulkan statistik
                class_means.append(float(np.mean(img_norm)))
                stats["global_std"].append(float(np.std(img_norm)))

                # Kembalikan ke uint8 untuk disimpan sebagai gambar
                # (nilai 0-1 → 0-255 untuk penyimpanan PNG)
                img_save = (img_norm * 255).astype(np.uint8)
                Image.fromarray(img_save).save(dest_path, "PNG")

                stats["success"] += 1

            except Exception as e:
                logger.error(f"  ❌ Error pada {filename}: {e}")
                stats["failed"] += 1

        # Simpan rata-rata kelas
        if class_means:
            stats["global_mean"].extend(class_means)

    # ── Hitung statistik global ──────────────────────────
    if stats["global_mean"]:
        stats["computed_mean"] = float(np.mean(stats["global_mean"]))
        stats["computed_std"]  = float(np.mean(stats["global_std"]))
        logger.info(f"  Global Mean: {stats['computed_mean']:.4f}")
        logger.info(f"  Global Std : {stats['computed_std']:.4f}")
    else:
        stats["computed_mean"] = 0.0
        stats["computed_std"]  = 0.0

    # Hapus data mentah yang terlalu besar untuk JSON
    del stats["global_mean"]
    del stats["global_std"]

    # ── Simpan statistik ke JSON ──────────────────────────
    if save_stats:
        stats_path = os.path.join(dest_dir, "normalization_stats.json")
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        logger.info(f"Statistik disimpan ke: {stats_path}")

    # ── Ringkasan ─────────────────────────────────────────
    logger.info("=" * 55)
    logger.info(f"✅ Berhasil : {stats['success']}")
    logger.info(f"❌ Gagal    : {stats['failed']}")
    logger.info("=" * 55)

    return stats


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    result = normalize_dataset()
    print(f"\n🔢 Normalisasi selesai: {result['success']} gambar diproses.")
