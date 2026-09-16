import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import GroupShuffleSplit


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = "data/training_dataset_v05.csv"

RANDOM_SEED = 42

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15


# ============================================================
# FEATURES
# ============================================================

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
]

TARGET = "fire"
GROUP_COLUMN = "source_fire_id"


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(
    DATASET_PATH
)


# ============================================================
# SAME GROUP-AWARE SPLIT AS V05
# ============================================================

groups = df[
    GROUP_COLUMN
]

first_split = GroupShuffleSplit(
    n_splits=1,
    train_size=TRAIN_RATIO,
    random_state=RANDOM_SEED,
)

train_indices, temp_indices = next(
    first_split.split(
        df,
        groups=groups
    )
)

train_df = (
    df
    .iloc[train_indices]
    .copy()
)

temp_df = (
    df
    .iloc[temp_indices]
    .copy()
)


validation_fraction = (
    VALIDATION_RATIO
    /
    (
        VALIDATION_RATIO
        + TEST_RATIO
    )
)

second_split = GroupShuffleSplit(
    n_splits=1,
    train_size=validation_fraction,
    random_state=RANDOM_SEED,
)

validation_indices, test_indices = next(
    second_split.split(
        temp_df,
        groups=temp_df[
            GROUP_COLUMN
        ]
    )
)

validation_df = (
    temp_df
    .iloc[validation_indices]
    .copy()
)

test_df = (
    temp_df
    .iloc[test_indices]
    .copy()
)


# ============================================================
# PREPARE DATA
# ============================================================

X_train = train_df[
    FEATURES
].to_numpy()

y_train = train_df[
    TARGET
].to_numpy()

X_validation = validation_df[
    FEATURES
].to_numpy()

y_validation = validation_df[
    TARGET
].to_numpy()

X_test = test_df[
    FEATURES
].to_numpy()

y_test = test_df[
    TARGET
].to_numpy()


# ============================================================
# RANDOM FOREST
# ============================================================

print("\n==============================")
print("TRAINING RANDOM FOREST V05")
print("==============================\n")

model = RandomForestClassifier(
    n_estimators=500,
    max_depth=None,
    min_samples_split=4,
    min_samples_leaf=2,
    max_features="sqrt",
    class_weight="balanced",
    random_state=RANDOM_SEED,
    n_jobs=-1,
)

model.fit(
    X_train,
    y_train
)


# ============================================================
# TEST EVALUATION
# ============================================================

probabilities = model.predict_proba(
    X_test
)[:, 1]

predictions = (
    probabilities >= 0.5
).astype(int)


accuracy = accuracy_score(
    y_test,
    predictions
)

precision = precision_score(
    y_test,
    predictions,
    zero_division=0
)

recall = recall_score(
    y_test,
    predictions,
    zero_division=0
)

f1 = f1_score(
    y_test,
    predictions,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    probabilities
)

cm = confusion_matrix(
    y_test,
    predictions
)


print("==============================")
print("RANDOM FOREST V05 RESULTS")
print("==============================")

print(
    f"Accuracy:  "
    f"{accuracy * 100:.2f}%"
)

print(
    f"Precision: "
    f"{precision * 100:.2f}%"
)

print(
    f"Recall:    "
    f"{recall * 100:.2f}%"
)

print(
    f"F1 Score:  "
    f"{f1 * 100:.2f}%"
)

print(
    f"ROC-AUC:   "
    f"{roc_auc:.3f}"
)

print(
    "\nConfusion Matrix:"
)

print(
    cm
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame(
    {
        "feature":
            FEATURES,

        "importance":
            model.feature_importances_,
    }
)

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\n==============================")
print("FEATURE IMPORTANCE")
print("==============================")

print(
    importance.to_string(
        index=False
    )
)