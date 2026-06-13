"""
=============================================================
 training/fine_tuning.py
 Skrip Fine-Tuning terpisah untuk mengoptimalkan model
 yang sudah dilatih pada fase Transfer Learning.
=============================================================
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FINETUNE] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    MODELS_DIR, CHECKPOINT_DIR, TRAINING_CSV,
    LABELS_FILE, BATCH_SIZE, FINE_TUNE_LR,
    UNFREEZE_LAYERS, TENSORBOARD
)


def run_fine_tuning(
    model_path:     str   = None,
    epochs:         int   = 20,
    batch_size:     int   = BATCH_SIZE,
    fine_tune_lr:   float = FINE_TUNE_LR,
    unfreeze_layers: int  = UNFREEZE_LAYERS
) -> None:
    """
    Menjalankan Fine-Tuning pada model yang sudah ada.
    Fine-tuning membuka layer terakhir MobileNetV2 untuk
    mengadaptasi low-level features ke domain batik.

    Args:
        model_path     : Path model .h5 (default: best_model.h5)
        epochs         : Jumlah epoch fine-tuning
        batch_size     : Ukuran batch
        fine_tune_lr   : Learning rate (sangat kecil)
        unfreeze_layers: Jumlah layer terakhir yang dibuka
    """
    import tensorflow as tf

    # Default model path
    model_path = model_path or os.path.join(MODELS_DIR, "best_model.h5")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model tidak ditemukan: {model_path}\n"
            "Jalankan train_model.py terlebih dahulu."
        )

    logger.info("=" * 60)
    logger.info("🔬 FINE-TUNING DIMULAI")
    logger.info(f"   Model sumber  : {model_path}")
    logger.info(f"   Epochs        : {epochs}")
    logger.info(f"   LR Fine-Tune  : {fine_tune_lr}")
    logger.info(f"   Layer dibuka  : {unfreeze_layers}")
    logger.info("=" * 60)

    # ── Load Model ────────────────────────────────────────
    logger.info("📥 Loading model...")
    model = tf.keras.models.load_model(model_path)
    logger.info(f"✅ Model dimuat dari: {model_path}")

    # ── Baca Epoch Terakhir dari CSV ─────────────────────
    initial_epoch = 0
    if os.path.exists(TRAINING_CSV):
        import csv
        with open(TRAINING_CSV, "r") as f:
            rows = list(csv.DictReader(f))
        if rows:
            initial_epoch = int(float(rows[-1].get("epoch", 0))) + 1

    logger.info(f"   Melanjutkan dari epoch: {initial_epoch}")

    # ── Buka Layer untuk Fine-Tuning ──────────────────────
    from training.transfer_learning import unfreeze_top_layers
    model = unfreeze_top_layers(
        model        = model,
        n_layers     = unfreeze_layers,
        fine_tune_lr = fine_tune_lr
    )

    # ── Setup Generator ───────────────────────────────────
    from preprocessing.augmentation import get_flow_generators
    train_gen, val_gen, _, _ = get_flow_generators(batch_size=batch_size)

    steps_per_epoch  = max(1, train_gen.samples // batch_size)
    validation_steps = max(1, val_gen.samples   // batch_size) if val_gen else None

    # ── Setup Callbacks ───────────────────────────────────
    from training.hyperparameter import get_callbacks
    callbacks = get_callbacks(
        checkpoint_dir  = CHECKPOINT_DIR,
        log_csv_path    = TRAINING_CSV,
        tensorboard_dir = TENSORBOARD
    )

    # ── Fine-Tuning ───────────────────────────────────────
    model.fit(
        train_gen,
        steps_per_epoch  = steps_per_epoch,
        validation_data  = val_gen,
        validation_steps = validation_steps,
        epochs           = initial_epoch + epochs,
        initial_epoch    = initial_epoch,
        callbacks        = callbacks,
        verbose          = 1
    )

    # Simpan model fine-tuned
    fine_tuned_path = os.path.join(MODELS_DIR, "mobilenet_model.h5")
    model.save(fine_tuned_path)
    logger.info(f"✅ Fine-tuned model disimpan: {fine_tuned_path}")


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    run_fine_tuning(epochs=20)
