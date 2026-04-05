"""
DEBUG SCRIPT - Analyze why accuracy is low
Check feature quality, data distribution, and potential issues
"""

import numpy as np
import pickle
import os
from collections import Counter
from hrv_features import extract_hrv_features

print("="*80)
print(" FEATURE QUALITY DIAGNOSTIC TOOL")
print("="*80)

# ============================================================================
# 1. LOAD SAMPLE DATA AND CHECK FEATURES
# ============================================================================
print("\n" + "="*80)
print(" 1. LOADING SAMPLE SUBJECT DATA")
print("="*80)

base_path = r"C:\\Users\\rahul\\Desktop\\Main_Proj_imp_POC1\\myprojectenv_poc1\\Datasets\\WESAD\\WESAD"

# Test with one subject first
test_subject = 3

subject_folder = os.path.join(base_path, f"S{test_subject}")
pkl_file = os.path.join(subject_folder, f"S{test_subject}.pkl")

print(f"\nTesting subject: S{test_subject}")
print(f"File: {pkl_file}")

try:
    with open(pkl_file, "rb") as f:
        data = pickle.load(f, encoding='latin1')
    
    print("✅ File loaded successfully")
    
    # Check structure
    print(f"\nData structure:")
    print(f"  - Top-level keys: {list(data.keys())}")
    print(f"  - Signal keys: {list(data['signal'].keys())}")
    print(f"  - Chest keys: {list(data['signal']['chest'].keys())}")
    
    # Get ECG
    ecg_full = data['signal']['chest']['ECG']
    labels_full = data['label']
    
    print(f"\nECG Info:")
    print(f"  - Shape: {ecg_full.shape}")
    print(f"  - Type: {ecg_full.dtype}")
    print(f"  - Min: {ecg_full.min():.4f}")
    print(f"  - Max: {ecg_full.max():.4f}")
    print(f"  - Mean: {ecg_full.mean():.4f}")
    print(f"  - Std: {ecg_full.std():.4f}")
    
    print(f"\nLabels Info:")
    print(f"  - Shape: {labels_full.shape}")
    print(f"  - Unique: {np.unique(labels_full)}")
    print(f"  - Distribution: {dict(Counter(labels_full))}")
    
except Exception as e:
    print(f"❌ Error loading data: {e}")
    exit(1)

# ============================================================================
# 2. TEST FEATURE EXTRACTION ON MULTIPLE WINDOWS
# ============================================================================
print("\n" + "="*80)
print(" 2. TESTING FEATURE EXTRACTION")
print("="*80)

window_size = 21000  # 30 seconds
stride = 10500       # 50% overlap

print(f"\nParameters:")
print(f"  - Window size: {window_size} samples (30s @ 700Hz)")
print(f"  - Stride: {stride} samples")
print(f"  - Total ECG length: {len(ecg_full)} samples")

all_features = []
all_labels = []
zero_count = 0
nan_count = 0

for start in range(0, len(ecg_full) - window_size, stride):
    ecg_window = ecg_full[start:start + window_size, 0]
    label_window = int(labels_full[start])
    
    if label_window not in [1, 2, 3]:
        continue
    
    features = extract_hrv_features(ecg_window)
    all_features.append(features)
    all_labels.append(label_window)
    
    # Check for zeros and NaN
    for name, value in features.items():
        if value == 0:
            zero_count += 1
        if np.isnan(value) or np.isinf(value):
            nan_count += 1

print(f"\nExtracted {len(all_features)} windows from S{test_subject}")
print(f"Zero values found: {zero_count} / {len(all_features) * 8}")
print(f"NaN/Inf values found: {nan_count} / {len(all_features) * 8}")

if zero_count / (len(all_features) * 8) > 0.5:
    print("❌ WARNING: >50% zero values - feature extraction may be failing!")
elif nan_count / (len(all_features) * 8) > 0.1:
    print("❌ WARNING: >10% NaN values - signal quality may be poor")
else:
    print("✅ Feature extraction looks reasonable")

# ============================================================================
# 3. ANALYZE FEATURE STATISTICS
# ============================================================================
print("\n" + "="*80)
print(" 3. FEATURE STATISTICS")
print("="*80)

# Convert to array
features_array = np.array([[f[name] for name in ["RMSSD", "SDNN", "MeanNN", "pNN50", "MedianNN", "CVNN", "SD1", "SD2"]] 
                           for f in all_features])

feature_names = ["RMSSD", "SDNN", "MeanNN", "pNN50", "MedianNN", "CVNN", "SD1", "SD2"]

print("\nFeature Statistics:")
print("-" * 80)
print(f"{'Feature':<12} {'Mean':<12} {'Std':<12} {'Min':<12} {'Max':<12} {'Zeros':<8}")
print("-" * 80)

for i, name in enumerate(feature_names):
    feature_col = features_array[:, i]
    zero_pct = np.sum(feature_col == 0) / len(feature_col) * 100
    print(f"{name:<12} {feature_col.mean():<12.4f} {feature_col.std():<12.4f} "
          f"{feature_col.min():<12.4f} {feature_col.max():<12.4f} {zero_pct:<7.1f}%")

# ============================================================================
# 4. CHECK DATA QUALITY ISSUES
# ============================================================================
print("\n" + "="*80)
print(" 4. DATA QUALITY ASSESSMENT")
print("="*80)

issues = []

# Check for zero-variance features
for i, name in enumerate(feature_names):
    feature_col = features_array[:, i]
    if feature_col.std() < 0.1:
        issues.append(f"❌ {name}: Low variance (std={feature_col.std():.4f})")
    elif feature_col.std() == 0:
        issues.append(f"❌ {name}: Zero variance (constant value)")

# Check for extreme outliers
for i, name in enumerate(feature_names):
    feature_col = features_array[:, i]
    if (feature_col > 100000).any() or (feature_col < -100000).any():
        issues.append(f"❌ {name}: Extreme outliers detected")

# Check for correlation issues
print("\nFeature Correlation Matrix (first 3 features):")
correlation = np.corrcoef(features_array[:, :3].T)
print(correlation)

if len(issues) > 0:
    print("\n⚠️  ISSUES DETECTED:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n✅ No obvious data quality issues")

# ============================================================================
# 5. RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80)
print(" 5. RECOMMENDATIONS")
print("="*80)

print("""
If accuracy is <75%, consider:

1. CHECK FEATURES:
   ✓ Run this diagnostic on multiple subjects
   ✓ Look for patterns in the output
   ✓ Check if features are mostly zero

2. TRY BINARY CLASSIFICATION:
   ✓ Much easier (90%+ accuracy typical)
   ✓ Edit train_HR_improved.py line ~125
   ✓ Map: {1: 0, 2: 1, 3: 0}  # Non-stress vs Stress

3. ADJUST WINDOW SIZE:
   ✓ Try 20-25 seconds (shorter)
   ✓ Try 40-60 seconds (longer)
   ✓ Current: 30 seconds

4. FILTER BAD FEATURES:
   ✓ Remove features with zero/low variance
   ✓ Remove features with extreme outliers
   ✓ Use only top 3-4 most important

5. INCREASE MODEL COMPLEXITY:
   ✓ Try n_estimators=1000 (instead of 500)
   ✓ Try max_depth=20 (instead of 15)
   ✓ Try GradientBoosting instead of RF

6. USE MORE DATA:
   ✓ Include all subjects (if available)
   ✓ Use different window overlaps
   ✓ Collect new subjects if possible
""")

print("\n" + "="*80)
