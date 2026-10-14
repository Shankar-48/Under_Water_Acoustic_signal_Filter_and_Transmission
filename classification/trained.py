"""Optional supervised classifier trained on LABELLED recordings registered in data/local_registry.json.

Rules that prevent fake or leaky results:
  * refuses to train unless every class has >= MIN_RECORDINGS distinct ORIGINAL recordings;
  * segments of one recording share a group id and never appear on both sides of the split;
  * metrics (precision/recall/F1/confusion matrix) are computed ONLY on the held-out groups;
  * nothing is reported if no model file exists - the UI then falls back to the heuristic baseline.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from audio.features import extract_features, FEATURE_NAMES

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "classifier.joblib"
MIN_RECORDINGS = 4
SEG_S = 1.0
FEATS = [n for n in FEATURE_NAMES if n not in ("snr_est_db", "duration_s", "rms", "peak")]   # level-independent


class TrainingError(RuntimeError):
    pass


def segments_from_clips(items, seg_s=SEG_S, max_seg=40):
    """items: iterable of (samples, fs, label, recording_id) -> X, y, groups."""
    X, y, g = [], [], []
    for x, fs, label, rid in items:
        n = int(seg_s * fs)
        if len(x) < n:
            starts = [0]; n = len(x)
        else:
            starts = list(range(0, len(x) - n + 1, n))[:max_seg]
        for s in starts:
            seg = x[s:s + n]
            if len(seg) < 256 or np.max(np.abs(seg)) == 0:
                continue
            f = extract_features(seg / np.max(np.abs(seg)), fs)
            X.append([f[k] for k in FEATS]); y.append(label); g.append(rid)
    return np.array(X), np.array(y), np.array(g)


def grouped_split(y, groups, test_fraction=0.3, seed=0):
    """Split by recording id with every class represented in train and test. Returns train_idx, test_idx."""
    rng = np.random.default_rng(seed)
    classes = sorted(set(y))
    train_g, test_g = set(), set()
    for c in classes:
        gs = sorted(set(groups[y == c]))
        rng.shuffle(gs)
        k = max(1, int(round(len(gs) * test_fraction)))
        if len(gs) - k < 1:
            raise TrainingError(f"Class {c!r} has too few recordings ({len(gs)}) for a leak-free split.")
        test_g.update(gs[:k]); train_g.update(gs[k:])
    assert not (train_g & test_g)
    tr = np.array([i for i, gg in enumerate(groups) if gg in train_g]); te = np.array([i for i, gg in enumerate(groups) if gg in test_g])
    return tr, te


def train(items, seed=0, save_path=None, demo_label=None):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix
    items = list(items)
    if not items:
        raise TrainingError("No labelled recordings are registered. Register real, labelled WAV files first (Data Explorer -> Register, or scripts/register_local_file.py).")
    X, y, g = segments_from_clips(items)
    if len(y) == 0:
        raise TrainingError("Registered recordings contain no usable (non-silent) segments.")
    for c in sorted(set(y)):
        n = len(set(g[y == c]))
        if n < MIN_RECORDINGS:
            raise TrainingError(f"Class {c!r}: only {n} original recording(s); need >= {MIN_RECORDINGS} to train and test without leakage.")
    tr, te = grouped_split(y, g, seed=seed)
    clf = RandomForestClassifier(n_estimators=200, random_state=seed, class_weight="balanced")
    clf.fit(X[tr], y[tr]); pred = clf.predict(X[te])
    labels = sorted(set(y))
    rep = classification_report(y[te], pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(y[te], pred, labels=labels)
    info = {"labels": labels, "n_train_segments": int(len(tr)), "n_test_segments": int(len(te)),
            "n_train_recordings": len(set(g[tr])), "n_test_recordings": len(set(g[te])), "report": rep,
            "confusion_matrix": cm.tolist(), "features": FEATS, "demo": demo_label}
    if save_path:
        import joblib
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": clf, "info": info}, save_path)
    return clf, info


def model_available(path=MODEL_PATH):
    return Path(path).exists()


def predict(x, fs, path=MODEL_PATH):
    import joblib
    if not Path(path).exists():
        raise TrainingError("No trained model found (models/classifier.joblib). Using the heuristic baseline instead.")
    blob = joblib.load(path); clf, info = blob["model"], blob["info"]
    f = extract_features(x / (np.max(np.abs(x)) + 1e-20), fs)
    v = np.array([[f[k] for k in info["features"]]])
    proba = clf.predict_proba(v)[0]
    ranked = sorted(zip(clf.classes_, proba), key=lambda kv: -kv[1])
    return {"prediction": ranked[0][0], "ranked": [(str(a), float(b)) for a, b in ranked], "features": f,
            "mode": "Trained random forest (RF vote fractions, not calibrated probabilities)", "model_info": info}
