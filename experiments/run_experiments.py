"""Headless runner:  python -m experiments.run_experiments [--fast] [--seed 42]
Writes CSV files to results/ and a Markdown report to docs/results.md."""
import argparse, datetime
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
import sys; sys.path.insert(0, str(ROOT))
from experiments.experiments import run_all
from signal_processing.dataset import default_signal
from signal_processing.noise import add_gaussian_noise
from signal_processing.pipeline import denoise_pipeline


def export_signals(x, fs, seed, path):
    y, _, sigma = add_gaussian_noise(x, 5.0, np.random.default_rng(seed))
    o = denoise_pipeline(y, sigma ** 2, fs)
    import pandas as pd
    df = pd.DataFrame({"t_s": np.arange(len(x)) / fs, "original": x, "noisy": y, "kalman": o["Kalman"],
                       "lms": o["LMS (adaptive)"], "wiener": o["Wiener"], "butterworth": o["Butterworth (final)"]})
    df.to_csv(path, index=False)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fast", action="store_true"); ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    x, fs, label = default_signal()
    (ROOT / "results").mkdir(exist_ok=True)
    res = run_all(x, fs, label, a.seed, a.fast)
    md = [f"# Results (generated)\n\nGenerated {datetime.datetime.now():%Y-%m-%d %H:%M} | seed={a.seed} | fast={a.fast}\n",
          f"Signal source: **{label}**\n",
          "> These are OUR experimental results from OUR simulation under the assumptions in docs/methodology.md. "
          "They are not results reported in the research paper.\n"]
    for name, df in res.items():
        slug = name.split(" - ")[0].lower().replace(" ", "")
        df.to_csv(ROOT / "results" / f"{slug}.csv", index=False)
        md += [f"\n## {name}\n", df.to_markdown(index=False) if _has_tab() else df.to_string(index=False)]
        print(f"\n=== {name} ===\n{df.to_string(index=False)}")
    export_signals(x, fs, a.seed, ROOT / "results" / "signal_export.csv")
    (ROOT / "docs" / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\nSaved CSVs to results/ and report to docs/results.md")


def _has_tab():
    try:
        import tabulate  # noqa
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    main()
