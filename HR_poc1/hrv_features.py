import neurokit2 as nk
import numpy as np

def extract_hrv_features(ecg_signal, sampling_rate=700):
    try:
        # Clean ECG signal
        cleaned = nk.ecg_clean(ecg_signal, sampling_rate=sampling_rate)

        # Detect R-peaks
        peaks, _ = nk.ecg_peaks(cleaned, sampling_rate=sampling_rate)

        # Compute HRV features
        hrv = nk.hrv(peaks, sampling_rate=sampling_rate, show=False)

        # Extract important features (safe access)
        features = {
            "RMSSD": float(hrv.get("HRV_RMSSD", [0])[0]),
            "SDNN": float(hrv.get("HRV_SDNN", [0])[0]),
            "MeanNN": float(hrv.get("HRV_MeanNN", [0])[0]),
            "pNN50": float(hrv.get("HRV_pNN50", [0])[0]),
            "MedianNN": float(hrv.get("HRV_MedianNN", [0])[0]),
            "CVNN": float(hrv.get("HRV_CVNN", [0])[0]),
            "SD1": float(hrv.get("HRV_SD1", [0])[0]),
            "SD2": float(hrv.get("HRV_SD2", [0])[0]),
        }

        # Handle missing or infinite values
        for key in features:
            if np.isnan(features[key]) or np.isinf(features[key]):
                features[key] = 0.0

        return features

    except Exception as e:
        print(f"Feature extraction error: {e}")
        return {
            "RMSSD": 0.0,
            "SDNN": 0.0,
            "MeanNN": 0.0,
            "pNN50": 0.0,
            "MedianNN": 0.0,
            "CVNN": 0.0,
            "SD1": 0.0,
            "SD2": 0.0
        }