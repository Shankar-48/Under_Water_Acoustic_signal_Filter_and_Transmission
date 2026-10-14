# Algorithms

## 1. Main multi-hop acoustic communication algorithm
```
Oceanographic sensor -> Explorer AUV --acoustic--> [channel + Gaussian noise] --> Hydrophone @ Relay AUV
   -> signal processing (Kalman -> LMS -> Wiener -> Butterworth) -> Relay re-transmits --acoustic--> Master/Sink AUV
   -> Master forwards --acoustic--> Surface Gateway (denoise, recover signal) -> Base station
```
* **Input:** clean waveform + simulated sensor reading. **Processing:** per-hop link budget, noise, packet-loss draw, denoise at relay/gateway.
* **Output:** recovered waveform, per-hop SNR, delay, delivered/lost flag. **Why:** acoustic range is limited and noisy; shorter hops have higher SNR.
* Architecture rule: only the Master AUV hands data to the surface gateway; relays and master are the only forwarding nodes.

## 2. Signal-processing algorithm
| Stage | Simple idea | Technical | Input -> Output |
|---|---|---|---|
| Gaussian noise | Add random hiss | `y = x + n`, `n~N(0,sigma^2)`, sigma from target SNR | clean -> noisy |
| Kalman (1-D) | Trust the model more than one noisy sample | random-walk state, gain `K=P/(P+R)`, optional RTS smoothing | noisy -> smoother |
| LMS (NLMS ALE) | A filter that learns to predict the whistle | `w += mu*e*u/(eps+u.u)`, delayed input | -> predicted tonal part |
| Wiener | Keep strong parts, flatten noise-like parts | local mean/variance, shrink factor `1 - sigma_n^2/sigma^2` | -> reduced noise |
| Butterworth | Remove everything above the signal band | 4th-order low-pass, zero-phase | -> final |
| SNR | Signal-to-error power ratio | `10 log10( sum x^2 / sum (x - x_hat)^2 )` | -> number in dB |

The receiver estimates noise variance from a noise-only listening interval (hydrophone `measure_noise_floor`).
Honest note: the stages are cascaded as the project brief specifies; the cascade helps at low SNR and can slightly hurt at high SNR (see `docs/results.md`).

## 3. Routing algorithm (best-link, Dijkstra on ETX)
1. Build directed links `u -> v` if `distance <= range(u)`, both nodes ACTIVE, and link SNR >= minimum.
2. Link cost = ETX = `1/(1-PER)` (expected transmissions for one successful hop; >= 1, so fewer hops win ties).
3. Dijkstra finds the minimum total ETX from source to gateway. Sensors/gateway never forward.
4. Alternative route: re-run excluding each intermediate node of the primary route, keep the best.
5. If a relay fails, rebuild links without it -> automatic route recovery (Experiment 5). If no alternative exists the source is unreachable (shown honestly).
