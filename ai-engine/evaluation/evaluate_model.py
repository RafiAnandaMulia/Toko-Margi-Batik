"""
=============================================================
 evaluation/evaluate_model.py
 Mengevaluasi model pada data test dan menyimpan laporan.
=============================================================
"""

import os
import sys
import json
import logging
import numpy as np
import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EVAL] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import MODELS_DIR, LABELS_FILE, TEST_DIR, BATCH_SIZE, IMG_SIZE, TRAINING_LOGS
from evaluation.utils import load_model_safe


def evaluate_model(
    model_path: str = None,
    batch_size: int = BATCH_SIZE
) -> dict:
    """
    Evaluasi model pada data test.

    Returns:
        dict: Hasil evaluasi (loss, accuracy, top3)
    """
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    model_path = model_path or os.path.join(MODELS_DIR, "best_model.h5")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

    logger.info(f"📥 Loading model: {os.path.basename(model_path)}")
    model = load_model_safe(model_path)  # ← ganti dari load_model biasa
    model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

    test_datagen = ImageDataGenerator(rescale=1.0/255.0)
    test_gen = test_datagen.flow_from_directory(
        TEST_DIR,
        target_size = IMG_SIZE,
        batch_size  = batch_size,
        class_mode  = "categorical",
        shuffle     = False
    )

    if test_gen.samples == 0:
        raise ValueError(f"Folder test kosong: {TEST_DIR}")

    logger.info(f"   Test samples: {test_gen.samples}")
    logger.info("🔍 Mengevaluasi model...")

    results       = model.evaluate(test_gen, verbose=1)
    metrics_names = model.metrics_names

    eval_result = {name: float(val) for name, val in zip(metrics_names, results)}
    eval_result["timestamp"] = datetime.datetime.now().isoformat()
    eval_result["model"]     = os.path.basename(model_path)

    logger.info("✅ Evaluasi selesai:")
    for name, val in eval_result.items():
        if isinstance(val, float):
            logger.info(f"   {name}: {val:.4f}")

    os.makedirs(TRAINING_LOGS, exist_ok=True)
    out_path = os.path.join(TRAINING_LOGS, "evaluation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(eval_result, f, indent=2)
    logger.info(f"✅ Hasil disimpan: {out_path}")

    return eval_result


if __name__ == "__main__":
    results = evaluate_model()
    print(f"\n📊 Test Accuracy: {results.get('accuracy', 0)*100:.2f}%")