"""
=============================================================
 preprocessing/augmentation.py
 Mendefinisikan konfigurasi ImageDataGenerator dengan
 augmentasi: Rotasi, Skalasi, Translasi, dan Kecerahan.
 Digunakan oleh train_model.py saat proses pelatihan.
=============================================================
"""

import os
import sys
import logging
import numpy as np
from PIL import Image

# ─── Setup Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AUGMENT] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── Tambahkan path root ──────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    AUGMENTED_DIR, TRAIN_DIR, IMG_SIZE,
    ROTATION_RANGE, ZOOM_RANGE,
    WIDTH_SHIFT_RANGE, HEIGHT_SHIFT_RANGE,
    BRIGHTNESS_RANGE, HORIZONTAL_FLIP, FILL_MODE,
    BATCH_SIZE
)


def get_train_datagen():
    """
    Mengembalikan ImageDataGenerator untuk data TRAIN dengan
    semua augmentasi aktif:

    1. Rotasi (rotation_range=25)         : Memutar gambar hingga 25 derajat
       → Alasan: Batik bisa difoto dari sudut berbeda
    2. Skalasi/Zoom (zoom_range=0.2)      : Zoom in/out hingga 20%
       → Alasan: Foto batik bisa diambil dari jarak berbeda
    3. Translasi (width/height_shift=0.2) : Geser horizontal & vertikal hingga 20%
       → Alasan: Objek batik tidak selalu di tengah frame
    4. Kecerahan (brightness=[0.8, 1.2])  : Ubah kecerahan 80%-120%
       → Alasan: Kondisi cahaya berbeda saat foto

    Preprocessing MobileNetV2 dilakukan secara inline (rescale 1/255)
    """
    try:
        from tensorflow.keras.preprocessing.image import ImageDataGenerator
    except ImportError:
        from keras.preprocessing.image import ImageDataGenerator

    datagen = ImageDataGenerator(
        # ── Normalisasi piksel [0,255] → [0.0, 1.0] ──────
        rescale=1.0 / 255.0,

        # ── Rotasi: memutar gambar acak hingga ±25 derajat ──
        rotation_range=ROTATION_RANGE,

        # ── Skalasi/Zoom: zoom in atau out hingga 20% ────
        zoom_range=ZOOM_RANGE,

        # ── Translasi Horizontal: geser kiri/kanan 20% ───
        width_shift_range=WIDTH_SHIFT_RANGE,

        # ── Translasi Vertikal: geser atas/bawah 20% ─────
        height_shift_range=HEIGHT_SHIFT_RANGE,

        # ── Kecerahan: rentang 80%-120% dari asli ────────
        brightness_range=BRIGHTNESS_RANGE,

        # ── Flip Horizontal: cermin kiri-kanan ───────────
        horizontal_flip=HORIZONTAL_FLIP,

        # ── Isi piksel kosong dengan nilai terdekat ───────
        fill_mode=FILL_MODE,

        # ── Shear kecil untuk variasi perspektif ─────────
        shear_range=0.1
    )

    logger.info("✅ Train ImageDataGenerator dikonfigurasi dengan augmentasi penuh:")
    logger.info(f"   Rotasi      : {ROTATION_RANGE}°")
    logger.info(f"   Zoom        : {ZOOM_RANGE*100:.0f}%")
    logger.info(f"   Translasi W : {WIDTH_SHIFT_RANGE*100:.0f}%")
    logger.info(f"   Translasi H : {HEIGHT_SHIFT_RANGE*100:.0f}%")
    logger.info(f"   Kecerahan   : {BRIGHTNESS_RANGE}")
    logger.info(f"   Flip H      : {HORIZONTAL_FLIP}")

    return datagen


def get_val_test_datagen():
    """
    Mengembalikan ImageDataGenerator untuk data VALIDASI dan TEST.
    TIDAK menggunakan augmentasi — hanya normalisasi piksel.
    Alasan: Validasi dan test harus mencerminkan data asli/nyata.
    """
    try:
        from tensorflow.keras.preprocessing.image import ImageDataGenerator
    except ImportError:
        from keras.preprocessing.image import ImageDataGenerator

    datagen = ImageDataGenerator(
        rescale=1.0 / 255.0    # Hanya normalisasi, tanpa augmentasi
    )

    logger.info("✅ Val/Test ImageDataGenerator dikonfigurasi (normalisasi only)")
    return datagen


def get_flow_generators(train_dir: str = TRAIN_DIR,
                        val_dir: str = None,
                        test_dir: str = None,
                        batch_size: int = BATCH_SIZE,
                        img_size: tuple = IMG_SIZE):
    """
    Membuat generator aliran data dari folder untuk training,
    validasi, dan test menggunakan flow_from_directory.

    Args:
        train_dir  : Path ke folder train
        val_dir    : Path ke folder validation (opsional)
        test_dir   : Path ke folder test (opsional)
        batch_size : Jumlah gambar per batch
        img_size   : Ukuran target gambar

    Returns:
        tuple: (train_gen, val_gen, test_gen, class_names)
    """
    from config import VAL_DIR as DEFAULT_VAL, TEST_DIR as DEFAULT_TEST

    val_dir  = val_dir  or DEFAULT_VAL
    test_dir = test_dir or DEFAULT_TEST

    train_datagen    = get_train_datagen()
    val_test_datagen = get_val_test_datagen()

    # ── Generator untuk data Training (dengan augmentasi) ──
    train_gen = train_datagen.flow_from_directory(
        train_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode="categorical",    # One-hot encoding untuk multi-class
        shuffle=True,                # Acak urutan data setiap epoch
        seed=42                      # Seed untuk reprodusibilitas
    )

    # ── Generator untuk data Validasi (tanpa augmentasi) ──
    val_gen = None
    if os.path.exists(val_dir) and os.listdir(val_dir):
        val_gen = val_test_datagen.flow_from_directory(
            val_dir,
            target_size=img_size,
            batch_size=batch_size,
            class_mode="categorical",
            shuffle=False            # Jangan acak validasi untuk konsistensi
        )

    # ── Generator untuk data Test (tanpa augmentasi) ──────
    test_gen = None
    if test_dir and os.path.exists(test_dir) and os.listdir(test_dir):
        test_gen = val_test_datagen.flow_from_directory(
            test_dir,
            target_size=img_size,
            batch_size=batch_size,
            class_mode="categorical",
            shuffle=False            # Jangan acak test untuk evaluasi yang adil
        )

    # Ambil daftar nama kelas dari generator
    class_names = list(train_gen.class_indices.keys())
    logger.info(f"✅ {len(class_names)} kelas ditemukan: {class_names}")
    logger.info(f"   Train samples : {train_gen.samples}")
    logger.info(f"   Val samples   : {val_gen.samples if val_gen else 0}")
    logger.info(f"   Test samples  : {test_gen.samples if test_gen else 0}")

    return train_gen, val_gen, test_gen, class_names


def preview_augmentation(source_dir: str, output_dir: str, n_samples: int = 5):
    """
    Menyimpan contoh gambar hasil augmentasi untuk preview visual.
    Berguna untuk memverifikasi konfigurasi augmentasi sebelum training.

    Args:
        source_dir : Folder berisi gambar asli
        output_dir : Folder tujuan menyimpan hasil preview
        n_samples  : Jumlah contoh per kelas
    """
    os.makedirs(output_dir, exist_ok=True)
    train_datagen = get_train_datagen()

    for class_name in sorted(os.listdir(source_dir)):
        class_src = os.path.join(source_dir, class_name)
        if not os.path.isdir(class_src):
            continue

        class_out = os.path.join(output_dir, class_name)
        os.makedirs(class_out, exist_ok=True)

        images = [
            f for f in os.listdir(class_src)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        if not images:
            continue

        # Ambil gambar pertama untuk di-augmentasi
        img_path  = os.path.join(class_src, images[0])
        with Image.open(img_path) as img:
            img_array = np.array(img.convert("RGB").resize(IMG_SIZE))
            img_array = img_array.reshape((1,) + img_array.shape)   # Shape: (1, H, W, C)

        # Generate n_samples augmentasi
        aug_gen = train_datagen.flow(
            img_array,
            batch_size=1,
            save_to_dir=class_out,
            save_prefix="aug",
            save_format="jpeg"
        )

        for i, _ in enumerate(aug_gen):
            if i >= n_samples:
                break

        logger.info(f"  Preview '{class_name}': {n_samples} gambar disimpan")


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    from config import RESIZED_DIR, AUGMENTED_DIR
    logger.info("Membuat preview augmentasi...")
    preview_augmentation(RESIZED_DIR, AUGMENTED_DIR, n_samples=3)
    print("✅ Preview augmentasi selesai. Cek folder augmented/")
