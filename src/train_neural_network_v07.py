import copy
import random

import joblib
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
    confusion_matrix,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = "data/training_dataset_v07.csv"

MODEL_PATH = "models/neural_network_v07.pth"
SCALER_PATH = "models/neural_network_v07_scaler.pkl"

RANDOM_SEED = 42

BATCH_SIZE = 128
LEARNING_RATE = 0.001
MAX_EPOCHS = 300
PATIENCE = 25


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


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)


# ============================================================
# DEVICE
# ============================================================

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
else:
    DEVICE = torch.device("cpu")


# ============================================================
# NEURAL NETWORK
# ============================================================

class BushfireNet(nn.Module):

    def __init__(self, input_size):

        super().__init__()

        self.layer1 = nn.Linear(
            input_size,
            64
        )

        self.layer2 = nn.Linear(
            64,
            32
        )

        self.layer3 = nn.Linear(
            32,
            16
        )

        self.output = nn.Linear(
            16,
            1
        )

        self.relu = nn.ReLU()

        self.dropout = nn.Dropout(
            p=0.20
        )


    def forward(self, x):

        x = self.layer1(x)
        x = self.relu(x)
        x = self.dropout(x)

        x = self.layer2(x)
        x = self.relu(x)
        x = self.dropout(x)

        x = self.layer3(x)
        x = self.relu(x)

        x = self.output(x)

        return x


# ============================================================
# EVALUATION
# ============================================================

def evaluate_model(
    model,
    X,
    y,
    label
):

    model.eval()

    with torch.no_grad():

        logits = model(X).squeeze(1)

        probabilities = torch.sigmoid(
            logits
        )

        predictions = (
            probabilities >= 0.5
        ).int()

    y_true = (
        y.detach()
        .cpu()
        .numpy()
        .astype(int)
    )

    y_pred = (
        predictions.detach()
        .cpu()
        .numpy()
    )

    y_prob = (
        probabilities.detach()
        .cpu()
        .numpy()
    )

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )

    auc = roc_auc_score(
        y_true,
        y_prob
    )

    matrix = confusion_matrix(
        y_true,
        y_pred
    )

    print("\n" + "=" * 40)
    print(f"{label} RESULTS")
    print("=" * 40)

    print(
        f"Accuracy:  {accuracy * 100:.2f}%"
    )

    print(
        f"Precision: {precision * 100:.2f}%"
    )

    print(
        f"Recall:    {recall * 100:.2f}%"
    )

    print(
        f"F1 Score:  {f1 * 100:.2f}%"
    )

    print(
        f"ROC-AUC:   {auc:.3f}"
    )

    print("\nConfusion Matrix:")
    print(matrix)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auc": auc,
    }


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 50)
print("BUSHFIRE AI V07 PYTORCH NEURAL NETWORK")
print("=" * 50)

print("\nDevice:", DEVICE)

df = pd.read_csv(
    DATA_PATH
)

print(
    f"Dataset rows: "
    f"{len(df):,}"
)

print(
    f"Matched pairs: "
    f"{df['source_fire_id'].nunique():,}"
)


# ============================================================
# GROUP-AWARE 70 / 15 / 15 SPLIT
# ============================================================

groups = df[
    "source_fire_id"
].astype(str)

split1 = GroupShuffleSplit(
    n_splits=1,
    train_size=0.70,
    random_state=RANDOM_SEED
)

train_index, temp_index = next(
    split1.split(
        df,
        df["fire"],
        groups
    )
)

train_df = (
    df.iloc[train_index]
    .copy()
    .reset_index(drop=True)
)

temp_df = (
    df.iloc[temp_index]
    .copy()
    .reset_index(drop=True)
)


split2 = GroupShuffleSplit(
    n_splits=1,
    train_size=0.50,
    random_state=RANDOM_SEED
)

validation_index, test_index = next(
    split2.split(
        temp_df,
        temp_df["fire"],
        temp_df["source_fire_id"]
    )
)

validation_df = (
    temp_df.iloc[validation_index]
    .copy()
    .reset_index(drop=True)
)

test_df = (
    temp_df.iloc[test_index]
    .copy()
    .reset_index(drop=True)
)


print("\n" + "=" * 50)
print("GROUP-AWARE 70 / 15 / 15 SPLIT")
print("=" * 50)

print(
    f"Train rows:      "
    f"{len(train_df):,} "
    f"({train_df['source_fire_id'].nunique():,} pairs)"
)

print(
    f"Validation rows: "
    f"{len(validation_df):,} "
    f"({validation_df['source_fire_id'].nunique():,} pairs)"
)

print(
    f"Test rows:       "
    f"{len(test_df):,} "
    f"({test_df['source_fire_id'].nunique():,} pairs)"
)


# ============================================================
# PREPARE FEATURES
# ============================================================

X_train = train_df[
    NUMERIC_FEATURES
].astype(float)

X_validation = validation_df[
    NUMERIC_FEATURES
].astype(float)

X_test = test_df[
    NUMERIC_FEATURES
].astype(float)


y_train = (
    train_df["fire"]
    .astype(float)
    .to_numpy()
)

y_validation = (
    validation_df["fire"]
    .astype(float)
    .to_numpy()
)

y_test = (
    test_df["fire"]
    .astype(float)
    .to_numpy()
)


# ============================================================
# NORMALISE FEATURES
# Fit ONLY on training data
# ============================================================

scaler = StandardScaler()

X_train = scaler.fit_transform(
    X_train
)

X_validation = scaler.transform(
    X_validation
)

X_test = scaler.transform(
    X_test
)

joblib.dump(
    scaler,
    SCALER_PATH
)


# ============================================================
# CONVERT TO PYTORCH TENSORS
# ============================================================

X_train_tensor = torch.tensor(
    X_train,
    dtype=torch.float32
)

y_train_tensor = torch.tensor(
    y_train,
    dtype=torch.float32
)

X_validation_tensor = torch.tensor(
    X_validation,
    dtype=torch.float32,
    device=DEVICE
)

y_validation_tensor = torch.tensor(
    y_validation,
    dtype=torch.float32,
    device=DEVICE
)

X_test_tensor = torch.tensor(
    X_test,
    dtype=torch.float32,
    device=DEVICE
)

y_test_tensor = torch.tensor(
    y_test,
    dtype=torch.float32,
    device=DEVICE
)


train_dataset = TensorDataset(
    X_train_tensor,
    y_train_tensor
)

generator = torch.Generator()
generator.manual_seed(
    RANDOM_SEED
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    generator=generator
)


# ============================================================
# CREATE MODEL
# ============================================================

model = BushfireNet(
    input_size=len(NUMERIC_FEATURES)
).to(DEVICE)

loss_function = (
    nn.BCEWithLogitsLoss()
)

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-4
)


print("\nArchitecture:")
print(model)

print(
    "\nTrainable parameters:",
    sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )
)


# ============================================================
# TRAINING
# ============================================================

print("\nTraining neural network...")

best_validation_loss = float(
    "inf"
)

best_state = None
epochs_without_improvement = 0
best_epoch = 0


for epoch in range(
    1,
    MAX_EPOCHS + 1
):

    model.train()

    training_loss = 0.0

    for batch_X, batch_y in train_loader:

        batch_X = batch_X.to(
            DEVICE
        )

        batch_y = batch_y.to(
            DEVICE
        )

        optimizer.zero_grad()

        logits = model(
            batch_X
        ).squeeze(1)

        loss = loss_function(
            logits,
            batch_y
        )

        loss.backward()

        optimizer.step()

        training_loss += (
            loss.item()
            * batch_X.size(0)
        )


    training_loss /= len(
        train_dataset
    )


    model.eval()

    with torch.no_grad():

        validation_logits = model(
            X_validation_tensor
        ).squeeze(1)

        validation_loss = (
            loss_function(
                validation_logits,
                y_validation_tensor
            ).item()
        )


    if (
        validation_loss
        < best_validation_loss
        - 1e-5
    ):

        best_validation_loss = (
            validation_loss
        )

        best_state = copy.deepcopy(
            model.state_dict()
        )

        best_epoch = epoch

        epochs_without_improvement = 0

    else:

        epochs_without_improvement += 1


    if (
        epoch == 1
        or epoch % 10 == 0
    ):

        print(
            f"Epoch {epoch:03d} | "
            f"Train loss: "
            f"{training_loss:.4f} | "
            f"Validation loss: "
            f"{validation_loss:.4f}"
        )


    if (
        epochs_without_improvement
        >= PATIENCE
    ):

        print(
            "\nEarly stopping triggered."
        )

        break


# ============================================================
# RESTORE BEST MODEL
# ============================================================

model.load_state_dict(
    best_state
)

print(
    f"\nBest epoch: {best_epoch}"
)

print(
    f"Best validation loss: "
    f"{best_validation_loss:.4f}"
)


# ============================================================
# VALIDATION
# ============================================================

validation_results = evaluate_model(
    model,
    X_validation_tensor,
    y_validation_tensor,
    "V07 NEURAL NETWORK VALIDATION"
)


# ============================================================
# FINAL TEST
# ============================================================

test_results = evaluate_model(
    model,
    X_test_tensor,
    y_test_tensor,
    "V07 NEURAL NETWORK TEST"
)


# ============================================================
# SAVE MODEL
# ============================================================

torch.save(
    {
        "model_state_dict":
            model.state_dict(),

        "input_size":
            len(NUMERIC_FEATURES),

        "numeric_features":
            NUMERIC_FEATURES,

        "architecture":
            [64, 32, 16],

        "dropout":
            0.20,

        "best_epoch":
            best_epoch,

        "validation_accuracy":
            validation_results[
                "accuracy"
            ],

        "validation_auc":
            validation_results[
                "auc"
            ],

        "test_accuracy":
            test_results[
                "accuracy"
            ],

        "test_auc":
            test_results[
                "auc"
            ],
    },
    MODEL_PATH
)


print(
    f"\nSaved model to "
    f"{MODEL_PATH}"
)

print(
    f"Saved scaler to "
    f"{SCALER_PATH}"
)


print("\nBaseline comparison:")
print(
    "Random Forest validation accuracy: "
    "59.61%"
)

print(
    "Neural Network validation accuracy: "
    f"{validation_results['accuracy'] * 100:.2f}%"
)

print(
    "Neural Network validation ROC-AUC:  "
    f"{validation_results['auc']:.3f}"
)
