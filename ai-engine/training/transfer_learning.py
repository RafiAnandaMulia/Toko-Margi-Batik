"""
=============================================================
 training/transfer_learning.py
 Mendefinisikan arsitektur model CNN berbasis MobileNetV2
 dengan Transfer Learning dari ImageNet.
 Fitur: Dropout (0.4) + L2 Regularization untuk mencegah
 overfitting pada epoch tinggi tanpa Early Stopping.
=============================================================
"""

import os
import sys
import logging

# ─── Setup Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MODEL] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ─── Tambahkan path root ──────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import IMG_SIZE, IMG_CHANNELS, DROPOUT_RATE, L2_LAMBDA


def build_mobilenetv2_model(
    num_classes:    int,
    img_size:       tuple  = IMG_SIZE,
    dropout_rate:   float  = DROPOUT_RATE,
    l2_lambda:      float  = L2_LAMBDA,
    learning_rate:  float  = 0.0001,
    freeze_base:    bool   = True
):
    """
    Membangun model MobileNetV2 dengan Transfer Learning.

    Arsitektur:
        MobileNetV2 (ImageNet, frozen) →
        GlobalAveragePooling2D →
        Dense(256, ReLU, L2) →
        BatchNormalization →
        Dropout(0.4) →
        Dense(num_classes, Softmax)

    Strategi Anti-Overfitting (tanpa Early Stopping):
    1. Data Augmentation kuat (didefinisikan di augmentation.py)
    2. Dropout(0.4) — menonaktifkan 40% neuron secara acak saat training
    3. L2 Regularization — menghukum bobot besar untuk generalisasi lebih baik
    4. BatchNormalization — menstabilkan distribusi aktivasi

    Args:
        num_classes  : Jumlah kelas batik
        img_size     : Ukuran input gambar (224, 224)
        dropout_rate : Tingkat dropout (default 0.4)
        l2_lambda    : Koefisien L2 (default 0.0001)
        learning_rate: Laju pembelajaran
        freeze_base  : True = semua layer base di-freeze saat fase pertama

    Returns:
        tf.keras.Model: Model yang sudah dikompilasi
    """
    import tensorflow as tf
    from tensorflow.keras import layers, regularizers, Model
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.optimizers import Adam

    logger.info(f"Membangun MobileNetV2 dengan {num_classes} kelas...")
    logger.info(f"   Input size  : {img_size} x {IMG_CHANNELS}")
    logger.info(f"   Dropout     : {dropout_rate}")
    logger.info(f"   L2 Lambda   : {l2_lambda}")
    logger.info(f"   Freeze Base : {freeze_base}")

    # ── Base Model: MobileNetV2 pretrained ImageNet ────────
    base_model = MobileNetV2(
        input_shape = (*img_size, IMG_CHANNELS),  # (224, 224, 3)
        include_top = False,                       # Tanpa classifier asli
        weights     = "imagenet"                   # Pre-trained ImageNet weights
    )

    # Freeze base model pada fase pertama (Transfer Learning)
    base_model.trainable = not freeze_base
    layer_status = "BEKU (frozen)" if freeze_base else "AKTIF (trainable)"
    logger.info(f"   Base Model  : {len(base_model.layers)} layers → {layer_status}")

    # ── Input Layer ───────────────────────────────────────
    inputs = layers.Input(shape=(*img_size, IMG_CHANNELS), name="input_layer")

    # ── Fitur MobileNetV2 ──────────────────────────────────
    # training=False agar BatchNorm di base model tetap pada mode inference
    x = base_model(inputs, training=False)

    # ── Global Average Pooling ────────────────────────────
    # Merata-ratakan feature maps (7,7,1280) → (1280,)
    # Lebih baik dari Flatten untuk mengurangi overfitting
    x = layers.GlobalAveragePooling2D(name="global_avg_pool")(x)

    # ── Dense Layer dengan L2 Regularization ──────────────
    # L2: menambah penalti untuk bobot besar, mendorong generalisasi
    x = layers.Dense(
        256,
        activation   = "relu",
        kernel_regularizer = regularizers.l2(l2_lambda),  # ← L2 Regularization
        name         = "dense_256"
    )(x)

    # ── Batch Normalization ────────────────────────────────
    # Menstabilkan distribusi aktivasi, mempercepat konvergensi
    x = layers.BatchNormalization(name="batch_norm")(x)

    # ── Dropout Layer ─────────────────────────────────────
    # Menonaktifkan 40% neuron secara acak saat training
    # → Mencegah model bergantung pada neuron tertentu (overfitting)
    x = layers.Dropout(dropout_rate, name="dropout_04")(x)

    # ── Output Layer ──────────────────────────────────────
    # Softmax untuk probabilitas multi-class
    outputs = layers.Dense(
        num_classes,
        activation = "softmax",     # Probabilitas tiap kelas (total=1.0)
        name       = "output_layer"
    )(x)

    # ── Buat Model ────────────────────────────────────────
    model = Model(inputs=inputs, outputs=outputs, name="BatikMobileNetV2")

    # ── Kompilasi Model ───────────────────────────────────
    model.compile(
        optimizer = Adam(learning_rate=learning_rate),  # Adaptive learning rate
        loss      = "categorical_crossentropy",          # Multi-class classification
        metrics   = [
            "accuracy",                                  # Akurasi klasifikasi
            tf.keras.metrics.TopKCategoricalAccuracy(
                k=3, name="top_3_accuracy"               # Top-3 accuracy
            )
        ]
    )

    # ── Ringkasan Model ───────────────────────────────────
    total_params     = model.count_params()
    trainable_params = sum(
        tf.size(w).numpy() for w in model.trainable_weights
    )
    frozen_params    = total_params - trainable_params

    logger.info(f"✅ Model berhasil dibangun:")
    logger.info(f"   Total parameter   : {total_params:,}")
    logger.info(f"   Trainable         : {trainable_params:,}")
    logger.info(f"   Frozen            : {frozen_params:,}")

    return model


def unfreeze_top_layers(model, n_layers: int = 30, fine_tune_lr: float = 1e-5):
    """
    Membuka (unfreeze) sejumlah layer terakhir dari base model
    untuk Fine-Tuning tahap kedua.

    Strategi Fine-Tuning:
    - Buka n_layers terakhir dari MobileNetV2 untuk fine-tuning
    - Gunakan learning rate yang jauh lebih kecil (1e-5)
    - Layer awal tetap beku (low-level features tidak perlu diubah)

    Args:
        model      : Model Keras yang sudah dilatih fase pertama
        n_layers   : Jumlah layer terakhir yang dibuka
        fine_tune_lr: Learning rate untuk fine-tuning

    Returns:
        Model yang sudah dikonfigurasi untuk fine-tuning
    """
    import tensorflow as tf
    from tensorflow.keras.optimizers import Adam

    # Temukan base model (MobileNetV2)
    base_model = None
    for layer in model.layers:
        if "mobilenet" in layer.name.lower():
            base_model = layer
            break

    if base_model is None:
        logger.error("Base model tidak ditemukan dalam model!")
        return model

    # Aktifkan seluruh base model dulu
    base_model.trainable = True

    # Freeze semua layer, kecuali n_layers terakhir
    total_layers = len(base_model.layers)
    freeze_until = total_layers - n_layers

    for i, layer in enumerate(base_model.layers):
        layer.trainable = i >= freeze_until  # Hanya layer akhir yang trainable

    # Re-kompilasi dengan learning rate lebih kecil
    model.compile(
        optimizer = Adam(learning_rate=fine_tune_lr),
        loss      = "categorical_crossentropy",
        metrics   = [
            "accuracy",
            tf.keras.metrics.TopKCategoricalAccuracy(k=3, name="top_3_accuracy")
        ]
    )

    trainable_now = sum(
        tf.size(w).numpy() for w in model.trainable_weights
    )
    logger.info(f"✅ Fine-Tuning: {n_layers} layer terakhir dibuka")
    logger.info(f"   Trainable sekarang : {trainable_now:,} parameter")
    logger.info(f"   Learning Rate FT   : {fine_tune_lr}")

    return model


def save_labels(class_names: list, labels_file: str = None) -> None:
    """
    Menyimpan daftar nama kelas ke file labels.txt.
    Digunakan saat prediksi untuk memetakan indeks → nama kelas.

    Args:
        class_names : List nama kelas sesuai urutan indeks model
        labels_file : Path file labels (default dari config)
    """
    from config import LABELS_FILE
    labels_file = labels_file or LABELS_FILE

    os.makedirs(os.path.dirname(labels_file), exist_ok=True)
    with open(labels_file, "w", encoding="utf-8") as f:
        for cls in class_names:
            f.write(cls + "\n")
    logger.info(f"✅ Labels disimpan: {labels_file} ({len(class_names)} kelas)")


# ─── Entry Point (Test) ───────────────────────────────────
if __name__ == "__main__":
    # Test bangun model dengan 21 kelas batik
    model = build_mobilenetv2_model(num_classes=21)
    model.summary()
    print("\n✅ Model berhasil dibangun dan dikompilasi.")
