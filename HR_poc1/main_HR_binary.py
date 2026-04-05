"""
Binary Classification Inference
Stress Detection: Stress vs Non-Stress
"""

import numpy as np
import pickle
import os
from hrv_features import extract_hrv_features

print("="*80)
print(" BINARY STRESS DETECTION - INFERENCE")
print("="*80)

# Load model & scaler
model_path = r"C:\Users\rahul\Desktop\Heart_Rate_Emotion_Detection\HR_poc1\Models\hr_model_binary.pkl"
scaler_path = r"C:\Users\rahul\Desktop\Heart_Rate_Emotion_Detection\HR_poc1\Models\hr_scaler_binary.pkl"
feature_path = r"C:\Users\rahul\Desktop\Heart_Rate_Emotion_Detection\HR_poc1\Models\feature_names_binary.pkl"

if not os.path.exists(model_path):
    print("❌ Model not found. Run train_HR_binary.py first!")
    exit(1)

model = pickle.load(open(model_path, "rb"))
scaler = pickle.load(open(scaler_path, "rb"))
feature_names = pickle.load(open(feature_path, "rb"))

print(f"✓ Model loaded")
print(f"✓ Features: {feature_names}\n")

# Get ECG (replace with real data)
ecg_signal = np.random.randn(21000)  # 30 seconds @ 700 Hz

print(f"✓ ECG shape: {ecg_signal.shape} (30 seconds)")

# Extract features
features = extract_hrv_features(ecg_signal)

print(f"✓ Features extracted:")
for name, value in features.items():
    print(f"  - {name}: {value:.4f}")

# Create feature vector
X = np.array([[features[name] for name in feature_names]])

# Scale
X_scaled = scaler.transform(X)

# Predict
prediction = model.predict(X_scaled)[0]
probabilities = model.predict_proba(X_scaled)[0]

# Display results
print("\n" + "="*80)
print(" PREDICTION RESULTS")
print("="*80)

label_map = {0: "🟢 NON-STRESSED (Calm/Happy)", 1: "🔴 STRESSED"}

print(f"\n🧠 DETECTED STATUS: {label_map[prediction]}")
print(f"   Confidence: {probabilities[prediction]:.2%}")

print(f"\n📊 PROBABILITY DISTRIBUTION:")
for i in range(2):
    prob = probabilities[i]
    bar = "█" * int(prob * 30) + "░" * (30 - int(prob * 30))
    print(f"   {label_map[i]:<30} [{bar}] {prob:.2%}")

if probabilities[prediction] < 0.6:
    print(f"\n⚠️  Low confidence - consider collecting more data")

print("\n" + "="*80)
