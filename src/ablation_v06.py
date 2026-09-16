import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATA_PATH = "data/training_dataset_v06.csv"
RANDOM_STATE = 42


BASE_FEATURES = [
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


def build_model(
    numeric_features,
    categorical_features=None
):

    if categorical_features is None:
        categorical_features = []

    transformers = [
        (
            "numeric",
            "passthrough",
            numeric_features
        )
    ]

    if categorical_features:

        transformers.append(
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                categorical_features
            )
        )

    preprocessor = ColumnTransformer(
        transformers=transformers
    )

    classifier = RandomForestClassifier(
        n_estimators=500,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "classifier",
                classifier
            ),
        ]
    )


def evaluate(
    name,
    model,
    X_train,
    X_test,
    y_train,
    y_test
):

    print("\n" + "=" * 50)
    print(name)
    print("=" * 50)

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    probabilities = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    results = {
        "Experiment": name,
        "Accuracy": accuracy_score(
            y_test,
            predictions
        ),
        "Precision": precision_score(
            y_test,
            predictions
        ),
        "Recall": recall_score(
            y_test,
            predictions
        ),
        "F1": f1_score(
            y_test,
            predictions
        ),
        "ROC_AUC": roc_auc_score(
            y_test,
            probabilities
        ),
    }

    print(
        f"Accuracy:  "
        f"{results['Accuracy'] * 100:.2f}%"
    )

    print(
        f"Precision: "
        f"{results['Precision'] * 100:.2f}%"
    )

    print(
        f"Recall:    "
        f"{results['Recall'] * 100:.2f}%"
    )

    print(
        f"F1:        "
        f"{results['F1'] * 100:.2f}%"
    )

    print(
        f"ROC-AUC:   "
        f"{results['ROC_AUC']:.3f}"
    )

    return results


def main():

    print("=" * 50)
    print("BUSHFIRE AI V06 ABLATION STUDY")
    print("=" * 50)

    df = pd.read_csv(
        DATA_PATH
    )

    df["vegetation_formation"] = (
        df["vegetation_formation"]
        .fillna("Unknown")
    )

    groups = (
        df["latitude"].astype(str)
        + "_"
        + df["longitude"].astype(str)
    )

    y = df["fire"]

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.15,
        random_state=RANDOM_STATE,
    )

    train_index, test_index = next(
        splitter.split(
            df,
            y,
            groups=groups
        )
    )

    y_train = y.iloc[
        train_index
    ]

    y_test = y.iloc[
        test_index
    ]

    print(
        f"\nTraining rows: "
        f"{len(train_index):,}"
    )

    print(
        f"Test rows: "
        f"{len(test_index):,}"
    )

    train_groups = set(
        groups.iloc[train_index]
    )

    test_groups = set(
        groups.iloc[test_index]
    )

    print(
        "Location overlap:",
        len(
            train_groups.intersection(
                test_groups
            )
        )
    )

    experiments = [
        {
            "name": "A - BASE V05 FEATURES",
            "numeric": BASE_FEATURES,
            "categorical": [],
        },
        {
            "name": "B - BASE + ELEVATION",
            "numeric": (
                BASE_FEATURES
                + ["elevation"]
            ),
            "categorical": [],
        },
        {
            "name": "C - BASE + VEGETATION",
            "numeric": BASE_FEATURES,
            "categorical": [
                "vegetation_formation"
            ],
        },
        {
            "name": (
                "D - BASE + ELEVATION "
                "+ VEGETATION"
            ),
            "numeric": (
                BASE_FEATURES
                + ["elevation"]
            ),
            "categorical": [
                "vegetation_formation"
            ],
        },
    ]

    results = []

    for experiment in experiments:

        features = (
            experiment["numeric"]
            + experiment["categorical"]
        )

        X = df[features]

        X_train = X.iloc[
            train_index
        ]

        X_test = X.iloc[
            test_index
        ]

        model = build_model(
            experiment["numeric"],
            experiment["categorical"]
        )

        result = evaluate(
            experiment["name"],
            model,
            X_train,
            X_test,
            y_train,
            y_test
        )

        results.append(
            result
        )

    results_df = pd.DataFrame(
        results
    )

    for column in [
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
    ]:

        results_df[column] = (
            results_df[column]
            * 100
        )

    print("\n" + "=" * 75)
    print("FINAL COMPARISON")
    print("=" * 75)

    print(
        results_df.to_string(
            index=False,
            formatters={
                "Accuracy":
                    lambda x: f"{x:.2f}%",
                "Precision":
                    lambda x: f"{x:.2f}%",
                "Recall":
                    lambda x: f"{x:.2f}%",
                "F1":
                    lambda x: f"{x:.2f}%",
                "ROC_AUC":
                    lambda x: f"{x:.3f}",
            }
        )
    )

    print("\n" + "=" * 75)
    print("ABLATION STUDY COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()
    