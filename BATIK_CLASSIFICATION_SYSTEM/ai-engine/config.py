"""
=============================================================
 config.py — Konfigurasi global untuk AI Engine Batik
=============================================================
"""

import os

# ─── Direktori Dasar ──────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR    = os.path.join(BASE_DIR, "dataset")
RAW_DIR        = os.path.join(DATASET_DIR, "original")
CLEANED_DIR    = os.path.join(DATASET_DIR, "cleaned")
RESIZED_DIR    = os.path.join(DATASET_DIR, "resized")
NORMALIZED_DIR = os.path.join(DATASET_DIR, "normalized")
AUGMENTED_DIR  = os.path.join(DATASET_DIR, "augmented")
SPLIT_DIR      = os.path.join(DATASET_DIR, "split")
TRAIN_DIR      = os.path.join(SPLIT_DIR, "train")
VAL_DIR        = os.path.join(SPLIT_DIR, "validation")
TEST_DIR       = os.path.join(SPLIT_DIR, "test")

# ─── Direktori Model ──────────────────────────────────────
MODELS_DIR     = os.path.join(BASE_DIR, "models")
CHECKPOINT_DIR = os.path.join(MODELS_DIR, "checkpoints")
BEST_MODEL     = os.path.join(MODELS_DIR, "best_model.h5")
MOBILENET_MODEL= os.path.join(MODELS_DIR, "mobilenet_model.h5")
LABELS_FILE    = os.path.join(MODELS_DIR, "labels.txt")

# ─── Direktori Log ────────────────────────────────────────
LOGS_DIR       = os.path.join(BASE_DIR, "logs")
TRAINING_LOGS  = os.path.join(LOGS_DIR, "training_logs")
TENSORBOARD    = os.path.join(LOGS_DIR, "tensorboard")
PREDICTIONS    = os.path.join(LOGS_DIR, "predictions")
TRAINING_CSV   = os.path.join(TRAINING_LOGS, "training_history.csv")

# ─── Direktori Upload ─────────────────────────────────────
UPLOADS_DIR    = os.path.join(BASE_DIR, "uploads")

# ─── Parameter Gambar ────────────────────────────────────
IMG_SIZE       = (224, 224)           # Ukuran input MobileNetV2
IMG_CHANNELS   = 3                    # RGB

# ─── Parameter Augmentasi ────────────────────────────────
ROTATION_RANGE         = 25           # Derajat rotasi maksimum
ZOOM_RANGE             = 0.2          # Persentase zoom
WIDTH_SHIFT_RANGE      = 0.2          # Pergeseran horizontal (translasi)
HEIGHT_SHIFT_RANGE     = 0.2          # Pergeseran vertikal (translasi)
BRIGHTNESS_RANGE       = [0.8, 1.2]   # Rentang kecerahan
HORIZONTAL_FLIP        = True         # Balik horizontal
FILL_MODE              = "nearest"    # Mode pengisian piksel kosong

# ─── Parameter Pembagian Dataset ─────────────────────────
TRAIN_RATIO = 0.70                    # 70% untuk pelatihan
VAL_RATIO   = 0.20                    # 20% untuk validasi
TEST_RATIO  = 0.10                    # 10% untuk pengujian

# ─── Parameter Pelatihan ─────────────────────────────────
EPOCHS          = 50                  # Jumlah epoch (tanpa early stopping)
BATCH_SIZE      = 32                  # Jumlah sampel per batch
LEARNING_RATE   = 0.0001             # Laju pembelajaran awal
FINE_TUNE_LR    = 0.00001            # Laju pembelajaran fine-tuning
DROPOUT_RATE    = 0.4                # Dropout sebelum output layer
L2_LAMBDA       = 0.0001            # Koefisien L2 Regularization
UNFREEZE_LAYERS = 30                 # Jumlah layer yang di-unfreeze saat fine-tuning

# ─── Pastikan semua folder ada ───────────────────────────
for _dir in [
    RAW_DIR, CLEANED_DIR, RESIZED_DIR, NORMALIZED_DIR,
    AUGMENTED_DIR, TRAIN_DIR, VAL_DIR, TEST_DIR,
    MODELS_DIR, CHECKPOINT_DIR, TRAINING_LOGS,
    TENSORBOARD, PREDICTIONS, UPLOADS_DIR
]:
    os.makedirs(_dir, exist_ok=True)
