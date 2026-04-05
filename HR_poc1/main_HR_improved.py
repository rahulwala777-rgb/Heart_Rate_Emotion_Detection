"""
HEART RATE EMOTION DETECTION - INFERENCE SCRIPT
Load trained model and make predictions on real/test ECG data
"""

import numpy as np
import pickle
import os
from hrv_features import extract_hrv_features


print("="*80)
print(" HEART RATE EMOTION DETECTION - INFERENCE")
print("="*80)

# ============================================================================
# STEP 1: LOAD SAVED MODEL AND SCALER
# ============================================================================
print("\n✓ Loading saved model and scaler...")

model_path = r"C:\Users\rahul\Desktop\Heart_Rate_Emotion_Detection\HR_poc1\Models\hr_model_improved.pkl"
scaler_path = r"C:\Users\rahul\Desktop\Heart_Rate_Emotion_Detection\HR_poc1\Models\hr_scaler_improved.pkl"
feature_names_path = r"C:\Users\rahul\Desktop\Heart_Rate_Emotion_Detection\HR_poc1\Models\feature_names.pkl"

# Check if files exist
if not os.path.exists(model_path):
    print(f"❌ ERROR: Model not found at {model_path}")
    print("   Please run train_HR_improved.py first!")
    exit(1)

model = pickle.load(open(model_path, "rb"))
scaler = pickle.load(open(scaler_path, "rb"))

# Try to load feature names, fallback to default if not available
try:
    feature_names = pickle.load(open(feature_names_path, "rb"))
    print(f"✓ Loaded feature names: {feature_names}")
except:
    feature_names = ["RMSSD", "SDNN", "MeanNN", "pNN50", "MedianNN", "CVNN", "SD1", "SD2"]
    print(f"⚠ Using default feature names: {feature_names}")

# ============================================================================
# STEP 2: PREPARE ECG SIGNAL
# ============================================================================
print("\n✓ Preparing ECG signal for inference...")

# TODO: Replace with real ECG data
# For now, using dummy data - in production, load from file/device/stream
ecg_signal = np.random.randn(21000)  # 30 seconds at 700 Hz

print(f"  - ECG signal shape: {ecg_signal.shape}")
print(f"  - Expected window size: 21000 samples (30 seconds at 700 Hz)")
print(f"  - Note: For production, replace np.random.randn(21000) with real ECG data")

# ============================================================================
# STEP 3: EXTRACT HRV FEATURES
# ============================================================================
print("\n✓ Extracting HRV features from ECG signal...")

features = extract_hrv_features(ecg_signal)

print("  - Extracted features:")
for name, value in features.items():
    print(f"    • {name}: {value:.4f}")

# ============================================================================
# STEP 4: CREATE FEATURE VECTOR
# ============================================================================
print("\n✓ Creating feature vector (must match training order)...")

# Ensure correct feature order (CRITICAL!)
X = np.array([[features[name] for name in feature_names]])

print(f"  - Feature vector shape: {X.shape}")
print(f"  - Feature values: {X[0]}")

# Handle NaN or infinite values
if np.isnan(X).any() or np.isinf(X).any():
    print("  ⚠ Warning: NaN or infinite values detected, replacing with 0")
    X = np.nan_to_num(X, nan=0.0)

# ============================================================================
# STEP 5: APPLY SCALING
# ============================================================================
print("\n✓ Applying feature scaling (must match training)...")

X_scaled = scaler.transform(X)

print(f"  - Scaled feature vector: {X_scaled[0]}")

# ============================================================================
# STEP 6: MAKE PREDICTION
# ============================================================================
print("\n✓ Making prediction...")

prediction = model.predict(X_scaled)[0]
probabilities = model.predict_proba(X_scaled)[0]

# ============================================================================
# STEP 7: DECODE AND DISPLAY RESULTS
# ============================================================================
print("\n" + "="*80)
print(" PREDICTION RESULTS")
print("="*80)

label_map = {
    0: "Neutral/Baseline",
    1: "Stressed",
    2: "Amused"
}

print(f"\n🧠 DETECTED EMOTION: {label_map[prediction]}")
print(f"   Prediction confidence: {probabilities[prediction]:.2%}")

print(f"\n📊 EMOTION PROBABILITIES:")
for emotion_id, emotion_name in sorted(label_map.items()):
    prob = probabilities[emotion_id]
    # Create a simple bar visualization
    bar_length = int(prob * 30)
    bar = "█" * bar_length + "░" * (30 - bar_length)
    print(f"   {emotion_name:20s} [{bar}] {prob:.2%}")

# ============================================================================
# STEP 8: ADVANCED DIAGNOSTICS
# ============================================================================
print("\n" + "="*80)
print(" ADVANCED DIAGNOSTICS")
print("="*80)

# Feature values summary
print("\n✓ Feature Statistics:")
for name, value in features.items():
    print(f"  - {name:10s}: {value:10.4f}", end="")
    if value == 0:
        print(" ⚠ (Zero - possible feature extraction issue)")
    else:
        print()

# Get decision path information (if available)
print(f"\n✓ Model Information:")
print(f"  - Model type: Random Forest Classifier")
print(f"  - Number of trees: {model.n_estimators}")
print(f"  - Number of features: {model.n_features_in_}")
print(f"  - Number of classes: {model.n_classes_}")

# Get feature importance
if hasattr(model, 'feature_importances_'):
    print(f"\n✓ Feature Importance (Top 3):")
    importances = model.feature_importances_
    top_indices = np.argsort(importances)[-3:][::-1]
    for idx in top_indices:
        print(f"  - {feature_names[idx]:10s}: {importances[idx]:.4f}")

# ============================================================================
# STEP 9: RECOMMENDATION SUMMARY
# ============================================================================
print("\n" + "="*80)
print(" RECOMMENDATIONS")
print("="*80)

confidence = probabilities[prediction]

if confidence >= 0.8:
    print(f"\n✅ HIGH CONFIDENCE PREDICTION ({confidence:.2%})")
    print("   The predicted emotion is very likely correct.")
elif confidence >= 0.6:
    print(f"\n⚠️  MODERATE CONFIDENCE PREDICTION ({confidence:.2%})")
    print("   Consider analyzing the ECG signal quality and environmental factors.")
else:
    print(f"\n❌ LOW CONFIDENCE PREDICTION ({confidence:.2%})")
    print("   The model is uncertain. Verify ECG signal quality and timing.")
    print("   Consider collecting more data or checking for signal artifacts.")

print("\n" + "="*80)
print(" END OF INFERENCE")
print("="*80)
