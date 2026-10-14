"""Acoustic feature extraction (NumPy/SciPy only; librosa is not required).

Spectral descriptors use a Welch power spectral density. All amplitudes are in the clip's own units
(digital full scale unless calibrated), so absolute levels are NOT acoustic pressures.
"""
from __future__ import annotations
import numpy as np
from scipy.signal import welch, spectrogram, hilbert
from scipy.stats import kurtosis

FEATURE_NAMES = ["rms", "peak", "duration_s", "crest_factor_db", "zero_crossing_rate", "dominant_freq_hz",
                 "spectral_centroid_hz", "spectral_bandwidth_hz", "spectral_rolloff_hz", "spectral_flatness",
                 "peak_to_median_db", "tonal_frame_fraction", "dominant_freq_rel_std", "freq_jump_fraction", "level_std_db",
                 "impulse_ratio_db", "kurtosis_excess", "low_band_ratio", "high_band_ratio", "snr_est_db"]


def compute_psd(x, fs, nperseg=None):
    x = np.asarray(x, float)
    nperseg = nperseg or int(min(len(x), max(256, 2 ** int(np.log2(max(len(x) // 8, 256))))))
    f, p = welch(x - np.mean(x), fs, nperseg=nperseg, noverlap=nperseg // 2)
    return f, p


def compute_spectrogram(x, fs, nperseg=None):
    x = np.asarray(x, float)
    nperseg = nperseg or int(min(len(x), 512 if fs <= 64000 else 1024))
    f, t, S = spectrogram(x - np.mean(x), fs, nperseg=nperseg, noverlap=int(nperseg * 0.75))
    return f, t, S


def intrinsic_snr_estimate(x, frame=256):
    """HEURISTIC loudest-25%-frames vs quietest-25%-frames estimate. NOT a ground-truth SNR."""
    x = np.asarray(x, float)
    n = len(x) // frame
    if n < 8:
        return float("nan")
    p = np.sort(np.mean(x[: n * frame].reshape(n, frame) ** 2, axis=1))
    k = max(1, n // 4)
    noise, sig = np.mean(p[:k]) + 1e-20, np.mean(p[-k:])
    return float(10 * np.log10(max(sig - noise, 1e-20) / noise))


def extract_features(x, fs, reference=None):
    """Return dict of scalar features. If a clean `reference` of equal length is given, adds `snr_ref_db`."""
    x = np.asarray(x, float)
    if len(x) < 64:
        raise ValueError("need at least 64 samples")
    x0 = x - np.mean(x)
    rms = float(np.sqrt(np.mean(x0 ** 2)))
    peak = float(np.max(np.abs(x0)))
    f, p = compute_psd(x0, fs)
    p = np.maximum(p, 1e-30)
    tot = p.sum()
    centroid = float(np.sum(f * p) / tot)
    bw = float(np.sqrt(np.sum(((f - centroid) ** 2) * p) / tot))
    roll = float(f[min(np.searchsorted(np.cumsum(p) / tot, 0.85), len(f) - 1)])
    flat = float(np.exp(np.mean(np.log(p))) / np.mean(p))
    band = f > 0.01 * fs                                # ignore DC leakage
    pk = int(np.argmax(np.where(band, p, 0)))
    dom = float(f[pk])
    ptm = float(10 * np.log10(p[pk] / np.median(p[band])))
    fr, tt, S = compute_spectrogram(x0, fs)
    S = np.maximum(S, 1e-30)
    fb = fr > 0.01 * fs
    peaks = np.argmax(np.where(fb[:, None], S, 0), axis=0)
    dfreq = fr[peaks]
    prom = 10 * np.log10(S[peaks, np.arange(S.shape[1])] / np.median(S[fb], axis=0))
    frame_e = S.sum(axis=0)
    active = frame_e > 0.1 * frame_e.max()
    tonal = float(np.mean((prom > 15)[active])) if active.any() else 0.0
    rel_std = float(np.std(dfreq[active]) / max(np.mean(dfreq[active]), 1.0)) if active.any() else 0.0
    da = dfreq[active]
    jump = float(np.mean(np.abs(np.diff(da)) > 0.1 * max(np.mean(da), 1.0))) if len(da) > 2 else 0.0
    lev = 10 * np.log10(frame_e)
    env = np.abs(hilbert(x0))
    n_env = max(1, len(env) // 64)
    env_blocks = env[: n_env * 64].reshape(n_env, 64).mean(axis=1) if n_env > 1 else env
    imp = float(20 * np.log10(np.max(env_blocks) / (np.median(env_blocks) + 1e-20) + 1e-20))
    lo, hi = p[f < 500].sum() / tot, p[f > 10000].sum() / tot
    out = {"rms": rms, "peak": peak, "duration_s": len(x) / fs, "crest_factor_db": float(20 * np.log10(peak / (rms + 1e-20) + 1e-20)),
           "zero_crossing_rate": float(np.mean(np.abs(np.diff(np.signbit(x0).astype(int))))),
           "dominant_freq_hz": dom, "spectral_centroid_hz": centroid, "spectral_bandwidth_hz": bw,
           "spectral_rolloff_hz": roll, "spectral_flatness": flat, "peak_to_median_db": ptm,
           "tonal_frame_fraction": tonal, "dominant_freq_rel_std": rel_std, "freq_jump_fraction": jump, "level_std_db": float(np.std(lev[active])) if active.any() else 0.0,
           "impulse_ratio_db": imp, "kurtosis_excess": float(kurtosis(x0)), "low_band_ratio": float(lo), "high_band_ratio": float(hi),
           "snr_est_db": intrinsic_snr_estimate(x0)}
    if reference is not None:
        r = np.asarray(reference, float)
        if r.shape == x.shape and np.sum(r ** 2) > 0:
            err = np.sum((r - x) ** 2)
            out["snr_ref_db"] = float("inf") if err <= 1e-30 else float(10 * np.log10(np.sum(r ** 2) / err))
    return out
