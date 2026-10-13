"""
Stage 13A - Random Forest Baseline

Uses the conservative Stage 12G pair-masked vegetation dataset.

Purpose:
Compare a tree-based model against the Stage 12G neural network
using the same information and the same frozen train/validation split.

TEST SET REMAINS LOCKED.
"""

from pathlib import Path
import json
import pickle

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
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

OUTPUT_DIR = Path("models/stage13a")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42

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

CATEGORICAL_FEATURES = [
    "vegetation_class",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

STAGE11_AUC = 0.592277
STAGE12G_NN_AUC = 0.6269


# ============================================================
# LOAD
# ============================================================

print("=" * 72)
print("STAGE 13A - RANDOM FOREST BASELINE")
print("=" * 72)

df = pd.read_csv(DATA_FILE)

train_df = df[df["split"] == "train"].copy()
val_df = df[df["split"] == "validation"].copy()

print(f"Train rows      : {len(train_df):,}")
print(f"Validation rows : {len(val_df):,}")
print("Test rows used  : 0 (LOCKED)")
print("Representation  : Stage 12G pair-masked vegetation")


X_train = train_df[FEATURES]
y_train = train_df["fire"].astype(int)

X_val = val_df[FEATURES]
y_val = val_df["fire"].astype(int)


# ============================================================
# PREPROCESSING
# ============================================================

encoder = OneHotEncoder(
    handle_unknown="ignore",
    sparse_output=True,
)

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            "passthrough",
            NUMERIC_FEATURES,
        ),
        (
            "vegetation",
            encoder,
            CATEGORICAL_FEATURES,
        ),
    ]
)

X_train_encoded = preprocessor.fit_transform(X_train)
X_val_encoded = preprocessor.transform(X_val)

print(
    f"Encoded input features : "
    f"{X_train_encoded.shape[1]}"
)


# ============================================================
# MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=500,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=2,
    max_features="sqrt",
    class_weight=None,
    random_state=SEED,
    n_jobs=-1,
)

print("Trees                  : 500")
print("min_samples_leaf       : 2")
print("max_features           : sqrt")

print("\nTraining Random Forest...")

model.fit(
    X_train_encoded,
    y_train,
)


# ============================================================
# EVALUATION
# ============================================================

def evaluate(X, y):

    probability = model.predict_proba(X)[:, 1]

    prediction = (
        probability >= 0.5
    ).astype(int)

    return {
        "accuracy": accuracy_score(
            y,
            prediction
        ),
        "precision": precision_score(
            y,
            prediction,
            zero_division=0
        ),
        "recall": recall_score(
            y,
            prediction,
            zero_division=0
        ),
        "f1": f1_score(
            y,
            prediction,
            zero_division=0
        ),
        "roc_auc": roc_auc_score(
            y,
            probability
        ),
    }


train_metrics = evaluate(
    X_train_encoded,
    y_train
)

val_metrics = evaluate(
    X_val_encoded,
    y_val
)


# ============================================================
# SAVE
# ============================================================

with open(
    OUTPUT_DIR / "random_forest.pkl",
    "wb"
) as file:

    pickle.dump(
        model,
        file
    )


with open(
    OUTPUT_DIR / "preprocessor.pkl",
    "wb"
) as file:

    pickle.dump(
        preprocessor,
        file
    )


metadata = {
    "seed": SEED,
    "numeric_features": NUMERIC_FEATURES,
    "categorical_features": CATEGORICAL_FEATURES,
    "representation":
        "Stage 12G pair-masked vegetation",
    "train_metrics": train_metrics,
    "validation_metrics": val_metrics,
}


with open(
    OUTPUT_DIR / "metadata.json",
    "w"
) as file:

    json.dump(
        metadata,
        file,
        indent=2
    )


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 72)
print("STAGE 13A RESULTS")
print("=" * 72)

print("\nTRAIN")

for key, value in train_metrics.items():
    print(
        f"  {key:10s}: {value:.4f}"
    )


print("\nVALIDATION")

for key, value in val_metrics.items():
    print(
        f"  {key:10s}: {value:.4f}"
    )


rf_auc = val_metrics["roc_auc"]

print("\n" + "-" * 72)

print(
    f"Stage 11 numeric NN AUC       : "
    f"{STAGE11_AUC:.4f}"
)

print(
    f"Stage 12G conservative NN AUC : "
    f"{STAGE12G_NN_AUC:.4f}"
)

print(
    f"Stage 13A Random Forest AUC   : "
    f"{rf_auc:.4f}"
)

print(
    f"RF vs Stage 12G NN            : "
    f"{rf_auc - STAGE12G_NN_AUC:+.4f}"
)


if rf_auc > STAGE12G_NN_AUC:
    print(
        "RESULT: Random Forest beats "
        "the conservative neural network."
    )
else:
    print(
        "RESULT: Conservative neural network "
        "remains ahead."
    )


print()
print("TEST SET REMAINS LOCKED.")
print("STAGE 13A COMPLETE")
print("=" * 72)
