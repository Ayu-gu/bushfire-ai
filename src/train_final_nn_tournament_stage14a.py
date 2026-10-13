"""
Stage 14A - Final Neural Network Tournament

Dataset:
    Stage 12G pair-masked vegetation representation.

Purpose:
    Compare three neural-network architectures under the same
    preprocessing, regularisation and training protocol.

Selection:
    Validation ROC-AUC.

IMPORTANT:
    Test set remains locked.
"""

from pathlib import Path
import copy
import json
import pickle
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from sklearn.preprocessing import OneHotEncoder
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
    "data/stage12g_pair_masked_vegetation.csv"
)

OUTPUT_DIR = Path("models/stage14a")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
MAX_EPOCHS = 300
PATIENCE = 30

LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-4
BATCH_SIZE = 256
DROPOUT = 0.25

RF_BENCHMARK_AUC = 0.6932


NUMERIC_FEATURES = [
    "month",
    "day_of_year",
    "season",
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

CATEGORICAL_FEATURE = "vegetation_class"


ARCHITECTURES = [
    {
        "name": "NN_128_64_32",
        "hidden": [128, 64, 32],
    },
    {
        "name": "NN_256_128_64",
        "hidden": [256, 128, 64],
    },
    {
        "name": "NN_512_256_128_64",
        "hidden": [512, 256, 128, 64],
    },
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


if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 80)
print("STAGE 14A - FINAL NEURAL NETWORK TOURNAMENT")
print("=" * 80)

print(f"Device          : {DEVICE}")

df = pd.read_csv(DATA_FILE)

train_df = df[
    df["split"] == "train"
].copy()

val_df = df[
    df["split"] == "validation"
].copy()

print(f"Train rows      : {len(train_df):,}")
print(f"Validation rows : {len(val_df):,}")
print("Test rows used  : 0 (LOCKED)")
print("Representation  : Stage 12G pair-masked vegetation")


# ============================================================
# NUMERIC PREPROCESSING — TRAIN ONLY
# ============================================================

train_numeric_raw = (
    train_df[NUMERIC_FEATURES]
    .to_numpy(dtype=np.float32)
)

val_numeric_raw = (
    val_df[NUMERIC_FEATURES]
    .to_numpy(dtype=np.float32)
)

mean = train_numeric_raw.mean(axis=0)
std = train_numeric_raw.std(axis=0)

std = np.where(
    std < 1e-8,
    1.0,
    std,
)

train_numeric = (
    train_numeric_raw - mean
) / std

val_numeric = (
    val_numeric_raw - mean
) / std


# ============================================================
# VEGETATION ENCODING — TRAIN ONLY
# ============================================================

encoder = OneHotEncoder(
    handle_unknown="ignore",
    sparse_output=False,
    dtype=np.float32,
)

train_vegetation = encoder.fit_transform(
    train_df[[CATEGORICAL_FEATURE]]
)

val_vegetation = encoder.transform(
    val_df[[CATEGORICAL_FEATURE]]
)

vegetation_categories = (
    encoder.categories_[0].tolist()
)


# ============================================================
# COMBINE INPUTS
# ============================================================

train_x = np.concatenate(
    [
        train_numeric,
        train_vegetation,
    ],
    axis=1,
).astype(np.float32)

val_x = np.concatenate(
    [
        val_numeric,
        val_vegetation,
    ],
    axis=1,
).astype(np.float32)

train_y = (
    train_df["fire"]
    .to_numpy(dtype=np.float32)
)

val_y = (
    val_df["fire"]
    .to_numpy(dtype=np.float32)
)

INPUT_SIZE = train_x.shape[1]

print(
    f"Numeric features      : "
    f"{len(NUMERIC_FEATURES)}"
)

print(
    f"Vegetation categories : "
    f"{len(vegetation_categories)}"
)

print(
    f"Total input features  : "
    f"{INPUT_SIZE}"
)

print(
    f"Dropout               : "
    f"{DROPOUT}"
)

print(
    f"Weight decay          : "
    f"{WEIGHT_DECAY}"
)


# ============================================================
# TORCH DATA
# ============================================================

train_dataset = torch.utils.data.TensorDataset(
    torch.tensor(
        train_x,
        dtype=torch.float32,
    ),
    torch.tensor(
        train_y,
        dtype=torch.float32,
    ).unsqueeze(1),
)

val_x_tensor = torch.tensor(
    val_x,
    dtype=torch.float32,
    device=DEVICE,
)

val_y_tensor = torch.tensor(
    val_y,
    dtype=torch.float32,
    device=DEVICE,
).unsqueeze(1)


# ============================================================
# MODEL
# ============================================================

class BushfireNN(nn.Module):

    def __init__(
        self,
        input_size,
        hidden_sizes,
        dropout,
    ):
        super().__init__()

        layers = []
        previous = input_size

        for hidden in hidden_sizes:

            layers.append(
                nn.Linear(
                    previous,
                    hidden,
                )
            )

            layers.append(
                nn.ReLU()
            )

            layers.append(
                nn.Dropout(dropout)
            )

            previous = hidden

        layers.append(
            nn.Linear(
                previous,
                1,
            )
        )

        self.network = nn.Sequential(*layers)


    def forward(self, x):
        return self.network(x)


# ============================================================
# METRICS
# ============================================================

def evaluate(model, x, y):

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
                prediction,
            ),

        "precision":
            precision_score(
                y_true,
                prediction,
                zero_division=0,
            ),

        "recall":
            recall_score(
                y_true,
                prediction,
                zero_division=0,
            ),

        "f1":
            f1_score(
                y_true,
                prediction,
                zero_division=0,
            ),

        "roc_auc":
            roc_auc_score(
                y_true,
                probability,
            ),
    }


# ============================================================
# TOURNAMENT
# ============================================================

results = []

best_model_state = None
best_result = None


for architecture in ARCHITECTURES:

    # Reset seed so architecture comparisons remain reproducible.
    set_seed(SEED)

    name = architecture["name"]
    hidden_sizes = architecture["hidden"]

    print("\n" + "-" * 80)
    print(f"TRAINING: {name}")

    architecture_string = (
        [INPUT_SIZE]
        + hidden_sizes
        + [1]
    )

    print(
        "Architecture: "
        + " -> ".join(
            map(str, architecture_string)
        )
    )

    model = BushfireNN(
        INPUT_SIZE,
        hidden_sizes,
        DROPOUT,
    ).to(DEVICE)

    parameter_count = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )

    print(
        f"Trainable parameters: "
        f"{parameter_count:,}"
    )

    criterion = nn.BCEWithLogitsLoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    # New deterministic loader for each architecture.
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

    best_val_loss = float("inf")
    best_epoch = 0
    best_state = None
    epochs_without_improvement = 0

    for epoch in range(
        1,
        MAX_EPOCHS + 1,
    ):

        model.train()

        total_loss = 0.0

        for batch_x, batch_y in train_loader:

            batch_x = batch_x.to(DEVICE)
            batch_y = batch_y.to(DEVICE)

            optimizer.zero_grad()

            logits = model(batch_x)

            loss = criterion(
                logits,
                batch_y,
            )

            loss.backward()
            optimizer.step()

            total_loss += (
                loss.item()
                * batch_x.size(0)
            )

        train_loss = (
            total_loss
            / len(train_dataset)
        )

        model.eval()

        with torch.no_grad():

            val_logits = model(
                val_x_tensor
            )

            val_loss = criterion(
                val_logits,
                val_y_tensor,
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
                f"Train Loss {train_loss:.5f} | "
                f"Val Loss {val_loss:.5f}"
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

    model.load_state_dict(
        best_state
    )

    train_metrics = evaluate(
        model,
        torch.tensor(
            train_x,
            dtype=torch.float32,
            device=DEVICE,
        ),
        torch.tensor(
            train_y,
            dtype=torch.float32,
            device=DEVICE,
        ).unsqueeze(1),
    )

    val_metrics = evaluate(
        model,
        val_x_tensor,
        val_y_tensor,
    )

    auc_gap = (
        train_metrics["roc_auc"]
        - val_metrics["roc_auc"]
    )

    result = {
        "name": name,
        "architecture":
            architecture_string,
        "hidden_sizes":
            hidden_sizes,
        "parameters":
            parameter_count,
        "best_epoch":
            best_epoch,
        "best_val_loss":
            best_val_loss,
        "train_metrics":
            train_metrics,
        "validation_metrics":
            val_metrics,
        "auc_gap":
            auc_gap,
    }

    results.append(result)

    checkpoint = {
        "model_state_dict":
            model.state_dict(),

        "input_size":
            INPUT_SIZE,

        "hidden_sizes":
            hidden_sizes,

        "dropout":
            DROPOUT,

        "numeric_features":
            NUMERIC_FEATURES,

        "vegetation_categories":
            vegetation_categories,

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

        "seed":
            SEED,
    }

    torch.save(
        checkpoint,
        OUTPUT_DIR / f"{name}.pth",
    )

    print(
        f"Best epoch : {best_epoch}"
    )

    print(
        f"Train AUC  : "
        f"{train_metrics['roc_auc']:.4f}"
    )

    print(
        f"Val AUC    : "
        f"{val_metrics['roc_auc']:.4f}"
    )

    print(
        f"AUC gap    : "
        f"{auc_gap:.4f}"
    )

    print(
        f"Val Acc    : "
        f"{val_metrics['accuracy']:.4f}"
    )

    print(
        f"Val F1     : "
        f"{val_metrics['f1']:.4f}"
    )

    if (
        best_result is None
        or val_metrics["roc_auc"]
        > best_result[
            "validation_metrics"
        ]["roc_auc"]
    ):

        best_result = result
        best_model_state = copy.deepcopy(
            model.state_dict()
        )


# ============================================================
# RANKING
# ============================================================

results = sorted(
    results,
    key=lambda x:
        x["validation_metrics"]["roc_auc"],
    reverse=True,
)

print("\n" + "=" * 80)
print("STAGE 14A NN RANKING")
print("=" * 80)

print(
    f"{'MODEL':24s} "
    f"{'PARAMS':>10s} "
    f"{'EPOCH':>7s} "
    f"{'TRAIN AUC':>10s} "
    f"{'VAL AUC':>10s} "
    f"{'GAP':>9s} "
    f"{'VAL F1':>9s}"
)

for result in results:

    print(
        f"{result['name']:24s} "
        f"{result['parameters']:10,d} "
        f"{result['best_epoch']:7d} "
        f"{result['train_metrics']['roc_auc']:10.4f} "
        f"{result['validation_metrics']['roc_auc']:10.4f} "
        f"{result['auc_gap']:9.4f} "
        f"{result['validation_metrics']['f1']:9.4f}"
    )


# ============================================================
# SAVE SHARED PREPROCESSING
# ============================================================

np.save(
    OUTPUT_DIR / "scaler_mean.npy",
    mean,
)

np.save(
    OUTPUT_DIR / "scaler_std.npy",
    std,
)

with open(
    OUTPUT_DIR / "vegetation_encoder.pkl",
    "wb",
) as file:

    pickle.dump(
        encoder,
        file,
    )

with open(
    OUTPUT_DIR / "results.json",
    "w",
) as file:

    json.dump(
        results,
        file,
        indent=2,
    )


# ============================================================
# WINNER
# ============================================================

nn_auc = (
    best_result[
        "validation_metrics"
    ]["roc_auc"]
)

print("\n" + "=" * 80)
print("BEST NEURAL NETWORK")
print("=" * 80)

print(
    f"Model          : "
    f"{best_result['name']}"
)

print(
    "Architecture   : "
    + " -> ".join(
        map(
            str,
            best_result["architecture"],
        )
    )
)

print(
    f"Best epoch     : "
    f"{best_result['best_epoch']}"
)

print(
    f"Train AUC      : "
    f"{best_result['train_metrics']['roc_auc']:.4f}"
)

print(
    f"Validation AUC : "
    f"{nn_auc:.4f}"
)

print(
    f"Validation Acc : "
    f"{best_result['validation_metrics']['accuracy']:.4f}"
)

print(
    f"Validation F1  : "
    f"{best_result['validation_metrics']['f1']:.4f}"
)

print("\n" + "-" * 80)

print(
    f"Best RF validation AUC : "
    f"{RF_BENCHMARK_AUC:.4f}"
)

print(
    f"Best NN validation AUC : "
    f"{nn_auc:.4f}"
)

print(
    f"NN vs RF difference    : "
    f"{nn_auc - RF_BENCHMARK_AUC:+.4f}"
)

print()
print("TEST SET REMAINS LOCKED.")
print("STAGE 14A COMPLETE")
print("=" * 80)
