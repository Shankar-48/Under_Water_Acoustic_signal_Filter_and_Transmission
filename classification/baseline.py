"""Heuristic, feature-based sound classifier (NO training).

Each category gets a rule score in [0,1] built from fuzzy ramps over measured features. The scores are
RELATIVE decision scores, not calibrated probabilities. Thresholds are hand-chosen from general
knowledge of underwater acoustics (e.g. ship noise is low-frequency and continuous; dolphin whistles are
tonal and frequency-modulated; impulsive events have high crest factor). They have NOT been fitted to or
validated on real labelled recordings. Treat output as a transparent first-pass hint.
"""
from __future__ import annotations
import numpy as np
from audio.features import extract_features

CATEGORIES = ["Biological sound", "Vessel-related noise", "Ambient environmental noise",
              "Impulsive or transient event", "Underwater communication signal", "Unknown or mixed sound"]
MODE_BASELINE = "Heuristic baseline (not trained; unvalidated on real data)"
LIMITATIONS = [
    "Rule thresholds are hand-chosen; they were not trained or validated on real labelled ocean recordings.",
    "Real recordings often contain overlapping sources; one label per clip is a simplification.",
    "A 'biological' result means a tonal/pulsed pattern typical of vocalisations, NOT a species identification.",
    "Low-frequency whale calls overlap vessel and seismic bands, so these categories can be confused.",
    "The score is a relative rule score, not a calibrated probability.",
]


def ramp(v, lo, hi):
    return float(np.clip((v - lo) / (hi - lo), 0.0, 1.0)) if hi != lo else float(v >= hi)


def category_scores(f):
    tonal = ramp(f["peak_to_median_db"], 15, 35)
    tonal_frames = ramp(f["tonal_frame_fraction"], 0.3, 0.8)
    stable = 1 - ramp(f["dominant_freq_rel_std"], 0.03, 0.12)           # 1 = constant frequency
    smooth = 1 - ramp(f["freq_jump_fraction"], 0.1, 0.5)                # continuous frequency track (not hopping between lines)
    fm = ramp(f["dominant_freq_rel_std"], 0.05, 0.2) * smooth           # smooth frequency modulation
    hf = ramp(f["dominant_freq_hz"], 1000, 4000)
    impulsive = max(ramp(f["impulse_ratio_db"], 12, 30), ramp(f["kurtosis_excess"], 5, 30))
    steady = 1 - ramp(f["level_std_db"], 2, 8)
    low = ramp(f["low_band_ratio"], 0.4, 0.85)
    flat = ramp(f["spectral_flatness"], 0.01, 0.2)
    narrow = 1 - ramp(f["spectral_bandwidth_hz"] / max(f["spectral_centroid_hz"], 1.0), 0.2, 0.8)
    s = {}
    s["Biological sound"] = 0.3 * tonal_frames * smooth + 0.3 * fm + 0.1 * tonal + 0.3 * hf - 0.3 * impulsive * (1 - tonal)
    s["Vessel-related noise"] = 0.35 * low * steady + 0.2 * steady + 0.15 * (1 - impulsive) + 0.15 * (1 - hf) + 0.15 * (1 - fm) - 0.45 * impulsive
    s["Ambient environmental noise"] = 0.3 * steady + 0.25 * (1 - tonal) + 0.2 * (1 - impulsive) + 0.15 * flat + 0.1 * (1 - low) - 0.4 * impulsive - 0.2 * tonal
    s["Impulsive or transient event"] = 0.7 * impulsive + 0.15 * (1 - steady) + 0.15 * (1 - tonal_frames)
    s["Underwater communication signal"] = 0.35 * tonal * stable + 0.25 * tonal_frames * stable + 0.2 * steady + 0.2 * narrow
    s = {k: float(np.clip(v, 0, 1)) for k, v in s.items()}
    return s


def classify(x, fs, reference=None):
    """Return dict(prediction, scores, ranked, features, mode, limitations, notes)."""
    f = extract_features(x, fs, reference)
    scores = category_scores(f)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    (b, bs), (_, ss) = ranked[0], ranked[1]
    notes = []
    pred = b
    if bs < 0.45:
        pred = "Unknown or mixed sound"; notes.append("No category reached a rule score of 0.45.")
    elif bs - ss < 0.08:
        pred = "Unknown or mixed sound"; notes.append(f"Top two categories are within 0.08 ({b} vs {ranked[1][0]}); possibly overlapping sources.")
    if fs < 8000 and f["dominant_freq_hz"] > 0.4 * fs:
        notes.append("Sampling rate is low; high-frequency content (e.g. dolphin clicks) cannot be represented.")
    return {"prediction": pred, "top_candidate": b, "scores": scores, "ranked": ranked, "features": f,
            "mode": MODE_BASELINE, "limitations": LIMITATIONS, "notes": notes}
