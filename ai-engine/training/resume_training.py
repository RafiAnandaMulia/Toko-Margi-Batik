"""
=============================================================
 training/resume_training.py
 Melanjutkan proses pelatihan dari checkpoint terakhir
 yang tersimpan secara otomatis.

 Cara kerja:
 1. Scan folder checkpoints/ untuk file .weights.h5 terbaru
 2. Baca CSV log untuk menentukan epoch terakhir yang sukses
 3. Load model dengan arsitektur yang sama
 4. Load weights dari checkpoint terakhir
 5. Lanjutkan training dari epoch berikutnya
=============================================================
"""

import os
import sys
import re
import csv
import json
import glob
import logging
import datetime

# ─── Setup Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RESUME] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── Tambahkan path root ──────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    CHECKPOINT_DIR, TRAINING_CSV, TRAINING_LOGS,
    EPOCHS, BATCH_SIZE, LEARNING_RATE, FINE_TUNE_LR,
    DROPOUT_RATE, L2_LAMBDA, LABELS_FILE,
    TRAIN_DIR, VAL_DIR, MODELS_DIR
)


def find_latest_checkpoint() -> tuple:
    """
    Mencari checkpoint terakhir di folder checkpoints/.

    Format nama file: epoch_XXX_val_acc_YYYY.weights.h5
    Contoh: epoch_015_val_acc_0.8342.weights.h5

    Returns:
        tuple: (checkpoint_path, epoch_number)
               atau (None, 0) jika tidak ada checkpoint
    """
    # Pola file checkpoint
    pattern = os.path.join(CHECKPOINT_DIR, "epoch_*.weights.h5")
    checkpoints = glob.glob(pattern)

    if not checkpoints:
        logger.warning(f"Tidak ada checkpoint di: {CHECKPOINT_DIR}")
        return None, 0

    # Ekstrak nomor epoch dari nama file untuk pengurutan
    def extract_epoch(filepath: str) -> int:
        """Ekstrak nomor epoch dari nama file checkpoint"""
        basename = os.path.basename(filepath)
        # Cari pola epoch_XXX di nama file
        match = re.search(r"epoch_(\d+)", basename)
        return int(match.group(1)) if match else 0

    # Urutkan berdasarkan nomor epoch (terbesar = terbaru)
    checkpoints_sorted = sorted(checkpoints, key=extract_epoch, reverse=True)
    latest_checkpoint  = checkpoints_sorted[0]
    epoch_number       = extract_epoch(latest_checkpoint)

    logger.info(f"✅ Checkpoint terbaru: {os.path.basename(latest_checkpoint)}")
    logger.info(f"   Epoch checkpoint  : {epoch_number}")

    return latest_checkpoint, epoch_number


def get_last_epoch_from_csv() -> tuple:
    """
    Membaca file CSV log training untuk mendapatkan epoch terakhir
    yang berhasil diselesaikan beserta metricsnya.

    Returns:
        tuple: (last_epoch, last_metrics_dict)
    """
    if not os.path.exists(TRAINING_CSV):
        logger.warning(f"CSV log tidak ditemukan: {TRAINING_CSV}")
        return 0, {}

    last_epoch   = 0
    last_metrics = {}

    try:
        with open(TRAINING_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows   = list(reader)

        if not rows:
            logger.warning("CSV log kosong")
            return 0, {}

        # Baris terakhir = epoch terakhir yang selesai
        last_row = rows[-1]

        # Epoch di CSV dimulai dari 0, tambah 1 untuk mendapat epoch berikutnya
        last_epoch = int(float(last_row.get("epoch", 0))) + 1

        # Ambil semua metrics dari baris terakhir
        last_metrics = {
            "epoch"        : last_epoch,
            "loss"         : float(last_row.get("loss",         0)),
            "accuracy"     : float(last_row.get("accuracy",     0)),
            "val_loss"     : float(last_row.get("val_loss",     0)),
            "val_accuracy" : float(last_row.get("val_accuracy", 0)),
        }

        logger.info(f"✅ Epoch terakhir dari CSV: {last_epoch}")
        logger.info(f"   Accuracy    : {last_metrics['accuracy']*100:.2f}%")
        logger.info(f"   Val Accuracy: {last_metrics['val_accuracy']*100:.2f}%")

    except Exception as e:
        logger.error(f"Error membaca CSV: {e}")
        return 0, {}

    return last_epoch, last_metrics


def resume_training(
    target_epochs:  int   = None,
    batch_size:     int   = BATCH_SIZE,
    learning_rate:  float = LEARNING_RATE
) -> None:
    """
    Melanjutkan proses training dari checkpoint terakhir.

    Langkah:
    1. Cari checkpoint terbaru di folder checkpoints/
    2. Baca epoch terakhir dari CSV log
    3. Bangun ulang arsitektur model
    4. Load weights dari checkpoint
    5. Lanjutkan fit() dari epoch berikutnya

    Args:
        target_epochs : Total epoch yang diinginkan (default = EPOCHS dari config)
        batch_size    : Ukuran batch
        learning_rate : Learning rate untuk melanjutkan training
    """
    import tensorflow as tf

    # Gunakan total epoch dari config jika tidak diberikan
    target_epochs = target_epochs or EPOCHS

    logger.info("=" * 60)
    logger.info("🔄 MELANJUTKAN TRAINING DARI CHECKPOINT")
    logger.info("=" * 60)

    # ── Cari Checkpoint Terbaru ───────────────────────────
    checkpoint_path, ckpt_epoch = find_latest_checkpoint()

    # ── Cari Epoch Terakhir dari CSV ──────────────────────
    csv_epoch, last_metrics = get_last_epoch_from_csv()

    # Gunakan nilai terbesar antara checkpoint dan CSV
    # (checkpoint lebih reliabel karena disimpan pada saat epoch selesai)
    start_epoch = max(ckpt_epoch, csv_epoch)

    if checkpoint_path is None and start_epoch == 0:
        logger.warning("⚠️  Tidak ada checkpoint atau CSV log yang ditemukan.")
        logger.info("   Memulai training dari awal...")
        # Import dan jalankan training baru
        from training.train_model import EpochStatusCallback, update_status
        train_model(epochs_phase1=target_epochs, batch_size=batch_size)
        return

    logger.info(f"   Melanjutkan dari epoch : {start_epoch}")
    logger.info(f"   Target epoch           : {target_epochs}")
    logger.info(f"   Epoch tersisa          : {target_epochs - start_epoch}")

    # Periksa apakah sudah mencapai target
    if start_epoch >= target_epochs:
        logger.info(f"✅ Training sudah selesai! (epoch {start_epoch}/{target_epochs})")
        return

    # ── Load Nama Kelas ──────────────────────────────────
    if not os.path.exists(LABELS_FILE):
        raise FileNotFoundError(
            f"labels.txt tidak ditemukan: {LABELS_FILE}\n"
            "Pastikan split_dataset.py sudah dijalankan."
        )
    with open(LABELS_FILE, "r", encoding="utf-8") as f:
        class_names = [line.strip() for line in f if line.strip()]
    num_classes = len(class_names)
    logger.info(f"✅ {num_classes} kelas ditemukan")

    # ── Bangun Ulang Model ────────────────────────────────
    logger.info("🏗️  Membangun ulang arsitektur model...")
    from training.transfer_learning import build_mobilenetv2_model
    model = build_mobilenetv2_model(
        num_classes   = num_classes,
        dropout_rate  = DROPOUT_RATE,
        l2_lambda     = L2_LAMBDA,
        learning_rate = learning_rate,
        freeze_base   = True
    )

    # ── Load Weights dari Checkpoint ─────────────────────
    if checkpoint_path:
        logger.info(f"📥 Loading weights: {os.path.basename(checkpoint_path)}")
        try:
            model.load_weights(checkpoint_path)
            logger.info("✅ Weights berhasil dimuat!")
        except Exception as e:
            logger.error(f"❌ Gagal load weights: {e}")
            logger.info("   Mencoba model lengkap (best_model.h5)...")

            # Coba load model lengkap sebagai fallback
            best_model_path = os.path.join(MODELS_DIR, "best_model.h5")
            if os.path.exists(best_model_path):
                model = tf.keras.models.load_model(best_model_path)
                logger.info("✅ Model best_model.h5 berhasil dimuat!")
            else:
                raise RuntimeError("Tidak ada checkpoint yang valid untuk dilanjutkan.")

    # ── Setup Data Generators ─────────────────────────────
    from preprocessing.augmentation import get_flow_generators
    train_gen, val_gen, _, _ = get_flow_generators(batch_size=batch_size)

    steps_per_epoch  = max(1, train_gen.samples // batch_size)
    validation_steps = max(1, val_gen.samples   // batch_size) if val_gen else None

    # ── Setup Callbacks ───────────────────────────────────
    from training.hyperparameter import get_callbacks
    from training.train_model import EpochStatusCallback, update_status

    callbacks = get_callbacks(
        checkpoint_dir  = CHECKPOINT_DIR,
        log_csv_path    = TRAINING_CSV,      # Append ke CSV yang sama
        tensorboard_dir = None               # TensorBoard opsional saat resume
    )

    # Status callback
    status_cb = EpochStatusCallback(total_epochs=target_epochs)
    keras_status_cb = tf.keras.callbacks.LambdaCallback(
        on_epoch_end = lambda ep, logs: status_cb.on_epoch_end(ep, logs),
        on_train_end = lambda logs: status_cb.on_train_end(logs)
    )
    callbacks.append(keras_status_cb)

    # ── Update Status ─────────────────────────────────────
    update_status(
        status        = "running",
        current_epoch = start_epoch,
        total_epochs  = target_epochs,
        message       = f"Resume dari epoch {start_epoch}, target {target_epochs}"
    )

    # ── Catat Resume di Log ───────────────────────────────
    resume_log = {
        "resume_time"     : datetime.datetime.now().isoformat(),
        "from_epoch"      : start_epoch,
        "target_epochs"   : target_epochs,
        "checkpoint_used" : os.path.basename(checkpoint_path) if checkpoint_path else "none",
        "last_metrics"    : last_metrics
    }
    resume_log_path = os.path.join(TRAINING_LOGS, "resume_history.json")
    # Baca riwayat resume sebelumnya jika ada
    existing_logs = []
    if os.path.exists(resume_log_path):
        with open(resume_log_path, "r") as f:
            try:
                existing_logs = json.load(f)
            except Exception:
                existing_logs = []
    existing_logs.append(resume_log)
    with open(resume_log_path, "w", encoding="utf-8") as f:
        json.dump(existing_logs, f, indent=2, ensure_ascii=False)
    logger.info(f"📝 Resume log: {resume_log_path}")

    # ════════════════════════════════════════════════════════
    # LANJUTKAN TRAINING
    # ════════════════════════════════════════════════════════
    logger.info("\n" + "=" * 60)
    logger.info(f"▶️  MELANJUTKAN DARI EPOCH {start_epoch + 1} → {target_epochs}")
    logger.info("=" * 60)

    history = model.fit(
        train_gen,
        steps_per_epoch  = steps_per_epoch,
        validation_data  = val_gen,
        validation_steps = validation_steps,
        epochs           = target_epochs,     # Total epoch akhir
        initial_epoch    = start_epoch,       # Mulai dari epoch ini
        callbacks        = callbacks,
        verbose          = 1
    )

    # Simpan model final setelah resume
    final_path = os.path.join(MODELS_DIR, "mobilenet_model.h5")
    model.save(final_path)

    update_status(
        status        = "completed",
        current_epoch = target_epochs,
        total_epochs  = target_epochs,
        message       = "Resume training berhasil diselesaikan!"
    )

    logger.info("=" * 60)
    logger.info(f"✅ RESUME TRAINING SELESAI!")
    logger.info(f"   Model disimpan: {final_path}")
    logger.info("=" * 60)


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    """
    Jalankan: python resume_training.py
    Atau dengan target epoch khusus: python resume_training.py 100
    """
    import sys
    target = int(sys.argv[1]) if len(sys.argv) > 1 else EPOCHS
    resume_training(target_epochs=target)
