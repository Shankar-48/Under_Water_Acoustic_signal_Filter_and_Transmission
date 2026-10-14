# Noise and sound classification methodology

**Categories:** biological sound, vessel-related noise, ambient environmental noise, impulsive/transient event, underwater communication signal, unknown/mixed.

**Features** (`audio/features.py`, NumPy/SciPy only): RMS, peak, duration, crest factor, zero-crossing rate, dominant frequency, spectral centroid/bandwidth/roll-off(85%)/flatness, peak-to-median ratio, tonal frame fraction, dominant-frequency stability and jump fraction, level variation, impulse ratio, kurtosis, low/high band energy ratios, heuristic SNR estimate, reference SNR (only if a clean reference is supplied).

**Engines**
1. *Heuristic baseline* (`classification/baseline.py`) - hand-written fuzzy rules; relative scores, not probabilities; **never trained or validated on real data**. Returns "Unknown or mixed" if the best score < 0.45 or the top two are within 0.08.
2. *Trained random forest* (`classification/trained.py`) - available only after `scripts/train_classifier.py` / the training panel succeeds on **registered real labelled recordings**. It refuses to train unless each class has >= 4 distinct original recordings; splits **by recording id** (no segment of one recording in both train and test); reports precision/recall/F1 and a confusion matrix on held-out recordings only.

**Current status in this delivery:** no real labelled recordings were available offline, so **no trained model exists and no real-data accuracy is reported**. `results/ext_classification_SYNTHETIC_DEMO.csv` shows the training/evaluation *mechanics* on synthetic generators (perfect scores there are expected and say nothing about the ocean).

**Observed baseline behaviour on the synthetic generators** (`results/ext_source_categories.csv`, `tests/test_new.py`): correct for the synthetic whistle, ship, impulsive and BPSK signals; wind-like noise is sometimes "Unknown"; a synthetic dolphin click train is labelled *Impulsive*; a low-frequency whale-like moan is labelled *Vessel*; a whistle mixed over ship noise is labelled *Biological* (not "mixed"). These are known weaknesses, not bugs hidden by tuning.

Detecting a vocalisation-like pattern is not species identification; the app never claims species.
