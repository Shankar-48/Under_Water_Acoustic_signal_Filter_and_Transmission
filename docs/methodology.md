# Methodology and assumptions

**Provenance labels used everywhere:** *Published research* (the IEEE APSCON 2024 paper) | *Our implementation* | *Our simulation assumptions* | *Our measured results*.

## Channel model (simplified, NOT a full ocean model)
```
TL(d) = k*10*log10(d) + alpha(f)*d/1000          k=1.5 (practical spreading)
alpha(f) = Thorp: 0.11 f^2/(1+f^2) + 44 f^2/(4100+f^2) + 2.75e-4 f^2 + 0.003   [dB/km, f in kHz]
SNR = SL - TL - NL                                (dB)
BER = 0.5 * erfc( sqrt(SNR_linear) )              coherent BPSK, Eb/N0 := SNR  (validated by Exp 8)
PER = 1 - (1 - BER)^bits                          bits = 256
delay = d/1500 + bits/bit_rate (+ processing delay at denoising nodes)
```
| Assumption | Value | Comment |
|---|---|---|
| Carrier | 10 kHz | single frequency |
| Source level | 170 dB re 1 uPa @1 m | assumption |
| Ambient noise (in-band) | 112 dB re 1 uPa (UI slider 95-125) | assumption, spatially uniform |
| Spreading factor | 1.5 | practical |
| Sound speed | 1500 m/s | constant (no stratification) |
| Bit rate | 2000 bps | assumption |
| Comm. range | gateway 2500, master 2000, relay 1500, explorer 1200, sensor 400 m | modem design range, assumption |
| Processing delay | 0.05 s per denoising node | assumption |
| Energy | 0.20 / 0.05 % per TX / RX | arbitrary units |
| Layout | procedural, flat seabed at 600 m | assumption |
Not modelled: multipath, Doppler, fading, ray bending, shadow zones, MAC collisions, retransmissions (except the demo's simple ARQ).

## Waveform path
Each hop re-normalises the waveform level and adds Gaussian noise whose power gives the *link* SNR (the link budget handles absolute attenuation). Relays and the gateway denoise (decode-and-forward style); the Master only forwards (so noise accumulates over its hop). SNR is always measured against the clean source signal ("reference-based"), which is possible only because it is a simulation.

## Filter parameters (hand-chosen, not optimised)
Kalman: Q estimated from `var(diff(z)) - 2R`, RTS smoothing on. LMS: 32 taps, mu=0.05, delay 1. Wiener: window 15, noise scale 0.25 (since earlier stages already removed noise; chosen from a small sweep over SNR 15..-5 dB on the synthetic whistle, so it may not be optimal on real clips). Butterworth: order 4, cutoff = 1.15 x frequency holding 99 % of spectrum power.

## "SNR before noise"
A clean recording has no noise reference, so SNR relative to itself is infinite. We report a heuristic *baseline SNR estimate* (loudest 25 % frames vs quietest 25 %), labelled as an estimate.

## Dataset
OpenWhistle is an external public dataset used for realistic whistle waveforms. It is not claimed to be the paper's data. Without clips in `data/samples/`, a synthetic chirp is used and every screen says so.

## Reproducibility
Fixed seeds (default 42). `python -m experiments.run_experiments` regenerates `results/*.csv` and `docs/results.md`.
