#!/usr/bin/env python3
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
    """ML trainer for network flow datasets"""
    
    def __init__(self, quick_mode=False):
        self.quick_mode = quick_mode
        self.max_samples = 10000 if quick_mode else None
        self.setup_directories()
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.smote = SMOTE(random_state=42)
        self.use_class_balancing = True
        self.cross_val_folds = 3 if quick_mode else 5  # Reduce folds in quick mode
        
        # Numeric features from network dataset
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
        
        # Model configuration with anti-overfitting regularization
        if quick_mode:
            # Simplified configuration for quick mode
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
            # Complete configuration for normal mode
            self.models_config = {
                'random_forest': {
                    'model': RandomForestClassifier,
                    'params': {
                        'n_estimators': [100, 200],
                        'max_depth': [10, 15, 20],  # Limit depth
                        'min_samples_split': [5, 10, 20],  # Increase min_samples_split
                        'min_samples_leaf': [2, 5, 10],   # Add min_samples_leaf
                        'max_features': ['sqrt', 'log2', 0.8],  # Limit features
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'random_state': [42]
                    }
                },
                'gradient_boosting': {
                    'model': GradientBoostingClassifier,
                    'params': {
                        'n_estimators': [100, 150],
                        'learning_rate': [0.05, 0.1, 0.15],
                        'max_depth': [3, 5],
                        'min_samples_split': [10, 20],
                        'min_samples_leaf': [5, 10],
                        'subsample': [0.8, 0.9],
                        'random_state': [42]
                    }
                },
                'logistic_regression': {
                    'model': LogisticRegression,
                    'params': {
                        'C': [0.01, 0.1, 1],
                        'penalty': ['l1', 'l2', 'elasticnet'],
                        'l1_ratio': [0.5],
                        'solver': ['liblinear', 'saga'],
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'random_state': [42],
                        'max_iter': [1000, 2000]
                    }
                },
                'svm': {
                    'model': SVC,
                    'params': {
                        'C': [0.1, 1, 5],
                        'kernel': ['rbf', 'linear'],
                        'gamma': ['scale', 'auto', 0.1, 0.01],
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'probability': [True],
                        'random_state': [42]
                    }
                }
            }
    
    def setup_directories(self):
        """Create necessary directories"""
        self.models_dir = Path("../models") #TODO : Adapt to current directory
        self.reports_dir = Path("../ml_reports")
        
        self.models_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        logger.info(f"Directories created: {self.models_dir}, {self.reports_dir}")
    
    def load_datasets(self):
        """Load all available datasets"""
        logger.info("Loading datasets...")
        
        datasets_dir = Path("../datasets")
        all_data = []
        
        # Search for all CSV files in datasets folder
        if datasets_dir.exists():
            csv_files = list(datasets_dir.glob("*.csv"))
            logger.info(f"CSV files found: {[f.name for f in csv_files]}")
            
            for csv_file in csv_files:
                try:
                    logger.info(f"Loading: {csv_file.name}")
                    df = pd.read_csv(csv_file)

                    # Check that file has Label column
                    if 'Label' in df.columns:
                        logger.info(f"✅ {csv_file.name}: {len(df)} rows, Labels: {df['Label'].value_counts().to_dict()}")
                        all_data.append(df)
                    else:
                        logger.warning(f"⚠️ {csv_file.name}: No 'Label' column, ignored")
                        
                except Exception as e:
                    logger.error(f"❌ Error loading {csv_file.name}: {e}")

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Combined dataset: {len(combined_df)} rows")
            logger.info(f"Label distribution: {combined_df['Label'].value_counts().to_dict()}")
            
            # Apply limitation in quick mode
            if self.quick_mode and self.max_samples and len(combined_df) > self.max_samples:
                logger.info(f"Quick mode activated: limiting to {self.max_samples} samples")
                # Stratified sampling to preserve class distribution
                combined_df = combined_df.groupby('Label').apply(
                    lambda x: x.sample(min(len(x), self.max_samples // combined_df['Label'].nunique()), 
                                     random_state=42)
                ).reset_index(drop=True)
                logger.info(f"Limited dataset: {len(combined_df)} rows")
                logger.info(f"New distribution: {combined_df['Label'].value_counts().to_dict()}")
            
            return combined_df
        else:
            logger.error("No valid dataset found")
            return None
    
    def preprocess_data(self, df):
        """Preprocess the data"""
        logger.info("Preprocessing data...")
        
        df_processed = df.copy()
        
        # Select only available numeric features
        available_numeric_features = [col for col in self.numeric_features if col in df_processed.columns]
        logger.info(f"Available numeric features: {len(available_numeric_features)}/{len(self.numeric_features)}")
        
        # Check missing values
        missing_info = df_processed[available_numeric_features].isnull().sum()
        if missing_info.sum() > 0:
            logger.warning(f"Missing values detected:")
            for col, missing in missing_info[missing_info > 0].items():
                logger.warning(f"  - {col}: {missing} missing values")
        
        # Replace missing values with median
        for col in available_numeric_features:
            if df_processed[col].isnull().sum() > 0:
                median_val = df_processed[col].median()
                df_processed[col].fillna(median_val, inplace=True)
        
        # Replace infinite values
        df_processed = df_processed.replace([np.inf, -np.inf], np.nan)
        for col in available_numeric_features:
            if df_processed[col].isnull().sum() > 0:
                median_val = df_processed[col].median()
                df_processed[col].fillna(median_val, inplace=True)
        
        # Prepare features and target
        X = df_processed[available_numeric_features]
        y = df_processed['Label']
        
        # Encode labels (Benign = 0, Malicious = 1)
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=available_numeric_features)
        
        logger.info(f"Preprocessing completed: {X_scaled.shape[0]} samples, {X_scaled.shape[1]} features")
        logger.info(f"Encoded classes: {dict(zip(self.label_encoder.classes_, range(len(self.label_encoder.classes_))))}")
        
        return X_scaled, y_encoded, available_numeric_features
    
    def balance_dataset(self, X, y, method='smote'):
        """Balance dataset to reduce class bias"""
        logger.info(f"Balancing dataset with {method}...")
        
        # Original distribution
        unique, counts = np.unique(y, return_counts=True)
        logger.info(f"Distribution before: {dict(zip(self.label_encoder.classes_[unique], counts))}")
        
        try:
            if method == 'smote':
                # SMOTE to generate synthetic samples of minority class
                X_balanced, y_balanced = self.smote.fit_resample(X, y)
                
            elif method == 'undersample':
                # Undersample majority class
                undersampler = RandomUnderSampler(random_state=42, sampling_strategy=0.5)  # 2:1 ratio
                X_balanced, y_balanced = undersampler.fit_resample(X, y)
                
            elif method == 'combined':
                # SMOTE + undersampling combination
                smote_enn = SMOTEENN(random_state=42)
                X_balanced, y_balanced = smote_enn.fit_resample(X, y)
                
            else:
                logger.warning(f"Unknown method {method}, no balancing")
                return X, y
            
            # Distribution after balancing
            unique_after, counts_after = np.unique(y_balanced, return_counts=True)
            logger.info(f"Distribution after: {dict(zip(self.label_encoder.classes_[unique_after], counts_after))}")
            logger.info(f"Balancing completed: {len(X)} → {len(X_balanced)} samples")
            
            return X_balanced, y_balanced
            
        except Exception as e:
            logger.error(f"Balancing error: {e}")
            return X, y
    
    def train_model(self, model_name, model_config, X_train, y_train, X_val, y_val):
        """Train a model with hyperparameter optimization and robust validation"""
        logger.info(f"Training {model_name}...")
        
        try:
            # Stratified cross-validation to handle imbalance
            stratified_cv = StratifiedKFold(n_splits=self.cross_val_folds, shuffle=True, random_state=42)
            
            # Grid Search with stratified validation
            grid_search = GridSearchCV(
                model_config['model'](),
                model_config['params'],
                cv=stratified_cv,
                scoring='roc_auc',  # Better metric for imbalanced data
                n_jobs=-1,
                verbose=2,
                return_train_score=True  # To detect overfitting
            )
            
            grid_search.fit(X_train, y_train)
            best_model = grid_search.best_estimator_
            
            # Analyze overfitting with train vs validation scores
            train_scores = grid_search.cv_results_['mean_train_score']
            val_scores = grid_search.cv_results_['mean_test_score']
            best_idx = grid_search.best_index_
            
            train_score_best = train_scores[best_idx]
            val_score_best = val_scores[best_idx]
            overfitting_gap = train_score_best - val_score_best
            
            # Predictions on validation
            val_pred = best_model.predict(X_val)
            val_proba = best_model.predict_proba(X_val)[:, 1]
            
            # Metrics
            val_accuracy = accuracy_score(y_val, val_pred)
            val_auc = roc_auc_score(y_val, val_proba)
            
            # Final cross-validation
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
            
            # Overfitting alerts
            if overfitting_gap > 0.05:
                logger.warning(f"{model_name}: Possible overfitting detected (gap: {overfitting_gap:.3f})")
            
            logger.info(f"{model_name}: Accuracy={val_accuracy:.3f}, AUC={val_auc:.3f}, "
                       f"CV={cv_scores.mean():.3f}(±{cv_scores.std():.3f}), Gap={overfitting_gap:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error {model_name}: {e}")
            return None
    
    def train_all_models(self):
        """Train all models"""
        logger.info("Starting training...")
        
        # Load data
        df = self.load_datasets()
        if df is None:
            return {}
        
        # Preprocessing
        X, y, feature_names = self.preprocess_data(df)
        
        # Train/validation/test split (test first to keep original balance)
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
        )
        
        # Balance only training data
        if self.use_class_balancing:
            logger.info("Applying class balancing...")
            X_train_balanced, y_train_balanced = self.balance_dataset(X_train, y_train, method='smote')
        else:
            X_train_balanced, y_train_balanced = X_train, y_train
        
        logger.info(f"Split: Train={len(X_train_balanced)}, Val={len(X_val)}, Test={len(X_test)}")
        
        # Train all models
        trained_models = {}
        best_model = None
        best_auc = 0
        
        for model_name, model_config in self.models_config.items():
            result = self.train_model(model_name, model_config, X_train_balanced, y_train_balanced, X_val, y_val)
            
            if result:
                trained_models[model_name] = result
                
                # Final test
                test_pred = result['model'].predict(X_test)
                test_proba = result['model'].predict_proba(X_test)[:, 1]
                test_accuracy = accuracy_score(y_test, test_pred)
                test_auc = roc_auc_score(y_test, test_proba)
                
                logger.info(f"{model_name} Test: Accuracy={test_accuracy:.3f}, AUC={test_auc:.3f}")
                
                # Keep best model
                if test_auc > best_auc:
                    best_auc = test_auc
                    best_model = (model_name, result['model'])
                
                # Save model
                model_path = self.models_dir / f"{model_name}.pkl"
                joblib.dump(result['model'], model_path)
                logger.info(f"Model saved: {model_path}")
                
                # Detailed report
                self.save_model_report(model_name, result, test_accuracy, test_auc, 
                                     X_test, y_test, test_pred, len(X_train_balanced))
        
        # Save preprocessors
        preprocessors = {
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_names': feature_names
        }
        joblib.dump(preprocessors, self.models_dir / "preprocessors.pkl")
        
        if best_model:
            logger.info(f"Best model: {best_model[0]} (Test AUC: {best_auc:.3f})")
            # Save best model separately
            joblib.dump(best_model[1], self.models_dir / "best_model.pkl")
        
        logger.info("Training completed!")
        return trained_models
    
    def save_model_report(self, model_name, results, test_acc, test_auc, X_test, y_test, test_pred, train_size):
        """Save detailed report with overfitting analysis"""
        report_path = self.reports_dir / f"{model_name}_report.txt"
        
        # Overfitting analysis
        overfitting_status = "No overfitting detected"
        if results['overfitting_gap'] > 0.1:
            overfitting_status = "Severe overfitting detected"
        elif results['overfitting_gap'] > 0.05:
            overfitting_status = "Moderate overfitting detected"
        
        report_content = f"""
=== Training Report: {model_name} ===
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Optimal Hyperparameters:
{json.dumps(results['best_params'], indent=2)}

Overfitting Analysis:
{overfitting_status}
- Train CV score: {results['train_score']:.4f}
- Validation CV score: {results['val_score']:.4f}
- Gap: {results['overfitting_gap']:.4f}

Validation Performance:
- Accuracy: {results['val_accuracy']:.4f}
- AUC-ROC: {results['val_auc']:.4f}
- Cross-Validation: {results['cv_mean']:.4f} (±{results['cv_std']:.4f})

Test Performance:
- Accuracy: {test_acc:.4f}
- AUC-ROC: {test_auc:.4f}

Dataset Information:
- Training samples: {train_size}
- Validation samples: {len(X_test)}
- Test samples: {len(X_test)}

Classification Report (Validation):
{results['classification_report']}

Confusion Matrix (Test):
{confusion_matrix(y_test, test_pred)}

Features used: {X_test.shape[1]}
Classes: {list(self.label_encoder.classes_)}

Anti-overfitting Recommendations:
- ✓ Stratified cross-validation used
- ✓ Regularization applied
- ✓ Class balancing applied
- ✓ Stratified train/val/test split
- ✓ Hyperparameters optimized for generalization
"""
        
        with open(report_path, 'w') as f:
            f.write(report_content)
    
    def predict_new_data(self, model_name, new_data_df):
        """Make predictions on new data (without labels)"""
        try:
            # Load model and preprocessors
            model_path = self.models_dir / f"{model_name}.pkl"
            preprocessors_path = self.models_dir / "preprocessors.pkl"
            
            if not model_path.exists() or not preprocessors_path.exists():
                logger.error("Model or preprocessors not found")
                return None
            
            model = joblib.load(model_path)
            preprocessors = joblib.load(preprocessors_path)
            
            # Preprocess new data
            feature_names = preprocessors['feature_names']
            available_features = [col for col in feature_names if col in new_data_df.columns]
            
            X_new = new_data_df[available_features]
            
            # Replace missing and infinite values
            for col in available_features:
                median_val = X_new[col].median()
                X_new[col] = X_new[col].replace([np.inf, -np.inf], np.nan).fillna(median_val)
            
            # Normalize
            X_scaled = preprocessors['scaler'].transform(X_new)
            
            # Predictions
            predictions = model.predict(X_scaled)
            probabilities = model.predict_proba(X_scaled)
            
            # Convert predictions to labels
            predicted_labels = preprocessors['label_encoder'].inverse_transform(predictions)
            
            return {
                'predictions': predicted_labels,
                'probabilities': probabilities,
                'confidence': np.max(probabilities, axis=1)
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='ML trainer for network flow datasets')
    parser.add_argument('--quick', action='store_true', 
                       help='Quick mode: limit dataset to 2000 samples for fast training')
    
    args = parser.parse_args()
    
    if args.quick:
        logger.info("QUICK mode activated - Fast training with 2000 max samples")
    
    trainer = NetworkFlowMLTrainer(quick_mode=args.quick)
    
    try:
        models = trainer.train_all_models()
        logger.info(f"Training completed! {len(models)} models created.")
        
        if args.quick:
            logger.info("Quick mode completed - For full training, run without --quick")
        
        # Quick prediction test
        logger.info("Testing prediction...")
        
        # Load sample for testing
        datasets_dir = Path("../datasets")
        test_file = next(datasets_dir.glob("*.csv"), None)
        
        if test_file:
            sample_df = pd.read_csv(test_file).head(5)
            # Remove Label column to simulate new data
            sample_df_no_label = sample_df.drop('Label', axis=1)
            
            # Test with best model if it exists
            if (trainer.models_dir / "best_model.pkl").exists():
                # Use any model for testing
                model_files = list(trainer.models_dir.glob("*.pkl"))
                if model_files:
                    model_name = model_files[0].stem
                    if model_name != "preprocessors" and model_name != "best_model":
                        predictions = trainer.predict_new_data(model_name, sample_df_no_label)
                        if predictions:
                            logger.info(f"Test predictions: {predictions['predictions']}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
