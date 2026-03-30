import numpy as np
import pickle
import matplotlib.pyplot as plt
import os

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils import shuffle

from hrv_features import extract_hrv_features
from collections import Counter

# -------------------------------
# Step 1: Prepare Dataset
# -------------------------------
X = []
y = []

feature_names = ["RMSSD", "SDNN", "pNN50", "LF", "HF", "LF_HF"]

base_path = "C:\\Users\\rahul\\Desktop\\Main_Proj_imp_POC1\\myprojectenv_poc1\\Datasets\\WESAD\\WESAD"

subjects = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]

label_map = {
    1: 0,  # Neutral
    2: 1,  # Stress
    3: 2   # Amusement
}

total_windows = 0
skipped_windows = 0

for subject in subjects:
    subject_folder = os.path.join(base_path, f"S{subject}")
    pkl_file = os.path.join(subject_folder, f"S{subject}.pkl")

    with open(pkl_file, "rb") as f:
        data = pickle.load(f, encoding='latin1')

    if 'chest' not in data['signal'] or 'ECG' not in data['signal']['chest']:
        print(f"⚠ ECG missing for S{subject}")
        continue

    ecg_signal_full = data['signal']['chest']['ECG']
    labels_full = data['label']

    window_size = 14000  # 20 sec windows

    for start in range(0, len(ecg_signal_full) - window_size, window_size):
        total_windows += 1

        ecg_window = ecg_signal_full[start:start + window_size, 0]
        label_window = int(labels_full[start])

        if label_window not in label_map:
            continue

        # Extract HRV features
        features = extract_hrv_features(ecg_window)
        if features is None:
            print(f"⚠ Skipping window {start} for S{subject} (bad ECG or HRV)")
            skipped_windows += 1
            continue

        # Build feature vector
        try:
            feature_vector = [features[name] for name in feature_names]
        except KeyError:
            skipped_windows += 1
            continue

        X.append(feature_vector)
        y.append(label_map[label_window])

# -------------------------------
# Convert to numpy arrays
# -------------------------------
X = np.array(X)
y = np.array(y)

if len(X) == 0:
    raise ValueError("❌ No valid data collected")

print("\n✅ Data Prepared")
print("Total windows:", total_windows)
print("Used windows:", len(X))
print("Skipped windows:", skipped_windows)
print("Label distribution:", Counter(y))

# Shuffle dataset
X, y = shuffle(X, y, random_state=42)

# -------------------------------
# Step 2: Train-Test Split
# -------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print("\nTrain distribution:", Counter(y_train))

# -------------------------------
# Step 3: Scaling
# -------------------------------
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# -------------------------------
# Step 4: Train Random Forest
# -------------------------------
model = RandomForestClassifier(
    n_estimators=500,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    class_weight="balanced_subsample"
)
model.fit(X_train, y_train)

# -------------------------------
# Step 5: Evaluation
# -------------------------------
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"\n🎯 Accuracy: {accuracy * 100:.2f}%")

print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

# Cross-validation
cv_scores = cross_val_score(model, X, y, cv=5)
print("🔁 Cross-validation accuracy:", cv_scores.mean())

# -------------------------------
# Step 6: Feature Importance
# -------------------------------
importances = model.feature_importances_

plt.figure(figsize=(6, 4))
plt.bar(feature_names, importances)
plt.title("Feature Importance (Random Forest)")
plt.xlabel("Features")
plt.ylabel("Importance")
plt.tight_layout()

# -------------------------------
# Step 7: Save Model
# -------------------------------
model_path = "C:\\Users\\rahul\\Desktop\\Heart_Rate_Emotion_Detection\\HR_poc1\\Models\\hr_model_v7.pkl"
scaler_path = "C:\\Users\\rahul\\Desktop\\Heart_Rate_Emotion_Detection\\HR_poc1\\Models\\hr_scaler_v7.pkl"

pickle.dump(model, open(model_path, "wb"))
pickle.dump(scaler, open(scaler_path, "wb"))

print("\n✅ Model and scaler saved successfully!")