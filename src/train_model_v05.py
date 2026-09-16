import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler

from torch.utils.data import (
    TensorDataset,
    DataLoader,
)

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = "data/training_dataset_v05.csv"

RANDOM_SEED = 42

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(
    RANDOM_SEED
)

np.random.seed(
    RANDOM_SEED
)

torch.manual_seed(
    RANDOM_SEED
)


# ============================================================
# MODEL FEATURES
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
# LOAD DATASET
# ============================================================

df = pd.read_csv(
    DATASET_PATH
)

print("\n==============================")
print("BUSHFIRE AI V05 TRAINING")
print("==============================")

print(
    f"\nDataset rows: "
    f"{len(df):,}"
)

print(
    f"Features: "
    f"{len(FEATURES)}"
)


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = (
    FEATURES
    + [
        TARGET,
        GROUP_COLUMN,
    ]
)

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise RuntimeError(
        "Dataset is missing required columns: "
        + ", ".join(missing_columns)
    )


# ============================================================
# GROUP-AWARE TRAIN / TEMP SPLIT
# ============================================================

groups = df[
    GROUP_COLUMN
]

group_split = GroupShuffleSplit(
    n_splits=1,
    train_size=TRAIN_RATIO,
    random_state=RANDOM_SEED,
)

train_indices, temp_indices = next(
    group_split.split(
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


# ============================================================
# GROUP-AWARE VALIDATION / TEST SPLIT
# ============================================================

validation_fraction_of_temp = (
    VALIDATION_RATIO
    / (
        VALIDATION_RATIO
        + TEST_RATIO
    )
)

temp_groups = temp_df[
    GROUP_COLUMN
]

validation_test_split = GroupShuffleSplit(
    n_splits=1,
    train_size=validation_fraction_of_temp,
    random_state=RANDOM_SEED,
)

validation_indices, test_indices = next(
    validation_test_split.split(
        temp_df,
        groups=temp_groups
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
# VERIFY GROUP ISOLATION
# ============================================================

train_groups = set(
    train_df[GROUP_COLUMN]
)

validation_groups = set(
    validation_df[GROUP_COLUMN]
)

test_groups = set(
    test_df[GROUP_COLUMN]
)

train_validation_overlap = (
    train_groups
    & validation_groups
)

train_test_overlap = (
    train_groups
    & test_groups
)

validation_test_overlap = (
    validation_groups
    & test_groups
)

if (
    train_validation_overlap
    or train_test_overlap
    or validation_test_overlap
):
    raise RuntimeError(
        "Data leakage detected between dataset splits."
    )


# ============================================================
# REPORT SPLITS
# ============================================================

print("\n==============================")
print("GROUP-AWARE DATA SPLIT")
print("==============================")

print(
    f"\nTraining rows:   "
    f"{len(train_df):,}"
)

print(
    f"Validation rows: "
    f"{len(validation_df):,}"
)

print(
    f"Test rows:       "
    f"{len(test_df):,}"
)

print(
    f"\nTraining groups:   "
    f"{len(train_groups):,}"
)

print(
    f"Validation groups: "
    f"{len(validation_groups):,}"
)

print(
    f"Test groups:       "
    f"{len(test_groups):,}"
)

print(
    "\nGroup overlap:"
)

print(
    "Train / Validation:",
    len(train_validation_overlap)
)

print(
    "Train / Test:",
    len(train_test_overlap)
)

print(
    "Validation / Test:",
    len(validation_test_overlap)
)


# ============================================================
# CLASS BALANCE
# ============================================================

print("\nClass balance:")

print("\nTraining:")
print(
    train_df[
        TARGET
    ].value_counts()
)

print("\nValidation:")
print(
    validation_df[
        TARGET
    ].value_counts()
)

print("\nTest:")
print(
    test_df[
        TARGET
    ].value_counts()
)


# ============================================================
# PREPARE FEATURES
# ============================================================

X_train = train_df[
    FEATURES
].to_numpy(
    dtype=np.float32
)

X_validation = validation_df[
    FEATURES
].to_numpy(
    dtype=np.float32
)

X_test = test_df[
    FEATURES
].to_numpy(
    dtype=np.float32
)

y_train = train_df[
    TARGET
].to_numpy(
    dtype=np.float32
)

y_validation = validation_df[
    TARGET
].to_numpy(
    dtype=np.float32
)

y_test = test_df[
    TARGET
].to_numpy(
    dtype=np.float32
)


# ============================================================
# SCALE FEATURES
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


# ============================================================
# CONVERT TO PYTORCH TENSORS
# ============================================================

X_train_tensor = torch.tensor(
    X_train,
    dtype=torch.float32
)

X_validation_tensor = torch.tensor(
    X_validation,
    dtype=torch.float32
)

X_test_tensor = torch.tensor(
    X_test,
    dtype=torch.float32
)

y_train_tensor = torch.tensor(
    y_train,
    dtype=torch.float32
).unsqueeze(1)

y_validation_tensor = torch.tensor(
    y_validation,
    dtype=torch.float32
).unsqueeze(1)

y_test_tensor = torch.tensor(
    y_test,
    dtype=torch.float32
).unsqueeze(1)


print("\nTensor shapes:")

print(
    "X train:",
    X_train_tensor.shape
)

print(
    "y train:",
    y_train_tensor.shape
)

print(
    "X validation:",
    X_validation_tensor.shape
)

print(
    "X test:",
    X_test_tensor.shape
)

# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

print(
    "\nUsing device:",
    device
)


# ============================================================
# DATA LOADERS
# ============================================================

BATCH_SIZE = 128

train_dataset = TensorDataset(
    X_train_tensor,
    y_train_tensor
)

validation_dataset = TensorDataset(
    X_validation_tensor,
    y_validation_tensor
)

test_dataset = TensorDataset(
    X_test_tensor,
    y_test_tensor
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)

validation_loader = DataLoader(
    validation_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)


# ============================================================
# MODEL
# ============================================================

class BushfireModelV05(nn.Module):

    def __init__(self):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(15, 64),
            nn.ReLU(),
            nn.Dropout(0.20),

            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.15),

            nn.Linear(32, 16),
            nn.ReLU(),

            nn.Linear(16, 1),
        )

    def forward(self, x):
        return self.network(x)


model = BushfireModelV05().to(
    device
)


# ============================================================
# TRAINING CONFIGURATION
# ============================================================

loss_function = nn.BCEWithLogitsLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=0.001,
    weight_decay=0.0001
)

MAX_EPOCHS = 200
EARLY_STOPPING_PATIENCE = 20

best_validation_loss = float(
    "inf"
)

best_model_state = None

epochs_without_improvement = 0

train_loss_history = []
validation_loss_history = []


# ============================================================
# TRAINING LOOP
# ============================================================

print("\n==============================")
print("TRAINING V05")
print("==============================\n")


for epoch in range(
    1,
    MAX_EPOCHS + 1
):

    # -----------------------------------
    # TRAIN
    # -----------------------------------

    model.train()

    total_train_loss = 0.0

    for X_batch, y_batch in train_loader:

        X_batch = X_batch.to(
            device
        )

        y_batch = y_batch.to(
            device
        )

        optimizer.zero_grad()

        logits = model(
            X_batch
        )

        loss = loss_function(
            logits,
            y_batch
        )

        loss.backward()

        optimizer.step()

        total_train_loss += (
            loss.item()
            * X_batch.size(0)
        )


    average_train_loss = (
        total_train_loss
        / len(train_loader.dataset)
    )


    # -----------------------------------
    # VALIDATION
    # -----------------------------------

    model.eval()

    total_validation_loss = 0.0

    with torch.no_grad():

        for (
            X_batch,
            y_batch
        ) in validation_loader:

            X_batch = X_batch.to(
                device
            )

            y_batch = y_batch.to(
                device
            )

            logits = model(
                X_batch
            )

            loss = loss_function(
                logits,
                y_batch
            )

            total_validation_loss += (
                loss.item()
                * X_batch.size(0)
            )


    average_validation_loss = (
        total_validation_loss
        / len(validation_loader.dataset)
    )


    train_loss_history.append(
        average_train_loss
    )

    validation_loss_history.append(
        average_validation_loss
    )


    # -----------------------------------
    # PRINT PROGRESS
    # -----------------------------------

    print(
        f"Epoch {epoch:3d} "
        f"| Train Loss: "
        f"{average_train_loss:.4f} "
        f"| Val Loss: "
        f"{average_validation_loss:.4f}"
    )


    # -----------------------------------
    # EARLY STOPPING
    # -----------------------------------

    if (
        average_validation_loss
        < best_validation_loss
    ):

        best_validation_loss = (
            average_validation_loss
        )

        best_model_state = {
            key:
                value.detach()
                .cpu()
                .clone()
            for key, value
            in model.state_dict().items()
        }

        epochs_without_improvement = 0

    else:

        epochs_without_improvement += 1


    if (
        epochs_without_improvement
        >= EARLY_STOPPING_PATIENCE
    ):

        print(
            "\nEarly stopping triggered."
        )

        print(
            f"Best validation loss: "
            f"{best_validation_loss:.4f}"
        )

        break


# ============================================================
# RESTORE BEST MODEL
# ============================================================

if best_model_state is None:
    raise RuntimeError(
        "No best model state was recorded."
    )

model.load_state_dict(
    best_model_state
)

model = model.to(
    device
)

model.eval()


# ============================================================
# TEST SET EVALUATION
# ============================================================

test_probabilities = []
test_predictions = []
test_targets = []


with torch.no_grad():

    for (
        X_batch,
        y_batch
    ) in test_loader:

        X_batch = X_batch.to(
            device
        )

        logits = model(
            X_batch
        )

        probabilities = torch.sigmoid(
            logits
        )

        predictions = (
            probabilities
            >= 0.5
        ).int()

        test_probabilities.extend(
            probabilities
            .cpu()
            .numpy()
            .flatten()
        )

        test_predictions.extend(
            predictions
            .cpu()
            .numpy()
            .flatten()
        )

        test_targets.extend(
            y_batch
            .numpy()
            .flatten()
        )


test_probabilities = np.array(
    test_probabilities
)

test_predictions = np.array(
    test_predictions
)

test_targets = np.array(
    test_targets
)


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    test_targets,
    test_predictions
)

precision = precision_score(
    test_targets,
    test_predictions,
    zero_division=0
)

recall = recall_score(
    test_targets,
    test_predictions,
    zero_division=0
)

f1 = f1_score(
    test_targets,
    test_predictions,
    zero_division=0
)

roc_auc = roc_auc_score(
    test_targets,
    test_probabilities
)

cm = confusion_matrix(
    test_targets,
    test_predictions
)


print("\n==============================")
print("BUSHFIRE AI V05 RESULTS")
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
# SAVE V05 CHECKPOINT
# ============================================================

checkpoint = {
    "model_state_dict":
        model.state_dict(),

    "features":
        FEATURES,

    "scaler_mean":
        scaler.mean_,

    "scaler_scale":
        scaler.scale_,

    "train_loss_history":
        train_loss_history,

    "validation_loss_history":
        validation_loss_history,

    "accuracy":
        accuracy,

    "precision":
        precision,

    "recall":
        recall,

    "f1":
        f1,

    "roc_auc":
        roc_auc,

    "confusion_matrix":
        cm,

    "architecture":
        [15, 64, 32, 16, 1],

    "batch_size":
        BATCH_SIZE,

    "random_seed":
        RANDOM_SEED,
}


torch.save(
    checkpoint,
    "models/bushfire_model_v05.pth"
)

print(
    "\nSaved model to "
    "models/bushfire_model_v05.pth"
)