import pandas as pd
import argparse
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
PAYLOAD_THRESHOLD = 200
FREQ_THRESHOLD = 100
VOLUME_THRESHOLD = 7500

def apply_dohxp_detection(row):
    return int(
        row["avg_packet_size"] > PAYLOAD_THRESHOLD or
        row["frequency"] > FREQ_THRESHOLD or
        row["volume_rate"] > VOLUME_THRESHOLD
    )

# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument("--csvs", nargs="+", required=True, help="List of paths to CSV files")
args = parser.parse_args()

# Read and concatenate CSVs
dfs = []
for csv_path in args.csvs:
    print(f"Reading: {csv_path}")
    df = pd.read_csv(csv_path)
    dfs.append(df)

if not dfs:
    raise ValueError("No valid CSV files found.")

df_all = pd.concat(dfs, ignore_index=True)

# Filter on Benign / Malicious
df_filtered = df_all[df_all["Label"].isin(["Benign", "Malicious"])].copy()
df_filtered["Label"] = df_filtered["Label"].map({"Benign": 0, "Malicious": 1})

# Create DoHxP features
df_filtered["avg_packet_size"] = df_filtered["FlowBytesSent"] / df_filtered["Duration"]
df_filtered["frequency"] = df_filtered["FlowBytesSent"] / df_filtered["PacketTimeMedian"]
df_filtered["volume_rate"] = df_filtered["FlowSentRate"]

# Cleanup
df_filtered = df_filtered.replace([float("inf"), -float("inf")], pd.NA).dropna()

# Features & Labels
X = df_filtered[["avg_packet_size", "frequency", "volume_rate"]]
y = df_filtered["Label"]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Evaluation
y_pred = clf.predict(X_test)
print("Test results:\n")
print(classification_report(y_test, y_pred, target_names=["Benign", "Malicious"]))
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Benign", "Malicious"])
disp.plot(cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.savefig("confusion_matrix.png")
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

ax.scatter(
    X_test["avg_packet_size"],
    X_test["frequency"],
    X_test["volume_rate"],
    c=y_test,
    cmap='coolwarm',
    alpha=0.6
)

ax.set_xlabel("avg_packet_size")
ax.set_ylabel("frequency")
ax.set_zlabel("volume_rate")
ax.set_title("3D Flow Representation")
plt.savefig("3d_representation.png")

# Create test DataFrame for easier visualization
df_test = X_test.copy()
df_test["true_label"] = y_test.values
df_test["predicted_label"] = y_pred

# False positives
fp = df_test[(df_test["true_label"] == 0) & (df_test["predicted_label"] == 1)]

# False negatives
fn = df_test[(df_test["true_label"] == 1) & (df_test["predicted_label"] == 0)]

# Display
plt.figure(figsize=(10, 6))

# FP in red
plt.scatter(fp["avg_packet_size"], fp["frequency"], color='red', label="False positives (Benign → Malicious)", alpha=0.7)

# FN in blue
plt.scatter(fn["avg_packet_size"], fn["frequency"], color='blue', label="False negatives (Malicious → Benign)", alpha=0.7)

plt.xlabel("avg_packet_size")
plt.ylabel("frequency")
plt.title("False positives and false negatives")
plt.legend()
plt.grid(True)
plt.savefig("false_positives_negatives.png")

# Add predictions to original DataFrame
df_filtered["predicted_label"] = clf.predict(X)

# False negatives: true label = 1 (malicious), prediction = 0 (benign)
false_negatives = df_filtered[
    (df_filtered["Label"] == 1) & (df_filtered["predicted_label"] == 0)
]

print(f"False negatives detected: {len(false_negatives)}")

# Display some examples
print(false_negatives[[
    "SourceIP", "DestinationIP", "SourcePort", "DestinationPort",
    "avg_packet_size", "frequency", "volume_rate", "Label", "predicted_label"
]].head())


# Feature importance
importances = clf.feature_importances_
features = ["avg_packet_size", "frequency", "volume_rate"]
print("\nFeature importance:")
for f, imp in zip(features, importances):
    print(f"  {f}: {imp:.4f}")
train_df = X_train.copy()
train_df["Label"] = y_train.values
test_df = X_test.copy()
test_df["Label"] = y_test.values

train_df.to_csv("train.csv", index=False)
test_df.to_csv("test.csv", index=False)
X_test_dohxp = X_test.copy()
X_test_dohxp["true_label"] = y_test.values
X_test_dohxp["dohxp_pred"] = X_test_dohxp.apply(apply_dohxp_detection, axis=1)
print("DoHxP performance on test set:\n")
print(classification_report(X_test_dohxp["true_label"], X_test_dohxp["dohxp_pred"], target_names=["Benign", "Malicious"]))
fp_dohxp = X_test_dohxp[(X_test_dohxp["true_label"] == 0) & (X_test_dohxp["dohxp_pred"] == 1)]
fn_dohxp = X_test_dohxp[(X_test_dohxp["true_label"] == 1) & (X_test_dohxp["dohxp_pred"] == 0)]

print(f"DoHxP false positives: {len(fp_dohxp)}")
print(f"DoHxP false negatives: {len(fn_dohxp)}")
