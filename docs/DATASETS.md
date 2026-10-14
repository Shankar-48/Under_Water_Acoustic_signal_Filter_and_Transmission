# Datasets, sources and attribution

Real recordings are **not bundled**. `data/manifest.json` lists public sources; `data/local_registry.json` lists the individual files you register; `data/download_status.json` logs every download attempt and its exact error.

| Source | Page | Fetch method here |
|---|---|---|
| NOAA Fisheries - Sounds in the Ocean: Environmental and Anthropogenic | https://www.fisheries.noaa.gov/national/science-data/sounds-ocean-environmental-and-anthropogenic | manual download, then register |
| NOAA NCEI Passive Acoustic Data Archive | https://www.ncei.noaa.gov/products/passive-acoustic-data | manual (large archive; take one short clip) |
| NOAA Passive Acoustic Data Viewer | https://www.ncei.noaa.gov/maps/passive-acoustic-data/ | viewer only |
| OpenWhistle | https://sumbre-lab.github.io/openwhistle/ | automatic via Hugging Face `dolphinteam/OpenWhistle-CNN` (needs internet + `datasets`) |

I could not verify direct file URLs offline, so none are invented: NOAA entries are manual by design. **Licence fields read "not verified automatically"** - read the usage statement on each source page before redistributing, and fill the licence field when you register a file.

```bash
python scripts/download_openwhistle_samples.py          # optional, internet
python scripts/register_local_file.py clip.wav --label vessel_large \
   --source-url "<page URL>" --attribution "NOAA ..." --licence "<terms>" --recording-id clip001
python scripts/train_classifier.py                       # only if >= 4 recordings per class are registered
```
If a download fails the app shows the error and keeps working with uploads and **clearly labelled synthetic** examples; it never substitutes synthetic audio silently.
