import pandas as pd
import torch
import torch.nn as nn

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

device = torch.device(
    "mps" if torch.backends.mps.is_available()
    else "cpu"
)

print("Using device:", device)

df = pd.read_csv("data/training_dataset_v04.csv")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

print("Dataset shape:", df.shape)
print(
    "Date range:",
    df["date"].min().date(),
    "to",
    df["date"].max().date()
)

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
    "temp_humidity_index",
    "temp_wind_index",
    "dryness_index",
    "vpd",
]

split_index = int(len(df) * 0.8)

train_df = df.iloc[:split_index]
test_df = df.iloc[split_index:]

print("\nTraining rows:", len(train_df))
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

X_train = train_df[features].values
y_train = train_df["fire"].values

X_test = test_df[features].values
y_test = test_df["fire"].values

scaler = StandardScaler()

X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

X_train_tensor = torch.tensor(
    X_train,
    dtype=torch.float32
).to(device)

X_test_tensor = torch.tensor(
    X_test,
    dtype=torch.float32
).to(device)

y_train_tensor = torch.tensor(
    y_train,
    dtype=torch.float32
).reshape(-1, 1).to(device)


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


model = BushfireModel().to(device)

loss_function = nn.BCEWithLogitsLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001
)

epochs = 150

print("\nTraining Bushfire AI v0.3...\n")

for epoch in range(epochs):

    model.train()

    logits = model(X_train_tensor)

    loss = loss_function(
        logits,
        y_train_tensor
    )

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if (epoch + 1) % 10 == 0:
        print(
            f"Epoch {epoch + 1:3d} "
            f"| Loss: {loss.item():.4f}"
        )


model.eval()

with torch.no_grad():

    logits = model(X_test_tensor)

    probabilities = torch.sigmoid(
        logits
    ).cpu().numpy().flatten()

predictions = (
    probabilities >= 0.5
).astype(int)

accuracy = accuracy_score(y_test, predictions)

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
torch.save(
    {
        "model_state_dict": model.state_dict(),
        "features": features,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
    },
    "models/bushfire_model_v04.pth"
)

print("\nModel saved to models/bushfire_model_v04.pth")

print("\n==============================")
print("BUSHFIRE AI v0.4 RESULTS")
print("==============================")

print(f"Accuracy:  {accuracy * 100:.2f}%")
print(f"Precision: {precision * 100:.2f}%")
print(f"Recall:    {recall * 100:.2f}%")
print(f"F1 Score:  {f1 * 100:.2f}%")
print(f"ROC-AUC:   {roc_auc:.3f}")

print("\nConfusion Matrix:")
print(cm)

print("\nFormat:")
print("[[True Negative, False Positive]")
print(" [False Negative, True Positive]]")