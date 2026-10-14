"""Fetch a few OpenWhistle clips into data/samples/ (streaming, small download)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from signal_processing.dataset import fetch_openwhistle_samples

if __name__ == "__main__":
    w, n = fetch_openwhistle_samples()
    print(f"Saved {w} whistle clips and {n} noise clips to data/samples/")
