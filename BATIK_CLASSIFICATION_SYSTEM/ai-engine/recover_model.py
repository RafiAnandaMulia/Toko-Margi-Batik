import tensorflow as tf
from training.transfer_learning import build_mobilenetv2_model

print("Membangun arsitektur model...")

model = build_mobilenetv2_model(
    num_classes=17,
    freeze_base=True
)

print("Memuat weights...")

model.load_weights(
    r"models\checkpoints\epoch_049_val_acc_0.9266.weights.h5"
)

print("Menyimpan model baru...")

model.save("models/recovered_model.keras")

print("SELESAI!")