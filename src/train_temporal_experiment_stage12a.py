"""
Stage 12A - Cyclical Temporal Encoding Experiment

Question:
Does representing annual time cyclically improve validation
performance compared with Stage 11?

Stage 11 benchmark:
    Architecture: 16 -> 128 -> 64 -> 32 -> 1
    Validation AUC: 0.592277

Stage 12A:
    Replace month/day_of_year/season with:
        day_sin
        day_cos

IMPORTANT:
    - Same Stage 10 split
    - Same seed
    - Same optimiser
    - Same batch size
    - Same early stopping
    - Test set remains untouched
"""

from pathlib import Path
import copy
import json
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)


# ============================================================
# CONFIG
# ============================================================

DATA_FILE = Path(
    "data/final_paired_bushfire_dataset_stage10_split.csv"
)

OUTPUT_DIR = Path(
    "models/stage12a"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SEED = 42
MAX_EPOCHS = 300
PATIENCE = 30

LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-4
BATCH_SIZE = 256

STAGE11_BENCHMARK_AUC = 0.592277


BASE_FEATURES = [
    "max_temp",
    "min_temp",
    "avg_humidity",
    "max_wind",
    "rain_today",
    "rain_last_7_days",
    "rain_last_30_days",
    "days_since_rain",
    "temp_humidity_index",
    "temp_wind_index",
    "dryness_index",
    "vpd",
    "elevation",
]

FEATURES = (
    BASE_FEATURES
    + [
        "day_sin",
        "day_cos",
    ]
)

HIDDEN_SIZES = [
    128,
    64,
    32,
]


# ============================================================
# REPRODUCIBILITY
# ============================================================

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)


set_seed(SEED)


# ============================================================
# DEVICE
# ============================================================

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(DATA_FILE)

print("=" * 72)
print("STAGE 12A - CYCLICAL TEMPORAL ENCODING")
print("=" * 72)

print(f"Device: {DEVICE}")


# ============================================================
# CREATE CYCLICAL FEATURES
# ============================================================

# 366 denominator handles leap-year day 366
# consistently across the dataset.
angle = (
    2.0
    * np.pi
    * (df["day_of_year"] - 1)
    / 366.0
)

df["day_sin"] = np.sin(angle)
df["day_cos"] = np.cos(angle)


train_df = df[
    df["split"] == "train"
].copy()

val_df = df[
    df["split"] == "validation"
].copy()


print(
    f"Train rows      : {len(train_df):,}"
)

print(
    f"Validation rows : {len(val_df):,}"
)

print(
    "Test rows used  : 0 (LOCKED)"
)

print(
    f"Input features  : {len(FEATURES)}"
)

print(
    "Architecture    : "
    f"{len(FEATURES)} -> "
    "128 -> 64 -> 32 -> 1"
)


# ============================================================
# VALIDATE
# ============================================================

if train_df[FEATURES].isna().any().any():
    raise ValueError(
        "Training features contain null values."
    )

if val_df[FEATURES].isna().any().any():
    raise ValueError(
        "Validation features contain null values."
    )


# ============================================================
# TRAINING-ONLY SCALER
# ============================================================

train_x_raw = (
    train_df[FEATURES]
    .to_numpy(dtype=np.float32)
)

val_x_raw = (
    val_df[FEATURES]
    .to_numpy(dtype=np.float32)
)

mean = train_x_raw.mean(axis=0)
std = train_x_raw.std(axis=0)

std = np.where(
    std < 1e-8,
    1.0,
    std
)

train_x = (
    train_x_raw - mean
) / std

val_x = (
    val_x_raw - mean
) / std

train_y = (
    train_df["fire"]
    .to_numpy(dtype=np.float32)
)

val_y = (
    val_df["fire"]
    .to_numpy(dtype=np.float32)
)


# Save preprocessing contract.
np.save(
    OUTPUT_DIR / "scaler_mean.npy",
    mean
)

np.save(
    OUTPUT_DIR / "scaler_std.npy",
    std
)

with open(
    OUTPUT_DIR / "feature_names.json",
    "w"
) as file:
    json.dump(
        FEATURES,
        file,
        indent=2
    )


# ============================================================
# DATASETS
# ============================================================

train_dataset = (
    torch.utils.data.TensorDataset(
        torch.tensor(
            train_x,
            dtype=torch.float32
        ),
        torch.tensor(
            train_y,
            dtype=torch.float32
        ).unsqueeze(1)
    )
)

val_x_tensor = torch.tensor(
    val_x,
    dtype=torch.float32,
    device=DEVICE
)

val_y_tensor = torch.tensor(
    val_y,
    dtype=torch.float32,
    device=DEVICE
).unsqueeze(1)


generator = torch.Generator()
generator.manual_seed(SEED)

train_loader = (
    torch.utils.data.DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        generator=generator,
    )
)


# ============================================================
# MODEL
# ============================================================

class BushfireNN(nn.Module):

    def __init__(self):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(
                len(FEATURES),
                128
            ),
            nn.ReLU(),

            nn.Linear(
                128,
                64
            ),
            nn.ReLU(),

            nn.Linear(
                64,
                32
            ),
            nn.ReLU(),

            nn.Linear(
                32,
                1
            ),
        )


    def forward(self, x):
        return self.network(x)


model = BushfireNN().to(DEVICE)


parameter_count = sum(
    parameter.numel()
    for parameter in model.parameters()
    if parameter.requires_grad
)

print(
    f"Trainable params: "
    f"{parameter_count:,}"
)


criterion = nn.BCEWithLogitsLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY
)


# ============================================================
# TRAIN
# ============================================================

best_val_loss = float("inf")
best_epoch = 0
best_state = None
epochs_without_improvement = 0


for epoch in range(
    1,
    MAX_EPOCHS + 1
):

    model.train()

    total_train_loss = 0.0


    for batch_x, batch_y in train_loader:

        batch_x = batch_x.to(DEVICE)
        batch_y = batch_y.to(DEVICE)

        optimizer.zero_grad()

        logits = model(batch_x)

        loss = criterion(
            logits,
            batch_y
        )

        loss.backward()
        optimizer.step()

        total_train_loss += (
            loss.item()
            * batch_x.size(0)
        )


    train_loss = (
        total_train_loss
        / len(train_dataset)
    )


    # Validation
    model.eval()

    with torch.no_grad():

        val_logits = model(
            val_x_tensor
        )

        val_loss = criterion(
            val_logits,
            val_y_tensor
        ).item()


    if val_loss < (
        best_val_loss - 1e-6
    ):

        best_val_loss = val_loss
        best_epoch = epoch

        best_state = copy.deepcopy(
            model.state_dict()
        )

        epochs_without_improvement = 0

    else:

        epochs_without_improvement += 1


    if (
        epoch == 1
        or epoch % 10 == 0
    ):

        print(
            f"Epoch {epoch:03d} | "
            f"Train Loss "
            f"{train_loss:.5f} | "
            f"Val Loss "
            f"{val_loss:.5f}"
        )


    if (
        epochs_without_improvement
        >= PATIENCE
    ):

        print(
            f"Early stopping at "
            f"epoch {epoch}"
        )

        break


# ============================================================
# RESTORE BEST
# ============================================================

model.load_state_dict(
    best_state
)


# ============================================================
# METRICS
# ============================================================

def metrics_for(
    x,
    y
):

    model.eval()

    with torch.no_grad():

        logits = model(x)

        probability = torch.sigmoid(
            logits
        ).squeeze(1)

        prediction = (
            probability >= 0.5
        ).int()


    y_true = (
        y.squeeze(1)
        .detach()
        .cpu()
        .numpy()
        .astype(int)
    )

    probability = (
        probability
        .detach()
        .cpu()
        .numpy()
    )

    prediction = (
        prediction
        .detach()
        .cpu()
        .numpy()
    )


    return {
        "accuracy":
            accuracy_score(
                y_true,
                prediction
            ),

        "precision":
            precision_score(
                y_true,
                prediction,
                zero_division=0
            ),

        "recall":
            recall_score(
                y_true,
                prediction,
                zero_division=0
            ),

        "f1":
            f1_score(
                y_true,
                prediction,
                zero_division=0
            ),

        "roc_auc":
            roc_auc_score(
                y_true,
                probability
            ),
    }


train_metrics = metrics_for(
    torch.tensor(
        train_x,
        dtype=torch.float32,
        device=DEVICE
    ),
    torch.tensor(
        train_y,
        dtype=torch.float32,
        device=DEVICE
    ).unsqueeze(1)
)


val_metrics = metrics_for(
    val_x_tensor,
    val_y_tensor
)


# ============================================================
# SAVE
# ============================================================

checkpoint = {
    "model_state_dict":
        model.state_dict(),

    "input_size":
        len(FEATURES),

    "hidden_sizes":
        HIDDEN_SIZES,

    "features":
        FEATURES,

    "scaler_mean":
        mean,

    "scaler_std":
        std,

    "best_epoch":
        best_epoch,

    "best_val_loss":
        best_val_loss,

    "validation_metrics":
        val_metrics,

    "temporal_encoding":
        "day_of_year_sin_cos",

    "seed":
        SEED,
}


torch.save(
    checkpoint,
    OUTPUT_DIR
    / "temporal_128_64_32.pth"
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 72)
print("STAGE 12A RESULTS")
print("=" * 72)

print(
    f"Best epoch       : "
    f"{best_epoch}"
)

print(
    f"Best val loss    : "
    f"{best_val_loss:.5f}"
)


print("\nTRAIN")

for key, value in train_metrics.items():

    print(
        f"  {key:10s}: "
        f"{value:.4f}"
    )


print("\nVALIDATION")

for key, value in val_metrics.items():

    print(
        f"  {key:10s}: "
        f"{value:.4f}"
    )


difference = (
    val_metrics["roc_auc"]
    - STAGE11_BENCHMARK_AUC
)


print("\n" + "-" * 72)

print(
    f"Stage 11 AUC     : "
    f"{STAGE11_BENCHMARK_AUC:.4f}"
)

print(
    f"Stage 12A AUC    : "
    f"{val_metrics['roc_auc']:.4f}"
)

print(
    f"AUC change       : "
    f"{difference:+.4f}"
)


if difference > 0:

    print(
        "RESULT           : "
        "Temporal encoding improved AUC"
    )

elif difference < 0:

    print(
        "RESULT           : "
        "Temporal encoding did not improve AUC"
    )

else:

    print(
        "RESULT           : "
        "No AUC change"
    )


print()
print("TEST SET REMAINS LOCKED.")
print(" STAGE 12A COMPLETE ")
print("=" * 72)
