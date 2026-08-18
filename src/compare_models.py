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


# ---------------------------------
# LOAD DATA
# ---------------------------------

df = pd.read_csv(
    "data/training_dataset_v02.csv"
)

df["date"] = pd.to_datetime(df["date"])

df = df.sort_values("date").reset_index(drop=True)


# ---------------------------------
# FEATURES
# ---------------------------------

features = [
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
]


# ---------------------------------
# SAME CHRONOLOGICAL SPLIT
# ---------------------------------

split_index = int(len(df) * 0.8)

train_df = df.iloc[:split_index]
test_df = df.iloc[split_index:]

X_train = train_df[features]
y_train = train_df["fire"]

X_test = test_df[features]
y_test = test_df["fire"]


print("Training rows:", len(train_df))
print("Testing rows:", len(test_df))

print(
    "Train period:",
    train_df["date"].min().date(),
    "to",
    train_df["date"].max().date()
)

print(
    "Test period:",
    test_df["date"].min().date(),
    "to",
    test_df["date"].max().date()
)


# ---------------------------------
# RANDOM FOREST
# ---------------------------------

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=8,
    random_state=42,
    class_weight="balanced",
)

print("\nTraining Random Forest...")

model.fit(
    X_train,
    y_train
)


# ---------------------------------
# PREDICTIONS
# ---------------------------------

predictions = model.predict(X_test)

probabilities = model.predict_proba(
    X_test
)[:, 1]


# ---------------------------------
# METRICS
# ---------------------------------

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


print("\n==============================")
print("RANDOM FOREST RESULTS")
print("==============================")

print(f"Accuracy:  {accuracy * 100:.2f}%")
print(f"Precision: {precision * 100:.2f}%")
print(f"Recall:    {recall * 100:.2f}%")
print(f"F1 Score:  {f1 * 100:.2f}%")
print(f"ROC-AUC:   {roc_auc:.3f}")

print("\nConfusion Matrix:")
print(cm)


# ---------------------------------
# FEATURE IMPORTANCE
# ---------------------------------

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

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