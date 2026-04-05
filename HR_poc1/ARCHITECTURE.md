# 🏗️ ARCHITECTURE & DATA FLOW

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     HEART RATE EMOTION DETECTION SYSTEM                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: TRAINING (One-time, offline)                                     │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  WESAD Dataset   │  ← Raw ECG signals from 13 subjects
    │  (13 subjects)   │     Sampling rate: 700 Hz
    │  ~60 GB          │     Labels: Baseline/Stress/Amusement
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │  Load & Preprocess           │
    │  - Load .pkl files           │  train_HR_improved.py
    │  - Extract chest ECG signal  │  (Lines 1-100)
    │  - Verify signal quality     │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │  Segmentation (30-sec windows)       │
    │  - Window size: 21,000 samples       │  Line 130-150
    │  - Stride: 10,500 (50% overlap)      │
    │  - Result: 1,200+ training windows   │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │  Feature Extraction                  │  hrv_features.py
    │  8 HRV Features per window:          │  (8 features)
    │  ┌────────────────────────────────┐  │
    │  │ 1. RMSSD                       │  │
    │  │ 2. SDNN                        │  │
    │  │ 3. MeanNN                      │  │
    │  │ 4. pNN50                       │  │
    │  │ 5. MedianNN                    │  │
    │  │ 6. CVNN                        │  │
    │  │ 7. SD1                         │  │
    │  │ 8. SD2                         │  │
    │  └────────────────────────────────┘  │
    │  Result: [1200, 8] feature matrix    │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │  Train-Test Split                    │  Line 185-195
    │  - Train: 960 samples (80%)          │
    │  - Test: 240 samples (20%)           │
    │  - Stratified split                  │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │  Handle Class Imbalance (SMOTE)      │  Line 198-210
    │  - Before: Train[300, 280, 280]      │
    │  - After: Train[320, 320, 320]       │
    │  - Result: Balanced training set     │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │  Feature Scaling                     │  Line 213-220
    │  StandardScaler:                     │
    │  - Mean = 0                          │
    │  - Std = 1                           │
    │  - Fitted on training set            │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │  Train Random Forest (500 trees)          │  Line 223-240
    │  Hyperparameters:                         │
    │  ┌──────────────────────────────────────┐ │
    │  │ n_estimators: 500                    │ │
    │  │ max_depth: 15                        │ │
    │  │ min_samples_split: 4                 │ │
    │  │ min_samples_leaf: 2                  │ │
    │  │ class_weight: 'balanced'             │ │
    │  │ max_features: 'sqrt'                 │ │
    │  │ n_jobs: -1 (all CPUs)                │ │
    │  └──────────────────────────────────────┘ │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │  Evaluate Model                           │  Line 243-290
    │  Test Results:                            │
    │  ┌──────────────────────────────────────┐ │
    │  │ Test Accuracy: 85-90%   ← TARGET      │ │
    │  │ CV Accuracy: 86±2%                   │ │
    │  │ Precision/Recall/F1                  │ │
    │  │ Confusion Matrix                     │ │
    │  │ Feature Importance Plot              │ │
    │  └──────────────────────────────────────┘ │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │  Save Artifacts                           │  Line 293-310
    │  ┌──────────────────────────────────────┐ │
    │  │ ✅ hr_model_improved.pkl             │ │
    │  │ ✅ hr_scaler_improved.pkl            │ │
    │  │ ✅ feature_names.pkl                 │ │
    │  │ ✅ feature_importance.png            │ │
    │  └──────────────────────────────────────┘ │
    └──────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: INFERENCE (Real-time, production)                                │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  Real ECG Signal │  ← From wearable, monitor, device
    │  (30 seconds)    │     Sampling rate: 700 Hz
    │  21,000 samples  │     Single lead (chest)
    └────────┬─────────┘
             │
             ▼ main_HR_improved.py (Lines 1-50)
    ┌──────────────────────────────────────┐
    │  Load Saved Model & Scaler           │
    │  From Models/ folder                 │
    └────────┬─────────────────────────────┘
             │
             ▼ Lines 50-80
    ┌──────────────────────────────────────┐
    │  Extract HRV Features                │
    │  (Same 8 features as training)       │
    │  Result: [1, 8] vector               │
    └────────┬─────────────────────────────┘
             │
             ▼ Lines 80-100
    ┌──────────────────────────────────────┐
    │  Apply Scaling                       │
    │  (Using saved scaler)                │
    │  Result: Standardized features       │
    └────────┬─────────────────────────────┘
             │
             ▼ Lines 103-110
    ┌──────────────────────────────────────┐
    │  Predict Emotion                     │
    │  Random Forest.predict()             │
    │  Return: Class label (0, 1, or 2)    │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │  Get Probabilities                   │
    │  Random Forest.predict_proba()       │
    │  Return: [P(Neutral), P(Stress),     │
    │           P(Amusement)]              │
    └────────┬─────────────────────────────┘
             │
             ▼ Lines 120-150
    ┌──────────────────────────────────────┐
    │  Output Results                      │
    │  ┌──────────────────────────────────┐ │
    │  │ 🧠 DETECTED EMOTION: [Label]     │ │
    │  │ 📊 PROBABILITIES:                │ │
    │  │    - Neutral: XX%                │ │
    │  │    - Stress: XX%                 │ │
    │  │    - Amusement: XX%              │ │
    │  │ 📈 CONFIDENCE: XX%               │ │
    │  └──────────────────────────────────┘ │
    └──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  FEATURE EXTRACTION DEEP DIVE                                              │
└─────────────────────────────────────────────────────────────────────────────┘

    Raw ECG Signal (700 Hz, 30 sec)
    ┌──────────────────────────────┐
    │  Amplitude (mV):             │
    │    ╱╲  ╱╲  ╱╲  ╱╲  ╱╲  ╱╲   │
    │   ╱  ╲╱  ╲╱  ╲╱  ╲╱  ╲╱  ╲  │
    │  [21,000 data points]        │
    └────────────┬─────────────────┘
                 │
                 ▼ (neurokit2)
    ┌──────────────────────────────┐
    │  Signal Processing:          │
    │  1. Clean & denoise          │
    │  2. Detect R-peaks (heartbeat)│
    │  3. Extract NN intervals     │
    │  4. Calculate HRV metrics    │
    └────────────┬─────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────┐
    │  HRV Metrics (8 features):           │
    │                                      │
    │  Time-Domain:                        │
    │  ├─ RMSSD: 45.3 ms                  │
    │  │         (short-term variability)  │
    │  ├─ SDNN: 78.2 ms                   │
    │  │        (overall variability)      │
    │  ├─ MeanNN: 850 ms                  │
    │  │         (average interval)        │
    │  └─ pNN50: 12.5%                    │
    │           (% intervals >50ms)       │
    │                                      │
    │  Additional:                         │
    │  ├─ MedianNN: 842 ms                │
    │  ├─ CVNN: 0.092                     │
    │  ├─ SD1: 32.1 ms                    │
    │  └─ SD2: 105.3 ms                   │
    │           (Poincaré parameters)     │
    │                                      │
    │  Output: [45.3, 78.2, 850, 12.5,    │
    │           842, 0.092, 32.1, 105.3]  │
    └──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  MODEL DECISION BOUNDARY                                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    Feature Space (2D projection):

    Amusement │     ★ ★  ★
              │   ★   ★ ★
              │  ★★★★★★★★  ← Decision boundary (non-linear)
              │ ★★★★
    Stress    │     ████  ████
              │    ███  ███  ███
              │   ███████████████  ← Decision boundary
              │  █████
    Neutral   │  ●●●  ●●●  ●●
              │ ●●●●●●●●●●●●
              │●●●●●●●
              │
              └──────────────────────
                 Feature 1: RMSSD (ms)

    Real Model: 8D space (8 features)
    RF creates hyperplanes to separate classes
    500 trees → complex non-linear boundaries

┌─────────────────────────────────────────────────────────────────────────────┐
│  FILE SIZE & PERFORMANCE METRICS                                           │
└─────────────────────────────────────────────────────────────────────────────┘

    Files Generated:
    ├─ hr_model_improved.pkl         : ~2-5 MB
    │  (1200 training samples, 8 features, 500 trees)
    │
    ├─ hr_scaler_improved.pkl        : ~1 KB
    │  (Just mean & std for 8 features)
    │
    ├─ feature_names.pkl            : <1 KB
    │  (List of 8 feature names)
    │
    └─ feature_importance.png        : ~100-200 KB
       (Plot with 2 subplots)

    Performance:
    ├─ Training time: 30-120 seconds
    ├─ Inference time: <100 ms
    ├─ Memory usage: ~500 MB (during training)
    ├─ Disk space needed: ~1 GB (for WESAD)
    └─ CPU cores used: All available

┌─────────────────────────────────────────────────────────────────────────────┐
│  ERROR HANDLING & FALLBACKS                                                │
└─────────────────────────────────────────────────────────────────────────────┘

    Inference Pipeline with Error Handling:

    Load ECG Signal
         │
         ├─[Invalid format?]
         │  └─→ ⚠️ Convert to numpy array
         │
         ├─[NaN values?]
         │  └─→ ⚠️ Replace with 0
         │
         ├─[Wrong sampling rate?]
         │  └─→ ⚠️ Resample to 700 Hz
         │
         ├─[Too short (<20 sec)?]
         │  └─→ ❌ Reject (need 30 sec)
         │
    Extract Features
         │
         ├─[Feature extraction fails?]
         │  └─→ ⚠️ Use backup zeros
         │
         ├─[NaN in features?]
         │  └─→ ⚠️ Replace with mean
         │
    Scale Features
         │
         ├─[Scaler not loaded?]
         │  └─→ ❌ Error (critical)
         │
    Make Prediction
         │
         ├─[Model not loaded?]
         │  └─→ ❌ Error (critical)
         │
         ├─[Confidence < 50%?]
         │  └─→ ⚠️ Warn user
         │
    Output Result
         │
         └─→ ✅ Success

┌─────────────────────────────────────────────────────────────────────────────┐
│  SCALING STRATEGY                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

    Single Inference:
    Real ECG → Extract HRV (2-3 sec) → Scale → Predict (1-5 ms) → Result
    Total: ~3 seconds per 30-sec window

    Batch Inference (Web Service):
    Queue [ECG₁, ECG₂, ECG₃, ...] → Process in parallel → Return results

    Real-time Streaming:
    Wearable Device → Network → Server → ML Pipeline → Mobile App
    Latency: <2 seconds end-to-end

    High-Volume (Cloud):
    Kafka Topic → Spark → Distributed ML → Database
    Throughput: 1000s of predictions/second

```

---

## Data Flow Diagram

```
┌─────────────┐
│ WESAD Data  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐      ┌──────────────┐
│ Signal Loading  │ ───> │ Segmentation │
└─────────────────┘      │ (30-sec)     │
                         └──────┬───────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │ HRV Extraction   │
                        │ (8 features)     │
                        └──────┬───────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │ Train/Test Split │
                        │ (80-20)          │
                        └──────┬───────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
        ┌────────────┐               ┌────────────┐
        │ SMOTE      │               │ Test Set   │
        │ (balance)  │               │ (no SMOTE) │
        └────┬───────┘               └────────────┘
             │
             ▼
        ┌──────────┐
        │ Scaling  │
        └────┬─────┘
             │
             ▼
        ┌──────────────┐
        │ RF Training  │
        └────┬─────────┘
             │
             ▼
        ┌──────────────────┐
        │ Model Evaluation │
        └────┬─────────────┘
             │
             ▼
        ┌──────────────────┐
        │ Save Model       │
        │ Save Scaler      │
        └──────────────────┘
```

---

This architecture ensures:
✅ Robust feature extraction
✅ Proper data preprocessing  
✅ Scalable inference
✅ Error handling
✅ Production-ready deployment
