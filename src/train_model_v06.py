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


DATA_PATH = "data/training_dataset_v06.csv"
MODEL_PATH = "models/random_forest_v06.pkl"

RANDOM_STATE = 42


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


def main():

    print("=" * 40)
    print("BUSHFIRE AI V06 RANDOM FOREST")
    print("=" * 40)

    df = pd.read_csv(DATA_PATH)

    print(f"\nDataset rows: {len(df):,}")

    # Missing vegetation represents locations without a
    # classified vegetation formation.
    df["vegetation_formation"] = (
        df["vegetation_formation"]
        .fillna("Unknown")
    )

    features = (
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    )

    X = df[features]
    y = df["fire"]

    # Each coordinate is treated as one group so the same
    # location cannot leak between train and test datasets.
    groups = (
        df["latitude"].astype(str)
        + "_"
        + df["longitude"].astype(str)
    )

    # --------------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------------

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.15,
        random_state=RANDOM_STATE,
    )

    train_index, test_index = next(
        splitter.split(
            X,
            y,
            groups=groups
        )
    )

    X_train = X.iloc[train_index]
    X_test = X.iloc[test_index]

    y_train = y.iloc[train_index]
    y_test = y.iloc[test_index]

    train_groups = groups.iloc[train_index]
    test_groups = groups.iloc[test_index]

    print("\n" + "=" * 40)
    print("GROUP-AWARE SPLIT")
    print("=" * 40)

    print(
        f"Training rows: "
        f"{len(X_train):,}"
    )

    print(
        f"Test rows: "
        f"{len(X_test):,}"
    )

    overlap = set(train_groups).intersection(
        set(test_groups)
    )

    print(
        f"Location overlap: "
        f"{len(overlap)}"
    )

    # --------------------------------------------------------
    # PREPROCESSING
    # --------------------------------------------------------

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES
            ),
            (
                "vegetation",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES
            ),
        ]
    )

    # --------------------------------------------------------
    # RANDOM FOREST
    # --------------------------------------------------------

    model = RandomForestClassifier(
        n_estimators=500,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    )

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "classifier",
                model
            ),
        ]
    )

    print("\nTraining Random Forest...")

    pipeline.fit(
        X_train,
        y_train
    )

    print("Training complete.")

    # --------------------------------------------------------
    # EVALUATION
    # --------------------------------------------------------

    predictions = pipeline.predict(
        X_test
    )

    probabilities = (
        pipeline.predict_proba(
            X_test
        )[:, 1]
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions
    )

    recall = recall_score(
        y_test,
        predictions
    )

    f1 = f1_score(
        y_test,
        predictions
    )

    auc = roc_auc_score(
        y_test,
        probabilities
    )

    matrix = confusion_matrix(
        y_test,
        predictions
    )

    print("\n" + "=" * 40)
    print("V06 RANDOM FOREST RESULTS")
    print("=" * 40)

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
        f"{auc:.3f}"
    )

    print("\nConfusion Matrix:")
    print(matrix)

    # --------------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------------

    joblib.dump(
        pipeline,
        MODEL_PATH
    )

    print(
        f"\nSaved model to "
        f"{MODEL_PATH}"
    )


if __name__ == "__main__":
    main()