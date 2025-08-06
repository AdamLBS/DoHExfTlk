#!/usr/bin/env python3
"""
Entraîneur de modèles ML pour la détection d'exfiltration DoH
Adapté pour les datasets de flow réseau avec features statistiques
"""

import os
import json
import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, accuracy_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.utils import resample
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTEENN
import joblib
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NetworkFlowMLTrainer:
    """Entraîneur ML pour datasets de flow réseau"""
    
    def __init__(self, quick_mode=False):
        self.quick_mode = quick_mode
        self.max_samples = 2000 if quick_mode else None
        self.setup_directories()
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.smote = SMOTE(random_state=42)
        self.use_class_balancing = True
        self.cross_val_folds = 3 if quick_mode else 5  # Réduire les folds en mode quick
        
        # Features numériques du dataset réseau
        self.numeric_features = [
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
            'ResponseTimeTimeCoefficientofVariation'
        ]
        
        # Configuration des modèles avec régularisation anti-overfitting
        if quick_mode:
            # Configuration simplifiée pour mode quick
            self.models_config = {
                'random_forest': {
                    'model': RandomForestClassifier,
                    'params': {
                        'n_estimators': [50, 100],
                        'max_depth': [10, 15],
                        'min_samples_split': [10],
                        'min_samples_leaf': [5],
                        'max_features': ['sqrt'],
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'random_state': [42]
                    }
                },
                'logistic_regression': {
                    'model': LogisticRegression,
                    'params': {
                        'C': [0.1, 1],
                        'penalty': ['l2'],
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'random_state': [42],
                        'max_iter': [1000]
                    }
                }
            }
        else:
            # Configuration complète pour mode normal
            self.models_config = {
                'random_forest': {
                    'model': RandomForestClassifier,
                    'params': {
                        'n_estimators': [100, 200],
                        'max_depth': [10, 15, 20],  # Limiter la profondeur
                        'min_samples_split': [5, 10, 20],  # Augmenter min_samples_split
                        'min_samples_leaf': [2, 5, 10],   # Ajouter min_samples_leaf
                        'max_features': ['sqrt', 'log2', 0.8],  # Limiter les features
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'random_state': [42]
                    }
                },
                'gradient_boosting': {
                    'model': GradientBoostingClassifier,
                    'params': {
                        'n_estimators': [100, 150],  # Réduire pour éviter l'overfitting
                        'learning_rate': [0.05, 0.1, 0.15],  # Ajouter des taux plus faibles
                        'max_depth': [3, 5],  # Limiter la profondeur
                        'min_samples_split': [10, 20],  # Augmenter
                        'min_samples_leaf': [5, 10],   # Ajouter
                        'subsample': [0.8, 0.9],  # Sous-échantillonnage
                        'random_state': [42]
                    }
                },
                'logistic_regression': {
                    'model': LogisticRegression,
                    'params': {
                        'C': [0.01, 0.1, 1],  # Ajouter plus de régularisation
                        'penalty': ['l1', 'l2', 'elasticnet'],  # Différents types de régularisation
                        'l1_ratio': [0.5],  # Pour elasticnet
                        'solver': ['liblinear', 'saga'],  # Saga pour elasticnet
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'random_state': [42],
                        'max_iter': [1000, 2000]
                    }
                },
                'svm': {
                    'model': SVC,
                    'params': {
                        'C': [0.1, 1, 5],  # Réduire C pour plus de régularisation
                        'kernel': ['rbf', 'linear'],
                        'gamma': ['scale', 'auto', 0.1, 0.01],  # Contrôler la complexité
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'probability': [True],
                        'random_state': [42]
                    }
                }
            }
    
    def setup_directories(self):
        """Crée les répertoires nécessaires"""
        self.models_dir = Path("../models") #TODO : Adapt to current directory
        self.reports_dir = Path("../ml_reports")
        
        self.models_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        logger.info(f"📁 Répertoires créés: {self.models_dir}, {self.reports_dir}")
    
    def load_datasets(self):
        """Charge tous les datasets disponibles"""
        logger.info("📊 Chargement des datasets...")
        
        datasets_dir = Path("../datasets")
        all_data = []
        
        # Chercher tous les fichiers CSV dans le dossier datasets
        if datasets_dir.exists():
            csv_files = list(datasets_dir.glob("*.csv"))
            logger.info(f"�� Fichiers CSV trouvés: {[f.name for f in csv_files]}")
            
            for csv_file in csv_files:
                try:
                    logger.info(f"📈 Chargement: {csv_file.name}")
                    df = pd.read_csv(csv_file)
                    
                    # Vérifier que le fichier a la colonne Label
                    if 'Label' in df.columns:
                        logger.info(f"✅ {csv_file.name}: {len(df)} lignes, Labels: {df['Label'].value_counts().to_dict()}")
                        all_data.append(df)
                    else:
                        logger.warning(f"⚠️ {csv_file.name}: Pas de colonne 'Label', ignoré")
                        
                except Exception as e:
                    logger.error(f"❌ Erreur chargement {csv_file.name}: {e}")
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"📊 Dataset combiné: {len(combined_df)} lignes")
            logger.info(f"📊 Distribution des labels: {combined_df['Label'].value_counts().to_dict()}")
            
            # Appliquer la limitation en mode quick
            if self.quick_mode and self.max_samples and len(combined_df) > self.max_samples:
                logger.info(f"🚀 Mode quick activé: limitation à {self.max_samples} échantillons")
                # Échantillonnage stratifié pour conserver la distribution des classes
                combined_df = combined_df.groupby('Label').apply(
                    lambda x: x.sample(min(len(x), self.max_samples // combined_df['Label'].nunique()), 
                                     random_state=42)
                ).reset_index(drop=True)
                logger.info(f"📊 Dataset limité: {len(combined_df)} lignes")
                logger.info(f"📊 Nouvelle distribution: {combined_df['Label'].value_counts().to_dict()}")
            
            return combined_df
        else:
            logger.error("❌ Aucun dataset valide trouvé")
            return None
    
    def preprocess_data(self, df):
        """Préprocesse les données"""
        logger.info("🔄 Préprocessing des données...")
        
        df_processed = df.copy()
        
        # Sélectionner seulement les features numériques disponibles
        available_numeric_features = [col for col in self.numeric_features if col in df_processed.columns]
        logger.info(f"📊 Features numériques disponibles: {len(available_numeric_features)}/{len(self.numeric_features)}")
        
        # Vérifier les valeurs manquantes
        missing_info = df_processed[available_numeric_features].isnull().sum()
        if missing_info.sum() > 0:
            logger.warning(f"⚠️ Valeurs manquantes détectées:")
            for col, missing in missing_info[missing_info > 0].items():
                logger.warning(f"  - {col}: {missing} valeurs manquantes")
        
        # Remplacer les valeurs manquantes par la médiane
        for col in available_numeric_features:
            if df_processed[col].isnull().sum() > 0:
                median_val = df_processed[col].median()
                df_processed[col].fillna(median_val, inplace=True)
        
        # Remplacer les valeurs infinies
        df_processed = df_processed.replace([np.inf, -np.inf], np.nan)
        for col in available_numeric_features:
            if df_processed[col].isnull().sum() > 0:
                median_val = df_processed[col].median()
                df_processed[col].fillna(median_val, inplace=True)
        
        # Préparer les features et le target
        X = df_processed[available_numeric_features]
        y = df_processed['Label']
        
        # Encoder les labels (Benign = 0, Malicious = 1)
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Normaliser les features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=available_numeric_features)
        
        logger.info(f"✅ Preprocessing terminé: {X_scaled.shape[0]} échantillons, {X_scaled.shape[1]} features")
        logger.info(f"📊 Classes encodées: {dict(zip(self.label_encoder.classes_, range(len(self.label_encoder.classes_))))}")
        
        return X_scaled, y_encoded, available_numeric_features
    
    def balance_dataset(self, X, y, method='smote'):
        """Équilibre le dataset pour réduire le biais de classe"""
        logger.info(f"⚖️ Équilibrage du dataset avec {method}...")
        
        # Distribution originale
        unique, counts = np.unique(y, return_counts=True)
        logger.info(f"📊 Distribution avant: {dict(zip(self.label_encoder.classes_[unique], counts))}")
        
        try:
            if method == 'smote':
                # SMOTE pour générer des échantillons synthétiques de la classe minoritaire
                X_balanced, y_balanced = self.smote.fit_resample(X, y)
                
            elif method == 'undersample':
                # Sous-échantillonnage de la classe majoritaire
                undersampler = RandomUnderSampler(random_state=42, sampling_strategy=0.5)  # 2:1 ratio
                X_balanced, y_balanced = undersampler.fit_resample(X, y)
                
            elif method == 'combined':
                # Combinaison SMOTE + sous-échantillonnage
                smote_enn = SMOTEENN(random_state=42)
                X_balanced, y_balanced = smote_enn.fit_resample(X, y)
                
            else:
                logger.warning(f"⚠️ Méthode {method} inconnue, pas d'équilibrage")
                return X, y
            
            # Distribution après équilibrage
            unique_after, counts_after = np.unique(y_balanced, return_counts=True)
            logger.info(f"📊 Distribution après: {dict(zip(self.label_encoder.classes_[unique_after], counts_after))}")
            logger.info(f"✅ Équilibrage terminé: {len(X)} → {len(X_balanced)} échantillons")
            
            return X_balanced, y_balanced
            
        except Exception as e:
            logger.error(f"❌ Erreur équilibrage: {e}")
            return X, y
    
    def train_model(self, model_name, model_config, X_train, y_train, X_val, y_val):
        """Entraîne un modèle avec optimisation des hyperparamètres et validation robuste"""
        logger.info(f"🤖 Entraînement {model_name}...")
        
        try:
            # Cross-validation stratifiée pour gérer le déséquilibre
            stratified_cv = StratifiedKFold(n_splits=self.cross_val_folds, shuffle=True, random_state=42)
            
            # Grid Search avec validation stratifiée
            grid_search = GridSearchCV(
                model_config['model'](),
                model_config['params'],
                cv=stratified_cv,
                scoring='roc_auc',  # Meilleure métrique pour données déséquilibrées
                n_jobs=-1,
                verbose=2,
                return_train_score=True  # Pour détecter l'overfitting
            )
            
            grid_search.fit(X_train, y_train)
            best_model = grid_search.best_estimator_
            
            # Analyser l'overfitting avec train vs validation scores
            train_scores = grid_search.cv_results_['mean_train_score']
            val_scores = grid_search.cv_results_['mean_test_score']
            best_idx = grid_search.best_index_
            
            train_score_best = train_scores[best_idx]
            val_score_best = val_scores[best_idx]
            overfitting_gap = train_score_best - val_score_best
            
            # Prédictions sur validation
            val_pred = best_model.predict(X_val)
            val_proba = best_model.predict_proba(X_val)[:, 1]
            
            # Métriques
            val_accuracy = accuracy_score(y_val, val_pred)
            val_auc = roc_auc_score(y_val, val_proba)
            
            # Cross-validation finale
            cv_scores = cross_val_score(best_model, X_train, y_train, 
                                      cv=stratified_cv, scoring='roc_auc')
            
            results = {
                'model': best_model,
                'best_params': grid_search.best_params_,
                'val_accuracy': val_accuracy,
                'val_auc': val_auc,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'train_score': train_score_best,
                'val_score': val_score_best,
                'overfitting_gap': overfitting_gap,
                'classification_report': classification_report(y_val, val_pred, 
                                                             target_names=self.label_encoder.classes_)
            }
            
            # Alertes overfitting
            if overfitting_gap > 0.05:
                logger.warning(f"⚠️ {model_name}: Possible overfitting détecté (gap: {overfitting_gap:.3f})")
            
            logger.info(f"✅ {model_name}: Accuracy={val_accuracy:.3f}, AUC={val_auc:.3f}, "
                       f"CV={cv_scores.mean():.3f}(±{cv_scores.std():.3f}), Gap={overfitting_gap:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur {model_name}: {e}")
            return None
    
    def train_all_models(self):
        """Entraîne tous les modèles"""
        logger.info("🚀 Début de l'entraînement...")
        
        # Charger les données
        df = self.load_datasets()
        if df is None:
            return {}
        
        # Préprocessing
        X, y, feature_names = self.preprocess_data(df)
        
        # Division train/validation/test (test d'abord pour garder l'équilibre original)
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
        )
        
        # Équilibrage seulement sur les données d'entraînement
        if self.use_class_balancing:
            logger.info("⚖️ Application de l'équilibrage des classes...")
            X_train_balanced, y_train_balanced = self.balance_dataset(X_train, y_train, method='smote')
        else:
            X_train_balanced, y_train_balanced = X_train, y_train
        
        logger.info(f"📊 Division: Train={len(X_train_balanced)}, Val={len(X_val)}, Test={len(X_test)}")
        
        # Entraîner tous les modèles
        trained_models = {}
        best_model = None
        best_auc = 0
        
        for model_name, model_config in self.models_config.items():
            result = self.train_model(model_name, model_config, X_train_balanced, y_train_balanced, X_val, y_val)
            
            if result:
                trained_models[model_name] = result
                
                # Test final
                test_pred = result['model'].predict(X_test)
                test_proba = result['model'].predict_proba(X_test)[:, 1]
                test_accuracy = accuracy_score(y_test, test_pred)
                test_auc = roc_auc_score(y_test, test_proba)
                
                logger.info(f"🏆 {model_name} Test: Accuracy={test_accuracy:.3f}, AUC={test_auc:.3f}")
                
                # Garder le meilleur modèle
                if test_auc > best_auc:
                    best_auc = test_auc
                    best_model = (model_name, result['model'])
                
                # Sauvegarder le modèle
                model_path = self.models_dir / f"{model_name}.pkl"
                joblib.dump(result['model'], model_path)
                logger.info(f"💾 Modèle sauvegardé: {model_path}")
                
                # Rapport détaillé
                self.save_model_report(model_name, result, test_accuracy, test_auc, 
                                     X_test, y_test, test_pred, len(X_train_balanced))
        
        # Sauvegarder les préprocesseurs
        preprocessors = {
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_names': feature_names
        }
        joblib.dump(preprocessors, self.models_dir / "preprocessors.pkl")
        
        if best_model:
            logger.info(f"🏆 Meilleur modèle: {best_model[0]} (AUC Test: {best_auc:.3f})")
            # Sauvegarder le meilleur modèle séparément
            joblib.dump(best_model[1], self.models_dir / "best_model.pkl")
        
        logger.info("✅ Entraînement terminé!")
        return trained_models
    
    def save_model_report(self, model_name, results, test_acc, test_auc, X_test, y_test, test_pred, train_size):
        """Sauvegarde un rapport détaillé avec analyse d'overfitting"""
        report_path = self.reports_dir / f"{model_name}_report.txt"
        
        # Analyse overfitting
        overfitting_status = "🟢 Pas d'overfitting détecté"
        if results['overfitting_gap'] > 0.1:
            overfitting_status = "🔴 Overfitting sévère détecté"
        elif results['overfitting_gap'] > 0.05:
            overfitting_status = "🟡 Overfitting modéré détecté"
        
        report_content = f"""
=== Rapport d'entraînement: {model_name} ===
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Hyperparamètres optimaux:
{json.dumps(results['best_params'], indent=2)}

Analyse de l'overfitting:
{overfitting_status}
- Score train CV: {results['train_score']:.4f}
- Score validation CV: {results['val_score']:.4f}
- Écart (Gap): {results['overfitting_gap']:.4f}

Performance Validation:
- Accuracy: {results['val_accuracy']:.4f}
- AUC-ROC: {results['val_auc']:.4f}
- Cross-Validation: {results['cv_mean']:.4f} (±{results['cv_std']:.4f})

Performance Test:
- Accuracy: {test_acc:.4f}
- AUC-ROC: {test_auc:.4f}

Informations dataset:
- Échantillons entraînement: {train_size}
- Échantillons validation: {len(X_test)}
- Échantillons test: {len(X_test)}

Classification Report (Validation):
{results['classification_report']}

Matrice de confusion (Test):
{confusion_matrix(y_test, test_pred)}

Features utilisées: {X_test.shape[1]}
Classes: {list(self.label_encoder.classes_)}

Recommandations anti-overfitting:
- ✓ Cross-validation stratifiée utilisée
- ✓ Régularisation appliquée
- ✓ Équilibrage des classes appliqué
- ✓ Division train/val/test stratifiée
- ✓ Hyperparamètres optimisés pour la généralisation
"""
        
        with open(report_path, 'w') as f:
            f.write(report_content)
    
    def predict_new_data(self, model_name, new_data_df):
        """Fait des prédictions sur de nouvelles données (sans label)"""
        try:
            # Charger le modèle et préprocesseurs
            model_path = self.models_dir / f"{model_name}.pkl"
            preprocessors_path = self.models_dir / "preprocessors.pkl"
            
            if not model_path.exists() or not preprocessors_path.exists():
                logger.error("❌ Modèle ou préprocesseurs introuvables")
                return None
            
            model = joblib.load(model_path)
            preprocessors = joblib.load(preprocessors_path)
            
            # Préprocessing des nouvelles données
            feature_names = preprocessors['feature_names']
            available_features = [col for col in feature_names if col in new_data_df.columns]
            
            X_new = new_data_df[available_features]
            
            # Remplacer valeurs manquantes et infinies
            for col in available_features:
                median_val = X_new[col].median()
                X_new[col] = X_new[col].replace([np.inf, -np.inf], np.nan).fillna(median_val)
            
            # Normaliser
            X_scaled = preprocessors['scaler'].transform(X_new)
            
            # Prédictions
            predictions = model.predict(X_scaled)
            probabilities = model.predict_proba(X_scaled)
            
            # Convertir les prédictions en labels
            predicted_labels = preprocessors['label_encoder'].inverse_transform(predictions)
            
            return {
                'predictions': predicted_labels,
                'probabilities': probabilities,
                'confidence': np.max(probabilities, axis=1)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur prédiction: {e}")
            return None

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Entraîneur ML pour datasets de flow réseau')
    parser.add_argument('--quick', action='store_true', 
                       help='Mode quick: limite le dataset à 2000 échantillons pour un entraînement rapide')
    
    args = parser.parse_args()
    
    if args.quick:
        logger.info("🚀 Mode QUICK activé - Entraînement rapide avec 2000 échantillons max")
    
    trainer = NetworkFlowMLTrainer(quick_mode=args.quick)
    
    try:
        models = trainer.train_all_models()
        logger.info(f"🎉 Entraînement terminé! {len(models)} modèles créés.")
        
        if args.quick:
            logger.info("✅ Mode quick terminé - Pour un entraînement complet, lancez sans --quick")
        
        # Test rapide de prédiction
        logger.info("🧪 Test de prédiction...")
        
        # Charger un échantillon pour tester
        datasets_dir = Path("../datasets")
        test_file = next(datasets_dir.glob("*.csv"), None)
        
        if test_file:
            sample_df = pd.read_csv(test_file).head(5)
            # Retirer la colonne Label pour simuler de nouvelles données
            sample_df_no_label = sample_df.drop('Label', axis=1)
            
            # Tester avec le meilleur modèle s'il existe
            if (trainer.models_dir / "best_model.pkl").exists():
                # Utiliser n'importe quel modèle pour le test
                model_files = list(trainer.models_dir.glob("*.pkl"))
                if model_files:
                    model_name = model_files[0].stem
                    if model_name != "preprocessors" and model_name != "best_model":
                        predictions = trainer.predict_new_data(model_name, sample_df_no_label)
                        if predictions:
                            logger.info(f"✅ Test prédictions: {predictions['predictions']}")
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()
