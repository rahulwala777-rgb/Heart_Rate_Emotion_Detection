"""
BINARY CLASSIFICATION VERSION - EASIER & FASTER TO ≥85% ACCURACY
Stress Detection: Stress vs Non-Stress (Neutral + Amusement)

This is the QUICKEST PATH to 85%+ accuracy!
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
print(" BINARY CLASSIFICATION - STRESS DETECTION")
print(" (Stress vs Non-Stress) - EASIER PATH TO ≥85%")
print("="*80)

# ============================================================================
# STEP 1: LOAD DATA - BINARY LABELS
# ============================================================================
print("\n" + "="*80)
print(" STEP 1: LOADING DATA")
print("="*80)

X = []
y = []

feature_names = ["RMSSD", "SDNN", "MeanNN", "pNN50", "MedianNN", "CVNN", "SD1", "SD2"]

base_path = r"C:\\Users\\rahul\\Desktop\\Main_Proj_imp_POC1\\myprojectenv_poc1\\Datasets\\WESAD\\WESAD"
subjects = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]

print(f"✓ Features: {feature_names}")
print(f"✓ Subjects: {subjects}")
print(f"✓ Task: Binary Classification (Stress vs Non-Stress)\n")

window_count = 0
successful_subjects = 0

for subject in subjects:
    subject_folder = os.path.join(base_path, f"S{subject}")
    pkl_file = os.path.join(subject_folder, f"S{subject}.pkl")
    
    try:
        with open(pkl_file, "rb") as f:
            data = pickle.load(f, encoding='latin1')

        if 'chest' not in data['signal'] or 'ECG' not in data['signal']['chest']:
            print(f"  ✗ S{subject}: No ECG, skipping")
            continue

        ecg_signal_full = data['signal']['chest']['ECG']
        labels_full = data['label']
        successful_subjects += 1

        window_size = 21000  # 30 seconds
        stride = 10500       # 50% overlap
        
        subject_windows = 0
        for start in range(0, len(ecg_signal_full) - window_size, stride):
            ecg_window = ecg_signal_full[start:start + window_size, 0]
            label_window = int(labels_full[start])

            if label_window not in [1, 2, 3]:
                continue

            # ⭐ KEY CHANGE: BINARY MAPPING
            # 0 = Non-Stress (Neutral + Amusement)
            # 1 = Stress
            if label_window == 1 or label_window == 3:
                binary_label = 0  # Non-Stress
            elif label_window == 2:
                binary_label = 1  # Stress
            else:
                continue

            y.append(binary_label)

            features = extract_hrv_features(ecg_window)
            X.append([features[name] for name in feature_names])
            
            subject_windows += 1
            window_count += 1
        
        print(f"  ✓ S{subject}: {subject_windows} windows")
        
    except Exception as e:
        print(f"  ✗ S{subject}: {str(e)}")
        continue

X = np.array(X)
y = np.array(y)

print("\n" + "-"*80)
print("DATASET STATISTICS")
print("-"*80)
print(f"✓ Subjects processed: {successful_subjects}/{len(subjects)}")
print(f"✓ Total windows: {window_count}")
print(f"✓ Feature matrix: {X.shape}")
print(f"✓ Label vector: {y.shape}")

print(f"\n✓ Class Distribution (BINARY):")
label_counts = dict(Counter(y))
for label in [0, 1]:
    if label in label_counts:
        count = label_counts[label]
        emotion = ["Non-Stress (Neutral+Amusement)", "Stress"][label]
        percentage = (count / len(y)) * 100
        print(f"  - {emotion}: {count} samples ({percentage:.1f}%)")

# Handle NaN
nan_count = np.isnan(X).sum()
if nan_count > 0:
    print(f"\n⚠ Replacing {nan_count} NaN values")
    X = np.nan_to_num(X, nan=0.0)

# ============================================================================
# STEP 2: TRAIN-TEST SPLIT
# ============================================================================
print("\n" + "="*80)
print(" STEP 2: TRAIN-TEST SPLIT")
print("="*80)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n✓ Train set: {X_train.shape[0]} samples")
print(f"✓ Test set: {X_test.shape[0]} samples")
print(f"✓ Distribution maintained (stratified)")

# ============================================================================
# STEP 3: SMOTE
# ============================================================================
print("\n" + "="*80)
print(" STEP 3: CLASS BALANCING (SMOTE)")
print("="*80)

smote = SMOTE(random_state=42, k_neighbors=5)
X_train, y_train = smote.fit_resample(X_train, y_train)

print(f"\n✓ After SMOTE: {X_train.shape[0]} samples")
print(f"✓ Distribution:")
for label in [0, 1]:
    count = np.sum(y_train == label)
    emotion = ["Non-Stress", "Stress"][label]
    print(f"  - {emotion}: {count}")

# ============================================================================
# STEP 4: SCALING
# ============================================================================
print("\n" + "="*80)
print(" STEP 4: FEATURE SCALING")
print("="*80)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("✓ Features scaled")

# ============================================================================
# STEP 5: TRAIN MODEL
# ============================================================================
print("\n" + "="*80)
print(" STEP 5: TRAINING RANDOM FOREST (BINARY)")
print("="*80)

# ⭐ STRONGER HYPERPARAMETERS FOR BINARY (easier task)
model = RandomForestClassifier(
    n_estimators=300,        # Fewer needed for binary
    max_depth=12,            # Less deep needed
    min_samples_split=5,     
    min_samples_leaf=2,      
    max_features='sqrt',
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)

print("\n✓ Model config:")
print(f"  - Trees: {model.n_estimators}")
print(f"  - Depth: {model.max_depth}")
print(f"  - Split: {model.min_samples_split}")

print("\n⏳ Training...")
model.fit(X_train_scaled, y_train)
print("✓ Done!")

# ============================================================================
# STEP 6: EVALUATION
# ============================================================================
print("\n" + "="*80)
print(" STEP 6: EVALUATION")
print("="*80)

y_pred_train = model.predict(X_train_scaled)
y_pred_test = model.predict(X_test_scaled)

train_acc = accuracy_score(y_train, y_pred_train)
test_acc = accuracy_score(y_test, y_pred_test)

print(f"\n✓ ACCURACY:")
print(f"  - Training: {train_acc * 100:.2f}%")
print(f"  - Test: {test_acc * 100:.2f}%")

# Cross-validation
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')

print(f"\n✓ CROSS-VALIDATION (5-Fold):")
print(f"  - Mean: {cv_scores.mean() * 100:.2f}%")
print(f"  - Std: {cv_scores.std() * 100:.2f}%")
print(f"  - Scores: {[f'{s:.1%}' for s in cv_scores]}")

# Classification report
print(f"\n✓ CLASSIFICATION REPORT:")
print(classification_report(
    y_test, y_pred_test,
    target_names=["Non-Stress", "Stress"],
    digits=4
))

# ============================================================================
# STEP 7: SAVE MODEL
# ============================================================================
print("\n" + "="*80)
print(" STEP 7: SAVING MODEL")
print("="*80)

models_folder = r"C:\\Users\\rahul\\Desktop\\Heart_Rate_Emotion_Detection\\HR_poc1\\Models"
os.makedirs(models_folder, exist_ok=True)

model_path = os.path.join(models_folder, "hr_model_binary.pkl")
scaler_path = os.path.join(models_folder, "hr_scaler_binary.pkl")
feature_path = os.path.join(models_folder, "feature_names_binary.pkl")

pickle.dump(model, open(model_path, "wb"))
pickle.dump(scaler, open(scaler_path, "wb"))
pickle.dump(feature_names, open(feature_path, "wb"))

print(f"\n✓ Model saved: {model_path}")
print(f"✓ Scaler saved: {scaler_path}")
print(f"✓ Features saved: {feature_path}")

# ============================================================================
# FINAL RESULTS
# ============================================================================
print("\n" + "="*80)
print(" ✅ BINARY CLASSIFICATION RESULTS")
print("="*80)

print(f"""
📊 PERFORMANCE:
   • Test Accuracy: {test_acc * 100:.2f}%  {'✅' if test_acc >= 0.85 else '⚠️'}
   • CV Accuracy: {cv_scores.mean() * 100:.2f}% ± {cv_scores.std() * 100:.2f}%
   • Training Samples: {X_train.shape[0]}
   • Test Samples: {X_test.shape[0]}

🎯 TARGET: ≥85% accuracy
   Status: {'✅ ACHIEVED!' if test_acc >= 0.85 else '⚠️  Below target'}

📁 FILES SAVED:
   • hr_model_binary.pkl
   • hr_scaler_binary.pkl
   • feature_names_binary.pkl

🔄 USAGE:
   1. For inference: main_HR_binary.py
   2. Update label mapping: 0='Non-Stress', 1='Stress'
""")

print("="*80)
