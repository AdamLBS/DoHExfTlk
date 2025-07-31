import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# === Configuration ===
DATA_PATH = "/data"
OUTPUT_PATH = "/output"
PAYLOAD_THRESHOLD = 200
FREQ_THRESHOLD = 100
VOLUME_THRESHOLD = 7500

def apply_dohxp(row):
    return int(
        row["avg_packet_size"] > PAYLOAD_THRESHOLD or
        row["frequency"] > FREQ_THRESHOLD or
        row["volume_rate"] > VOLUME_THRESHOLD
    )

def load_and_prepare():
    benign = pd.read_csv(os.path.join(DATA_PATH, "l2-benign.csv"))
    malicious = pd.read_csv(os.path.join(DATA_PATH, "l2-malicious.csv"))

    df = pd.concat([benign, malicious], ignore_index=True)
    df = df[df["Label"].isin(["Benign", "Malicious"])]
    df["Label"] = df["Label"].map({"Benign": 0, "Malicious": 1})

    # Feature engineering
    df["avg_packet_size"] = df["FlowBytesSent"] / df["Duration"]
    df["frequency"] = df["FlowBytesSent"] / df["PacketTimeMedian"]
    df["volume_rate"] = df["FlowSentRate"]

    df = df.replace([float("inf"), -float("inf")], pd.NA).dropna()
    return df

def train_model(df):
    X = df[["avg_packet_size", "frequency", "volume_rate"]]
    y = df["Label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluation
    y_pred = clf.predict(X_test)
    print("✅ RandomForest Results:")
    print(classification_report(y_test, y_pred, target_names=["Benign", "Malicious"]))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Benign", "Malicious"])
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Confusion Matrix - RandomForest")
    plt.savefig(os.path.join(OUTPUT_PATH, "confusion_matrix_rf.png"))

    # Save test set with predictions
    df_test = X_test.copy()
    df_test["true_label"] = y_test.values
    df_test["predicted_label"] = y_pred
    df_test.to_csv(os.path.join(OUTPUT_PATH, "rf_predictions.csv"), index=False)

    return clf, X_test, y_test

def compare_with_dohxp(df):
    df["dohxp_pred"] = df.apply(apply_dohxp, axis=1)
    report = classification_report(df["Label"], df["dohxp_pred"], target_names=["Benign", "Malicious"])
    print("📏 DoHxP Results:")
    print(report)

    # Sauvegarder la comparaison
    with open(os.path.join(OUTPUT_PATH, "dohxp_report.txt"), "w") as f:
        f.write(report)

if __name__ == "__main__":
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    df = load_and_prepare()
    clf, X_test, y_test = train_model(df)
    compare_with_dohxp(df)
