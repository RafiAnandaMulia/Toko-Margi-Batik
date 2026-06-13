"""
=============================================================
 evaluation/utils.py
 Helper shared untuk semua script evaluasi.
=============================================================
"""

import os
import logging
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import MODELS_DIR, TEST_DIR, IMG_SIZE

logger = logging.getLogger(__name__)


def load_model_safe(model_path: str):
    """
    Load model .h5 dengan fix kompatibilitas Keras versi baru.
    Menangani error DepthwiseConv2D 'groups' parameter.
    """
    import tensorflow as tf
    import h5py

    class FixedDepthwiseConv2D(tf.keras.layers.DepthwiseConv2D):
        def __init__(self, *args, **kwargs):
            kwargs.pop("groups", None)
            super().__init__(*args, **kwargs)

    try:
        logger.info("Mencoba load model dengan custom_objects...")
        model = tf.keras.models.load_model(
            model_path,
            custom_objects={"DepthwiseConv2D": FixedDepthwiseConv2D}
        )
        logger.info("✅ Model berhasil di-load.")
        return model

    except Exception as e:
        logger.warning(f"Load gagal ({e}), mencoba rebuild architecture + load weights...")

        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(*IMG_SIZE, 3),
            include_top=False,
            weights=None
        )
        base_model.trainable = False

        inputs = tf.keras.Input(shape=(*IMG_SIZE, 3))
        x      = base_model(inputs, training=False)
        x      = tf.keras.layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
        x      = tf.keras.layers.Dense(256, activation="relu", name="dense_256")(x)
        x      = tf.keras.layers.BatchNormalization(name="batch_norm")(x)
        x      = tf.keras.layers.Dropout(0.4, name="dropout_04")(x)

        with h5py.File(model_path, "r") as f:
            try:
                w = f["model_weights"]["output_layer"]["output_layer"]["kernel:0"]
                num_classes = w.shape[1]
                logger.info(f"Jumlah kelas dari bobot: {num_classes}")
            except Exception:
                num_classes = len([
                    d for d in os.listdir(TEST_DIR)
                    if os.path.isdir(os.path.join(TEST_DIR, d))
                ])
                logger.info(f"Jumlah kelas dari TEST_DIR: {num_classes}")

        outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="output_layer")(x)
        model   = tf.keras.Model(inputs, outputs)
        model.load_weights(model_path, by_name=True, skip_mismatch=True)
        logger.info("✅ Model berhasil di-rebuild dan weights di-load.")
        return model