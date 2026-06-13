"""
=============================================================
 training/hyperparameter.py
 Mendefinisikan semua konfigurasi hyperparameter untuk
 proses pelatihan MobileNetV2.
=============================================================
"""

import os
import sys
import json
import logging
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    EPOCHS, BATCH_SIZE, LEARNING_RATE, FINE_TUNE_LR,
    DROPOUT_RATE, L2_LAMBDA, UNFREEZE_LAYERS, IMG_SIZE,
    ROTATION_RANGE, ZOOM_RANGE, WIDTH_SHIFT_RANGE,
    HEIGHT_SHIFT_RANGE, BRIGHTNESS_RANGE
)

logger = logging.getLogger(__name__)


@dataclass
class TrainingHyperparams:
    """
    Konfigurasi hyperparameter untuk proses training.
    Semua nilai diambil dari config.py sebagai default.
    """

    # ── Arsitektur ────────────────────────────────────────
    model_name      : str   = "MobileNetV2"          # Nama arsitektur
    pretrained_on   : str   = "ImageNet"             # Dataset pretraining
    img_size        : tuple = IMG_SIZE               # (224, 224)
    num_channels    : int   = 3                      # RGB

    # ── Pelatihan Utama (Fase 1: Transfer Learning) ───────
    epochs_phase1   : int   = EPOCHS                 # 50-100 epoch (tanpa early stop)
    batch_size      : int   = BATCH_SIZE             # 32 sampel per batch
    learning_rate   : float = LEARNING_RATE          # 0.0001
    optimizer       : str   = "Adam"                 # Adaptive Moment Estimation

    # ── Fine-Tuning (Fase 2) ──────────────────────────────
    fine_tune_lr    : float = FINE_TUNE_LR           # 0.00001 (10x lebih kecil)
    unfreeze_layers : int   = UNFREEZE_LAYERS        # Jumlah layer yang dibuka
    epochs_phase2   : int   = 20                     # Epoch tambahan fine-tuning

    # ── Regulasi Anti-Overfitting ─────────────────────────
    dropout_rate    : float = DROPOUT_RATE           # 0.4 sebelum output
    l2_lambda       : float = L2_LAMBDA              # 0.0001 L2 penalty
    use_early_stop  : bool  = False                  # TIDAK menggunakan early stop

    # ── Augmentasi ────────────────────────────────────────
    rotation_range  : int   = ROTATION_RANGE         # 25 derajat
    zoom_range      : float = ZOOM_RANGE             # 0.2 (20%)
    width_shift     : float = WIDTH_SHIFT_RANGE      # 0.2 (20%)
    height_shift    : float = HEIGHT_SHIFT_RANGE     # 0.2 (20%)
    brightness_range: list  = None                   # [0.8, 1.2]
    horizontal_flip : bool  = True
    fill_mode       : str   = "nearest"

    # ── Checkpoint ────────────────────────────────────────
    save_best_only  : bool  = False                  # Simpan SETIAP epoch
    checkpoint_mode : str   = "weights"              # Simpan weights saja
    monitor_metric  : str   = "val_accuracy"         # Metric yang dipantau

    def __post_init__(self):
        """Inisialisasi nilai default yang tidak bisa di dataclass"""
        if self.brightness_range is None:
            self.brightness_range = BRIGHTNESS_RANGE

    def to_dict(self) -> dict:
        """Konversi ke dictionary untuk serialisasi JSON"""
        d = asdict(self)
        d["img_size"] = list(d["img_size"])           # Tuple → list untuk JSON
        return d

    def save(self, filepath: str) -> None:
        """Simpan hyperparameter ke file JSON"""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Hyperparameter disimpan: {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "TrainingHyperparams":
        """Muat hyperparameter dari file JSON"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["img_size"] = tuple(data["img_size"])    # list → tuple
        logger.info(f"✅ Hyperparameter dimuat: {filepath}")
        return cls(**data)

    def print_summary(self) -> None:
        """Tampilkan ringkasan hyperparameter ke console"""
        logger.info("=" * 55)
        logger.info("📋 HYPERPARAMETER TRAINING:")
        logger.info(f"   Model          : {self.model_name} ({self.pretrained_on})")
        logger.info(f"   Input Size     : {self.img_size}")
        logger.info(f"   Epochs (Fase1) : {self.epochs_phase1}")
        logger.info(f"   Epochs (Fase2) : {self.epochs_phase2}")
        logger.info(f"   Batch Size     : {self.batch_size}")
        logger.info(f"   LR (Fase1)     : {self.learning_rate}")
        logger.info(f"   LR (Fase2)     : {self.fine_tune_lr}")
        logger.info(f"   Dropout        : {self.dropout_rate}")
        logger.info(f"   L2 Lambda      : {self.l2_lambda}")
        logger.info(f"   Early Stop     : {self.use_early_stop} ← SENGAJA TIDAK AKTIF")
        logger.info(f"   Augmentasi:")
        logger.info(f"     - Rotasi     : {self.rotation_range}°")
        logger.info(f"     - Zoom       : {self.zoom_range}")
        logger.info(f"     - Translasi  : {self.width_shift}/{self.height_shift}")
        logger.info(f"     - Kecerahan  : {self.brightness_range}")
        logger.info("=" * 55)


def get_callbacks(checkpoint_dir: str,
                  log_csv_path:   str,
                  tensorboard_dir: str = None) -> list:
    """
    Membuat dan mengembalikan list callbacks untuk training.
    TIDAK termasuk EarlyStopping sesuai permintaan.

    Callbacks yang digunakan:
    1. ModelCheckpoint  — Simpan checkpoint setiap epoch
    2. CSVLogger        — Catat loss/accuracy ke CSV setiap epoch
    3. ReduceLROnPlateau— Turunkan LR jika val_loss stagnan
    4. TensorBoard      — Visualisasi training (opsional)

    Args:
        checkpoint_dir  : Folder penyimpanan checkpoint
        log_csv_path    : Path file CSV untuk log training
        tensorboard_dir : Folder log TensorBoard (opsional)

    Returns:
        list: Daftar callback yang siap dipakai
    """
    import tensorflow as tf

    callbacks = []
    os.makedirs(checkpoint_dir, exist_ok=True)
    os.makedirs(os.path.dirname(log_csv_path), exist_ok=True)

    # ── 1. ModelCheckpoint ────────────────────────────────
    # Simpan SETIAP epoch (bukan hanya best) agar bisa resume
    checkpoint_path = os.path.join(
        checkpoint_dir,
        "epoch_{epoch:03d}_val_acc_{val_accuracy:.4f}.weights.h5"
    )
    ckpt_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath        = checkpoint_path,
        save_weights_only = True,      # Simpan weights saja (lebih kecil)
        save_best_only  = False,       # ← Simpan SETIAP epoch untuk resume
        monitor         = "val_accuracy",
        verbose         = 1
    )
    callbacks.append(ckpt_callback)
    logger.info(f"✅ ModelCheckpoint: {checkpoint_path}")

    # ── 2. Best Model Checkpoint ─────────────────────────
    # Juga simpan model terbaik secara terpisah
    from config import BEST_MODEL
    best_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath        = BEST_MODEL,
        save_weights_only = False,     # Simpan model lengkap
        save_best_only  = True,        # Hanya simpan yang terbaik
        monitor         = "val_accuracy",
        mode            = "max",
        verbose         = 1
    )
    callbacks.append(best_callback)
    logger.info(f"✅ BestModel Checkpoint: {BEST_MODEL}")

    # ── 3. CSVLogger ──────────────────────────────────────
    # Catat epoch, loss, accuracy, val_loss, val_accuracy ke CSV
    # File ini dibaca oleh PHP untuk tampilkan progress real-time
    csv_callback = tf.keras.callbacks.CSVLogger(
        filename = log_csv_path,
        separator = ",",
        append   = True         # Append agar data resume tidak hilang
    )
    callbacks.append(csv_callback)
    logger.info(f"✅ CSVLogger: {log_csv_path}")

    # ── 4. ReduceLROnPlateau ──────────────────────────────
    # Kurangi learning rate jika validasi stagnan 5 epoch
    # (Bukan early stopping — hanya penyesuaian LR)
    rlrop_callback = tf.keras.callbacks.ReduceLROnPlateau(
        monitor   = "val_loss",
        factor    = 0.5,          # LR × 0.5 saat plateau
        patience  = 5,            # Tunggu 5 epoch sebelum kurangi LR
        min_lr    = 1e-7,         # LR minimum
        verbose   = 1
    )
    callbacks.append(rlrop_callback)
    logger.info("✅ ReduceLROnPlateau: patience=5, factor=0.5")

    # ── 5. TensorBoard (opsional) ────────────────────────
    if tensorboard_dir:
        os.makedirs(tensorboard_dir, exist_ok=True)
        tb_callback = tf.keras.callbacks.TensorBoard(
            log_dir          = tensorboard_dir,
            histogram_freq   = 1,    # Histogram weights setiap 1 epoch
            write_graph      = True,
            update_freq      = "epoch"
        )
        callbacks.append(tb_callback)
        logger.info(f"✅ TensorBoard: {tensorboard_dir}")

    return callbacks


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    hp = TrainingHyperparams()
    hp.print_summary()

    # Simpan ke file JSON
    from config import LOGS_DIR
    save_path = os.path.join(LOGS_DIR, "hyperparameters.json")
    hp.save(save_path)
    print(f"\n✅ Hyperparameter disimpan ke: {save_path}")
