#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("predictor")

NUMERIC_FEATURES = [
    'SourcePort', 'DestinationPort', 'Duration',
    'FlowBytesSent', 'FlowSentRate', 'FlowBytesReceived', 'FlowReceivedRate',
    'PacketLengthVariance', 'PacketLengthStandardDeviation', 'PacketLengthMean',
    'PacketLengthMedian', 'PacketLengthMode', 'PacketLengthSkewFromMedian',
    'PacketLengthSkewFromMode', 'PacketLengthCoefficientofVariation',
    'PacketTimeVariance', 'PacketTimeStandardDeviation', 'PacketTimeMean',
    'PacketTimeMedian', 'PacketTimeMode', 'PacketTimeSkewFromMedian',
    'PacketTimeSkewFromMode', 'PacketTimeCoefficientofVariation',
    'ResponseTimeTimeVariance', 'ResponseTimeTimeStandardDeviation',
    'ResponseTimeTimeMean', 'ResponseTimeTimeMedian', 'ResponseTimeTimeMode',
    'ResponseTimeTimeSkewFromMedian', 'ResponseTimeTimeSkewFromMode',
    'ResponseTimeTimeCoefficientofVariation',
]

MODELS_DIR = Path("../models")

def load_thresholds():
    thr_path = MODELS_DIR / "thresholds.json"
    if thr_path.exists():
        try:
            with open(thr_path, "r") as f:
                data = json.load(f)
            return {k: float(v.get("threshold", 0.5)) for k, v in data.items()}
        except Exception as e:
            log.warning(f"⚠️ Could not read thresholds.json: {e}")
    return {}

def load_pipelines():
    loaded = {}
    for pkl in MODELS_DIR.glob("*.pkl"):
        name = pkl.stem
        if name in {"best_model", "preprocessors"}:
            continue
        try:
            model = joblib.load(pkl)
            if not hasattr(model, "predict_proba"):
                log.warning(f"⚠️ {name}: no predict_proba — skipped")
                continue
            loaded[name] = model
            log.info(f"Loaded model: {name}")
        except Exception as e:
            log.error(f"Error loading {pkl}: {e}")
    return loaded

def load_csv_as_dataframe(csv_path: Path) -> pd.DataFrame:
    log.info(f"Loading data: {csv_path}")
    df = pd.read_csv(csv_path)
    if "Label" in df.columns:
        df = df.drop(columns=["Label"])
    for col in NUMERIC_FEATURES:
        if col not in df.columns:
            df[col] = np.nan
    df = df[NUMERIC_FEATURES]
    for col in NUMERIC_FEATURES:
        s = pd.to_numeric(df[col], errors="coerce")
        if s.isnull().any():
            s = s.fillna(s.median())
        df[col] = s
    log.info(f"Features used: {df.shape[1]}/{len(NUMERIC_FEATURES)}")
    return df

def load_dohxp_model(config_path: Path):
    with open(config_path, "r") as f:
        cfg = json.load(f)
    rules = cfg.get("rules", [])
    clip_low, clip_high = cfg.get("clip", [0.0, 1.0])
    bias = float(cfg.get("bias", 0.0))
    agg = cfg.get("aggregation", "sum").lower()

    def predict_proba(X: pd.DataFrame):
        scores = []
        for _, row in X.iterrows():
            hits = []
            for r in rules:
                feat = r["feature"]
                op = r["op"]
                thr = r["value"]
                weight = r.get("weight", 1.0)
                val = row[feat]
                hit = False
                if op == ">": hit = val > thr
                elif op == "<": hit = val < thr
                elif op == ">=": hit = val >= thr
                elif op == "<=": hit = val <= thr
                elif op == "==": hit = val == thr
                elif op == "!=": hit = val != thr
                if hit:
                    hits.append(weight)
            if agg == "mean" and hits:
                score = sum(hits) / len(rules)
            else:
                score = sum(hits)
            score += bias
            score = max(clip_low, min(clip_high, score))
            scores.append(score)
        p1 = np.array(scores)
        p0 = 1.0 - p1
        return np.vstack([p0, p1]).T

    return type("DoHXPModel", (), {"predict_proba": staticmethod(predict_proba)})

def summarize_predictions(model_name, y_pred, y_proba, threshold):
    benign = int((y_pred == 0).sum())
    malic = int((y_pred == 1).sum())
    conf = np.maximum(y_proba, 1.0 - y_proba).mean() if len(y_proba) else float("nan")
    log.info(f"🤖 {model_name.upper()}:")
    log.info(f"   - Benign: {benign}")
    log.info(f"   - Malicious: {malic}")
    log.info(f"   - Threshold applied: {threshold:.3f}")
    log.info(f"   - Avg confidence: {conf:.3f}")
    return benign, malic, conf

def main():
    parser = argparse.ArgumentParser(description="Predictor for network flow CSV using trained pipelines + DoHXP model")
    parser.add_argument("csv_path", help="Path to CSV without Label column")
    parser.add_argument("--default-threshold", type=float, default=0.5,
                        help="Default threshold if not found in thresholds.json")
    parser.add_argument("--dohxp-config", type=Path, default=MODELS_DIR / "dohxp_model.json",
                        help="Path to DoHXP model JSON")
    args = parser.parse_args()

    thresholds = load_thresholds()
    models = load_pipelines()

    if args.dohxp_config.exists():
        models["dohxp"] = load_dohxp_model(args.dohxp_config)
        log.info(f"Loaded DoHXP rule-based model from {args.dohxp_config}")
    else:
        log.warning(f"DoHXP model config not found: {args.dohxp_config}")

    if not models:
        log.error("No models loaded from ../models")
        return

    df = load_csv_as_dataframe(Path(args.csv_path))

    overall = []
    log.info("=== PREDICTIONS ===")
    for name, model in models.items():
        try:
            proba = model.predict_proba(df)[:, 1]
            thr = thresholds.get(name, args.default_threshold)
            pred = (proba >= thr).astype(int)
            b, m, c = summarize_predictions(name, pred, proba, thr)
            overall.append((name, b, m, len(pred), c, thr))
        except Exception as e:
            log.error(f"Error predicting with {name}: {e}")

    if overall:
        log.info("\n=== SUMMARY OF PREDICTIONS ===\n")
        header = f"{'Model':<24} {'Benign':>8} {'Malicious':>12} {'Total':>10} {'Threshold':>8} {'Confidence':>12}"
        sep = "-" * len(header)
        print(header)
        print(sep)
        for (name, b, m, tot, c, thr) in overall:
            print(f"{name:<24} {b:>8} {m:>12} {tot:>10} {thr:>8.3f} {c:>12.3f}")
    else:
        log.info("No usable results.")

if __name__ == "__main__":
    main()
