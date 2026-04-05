"""
DIAGNOSTIC TOOL - Debug your model training issues
Run this to identify problems with data, features, or model
"""

import numpy as np
import pickle
import os
import sys

print("="*80)
print(" HEART RATE EMOTION DETECTION - DIAGNOSTIC TOOL")
print("="*80)

# ============================================================================
# 1. CHECK DATASET
# ============================================================================
print("\n" + "="*80)
print(" 1. CHECKING WESAD DATASET")
print("="*80)

base_path = r"C:\Users\rahul\Desktop\Main_Proj_imp_POC1\myprojectenv_poc1\Datasets\WESAD\WESAD"

if os.path.exists(base_path):
    print(f"✅ Dataset path found: {base_path}")
else:
    print(f"❌ Dataset path NOT found: {base_path}")
    print("   Fix: Update base_path in train_HR_improved.py")
    sys.exit(1)

# Check subjects
subjects = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]
print(f"\n✓ Checking {len(subjects)} subjects...")

available_subjects = []
for subject in subjects:
    subject_folder = os.path.join(base_path, f"S{subject}")
    pkl_file = os.path.join(subject_folder, f"S{subject}.pkl")
    
    if os.path.exists(pkl_file):
        try:
            with open(pkl_file, "rb") as f:
                data = pickle.load(f, encoding='latin1')
            
            # Check for ECG
            if 'chest' in data['signal'] and 'ECG' in data['signal']['chest']:
                ecg = data['signal']['chest']['ECG']
                labels = data['label']
                available_subjects.append(subject)
                print(f"  ✅ S{subject}: ECG shape={ecg.shape}, labels shape={labels.shape}")
            else:
                print(f"  ⚠️  S{subject}: Missing ECG data")
        except Exception as e:
            print(f"  ❌ S{subject}: Error loading - {str(e)}")
    else:
        print(f"  ❌ S{subject}: File not found")

print(f"\n✓ Available subjects: {available_subjects}")
print(f"  Total: {len(available_subjects)}/{len(subjects)}")

if len(available_subjects) < 10:
    print("\n⚠️  WARNING: Less than 10 subjects available!")
    print("   This may result in low accuracy. Consider:")
    print("   - Checking dataset path is correct")
    print("   - Verifying WESAD folder structure")
    print("   - Using binary classification instead")

# ============================================================================
# 2. CHECK DEPENDENCIES
# ============================================================================
print("\n" + "="*80)
print(" 2. CHECKING DEPENDENCIES")
print("="*80)

dependencies = [
    'numpy',
    'sklearn',
    'scipy',
    'imblearn',
    'neurokit2',
    'matplotlib',
    'seaborn'
]

print("\n✓ Checking installed packages...\n")

for pkg in dependencies:
    try:
        __import__(pkg)
        print(f"  ✅ {pkg:15s} installed")
    except ImportError:
        print(f"  ❌ {pkg:15s} NOT installed")
        print(f"     Fix: pip install {pkg}")

# ============================================================================
# 3. CHECK FEATURE EXTRACTION
# ============================================================================
print("\n" + "="*80)
print(" 3. TESTING FEATURE EXTRACTION")
print("="*80)

try:
    from hrv_features import extract_hrv_features
    print("✅ hrv_features.py imported successfully")
    
    # Test with dummy ECG
    print("\n✓ Testing feature extraction with dummy ECG...")
    dummy_ecg = np.random.randn(21000)  # 30 seconds
    features = extract_hrv_features(dummy_ecg)
    
    print(f"\n✓ Extracted features:")
    zero_count = 0
    nan_count = 0
    
    for name, value in features.items():
        if value == 0:
            status = "⚠️  (ZERO)"
            zero_count += 1
        elif np.isnan(value) or np.isinf(value):
            status = "❌ (NaN/Inf)"
            nan_count += 1
        else:
            status = "✅"
        print(f"  {name:10s}: {value:10.4f} {status}")
    
    if zero_count > 3:
        print(f"\n⚠️  WARNING: {zero_count} features are zero!")
        print("   This may indicate neurokit2 not working properly")
        print("   Try: pip install --upgrade neurokit2")
    
    if nan_count > 0:
        print(f"\n⚠️  WARNING: {nan_count} features are NaN!")
        print("   Check ECG signal quality")
    
except ImportError as e:
    print(f"❌ Error importing hrv_features.py: {e}")
    print("   Make sure hrv_features.py is in the same directory")
except Exception as e:
    print(f"❌ Error in feature extraction: {e}")

# ============================================================================
# 4. CHECK MODEL FILES
# ============================================================================
print("\n" + "="*80)
print(" 4. CHECKING SAVED MODELS")
print("="*80)

models_folder = r"C:\Users\rahul\Desktop\Heart_Rate_Emotion_Detection\HR_poc1\Models"
model_path = os.path.join(models_folder, "hr_model_improved.pkl")
scaler_path = os.path.join(models_folder, "hr_scaler_improved.pkl")

print(f"\n✓ Checking Models folder: {models_folder}")

if os.path.exists(models_folder):
    print("  ✅ Models folder exists")
    
    # List files
    files = os.listdir(models_folder)
    print(f"  ✓ Files in folder: {files}")
    
    if os.path.exists(model_path):
        print(f"  ✅ Model found: {os.path.getsize(model_path) / 1024 / 1024:.2f} MB")
    else:
        print(f"  ❌ Model not found (run train_HR_improved.py first)")
    
    if os.path.exists(scaler_path):
        print(f"  ✅ Scaler found: {os.path.getsize(scaler_path) / 1024:.2f} KB")
    else:
        print(f"  ❌ Scaler not found (run train_HR_improved.py first)")
else:
    print("  ❌ Models folder does not exist")
    print(f"     Will be created when you run train_HR_improved.py")

# ============================================================================
# 5. CHECK FEATURE NAMES CONSISTENCY
# ============================================================================
print("\n" + "="*80)
print(" 5. CHECKING FEATURE NAMES CONSISTENCY")
print("="*80)

expected_features = ["RMSSD", "SDNN", "MeanNN", "pNN50", "MedianNN", "CVNN", "SD1", "SD2"]
print(f"\n✓ Expected features: {expected_features}")

# Check hrv_features.py
print("\n✓ Checking hrv_features.py...")
try:
    with open("hrv_features.py", "r") as f:
        content = f.read()
    
    all_match = True
    for feat in expected_features:
        if feat in content:
            print(f"  ✅ {feat} found in hrv_features.py")
        else:
            print(f"  ❌ {feat} NOT found in hrv_features.py")
            all_match = False
    
    if all_match:
        print("\n  ✅ All features present in hrv_features.py")
    else:
        print("\n  ❌ Some features missing - check hrv_features.py")
except:
    print("  ⚠️  Could not read hrv_features.py")

# ============================================================================
# 6. RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80)
print(" 6. RECOMMENDATIONS")
print("="*80)

print("""
✅ If all checks passed:
   1. Run: python train_HR_improved.py
   2. Monitor accuracy (target: ≥85%)
   3. If < 85%, try binary classification
   4. Check feature_importance.png

⚠️  If dataset check failed:
   1. Verify WESAD dataset path
   2. Check folder structure: S2/, S3/, ..., S15/
   3. Each should contain S[N].pkl file
   4. Try: ls C:\\...\\WESAD\\WESAD

❌ If dependency check failed:
   1. Install missing packages: pip install [package]
   2. Verify versions:
      - numpy: 1.20+
      - scikit-learn: 0.24+
      - neurokit2: 0.2+

⚠️  If feature extraction failed:
   1. Try: pip install --upgrade neurokit2
   2. Check scipy is working
   3. Verify ECG sampling rate is 700 Hz
   4. Check signal is not all zeros
""")

print("\n" + "="*80)
print(" DIAGNOSTIC COMPLETE")
print("="*80)
