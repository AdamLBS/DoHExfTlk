import pandas as pd
import argparse
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument("--csvs", nargs="+", required=True, help="Liste des chemins vers les fichiers CSV")
args = parser.parse_args()

# Lire et concaténer les CSV
dfs = []
for csv_path in args.csvs:
    print(f"Lecture de : {csv_path}")
    df = pd.read_csv(csv_path)
    dfs.append(df)

if not dfs:
    raise ValueError("Aucun fichier CSV valide trouvé.")

df_all = pd.concat(dfs, ignore_index=True)

# Filtrage sur Benign / Malicious
df_filtered = df_all[df_all["Label"].isin(["Benign", "Malicious"])].copy()
df_filtered["Label"] = df_filtered["Label"].map({"Benign": 0, "Malicious": 1})

# Création des features DoHxP
df_filtered["avg_packet_size"] = df_filtered["FlowBytesSent"] / df_filtered["Duration"]
df_filtered["frequency"] = df_filtered["FlowBytesSent"] / df_filtered["PacketTimeMedian"]
df_filtered["volume_rate"] = df_filtered["FlowSentRate"]

# Nettoyage
df_filtered = df_filtered.replace([float("inf"), -float("inf")], pd.NA).dropna()

# Features & Labels
X = df_filtered[["avg_packet_size", "frequency", "volume_rate"]]
y = df_filtered["Label"]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Modèle
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Évaluation
y_pred = clf.predict(X_test)
print("✅ Résultats sur le jeu de test :\n")
print(classification_report(y_test, y_pred, target_names=["Benign", "Malicious"]))

# Importance des features
importances = clf.feature_importances_
features = ["avg_packet_size", "frequency", "volume_rate"]
print("\n🎯 Importance des features :")
for f, imp in zip(features, importances):
    print(f"  {f} : {imp:.4f}")
