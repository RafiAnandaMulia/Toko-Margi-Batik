"""
=============================================================
 preprocessing/resize.py
 Meresize semua gambar dari CLEANED_DIR ke (224, 224)
 dan menyimpannya ke RESIZED_DIR.
=============================================================
"""

import os
import sys
import logging
from PIL import Image, UnidentifiedImageError

# ─── Setup Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RESIZE] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── Tambahkan path root ──────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import CLEANED_DIR, RESIZED_DIR, IMG_SIZE


def resize_dataset(
    source_dir: str = CLEANED_DIR,
    dest_dir:   str = RESIZED_DIR,
    img_size:   tuple = IMG_SIZE
) -> dict:
    """
    Meresize semua gambar dari source_dir ke ukuran img_size
    dengan mempertahankan struktur subfolder kelas.

    Args:
        source_dir: Direktori sumber gambar (setelah cleaning)
        dest_dir:   Direktori tujuan gambar yang sudah diresize
        img_size:   Tuple ukuran target (width, height) default (224, 224)

    Returns:
        dict: Statistik { success, failed, skipped }
    """
    os.makedirs(dest_dir, exist_ok=True)

    stats = {
        "success" : 0,   # Gambar berhasil diresize
        "failed"  : 0,   # Gambar gagal diproses
        "skipped" : 0    # File yang bukan gambar
    }

    # Ekstensi gambar yang didukung
    valid_ext = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}

    logger.info(f"Memulai resize dari '{source_dir}' → '{dest_dir}' (ukuran: {img_size})")

    # Jalan melalui semua subfolder (setiap subfolder = 1 kelas)
    for class_name in sorted(os.listdir(source_dir)):
        class_src = os.path.join(source_dir, class_name)

        # Lewati jika bukan folder
        if not os.path.isdir(class_src):
            continue

        # Buat folder kelas di direktori tujuan
        class_dest = os.path.join(dest_dir, class_name)
        os.makedirs(class_dest, exist_ok=True)

        image_files = [
            f for f in os.listdir(class_src)
            if os.path.splitext(f)[1].lower() in valid_ext
        ]

        logger.info(f"  Kelas '{class_name}': {len(image_files)} gambar")

        for filename in image_files:
            src_path  = os.path.join(class_src, filename)
            # Simpan selalu sebagai .jpg untuk konsistensi
            base_name = os.path.splitext(filename)[0]
            dest_path = os.path.join(class_dest, f"{base_name}.jpg")

            try:
                with Image.open(src_path) as img:
                    # Konversi ke RGB (menangani gambar RGBA/grayscale/palette)
                    img_rgb = img.convert("RGB")

                    # Resize dengan metode LANCZOS (kualitas terbaik untuk downscale)
                    img_resized = img_rgb.resize(img_size, Image.LANCZOS)

                    # Simpan sebagai JPEG dengan kualitas 95%
                    img_resized.save(dest_path, "JPEG", quality=95, optimize=True)

                stats["success"] += 1

            except UnidentifiedImageError:
                # File tidak bisa dikenali sebagai gambar
                logger.warning(f"  ⚠️  File tidak valid: {filename}")
                stats["failed"] += 1

            except Exception as e:
                # Error lain saat proses
                logger.error(f"  ❌ Error pada {filename}: {e}")
                stats["failed"] += 1

    # ── Ringkasan ─────────────────────────────────────────
    logger.info("=" * 55)
    logger.info(f"✅ Berhasil : {stats['success']}")
    logger.info(f"❌ Gagal    : {stats['failed']}")
    logger.info(f"⚠️  Dilewati: {stats['skipped']}")
    logger.info("=" * 55)

    return stats


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    result = resize_dataset()
    print(f"\n📏 Resize selesai: {result['success']} gambar berhasil diproses.")
