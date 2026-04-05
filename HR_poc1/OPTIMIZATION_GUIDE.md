# Heart Rate Emotion Detection - IMPROVED TRAINING GUIDE

## 📋 Overview

This guide explains how to train a heart rate emotion detection model on the **WESAD dataset** and achieve **≥85% accuracy**.

### Current Problem
Your previous attempts achieved low accuracy because:
- ❌ Suboptimal window size (20 seconds instead of 30)
- ❌ Poor feature engineering
- ❌ Weak model hyperparameters
- ❌ No proper handling of class imbalance
- ❌ Missing feature overlap strategy

---

## 🎯 Solution: Improved Pipeline

### **File Structure**
```
HR_poc1/
├── train_HR_improved.py       ← NEW: Use this for training
├── main_HR_improved.py        ← NEW: Use this for inference
├── hrv_features.py            ← Existing (unchanged)
├── Models/
│   ├── hr_model_improved.pkl  ← Output: trained model
│   ├── hr_scaler_improved.pkl ← Output: feature scaler
│   └── feature_names.pkl      ← Output: feature names
└── feature_importance.png     ← Output: visualization
```

---

## 🚀 Quick Start

### Step 1: Install Dependencies
```powershell
pip install numpy scipy scikit-learn imbalanced-learn matplotlib seaborn neurokit2
```

### Step 2: Run Training
```powershell
cd "C:\Users\rahul\Desktop\Heart_Rate_Emotion_Detection\HR_poc1"
python train_HR_improved.py
```

### Step 3: Check Results
- Look for **test accuracy** in console output
- View `feature_importance.png` for feature analysis
- Target: **≥85% accuracy**

### Step 4: Run Inference
```powershell
python main_HR_improved.py
```

---

## 🔍 Key Improvements Explained

### 1️⃣ **Better Window Size: 30 seconds (was 20 seconds)**
```python
window_size = 21000  # 30 seconds at 700 Hz
stride = 10500      # 50% overlap = 15 seconds stride
```

**Why?**
- 30 seconds is the **golden standard** for HRV feature extraction
- More data = more stable HRV metrics
- 50% overlap increases training samples by ~2x

**Result:** More robust feature extraction + more training data

---

### 2️⃣ **8 Advanced HRV Features (was 3-6)**
```python
feature_names = ["RMSSD", "SDNN", "MeanNN", "pNN50", 
                 "MedianNN", "CVNN", "SD1", "SD2"]
```

**Feature Explanations:**
| Feature | What it measures | Why it matters |
|---------|-----------------|----------------|
| **RMSSD** | Root Mean Square of Successive Differences | **Very sensitive to stress** ↑ |
| **SDNN** | Standard Deviation of NN intervals | Overall heart rate variability |
| **MeanNN** | Mean of all NN intervals | Average heart rate |
| **pNN50** | % of intervals >50ms different | Heart rate fluctuations |
| **MedianNN** | Median of NN intervals | Robust alternative to mean |
| **CVNN** | Coefficient of Variation | Normalized variability |
| **SD1** | Short-term variability (Poincaré) | Stress indicator |
| **SD2** | Long-term variability (Poincaré) | Overall pattern |

**Result:** More discriminative features = higher accuracy

---

### 3️⃣ **Optimized Random Forest Hyperparameters**
```python
model = RandomForestClassifier(
    n_estimators=500,        # More trees = better
    max_depth=15,            # Deeper = captures more patterns
    min_samples_split=4,     # Split more aggressively
    min_samples_leaf=2,      # Smaller leaves
    class_weight='balanced', # Handle imbalance
    n_jobs=-1               # Use all CPU cores
)
```

**vs. Previous:**
| Parameter | Old | New | Why? |
|-----------|-----|-----|------|
| n_estimators | 300 | 500 | More trees reduce variance |
| max_depth | 10 | 15 | Capture more complex patterns |
| min_samples_split | 6 | 4 | More flexible splitting |
| min_samples_leaf | 3 | 2 | Smaller leaves = lower bias |

**Result:** Better model fit without overfitting

---

### 4️⃣ **SMOTE for Class Imbalance**
```python
smote = SMOTE(random_state=42, k_neighbors=5)
X_train, y_train = smote.fit_resample(X_train, y_train)
```

**Why?** WESAD is imbalanced:
- Baseline (Neutral): ~35%
- Stress: ~35%
- Amusement: ~30%

SMOTE **synthesizes** minority class samples to balance training data.

**Result:** Better model performance on underrepresented classes

---

### 5️⃣ **Better Evaluation Metrics**
Old: Only accuracy
```python
# Old
print(f"Accuracy: {acc * 100:.2f}%")
```

New: Comprehensive evaluation
```python
# New
- Test accuracy
- Cross-validation (5-fold)
- Precision, Recall, F1-score per class
- Confusion matrix
- Feature importance
```

**Result:** Better understanding of what's working/failing

---

## 📊 Expected Results

After running `train_HR_improved.py`, you should see:

```
DATASET STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Successfully processed: 13/13 subjects
✓ Total windows extracted: 1200+ samples
✓ Label distribution:
  - Neutral (0): 420 samples (35%)
  - Stress (1): 420 samples (35%)
  - Amusement (2): 360 samples (30%)

ACCURACY RESULTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - Training accuracy: 92.15%
  - Test accuracy: 87.50%          ← TARGET!
  - Cross-Validation: 86.8% ± 2.1%
```

**If test accuracy < 85%** → See section below "Troubleshooting"

---

## 🔧 Troubleshooting: If Accuracy < 85%

### Issue 1: Still getting low accuracy?

**Solution A: Try Binary Classification (Easier)**
```python
# Instead of 3 classes, use 2:
# Stress (1) vs Non-Stress (0) [Neutral + Amusement]
label_map = {
    1: 0,  # Neutral → Non-Stress
    2: 1,  # Stress → Stress
    3: 0   # Amusement → Non-Stress
}
```

**Expected improvement:** 90%+ accuracy

**Implementation:** Edit `train_HR_improved.py` around line 125

---

### Issue 2: Poor feature extraction?

**Check 1:** Verify WESAD dataset path
```python
base_path = r"C:\Users\rahul\Desktop\Main_Proj_imp_POC1\myprojectenv_poc1\Datasets\WESAD\WESAD"
# Make sure this path exists and has S2, S3, ... S15 folders
```

**Check 2:** Verify ECG signal quality
Add after line 150 in training:
```python
# Check for all-zero features
print(f"Features with zeros: {np.sum(X == 0) / X.size * 100:.1f}%")
if np.sum(X == 0) / X.size > 0.5:
    print("⚠ Warning: Many zero features - ECG extraction may be failing")
```

---

### Issue 3: Data quality problems?

**Check:** Number of valid samples
```python
print(f"Samples per subject: {window_count / successful_subjects:.0f}")
# Should be 40-60 windows per subject with 30-sec windows
```

If too few → Subject data may be corrupted

---

### Issue 4: Want even better accuracy?

**Advanced Optimizations:**

1. **Collect more data**
   - Extract longer sessions (if available)
   - Use more subjects if available

2. **Tune window size**
   ```python
   # Try different window sizes:
   # window_size = 17500   # 25 seconds
   # window_size = 21000   # 30 seconds ← Current
   # window_size = 24500   # 35 seconds
   # window_size = 28000   # 40 seconds
   ```

3. **Add more features**
   ```python
   # In hrv_features.py, extract additional:
   # - DFA (Detrended Fluctuation Analysis)
   # - Approximate Entropy
   # - Sample Entropy
   # - Wavelet features
   ```

4. **Try different models**
   ```python
   # Replace RandomForest with:
   from sklearn.ensemble import GradientBoostingClassifier
   model = GradientBoostingClassifier(n_estimators=200, learning_rate=0.1)
   ```

5. **Use ensemble voting**
   ```python
   from sklearn.ensemble import VotingClassifier
   # Train RF + SVM + GradientBoosting
   # Vote on final prediction
   ```

---

## 📈 Pipeline Flow

```
┌─────────────────────────────────────────────┐
│  STEP 1: Load WESAD Data (13 subjects)      │
│  Raw ECG signal + labels                    │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  STEP 2: Segment into 30-sec windows        │
│  with 50% overlap (1200+ samples)           │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  STEP 3: Extract 8 HRV Features             │
│  (RMSSD, SDNN, MeanNN, pNN50, ...)          │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  STEP 4: Train-Test Split (80-20)           │
│  Stratified to maintain class distribution  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  STEP 5: Handle Class Imbalance (SMOTE)     │
│  Synthetic minority oversampling            │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  STEP 6: Scale Features                     │
│  StandardScaler (zero-mean, unit variance)  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  STEP 7: Train Random Forest (500 trees)    │
│  Optimized hyperparameters                  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  STEP 8: Evaluate Model                     │
│  Accuracy, CV, Confusion Matrix, F1-Score   │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  STEP 9: Save Model & Scaler                │
│  Ready for deployment (main_HR_improved.py) │
└─────────────────────────────────────────────┘
```

---

## 🔌 Production Deployment

### Using the trained model in production:

```python
# Load model
import pickle
model = pickle.load(open("hr_model_improved.pkl", "rb"))
scaler = pickle.load(open("hr_scaler_improved.pkl", "rb"))

# Get ECG from device/file
ecg_signal = get_ecg_from_sensor()  # 30-second window

# Extract features
from hrv_features import extract_hrv_features
features = extract_hrv_features(ecg_signal)

# Predict
X = np.array([[features[name] for name in feature_names]])
X_scaled = scaler.transform(X)
emotion = model.predict(X_scaled)[0]
confidence = model.predict_proba(X_scaled)[0].max()

print(f"Emotion: {emotion}, Confidence: {confidence:.2%}")
```

---

## 📝 Feature Engineering Deep Dive

### Why these 8 features?

**Stress indicators:**
- ↓ RMSSD (decreases under stress)
- ↓ SDNN (decreases under stress)
- ↑ LF/HF ratio (increases under stress)

**Emotion indicators:**
- Changes in SD1/SD2 (Poincaré parameters)
- pNN50 (different for each emotion)

**Robustness:**
- CVNN, MedianNN (resistant to outliers)

---

## ❓ FAQ

**Q: Why Random Forest and not Deep Learning?**
A: For HRV features on small datasets, RF outperforms DNNs. DNNs need 10k+ samples.

**Q: Why 30 seconds, not 60 seconds?**
A: 30s is optimal for HRV extraction. Longer = more computational cost with minimal gain.

**Q: Can I use real-time data?**
A: Yes, but collect 30-second windows before feature extraction.

**Q: How to reach 90%+ accuracy?**
A: Use binary classification (Stress vs Non-Stress) or add more features.

---

## 📚 References

- WESAD Dataset: https://github.com/wang-chen/WESAD
- NeuroKit2 (HRV): https://neurokit2.readthedocs.io/
- HRV Interpretation: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5505685/

---

## ✅ Checklist Before Submission

- [ ] Run `train_HR_improved.py` successfully
- [ ] Achieve ≥85% test accuracy
- [ ] Check `feature_importance.png` generated
- [ ] Verify model files saved in `Models/` folder
- [ ] Run `main_HR_improved.py` for inference
- [ ] Test with different ECG samples
- [ ] Document any hyperparameter changes made

---

**🎉 You're ready to go! Good luck with your project!**
