import neurokit2 as nk
import numpy as np


def extract_hrv_features(ecg_signal, sampling_rate=700):
    """
    Extract HRV features safely from ECG signal.
    Returns a dictionary of features or None if extraction fails.
    """

    try:
        # -----------------------------
        # 1. Validate input signal
        # -----------------------------
        if ecg_signal is None or len(ecg_signal) < sampling_rate * 5:
            raise ValueError("ECG signal too short (need at least 5 seconds)")

        ecg_signal = np.asarray(ecg_signal).flatten()

        print(f"Window length: {len(ecg_signal)}, cleaned length: {len(cleaned)}")
        print(f"First 5 ECG samples: {ecg_signal[:5]}")
        print(f"First 5 cleaned samples: {cleaned[:5]}")
        
        # -----------------------------
        # 2. Clean ECG signal
        # -----------------------------
        cleaned = nk.ecg_clean(ecg_signal, sampling_rate=sampling_rate)
        cleaned = np.asarray(cleaned).flatten()
        
        # -----------------------------
        # 3. Detect R-peaks
        # -----------------------------
        peaks, _ = nk.ecg_peaks(cleaned, sampling_rate=sampling_rate)

        if "ECG_R_Peaks" not in peaks:
            raise ValueError("R-peaks not detected")

        rpeaks = peaks["ECG_R_Peaks"]

        # -----------------------------
        # 4. Validate peak count
        # -----------------------------
        if len(rpeaks) < 5:
            raise ValueError(f"Not enough R-peaks ({len(rpeaks)})")

        # -----------------------------
        # 5. Compute HRV safely
        # -----------------------------
        hrv = nk.hrv(peaks, sampling_rate=sampling_rate, show=False)

        # -----------------------------
        # 6. Extract features safely
        # -----------------------------
        def safe_get(feature_name):
            val = hrv.get(feature_name, [None])
            if isinstance(val, (list, np.ndarray)):
                val = val[0] if len(val) > 0 else None
            if val is None or np.isnan(val) or np.isinf(val):
                return None
            return float(val)

        features = {
            "RMSSD": safe_get("HRV_RMSSD"),
            "SDNN": safe_get("HRV_SDNN"),
            "pNN50": safe_get("HRV_pNN50"),
            "LF": safe_get("HRV_LF"),
            "HF": safe_get("HRV_HF"),
            "LF_HF": safe_get("HRV_LFHF"),
        }

        # -----------------------------
        # 7. Check for any missing values
        # -----------------------------
        if any(v is None for v in features.values()):
            # Skip this window if any feature failed
            return None

        return features

    except Exception as e:
        print(f"Feature extraction error: {e}")
        return None