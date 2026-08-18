import pandas as pd
import torch
import torch.nn as nn

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# -------------------------
# DEVICE
# -------------------------

device = torch.device(
    "mps" if torch.backends.mps.is_available()
    else "cpu"
)

print("Using device:", device)


# -------------------------
# LOAD DATA
# -------------------------

df = pd.read_csv("data/training_dataset_v02.csv")

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

X = df[features].values
y = df["fire"].values


# -------------------------
# TRAIN / TEST SPLIT
# -------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# -------------------------
# SCALE FEATURES
# -------------------------

scaler = StandardScaler()

X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)


# -------------------------
# CONVERT TO TENSORS
# -------------------------

X_train = torch.tensor(
    X_train,
    dtype=torch.float32
).to(device)

X_test = torch.tensor(
    X_test,
    dtype=torch.float32
).to(device)

y_train = torch.tensor(
    y_train,
    dtype=torch.float32
).reshape(-1, 1).to(device)

y_test = torch.tensor(
    y_test,
    dtype=torch.float32
).reshape(-1, 1).to(device)


# -------------------------
# NEURAL NETWORK
# -------------------------

class BushfireModel(nn.Module):

    def __init__(self):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(11, 16),
            nn.ReLU(),

            nn.Linear(16, 8),
            nn.ReLU(),

            nn.Linear(8, 1)
        )

    def forward(self, x):
        return self.network(x)


model = BushfireModel().to(device)


# -------------------------
# TRAINING SETUP
# -------------------------

loss_function = nn.BCEWithLogitsLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001
)


# -------------------------
# TRAIN
# -------------------------

epochs = 100

print("\nTraining neural network...\n")

for epoch in range(epochs):

    model.train()

    predictions = model(X_train)

    loss = loss_function(
        predictions,
        y_train
    )

    optimizer.zero_grad()

    loss.backward()

    optimizer.step()

    if (epoch + 1) % 10 == 0:
        print(
            f"Epoch {epoch + 1:3d} | "
            f"Loss: {loss.item():.4f}"
        )


# -------------------------
# TEST
# -------------------------

model.eval()

with torch.no_grad():

    logits = model(X_test)

    probabilities = torch.sigmoid(logits)

    predictions = (
        probabilities >= 0.5
    ).float()

    accuracy = (
        predictions == y_test
    ).float().mean()


print("\n----------------------------")
print("TEST RESULTS")
print("----------------------------")

print(
    f"Accuracy: "
    f"{accuracy.item() * 100:.2f}%"
)

print("\nPredictions:")

for probability, actual in zip(
    probabilities.cpu(),
    y_test.cpu()
):

    print(
        f"Predicted risk: "
        f"{probability.item() * 100:5.1f}% "
        f"| Actual: {int(actual.item())}"
    )