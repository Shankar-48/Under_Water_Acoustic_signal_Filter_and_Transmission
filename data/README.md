# Data

Nothing large is stored in this repository.

## Acoustic signal sources (in order of preference)
1. **OpenWhistle clips** (external public dataset of bottlenose-dolphin whistles, Hugging Face `dolphinteam/OpenWhistle-CNN`).
   Clips are 0.4 s WAV files with a `label` field (0 = noise, 1 = whistle).
   Fetch a few (streaming, no full download):
   ```bash
   pip install -r requirements-optional.txt
   python scripts/download_openwhistle_samples.py
   ```
   Files are saved to `data/samples/` (git-ignored). The app picks the first `whistle_*.wav` automatically.
   The loader was written against the dataset card's published fields (`audio`, `label`); it could not be run
   in the environment where the project was generated (no internet) - if a split name or field differs, the script
   prints the error and the app falls back to the synthetic signal.
2. **Your own WAV** via the sidebar upload.
3. **Synthetic whistle-like chirp** (fallback, always labelled "SYNTHETIC").

## Provenance (do not blur these in your report)
* The dolphin dataset is **external**; it is **not** the data used in the IEEE APSCON 2024 paper.
* Noise is **our simulated** Gaussian noise. Sensor values are **simulated**.
* Check the dataset licence on its Hugging Face page before redistributing clips.
