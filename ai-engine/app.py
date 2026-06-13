"""
=============================================================
 ai-engine/app.py
 Script pipeline lengkap: preprocessing → training → evaluasi
 Jalankan satu per satu atau sekaligus.
=============================================================
"""

import os
import sys
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [APP] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Tambahkan root directory ke path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    RAW_DIR, EPOCHS, BATCH_SIZE, LEARNING_RATE,
    FINE_TUNE_LR, LABELS_FILE
)


def run_preprocessing(zip_path: str = None):
    """Menjalankan pipeline preprocessing lengkap"""
    logger.info("=" * 60)
    logger.info("🔄 MEMULAI PREPROCESSING")
    logger.info("=" * 60)

    from preprocessing.dataset_cleaning import extract_and_clean_zip
    from preprocessing.resize            import resize_dataset
    from preprocessing.normalization     import normalize_dataset
    from preprocessing.split_dataset     import split_dataset

    logger.info("[1/4] Membersihkan dan mengekstrak dataset...")
    extract_and_clean_zip(zip_path=zip_path)

    logger.info("[2/4] Resize gambar ke 224x224...")
    resize_dataset()

    logger.info("[3/4] Normalisasi piksel (÷255)...")
    normalize_dataset()

    logger.info("[4/4] Split dataset 70/20/10...")
    result = split_dataset()

    logger.info("✅ Preprocessing selesai!")
    logger.info(f"   {result['_summary']['total_images']} gambar | "
                f"{result['_summary']['n_classes']} kelas")


def run_training(epochs_p1: int = EPOCHS, epochs_p2: int = 20,
                 batch_size: int = BATCH_SIZE):
    """Menjalankan training model"""
    from training.train_model import train_model
    train_model(
        epochs_phase1 = epochs_p1,
        epochs_phase2 = epochs_p2,
        batch_size    = batch_size,
        learning_rate = LEARNING_RATE,
        fine_tune_lr  = FINE_TUNE_LR
    )


def run_evaluation():
    """Mengevaluasi model pada test set"""
    from evaluation.evaluate_model          import evaluate_model
    from evaluation.confusion_matrix        import generate_confusion_matrix
    from evaluation.classification_report   import generate_classification_report

    logger.info("📊 Evaluasi model...")
    results = evaluate_model()
    generate_confusion_matrix()
    generate_classification_report()
    logger.info(f"✅ Test Accuracy: {results.get('accuracy', 0)*100:.2f}%")
    return results


def run_resume(target_epochs: int = None):
    """Resume training dari checkpoint"""
    from training.resume_training import resume_training
    resume_training(target_epochs=target_epochs)


# ─── Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Margi Batik AI Pipeline")
    parser.add_argument(
        "command",
        choices=["preprocess", "train", "evaluate", "resume", "all"],
        help="Perintah yang dijalankan"
    )
    parser.add_argument("--zip",     type=str, help="Path ke file zip dataset")
    parser.add_argument("--epochs",  type=int, default=EPOCHS)
    parser.add_argument("--epochs2", type=int, default=20)
    parser.add_argument("--batch",   type=int, default=BATCH_SIZE)

    args = parser.parse_args()

    if args.command == "preprocess":
        run_preprocessing(zip_path=args.zip)
    elif args.command == "train":
        run_training(args.epochs, args.epochs2, args.batch)
    elif args.command == "evaluate":
        run_evaluation()
    elif args.command == "resume":
        run_resume(target_epochs=args.epochs)
    elif args.command == "all":
        run_preprocessing(zip_path=args.zip)
        run_training(args.epochs, args.epochs2, args.batch)
        run_evaluation()
