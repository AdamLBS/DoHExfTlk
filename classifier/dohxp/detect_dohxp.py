# detect_dohxp.py

import os
import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Seuils DoHxP
PAYLOAD_THRESHOLD = 200
FREQ_THRESHOLD = 100
VOLUME_THRESHOLD = 7500

def analyze_dohlyzer_json(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)

    if not data:
        return {"filename": os.path.basename(filepath), "error": "Empty file or invalid format"}

    # Handle different JSON formats (dict or list of lists)
    if isinstance(data[0], dict) and "features" in data[0]:
        session = data[0]
        features = session.get("features", [])
        meta = session.get("meta", {})
        src_ip = meta.get("src_ip", "unknown")
        dst_ip = meta.get("dst_ip", "unknown")

    elif isinstance(data[0], list) and isinstance(data[0][0], list):
        features = data[0]
        src_ip = "unknown"
        dst_ip = "unknown"
    
    else:
        return {"filename": os.path.basename(filepath), "error": "Unsupported file format"}

    total_packets = len(features)
    total_bytes = sum(f[2] for f in features)
    start_ts = features[0][0] if features else 0
    end_ts = features[-1][0] if features else 0
    duration = end_ts - start_ts if (end_ts - start_ts) > 0 else 1

    avg_payload = total_bytes / total_packets if total_packets else 0
    freq_pps = total_packets / duration
    volume_bps = total_bytes / duration

    suspicious = (
        avg_payload > PAYLOAD_THRESHOLD or
        freq_pps > FREQ_THRESHOLD or
        volume_bps > VOLUME_THRESHOLD
    )

    return {
        "filename": os.path.basename(filepath),
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "avg_payload": round(avg_payload, 2),
        "freq_pps": round(freq_pps, 2),
        "volume_bps": round(volume_bps, 2),
        "suspicious": suspicious
    }

def plot_3d_scatter(df, output_path="detection_plot.png"):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    benign = df[df["suspicious"] == False]
    malicious = df[df["suspicious"] == True]

    ax.scatter(benign["avg_payload"], benign["freq_pps"], benign["volume_bps"], 
               c='green', label="Benign", alpha=0.6)
    ax.scatter(malicious["avg_payload"], malicious["freq_pps"], malicious["volume_bps"], 
               c='red', label="Suspicious", alpha=0.6)

    ax.set_xlabel("Avg Payload Size (bytes)")
    ax.set_ylabel("Frequency (pkt/s)")
    ax.set_zlabel("Volume (bytes/s)")
    ax.set_title("DoHxP Detection - Feature Space")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"[+] 3D plot saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Detect suspicious DoH flows from DoHLyzer JSON output.")
    parser.add_argument("folder", help="Folder containing DoHLyzer JSON files")
    parser.add_argument("-o", "--output", default="detection_report.csv", help="CSV file to save results")
    args = parser.parse_args()

    results = []
    for filename in os.listdir(args.folder):
        if filename.endswith(".json"):
            path = os.path.join(args.folder, filename)
            result = analyze_dohlyzer_json(path)
            results.append(result)

    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False)
    print(f"[+] Analysis complete: {args.output}")
    print(df)

    # Générer le graphe si les données sont valides
    if not df.empty and "error" not in df.columns:
        plot_3d_scatter(df)

if __name__ == "__main__":
    main()
