#!/usr/bin/env python3
"""
Script de prédiction ML pour la détection d'exfiltration DoH
Utilise les modèles entraînés pour analyser de nouvelles données
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from sklearn.externals import joblib
import argparse
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DoHPredictor:
    """Prédicteur ML pour la détection d'exfiltration DoH"""
    
    def __init__(self, models_dir="/home/ubuntu/Kent-Dissertation/models"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.preprocessors = None
        self.load_models()
    
    def load_models(self):
        """Charge tous les modèles disponibles"""
        if not self.models_dir.exists():
            raise FileNotFoundError(f"Répertoire des modèles introuvable: {self.models_dir}")
        
        # Charger les préprocesseurs
        preprocessors_path = self.models_dir / "preprocessors.pkl"
        if preprocessors_path.exists():
            self.preprocessors = joblib.load(preprocessors_path)
            logger.info("✅ Préprocesseurs chargés")
        else:
            raise FileNotFoundError("Préprocesseurs introuvables. Entraînez d'abord les modèles.")
        
        # Charger tous les modèles
        model_files = list(self.models_dir.glob("*.pkl"))
        for model_file in model_files:
            if model_file.name not in ["preprocessors.pkl", "best_model.pkl"]:
                try:
                    model_name = model_file.stem
                    model = joblib.load(model_file)
                    self.models[model_name] = model
                    logger.info(f"✅ Modèle chargé: {model_name}")
                except Exception as e:
                    logger.error(f"❌ Erreur chargement {model_file}: {e}")
        
        if not self.models:
            raise ValueError("Aucun modèle trouvé. Entraînez d'abord les modèles.")
        
        logger.info(f"📊 {len(self.models)} modèles chargés: {list(self.models.keys())}")
    
    def predict_single_model(self, model_name, data_df):
        """Fait des prédictions avec un modèle spécifique"""
        if model_name not in self.models:
            raise ValueError(f"Modèle '{model_name}' non trouvé. Disponibles: {list(self.models.keys())}")
        
        # Préprocessing
        processed_data = self.preprocess_data(data_df)
        
        # Prédictions
        model = self.models[model_name]
        predictions = model.predict(processed_data)
        probabilities = model.predict_proba(processed_data)
        
        # Convertir en labels
        predicted_labels = self.preprocessors['label_encoder'].inverse_transform(predictions)
        
        return {
            'model': model_name,
            'predictions': predicted_labels.tolist(),
            'probabilities': probabilities.tolist(),
            'confidence': np.max(probabilities, axis=1).tolist()
        }
    
    def predict_all_models(self, data_df):
        """Fait des prédictions avec tous les modèles (ensemble)"""
        results = {}
        
        for model_name in self.models.keys():
            try:
                results[model_name] = self.predict_single_model(model_name, data_df)
            except Exception as e:
                logger.error(f"❌ Erreur prédiction {model_name}: {e}")
        
        # Calcul du consensus (vote majoritaire)
        if len(results) > 1:
            consensus = self.calculate_consensus(results, len(data_df))
            results['consensus'] = consensus
        
        return results
    
    def calculate_consensus(self, results, n_samples):
        """Calcule le consensus entre tous les modèles"""
        all_predictions = []
        all_confidences = []
        
        for model_name, result in results.items():
            all_predictions.append(result['predictions'])
            all_confidences.append(result['confidence'])
        
        consensus_predictions = []
        consensus_confidences = []
        
        for i in range(n_samples):
            # Vote majoritaire pour chaque échantillon
            sample_predictions = [preds[i] for preds in all_predictions]
            
            # Compter les votes
            benign_votes = sample_predictions.count('Benign')
            malicious_votes = sample_predictions.count('Malicious')
            
            if malicious_votes > benign_votes:
                consensus_pred = 'Malicious'
            else:
                consensus_pred = 'Benign'
            
            # Confiance moyenne
            sample_confidences = [confs[i] for confs in all_confidences]
            avg_confidence = np.mean(sample_confidences)
            
            consensus_predictions.append(consensus_pred)
            consensus_confidences.append(avg_confidence)
        
        return {
            'model': 'consensus',
            'predictions': consensus_predictions,
            'confidence': consensus_confidences,
            'voting_details': {
                'n_models': len(results),
                'models_used': list(results.keys())
            }
        }
    
    def preprocess_data(self, data_df):
        """Préprocesse les nouvelles données comme lors de l'entraînement"""
        feature_names = self.preprocessors['feature_names']
        available_features = [col for col in feature_names if col in data_df.columns]
        
        if not available_features:
            raise ValueError(f"Aucune feature reconnue. Features attendues: {feature_names}")
        
        logger.info(f"📊 Features utilisées: {len(available_features)}/{len(feature_names)}")
        
        # Sélectionner les features
        X = data_df[available_features].copy()
        
        # Nettoyer les données
        for col in available_features:
            # Remplacer valeurs infinies
            X[col] = X[col].replace([np.inf, -np.inf], np.nan)
            
            # Remplacer valeurs manquantes par la médiane
            if X[col].isnull().sum() > 0:
                median_val = X[col].median()
                if pd.isna(median_val):  # Si toute la colonne est NaN
                    median_val = 0
                X[col].fillna(median_val, inplace=True)
        
        # Normaliser avec le scaler d'entraînement
        X_scaled = self.preprocessors['scaler'].transform(X)
        
        return X_scaled
    
    def predict_from_csv(self, csv_path, output_path=None, model_name=None):
        """Fait des prédictions sur un fichier CSV"""
        logger.info(f"📊 Chargement données: {csv_path}")
        
        data_df = pd.read_csv(csv_path)
        
        # Retirer la colonne Label si elle existe (pour éviter les erreurs)
        if 'Label' in data_df.columns:
            data_df = data_df.drop('Label', axis=1)
            logger.info("⚠️ Colonne 'Label' supprimée des données d'entrée")
        
        # Prédictions
        if model_name:
            results = {model_name: self.predict_single_model(model_name, data_df)}
        else:
            results = self.predict_all_models(data_df)
        
        # Sauvegarder les résultats
        if output_path:
            self.save_predictions(results, data_df, output_path)
        
        return results
    
    def save_predictions(self, results, original_data, output_path):
        """Sauvegarde les prédictions"""
        output_path = Path(output_path)
        
        # Créer un DataFrame avec les données originales + prédictions
        result_df = original_data.copy()
        
        # Ajouter les prédictions de chaque modèle
        for model_name, result in results.items():
            result_df[f'Prediction_{model_name}'] = result['predictions']
            result_df[f'Confidence_{model_name}'] = result['confidence']
        
        # Sauvegarder CSV
        csv_output = output_path.with_suffix('.csv')
        result_df.to_csv(csv_output, index=False)
        logger.info(f"💾 Prédictions sauvegardées: {csv_output}")
        
        # Sauvegarder JSON avec détails complets
        json_output = output_path.with_suffix('.json')
        full_results = {
            'timestamp': datetime.now().isoformat(),
            'input_samples': len(original_data),
            'models_used': list(results.keys()),
            'predictions': results
        }
        
        with open(json_output, 'w') as f:
            json.dump(full_results, f, indent=2)
        logger.info(f"💾 Détails sauvegardés: {json_output}")


# Fonctions utilitaires pour usage direct
def quick_predict(csv_path, model_name='random_forest'):
    """Fonction rapide pour faire une prédiction"""
    predictor = DoHPredictor()
    results = predictor.predict_from_csv(csv_path, model_name=model_name)
    return results[model_name]['predictions']


def predict_sample_data():
    """Teste le prédicteur avec des données d'exemple"""
    # Données d'exemple (format réseau)
    sample_data = pd.DataFrame({
        'SourcePort': [443, 80, 53, 443, 8080],
        'DestinationPort': [12345, 443, 53, 54321, 443],
        'Duration': [120.5, 95.2, 0.15, 180.3, 45.8],
        'FlowBytesSent': [15000, 8500, 512, 25000, 3200],
        'FlowSentRate': [125.5, 89.5, 3413.3, 138.9, 69.9],
        'FlowBytesReceived': [18000, 12000, 1024, 28000, 4800],
        'FlowReceivedRate': [149.4, 126.3, 6826.7, 155.6, 104.7],
        'PacketLengthMean': [142.5, 128.3, 64.0, 156.8, 95.2],
        'PacketLengthVariance': [8500, 6200, 1200, 9800, 4100],
        'PacketLengthStandardDeviation': [92.2, 78.7, 34.6, 99.0, 64.0]
    })
    
    try:
        predictor = DoHPredictor()
        results = predictor.predict_all_models(sample_data)
        
        print("🧪 === TEST PRÉDICTEUR ===")
        for model_name, result in results.items():
            print(f"\n🤖 {model_name.upper()}:")
            for i, (pred, conf) in enumerate(zip(result['predictions'], result['confidence'])):
                print(f"   Échantillon {i+1}: {pred} (confiance: {conf:.3f})")
        
        return results
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return None


def main():
    """Interface en ligne de commande"""
    parser = argparse.ArgumentParser(description="Prédiction ML pour détection DoH")
    parser.add_argument('input', nargs='?', help="Fichier CSV d'entrée")
    parser.add_argument('-o', '--output', help="Fichier de sortie (optionnel)")
    parser.add_argument('-m', '--model', help="Modèle spécifique à utiliser")
    parser.add_argument('--models-dir', default="/home/ubuntu/Kent-Dissertation/models",
                      help="Répertoire des modèles")
    parser.add_argument('--test', action='store_true', 
                      help="Tester avec des données d'exemple")
    
    args = parser.parse_args()
    
    # Mode test
    if args.test:
        predict_sample_data()
        return 0
    
    # Mode fichier
    if not args.input:
        print("❌ Spécifiez un fichier d'entrée ou utilisez --test")
        return 1
    
    try:
        # Créer le prédicteur
        predictor = DoHPredictor(args.models_dir)
        
        # Faire les prédictions
        results = predictor.predict_from_csv(
            args.input, 
            args.output, 
            args.model
        )
        
        # Afficher un résumé
        logger.info("📊 === RÉSUMÉ DES PRÉDICTIONS ===")
        for model_name, result in results.items():
            predictions = result['predictions']
            benign_count = predictions.count('Benign')
            malicious_count = predictions.count('Malicious')
            avg_confidence = np.mean(result['confidence'])
            
            logger.info(f"🤖 {model_name.upper()}:")
            logger.info(f"   - Benign: {benign_count}")
            logger.info(f"   - Malicious: {malicious_count}")
            logger.info(f"   - Confiance moyenne: {avg_confidence:.3f}")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
