#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, accuracy_score, roc_curve)
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.calibration import CalibratedClassifierCV
from sklearn.utils.validation import check_is_fitted

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTEENN

import joblib
import sklearn

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("trainer")


def pick_threshold_at_fpr(y_true, y_proba, target_fpr=0.01):
    fpr, tpr, thr = roc_curve(y_true, y_proba)
    if len(thr) == 0:
        return 0.5
    idx = np.argmin(np.abs(fpr - target_fpr))
    return float(thr[idx])


class NetworkFlowMLTrainer:
    def __init__(self, quick_mode=False, fpr_target=0.01, group_col=None):
        self.quick_mode = quick_mode
        self.max_samples = 10000 if quick_mode else None
        self.fpr_target = fpr_target
        self.group_col = group_col

        self.setup_directories()

        self.label_encoder = LabelEncoder()

        self.smote = SMOTE(random_state=42)
        self.use_class_balancing = True
        self.cross_val_folds = 3 if quick_mode else 5

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

        if quick_mode:
            self.models_config = {
                'random_forest': {
                    'model': RandomForestClassifier,
                    'params': {
                        'n_estimators': [100],
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
                        'max_iter': [1000],
                        'solver': ['liblinear']
                    }
                }
            }
        else:
            self.models_config = {
                'random_forest': {
                    'model': RandomForestClassifier,
                    'params': {
                        'n_estimators': [100, 200],
                        'max_depth': [10, 15, 20],
                        'min_samples_split': [5, 10, 20],
                        'min_samples_leaf': [2, 5, 10],
                        'max_features': ['sqrt', 'log2', 0.8],
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'random_state': [42]
                    }
                },
                'gradient_boosting': {
                    'model': GradientBoostingClassifier,
                    'params': {
                        'n_estimators': [100, 150],
                        'learning_rate': [0.05, 0.1],
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
                        'penalty': ['l1', 'l2'],
                        'solver': ['liblinear', 'saga'],
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                        'random_state': [42],
                        'max_iter': [2000]
                    }
                },
                'svm': {
                    'model': SVC,
                    'params': {
                        'C': [0.1, 1, 5],
                        'kernel': ['rbf', 'linear'],
                        'gamma': ['scale', 'auto', 0.1],
                        'class_weight': ['balanced'] if self.use_class_balancing else [None],
                    }
                }
            }

    def setup_directories(self):
        self.models_dir = Path("../models")
        self.reports_dir = Path("../ml_reports")
        self.models_dir.mkdir(exist_ok=True, parents=True)
        self.reports_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Directories created: {self.models_dir}, {self.reports_dir}")

    def load_datasets(self):
        logger.info("Loading datasets...")
        datasets_dir = Path("../datasets")
        all_data = []
        if datasets_dir.exists():
            csv_files = list(datasets_dir.glob("*.csv"))
            logger.info(f"CSV files found: {[f.name for f in csv_files]}")
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    if 'Label' in df.columns:
                        logger.info(f"✅ {csv_file.name}: {len(df)} rows, Labels: {df['Label'].value_counts().to_dict()}")
                        all_data.append(df)
                    else:
                        logger.warning(f"⚠️ {csv_file.name}: No 'Label' column, ignored")
                except Exception as e:
                    logger.error(f"❌ Error loading {csv_file.name}: {e}")

        if not all_data:
            logger.error("No valid dataset found")
            return None

        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"Combined dataset: {len(combined_df)} rows")
        logger.info(f"Label distribution: {combined_df['Label'].value_counts().to_dict()}")

        if self.quick_mode and self.max_samples and len(combined_df) > self.max_samples:
            logger.info(f"Quick mode: limiting to {self.max_samples} samples (stratified)")
            combined_df = combined_df.groupby('Label', group_keys=False).apply(
                lambda x: x.sample(
                    min(len(x), self.max_samples // combined_df['Label'].nunique()),
                    random_state=42
                )
            ).reset_index(drop=True)
            logger.info(f"Limited dataset: {len(combined_df)} rows")

        return combined_df

    def preprocess_data(self, df: pd.DataFrame):
        dfp = df.copy()
        available = [c for c in self.numeric_features if c in dfp.columns]

        for col in available:
            s = pd.to_numeric(dfp[col], errors='coerce')
            s = s.replace([np.inf, -np.inf], np.nan)
            if s.isnull().any():
                s = s.fillna(s.median())
            dfp[col] = s

        if 'Label' not in dfp.columns:
            raise ValueError("Column 'Label' not found in dataset")

        X = dfp[available].copy()
        y = self.label_encoder.fit_transform(dfp['Label'])

        logger.info(f"Preprocessing completed: {X.shape[0]} samples, {X.shape[1]} features")
        logger.info(f"Encoded classes: {dict(zip(self.label_encoder.classes_, range(len(self.label_encoder.classes_))))}")
        return X, y, available

    def balance_dataset(self, X, y, method='smote'):
        logger.info(f"Balancing dataset with {method}...")
        unique, counts = np.unique(y, return_counts=True)
        logger.info(f"Distribution before: {dict(zip(unique, counts))}")
        try:
            if method == 'smote':
                Xb, yb = self.smote.fit_resample(X, y)
            elif method == 'undersample':
                rus = RandomUnderSampler(random_state=42, sampling_strategy=0.5)
                Xb, yb = rus.fit_resample(X, y)
            elif method == 'combined':
                smote_enn = SMOTEENN(random_state=42)
                Xb, yb = smote_enn.fit_resample(X, y)
            else:
                logger.warning(f"Unknown method {method}, no balancing")
                return X, y

            unique_after, counts_after = np.unique(yb, return_counts=True)
            logger.info(f"Distribution after : {dict(zip(unique_after, counts_after))}")
            logger.info(f"Balancing completed: {len(X)} → {len(Xb)} samples")
            return Xb, yb
        except Exception as e:
            logger.error(f"Balancing error: {e}")
            return X, y

    def make_pipeline(self, base_model_cls, feature_names):
        coltx = ColumnTransformer(
            transformers=[("num", StandardScaler(), feature_names)],
            remainder="drop"
        )

        if base_model_cls is SVC or base_model_cls.__name__.lower() == "svc":
            base_model = base_model_cls(probability=True, random_state=42)
        else:
            try:
                base_model = base_model_cls(random_state=42)
            except TypeError:
                base_model = base_model_cls()

        clf = CalibratedClassifierCV(estimator=base_model, method='isotonic', cv=3)

        pipe = Pipeline(steps=[("pre", coltx), ("clf", clf)])
        return pipe

    def param_grid_for(self, model_config):
        return {f"clf__estimator__{k}": v for k, v in model_config['params'].items()}

    def train_model(self, model_name, model_config, X_train, y_train, X_val, y_val, feature_names):
        logger.info(f"Training {model_name}...")
        pipe = self.make_pipeline(model_config['model'], feature_names)
        param_grid = self.param_grid_for(model_config)

        cv = StratifiedKFold(n_splits=self.cross_val_folds, shuffle=True, random_state=42)

        grid = GridSearchCV(
            estimator=pipe,
            param_grid=param_grid,
            cv=cv,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=2,
            return_train_score=True
        )

        grid.fit(X_train, y_train)
        best_pipe = grid.best_estimator_

        val_proba = best_pipe.predict_proba(X_val)[:, 1]
        val_pred_default = (val_proba >= 0.5).astype(int)
        thr = pick_threshold_at_fpr(y_val, val_proba, target_fpr=self.fpr_target)
        val_pred_tuned = (val_proba >= thr).astype(int)

        val_acc_default = accuracy_score(y_val, val_pred_default)
        val_acc_tuned = accuracy_score(y_val, val_pred_tuned)
        val_auc = roc_auc_score(y_val, val_proba)

        train_scores = grid.cv_results_['mean_train_score']
        val_scores = grid.cv_results_['mean_test_score']
        best_idx = grid.best_index_
        overfit_gap = float(train_scores[best_idx] - val_scores[best_idx])

        logger.info(
            f"{model_name}: Val AUC={val_auc:.3f} | Val Acc@0.5={val_acc_default:.3f} | "
            f"Val Acc@thr={val_acc_tuned:.3f} (thr={thr:.3f}) | Gap={overfit_gap:.3f}"
        )

        return {
            "pipeline": best_pipe,
            "best_params": grid.best_params_,
            "val_auc": float(val_auc),
            "val_acc_default": float(val_acc_default),
            "val_acc_tuned": float(val_acc_tuned),
            "threshold": float(thr),
            "overfitting_gap": float(overfit_gap),
        }

    def train_all_models(self):
        logger.info("Starting training...")

        df = self.load_datasets()
        if df is None:
            return {}

        X_all, y_all, feature_names = self.preprocess_data(df)

        X_temp, X_test, y_temp, y_test = train_test_split(
            X_all, y_all, test_size=0.2, random_state=42, stratify=y_all
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
        )

        if self.use_class_balancing:
            X_train_bal, y_train_bal = self.balance_dataset(X_train, y_train, method='smote')
        else:
            X_train_bal, y_train_bal = X_train, y_train

        logger.info(f"Split sizes: Train={len(X_train_bal)}, Val={len(X_val)}, Test={len(X_test)}")

        trained = {}
        best_model_name = None
        best_auc = -np.inf
        thresholds_registry = {}

        for model_name, cfg in self.models_config.items():
            res = self.train_model(model_name, cfg, X_train_bal, y_train_bal, X_val, y_val, feature_names)
            if not res:
                continue

            pipe = res["pipeline"]
            thr = res["threshold"]

            test_proba = pipe.predict_proba(X_test)[:, 1]
            test_pred_default = (test_proba >= 0.5).astype(int)
            test_pred_tuned = (test_proba >= thr).astype(int)

            test_auc = roc_auc_score(y_test, test_proba)
            test_acc_default = accuracy_score(y_test, test_pred_default)
            test_acc_tuned = accuracy_score(y_test, test_pred_tuned)

            logger.info(f"{model_name} Test: AUC={test_auc:.3f} | Acc@0.5={test_acc_default:.3f} | "
                        f"Acc@thr({thr:.3f})={test_acc_tuned:.3f}")

            model_path = self.models_dir / f"{model_name}.pkl"
            joblib.dump(pipe, model_path)
            logger.info(f"Model (pipeline) saved: {model_path}")

            try:
                pre = pipe.named_steps['pre']
                scaler = None
                for name, trans, cols in pre.transformers_:
                    if name == 'num':
                        scaler = trans
                        break
                preprocessors = {
                    'scaler': scaler,
                    'label_encoder': self.label_encoder,
                    'feature_names': feature_names
                }
                joblib.dump(preprocessors, self.models_dir / "preprocessors.pkl")
            except Exception as e:
                logger.warning(f"Could not export preprocessors.pkl: {e}")

            thresholds_registry[model_name] = {
                "threshold": thr,
                "picked_on": "validation",
                "target_fpr": self.fpr_target
            }
            with open(self.models_dir / "thresholds.json", "w") as f:
                json.dump(thresholds_registry, f, indent=2)

            trained[model_name] = {
                "path": str(model_path),
                "val_auc": res["val_auc"],
                "test_auc": float(test_auc),
                "threshold": thr
            }

            if test_auc > best_auc:
                best_auc = test_auc
                best_model_name = model_name
                joblib.dump(pipe, self.models_dir / "best_model.pkl")

        meta = {
            "sklearn_version": sklearn.__version__,
            "trained_at": datetime.now().isoformat(),
            "features": feature_names,
            "label_classes": list(self.label_encoder.classes_),
            "best_model": best_model_name,
            "fpr_target": self.fpr_target
        }
        with open(self.models_dir / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

        logger.info(f"Training completed! Best: {best_model_name} (AUC={best_auc:.3f})")
        return trained


def main():
    parser = argparse.ArgumentParser(description="Network flow ML trainer (Pipeline + Calibration + Threshold)")
    parser.add_argument('--quick', action='store_true', help='Quick mode')
    parser.add_argument('--fpr', type=float, default=0.01, help='FPR target for threshold tuning (default: 0.01)')
    args = parser.parse_args()

    logger.info(f"scikit-learn version: {sklearn.__version__}")
    if args.quick:
        logger.info("QUICK mode activated")

    trainer = NetworkFlowMLTrainer(quick_mode=args.quick, fpr_target=args.fpr)
    try:
        trainer.train_all_models()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
