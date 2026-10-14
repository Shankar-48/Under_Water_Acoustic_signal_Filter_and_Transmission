# Acoustic channel assumptions

## Link-budget model (network simulation)
`SNR = SL - TL(d) - NL`, `TL = k*10*log10(d) + alpha(f)*d/1000` (k=1.5 default, Thorp alpha at the carrier), BPSK `BER = 0.5*erfc(sqrt(Eb/N0))` with **Eb/N0 := SNR**, `PER = 1-(1-BER)^bits`, ETX = 1/(1-PER), delay = d/1500 + bits/bit-rate.
Noise: either the legacy **fixed in-band level (112 dB re 1 uPa, an assumption)** or a **Wenz-type** level `N0(fc) + 10*log10(bit rate)`.

**Finding worth knowing:** at 10-12 kHz the Wenz-type estimate (wind 5 m/s, shipping 0.5) gives about 79 dB in-band at the default 2 kbps, i.e. roughly 33 dB *below* the legacy 112 dB default. The legacy value was kept as default to preserve earlier results; it represents a very noisy environment. Switch in the sidebar to see ranges grow dramatically.

## Waveform model (`simulation/waveform_channel.py`)
Pressure in uPa; source level SL dB re 1 uPa @ 1 m sets the 1 m RMS.

| Effect | Implementation | Approximation / limitation |
|---|---|---|
| Spreading | `k*10log10(r)` | k is a user assumption (1=cylindrical, 2=spherical) |
| Absorption | Thorp, applied per frequency bin by FFT filtering | Thorp is an empirical fit, not site-specific |
| Delay | `r/c`, c = 1500 m/s, **reported analytically, not inserted as silence** (only relative multipath delays are in the waveform) | isovelocity |
| Ambient noise | colour-shaped Gaussian noise from Stojanovic's empirical turbulence+shipping+wind+thermal PSD, or flat PSD baseline | stationary Gaussian; real noise is often non-Gaussian/impulsive (snapping shrimp, ships) |
| Multipath | image method: direct, surface, bottom, 2 double-bounce paths; surface R=-0.95, bottom R=0.4 (assumed) | no refraction, no scattering, time-invariant, flat seabed |
| Doppler | uniform time compression `1+v/c` | constant radial speed; no time-varying Doppler |
| Interference | in-band BPSK / tone / noise at a chosen received level | single interferer, stationary level |

Modem: coherent BPSK, 12 kHz carrier, 1 kbps default, 48 kHz sampling, rectangular pulses, 32-bit preamble correlation for integer-sample timing and carrier phase, decision-directed phase/frequency tracking loop. **No equaliser and no timing tracking**, so multipath ISI and Doppler above ~1-2 m/s genuinely break packets (see experiments).

**Validation performed:** noise synthesis matches the requested PSD (unit test); measured BER agrees with AWGN BPSK theory (e.g. Eb/N0 = 6.2 dB: measured 2.3e-3 vs theory 2.0e-3; at 2.2 dB a ~0.5-1 dB implementation loss remains). The link-budget PER and waveform PER agree closely (see `results/ext_model_vs_waveform.csv`; one point differs at 5 km where the 60-packet waveform estimate is 0.15 vs model 0.28).
This is **not** a full ocean propagation model (no ray tracing / normal modes / Bellhop).
