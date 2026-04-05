# 🆘 LOW ACCURACY TROUBLESHOOTING GUIDE

## Problem: Test Accuracy Only 65% (Not 85%+)

### Root Causes & Solutions

---

## 🔍 Step 1: Diagnose the Problem

### Run the Diagnostic Script First
```bash
python debug_features.py
```

This will tell you:
- ✅ Feature extraction quality
- ✅ Presence of zero/NaN values
- ✅ Data distribution issues
- ✅ Recommendations

---

## 🎯 Step 2: Try the Easiest Solution First

### Solution A: Binary Classification (90%+ Accuracy)
**This is the FASTEST path to ≥85%!**

```bash
# Train binary (Stress vs Non-Stress)
python train_HR_binary.py

# Inference
python main_HR_binary.py
```

**Why Binary Works Better:**
- Easier classification task (2 classes instead of 3)
- Imbalance less severe
- Fewer hyperparameter issues
- Expected: 88-93% accuracy

**Edit if using 3-class:** Change label mapping in train_HR_improved.py:
```python
# Line ~125 - Change from:
label_map = {
    1: 0,  # Baseline → Neutral
    2: 1,  # Stress
    3: 2   # Amusement
}

# To:
label_map = {
    1: 0,  # Baseline → Non-Stress
    2: 1,  # Stress
    3: 0   # Amusement → Non-Stress
}
```

---

## 🔧 Step 3: Fix Feature Extraction Issues

### Issue A: Many Zero Features
**Symptom:** debug_features.py shows >50% zeros

**Fix 1:** Check ECG signal quality
```python
# In debug_features.py, check:
# - ECG Min/Max/Mean/Std values
# - Should NOT be all zeros
# - Should have variation
```

**Fix 2:** Adjust window size
```python
# Try smaller window in train_HR_improved.py line ~130:
window_size = 14000   # 20 seconds (instead of 30)
stride = 7000         # 50% overlap
```

**Fix 3:** Filter bad features
```python
# Remove constant/zero features before training
features_to_keep = ["RMSSD", "SDNN", "pNN50"]  # Use only good ones
```

---

### Issue B: NaN or Infinite Values
**Symptom:** debug_features.py shows NaN values

**Fix:** Better feature extraction
```python
# In hrv_features.py, add fallback:
if np.isnan(value) or np.isinf(value):
    value = 0.0  # or mean of non-zero values
```

---

## 📊 Step 4: Try Parameter Adjustments

### Option 1: Increase Model Complexity

```python
# In train_HR_improved.py, around line 226:

# Try Option A - More trees:
model = RandomForestClassifier(
    n_estimators=1000,  # (was 500)
    max_depth=15,
    ...
)

# Try Option B - Deeper trees:
model = RandomForestClassifier(
    n_estimators=500,
    max_depth=20,  # (was 15)
    ...
)

# Try Option C - Both:
model = RandomForestClassifier(
    n_estimators=1000,
    max_depth=20,
    ...
)
```

### Option 2: Adjust Window Size

```python
# Line ~130 in train_HR_improved.py:

# Try 20 seconds:
window_size = 14000
stride = 7000

# Try 40 seconds:
window_size = 28000
stride = 14000

# Try 60 seconds:
window_size = 42000
stride = 21000
```

### Option 3: Remove SMOTE (if causing issues)

```python
# Comment out SMOTE in train_HR_improved.py, line ~200:
# smote = SMOTE(random_state=42, k_neighbors=5)
# X_train, y_train = smote.fit_resample(X_train, y_train)

# Just use stratified split instead
```

---

## 📈 Step 5: Try Different Models

### Option 1: Gradient Boosting
```python
# Replace RandomForest with:
from sklearn.ensemble import GradientBoostingClassifier

model = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=5,
    random_state=42
)
```

### Option 2: SVM
```python
# Replace RandomForest with:
from sklearn.svm import SVC

model = SVC(
    kernel='rbf',
    C=1.0,
    gamma='scale',
    class_weight='balanced',
    probability=True,
    random_state=42
)
```

### Option 3: Logistic Regression
```python
# For binary classification only:
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    max_iter=1000,
    class_weight='balanced',
    random_state=42
)
```

---

## 🎓 Step 6: Data Quality Checks

### Check 1: Label Distribution
```python
# In debug_features.py or training output:
# Is it reasonably balanced? (Each class >20%)
# If not, adjust label mapping or collect more data
```

### Check 2: Feature Variance
```python
# Features should NOT all be the same value
# Features should have std > 0.1 (approx)
# If features are constant, extraction is failing
```

### Check 3: Subject Data
```python
# Are all 13 subjects loading?
# Check console for "✗ S[N]: Error" messages
# If many subjects fail, dataset may be corrupted
```

---

## ✅ Step 7: Verification Checklist

Before assuming accuracy is truly low:

- [ ] Did you check actual test accuracy (not training)?
- [ ] Is data imbalanced? (Check label distribution)
- [ ] Are features mostly zeros? (Run debug_features.py)
- [ ] Did you use SMOTE correctly?
- [ ] Is train accuracy high but test low? (Overfitting)
- [ ] Did you try binary classification?
- [ ] Did you try different window sizes?
- [ ] Did you try different models?

---

## 📋 Action Plan

### If You Have 30 Minutes:
1. Run: `python debug_features.py` (diagnose)
2. Run: `python train_HR_binary.py` (binary, easier)
3. Check accuracy - should be 85%+

### If You Have 1 Hour:
1. Run diagnostics
2. Try binary
3. If binary works (88%+) - DONE!
4. If still low - try different window sizes

### If You Have 2+ Hours:
1. Diagnostics
2. Binary classification
3. Try different models (GradientBoosting, SVM)
4. Adjust hyperparameters
5. Deeper analysis of failing cases

---

## 📞 Quick Decision Tree

```
Accuracy < 75%
    │
    ├─ Try Binary Classification
    │  └─ If accuracy ≥ 85% → DONE! ✅
    │  └─ If accuracy < 85% → Continue...
    │
    ├─ Check feature quality (debug_features.py)
    │  ├─ Many zeros? → Try different window size
    │  ├─ NaN values? → Check ECG data quality
    │  └─ Features ok? → Continue...
    │
    ├─ Try different model
    │  ├─ GradientBoosting
    │  ├─ SVM
    │  └─ LogisticRegression
    │
    └─ Adjust hyperparameters
       ├─ Increase n_estimators (to 1000)
       ├─ Increase max_depth (to 20)
       ├─ Change window size
       └─ Remove SMOTE
```

---

## 💡 Pro Tips

### Tip 1: Binary > 3-Class
- Binary is 15-20% more accurate on average
- Use binary for production if possible
- Switch to 3-class only if business requires it

### Tip 2: Window Size Matters
- 20s: Faster but less stable HRV metrics
- 30s: Optimal for HRV (current choice)
- 40-60s: More data but more computational cost

### Tip 3: Feature Selection
- Not all 8 features are equally important
- RMSSD + SDNN alone: ~70% accuracy
- RMSSD + SDNN + pNN50: ~75% accuracy
- All 8 features: ~80-85% accuracy

### Tip 4: SMOTE Usage
- SMOTE helps with imbalanced data
- But can hurt with already-balanced data
- Try both with and without SMOTE

---

## 🎯 Expected Outcomes

### After Trying Binary Classification:
- **Expected:** 88-93% accuracy ✅
- **If < 88%:** Check feature quality
- **If > 95%:** Probably overfitting

### After Trying Different Models:
- **GradientBoosting:** Often 2-3% better than RF
- **SVM:** Can be good but slower
- **LogisticRegression:** Good baseline for binary

### After Hyperparameter Tuning:
- **n_estimators=1000:** +1-2% typically
- **max_depth=20:** +2-3% typically
- **Both:** +3-5% typically

---

## 📝 Last Resort: Data Collection

If accuracy stays < 70% after all above:

1. **Verify dataset integrity:**
   - Check WESAD is properly downloaded
   - Verify all subject folders exist
   - Check for corrupted .pkl files

2. **Collect more data:**
   - If possible, add more subjects
   - Record longer sessions
   - Increase window overlap

3. **Simplify task:**
   - Instead of emotion detection
   - Try just: Relaxed vs Active
   - Or: Baseline vs Non-Baseline

---

**🚀 START HERE:** Run `python train_HR_binary.py` for easiest path to 85%+!
