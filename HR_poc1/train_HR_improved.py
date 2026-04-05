"""
HEART RATE EMOTION DETECTION - IMPROVED TRAINING PIPELINE
Optimized for WESAD dataset to achieve >85% accuracy
"""

import numpy as np
import pickle
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
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
print(" HEART RATE EMOTION DETECTION - TRAINING PIPELINE v2 (IMPROVED)")
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
print(f"  - RMSSD: Root Mean Square of Successive Differences (stress indicator)")
print(f"  - SDNN: Standard Deviation of NN intervals (overall variability)")
print(f"  - MeanNN: Mean of NN intervals")
print(f"  - pNN50: Percentage of NN50 (heart rate variation)")
print(f"  - MedianNN, CVNN, SD1, SD2: Additional HRV features")

# Base folder where all subject folders are
base_path = r"C:\\Users\\rahul\\Desktop\\Main_Proj_imp_POC1\\myprojectenv_poc1\\Datasets\\WESAD\\WESAD"

# List of subjects to use (skip S1 and S12 - often have issues)
subjects = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]

print(f"\n✓ Subjects to process: {subjects}")

window_count = 0
successful_subjects = 0
failed_subjects = []

for subject in subjects:
    subject_folder = os.path.join(base_path, f"S{subject}")
    pkl_file = os.path.join(subject_folder, f"S{subject}.pkl")
    
    try:
        # Load subject data
        with open(pkl_file, "rb") as f:
            data = pickle.load(f, encoding='latin1')

        # ECG from chest (ECG at 700 Hz)
        if 'chest' not in data['signal'] or 'ECG' not in data['signal']['chest']:
            print(f"  ✗ S{subject}: ECG signal not found, skipping")
            failed_subjects.append(subject)
            continue

        ecg_signal_full = data['signal']['chest']['ECG']
        labels_full = data['label']
        
        successful_subjects += 1

        # **KEY IMPROVEMENT**: Use 30-second windows with 50% overlap
        # 30 seconds is optimal for HRV feature extraction
        window_size = 21000  # 30 seconds at 700 Hz
        stride = 10500      # 50% overlap = 15 seconds stride
        
        subject_windows = 0
        for start in range(0, len(ecg_signal_full) - window_size, stride):
            ecg_window = ecg_signal_full[start:start + window_size, 0]
            label_window = int(labels_full[start])

            # Keep only useful emotion classes
            if label_window not in [1, 2, 3]:
                continue

            # Map WESAD labels to emotion classes
            label_map = {
                1: 0,  # Baseline → Neutral
                2: 1,  # Stress
                3: 2   # Amusement
            }

            y.append(label_map[label_window])

            # Extract HRV features
            features = extract_hrv_features(ecg_window)
            X.append([features[name] for name in feature_names])
            
            subject_windows += 1
            window_count += 1
        
        print(f"  ✓ S{subject}: Extracted {subject_windows} windows")
        
    except Exception as e:
        print(f"  ✗ S{subject}: Error - {str(e)}")
        failed_subjects.append(subject)
        continue

X = np.array(X)
y = np.array(y)

# Dataset Statistics
print("\n" + "-"*80)
print(" DATASET STATISTICS")
print("-"*80)
print(f"✓ Successfully processed: {successful_subjects}/{len(subjects)} subjects")
if failed_subjects:
    print(f"⚠ Failed subjects: {failed_subjects}")
print(f"✓ Total windows extracted: {window_count}")
print(f"✓ Feature matrix shape: {X.shape}")
print(f"✓ Label vector shape: {y.shape}")
print(f"\n✓ Label distribution:")
label_counts = dict(Counter(y))
for label, count in sorted(label_counts.items()):
    emotion = ["Neutral", "Stress", "Amusement"][label]
    percentage = (count / len(y)) * 100
    print(f"  - {emotion} ({label}): {count} samples ({percentage:.1f}%)")

# Check for NaN values
nan_count = np.isnan(X).sum()
if nan_count > 0:
    print(f"\n⚠ WARNING: Found {nan_count} NaN values in features!")
    print("  Replacing NaN with 0...")
    X = np.nan_to_num(X, nan=0.0)

# ============================================================================
# STEP 2: TRAIN-TEST SPLIT
# ============================================================================
print("\n" + "="*80)
print(" STEP 2: TRAIN-TEST SPLIT")
print("="*80)

# Stratified split: maintain class distribution
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n✓ Train set size: {X_train.shape[0]} samples")
print(f"✓ Test set size: {X_test.shape[0]} samples")
print(f"\nBefore SMOTE - Training set distribution:")
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

smote = SMOTE(random_state=42, k_neighbors=5)
X_train, y_train = smote.fit_resample(X_train, y_train)

print(f"\n✓ After SMOTE - Training set size: {X_train.shape[0]} samples")
print(f"✓ After SMOTE - Training set distribution:")
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
# STEP 5: TRAIN RANDOM FOREST MODEL
# ============================================================================
print("\n" + "="*80)
print(" STEP 5: TRAINING RANDOM FOREST MODEL")
print("="*80)

# **OPTIMIZED HYPERPARAMETERS** for better accuracy
model = RandomForestClassifier(
    n_estimators=500,        # More trees for better generalization
    max_depth=15,            # Deeper trees to capture patterns
    min_samples_split=4,     # Split with fewer samples
    min_samples_leaf=2,      # Leaf nodes can be smaller
    max_features='sqrt',     # Feature selection strategy
    random_state=42,
    class_weight='balanced', # Handle remaining imbalance
    n_jobs=-1,              # Use all CPU cores
    verbose=0
)

print("\n✓ Model hyperparameters:")
print(f"  - n_estimators: {model.n_estimators} trees")
print(f"  - max_depth: {model.max_depth}")
print(f"  - min_samples_split: {model.min_samples_split}")
print(f"  - min_samples_leaf: {model.min_samples_leaf}")
print(f"  - class_weight: balanced")

print("\n⏳ Training model...")
model.fit(X_train_scaled, y_train)
print("✓ Model training complete!")

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

print(f"\n✓ ACCURACY RESULTS:")
print(f"  - Training accuracy: {train_acc * 100:.2f}%")
print(f"  - Test accuracy: {test_acc * 100:.2f}%")

# Cross-validation
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')

print(f"\n✓ CROSS-VALIDATION RESULTS (5-Fold):")
print(f"  - CV scores: {[f'{s:.2%}' for s in cv_scores]}")
print(f"  - Mean CV accuracy: {cv_scores.mean() * 100:.2f}%")
print(f"  - Std CV accuracy: {cv_scores.std() * 100:.2f}%")

# Detailed classification report
print(f"\n✓ CLASSIFICATION REPORT (Test Set):")
print(classification_report(
    y_test, y_pred_test,
    target_names=["Neutral", "Stress", "Amusement"],
    digits=4
))

# Per-class metrics
precision, recall, f1, support = precision_recall_fscore_support(
    y_test, y_pred_test, average=None
)

print(f"\n✓ PER-CLASS METRICS (Test Set):")
for i, emotion in enumerate(["Neutral", "Stress", "Amusement"]):
    print(f"  - {emotion}:")
    print(f"    Precision: {precision[i]:.4f}")
    print(f"    Recall: {recall[i]:.4f}")
    print(f"    F1-Score: {f1[i]:.4f}")
    print(f"    Support: {support[i]}")

# ============================================================================
# STEP 7: FEATURE IMPORTANCE
# ============================================================================
print("\n" + "="*80)
print(" STEP 7: FEATURE IMPORTANCE ANALYSIS")
print("="*80)

importances = model.feature_importances_

print(f"\n✓ Feature importance scores:")
for name, importance in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True):
    print(f"  - {name}: {importance:.4f}")

# Create visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Feature importance bar plot
sorted_idx = np.argsort(importances)
ax1.barh(np.array(feature_names)[sorted_idx], importances[sorted_idx])
ax1.set_xlabel('Importance')
ax1.set_title('Feature Importance (Random Forest)')
ax1.grid(axis='x', alpha=0.3)

# Confusion matrix
cm = confusion_matrix(y_test, y_pred_test)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax2,
            xticklabels=["Neutral", "Stress", "Amusement"],
            yticklabels=["Neutral", "Stress", "Amusement"])
ax2.set_xlabel('Predicted')
ax2.set_ylabel('Actual')
ax2.set_title(f'Confusion Matrix (Test Accuracy: {test_acc:.2%})')

plt.tight_layout()
plt.savefig("feature_importance.png", dpi=300, bbox_inches='tight')
print("\n✓ Visualization saved to 'feature_importance.png'")
plt.close()

# ============================================================================
# STEP 8: SAVE MODEL AND SCALER
# ============================================================================
print("\n" + "="*80)
print(" STEP 8: SAVING MODEL AND SCALER")
print("="*80)

model_path = r"C:\\Users\\rahul\\Desktop\\Heart_Rate_Emotion_Detection\\HR_poc1\\Models\\hr_model_improved.pkl"
scaler_path = r"C:\\Users\\rahul\\Desktop\\Heart_Rate_Emotion_Detection\\HR_poc1\\Models\\hr_scaler_improved.pkl"

# Create Models directory if it doesn't exist
os.makedirs(os.path.dirname(model_path), exist_ok=True)

pickle.dump(model, open(model_path, "wb"))
pickle.dump(scaler, open(scaler_path, "wb"))

print(f"\n✓ Model saved to: {model_path}")
print(f"✓ Scaler saved to: {scaler_path}")

# Save feature names for reference
feature_names_path = r"C:\\Users\\rahul\\Desktop\\Heart_Rate_Emotion_Detection\\HR_poc1\\Models\\feature_names.pkl"
pickle.dump(feature_names, open(feature_names_path, "wb"))
print(f"✓ Feature names saved to: {feature_names_path}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print(" TRAINING COMPLETE - SUMMARY")
print("="*80)

print(f"""
✅ Model Training Successful!

📊 PERFORMANCE:
   • Test Accuracy: {test_acc * 100:.2f}%
   • Cross-Validation Accuracy: {cv_scores.mean() * 100:.2f}% (±{cv_scores.std() * 100:.2f}%)
   • Training Samples: {X_train.shape[0]}
   • Test Samples: {X_test.shape[0]}

📁 SAVED FILES:
   • Model: hr_model_improved.pkl
   • Scaler: hr_scaler_improved.pkl
   • Features: feature_names.pkl
   • Plot: feature_importance.png

🎯 TARGET ACCURACY: ≥85%
   • Current Accuracy: {test_acc * 100:.2f}%
   • Status: {'✅ TARGET REACHED!' if test_acc >= 0.85 else '⚠ Below target - see recommendations'}

📝 NEXT STEPS:
   1. Use main_HR_improved.py for inference
   2. If accuracy < 85%:
      - Try binary classification (Stress vs Non-Stress)
      - Increase window size to 45-60 seconds
      - Extract more subjects if available
      - Try different train/test splits
""")

print("="*80)
