"""
=============================================================
 training/train_model.py
 Skrip utama untuk melatih model MobileNetV2 klasifikasi
 citra batik Toko Margi Batik.

 Fitur:
   - Transfer Learning + Fine-Tuning MobileNetV2
   - Augmentasi: Rotasi, Skalasi, Translasi, Kecerahan
   - Checkpoint setiap epoch (mendukung resume)
   - Custom CSV Logger (dibaca PHP real-time)
   - Dropout (0.4) + L2 Regularization
   - TANPA Early Stopping
=============================================================
"""

import os
import sys
import json
import time
import logging
import datetime
import threading

# ─── Setup Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TRAIN] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── Tambahkan path root ──────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    TRAIN_DIR, VAL_DIR, TEST_DIR, LABELS_FILE,
    MODELS_DIR, CHECKPOINT_DIR, BEST_MODEL,
    TRAINING_CSV, TENSORBOARD, TRAINING_LOGS,
    EPOCHS, BATCH_SIZE, LEARNING_RATE, FINE_TUNE_LR,
    DROPOUT_RATE, L2_LAMBDA, UNFREEZE_LAYERS, LOGS_DIR
)


# ─── Status Training (dibaca oleh Flask API) ──────────────
STATUS_FILE = os.path.join(TRAINING_LOGS, "training_status.json")


def update_status(status: str, current_epoch: int = 0,
                  total_epochs: int = 0, metrics: dict = None,
                  message: str = "") -> None:
    """
    Update file status training yang dibaca oleh Flask API dan PHP.

    Args:
        status       : "idle" | "running" | "completed" | "error"
        current_epoch: Epoch yang sedang berjalan
        total_epochs : Total epoch yang direncanakan
        metrics      : Dict berisi loss, acc, val_loss, val_acc terakhir
        message      : Pesan tambahan
    """
    os.makedirs(TRAINING_LOGS, exist_ok=True)
    data = {
        "status"         : status,
        "current_epoch"  : current_epoch,
        "total_epochs"   : total_epochs,
        "percentage"     : round(current_epoch / total_epochs * 100, 1)
                           if total_epochs > 0 else 0,
        "metrics"        : metrics or {},
        "message"        : message,
        "timestamp"      : datetime.datetime.now().isoformat(),
        "phase"          : "transfer_learning"
    }
    # Tulis atomik (gunakan file temp lalu rename)
    tmp_path = STATUS_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, STATUS_FILE)   # Atomic replace, aman untuk multi-thread


class EpochStatusCallback:
    """
    Custom Keras Callback untuk update STATUS_FILE setiap akhir epoch.
    Memungkinkan Flask API mengambil progress training secara real-time.
    """

    def __init__(self, total_epochs: int, phase: str = "transfer_learning"):
        self.total_epochs = total_epochs
        self.phase        = phase

    def on_epoch_end(self, epoch: int, logs: dict = None) -> None:
        """Dipanggil setiap akhir epoch"""
        logs = logs or {}
        current_epoch = epoch + 1    # epoch mulai dari 0

        # Ambil dan bulatkan semua metrics
        metrics = {
            "loss"          : round(float(logs.get("loss",         0)), 5),
            "accuracy"      : round(float(logs.get("accuracy",     0)), 5),
            "val_loss"      : round(float(logs.get("val_loss",     0)), 5),
            "val_accuracy"  : round(float(logs.get("val_accuracy", 0)), 5),
            "top_3_accuracy": round(float(logs.get("top_3_accuracy", 0)), 5),
            "learning_rate" : round(float(logs.get("lr",           LEARNING_RATE)), 8),
        }

        # Hitung estimasi waktu tersisa
        message = (
            f"Epoch {current_epoch}/{self.total_epochs} | "
            f"Acc: {metrics['accuracy']*100:.2f}% | "
            f"Val_Acc: {metrics['val_accuracy']*100:.2f}%"
        )

        update_status(
            status        = "running",
            current_epoch = current_epoch,
            total_epochs  = self.total_epochs,
            metrics       = metrics,
            message       = message
        )
        logger.info(message)

    def on_train_end(self, logs: dict = None) -> None:
        """Dipanggil saat training selesai"""
        logs = logs or {}
        update_status(
            status        = "completed",
            current_epoch = self.total_epochs,
            total_epochs  = self.total_epochs,
            message       = "Training selesai dengan sukses!"
        )
        logger.info("✅ Training selesai!")


def load_class_names() -> list:
    """
    Membaca nama kelas dari labels.txt.
    Returns: List nama kelas yang diurutkan.
    """
    if not os.path.exists(LABELS_FILE):
        raise FileNotFoundError(
            f"File labels.txt tidak ditemukan: {LABELS_FILE}\n"
            "Jalankan split_dataset.py terlebih dahulu."
        )
    with open(LABELS_FILE, "r", encoding="utf-8") as f:
        classes = [line.strip() for line in f if line.strip()]
    logger.info(f"✅ Dimuat {len(classes)} kelas dari labels.txt")
    return classes


def train_model(
    epochs_phase1:   int   = EPOCHS,
    epochs_phase2:   int   = 20,
    batch_size:      int   = BATCH_SIZE,
    learning_rate:   float = LEARNING_RATE,
    fine_tune_lr:    float = FINE_TUNE_LR,
    start_from_epoch: int  = 0
) -> None:
    """
    Proses pelatihan lengkap dua fase:

    FASE 1 — Transfer Learning (base model frozen):
      - Hanya custom head yang dilatih
      - Epoch: epochs_phase1

    FASE 2 — Fine-Tuning (top N layers dibuka):
      - Layer terakhir base model + head dilatih bersama
      - LR lebih kecil untuk menghindari catastrophic forgetting
      - Epoch: epochs_phase2

    Args:
        epochs_phase1   : Epoch untuk fase Transfer Learning
        epochs_phase2   : Epoch tambahan untuk Fine-Tuning
        batch_size      : Ukuran batch
        learning_rate   : LR awal fase 1
        fine_tune_lr    : LR untuk fase 2
        start_from_epoch: Mulai dari epoch ke-n (untuk resume)
    """
    import tensorflow as tf

    # Mulai timer
    start_time = time.time()

    # ── Validasi Dataset ──────────────────────────────────
    if not os.path.exists(TRAIN_DIR) or not os.listdir(TRAIN_DIR):
        raise FileNotFoundError(
            f"Folder train kosong: {TRAIN_DIR}\n"
            "Jalankan split_dataset.py terlebih dahulu."
        )

    logger.info("=" * 60)
    logger.info("🚀 MEMULAI TRAINING BATIK CLASSIFICATION")
    logger.info(f"   TensorFlow: {tf.__version__}")
    logger.info(f"   GPU tersedia: {len(tf.config.list_physical_devices('GPU'))} GPU")
    logger.info("=" * 60)

    # ── Load Nama Kelas ──────────────────────────────────
    class_names = load_class_names()
    num_classes = len(class_names)

    # ── Setup Data Generators ─────────────────────────────
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from preprocessing.augmentation import get_flow_generators

    train_gen, val_gen, test_gen, detected_classes = get_flow_generators(
        batch_size = batch_size
    )

    # Gunakan nama kelas dari generator (lebih akurat)
    class_names = detected_classes
    num_classes = len(class_names)

    # Simpan labels.txt dengan urutan yang benar dari generator
    from training.transfer_learning import save_labels
    save_labels(class_names)

    # ── Hitung Steps ──────────────────────────────────────
    steps_per_epoch  = max(1, train_gen.samples // batch_size)
    validation_steps = max(1, val_gen.samples   // batch_size) if val_gen else None

    logger.info(f"   Train samples    : {train_gen.samples}")
    logger.info(f"   Val samples      : {val_gen.samples if val_gen else 0}")
    logger.info(f"   Steps per epoch  : {steps_per_epoch}")
    logger.info(f"   Num classes      : {num_classes}")
    logger.info(f"   Epochs (Fase 1)  : {epochs_phase1}")
    logger.info(f"   Epochs (Fase 2)  : {epochs_phase2}")

    # ── Bangun Model ──────────────────────────────────────
    from training.transfer_learning import build_mobilenetv2_model, unfreeze_top_layers
    from training.hyperparameter    import get_callbacks

    model = build_mobilenetv2_model(
        num_classes   = num_classes,
        dropout_rate  = DROPOUT_RATE,
        l2_lambda     = L2_LAMBDA,
        learning_rate = learning_rate,
        freeze_base   = True         # Fase 1: base model beku
    )

    # ── Setup Callbacks ───────────────────────────────────
    callbacks = get_callbacks(
        checkpoint_dir  = CHECKPOINT_DIR,
        log_csv_path    = TRAINING_CSV,
        tensorboard_dir = TENSORBOARD
    )

    # Tambahkan status callback (update JSON setiap epoch)
    total_epochs = epochs_phase1 + epochs_phase2
    status_cb    = EpochStatusCallback(total_epochs=total_epochs, phase="phase1")

    # Konversi status_cb ke Keras LambdaCallback
    import tensorflow as tf
    keras_status_cb = tf.keras.callbacks.LambdaCallback(
        on_epoch_end  = lambda epoch, logs: status_cb.on_epoch_end(epoch, logs),
        on_train_end  = lambda logs: status_cb.on_train_end(logs)
    )
    callbacks.append(keras_status_cb)

    # ── Simpan Hyperparameter ─────────────────────────────
    from training.hyperparameter import TrainingHyperparams
    hp = TrainingHyperparams(
        epochs_phase1 = epochs_phase1,
        epochs_phase2 = epochs_phase2,
        batch_size    = batch_size,
        learning_rate = learning_rate,
        fine_tune_lr  = fine_tune_lr
    )
    hp.save(os.path.join(LOGS_DIR, "hyperparameters.json"))
    hp.print_summary()

    # ── Update Status: Dimulai ────────────────────────────
    update_status(
        status       = "running",
        current_epoch = start_from_epoch,
        total_epochs  = total_epochs,
        message      = "Fase 1: Transfer Learning dimulai"
    )

    # ════════════════════════════════════════════════════════
    # FASE 1: TRANSFER LEARNING
    # Base model (MobileNetV2) FROZEN, hanya custom head dilatih
    # ════════════════════════════════════════════════════════
    logger.info("\n" + "=" * 60)
    logger.info("📚 FASE 1: TRANSFER LEARNING")
    logger.info("   Base model beku, melatih custom head")
    logger.info("=" * 60)

    history_phase1 = model.fit(
        train_gen,
        steps_per_epoch  = steps_per_epoch,
        validation_data  = val_gen,
        validation_steps = validation_steps,
        epochs           = epochs_phase1,
        initial_epoch    = start_from_epoch,   # Untuk resume
        callbacks        = callbacks,
        verbose          = 1                   # Tampilkan progress bar
    )

    # Simpan model setelah fase 1
    model_phase1_path = os.path.join(MODELS_DIR, "mobilenet_model.h5")
    model.save(model_phase1_path)
    logger.info(f"✅ Model Fase 1 disimpan: {model_phase1_path}")

    # ════════════════════════════════════════════════════════
    # FASE 2: FINE-TUNING
    # Buka top N layer MobileNetV2 untuk fine-tuning
    # ════════════════════════════════════════════════════════
    if epochs_phase2 > 0:
        logger.info("\n" + "=" * 60)
        logger.info("🔬 FASE 2: FINE-TUNING")
        logger.info(f"   Membuka {UNFREEZE_LAYERS} layer terakhir")
        logger.info(f"   LR: {fine_tune_lr} (lebih kecil dari fase 1)")
        logger.info("=" * 60)

        # Update status untuk fase 2
        update_status(
            status        = "running",
            current_epoch = epochs_phase1,
            total_epochs  = total_epochs,
            message       = f"Fase 2: Fine-Tuning dimulai (membuka {UNFREEZE_LAYERS} layers)"
        )

        # Ubah status callback ke fase 2
        keras_status_cb = tf.keras.callbacks.LambdaCallback(
            on_epoch_end = lambda epoch, logs: EpochStatusCallback(
                total_epochs=total_epochs, phase="fine_tuning"
            ).on_epoch_end(epochs_phase1 + epoch, logs)
        )

        # Update callbacks dengan fase 2 status
        callbacks_ft = get_callbacks(
            checkpoint_dir   = CHECKPOINT_DIR,
            log_csv_path     = TRAINING_CSV,     # Append ke CSV yang sama
            tensorboard_dir  = TENSORBOARD
        )
        callbacks_ft.append(keras_status_cb)

        # Buka layer untuk fine-tuning
        model = unfreeze_top_layers(
            model        = model,
            n_layers     = UNFREEZE_LAYERS,
            fine_tune_lr = fine_tune_lr
        )

        # Lanjutkan training (fine-tuning)
        history_phase2 = model.fit(
            train_gen,
            steps_per_epoch  = steps_per_epoch,
            validation_data  = val_gen,
            validation_steps = validation_steps,
            epochs           = epochs_phase1 + epochs_phase2,  # Total epoch
            initial_epoch    = epochs_phase1,                   # Lanjutkan dari fase 1
            callbacks        = callbacks_ft,
            verbose          = 1
        )

        # Simpan model final
        model.save(os.path.join(MODELS_DIR, "mobilenet_model.h5"))
        logger.info(f"✅ Model Final disimpan")

    # ── Evaluasi Akhir ────────────────────────────────────
    if test_gen:
        logger.info("\n📊 EVALUASI PADA DATA TEST:")
        test_loss, test_acc, test_top3 = model.evaluate(
            test_gen, verbose=1
        )
        logger.info(f"   Test Loss     : {test_loss:.4f}")
        logger.info(f"   Test Accuracy : {test_acc*100:.2f}%")
        logger.info(f"   Top-3 Accuracy: {test_top3*100:.2f}%")

        # Simpan hasil evaluasi test
        eval_results = {
            "test_loss"     : float(test_loss),
            "test_accuracy" : float(test_acc),
            "test_top3"     : float(test_top3),
            "timestamp"     : datetime.datetime.now().isoformat()
        }
        eval_path = os.path.join(TRAINING_LOGS, "test_evaluation.json")
        with open(eval_path, "w") as f:
            json.dump(eval_results, f, indent=2)

    # ── Selesai ───────────────────────────────────────────
    elapsed = time.time() - start_time
    hours   = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)

    update_status(
        status        = "completed",
        current_epoch = total_epochs,
        total_epochs  = total_epochs,
        message       = f"Training selesai dalam {hours}j {minutes}m {seconds}d"
    )

    logger.info("=" * 60)
    logger.info(f"🎉 TRAINING SELESAI!")
    logger.info(f"   Waktu total    : {hours}j {minutes}m {seconds}d")
    logger.info(f"   Model terbaik  : {BEST_MODEL}")
    logger.info("=" * 60)


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    """
    Jalankan: python train_model.py
    """
    train_model(
        epochs_phase1 = EPOCHS,
        epochs_phase2 = 20,
        batch_size    = BATCH_SIZE,
        learning_rate = LEARNING_RATE,
        fine_tune_lr  = FINE_TUNE_LR
    )
