import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import GroupShuffleSplit


DATA_PATH = "data/training_dataset_v06_control_4995.csv"
MODEL_PATH = "models/random_forest_v06_control.pkl"

RANDOM_STATE = 42

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15

GROUP_COLUMN = "source_fire_id"


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
    "vegetation_formation",
]


def evaluate(name, pipeline, X, y):

    predictions = pipeline.predict(X)
    probabilities = pipeline.predict_proba(X)[:, 1]

    accuracy = accuracy_score(y, predictions)
    precision = precision_score(y, predictions)
    recall = recall_score(y, predictions)
    f1 = f1_score(y, predictions)
    auc = roc_auc_score(y, probabilities)
    matrix = confusion_matrix(y, predictions)

    print("\n" + "=" * 40)
    print(f"{name} RESULTS")
    print("=" * 40)

    print(f"Accuracy:  {accuracy * 100:.2f}%")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall:    {recall * 100:.2f}%")
    print(f"F1 Score:  {f1 * 100:.2f}%")
    print(f"ROC-AUC:   {auc:.3f}")

    print("\nConfusion Matrix:")
    print(matrix)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": auc,
    }


def main():

    print("=" * 45)
    print("BUSHFIRE AI V06 CONTROL RANDOM FOREST")
    print("=" * 45)

    df = pd.read_csv(DATA_PATH)

    print(f"\nDataset rows: {len(df):,}")
    print(
        f"Matched pairs: "
        f"{df[GROUP_COLUMN].nunique():,}"
    )

    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES

    # --------------------------------------------------------
    # TRAIN / TEMP SPLIT
    # --------------------------------------------------------

    first_split = GroupShuffleSplit(
        n_splits=1,
        train_size=TRAIN_RATIO,
        random_state=RANDOM_STATE,
    )

    train_idx, temp_idx = next(
        first_split.split(
            df,
            groups=df[GROUP_COLUMN],
        )
    )

    train_df = df.iloc[train_idx].copy()
    temp_df = df.iloc[temp_idx].copy()

    # --------------------------------------------------------
    # VALIDATION / TEST SPLIT
    # --------------------------------------------------------

    validation_fraction = (
        VALIDATION_RATIO
        / (VALIDATION_RATIO + TEST_RATIO)
    )

    second_split = GroupShuffleSplit(
        n_splits=1,
        train_size=validation_fraction,
        random_state=RANDOM_STATE,
    )

    validation_idx, test_idx = next(
        second_split.split(
            temp_df,
            groups=temp_df[GROUP_COLUMN],
        )
    )

    validation_df = (
        temp_df.iloc[validation_idx].copy()
    )

    test_df = (
        temp_df.iloc[test_idx].copy()
    )

    # --------------------------------------------------------
    # VERIFY GROUP ISOLATION
    # --------------------------------------------------------

    train_groups = set(train_df[GROUP_COLUMN])
    validation_groups = set(
        validation_df[GROUP_COLUMN]
    )
    test_groups = set(test_df[GROUP_COLUMN])

    train_validation_overlap = (
        train_groups & validation_groups
    )

    train_test_overlap = (
        train_groups & test_groups
    )

    validation_test_overlap = (
        validation_groups & test_groups
    )

    print("\n" + "=" * 45)
    print("GROUP-AWARE 70 / 15 / 15 SPLIT")
    print("=" * 45)

    print(
        f"Train rows:      {len(train_df):,} "
        f"({train_df[GROUP_COLUMN].nunique():,} pairs)"
    )

    print(
        f"Validation rows: {len(validation_df):,} "
        f"({validation_df[GROUP_COLUMN].nunique():,} pairs)"
    )

    print(
        f"Test rows:       {len(test_df):,} "
        f"({test_df[GROUP_COLUMN].nunique():,} pairs)"
    )

    print(
        f"\nTrain/validation overlap: "
        f"{len(train_validation_overlap)}"
    )

    print(
        f"Train/test overlap:       "
        f"{len(train_test_overlap)}"
    )

    print(
        f"Validation/test overlap:  "
        f"{len(validation_test_overlap)}"
    )

    if (
        train_validation_overlap
        or train_test_overlap
        or validation_test_overlap
    ):
        raise RuntimeError(
            "Matched-pair leakage detected."
        )

    print("\nClass distributions:")

    print(
        "Train:",
        train_df["fire"]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    print(
        "Validation:",
        validation_df["fire"]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    print(
        "Test:",
        test_df["fire"]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    X_train = train_df[features]
    y_train = train_df["fire"]

    X_validation = validation_df[features]
    y_validation = validation_df["fire"]

    X_test = test_df[features]
    y_test = test_df["fire"]

    # --------------------------------------------------------
    # PREPROCESSING
    # --------------------------------------------------------

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
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    # --------------------------------------------------------
    # RANDOM FOREST BASELINE
    # --------------------------------------------------------

    classifier = RandomForestClassifier(
        n_estimators=500,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )

    print("\nTraining V07 Random Forest...")

    pipeline.fit(
        X_train,
        y_train,
    )

    print("Training complete.")

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    validation_metrics = evaluate(
        "V06 CONTROL VALIDATION",
        pipeline,
        X_validation,
        y_validation,
    )

    # --------------------------------------------------------
    # TEST
    # --------------------------------------------------------

    test_metrics = evaluate(
        "V06 CONTROL TEST",
        pipeline,
        X_test,
        y_test,
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    joblib.dump(
        pipeline,
        MODEL_PATH,
    )

    print(
        f"\nSaved model to {MODEL_PATH}"
    )

    print("\nBaseline summary:")
    print(
        f"Validation accuracy: "
        f"{validation_metrics['accuracy'] * 100:.2f}%"
    )
    print(
        f"Validation ROC-AUC:  "
        f"{validation_metrics['roc_auc']:.3f}"
    )
    print(
        f"Test accuracy:       "
        f"{test_metrics['accuracy'] * 100:.2f}%"
    )
    print(
        f"Test ROC-AUC:        "
        f"{test_metrics['roc_auc']:.3f}"
    )


if __name__ == "__main__":
    main()
