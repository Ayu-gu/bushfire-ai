"""
Stage 11 - Neural Network Architecture Experiments
---------------------------------------------------

Purpose:
    Compare multiple PyTorch neural-network architectures
    using the SAME:
        - Stage 10 train split
        - Stage 10 validation split
        - 16 numeric features
        - training-only scaler
        - optimizer
        - loss function
        - early stopping rules

IMPORTANT:
    The TEST split is NOT evaluated here.

Architecture selection is based only on validation
performance.

Output:
    models/stage11/
        experiment_results.csv
        scaler_mean.npy
        scaler_std.npy
        feature_names.json
        <model checkpoints>
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
    "models/stage11"
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


FEATURES = [
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


ARCHITECTURES = {

    "baseline_32_16_8":
        [32, 16, 8],

    "medium_64_32_16":
        [64, 32, 16],

    "large_128_64_32":
        [128, 64, 32],

    "xl_256_128_64":
        [256, 128, 64],

    "boss_512_256_128_64":
        [512, 256, 128, 64],
}


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


print("=" * 72)
print("STAGE 11 - NEURAL NETWORK EXPERIMENTS")
print("=" * 72)

print(f"Device: {DEVICE}")


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(DATA_FILE)

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
    "Test rows used  : 0 "
    "(LOCKED)"
)


# ============================================================
# FEATURE VALIDATION
# ============================================================

missing_features = [
    feature
    for feature in FEATURES
    if feature not in df.columns
]

if missing_features:
    raise ValueError(
        f"Missing features: "
        f"{missing_features}"
    )


if train_df[FEATURES].isna().any().any():
    raise ValueError(
        "Training features contain null values."
    )

if val_df[FEATURES].isna().any().any():
    raise ValueError(
        "Validation features contain null values."
    )


# ============================================================
# TRAINING-ONLY STANDARDISATION
# ============================================================

train_x_raw = (
    train_df[FEATURES]
    .to_numpy(dtype=np.float32)
)

val_x_raw = (
    val_df[FEATURES]
    .to_numpy(dtype=np.float32)
)


mean = train_x_raw.mean(
    axis=0
)

std = train_x_raw.std(
    axis=0
)

# Protect against division by zero.
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
# TORCH DATA
# ============================================================

train_x_tensor = torch.tensor(
    train_x,
    dtype=torch.float32
)

train_y_tensor = torch.tensor(
    train_y,
    dtype=torch.float32
).unsqueeze(1)


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


train_dataset = (
    torch.utils.data.TensorDataset(
        train_x_tensor,
        train_y_tensor
    )
)


# ============================================================
# MODEL
# ============================================================

class BushfireNN(nn.Module):

    def __init__(
        self,
        input_size,
        hidden_sizes
    ):
        super().__init__()

        layers = []

        previous_size = input_size

        for hidden_size in hidden_sizes:

            layers.append(
                nn.Linear(
                    previous_size,
                    hidden_size
                )
            )

            layers.append(
                nn.ReLU()
            )

            previous_size = hidden_size

        layers.append(
            nn.Linear(
                previous_size,
                1
            )
        )

        self.network = nn.Sequential(
            *layers
        )


    def forward(self, x):
        return self.network(x)


# ============================================================
# HELPERS
# ============================================================

def parameter_count(model):
    return sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )


def evaluate(
    model,
    x,
    y
):
    model.eval()

    with torch.no_grad():

        logits = model(x)

        probabilities = torch.sigmoid(
            logits
        ).squeeze(1)

        predictions = (
            probabilities >= 0.5
        ).int()

    y_true = (
        y.squeeze(1)
        .detach()
        .cpu()
        .numpy()
        .astype(int)
    )

    y_probability = (
        probabilities
        .detach()
        .cpu()
        .numpy()
    )

    y_prediction = (
        predictions
        .detach()
        .cpu()
        .numpy()
    )

    return {
        "accuracy":
            accuracy_score(
                y_true,
                y_prediction
            ),

        "precision":
            precision_score(
                y_true,
                y_prediction,
                zero_division=0
            ),

        "recall":
            recall_score(
                y_true,
                y_prediction,
                zero_division=0
            ),

        "f1":
            f1_score(
                y_true,
                y_prediction,
                zero_division=0
            ),

        "roc_auc":
            roc_auc_score(
                y_true,
                y_probability
            ),
    }


# ============================================================
# TRAIN ONE ARCHITECTURE
# ============================================================

def train_experiment(
    name,
    hidden_sizes
):

    print("\n" + "=" * 72)

    print(
        f"EXPERIMENT: {name}"
    )

    architecture_text = (
        [len(FEATURES)]
        + hidden_sizes
        + [1]
    )

    print(
        "Architecture:",
        " -> ".join(
            map(
                str,
                architecture_text
            )
        )
    )


    # Reset seed so architecture comparisons
    # remain reproducible.
    set_seed(SEED)


    model = BushfireNN(
        input_size=len(FEATURES),
        hidden_sizes=hidden_sizes
    ).to(DEVICE)


    params = parameter_count(
        model
    )

    print(
        f"Trainable parameters: "
        f"{params:,}"
    )


    criterion = (
        nn.BCEWithLogitsLoss()
    )


    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )


    # New deterministic DataLoader generator
    # for every architecture.
    loader_generator = (
        torch.Generator()
    )

    loader_generator.manual_seed(
        SEED
    )


    train_loader = (
        torch.utils.data.DataLoader(
            train_dataset,
            batch_size=BATCH_SIZE,
            shuffle=True,
            generator=loader_generator,
        )
    )


    best_val_loss = float(
        "inf"
    )

    best_epoch = 0

    best_state = None

    epochs_without_improvement = 0


    for epoch in range(
        1,
        MAX_EPOCHS + 1
    ):

        # ------------------------
        # TRAIN
        # ------------------------

        model.train()

        total_train_loss = 0.0


        for batch_x, batch_y in train_loader:

            batch_x = batch_x.to(
                DEVICE
            )

            batch_y = batch_y.to(
                DEVICE
            )


            optimizer.zero_grad()


            logits = model(
                batch_x
            )

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


        # ------------------------
        # VALIDATION LOSS
        # ------------------------

        model.eval()

        with torch.no_grad():

            val_logits = model(
                val_x_tensor
            )

            val_loss = criterion(
                val_logits,
                val_y_tensor
            ).item()


        # ------------------------
        # EARLY STOPPING
        # ------------------------

        if val_loss < (
            best_val_loss - 1e-6
        ):

            best_val_loss = (
                val_loss
            )

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


    # ========================================================
    # RESTORE BEST MODEL
    # ========================================================

    model.load_state_dict(
        best_state
    )


    # ========================================================
    # FINAL TRAIN + VALIDATION METRICS
    # ========================================================

    train_metrics = evaluate(
        model,
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


    val_metrics = evaluate(
        model,
        val_x_tensor,
        val_y_tensor
    )


    checkpoint_path = (
        OUTPUT_DIR
        / f"{name}.pth"
    )


    torch.save(
        {
            "model_state_dict":
                model.state_dict(),

            "input_size":
                len(FEATURES),

            "hidden_sizes":
                hidden_sizes,

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

            "seed":
                SEED,
        },
        checkpoint_path
    )


    print(
        f"\nBest epoch: "
        f"{best_epoch}"
    )

    print(
        f"Best validation loss: "
        f"{best_val_loss:.5f}"
    )


    print("\nTRAIN METRICS")

    for key, value in (
        train_metrics.items()
    ):
        print(
            f"  {key:10s}: "
            f"{value:.4f}"
        )


    print("\nVALIDATION METRICS")

    for key, value in (
        val_metrics.items()
    ):
        print(
            f"  {key:10s}: "
            f"{value:.4f}"
        )


    print(
        f"\nSaved: "
        f"{checkpoint_path}"
    )


    return {

        "name":
            name,

        "architecture":
            "-".join(
                map(
                    str,
                    architecture_text
                )
            ),

        "parameters":
            params,

        "best_epoch":
            best_epoch,

        "best_val_loss":
            best_val_loss,

        "train_accuracy":
            train_metrics[
                "accuracy"
            ],

        "train_f1":
            train_metrics[
                "f1"
            ],

        "train_auc":
            train_metrics[
                "roc_auc"
            ],

        "val_accuracy":
            val_metrics[
                "accuracy"
            ],

        "val_precision":
            val_metrics[
                "precision"
            ],

        "val_recall":
            val_metrics[
                "recall"
            ],

        "val_f1":
            val_metrics[
                "f1"
            ],

        "val_auc":
            val_metrics[
                "roc_auc"
            ],
    }


# ============================================================
# RUN EXPERIMENTS
# ============================================================

results = []


for name, hidden_sizes in (
    ARCHITECTURES.items()
):

    result = train_experiment(
        name,
        hidden_sizes
    )

    results.append(
        result
    )


# ============================================================
# RESULTS TABLE
# ============================================================

results_df = pd.DataFrame(
    results
)


results_df = (
    results_df
    .sort_values(
        [
            "val_auc",
            "val_f1",
        ],
        ascending=False
    )
    .reset_index(drop=True)
)


results_df.to_csv(
    OUTPUT_DIR
    / "experiment_results.csv",
    index=False
)


print("\n" + "=" * 72)
print("STAGE 11 RESULTS")
print("=" * 72)


display_columns = [
    "name",
    "architecture",
    "parameters",
    "best_epoch",
    "val_accuracy",
    "val_precision",
    "val_recall",
    "val_f1",
    "val_auc",
]


print(
    results_df[
        display_columns
    ].to_string(
        index=False
    )
)


winner = results_df.iloc[0]


print("\n" + "=" * 72)

print(
    "VALIDATION WINNER:"
)

print(
    winner["name"]
)

print(
    f"AUC      : "
    f"{winner['val_auc']:.4f}"
)

print(
    f"F1       : "
    f"{winner['val_f1']:.4f}"
)

print(
    f"Accuracy : "
    f"{winner['val_accuracy']:.4f}"
)

print()
print(
    "TEST SET REMAINS LOCKED."
)

print(
    " STAGE 11 COMPLETE "
)

print("=" * 72)
