"""
=============================================================
 preprocessing/split_dataset.py
 Membagi dataset gambar menjadi:
   - Train      : 70%
   - Validation : 20%
   - Test       : 10%
 secara SEIMBANG per kelas (stratified split).
=============================================================
"""

import os
import sys
import json
import shutil
import random
import logging
from pathlib import Path

# ─── Setup Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SPLIT] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── Tambahkan path root ──────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    RESIZED_DIR, TRAIN_DIR, VAL_DIR, TEST_DIR,
    TRAIN_RATIO, VAL_RATIO, TEST_RATIO,
    LABELS_FILE
)


def split_dataset(
    source_dir:  str   = RESIZED_DIR,
    train_dir:   str   = TRAIN_DIR,
    val_dir:     str   = VAL_DIR,
    test_dir:    str   = TEST_DIR,
    train_ratio: float = TRAIN_RATIO,
    val_ratio:   float = VAL_RATIO,
    test_ratio:  float = TEST_RATIO,
    seed:        int   = 42,
    copy_mode:   bool  = True
) -> dict:
    """
    Membagi dataset secara stratified (seimbang per kelas).

    Args:
        source_dir  : Direktori sumber berisi subfolder per kelas
        train_dir   : Direktori tujuan untuk data training
        val_dir     : Direktori tujuan untuk data validasi
        test_dir    : Direktori tujuan untuk data test
        train_ratio : Proporsi data training (default 0.70)
        val_ratio   : Proporsi data validasi (default 0.20)
        test_ratio  : Proporsi data test (default 0.10)
        seed        : Seed random untuk reprodusibilitas
        copy_mode   : True=salin file, False=pindahkan file

    Returns:
        dict: Statistik pembagian per kelas
    """
    # Validasi rasio: harus berjumlah 1.0
    total = round(train_ratio + val_ratio + test_ratio, 10)
    assert abs(total - 1.0) < 1e-9, \
        f"Rasio harus berjumlah 1.0, tapi {total}"

    # Set seed untuk reprodusibilitas
    random.seed(seed)

    # Buat folder tujuan
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir,   exist_ok=True)
    os.makedirs(test_dir,  exist_ok=True)

    stats       = {}    # Statistik per kelas
    all_classes = []    # Daftar semua kelas

    # Ekstensi gambar yang valid
    valid_ext = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}

    logger.info(f"Sumber   : {source_dir}")
    logger.info(f"Train    : {train_ratio*100:.0f}%  → {train_dir}")
    logger.info(f"Val      : {val_ratio*100:.0f}%   → {val_dir}")
    logger.info(f"Test     : {test_ratio*100:.0f}%   → {test_dir}")
    logger.info(f"Seed     : {seed}")
    logger.info(f"Mode     : {'Salin' if copy_mode else 'Pindah'}")
    logger.info("=" * 55)

    # ── Proses setiap kelas ──────────────────────────────
    for class_name in sorted(os.listdir(source_dir)):
        class_src = os.path.join(source_dir, class_name)

        # Lewati jika bukan folder
        if not os.path.isdir(class_src):
            continue

        # Kumpulkan semua file gambar di kelas ini
        all_images = sorted([
            f for f in os.listdir(class_src)
            if os.path.splitext(f)[1].lower() in valid_ext
        ])

        n_total = len(all_images)

        if n_total == 0:
            logger.warning(f"  ⚠️  Kelas '{class_name}' tidak memiliki gambar, dilewati.")
            continue

        # Acak urutan gambar dengan seed yang sama
        random.shuffle(all_images)

        # ── Hitung jumlah per split ──────────────────────
        n_train = max(1, int(n_total * train_ratio))    # Minimal 1 gambar
        n_val   = max(1, int(n_total * val_ratio))      # Minimal 1 gambar
        n_test  = n_total - n_train - n_val              # Sisa untuk test

        # Pastikan test minimal 1 gambar jika total > 3
        if n_test < 1 and n_total >= 3:
            n_val  = max(1, n_val - 1)
            n_test = n_total - n_train - n_val

        # Potong daftar gambar sesuai split
        train_imgs = all_images[:n_train]
        val_imgs   = all_images[n_train : n_train + n_val]
        test_imgs  = all_images[n_train + n_val :]

        # ── Salin/Pindahkan ke folder tujuan ─────────────
        transfer_fn = shutil.copy2 if copy_mode else shutil.move

        for split_name, split_imgs, split_dir in [
            ("train",      train_imgs, train_dir),
            ("validation", val_imgs,   val_dir),
            ("test",       test_imgs,  test_dir),
        ]:
            # Buat subfolder kelas di split
            split_class_dir = os.path.join(split_dir, class_name)
            os.makedirs(split_class_dir, exist_ok=True)

            for filename in split_imgs:
                src  = os.path.join(class_src, filename)
                dest = os.path.join(split_class_dir, filename)

                # Tangani konflik nama file
                if os.path.exists(dest):
                    base, ext = os.path.splitext(filename)
                    dest = os.path.join(split_class_dir, f"{base}_dup{ext}")

                try:
                    transfer_fn(src, dest)
                except Exception as e:
                    logger.error(f"  ❌ Gagal transfer {filename}: {e}")

        # Catat statistik kelas ini
        stats[class_name] = {
            "total"      : n_total,
            "train"      : len(train_imgs),
            "validation" : len(val_imgs),
            "test"       : len(test_imgs),
            "train_pct"  : round(len(train_imgs) / n_total * 100, 1),
            "val_pct"    : round(len(val_imgs)   / n_total * 100, 1),
            "test_pct"   : round(len(test_imgs)  / n_total * 100, 1),
        }
        all_classes.append(class_name)

        logger.info(
            f"  {class_name:<35} "
            f"Total:{n_total:4d} | "
            f"Train:{len(train_imgs):4d} | "
            f"Val:{len(val_imgs):3d} | "
            f"Test:{len(test_imgs):3d}"
        )

    # ── Ringkasan Global ──────────────────────────────────
    total_img   = sum(s["total"]      for s in stats.values())
    total_train = sum(s["train"]      for s in stats.values())
    total_val   = sum(s["validation"] for s in stats.values())
    total_test  = sum(s["test"]       for s in stats.values())

    logger.info("=" * 55)
    logger.info(f"📊 TOTAL DATASET : {total_img} gambar")
    logger.info(f"   Train         : {total_train} ({total_train/total_img*100:.1f}%)")
    logger.info(f"   Validation    : {total_val}  ({total_val/total_img*100:.1f}%)")
    logger.info(f"   Test          : {total_test}   ({total_test/total_img*100:.1f}%)")
    logger.info(f"   Kelas         : {len(all_classes)}")
    logger.info("=" * 55)

    # ── Simpan Labels ─────────────────────────────────────
    os.makedirs(os.path.dirname(LABELS_FILE), exist_ok=True)
    with open(LABELS_FILE, "w", encoding="utf-8") as f:
        for cls in sorted(all_classes):
            f.write(cls + "\n")
    logger.info(f"Labels disimpan: {LABELS_FILE}")

    # ── Simpan Statistik Split ────────────────────────────
    stats_file = os.path.join(os.path.dirname(TRAIN_DIR), "split_stats.json")
    stats["_summary"] = {
        "total_images" : total_img,
        "total_train"  : total_train,
        "total_val"    : total_val,
        "total_test"   : total_test,
        "n_classes"    : len(all_classes),
        "classes"      : sorted(all_classes)
    }
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    logger.info(f"Statistik split disimpan: {stats_file}")

    return stats


def verify_split(train_dir: str = TRAIN_DIR,
                 val_dir:   str = VAL_DIR,
                 test_dir:  str = TEST_DIR) -> None:
    """
    Memverifikasi hasil split dengan menghitung ulang jumlah file
    di setiap folder split.
    """
    logger.info("\n🔍 VERIFIKASI SPLIT:")
    for split_name, split_dir in [("train", train_dir),
                                   ("validation", val_dir),
                                   ("test", test_dir)]:
        if not os.path.exists(split_dir):
            logger.warning(f"  Folder tidak ada: {split_dir}")
            continue

        for class_name in sorted(os.listdir(split_dir)):
            class_path = os.path.join(split_dir, class_name)
            if os.path.isdir(class_path):
                count = len([
                    f for f in os.listdir(class_path)
                    if os.path.splitext(f)[1].lower() in
                    {".jpg", ".jpeg", ".png", ".bmp"}
                ])
                logger.info(f"  {split_name:<12} | {class_name:<35} : {count:4d} gambar")


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    result = split_dataset()
    verify_split()
    print(f"\n✅ Split selesai: {result['_summary']['n_classes']} kelas, "
          f"{result['_summary']['total_images']} gambar total.")
