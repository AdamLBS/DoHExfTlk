# Machine Learning Analysis Guide

## 🤖 Overview

The ML component of the DoH Exfiltration Detection Platform uses supervised learning to classify network flows as benign or malicious. This guide covers the machine learning pipeline, models, and analysis techniques.

## 📊 Dataset and Features

### CIRA-CIC-DoHBrw-2020 Dataset

The platform uses the **CIRA-CIC-DoHBrw-2020** dataset for training and evaluation:

**Dataset Information:**
- **Source**: https://www.unb.ca/cic/datasets/dohbrw-2020.html
- **Provider**: Canadian Institute for Cybersecurity (CIC)
- **Content**: Comprehensive DoH traffic flows (benign and malicious)
- **Format**: CSV files with extracted network flow features
- **Size**: Multiple CSV files containing thousands of labeled flow records
- **Location**: CSV files should be placed in the `datasets/` directory

**Key Features:**
- Real-world DoH traffic captures
- Balanced dataset with benign and malicious samples
- Comprehensive feature set for flow-based analysis
- Pre-labeled data for supervised learning
- Suitable for binary and multi-class classification

### Dataset Structure
The platform works with network flow datasets containing statistical features extracted from DoH traffic:

```csv
SourcePort,DestinationPort,Duration,FlowBytesSent,FlowBytesReceived,
PacketLengthMean,PacketLengthVariance,PacketTimeMean,PacketTimeVariance,
ResponseTimeTimeMean,Label
53,443,1.234,1024,2048,128.5,45.2,0.1,0.02,0.05,Benign
8080,443,2.456,2048,1024,256.7,128.4,0.2,0.08,0.12,Malicious
```

### Feature Categories

#### 1. Basic Flow Features
- **SourcePort**: Source port number
- **DestinationPort**: Destination port number  
- **Duration**: Flow duration in seconds
- **FlowBytesSent**: Total bytes sent
- **FlowBytesReceived**: Total bytes received
- **FlowSentRate**: Bytes sent per second
- **FlowReceivedRate**: Bytes received per second

#### 2. Packet Length Statistics
- **PacketLengthMean**: Average packet size
- **PacketLengthMedian**: Median packet size
- **PacketLengthMode**: Most frequent packet size
- **PacketLengthVariance**: Packet size variance
- **PacketLengthStandardDeviation**: Packet size std dev
- **PacketLengthSkewFromMedian**: Skewness from median
- **PacketLengthCoefficientofVariation**: Coefficient of variation

#### 3. Packet Timing Statistics
- **PacketTimeMean**: Average inter-packet time
- **PacketTimeMedian**: Median inter-packet time
- **PacketTimeVariance**: Inter-packet time variance
- **PacketTimeStandardDeviation**: Inter-packet time std dev
- **PacketTimeCoefficientofVariation**: Timing coefficient of variation

#### 4. Response Time Statistics
- **ResponseTimeTimeMean**: Average response time
- **ResponseTimeTimeMedian**: Median response time
- **ResponseTimeTimeVariance**: Response time variance
- **ResponseTimeTimeStandardDeviation**: Response time std dev

## 🔬 Model Architecture

### Available Models

#### 1. Random Forest Classifier
```python
RandomForestClassifier(
    n_estimators=100-200,
    max_depth=10-20,
    min_samples_split=5-20,
    min_samples_leaf=2-10,
    max_features='sqrt'|'log2'|0.8,
    class_weight='balanced',
    random_state=42
)
```

**Advantages:**
- Robust to overfitting
- Handles mixed data types well
- Provides feature importance
- Good baseline performance

**Use Cases:**
- General purpose classification
- Feature importance analysis
- Robust to noisy data

#### 2. Gradient Boosting Classifier
```python
GradientBoostingClassifier(
    n_estimators=100-150,
    learning_rate=0.05-0.15,
    max_depth=3-5,
    min_samples_split=10-20,
    min_samples_leaf=5-10,
    subsample=0.8-0.9,
    random_state=42
)
```

**Advantages:**
- High predictive accuracy
- Handles complex patterns
- Sequential error correction
- Good for structured data

**Use Cases:**
- High-accuracy requirements
- Complex pattern detection
- Competition-level performance

#### 3. Logistic Regression
```python
LogisticRegression(
    C=0.01-1.0,
    penalty='l1'|'l2'|'elasticnet',
    solver='liblinear'|'saga',
    class_weight='balanced',
    max_iter=1000-2000,
    random_state=42
)
```

**Advantages:**
- Fast training and prediction
- Interpretable coefficients
- Probabilistic output
- Linear decision boundary

**Use Cases:**
- Real-time classification
- Interpretability requirements
- Linear separable data

#### 4. Support Vector Machine (SVM)
```python
SVC(
    C=0.1-5.0,
    kernel='rbf'|'linear',
    gamma='scale'|'auto'|0.01-0.1,
    class_weight='balanced',
    probability=True,
    random_state=42
)
```

**Advantages:**
- Effective in high dimensions
- Memory efficient
- Versatile (different kernels)
- Works well with small datasets

**Use Cases:**
- High-dimensional data
- Non-linear patterns (RBF kernel)
- Memory-constrained environments

## 🎯 Training Pipeline

### 1. Data Preprocessing

#### Data Loading and Validation
```python
def load_datasets():
    """Load and combine multiple CSV datasets"""
    datasets_dir = Path("../datasets")
    csv_files = list(datasets_dir.glob("*.csv"))
    
    combined_df = pd.concat([
        pd.read_csv(f) for f in csv_files 
        if 'Label' in pd.read_csv(f).columns
    ], ignore_index=True)
    
    return combined_df
```

#### Feature Selection and Cleaning
```python
def preprocess_data(df):
    """Clean and prepare features"""
    # Select numeric features
    numeric_features = [col for col in FEATURE_LIST if col in df.columns]
    
    # Handle missing values
    for col in numeric_features:
        df[col].fillna(df[col].median(), inplace=True)
    
    # Handle infinite values
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(df.median(), inplace=True)
    
    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[numeric_features])
    
    return X_scaled, df['Label'].values
```

#### Class Balance Handling
```python
def balance_dataset(X, y, method='smote'):
    """Handle class imbalance"""
    if method == 'smote':
        smote = SMOTE(random_state=42)
        X_balanced, y_balanced = smote.fit_resample(X, y)
    elif method == 'undersample':
        undersampler = RandomUnderSampler(random_state=42)
        X_balanced, y_balanced = undersampler.fit_resample(X, y)
    
    return X_balanced, y_balanced
```

### 2. Model Training and Validation

#### Cross-Validation Strategy
```python
def train_model(model_name, model_config, X_train, y_train):
    """Train with stratified cross-validation"""
    stratified_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    grid_search = GridSearchCV(
        model_config['model'](),
        model_config['params'],
        cv=stratified_cv,
        scoring='roc_auc',
        n_jobs=-1,
        return_train_score=True
    )
    
    grid_search.fit(X_train, y_train)
    return grid_search.best_estimator_
```

#### Overfitting Detection
```python
def detect_overfitting(grid_search):
    """Analyze train vs validation scores"""
    train_scores = grid_search.cv_results_['mean_train_score']
    val_scores = grid_search.cv_results_['mean_test_score']
    best_idx = grid_search.best_index_
    
    overfitting_gap = train_scores[best_idx] - val_scores[best_idx]
    
    if overfitting_gap > 0.05:
        return "Overfitting detected"
    return "No overfitting"
```

### 3. Model Evaluation

#### Performance Metrics
```python
def evaluate_model(model, X_test, y_test):
    """Comprehensive model evaluation"""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'auc': roc_auc_score(y_test, y_proba),
        'confusion_matrix': confusion_matrix(y_test, y_pred)
    }
    
    return metrics
```

#### ROC and Precision-Recall Analysis
```python
def plot_performance_curves(model, X_test, y_test):
    """Generate ROC and PR curves"""
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    auc_score = auc(fpr, tpr)
    
    # Precision-Recall Curve
    precision, recall, _ = precision_recall_curve(y_test, y_proba)
    pr_auc = auc(recall, precision)
    
    return {
        'roc': {'fpr': fpr, 'tpr': tpr, 'auc': auc_score},
        'pr': {'precision': precision, 'recall': recall, 'auc': pr_auc}
    }
```

## 📈 Feature Analysis

### Feature Importance Analysis
```python
def analyze_feature_importance(model, feature_names):
    """Extract and rank feature importance"""
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
        
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return feature_importance
    
    elif hasattr(model, 'coef_'):
        # For linear models
        importance = np.abs(model.coef_[0])
        
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return feature_importance
```

### Top Discriminative Features

Based on analysis of DoH exfiltration patterns, key features include:

1. **PacketLengthVariance**: Exfiltration often shows irregular packet sizes
2. **PacketTimeMean**: Timing patterns differ between benign and malicious traffic
3. **FlowBytesSent**: Data exfiltration typically involves more outbound data
4. **Duration**: Exfiltration sessions may have characteristic durations
5. **ResponseTimeTimeMean**: DoH exfiltration may show different response patterns

### Correlation Analysis
```python
def analyze_feature_correlations(df, features):
    """Analyze feature correlations and multicollinearity"""
    correlation_matrix = df[features].corr()
    
    # Find highly correlated features (>0.9)
    high_corr_pairs = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            if abs(correlation_matrix.iloc[i, j]) > 0.9:
                high_corr_pairs.append((
                    correlation_matrix.columns[i],
                    correlation_matrix.columns[j],
                    correlation_matrix.iloc[i, j]
                ))
    
    return correlation_matrix, high_corr_pairs
```

## 🚀 Usage Examples

### Quick Training
```bash
# Fast training for development
cd ml_analyzer
python3 model_trainer.py --quick

# View results
cat ../ml_reports/random_forest_report.txt
```

### Production Training
```bash
# Full training with all data
python3 model_trainer.py

# Check all model reports
ls -la ../ml_reports/
```

### Custom Configuration
```python
# Custom ML configuration
from model_trainer import NetworkFlowMLTrainer, MLConfig

# Configure for specific needs
MLConfig.CROSS_VAL_FOLDS = 10  # More thorough validation
MLConfig.MAX_SAMPLES = 100000  # Larger dataset
MLConfig.USE_SMOTE = True      # Handle class imbalance

trainer = NetworkFlowMLTrainer(quick_mode=False)
models = trainer.train_all_models()
```

### Real-time Prediction
```python
# Load trained model for prediction
import joblib
from predictor import MLPredictor

# Load model and preprocessors
model = joblib.load('../models/best_model.pkl')
preprocessors = joblib.load('../models/preprocessors.pkl')

# Create predictor
predictor = MLPredictor(model, preprocessors)

# Predict on new data
new_flows = pd.read_csv('new_traffic.csv')
predictions = predictor.predict(new_flows)

print(f"Malicious flows detected: {predictions['malicious_count']}")
print(f"Confidence scores: {predictions['confidence_scores']}")
```

## 📊 Performance Optimization

### Hyperparameter Tuning
```python
# Advanced hyperparameter tuning
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint, uniform

# Random search for efficiency
param_distributions = {
    'n_estimators': randint(50, 300),
    'max_depth': randint(5, 25),
    'min_samples_split': randint(2, 20),
    'min_samples_leaf': randint(1, 10),
    'max_features': uniform(0.1, 0.9)
}

random_search = RandomizedSearchCV(
    RandomForestClassifier(),
    param_distributions,
    n_iter=100,
    cv=5,
    scoring='roc_auc',
    n_jobs=-1,
    random_state=42
)
```

### Feature Selection
```python
def select_best_features(X, y, k=20):
    """Select top k features using mutual information"""
    from sklearn.feature_selection import SelectKBest, mutual_info_classif
    
    selector = SelectKBest(mutual_info_classif, k=k)
    X_selected = selector.fit_transform(X, y)
    
    selected_features = selector.get_support(indices=True)
    return X_selected, selected_features
```

### Model Ensemble
```python
def create_ensemble_model(models):
    """Create voting ensemble of best models"""
    from sklearn.ensemble import VotingClassifier
    
    ensemble = VotingClassifier(
        estimators=[
            ('rf', models['random_forest']),
            ('gb', models['gradient_boosting']),
            ('lr', models['logistic_regression'])
        ],
        voting='soft'  # Use probabilities
    )
    
    return ensemble
```

## 🔍 Analysis and Interpretation

### Model Interpretability
```python
def explain_prediction(model, X_sample, feature_names):
    """Explain individual predictions using SHAP"""
    import shap
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    # Create explanation plot
    shap.summary_plot(shap_values, X_sample, feature_names)
    
    return shap_values
```

### Error Analysis
```python
def analyze_errors(model, X_test, y_test, feature_names):
    """Analyze misclassified samples"""
    y_pred = model.predict(X_test)
    misclassified = X_test[y_test != y_pred]
    
    # Analyze feature distributions of errors
    error_stats = {}
    for feature in feature_names:
        error_stats[feature] = {
            'mean': misclassified[feature].mean(),
            'std': misclassified[feature].std(),
            'min': misclassified[feature].min(),
            'max': misclassified[feature].max()
        }
    
    return error_stats
```

### Drift Detection
```python
def detect_data_drift(reference_data, new_data, threshold=0.05):
    """Detect distribution drift in new data"""
    from scipy.stats import ks_2samp
    
    drift_results = {}
    for column in reference_data.columns:
        statistic, p_value = ks_2samp(
            reference_data[column], 
            new_data[column]
        )
        
        drift_results[column] = {
            'statistic': statistic,
            'p_value': p_value,
            'drift_detected': p_value < threshold
        }
    
    return drift_results
```

## 📋 Best Practices

### Data Quality
1. **Validation**: Always validate data quality before training
2. **Outliers**: Handle extreme values appropriately
3. **Missing Data**: Use domain-appropriate imputation strategies
4. **Feature Engineering**: Create meaningful derived features

### Model Development
1. **Baseline**: Start with simple models as baselines
2. **Cross-Validation**: Use stratified CV for imbalanced data
3. **Regularization**: Prevent overfitting with appropriate regularization
4. **Ensemble**: Combine multiple models for better performance

### Production Deployment
1. **Monitoring**: Monitor model performance in production
2. **Retraining**: Regular retraining with new data
3. **A/B Testing**: Compare model versions carefully
4. **Fallback**: Have fallback strategies for model failures

### Evaluation Metrics
- **Precision**: Minimize false positives in security contexts
- **Recall**: Ensure high detection of actual attacks
- **F1-Score**: Balance precision and recall
- **AUC-ROC**: Overall discriminative ability
- **AUC-PR**: Performance on imbalanced datasets
