"""
HEART RATE EMOTION DETECTION - IMPROVED TRAINING PIPELINE v4
Using GradientBoosting with aggressive regularization
Target: >85% test accuracy with minimal overfitting
"""

import numpy as np
import pickle
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.metrics import precision_recall_fscore_support
import seaborn as sns

from hrv_features import extract_hrv_features
from collections import Counter
from imblearn.over_sampling import SMOTE


print("="*80)
print(" HEART RATE EMOTION DETECTION - TRAINING PIPELINE v4 (GRADIENT BOOSTING)")
print("="*80)

# ============================================================================
# STEP 1: DATASET PREPARATION
# ============================================================================
print("\n" + "="*80)
print(" STEP 1: LOADING DATA FROM WESAD DATASET")
print("="*80)

X = []
y = []

# Use ALL 8 recommended features for best accuracy
feature_names = ["RMSSD", "SDNN", "MeanNN", "pNN50", "MedianNN", "CVNN", "SD1", "SD2"]

print(f"\n✓ Features to extract: {feature_names}")

# Base folder where all subject folders are
base_path = r"C:\\Users\\rahul\\Desktop\\Main_Proj_imp_POC1\\myprojectenv_poc1\\Datasets\\WESAD\\WESAD"

# Model save folder
model_folder = r"C:\\Users\\rahul\\Desktop\\Heart_Rate_Emotion_Detection\\HR_poc1\\Models"
os.makedirs(model_folder, exist_ok=True)

# Load data from pickle files for each subject
print("\n✓ Processing subjects from WESAD dataset...")

# Try to load pre-extracted features if they exist
feature_cache = os.path.join(model_folder, 'wesad_features_cache.pkl')

if os.path.exists(feature_cache):
    print("  ✓ Loading cached features...")
    with open(feature_cache, 'rb') as f:
        X, y = pickle.load(f)
    print(f"  ✓ Loaded {len(X)} samples from cache")
else:
    # Extract features from WESAD dataset
    SUBJECTS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]  # WESAD subjects
    
    for subject in SUBJECTS:
        subject_folder = os.path.join(base_path, f"S{subject}")
        
        if not os.path.exists(subject_folder):
            print(f"  ⚠ Subject folder not found: {subject_folder}")
            continue
            
        try:
            # Load pickle file for this subject
            pkl_file = os.path.join(subject_folder, f"S{subject}.pkl")
            
            if not os.path.exists(pkl_file):
                print(f"  ⚠ Pickle file not found: {pkl_file}")
                continue
            
            with open(pkl_file, 'rb') as f:
                data = pickle.load(f, encoding='latin1')
            
            # Extract signal and labels
            # WESAD stores ECG in data['signal']['chest']['ECG']
            if 'chest' in data['signal'] and 'ECG' in data['signal']['chest']:
                ecg_signal = data['signal']['chest']['ECG'][:, 0]  # Get single lead
            else:
                print(f"  ⚠ Warning: ECG not found for subject {subject}")
                continue
            
            labels_full = data['label']
            
            # Process ECG signal with 30-second windows (50% overlap)
            fs = 700  # Sampling frequency for WESAD ECG
            window_size = 30 * fs  # 30 seconds
            stride = window_size // 2  # 50% overlap
            
            print(f"  ✓ Subject {subject}: {len(ecg_signal)} samples")
            
            # Extract features from each window
            for start in range(0, len(ecg_signal) - window_size, stride):
                window = ecg_signal[start:start + window_size]
                label_window = int(labels_full[start])  # Label at window start
                
                # Keep only useful classes: 1=Baseline, 2=Stress, 3=Amusement
                if label_window not in [1, 2, 3]:
                    continue
                
                # Extract HRV features
                features = extract_hrv_features(window)
                
                if features is not None:
                    # Convert feature dict to list in correct order
                    feature_list = [features[name] for name in feature_names]
                    X.append(feature_list)
                    
                    # Map label: 1→0 (Neutral), 2→1 (Stress), 3→2 (Amusement)
                    label_mapped = label_window - 1
                    y.append(label_mapped)
        
        except Exception as e:
            print(f"  ⚠ Error processing subject {subject}: {str(e)}")
            continue
    
    # Cache the features
    print(f"\n✓ Caching {len(X)} extracted features...")
    with open(feature_cache, 'wb') as f:
        pickle.dump((X, y), f)

# Convert to numpy arrays
X = np.array(X)
y = np.array(y)

print(f"\n✓ Total samples extracted: {len(X)}")
print(f"✓ Features per sample: {X.shape[1]}")
print(f"\nClass distribution (before SMOTE):")
for label in sorted(np.unique(y)):
    count = np.sum(y == label)
    emotion = ["Neutral", "Stress", "Amusement"][label]
    print(f"  - {emotion}: {count} ({100*count/len(y):.1f}%)")

# Handle NaN and inf values
print("\n✓ Checking for invalid values...")
nan_count = np.isnan(X).sum()
if nan_count > 0:
    print(f"  ⚠ Found {nan_count} NaN values - replacing with 0")
    X = np.nan_to_num(X, nan=0.0)

inf_count = np.isinf(X).sum()
if inf_count > 0:
    print(f"  ⚠ Found {inf_count} inf values - replacing with 0")
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

# ============================================================================
# STEP 2: TRAIN-TEST SPLIT
# ============================================================================
print("\n" + "="*80)
print(" STEP 2: TRAIN-TEST SPLIT (STRATIFIED)")
print("="*80)

# Stratified split: maintain class distribution
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n✓ Train set size: {X_train.shape[0]} samples")
print(f"✓ Test set size: {X_test.shape[0]} samples")
print(f"\nTraining set distribution (before SMOTE):")
for label in sorted(np.unique(y_train)):
    count = np.sum(y_train == label)
    emotion = ["Neutral", "Stress", "Amusement"][label]
    print(f"  - {emotion}: {count}")

# ============================================================================
# STEP 3: HANDLE CLASS IMBALANCE WITH SMOTE
# ============================================================================
print("\n" + "="*80)
print(" STEP 3: HANDLING CLASS IMBALANCE (SMOTE)")
print("="*80)

# Use SMOTE with careful parameters
smote = SMOTE(random_state=42, k_neighbors=5)
X_train, y_train = smote.fit_resample(X_train, y_train)

print(f"\n✓ After SMOTE - Training set size: {X_train.shape[0]} samples")
print(f"✓ Training set distribution (after SMOTE):")
for label in sorted(np.unique(y_train)):
    count = np.sum(y_train == label)
    emotion = ["Neutral", "Stress", "Amusement"][label]
    print(f"  - {emotion}: {count}")

# ============================================================================
# STEP 4: FEATURE SCALING
# ============================================================================
print("\n" + "="*80)
print(" STEP 4: FEATURE SCALING")
print("="*80)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("\n✓ Features scaled using StandardScaler")
print(f"  - Training set mean: {X_train_scaled.mean(axis=0).round(3)}")
print(f"  - Training set std: {X_train_scaled.std(axis=0).round(3)}")

# ============================================================================
# STEP 5: TRAIN GRADIENT BOOSTING MODEL (v4)
# ============================================================================
print("\n" + "="*80)
print(" STEP 5: TRAINING GRADIENT BOOSTING MODEL (v4)")
print("="*80)

# GradientBoosting with AGGRESSIVE regularization
# This algorithm naturally has better regularization than Random Forest
model = GradientBoostingClassifier(
    n_estimators=200,           # Moderate number of boosting stages
    learning_rate=0.05,         # SMALL learning rate = more conservative updates
    max_depth=5,                # SHALLOW trees = less overfitting
    min_samples_split=20,       # Need many samples to split
    min_samples_leaf=10,        # Larger leaf nodes
    subsample=0.8,              # Use 80% of samples for each tree (bagging)
    max_features='sqrt',        # Feature selection strategy
    random_state=42,
    verbose=0
)

print("\n✓ Model hyperparameters (v4 - GRADIENT BOOSTING):")
print(f"  - Algorithm: GradientBoostingClassifier (better regularization)")
print(f"  - n_estimators: {model.n_estimators} boosting stages")
print(f"  - learning_rate: {model.learning_rate} (small = conservative)")
print(f"  - max_depth: {model.max_depth} (shallow trees)")
print(f"  - min_samples_split: {model.min_samples_split}")
print(f"  - min_samples_leaf: {model.min_samples_leaf}")
print(f"  - subsample: {model.subsample} (use 80% of data per tree)")
print(f"\n  Strategy: Use GradientBoosting instead of RandomForest")
print(f"  Benefit: Better regularization, smoother decision boundaries")

print("\n⏳ Training model...")
model.fit(X_train_scaled, y_train)
print("✓ Model training complete!")

# Feature importance
print("\n✓ Feature Importance:")
for fname, imp in zip(feature_names, model.feature_importances_):
    print(f"  - {fname}: {imp:.4f}")

# ============================================================================
# STEP 6: EVALUATION
# ============================================================================
print("\n" + "="*80)
print(" STEP 6: MODEL EVALUATION")
print("="*80)

# Predictions
y_pred_train = model.predict(X_train_scaled)
y_pred_test = model.predict(X_test_scaled)

# Accuracy scores
train_acc = accuracy_score(y_train, y_pred_train)
test_acc = accuracy_score(y_test, y_pred_test)

print(f"\n✓ Training Accuracy: {train_acc*100:.2f}%")
print(f"✓ Test Accuracy: {test_acc*100:.2f}%")

# Check for overfitting
overfitting_gap = train_acc - test_acc
print(f"\n✓ Overfitting Analysis:")
print(f"  - Train-Test Gap: {overfitting_gap*100:.2f}%")
if overfitting_gap > 0.15:
    print(f"  - ⚠ WARNING: Still overfitting! Gap > 15%")
elif overfitting_gap > 0.10:
    print(f"  - ⚠ CAUTION: Slight overfitting detected")
else:
    print(f"  - ✅ Good balance between train/test accuracy")

if test_acc >= 0.85:
    print(f"\n🎉 SUCCESS! Test accuracy {test_acc*100:.2f}% >= 85% target!")
else:
    print(f"\n⚠ Test accuracy {test_acc*100:.2f}% < 85% target")
    if test_acc >= 0.80:
        print(f"  Close to target! Consider:")
        print(f"  1. Try different window sizes (20s, 40s, 60s)")
        print(f"  2. Try SVM or other models")
        print(f"  3. Or use binary classification (87.99% guaranteed)")
    else:
        print(f"  Recommendations:")
        print(f"  1. 3-class task may be too hard for heart rate data alone")
        print(f"  2. Try binary classification (Stress vs Non-Stress: 87.99%)")
        print(f"  3. Try combining with other physiological signals")

# Cross-validation score
print("\n✓ Cross-validation (5-fold):")
cv_scores = cross_val_score(
    model, X_train_scaled, y_train, 
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    scoring='accuracy'
)
print(f"  - CV Scores: {[f'{s*100:.2f}%' for s in cv_scores]}")
print(f"  - Mean CV: {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")

# Classification report
print("\n✓ Classification Report (Test Set):")
print(classification_report(
    y_test, y_pred_test,
    target_names=["Neutral", "Stress", "Amusement"],
    digits=4
))

# Precision, Recall, F1
precision, recall, f1, support = precision_recall_fscore_support(
    y_test, y_pred_test, average='weighted'
)
print(f"✓ Weighted Metrics:")
print(f"  - Precision: {precision:.4f}")
print(f"  - Recall: {recall:.4f}")
print(f"  - F1-Score: {f1:.4f}")

# Confusion matrix
cm = confusion_matrix(y_test, y_pred_test)
print(f"\n✓ Confusion Matrix:")
print(cm)

# ============================================================================
# STEP 7: SAVE MODEL
# ============================================================================
print("\n" + "="*80)
print(" STEP 7: SAVING MODEL")
print("="*80)

# Save model
model_path = os.path.join(model_folder, 'hr_model_improved_v4.pkl')
with open(model_path, 'wb') as f:
    pickle.dump(model, f)
print(f"✓ Model saved: {model_path}")

# Save scaler
scaler_path = os.path.join(model_folder, 'hr_scaler_improved_v4.pkl')
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)
print(f"✓ Scaler saved: {scaler_path}")

# Save feature names
feature_names_path = os.path.join(model_folder, 'feature_names_improved_v4.pkl')
with open(feature_names_path, 'wb') as f:
    pickle.dump(feature_names, f)
print(f"✓ Feature names saved: {feature_names_path}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print(" TRAINING SUMMARY")
print("="*80)

print(f"""
📊 RESULTS:
   - Test Accuracy: {test_acc*100:.2f}%
   - Train Accuracy: {train_acc*100:.2f}%
   - Train-Test Gap: {overfitting_gap*100:.2f}%
   - CV Accuracy: {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%

🎯 TARGET: ≥85% accuracy
   Status: {'✅ ACHIEVED!' if test_acc >= 0.85 else '⚠️ Below target'}

🔍 OVERFITTING CHECK:
   Gap Status: {'✅ Good balance' if overfitting_gap <= 0.10 else ('⚠ Slight overfitting' if overfitting_gap <= 0.15 else '⚠ Significant overfitting')}

📁 FILES SAVED:
   • hr_model_improved_v4.pkl (GradientBoosting)
   • hr_scaler_improved_v4.pkl
   • feature_names_improved_v4.pkl

🔄 COMPARISON:
   • Binary Classification: 87.99% ✅ (easiest)
   • 3-Class v1: 65.54%   (original)
   • 3-Class v2: 67.10%   (overfit)
   • 3-Class v3: 67.89%   (still overfit)
   • 3-Class v4: {test_acc*100:.2f}%  (GradientBoosting)
""")

print("="*80)
