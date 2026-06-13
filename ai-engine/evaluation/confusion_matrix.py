"""
=============================================================
 evaluation/confusion_matrix.py
 Membuat dan menyimpan confusion_matrix lengkap
 (Precision, Recall, F1-Score, Support)
=============================================================
"""

import os
import sys
import json
import logging
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [REPORT] %(message)s"
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (
    MODELS_DIR,
    TEST_DIR,
    BATCH_SIZE,
    IMG_SIZE,
    TRAINING_LOGS
)

from evaluation.utils import load_model_safe


def generate_confusion_matrix(
    model_path: str = None,
    batch_size: int = BATCH_SIZE
) -> dict:
    """
    Membuat confusion_matrixlengkap
    dan menyimpannya ke JSON + TXT + Summary.

    Returns:confusion_matrix
    """

    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    classification_report
    )

    model_path = model_path or os.path.join(
        MODELS_DIR,
        "best_model.h5"
    )

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model tidak ditemukan: {model_path}"
        )

    logger.info(f"Memuat model: {model_path}")

    model = load_model_safe(model_path)

    datagen = ImageDataGenerator(
        rescale=1.0 / 255.0
    )

    test_gen = datagen.flow_from_directory(
        TEST_DIR,
        target_size=IMG_SIZE,
        batch_size=batch_size,
        class_mode="categorical",
        shuffle=False
    )

    logger.info(
        f"Total data test: {test_gen.samples}"
    )

    # Prediksi
    predictions = model.predict(
        test_gen,
        verbose=1
    )

    y_pred = np.argmax(
        predictions,
        axis=1
    )

    y_true = test_gen.classes

    class_names = list(
        test_gen.class_indices.keys()
    )

    cm = confusion_matrix(y_true, y_pred)

    accuracy = accuracy_score(
        y_true,
        y_pred
        ) * 100
    report_dict = classification_report(
        y_true,
        y_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0
        )
    report_text = classification_report(
        y_true,
        y_pred,
        target_names=class_names,
        zero_division=0
        )

    os.makedirs(
            TRAINING_LOGS,
            exist_ok=True
        )

    # =====================================================
    # SIMPAN JSON
    # =====================================================
    json_path = os.path.join(
        TRAINING_LOGS,
        "confusion_matrix.json"
    )
    print("DEBUG REPORT_DICT:", type(report_dict))
    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            report_dict,
            f,
            indent=2,
            ensure_ascii=False
        )

    logger.info(
        f"✅ JSON disimpan: {json_path}"
    )

    # =====================================================
    # SIMPAN TXT ASLI
    # =====================================================
    txt_path = os.path.join(
        TRAINING_LOGS,
        "confusion_matrix.txt"
    )

    with open(
        txt_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(report_text)

    logger.info(
        f"✅ TXT disimpan: {txt_path}"
    )

    # =====================================================
    # SUMMARY UNTUK SKRIPSI
    # =====================================================
    summary_lines = [
         "=" * 70,
    "      LAPORAN confusion_matrix",
    "=" * 70,
    "",
    f"Model          : {os.path.basename(model_path)}",
    f"Total Sampel   : {len(y_true)}",
    f"Accuracy       : {accuracy:.2f}%",
    "",
    "Rumus yang digunakan:",
    "",
    "1. Rumus untuk menghitung nilai Accuracy:",
    "   Accuracy = (TP + TN) / (TP + TN + FP + FN)",
    "",
    "2. Rumus untuk menghitung nilai Precision:",
    "   Precision = TP / (TP + FP)",
    "",
    "3. Rumus untuk menghitung nilai Recall:",
    "   Recall = TP / (TP + FN)",
    "",
    "4. Rumus untuk menghitung nilai F1-Score:",
    "   F1-Score = 2 × (Precision × Recall) / (Precision + Recall)",
    "",
    "Keterangan:",
    "TP (True Positive)  = Jumlah data yang diprediksi benar sebagai kelas tersebut",
    "TN (True Negative)  = Jumlah data yang diprediksi benar bukan sebagai kelas tersebut",
    "FP (False Positive) = Jumlah data dari kelas lain yang salah diprediksi sebagai kelas tersebut",
    "FN (False Negative) = Jumlah data dari kelas tersebut yang salah diprediksi sebagai kelas lain",
    "",
    "-" * 70,
    f"{'Kelas':<25} {'Prec%':>8} {'Recall%':>8} {'F1%':>8} {'Support':>10}",
    "-" * 70
    ]
    cm = confusion_matrix(y_true, y_pred)

    for i, kelas in enumerate(class_names):
        tp = int(cm[i, i])
        fp = int(cm[:, i].sum() - tp)
        fn = int(cm[i, :].sum() - tp)
        tn = int(cm.sum() - tp - fp - fn)

        accuracy_cls = ((tp + tn) / (tp + tn + fp + fn)) * 100

        precision_cls = (
        tp / (tp + fp) * 100
        if (tp + fp) > 0 else 0
        )

        recall_cls = (
        tp / (tp + fn) * 100
        if (tp + fn) > 0 else 0
        )

        f1_cls = (
            2 * precision_cls * recall_cls /
            (precision_cls + recall_cls)
            if (precision_cls + recall_cls) > 0 else 0
        )

        summary_lines.extend([
        "",
        "=" * 70,
        f"KELAS : {kelas}",
        "=" * 70,
        "",

        f"TP = {tp}",
        f"FP = {fp}",
        f"FN = {fn}",
        f"TN = {tn}",
        "",

        "Perhitungan Accuracy",
        "",
        "            TP + TN",
        "Accuracy = ___________",
        "         TP+TN+FP+FN",
        "",
        f"         {tp} + {tn}",
        f"       = ___________________",
        f"         {tp}+{tn}+{fp}+{fn}",
        "",
        f"       = {tp+tn}",
        f"         {'-' * len(str(tp+tn+fp+fn))}",
        f"         {tp+tn+fp+fn}",
        "",
        f"       = {accuracy_cls:.2f}%",
        "",

        "Perhitungan Precision",
        "",
        "             TP",
        "Precision = _______",
        "           TP + FP",
        "",
        f"           {tp}",
        f"         = _________",
        f"           {tp}+{fp}",
        "",
        f"         = {precision_cls:.2f}%",
        "",

        "Perhitungan Recall",
        "",
        "           TP",
        "Recall = ------",
        "          TP+FN",
        "",
        f"          {tp}",
        f"       = __________",
        f"          {tp}+{fn}",
        "",
        f"       = {recall_cls:.2f}%",
        "",

        "Perhitungan F1-Score",
        "",
        "            2 × (Precision × Recall)",
        "F1-Score = ___________________________",
        "             Precision + Recall",
        "",

        f"Precision = {precision_cls/100:.4f}",
        f"Recall    = {recall_cls/100:.4f}",
        "",

        f"         = 2 × ({precision_cls/100:.4f} × {recall_cls/100:.4f})",
        f"           __________________________________________________",
        f"             {precision_cls/100:.4f} + {recall_cls/100:.4f}",
        "",

        f"         = 2 × {(precision_cls/100)*(recall_cls/100):.4f}",
        f"           ______________________________________________",
        f"             {(precision_cls/100)+(recall_cls/100):.4f}",
        "",

        f"         = {(2*(precision_cls/100)*(recall_cls/100))/((precision_cls/100)+(recall_cls/100)):.4f}",
        "",

        f"         = {f1_cls:.2f}%",
        ""
    ])
    
    summary_content = "\n".join(summary_lines)

    # =====================================================
    # SIMPAN SUMMARY TXT
    # =====================================================
    summary_path = os.path.join(
        TRAINING_LOGS,
        "confusion_matrix_summary.txt"
    )

    with open(
        summary_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(summary_content)

    logger.info(
        f"✅ Summary TXT disimpan: {summary_path}"
    )

    # =====================================================
    # SIMPAN SUMMARY JSON
    # =====================================================
    summary_json_path = os.path.join(
        TRAINING_LOGS,
        "confusion_matrix_summary.json"
    )

    json_result = {
        "accuracy": round(accuracy, 2),
        "class_names": class_names,
        "confusion_matrix": cm.tolist(),
        "classification_report": report_dict
    }

    with open(
        summary_json_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            json_result,
            f,
            indent=2,
            ensure_ascii=False
        )

    logger.info(
        f"✅ Summary JSON disimpan: {summary_json_path}"
    )
    print("\n")
    print(summary_content)
    return {
        "accuracy": round(
            accuracy,
            2
        ),
        "report": report_dict
    }
if __name__ == "__main__":
    generate_confusion_matrix()