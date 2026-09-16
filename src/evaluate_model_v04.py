import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt

from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
)



MODEL_PATH = "models/bushfire_model_v04.pth"
DATA_PATH = "data/training_dataset_v04.csv"


# -----------------------------------
# MODEL ARCHITECTURE
# -----------------------------------

class BushfireModel(nn.Module):

    def __init__(self):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(15, 32),
            nn.ReLU(),

            nn.Linear(32, 16),
            nn.ReLU(),

            nn.Linear(16, 8),
            nn.ReLU(),

            nn.Linear(8, 1),
        )

    def forward(self, x):
        return self.network(x)


# -----------------------------------
# LOAD SAVED CHECKPOINT
# -----------------------------------

checkpoint = torch.load(
    MODEL_PATH,
    map_location="cpu",
    weights_only=False
)

features = checkpoint["features"]

scaler_mean = np.array(
    checkpoint["scaler_mean"]
)

scaler_scale = np.array(
    checkpoint["scaler_scale"]
)

model = BushfireModel()

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()


# -----------------------------------
# LOAD DATASET
# -----------------------------------

df = pd.read_csv(DATA_PATH)

df["date"] = pd.to_datetime(
    df["date"]
)

df = df.sort_values(
    "date"
).reset_index(drop=True)


# -----------------------------------
# SAME CHRONOLOGICAL SPLIT AS V04
# -----------------------------------

split_index = int(
    len(df) * 0.8
)

test_df = df.iloc[
    split_index:
].copy()

X_test = test_df[
    features
].values

y_test = test_df[
    "fire"
].values


# -----------------------------------
# APPLY SAVED SCALER
# -----------------------------------

X_test_scaled = (
    X_test - scaler_mean
) / scaler_scale

X_test_tensor = torch.tensor(
    X_test_scaled,
    dtype=torch.float32
)


# -----------------------------------
# RUN SAVED MODEL
# -----------------------------------

with torch.no_grad():

    logits = model(
        X_test_tensor
    )

    probabilities = torch.sigmoid(
        logits
    ).numpy().flatten()


predictions = (
    probabilities >= 0.5
).astype(int)


# -----------------------------------
# METRICS
# -----------------------------------

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
print("BUSHFIRE AI V04 EVALUATION")
print("==============================")

print(f"Test rows:  {len(test_df)}")
print(f"Accuracy:   {accuracy * 100:.2f}%")
print(f"Precision:  {precision * 100:.2f}%")
print(f"Recall:     {recall * 100:.2f}%")
print(f"F1 Score:   {f1 * 100:.2f}%")
print(f"ROC-AUC:    {roc_auc:.3f}")

print("\nConfusion Matrix:")
print(cm)


# -----------------------------------
# CONFUSION MATRIX VISUAL
# -----------------------------------

fig, ax = plt.subplots(
    figsize=(6, 5)
)

image = ax.imshow(cm)

ax.set_title(
    "Bushfire AI V04 — Confusion Matrix"
)

ax.set_xlabel(
    "Predicted Class"
)

ax.set_ylabel(
    "Actual Class"
)

ax.set_xticks(
    [0, 1],
    labels=[
        "No Fire",
        "Fire"
    ]
)

ax.set_yticks(
    [0, 1],
    labels=[
        "No Fire",
        "Fire"
    ]
)


for i in range(2):
    for j in range(2):

        ax.text(
            j,
            i,
            cm[i, j],
            ha="center",
            va="center",
            fontsize=18
        )


plt.tight_layout()

plt.show()

# -----------------------------------
# ROC CURVE
# -----------------------------------

fpr, tpr, thresholds = roc_curve(
    y_test,
    probabilities
)

fig, ax = plt.subplots(
    figsize=(7, 6)
)

ax.plot(
    fpr,
    tpr,
    linewidth=2,
    label=f"V04 (AUC = {roc_auc:.3f})"
)

ax.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    linewidth=1,
    label="Random classifier"
)

ax.set_title(
    "Bushfire AI V04 — ROC Curve"
)

ax.set_xlabel(
    "False Positive Rate"
)

ax.set_ylabel(
    "True Positive Rate (Recall)"
)

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

ax.grid(
    alpha=0.25
)

ax.legend()

plt.tight_layout()

plt.show()

# -----------------------------------
# THRESHOLD ANALYSIS
# -----------------------------------

print("\n==============================")
print("THRESHOLD ANALYSIS")
print("==============================")

threshold_values = [
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
]

for threshold in threshold_values:

    threshold_predictions = (
        probabilities >= threshold
    ).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        threshold_predictions
    ).ravel()

    threshold_precision = precision_score(
        y_test,
        threshold_predictions,
        zero_division=0
    )

    threshold_recall = recall_score(
        y_test,
        threshold_predictions,
        zero_division=0
    )

    threshold_f1 = f1_score(
        y_test,
        threshold_predictions,
        zero_division=0
    )

    print(
        f"\nThreshold: {threshold:.0%}"
    )

    print(
        f"Fire detected: {tp}"
    )

    print(
        f"Fire missed:   {fn}"
    )

    print(
        f"False alarms:  {fp}"
    )

    print(
        f"Precision:     "
        f"{threshold_precision * 100:.2f}%"
    )

    print(
        f"Recall:        "
        f"{threshold_recall * 100:.2f}%"
    )

    print(
        f"F1 Score:      "
        f"{threshold_f1 * 100:.2f}%"
    )

# -----------------------------------
# THRESHOLD METRIC VISUALISATION
# -----------------------------------

threshold_values = np.array([
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
])

precision_values = []
recall_values = []
f1_values = []

missed_fire_values = []
false_alarm_values = []


for threshold in threshold_values:

    threshold_predictions = (
        probabilities >= threshold
    ).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        threshold_predictions
    ).ravel()

    precision_values.append(
        precision_score(
            y_test,
            threshold_predictions,
            zero_division=0
        )
    )

    recall_values.append(
        recall_score(
            y_test,
            threshold_predictions,
            zero_division=0
        )
    )

    f1_values.append(
        f1_score(
            y_test,
            threshold_predictions,
            zero_division=0
        )
    )

    missed_fire_values.append(fn)
    false_alarm_values.append(fp)


# -----------------------------------
# CHART 1
# Precision / Recall / F1
# -----------------------------------

plt.figure(
    figsize=(9, 6)
)

plt.plot(
    threshold_values,
    precision_values,
    marker="o",
    label="Precision"
)

plt.plot(
    threshold_values,
    recall_values,
    marker="o",
    label="Recall"
)

plt.plot(
    threshold_values,
    f1_values,
    marker="o",
    label="F1 Score"
)

plt.axvline(
    x=0.50,
    linestyle="--",
    label="Current threshold (50%)"
)

plt.title(
    "Bushfire AI V04 — Threshold Performance"
)

plt.xlabel(
    "Decision Threshold"
)

plt.ylabel(
    "Score"
)

plt.xticks(
    threshold_values,
    [
        "20%",
        "30%",
        "40%",
        "50%",
        "60%",
        "70%",
        "80%",
    ]
)

plt.ylim(
    0,
    1.05
)

plt.grid(
    alpha=0.25
)

plt.legend()

plt.tight_layout()

plt.show()

# -----------------------------------
# CHART 2
# MISSED FIRES VS FALSE ALARMS
# -----------------------------------

plt.figure(
    figsize=(9, 6)
)

plt.plot(
    threshold_values,
    missed_fire_values,
    marker="o",
    label="Missed Fires"
)

plt.plot(
    threshold_values,
    false_alarm_values,
    marker="o",
    label="False Alarms"
)

plt.axvline(
    x=0.50,
    linestyle="--",
    label="Current threshold (50%)"
)

plt.title(
    "Bushfire AI V04 — Error Trade-off"
)

plt.xlabel(
    "Decision Threshold"
)

plt.ylabel(
    "Number of Cases"
)

plt.xticks(
    threshold_values,
    [
        "20%",
        "30%",
        "40%",
        "50%",
        "60%",
        "70%",
        "80%",
    ]
)

plt.grid(
    alpha=0.25
)

plt.legend()

plt.tight_layout()

plt.show()