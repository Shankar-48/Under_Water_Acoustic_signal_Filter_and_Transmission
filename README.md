# UASN Virtual Testbed v2 - Underwater Acoustic Monitoring, Noise Classification, Signal Processing and AUV Communication Simulator

An interactive research prototype (Python + Streamlit + Plotly) for a third-year engineering project. **It is a simulator**: sound recordings are stored/uploaded/synthetic files, the channel and network are simulated, and nothing listens to the real ocean.

## What is new in v2 (all implemented and tested unless listed under limitations)
* **Ocean Environment**: animated 3-D playback of a computed run - AUV waypoint patrol (turn, change depth, pause), ships, fish schools, dolphins, hydrophones, packets travelling the real route, losses marked at the failing link, link colours from link-budget SNR, failure injection, Play/Pause/Reset + time slider, node details.
* **Acoustic Data Explorer**: WAV upload, playback, waveform/spectrogram/PSD, sampling rate/duration/channels, dataset manifest + status screen, registration of downloaded files with source/licence/attribution, optional microphone recording (airborne sound only).
* **Noise Classification**: feature extraction + transparent heuristic baseline; grouped-split trained classifier pipeline (refuses to train without enough real labelled recordings).
* **Connection Establishment**: proposed 10-step handshake with timestamps, retries, timeouts, reconnect, fault injection and a sequence diagram; waveform-level digital link (framing, CRC-16, BPSK, ARQ) separate from passive monitoring.
* **Waveform channel**: spreading, Thorp absorption, Wenz-type ambient noise, image-method multipath, Doppler, interference - each switchable.
* **Routing**: ETX/Dijkstra over the *current* graph (including ship-raised receiver noise), alternative route, explicit "unreachable" reasons, routing-table change log, modelled battery.
* **Experiments**: `experiments/extended.py` writes CSV (with a `data_mode` column) and PNG graphs.
* **Original pages kept**: Dashboard, Network Simulation, Node Details, Results (experiments 1-8), Faculty Demo, About. Filters, ETX and original tests unchanged.

Documentation: `docs/ARCHITECTURE.md` (Mermaid architecture + handshake sequence), `docs/CHANNEL.md`, `docs/CLASSIFICATION.md`, `docs/DATASETS.md`, `docs/FACULTY_DEMO.md` (10-minute script), `docs/CHANGES_AND_LIMITATIONS.md`.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt      # optional extras: pip install -r requirements-optional.txt
streamlit run app.py                 # http://localhost:8501
python -m unittest discover -s tests -v          # all tests
python scripts/run_extended_experiments.py [--full]   # CSVs -> results/, graphs -> results/figures/
```
Python 3.10+ (developed on 3.12). No GPU, API keys or paid services needed. Works offline.

---
# Original project README (v1, retained)

# Virtual Underwater Acoustic Sensor Network with Multi-Hop AUV Communication and Acoustic Signal Processing

A software-only **virtual test-bed** (Python + Streamlit + Plotly) in which simulated AUVs and sensor nodes exchange packets over a simulated acoustic channel, and received signals are denoised by Kalman, LMS, Wiener and Butterworth filters.

> **Academic honesty.** This project re-creates *concepts* from the published paper. Its numbers are **our experimental results** under **our simulation assumptions**; they are not the paper's results. The dolphin dataset is an **external** public dataset, not the paper's data. Sensor values are **simulated**.

## 1-3. Title, Abstract, Problem statement
**Abstract.** Underwater Acoustic Sensor Networks (UASN) enable continuous, real-time ocean sampling but suffer from limited range, high noise and long delay. We build a virtual UASN containing a surface gateway, a master/sink AUV, relay AUVs, explorer AUVs and sensor nodes. Packets travel Explorer -> Relay -> Master -> Gateway through a link-budget acoustic channel with Gaussian noise; a real signal-processing chain (Kalman -> LMS -> Wiener -> Butterworth) denoises waveforms and SNR is measured at every stage. Routing is best-link (ETX/Dijkstra) with automatic recovery from relay failure.

**Problem.** Physical underwater test-beds are expensive and hard to access; students need a transparent environment to study multi-hop acoustic networking and denoising.

## 4. Objectives
1. Model a UASN with transducer, hydrophone, modem, sensors and AUV roles in software.
2. Demonstrate multi-hop communication and compare it with single-hop.
3. Implement and measure real denoising filters (no fake graphs).
4. Show route recovery after a relay failure.
5. Provide reproducible experiments and honest reporting.

## 5-6. Existing vs proposed system
*Existing (paper):* physical UASN demonstration with transducers, hydrophones, oceanographic sensors and underwater modems; multi-hop communication; NS-3/Aqua-Sim NG context.
*Proposed (ours):* the same concepts as a virtual test-bed, plus our own signal-processing study on real public acoustic clips. See the comparison table in the app (About page) and `docs/methodology.md`.

## 7. System architecture
See `docs/architecture.md`. Packages: `config/`, `simulation/`, `communication/`, `signal_processing/`, `visualization/`, `experiments/`, `app.py`.

## 8. Main algorithm
```
Oceanographic Sensor -> Explorer AUV --acoustic--> Virtual Channel (+Gaussian noise) -> Virtual Hydrophone
   -> signal processing -> Relay AUV --acoustic--> Master AUV / Sink --acoustic--> Surface Gateway -> Base station
```
Details in `docs/algorithm.md`.

## 9. Signal-processing algorithm
`Original -> + Gaussian noise -> Kalman -> LMS (NLMS) -> Wiener -> Butterworth low-pass -> SNR`.
`SNR_dB = 10 log10( sum x^2 / sum (x - x_hat)^2 )`.

## 10. Routing algorithm
Best-link multi-hop routing: Dijkstra over links weighted by ETX = 1/(1-PER); nodes must be ACTIVE and in range; the gateway is reached only through the Master. An alternative route is computed by excluding each intermediate node.

## 11. Technologies
Python 3.10+, NumPy, SciPy (filters), Pandas, Plotly (3-D + charts), Streamlit (UI). Optional: Hugging Face `datasets`, MATLAB, NS-3/Aqua-Sim NG. PyTorch is **not** used (see Future enhancements).

## 12. Dataset
OpenWhistle (`dolphinteam/OpenWhistle-CNN`, bottlenose-dolphin whistles, 0.4 s clips). Optional download: `python scripts/download_openwhistle_samples.py`. Fallback: synthetic whistle-like chirp (always labelled). See `data/README.md`.

## 13. Installation
```bash
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows
pip install -r requirements.txt
```
## 14. Running
```bash
streamlit run app.py               # open http://localhost:8501
python -m unittest tests.test_core # 6 unit tests
python -m experiments.run_experiments [--fast]   # CSVs -> results/, report -> docs/results.md
```
Use **Faculty Demo Mode** in the sidebar for the 15-step, 5-10 minute presentation.

## 15. Screenshots
Add your own after running: `docs/img/dashboard.png`, `docs/img/network3d.png`, `docs/img/signal_lab.png`, `docs/img/results.png` (placeholders).

## 16. Experiments
1 clean signal | 2 Gaussian noise (target vs measured SNR) | 3 denoising chain | 4 single-hop vs multi-hop (+4b waveform SNR with/without relay denoising) | 5 link failure | 6 noise levels | 7 communication performance | 8 BER-model validation.

## 17. Results (our run: seed 42, **synthetic** signal, `docs/results.md` has everything)
Denoising chain, mean of 5 noise draws:

| Noise | Input SNR | After Kalman | After LMS | After Wiener | Final | Improvement |
|---|---|---|---|---|---|---|
| Low | 15 dB | 15.19 | 15.08 | 14.96 | 14.97 | -0.02 dB |
| Medium | 5 dB | 6.26 | 8.42 | 7.41 | 7.43 | +2.44 dB |
| High | -5 dB | -0.48 | 0.10 | -0.36 | -0.40 | +4.61 dB |

Waveform SNR at the gateway (Explorer-01, 3 hops): denoising OFF/ON = 8.27/9.99 dB (noise 112 dB), 1.82/6.06 dB (118 dB), -2.98/2.74 dB (122 dB).
Link failure: with RELAY-01 down, EXPLORER-01 re-routes via RELAY-02; EXPLORER-02 becomes unreachable (it only has RELAY-01 in range) - a real limitation of this topology.
**Interpretation:** the cascade helps when noise is high and gives no benefit (slightly negative) at high SNR, because smoothing also removes signal detail. Re-run on your own machine / with real OpenWhistle clips; numbers will differ.

## 18. Limitations
Simplified channel (no multipath/Doppler/stratification); BER model assumes Eb/N0 = SNR; fixed hand-chosen filter parameters; reference-based SNR (needs the clean signal, only possible in simulation); no MAC collisions/retransmission (except demo ARQ); 3-D plot supports hover and a selection list rather than click-to-select; Streamlit/Plotly UI rendering was not browser-tested by the project generator - see Troubleshooting.

## 19. Future enhancements
* Optional PyTorch whistle **detector**: input = spectrogram, model = small CNN, output = whistle/noise, data = OpenWhistle labels, metric = F1 on held-out recordings. Only add it if you can explain and evaluate it.
* Multipath/Doppler channel, MAC protocol (TDMA), mobility-aware routing, NS-3/Aqua-Sim NG validation.

## 20. Conclusion
The test-bed shows why multi-hop acoustic relaying and receiver-side denoising matter, with every metric computed by code and labelled by provenance.

## 21. References
1. 2024 IEEE Applied Sensing Conference (APSCON), Goa, India, 22-24 Jan 2024, DOI 10.1109/APSCON60364.2024.10465917 (research basis; read the full paper for authors/title and cite properly).
2. OpenWhistle dataset, Hugging Face `dolphinteam/OpenWhistle-CNN`.
3. Aqua-Sim NG: https://github.com/rmartin5/aqua-sim-ng
4. Thorp, W. H., "Analytic description of the low-frequency attenuation coefficient", JASA 42, 1967.
5. Stojanovic, M., Preisig, J., "Underwater acoustic communication channels: propagation models and statistical characterization", IEEE Commun. Mag., 2009.

---
## Deployment
**Streamlit Community Cloud (simplest):** push to GitHub -> https://share.streamlit.io -> New app -> select repo, branch `main`, main file `app.py` -> Deploy. `requirements.txt` is picked up automatically; no environment variables are needed. The free tier has limited RAM/CPU; use Fast mode in Results. Do not rely on the OpenWhistle download button in the cloud; commit a few small clips to `data/samples/` instead (remove `data/samples/*.wav` from `.gitignore` and check the dataset licence).
**Render / Railway:** build `pip install -r requirements.txt`; start `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.

## GitHub
```bash
git init && git add . && git commit -m "UASN virtual test-bed"
git branch -M main
git remote add origin https://github.com/<you>/UASN_Virtual_Testbed.git
git push -u origin main
```
## Troubleshooting
* `ModuleNotFoundError: config` -> run commands from the project root.
* Blank 3-D plot -> use a current Chrome/Edge/Firefox with WebGL enabled.
* Streamlit `width`/`use_container_width` warnings -> harmless; wrappers in `visualization/dashboard.py` handle both versions.
* OpenWhistle download fails -> install `requirements-optional.txt`, check internet, or just use the synthetic signal / upload a WAV.
* Slow Signal Lab -> the LMS loop is pure Python; waveforms are capped at 16 384 samples (`config.MAX_SAMPLES`).
* No route shown -> a relay is FAILED or the noise level is too high; use Routing -> Restore all nodes.
