#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("predictor")

# Les 31 features attendues (ordre figé)
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
            log.warning(f"⚠️ Impossible de lire thresholds.json: {e}")
    return {}

def load_pipelines():
    """Charge tous les *.pkl dans ../models/ (sauf best_model.pkl et preprocessors.pkl)."""
    loaded = {}
    for pkl in MODELS_DIR.glob("*.pkl"):
        name = pkl.stem
        if name in {"best_model", "preprocessors"}:
            continue
        try:
            model = joblib.load(pkl)
            # sanity check: doit implémenter predict_proba
            if not hasattr(model, "predict_proba"):
                log.warning(f"⚠️ {name}: pas de predict_proba — ignoré")
                continue
            loaded[name] = model
            log.info(f"✅ Modèle chargé: {name}")
        except Exception as e:
            log.error(f"❌ Erreur chargement {pkl}: {e}")
    return loaded

def load_csv_as_dataframe(csv_path: Path) -> pd.DataFrame:
    log.info(f"📊 Chargement données: {csv_path}")
    df = pd.read_csv(csv_path)
    # si une colonne Label traîne, on l’enlève
    if "Label" in df.columns:
        df = df.drop(columns=["Label"])

    # S’assure que toutes les colonnes existent (colonnes manquantes → NaN)
    for col in NUMERIC_FEATURES:
        if col not in df.columns:
            df[col] = np.nan

    # Réordonner exactement comme attendu
    df = df[NUMERIC_FEATURES]

    # Nettoyage: numeric + fillna(median) par colonne
    for col in NUMERIC_FEATURES:
        s = pd.to_numeric(df[col], errors="coerce")
        if s.isnull().any():
            s = s.fillna(s.median())
        df[col] = s

    log.info(f"📊 Features utilisées: {df.shape[1]}/{len(NUMERIC_FEATURES)}")
    return df

def summarize_predictions(model_name, y_pred, y_proba, threshold):
    # y_pred already thresholded; confidence = max(p, 1-p)
    benign = int((y_pred == 0).sum())
    malic = int((y_pred == 1).sum())
    conf = np.maximum(y_proba, 1.0 - y_proba).mean() if len(y_proba) else float("nan")
    log.info(f"🤖 {model_name.upper()}:")
    log.info(f"   - Benign: {benign}")
    log.info(f"   - Malicious: {malic}")
    log.info(f"   - Seuil appliqué: {threshold:.3f}")
    log.info(f"   - Confiance moyenne: {conf:.3f}")
    return benign, malic, conf

def main():
    parser = argparse.ArgumentParser(description="Predictor for network flow CSV using trained pipelines")
    parser.add_argument("csv_path", help="Chemin vers le CSV de flux (sans Label)")
    parser.add_argument("--default-threshold", type=float, default=0.5,
                        help="Seuil par défaut si non trouvé dans thresholds.json (0.5)")
    args = parser.parse_args()

    # 1) Charger pipelines + seuils
    thresholds = load_thresholds()
    models = load_pipelines()
    if not models:
        log.error("❌ Aucun modèle chargé dans ../models — as-tu bien entraîné/sauvegardé ?")
        return

    # 2) Charger CSV en **DataFrame** (important !)
    df = load_csv_as_dataframe(Path(args.csv_path))

    overall = []
    log.info("📊 === PRÉDICTIONS ===")
    for name, pipe in models.items():
        try:
            # proba de la classe 1 (Malicious)
            proba = pipe.predict_proba(df)[:, 1]
            thr = thresholds.get(name, args.default_threshold)
            pred = (proba >= thr).astype(int)
            b, m, c = summarize_predictions(name, pred, proba, thr)
            overall.append((name, b, m, len(pred), c, thr))
        except Exception as e:
            log.error(f"❌ Erreur prédiction {name}: {e}")

    # 3) Résumé global
    if overall:
        log.info("\n📊 === RÉSUMÉ DES PRÉDICTIONS ===\n")
        header = f"{'Modèle':<24} {'Benign':>8} {'Malicious':>12} {'Total':>10} {'Seuil':>8} {'Confiance':>12}"
        sep = "-" * len(header)
        print(header)
        print(sep)
        for (name, b, m, tot, c, thr) in overall:
            print(f"{name:<24} {b:>8} {m:>12} {tot:>10} {thr:>8.3f} {c:>12.3f}")
    else:
        log.info("Aucun résultat exploitable.")

if __name__ == "__main__":
    main()
