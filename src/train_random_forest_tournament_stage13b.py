"""
Stage 13B - Regularised Random Forest Tournament

Same frozen Stage 10 split.
Same conservative Stage 12G vegetation representation.
Test set remains completely locked.

Goal:
Reduce the extreme overfitting observed in Stage 13A while
maximising validation ROC-AUC.
"""

from pathlib import Path
import json
import pickle
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

DATA_FILE = Path("data/stage12g_pair_masked_vegetation.csv")
OUTPUT_DIR = Path("models/stage13b")
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

CATEGORICAL_FEATURES = ["vegetation_class"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

CONFIGS = [
    {
        "name": "RF_A_current",
        "max_depth": None,
        "min_samples_leaf": 2,
    },
    {
        "name": "RF_B_depth20_leaf5",
        "max_depth": 20,
        "min_samples_leaf": 5,
    },
    {
        "name": "RF_C_depth15_leaf10",
        "max_depth": 15,
        "min_samples_leaf": 10,
    },
    {
        "name": "RF_D_depth10_leaf15",
        "max_depth": 10,
        "min_samples_leaf": 15,
    },
]


print("=" * 78)
print("STAGE 13B - REGULARISED RANDOM FOREST TOURNAMENT")
print("=" * 78)

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


# ------------------------------------------------------------
# Preprocessing — fit TRAIN only
# ------------------------------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            "passthrough",
            NUMERIC_FEATURES,
        ),
        (
            "vegetation",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=True,
            ),
            CATEGORICAL_FEATURES,
        ),
    ]
)

X_train_encoded = preprocessor.fit_transform(X_train)
X_val_encoded = preprocessor.transform(X_val)

print(f"Encoded features : {X_train_encoded.shape[1]}")


def metrics(model, X, y):
    probability = model.predict_proba(X)[:, 1]
    prediction = (probability >= 0.5).astype(int)

    return {
        "accuracy": accuracy_score(y, prediction),
        "precision": precision_score(
            y, prediction, zero_division=0
        ),
        "recall": recall_score(
            y, prediction, zero_division=0
        ),
        "f1": f1_score(
            y, prediction, zero_division=0
        ),
        "roc_auc": roc_auc_score(
            y, probability
        ),
    }


results = []
best_model = None
best_result = None


# ------------------------------------------------------------
# Tournament
# ------------------------------------------------------------

for config in CONFIGS:

    print("\n" + "-" * 78)
    print(f"TRAINING: {config['name']}")
    print(
        f"max_depth={config['max_depth']} | "
        f"min_samples_leaf={config['min_samples_leaf']}"
    )

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=config["max_depth"],
        min_samples_split=2,
        min_samples_leaf=config["min_samples_leaf"],
        max_features="sqrt",
        random_state=SEED,
        n_jobs=-1,
    )

    model.fit(
        X_train_encoded,
        y_train,
    )

    train_metrics = metrics(
        model,
        X_train_encoded,
        y_train,
    )

    val_metrics = metrics(
        model,
        X_val_encoded,
        y_val,
    )

    gap = (
        train_metrics["roc_auc"]
        - val_metrics["roc_auc"]
    )

    result = {
        "name": config["name"],
        "max_depth": config["max_depth"],
        "min_samples_leaf": config["min_samples_leaf"],
        "train_metrics": train_metrics,
        "validation_metrics": val_metrics,
        "auc_gap": gap,
    }

    results.append(result)

    print(
        f"Train AUC : "
        f"{train_metrics['roc_auc']:.4f}"
    )

    print(
        f"Val AUC   : "
        f"{val_metrics['roc_auc']:.4f}"
    )

    print(
        f"AUC gap   : "
        f"{gap:.4f}"
    )

    print(
        f"Val Acc   : "
        f"{val_metrics['accuracy']:.4f}"
    )

    print(
        f"Val F1    : "
        f"{val_metrics['f1']:.4f}"
    )

    if (
        best_result is None
        or val_metrics["roc_auc"]
        > best_result["validation_metrics"]["roc_auc"]
    ):
        best_result = result
        best_model = model


# ------------------------------------------------------------
# Ranking
# ------------------------------------------------------------

results = sorted(
    results,
    key=lambda x:
        x["validation_metrics"]["roc_auc"],
    reverse=True,
)

print("\n" + "=" * 78)
print("STAGE 13B RANKING")
print("=" * 78)

print(
    f"{'MODEL':28s} "
    f"{'TRAIN AUC':>10s} "
    f"{'VAL AUC':>10s} "
    f"{'GAP':>10s} "
    f"{'VAL ACC':>10s} "
    f"{'VAL F1':>10s}"
)

for result in results:

    train_auc = (
        result["train_metrics"]["roc_auc"]
    )

    val_auc = (
        result["validation_metrics"]["roc_auc"]
    )

    val_acc = (
        result["validation_metrics"]["accuracy"]
    )

    val_f1 = (
        result["validation_metrics"]["f1"]
    )

    print(
        f"{result['name']:28s} "
        f"{train_auc:10.4f} "
        f"{val_auc:10.4f} "
        f"{result['auc_gap']:10.4f} "
        f"{val_acc:10.4f} "
        f"{val_f1:10.4f}"
    )


# ------------------------------------------------------------
# Save winner
# ------------------------------------------------------------

with open(
    OUTPUT_DIR / "best_random_forest.pkl",
    "wb"
) as file:
    pickle.dump(best_model, file)


with open(
    OUTPUT_DIR / "preprocessor.pkl",
    "wb"
) as file:
    pickle.dump(preprocessor, file)


with open(
    OUTPUT_DIR / "results.json",
    "w"
) as file:
    json.dump(
        results,
        file,
        indent=2,
    )


print("\n" + "=" * 78)
print("WINNER")
print("=" * 78)

print(
    f"Model            : "
    f"{best_result['name']}"
)

print(
    f"Train AUC        : "
    f"{best_result['train_metrics']['roc_auc']:.4f}"
)

print(
    f"Validation AUC   : "
    f"{best_result['validation_metrics']['roc_auc']:.4f}"
)

print(
    f"AUC gap          : "
    f"{best_result['auc_gap']:.4f}"
)

print(
    f"Validation Acc   : "
    f"{best_result['validation_metrics']['accuracy']:.4f}"
)

print(
    f"Validation Prec  : "
    f"{best_result['validation_metrics']['precision']:.4f}"
)

print(
    f"Validation Recall: "
    f"{best_result['validation_metrics']['recall']:.4f}"
)

print(
    f"Validation F1    : "
    f"{best_result['validation_metrics']['f1']:.4f}"
)

print()
print("TEST SET REMAINS LOCKED.")
print("STAGE 13B COMPLETE")
print("=" * 78)
