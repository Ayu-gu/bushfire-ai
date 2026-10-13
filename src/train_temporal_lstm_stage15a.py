"""
Stage 15A - Temporal LSTM Bushfire Model

Temporal branch:
    31 days x 5 weather features
        - max temperature
        - min temperature
        - precipitation
        - max wind
        - mean daily relative humidity

Static branch:
    - month cyclical encoding
    - day-of-year cyclical encoding
    - season cyclical encoding
    - elevation

Fusion:
    LSTM temporal embedding + static context
        -> DFF
        -> fire probability

Uses TRAIN + VALIDATION only.
TEST SET REMAINS LOCKED.
"""

from pathlib import Path
import copy
import json
import math
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

FIRE_CACHE = Path("data/weather_cache_stage4")
CONTROL_CACHE = Path("data/weather_cache_stage8_controls")

OUTPUT_DIR = Path("models/stage15a")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
SEQUENCE_LENGTH = 31

TEMPORAL_FEATURES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
    "daily_mean_relative_humidity",
]

TEMPORAL_SIZE = len(TEMPORAL_FEATURES)

LSTM_HIDDEN_SIZE = 64
LSTM_LAYERS = 2
LSTM_DROPOUT = 0.20

FUSION_HIDDEN = [64, 32]
FUSION_DROPOUT = 0.25

BATCH_SIZE = 256
MAX_EPOCHS = 200
PATIENCE = 25

LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-4

RF_BENCHMARK_AUC = 0.6932
DFF_BENCHMARK_AUC = 0.6417


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
# WEATHER SEQUENCE
# ============================================================

def build_daily_humidity(hourly):

    times = pd.to_datetime(hourly["time"])

    humidity = pd.to_numeric(
        pd.Series(hourly["relative_humidity_2m"]),
        errors="coerce",
    )

    frame = pd.DataFrame({
        "time": times,
        "humidity": humidity,
    })

    frame["date"] = frame["time"].dt.date

    daily = (
        frame.groupby("date")["humidity"]
        .mean()
    )

    return daily


def load_sequence(row):

    source_id = str(int(row["source_row_id"]))

    folder = (
        FIRE_CACHE
        if int(row["fire"]) == 1
        else CONTROL_CACHE
    )

    path = folder / f"{source_id}.json"

    with open(path) as file:
        data = json.load(file)

    daily = data["daily"]

    dates = pd.to_datetime(
        daily["time"]
    )

    humidity_by_date = build_daily_humidity(
        data["hourly"]
    )

    humidity_values = []

    for date in dates:
        value = humidity_by_date.get(
            date.date(),
            np.nan,
        )
        humidity_values.append(value)

    sequence = np.column_stack([
        np.asarray(
            daily["temperature_2m_max"],
            dtype=np.float32,
        ),
        np.asarray(
            daily["temperature_2m_min"],
            dtype=np.float32,
        ),
        np.asarray(
            daily["precipitation_sum"],
            dtype=np.float32,
        ),
        np.asarray(
            daily["wind_speed_10m_max"],
            dtype=np.float32,
        ),
        np.asarray(
            humidity_values,
            dtype=np.float32,
        ),
    ])

    if sequence.shape != (
        SEQUENCE_LENGTH,
        TEMPORAL_SIZE,
    ):
        raise ValueError(
            f"Unexpected sequence shape "
            f"{sequence.shape} for {path}"
        )

    return sequence


# ============================================================
# STATIC FEATURES
# ============================================================

def build_static_features(frame):

    month = frame["month"].to_numpy(
        dtype=np.float32
    )

    day = frame["day_of_year"].to_numpy(
        dtype=np.float32
    )

    season = frame["season"].to_numpy(
        dtype=np.float32
    )

    elevation = frame["elevation"].to_numpy(
        dtype=np.float32
    )

    features = np.column_stack([
        np.sin(2 * np.pi * month / 12.0),
        np.cos(2 * np.pi * month / 12.0),

        np.sin(2 * np.pi * day / 365.25),
        np.cos(2 * np.pi * day / 365.25),

        np.sin(2 * np.pi * season / 4.0),
        np.cos(2 * np.pi * season / 4.0),

        elevation,
    ])

    return features.astype(np.float32)


# ============================================================
# LOAD
# ============================================================

print("=" * 80)
print("STAGE 15A - TEMPORAL LSTM BUSHFIRE MODEL")
print("=" * 80)

print(f"Device          : {DEVICE}")

df = pd.read_csv(DATA_FILE)

# IMPORTANT:
# We deliberately construct only train/validation tensors.
# Test rows are not loaded into model evaluation.

train_df = df[
    df["split"] == "train"
].copy()

val_df = df[
    df["split"] == "validation"
].copy()

print(f"Train rows      : {len(train_df):,}")
print(f"Validation rows : {len(val_df):,}")
print("Test rows used  : 0 (LOCKED)")
print(
    f"Temporal input  : "
    f"{SEQUENCE_LENGTH} days x "
    f"{TEMPORAL_SIZE} features"
)

print("\nLoading cached weather sequences...")


def build_sequences(frame):

    sequences = []

    for count, (_, row) in enumerate(
        frame.iterrows(),
        start=1,
    ):
        sequences.append(
            load_sequence(row)
        )

        if count % 2500 == 0:
            print(
                f"  loaded {count:,}/"
                f"{len(frame):,}"
            )

    return np.stack(sequences)


train_sequence = build_sequences(
    train_df
)

val_sequence = build_sequences(
    val_df
)

print(
    "Train sequence shape:",
    train_sequence.shape,
)

print(
    "Val sequence shape  :",
    val_sequence.shape,
)


# ============================================================
# MISSING VALUES
# ============================================================

# Calculate temporal imputation values using TRAIN ONLY.

temporal_fill = np.nanmedian(
    train_sequence,
    axis=(0, 1),
)

for feature_index in range(TEMPORAL_SIZE):

    train_mask = np.isnan(
        train_sequence[:, :, feature_index]
    )

    val_mask = np.isnan(
        val_sequence[:, :, feature_index]
    )

    train_sequence[
        :, :, feature_index
    ][train_mask] = temporal_fill[
        feature_index
    ]

    val_sequence[
        :, :, feature_index
    ][val_mask] = temporal_fill[
        feature_index
    ]


# ============================================================
# TEMPORAL STANDARDISATION — TRAIN ONLY
# ============================================================

temporal_mean = train_sequence.mean(
    axis=(0, 1)
)

temporal_std = train_sequence.std(
    axis=(0, 1)
)

temporal_std = np.where(
    temporal_std < 1e-8,
    1.0,
    temporal_std,
)

train_sequence = (
    train_sequence - temporal_mean
) / temporal_std

val_sequence = (
    val_sequence - temporal_mean
) / temporal_std


# ============================================================
# STATIC PREPROCESSING — TRAIN ONLY
# ============================================================

train_static = build_static_features(
    train_df
)

val_static = build_static_features(
    val_df
)

static_fill = np.nanmedian(
    train_static,
    axis=0,
)

train_nan = np.where(
    np.isnan(train_static)
)

val_nan = np.where(
    np.isnan(val_static)
)

train_static[train_nan] = np.take(
    static_fill,
    train_nan[1],
)

val_static[val_nan] = np.take(
    static_fill,
    val_nan[1],
)

static_mean = train_static.mean(
    axis=0
)

static_std = train_static.std(
    axis=0
)

static_std = np.where(
    static_std < 1e-8,
    1.0,
    static_std,
)

train_static = (
    train_static - static_mean
) / static_std

val_static = (
    val_static - static_mean
) / static_std


# ============================================================
# LABELS
# ============================================================

train_y = train_df["fire"].to_numpy(
    dtype=np.float32
)

val_y = val_df["fire"].to_numpy(
    dtype=np.float32
)


# ============================================================
# DATASET
# ============================================================

train_dataset = torch.utils.data.TensorDataset(
    torch.tensor(
        train_sequence,
        dtype=torch.float32,
    ),
    torch.tensor(
        train_static,
        dtype=torch.float32,
    ),
    torch.tensor(
        train_y,
        dtype=torch.float32,
    ).unsqueeze(1),
)

generator = torch.Generator()
generator.manual_seed(SEED)

train_loader = torch.utils.data.DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    generator=generator,
)

val_sequence_tensor = torch.tensor(
    val_sequence,
    dtype=torch.float32,
    device=DEVICE,
)

val_static_tensor = torch.tensor(
    val_static,
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

class TemporalBushfireLSTM(nn.Module):

    def __init__(self):
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=TEMPORAL_SIZE,
            hidden_size=LSTM_HIDDEN_SIZE,
            num_layers=LSTM_LAYERS,
            batch_first=True,
            dropout=LSTM_DROPOUT,
        )

        fusion_input = (
            LSTM_HIDDEN_SIZE
            + train_static.shape[1]
        )

        self.fusion = nn.Sequential(
            nn.Linear(
                fusion_input,
                FUSION_HIDDEN[0],
            ),
            nn.ReLU(),
            nn.Dropout(FUSION_DROPOUT),

            nn.Linear(
                FUSION_HIDDEN[0],
                FUSION_HIDDEN[1],
            ),
            nn.ReLU(),
            nn.Dropout(FUSION_DROPOUT),

            nn.Linear(
                FUSION_HIDDEN[1],
                1,
            ),
        )


    def forward(
        self,
        sequence,
        static,
    ):

        _, (hidden, _) = self.lstm(
            sequence
        )

        temporal_embedding = hidden[-1]

        combined = torch.cat(
            [
                temporal_embedding,
                static,
            ],
            dim=1,
        )

        return self.fusion(
            combined
        )


model = TemporalBushfireLSTM().to(
    DEVICE
)

parameter_count = sum(
    p.numel()
    for p in model.parameters()
    if p.requires_grad
)

print("\nMODEL")
print(
    f"LSTM hidden size : "
    f"{LSTM_HIDDEN_SIZE}"
)

print(
    f"LSTM layers      : "
    f"{LSTM_LAYERS}"
)

print(
    f"Static features  : "
    f"{train_static.shape[1]}"
)

print(
    f"Parameters       : "
    f"{parameter_count:,}"
)


# ============================================================
# TRAINING
# ============================================================

criterion = nn.BCEWithLogitsLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY,
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

    for (
        batch_sequence,
        batch_static,
        batch_y,
    ) in train_loader:

        batch_sequence = (
            batch_sequence.to(DEVICE)
        )

        batch_static = (
            batch_static.to(DEVICE)
        )

        batch_y = batch_y.to(DEVICE)

        optimizer.zero_grad()

        logits = model(
            batch_sequence,
            batch_static,
        )

        loss = criterion(
            logits,
            batch_y,
        )

        loss.backward()
        optimizer.step()

        total_loss += (
            loss.item()
            * batch_sequence.size(0)
        )

    train_loss = (
        total_loss
        / len(train_dataset)
    )

    model.eval()

    with torch.no_grad():

        val_logits = model(
            val_sequence_tensor,
            val_static_tensor,
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


# ============================================================
# EVALUATION
# ============================================================

def evaluate(
    model,
    sequence,
    static,
    labels,
):

    model.eval()

    with torch.no_grad():

        logits = model(
            sequence,
            static,
        )

        probability = torch.sigmoid(
            logits
        ).squeeze(1)

        prediction = (
            probability >= 0.5
        ).int()

    probability = (
        probability
        .cpu()
        .numpy()
    )

    prediction = (
        prediction
        .cpu()
        .numpy()
    )

    labels = (
        labels.squeeze(1)
        .cpu()
        .numpy()
        .astype(int)
    )

    return {
        "accuracy":
            accuracy_score(
                labels,
                prediction,
            ),

        "precision":
            precision_score(
                labels,
                prediction,
                zero_division=0,
            ),

        "recall":
            recall_score(
                labels,
                prediction,
                zero_division=0,
            ),

        "f1":
            f1_score(
                labels,
                prediction,
                zero_division=0,
            ),

        "roc_auc":
            roc_auc_score(
                labels,
                probability,
            ),
    }


train_metrics = evaluate(
    model,

    torch.tensor(
        train_sequence,
        dtype=torch.float32,
        device=DEVICE,
    ),

    torch.tensor(
        train_static,
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
    val_sequence_tensor,
    val_static_tensor,
    val_y_tensor,
)


# ============================================================
# SAVE
# ============================================================

checkpoint = {
    "model_state_dict":
        model.state_dict(),

    "sequence_length":
        SEQUENCE_LENGTH,

    "temporal_features":
        TEMPORAL_FEATURES,

    "temporal_fill":
        temporal_fill,

    "temporal_mean":
        temporal_mean,

    "temporal_std":
        temporal_std,

    "static_fill":
        static_fill,

    "static_mean":
        static_mean,

    "static_std":
        static_std,

    "lstm_hidden_size":
        LSTM_HIDDEN_SIZE,

    "lstm_layers":
        LSTM_LAYERS,

    "lstm_dropout":
        LSTM_DROPOUT,

    "fusion_hidden":
        FUSION_HIDDEN,

    "fusion_dropout":
        FUSION_DROPOUT,

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
    OUTPUT_DIR / "temporal_lstm.pth",
)


metadata = {
    "model":
        "Temporal LSTM + static fusion",

    "sequence":
        "31 days x 5 weather features",

    "vegetation_used":
        False,

    "reason_vegetation_excluded":
        "Avoid known mapping-availability shortcut",

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

    "test_used":
        False,
}

with open(
    OUTPUT_DIR / "metadata.json",
    "w",
) as file:

    json.dump(
        metadata,
        file,
        indent=2,
    )


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 80)
print("STAGE 15A RESULTS")
print("=" * 80)

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


lstm_auc = val_metrics[
    "roc_auc"
]

print("\n" + "-" * 80)

print(
    f"Static DFF AUC      : "
    f"{DFF_BENCHMARK_AUC:.4f}"
)

print(
    f"Random Forest AUC   : "
    f"{RF_BENCHMARK_AUC:.4f}"
)

print(
    f"Temporal LSTM AUC   : "
    f"{lstm_auc:.4f}"
)

print(
    f"LSTM vs DFF         : "
    f"{lstm_auc - DFF_BENCHMARK_AUC:+.4f}"
)

print(
    f"LSTM vs RF          : "
    f"{lstm_auc - RF_BENCHMARK_AUC:+.4f}"
)

print()
print("TEST SET REMAINS LOCKED.")
print("STAGE 15A COMPLETE")
print("=" * 80)
