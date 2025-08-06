import pandas as pd
from sklearn.metrics import classification_report
from pathlib import Path

# Seuils DoHxP
PAYLOAD_THRESHOLD = 200
FREQ_THRESHOLD = 100
VOLUME_THRESHOLD = 7500

def apply_dohxp_detection(row):
    avg_packet_size = row["PacketLengthMean"]
    duration = row["Duration"]
    total_bytes = row["FlowBytesSent"]
    total_packets = total_bytes / avg_packet_size if avg_packet_size > 0 else 0

    freq = total_packets / duration if duration > 0 else 0
    volume_rate = total_bytes / duration if duration > 0 else 0

    return (
        avg_packet_size > PAYLOAD_THRESHOLD or
        freq > FREQ_THRESHOLD or
        volume_rate > VOLUME_THRESHOLD
    )

def evaluate_from_folder(folder_path):
    all_dfs = []

    for csv_file in Path(folder_path).rglob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            df = df[df["Label"].isin(["Benign", "Malicious"])].copy()
            df["label"] = df["Label"].map({"Benign": 0, "Malicious": 1})
            df["source_file"] = str(csv_file)
            all_dfs.append(df)
        except Exception as e:
            print(f"❌ Erreur lecture {csv_file}: {e}")

    if not all_dfs:
        print("❌ Aucun fichier CSV valide trouvé.")
        return

    df = pd.concat(all_dfs, ignore_index=True)
    df["prediction"] = df.apply(apply_dohxp_detection, axis=1)

    print(f"\n✅ Total flows analysés : {len(df)}\n")
    print(classification_report(df["label"], df["prediction"], target_names=["Benign", "Malicious"]))

    # Faux positifs
    false_positives = df[(df["label"] == 0) & (df["prediction"] == True)]
    if not false_positives.empty:
        print("\n🚨 Faux positifs détectés :")
        for _, row in false_positives.iterrows():
            avg_packet_size = row["PacketLengthMean"]
            duration = row["Duration"]
            total_bytes = row["FlowBytesSent"]
            total_packets = total_bytes / avg_packet_size if avg_packet_size > 0 else 0
            freq = total_packets / duration if duration > 0 else 0
            volume = total_bytes / duration if duration > 0 else 0

            print(f"Flow {row['SourceIP']}->{row['DestinationIP']} (fichier: {row['source_file']}) détecté comme malveillant :")
            print(f"  Payload moyen : {avg_packet_size:.2f}")
            print(f"  Fréquence     : {freq:.2f} pkt/s")
            print(f"  Volume        : {volume:.2f} B/s")
            print(f"  Seuils dépassés ?")
            print(f"    avg_packet_size > {PAYLOAD_THRESHOLD}: {avg_packet_size > PAYLOAD_THRESHOLD}")
            print(f"    frequency > {FREQ_THRESHOLD}: {freq > FREQ_THRESHOLD}")
            print(f"    volume > {VOLUME_THRESHOLD}: {volume > VOLUME_THRESHOLD}")
            print("-" * 60)
    else:
        print("✅ Aucun faux positif détecté.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", required=True, help="Dossier contenant les CSV")
    args = parser.parse_args()

    evaluate_from_folder(args.directory)
