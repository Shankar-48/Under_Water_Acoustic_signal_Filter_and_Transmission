"""Reproducible experiments 1-8. Every number is computed here; nothing is hard-coded.
All results are OUR experimental results under OUR simulation assumptions."""
import copy
import numpy as np
import pandas as pd
from config.config import ChannelConfig, GATEWAY_ID
from simulation.environment import Environment
from communication.modem import measured_ber
from signal_processing.noise import add_gaussian_noise
from signal_processing.pipeline import denoise_pipeline, STAGES
from signal_processing.snr import snr_db, intrinsic_snr_estimate
from simulation.acoustic_channel import AcousticChannel

NOISE_LEVELS = {"Low": 15.0, "Medium": 5.0, "High": -5.0}   # input SNR in dB


def exp1_clean(x, fs, label):
    return pd.DataFrame([{"Source": label, "Samples": len(x), "fs (Hz)": fs, "Duration (s)": round(len(x) / fs, 3),
                          "RMS": round(float(np.sqrt(np.mean(x ** 2))), 4),
                          "Baseline SNR estimate (dB, heuristic)": round(intrinsic_snr_estimate(x), 2)}])


def exp2_noise(x, targets=(20, 10, 5, 0, -5), seed=42):
    rows = []
    for t in targets:
        y, _, sigma = add_gaussian_noise(x, t, np.random.default_rng(seed))
        rows.append({"Target SNR (dB)": t, "Noise sigma": round(sigma, 4), "Measured SNR after noise (dB)": round(snr_db(x, y), 2)})
    return pd.DataFrame(rows)


def _stage_snrs(x, fs, snr_in, seed):
    y, _, sigma = add_gaussian_noise(x, snr_in, np.random.default_rng(seed))
    out = denoise_pipeline(y, sigma ** 2, fs)
    return {k: snr_db(x, out[k]) for k in STAGES}, out


def exp3_denoise(x, fs, snr_in=5.0, seed=42):
    s, _ = _stage_snrs(x, fs, snr_in, seed)
    return pd.DataFrame([{"Stage": k, "SNR (dB)": round(v, 2), "Change vs noisy (dB)": round(v - s["Noisy"], 2)} for k, v in s.items()])


def exp6_noise_levels(x, fs, levels=NOISE_LEVELS, trials=5, seed=42):
    rows = []
    base = intrinsic_snr_estimate(x)
    for name, snr_in in levels.items():
        acc = {k: [] for k in STAGES}
        for t in range(trials):
            s, _ = _stage_snrs(x, fs, snr_in, seed + t)
            for k in STAGES: acc[k].append(s[k])
        m = {k: float(np.mean(v)) for k, v in acc.items()}
        rows.append({"Noise level": name, "Input SNR (dB)": snr_in, "Baseline clip SNR (est.)": round(base, 1),
                     "SNR after noise": round(m["Noisy"], 2), "After Kalman": round(m["Kalman"], 2),
                     "After LMS": round(m["LMS (adaptive)"], 2), "After Wiener": round(m["Wiener"], 2),
                     "Final (Butterworth)": round(m["Butterworth (final)"], 2),
                     "Improvement (dB)": round(m["Butterworth (final)"] - m["Noisy"], 2),
                     "Std of final (dB)": round(float(np.std(acc["Butterworth (final)"])), 2), "Trials": trials})
    return pd.DataFrame(rows)


def make_env(noise_db=112.0, seed=42, **kw):
    return Environment(ChannelConfig(noise_level_db=noise_db), seed=seed, **kw)


def exp4_single_vs_multi(noise_levels=(105, 112, 118, 122), n=2000, seed=42):
    rows = []
    for nl in noise_levels:
        env = make_env(nl, seed)
        for e in env.ids("EXPLORER"):
            for mode, lab in (("direct_range_limited", "Single-hop (range-limited)"),
                              ("direct_ignore_range", "Single-hop (range limit ignored)"),
                              ("multihop", "Multi-hop")):
                r = env.simulate_delivery(e, n, mode)
                rows.append({"Noise level (dB)": nl, "Source": e, "Scheme": lab, "Hops": r["hops"],
                             "PDR": round(r["pdr"], 4), "Min link SNR (dB)": None if np.isnan(r["min_link_snr_db"]) else round(r["min_link_snr_db"], 1),
                             "Mean delay (s)": None if np.isnan(r["mean_delay_s"]) else round(r["mean_delay_s"], 3)})
    return pd.DataFrame(rows)


def exp4b_waveform_relay_processing(x, fs, noise_levels=(112, 118, 122), trials=3, seed=42):
    """Waveform SNR at the gateway with/without denoising at relay+gateway (delivery forced)."""
    rows = []
    for nl in noise_levels:
        for proc in (False, True):
            v = []
            for t in range(trials):
                env = make_env(nl, seed + t)
                v.append(env.transmit("EXPLORER-01", x, fs, process=proc, ignore_loss=True).final_snr_db)
            rows.append({"Noise level (dB)": nl, "Relay/gateway denoising": "ON" if proc else "OFF",
                         "Mean SNR at gateway (dB)": round(float(np.mean(v)), 2), "Std (dB)": round(float(np.std(v)), 2), "Trials": trials})
    return pd.DataFrame(rows)


def exp5_link_failure(noise_db=112.0, n=2000, seed=42):
    rows = []
    for failed in ("RELAY-01", "RELAY-02"):
        for e in make_env(noise_db, seed).ids("EXPLORER"):
            env = make_env(noise_db, seed)
            b = env.route(e); pb = env.simulate_delivery(e, n)
            env.set_state(failed, "FAILED")
            a = env.route(e); pa = env.simulate_delivery(e, n)
            rows.append({"Failed node": failed, "Source": e, "Route before": " > ".join(b.path) if b else "none",
                         "Route after": " > ".join(a.path) if a else "NO ROUTE (unreachable)",
                         "Recovered": bool(a), "PDR before": round(pb["pdr"], 3), "PDR after": round(pa["pdr"], 3)})
    return pd.DataFrame(rows)


def exp7_performance(noise_levels=(105, 112, 118), n=2000, seed=42):
    rows = []
    for nl in noise_levels:
        env = make_env(nl, seed)
        for e in env.ids("EXPLORER"):
            r = env.simulate_delivery(e, n)
            rows.append({"Noise level (dB)": nl, "Source": e, "Route": r["route"], "Hops": r["hops"],
                         "PDR": round(r["pdr"], 4), "Packet loss": round(r["loss"], 4),
                         "Min link SNR (dB)": round(r["min_link_snr_db"], 1), "End-to-end delay (s)": round(r["mean_delay_s"], 3),
                         "Success rate (%)": round(100 * r["pdr"], 2)})
    return pd.DataFrame(rows)


def exp8_ber_validation(snrs=(0, 2, 4, 6, 8), n_bits=200_000):
    rows = []
    for s in snrs:
        m, t = measured_ber(s, n_bits)
        rows.append({"SNR (dB)": s, "Measured BER (BPSK sim)": round(m, 6), "Theory 0.5*erfc(sqrt(SNR))": round(t, 6)})
    return pd.DataFrame(rows)


def run_all(x, fs, label, seed=42, fast=False):
    return {
        "Exp 1 - Clean signal": exp1_clean(x, fs, label),
        "Exp 2 - Gaussian noise": exp2_noise(x, seed=seed),
        "Exp 3 - Denoising (input SNR 5 dB)": exp3_denoise(x, fs, 5.0, seed),
        "Exp 4 - Single-hop vs multi-hop (packet level)": exp4_single_vs_multi(n=500 if fast else 2000, seed=seed),
        "Exp 4b - Waveform SNR at gateway": exp4b_waveform_relay_processing(x, fs, trials=1 if fast else 3, seed=seed),
        "Exp 5 - Link failure and route recovery": exp5_link_failure(n=500 if fast else 2000, seed=seed),
        "Exp 6 - Noise levels (denoising chain)": exp6_noise_levels(x, fs, trials=2 if fast else 5, seed=seed),
        "Exp 7 - Communication performance": exp7_performance(n=500 if fast else 2000, seed=seed),
        "Exp 8 - BER model validation": exp8_ber_validation(n_bits=50_000 if fast else 200_000),
    }
