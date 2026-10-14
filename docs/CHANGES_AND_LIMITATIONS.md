# Changes, test status and limitations

## Bugs / issues found in the delivered v1 and fixed
1. `requirements.txt` made the heavy, optional Hugging Face `datasets` package mandatory -> moved to `requirements-optional.txt`; added `scikit-learn`, `joblib`, `matplotlib`.
2. The app silently processed only the first 16 384 samples of any recording -> the full clip is kept; the user chooses the segment and the UI states how much is used.
3. Uploaded WAV handling had no actionable errors for empty/corrupt/NaN files or invalid sampling rates -> `audio/io.py` raises `AudioError` with a fix suggestion.
4. SNR was always shown against the loaded signal as if clean -> a "no clean reference" mode shows heuristic estimates only and says so.
5. Link-budget channel had a single global noise value -> receiver-specific noise (ambient + ships) and an optional Wenz-type model.
6. A confound I introduced and caught while testing: modelled batteries drained during 400-packet experiments and made relays "die"; the relay-failure experiment now refills batteries per packet (documented in code).

## Files added / changed (summary)
Added: `audio/` (io, features, synth, datasets), `classification/` (baseline, trained), `communication/` (framing, bpsk, acoustic_link), `simulation/` (waveform_channel, handshake, scene, run), `visualization/` (ocean_3d, audio_plots, sequence), `ui/` (common, pages_new), `experiments/extended.py`, `scripts/` (register, train, run experiments), `tests/` (test_new, test_ui_smoke, fake_streamlit), `data/manifest.json`, `docs/*.md`, `results/ext_*.csv` + `results/figures/*.png`.
Changed: `app.py` (12 pages, new sidebar), `simulation/environment.py` (scene, sessions, traces, receiver noise, routing table), `simulation/routing.py` (noise function, unreachable explanation, routing table), `simulation/acoustic_channel.py` (receiver noise, frame-size PER, Wenz option), `simulation/auv.py` (waypoints), `config/config.py` (noise model fields), requirements, README.

## Test status (as run in the delivery environment)
* `python -m compileall`: passes.  * `tests.test_core` (6 original tests): pass.  * `tests.test_new` (56 tests; audio loading, features, noise, filters, SNR, classification, datasets offline/missing, framing/CRC, BPSK vs AWGN theory, channel effects, handshake transitions, routing/ETX, relay failure/unreachable, scene/animation snapshots): pass.
* **Not run in this environment:** Streamlit and Plotly were **not installed and there was no internet**, so (a) the 3-D/Plotly figure builders were never executed against real Plotly (their test is skipped), and (b) the app was **never launched or visually inspected**. `tests/test_ui_smoke.py` runs every page and every button through a *stub* of Streamlit/Plotly - it catches Python errors and wrong data shapes but **cannot** catch Plotly schema mistakes, layout problems or real rendering issues. On your machine, run `python -m unittest discover -s tests -v`: with the real packages installed the Plotly test runs and the smoke test switches to `streamlit.testing.v1.AppTest`. Expect to possibly fix small Plotly/Streamlit API issues on first launch.

## Remaining limitations / not done
* No real recordings were downloaded (no network). No trained classifier exists; no real-data accuracy is reported. The baseline is hand-tuned, and its only checks are on synthetic generators.
* NOAA direct file URLs were not verified, so those sources are manual-register only; licence fields are "verify at source".
* Channel is isovelocity: no refraction/ray tracing, no time-varying multipath, no timing tracking in the modem (Doppler above roughly 1-2 m/s fails), no equaliser, no coding.
* Animals are decorative kinematics; they do not emit sound into the link model. Ship source levels (155/145/138 dB in-band) are assumptions.
* The network simulation's per-hop data packets use the link-budget model; only the Connection Establishment page and experiments run waveform-level BPSK.
* The 3-D scene is a precomputed playback (browser-side Play/Pause), not a live continuously-running simulation; playback speed applies when the run is re-computed. Clicking a node in the 3-D scene does not select it (use the node selector).
* The handshake is our proposal and is not claimed to match the paper or any standard. Battery values are modelled. NS-3/Aqua-Sim NG export remains the original topology-only helper.
* Microphone recording is optional and untested here (no audio device).
