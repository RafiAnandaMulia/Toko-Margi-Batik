"""
=============================================================
 preprocessing/dataset_cleaning.py
 Membersihkan nama file dan mengekstrak original.zip ke
 folder dataset/cleaned/ dengan nama file yang aman.
=============================================================
"""

import os
import re
import sys
import shutil
import zipfile
import unicodedata
import logging

# ─── Setup Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CLEANING] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ──import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

RAW_DIR = os.path.join(BASE_DIR, "dataset", "original")

CLEANED_DIR = os.path.join(BASE_DIR, "dataset", "cleaned")

def slugify_filename(filename: str) -> str:
    """
    Mengubah nama file menjadi format aman:
    - Hapus karakter unicode tidak standar
    - Ganti spasi dan karakter khusus dengan underscore
    - Ubah ke huruf kecil
    - Pertahankan ekstensi file
    """
    # Pisahkan nama dan ekstensi
    name, ext = os.path.splitext(filename)
    ext = ext.lower()                                     # Ekstensi ke huruf kecil

    # Normalisasi unicode (NFD) lalu encode ke ASCII
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # Ganti semua karakter bukan alfanumerik dengan underscore
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

    # Ganti multi-underscore berturut dengan satu underscore
    name = re.sub(r"_+", "_", name)

    # Hapus underscore di awal/akhir nama
    name = name.strip("_").lower()

    # Pastikan nama tidak kosong setelah proses
    if not name:
        name = "image"

    return f"{name}{ext}"


def is_valid_image(filename: str) -> bool:
    """
    Memeriksa apakah file adalah gambar valid berdasarkan ekstensi.
    Mendukung: .jpg, .jpeg, .png, .bmp, .webp, .tiff
    """
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}
    _, ext = os.path.splitext(filename)
    return ext.lower() in valid_extensions


def extract_and_clean_zip(
    zip_path: str = None,
    source_dir: str = RAW_DIR,
    dest_dir: str = CLEANED_DIR
) -> dict:
    """
    Mengekstrak file zip dari RAW_DIR atau langsung dari zip_path,
    lalu membersihkan nama file dan menyalinnya ke CLEANED_DIR.

    Returns:
        dict: Statistik proses { total, valid, skipped, classes }
    """
    os.makedirs(dest_dir, exist_ok=True)

    stats = {
        "total"   : 0,   # Total file yang ditemukan
        "valid"   : 0,   # File gambar valid yang diproses
        "skipped" : 0,   # File yang dilewati (bukan gambar)
        "classes" : []   # Daftar nama kelas
    }

    # ── Tentukan sumber data ──────────────────────────────
    if zip_path and os.path.isfile(zip_path):
        # Gunakan zip path yang diberikan langsung
        zip_files = [zip_path]
        logger.info(f"Memproses zip: {zip_path}")
    else:
        # Cari semua file .zip di RAW_DIR
        zip_files = [
            os.path.join(source_dir, f)
            for f in os.listdir(source_dir)
            if f.endswith(".zip")
        ]
        logger.info(f"Ditemukan {len(zip_files)} file zip di {source_dir}")

    if not zip_files:
        logger.warning("Tidak ada file zip ditemukan. Mencari folder gambar langsung...")
        # Proses folder langsung jika tidak ada zip
        return _process_folder_directly(source_dir, dest_dir, stats)

    # ── Ekstrak setiap file zip ───────────────────────────
    for zip_path in zip_files:
        logger.info(f"Mengekstrak: {os.path.basename(zip_path)}")
        extract_temp = os.path.join(source_dir, "_temp_extract")

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_temp)                # Ekstrak ke folder sementara
            logger.info(f"Ekstraksi selesai ke {extract_temp}")
        except zipfile.BadZipFile as e:
            logger.error(f"File zip rusak: {e}")
            continue

        # Proses hasil ekstraksi
        _process_folder_directly(extract_temp, dest_dir, stats)

        # Hapus folder sementara
        shutil.rmtree(extract_temp, ignore_errors=True)
        logger.info("Folder sementara dihapus.")

    # Simpan daftar kelas ke labels.txt
    labels_file = os.path.join(
        os.path.dirname(dest_dir), "..", "models", "labels.txt"
    )
    os.makedirs(os.path.dirname(labels_file), exist_ok=True)
    with open(labels_file, "w", encoding="utf-8") as f:
        for cls in sorted(stats["classes"]):
            f.write(cls + "\n")
    logger.info(f"Labels disimpan ke: {labels_file}")

    # ── Ringkasan ─────────────────────────────────────────
    logger.info("=" * 55)
    logger.info(f"✅ Total file   : {stats['total']}")
    logger.info(f"✅ Valid gambar : {stats['valid']}")
    logger.info(f"⚠️  Dilewati    : {stats['skipped']}")
    logger.info(f"📁 Kelas        : {len(stats['classes'])}")
    logger.info("=" * 55)

    return stats


def _process_folder_directly(
    source: str,
    dest_dir: str,
    stats: dict
) -> dict:
    """
    Memproses folder gambar secara langsung (tanpa zip).
    Menyalin gambar ke dest_dir dengan nama file yang dibersihkan,
    mempertahankan struktur subfolder kelas.
    """
    for root, dirs, files in os.walk(source):
        for filename in files:
            stats["total"] += 1

            # Lewati jika bukan gambar
            if not is_valid_image(filename):
                stats["skipped"] += 1
                logger.debug(f"Dilewati (bukan gambar): {filename}")
                continue

            # Tentukan nama kelas dari subfolder
            rel_path  = os.path.relpath(root, source)   # Relative path dari source
            parts     = rel_path.replace("\\", "/").split("/")
            # Ambil level pertama yang bermakna sebagai nama kelas
            class_name = None
            for part in parts:
                if part and part != ".":
                    class_name = part
                    break

            if class_name is None:
                class_name = "uncategorized"

            # Bersihkan nama kelas
            clean_class = slugify_filename(class_name)
            clean_class = os.path.splitext(clean_class)[0]  # Hapus ekstensi dari nama kelas

            # Buat folder kelas di dest_dir
            class_dest = os.path.join(dest_dir, clean_class)
            os.makedirs(class_dest, exist_ok=True)

            # Tambahkan ke daftar kelas
            if clean_class not in stats["classes"]:
                stats["classes"].append(clean_class)
                logger.info(f"Kelas baru ditemukan: {clean_class}")

            # Bersihkan nama file
            clean_filename = slugify_filename(filename)

            # Tangani duplikat nama file dengan menambahkan nomor
            dest_path = os.path.join(class_dest, clean_filename)
            counter   = 1
            while os.path.exists(dest_path):
                name, ext  = os.path.splitext(clean_filename)
                dest_path  = os.path.join(class_dest, f"{name}_{counter:04d}{ext}")
                counter   += 1

            # Salin file ke tujuan
            src_path = os.path.join(root, filename)
            shutil.copy2(src_path, dest_path)

            stats["valid"] += 1
            logger.debug(f"  {filename} → {os.path.basename(dest_path)}")

    return stats


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    """
    Jalankan: python dataset_cleaning.py
    Atau: python dataset_cleaning.py /path/to/original.zip
    """
    zip_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result  = extract_and_clean_zip(zip_path=zip_arg)
    print(f"\n📊 Hasil: {result['valid']} gambar dari {len(result['classes'])} kelas.")
