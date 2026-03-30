import numpy as np
import pickle
import matplotlib.pyplot as plt
import os

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from hrv_features import extract_hrv_features

# -------------------------------
# Step 1: Prepare Dataset
# -------------------------------
X = []
y = []

feature_names = ["RMSSD", "SDNN", "LFHF"]

# Base folder where all subject folders are
base_path = "C:\\Users\\rahul\\Desktop\\Main_Proj_imp_POC1\\myprojectenv_poc1\\Datasets\\WESAD\\WESAD"

# List of subjects to use (skip S1 and S12)
subjects = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]
# subjects = [3]


for subject in subjects:
    # with open(os.path.join(base_path, f"S{subject}", f"S{subject}.pkl"), "rb") as f:
    #     data1 = pickle.load(f, encoding='latin1')

    # print(data1.keys())          # top-level keys
    # print(data1['signal'].keys())  # keys inside 'signal'
    # print(data1['signal']['chest'].keys())



    # Each subject has its own folder: S1, S2, ...
    subject_folder = os.path.join(base_path, f"S{subject}")
    pkl_file = os.path.join(subject_folder, f"S{subject}.pkl")
    
    # Load subject data
    with open(pkl_file, "rb") as f:
        data = pickle.load(f, encoding='latin1')  # WESAD uses latin1


    # ECG from chest
    if 'chest' in data['signal'] and 'ECG' in data['signal']['chest']:
        ecg_signal_full = data['signal']['chest']['ECG']
    else:
        print(f"⚠ Warning: ECG not found for S{subject}, skipping")
        continue

    labels_full = data['label']

    # Segment ECG into windows (e.g., 10 sec)
    window_size = 7000  # 10 seconds at 700Hz
    for start in range(0, len(ecg_signal_full) - window_size, window_size):
        ecg_window = ecg_signal_full[start:start + window_size, 0]  # single lead
        label_window = int(labels_full[start])  # label at window start

        features = extract_hrv_features(ecg_window)
        # Debug 
        print(f"Extracted features for S{subject}, window starting at {start}: {features}") 

        X.append([features[name] for name in feature_names])
        y.append(label_window)

X = np.array(X)
y = np.array(y)

# -------------------------------
# Debug: Check LFHF values
# -------------------------------
lfhf_values = X[:, 2]  # 3rd feature = LFHF

print("\nLFHF stats:")
print("Min:", np.min(lfhf_values))
print("Max:", np.max(lfhf_values))
print("Sample values:", lfhf_values[:10])

# -------------------------------
# Visual check (distribution)
# -------------------------------
import matplotlib.pyplot as plt

plt.hist(lfhf_values, bins=20)
plt.title("LFHF Distribution")
plt.xlabel("LFHF")
plt.ylabel("Frequency")
plt.show()

# -------------------------------
# Step 2: Train-Test Split
# -------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# -------------------------------
# Step 3: (Optional) Scaling
# -------------------------------
# NOTE: Random Forest does NOT need scaling,
# but keeping it for compatibility/future models
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# -------------------------------
# Step 4: Train Random Forest
# -------------------------------
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    random_state=42,
    class_weight="balanced"
)

model.fit(X_train, y_train)

# -------------------------------
# Step 5: Evaluation
# -------------------------------
y_pred = model.predict(X_test)

acc = accuracy_score(y_test, y_pred)
print(f"\nAccuracy: {acc * 100:.2f}%")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# -------------------------------
# Step 6: Feature Importance Plot
# -------------------------------
importances = model.feature_importances_

plt.figure(figsize=(6, 4))
plt.bar(feature_names, importances)
plt.title("Feature Importance (Random Forest)")
plt.xlabel("Features")
plt.ylabel("Importance")
plt.tight_layout()

plt.savefig("feature_importance.png")
plt.show()

# -------------------------------
# Step 7: Save Model
# -------------------------------
pickle.dump(model, open("C:\\Users\\rahul\\Desktop\\Main_Proj_imp_POC1\\myprojectenv_poc1\\HR_poc1\\Models\\hr_model.pkl", "wb"))
pickle.dump(scaler, open("C:\\Users\\rahul\\Desktop\\Main_Proj_imp_POC1\\myprojectenv_poc1\\HR_poc1\\Models\\hr_scaler.pkl", "wb"))

print("\n✅ Model and scaler saved successfully!")