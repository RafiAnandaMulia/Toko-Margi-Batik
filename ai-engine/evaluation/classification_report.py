"""
=============================================================
 evaluation/confusion_matrix.py
 Membuat dan menyimpan confusion matrix evaluasi model
 sebagai gambar PNG + JSON + ringkasan teks.
=============================================================
"""

import os
import sys
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CONFMAT] %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import MODELS_DIR, LABELS_FILE, TEST_DIR, BATCH_SIZE, IMG_SIZE, TRAINING_LOGS
from evaluation.utils import load_model_safe


def generate_confusion_matrix(model_path: str = None, batch_size: int = BATCH_SIZE) -> dict:
    """
    Membuat confusion matrix dari prediksi model pada data test.
    Output: gambar PNG + JSON + ringkasan teks.

    Returns:
        dict: Confusion matrix beserta label kelas
    """
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from sklearn.metrics import confusion_matrix as sk_confusion_matrix

    model_path = model_path or os.path.join(MODELS_DIR, "best_model.h5")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

    model    = load_model_safe(model_path)
    datagen  = ImageDataGenerator(rescale=1./255.)
    test_gen = datagen.flow_from_directory(
        TEST_DIR, target_size=IMG_SIZE, batch_size=batch_size,
        class_mode="categorical", shuffle=False
    )

    # Prediksi semua data test
    predictions = model.predict(test_gen, verbose=1)
    y_pred      = np.argmax(predictions, axis=1)
    y_true      = test_gen.classes
    class_names = list(test_gen.class_indices.keys())

    # Buat confusion matrix
    cm            = sk_confusion_matrix(y_true, y_pred)
    total_samples = len(y_true)
    total_benar   = int(np.trace(cm))  # diagonal = prediksi benar
    accuracy      = total_benar / total_samples * 100

    os.makedirs(TRAINING_LOGS, exist_ok=True)

    # ── 1. Simpan PNG ─────────────────────────────────────────
    num_classes = len(class_names)
    fig_size    = max(10, num_classes * 1.2)

    fig, ax = plt.subplots(figsize=(fig_size, fig_size))
    sns.heatmap(
        cm,
        annot       = True,
        fmt         = "d",
        cmap        = "Blues",
        xticklabels = class_names,
        yticklabels = class_names,
        linewidths  = 0.5,
        ax          = ax
    )
    ax.set_title("Confusion Matrix", fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Predicted Label", fontsize=12, labelpad=10)
    ax.set_ylabel("True Label", fontsize=12, labelpad=10)
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    plt.tight_layout()

    png_path = os.path.join(TRAINING_LOGS, "confusion_matrix.png")
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"✅ PNG disimpan: {png_path}")

    # ── 2. Hitung metrik per kelas ────────────────────────────
    per_kelas = []
    for i, nama in enumerate(class_names):
        tp = int(cm[i, i])
        fp = int(cm[:, i].sum() - tp)   # kolom i dikurangi diagonal
        fn = int(cm[i, :].sum() - tp)   # baris i dikurangi diagonal
        tn = int(total_samples - tp - fp - fn)

        precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)

        per_kelas.append({
            "kelas"    : nama,
            "TP"       : tp,
            "FP"       : fp,
            "FN"       : fn,
            "TN"       : tn,
            "precision": round(precision, 2),
            "recall"   : round(recall, 2),
            "f1_score" : round(f1, 2),
        })

    # ── 3. Simpan JSON ────────────────────────────────────────
    result = {
        "accuracy"        : round(accuracy, 2),
        "total_benar"     : total_benar,
        "total_samples"   : total_samples,
        "confusion_matrix": cm.tolist(),
        "class_names"     : class_names,
        "per_kelas"       : per_kelas,
    }
    json_path = os.path.join(TRAINING_LOGS, "confusion_matrix.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ JSON disimpan: {json_path}")

    # ── 4. Simpan ringkasan teks ──────────────────────────────
    txt_lines = [
        "=" * 60,
        "         LAPORAN CONFUSION MATRIX - BATIK CLASSIFICATION",
        "=" * 60,
        f"  Model          : {os.path.basename(model_path)}",
        f"  Total Sampel   : {total_samples}",
        f"  Total Benar    : {total_benar}",
        f"  Accuracy       : {accuracy:.2f}%",
        "",
        "  Rumus yang digunakan:",
        "    Accuracy  = TP_semua / Total Sampel",
        "    Precision = TP / (TP + FP)",
        "    Recall    = TP / (TP + FN)",
        "    F1-Score  = 2 * (Precision * Recall) / (Precision + Recall)",
        "",
        "  Keterangan:",
        "    TP (True Positive)  = Prediksi benar untuk kelas ini",
        "    FP (False Positive) = Kelas lain salah diprediksi sebagai kelas ini",
        "    FN (False Negative) = Kelas ini salah diprediksi sebagai kelas lain",
        "    TN (True Negative)  = Bukan kelas ini dan diprediksi bukan kelas ini",
        "",
        "-" * 60,
        f"  {'Kelas':<25} {'TP':>5} {'FP':>5} {'FN':>5} {'TN':>6} {'Prec%':>7} {'Rec%':>7} {'F1%':>7}",
        "-" * 60,
    ]

    for k in per_kelas:
        txt_lines.append(
            f"  {k['kelas']:<25} {k['TP']:>5} {k['FP']:>5} {k['FN']:>5} "
            f"{k['TN']:>6} {k['precision']:>7.2f} {k['recall']:>7.2f} {k['f1_score']:>7.2f}"
        )
    # ==========================================================
# PERHITUNGAN DETAIL SETIAP KELAS
# ==========================================================

    txt_lines.extend([
    "",
    "=" * 70,
    "PERHITUNGAN DETAIL SETIAP KELAS",
    "=" * 70,
    ])

    for k in per_kelas:

      tp = k["TP"]
      fp = k["FP"]
      fn = k["FN"]
      tn = k["TN"]

    accuracy_cls = ((tp + tn) / (tp + tn + fp + fn)) * 100

    precision_cls = k["precision"]
    recall_cls    = k["recall"]
    f1_cls        = k["f1_score"]

    txt_lines.extend([

        "",
        "=" * 70,
        f"KELAS : {k['kelas']}",
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
        "Accuracy = ----------",
        "         TP+TN+FP+FN",
        "",
        f"         {tp} + {tn}",
        f"       = ------------",
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
        "Precision = ------",
        "           TP + FP",
        "",
        f"           {tp}",
        f"         = ------",
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
        f"       = ------",
        f"          {tp}+{fn}",
        "",
        f"       = {recall_cls:.2f}%",
        "",

        "Perhitungan F1-Score",
        "",
        "            2 × (Precision × Recall)",
        "F1-Score = --------------------------",
        "             Precision + Recall",
        "",
        f"         = 2 × ({precision_cls:.2f} × {recall_cls:.2f})",
        f"           -----------------------------------",
        f"              ({precision_cls:.2f} + {recall_cls:.2f})",
        "",
        f"         = {f1_cls:.2f}%",
        ""
    ])

    txt_lines += [
        "-" * 60,
        "",
        "  File output:",
        f"    - {png_path}",
        f"    - {json_path}",
        "=" * 60,
    ]

    txt_content = "\n".join(txt_lines)
    txt_path    = os.path.join(TRAINING_LOGS, "classification_report_summary.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_content)

    logger.info(f"✅ Ringkasan teks disimpan: {txt_path}")
    print("\n" + txt_content)  # tampilkan juga di terminal

    return result


if __name__ == "__main__":
    generate_confusion_matrix()