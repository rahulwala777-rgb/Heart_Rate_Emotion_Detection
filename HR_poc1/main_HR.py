import numpy as np
import pickle
from hrv_features import extract_hrv_features

# -------------------------------
# Step 1: Load saved model & scaler
# -------------------------------
model = pickle.load(open("C:\\Users\\rahul\\Desktop\\Heart_Rate_Emotion_Detection\\HR_poc1\\Models\\hr_model_v6.pkl", "rb"))
scaler = pickle.load(open("C:\\Users\\rahul\\Desktop\\Heart_Rate_Emotion_Detection\\HR_poc1\\Models\\hr_scaler_v6.pkl", "rb"))

# Feature order MUST match training
# feature_names = ["RMSSD", "SDNN", "LFHF"]
feature_names = ["RMSSD", "SDNN", "pNN50", "LF", "HF", "LF_HF"]

# -------------------------------
# Step 2: Load / simulate ECG signal
# -------------------------------
# TODO: Replace with real ECG input
ecg_signal = np.random.randn(7000)

# -------------------------------
# Step 3: Extract features
# -------------------------------
features = extract_hrv_features(ecg_signal)

# Ensure correct feature order
X = np.array([[features[name] for name in feature_names]])

# -------------------------------
# Step 4: Apply scaling
# -------------------------------
X_scaled = scaler.transform(X)

# -------------------------------
# Step 5: Predict
# -------------------------------
prediction = model.predict(X_scaled)[0]
probabilities = model.predict_proba(X_scaled)[0]

# -------------------------------
# Step 6: Decode result
# -------------------------------
label_map = {
    0: "Neutral",
    1: "Stress",
    2: "Amusement"
}

print("\n🧠 Prediction:", label_map[prediction])

print("\n📊 Probabilities:")
for i, prob in enumerate(probabilities):
    print(f"{label_map[i]}: {prob:.2f}")

probs = model.predict_proba(X_scaled)
print("Confidence:", probs)