import os
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================

# PATH

# =====================================================

history_path = os.path.join(
"logs",
"training_logs",
"training_history.csv"
)

output_dir = os.path.join(
"logs",
"training_logs"
)

os.makedirs(output_dir, exist_ok=True)

# =====================================================

# LOAD CSV

# =====================================================

if not os.path.exists(history_path):
    raise FileNotFoundError(
    f"File tidak ditemukan: {os.path.abspath(history_path)}"
    )
history = pd.read_csv(history_path)


epochs = history["epoch"]

final_acc = history["accuracy"].iloc[-1] * 100
final_val_acc = history["val_accuracy"].iloc[-1] * 100

final_loss = history["loss"].iloc[-1]
final_val_loss = history["val_loss"].iloc[-1]

final_top3 = history["top_3_accuracy"].iloc[-1] * 100
final_val_top3 = history["val_top_3_accuracy"].iloc[-1] * 100

best_epoch = int(history["val_accuracy"].idxmax())
best_val_acc = history["val_accuracy"].max() * 100

# =====================================================

# 1. TRAINING ACCURACY

# =====================================================

plt.figure(figsize=(10, 5))

plt.plot(
epochs,
history["accuracy"],
label="Train Accuracy"
)

plt.plot(
epochs,
history["val_accuracy"],
label="Validation Accuracy"
)

plt.title(
f"Training Accuracy | "
f"Final Val={final_val_acc:.2f}% | "
f"Best={best_val_acc:.2f}% (Epoch {best_epoch})"
)

plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.legend()
plt.grid(True)

plt.savefig(
os.path.join(output_dir, "training_accuracy.png"),
dpi=300,
bbox_inches="tight"
)

plt.close()

# =====================================================

# 2. TRAINING LOSS

# =====================================================

plt.figure(figsize=(10, 5))

plt.plot(
epochs,
history["loss"],
label="Train Loss"
)

plt.plot(
epochs,
history["val_loss"],
label="Validation Loss"
)

plt.title(
f"Training Loss | "
f"Train={final_loss:.4f} | "
f"Val={final_val_loss:.4f}"
)

plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend()
plt.grid(True)

plt.savefig(
os.path.join(output_dir, "training_loss.png"),
dpi=300,
bbox_inches="tight"
)

plt.close()

# =====================================================

# 3. TOP-3 ACCURACY

# =====================================================

plt.figure(figsize=(10, 5))

plt.plot(
epochs,
history["top_3_accuracy"],
label="Train Top-3"
)

plt.plot(
epochs,
history["val_top_3_accuracy"],
label="Validation Top-3"
)

plt.title(
f"Top-3 Accuracy | "
f"Train={final_top3:.2f}% | "
f"Val={final_val_top3:.2f}%"
)

plt.xlabel("Epoch")
plt.ylabel("Top-3 Accuracy")
plt.legend()
plt.grid(True)

plt.savefig(
os.path.join(output_dir, "training_top3_accuracy.png"),
dpi=300,
bbox_inches="tight"
)

plt.close()

# =====================================================

# 4. ACCURACY VS TOP-3

# =====================================================

plt.figure(figsize=(10, 5))

plt.plot(
epochs,
history["accuracy"],
label="Accuracy"
)

plt.plot(
epochs,
history["top_3_accuracy"],
label="Top-3 Accuracy"
)

plt.title(
"Accuracy vs Top-3 Accuracy"
)

plt.xlabel("Epoch")
plt.ylabel("Score")
plt.legend()
plt.grid(True)

plt.savefig(
os.path.join(output_dir, "training_combined.png"),
dpi=300,
bbox_inches="tight"
)

plt.close()

# =====================================================

# OUTPUT

# =====================================================

print("✅ training_accuracy.png berhasil dibuat")
print("✅ training_loss.png berhasil dibuat")
print("✅ training_top3_accuracy.png berhasil dibuat")
print("✅ training_combined.png berhasil dibuat")

print("\n===== RINGKASAN TRAINING =====")
print(f"Final Accuracy       : {final_acc:.2f}%")
print(f"Final Val Accuracy   : {final_val_acc:.2f}%")
print(f"Best Val Accuracy    : {best_val_acc:.2f}%")
print(f"Best Epoch           : {best_epoch}")
print(f"Final Loss           : {final_loss:.4f}")
print(f"Final Val Loss       : {final_val_loss:.4f}")
print(f"Final Top-3 Accuracy : {final_top3:.2f}%")
print(f"Final Val Top-3 Acc  : {final_val_top3:.2f}%")
