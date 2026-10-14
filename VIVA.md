# Viva preparation

**What is a UASN?** A network of underwater nodes (static sensors, AUVs, gateways) that sense the ocean and send data by sound to a surface station for continuous, real-time monitoring.

**Why acoustic communication underwater?** Sound travels kilometres in water with moderate loss; radio and light are absorbed within metres (light also needs clear water).

**Why not ordinary Wi-Fi?** 2.4/5 GHz radio is absorbed by conductive seawater within centimetres to a few metres.

**What is an AUV?** Autonomous Underwater Vehicle: an unmanned, self-navigating submarine robot. In our project it is a software node with position, role, battery and counters.

**What is a hydrophone?** An underwater microphone that converts pressure waves to an electrical signal (our `VirtualHydrophone` adds channel noise to the received waveform).

**What is a transducer?** A device converting electrical energy to sound (transmit) and back; ours (`VirtualTransducer`) creates the simulated acoustic transmission.

**What is an acoustic modem?** Modulates data onto sound and demodulates at the receiver. Ours models BPSK to compute bit-error rate, validated in Experiment 8.

**What is multi-hop communication?** Data hops through intermediate nodes instead of one long link: Explorer -> Relay -> Master -> Gateway.

**Why relay nodes?** Loss grows with distance; two shorter links have higher SNR each than one long link, and relays extend coverage beyond a single node's range.

**What is Gaussian noise / why add it?** Random noise with a bell-shaped amplitude distribution, `n ~ N(0, sigma^2)`; it models ambient and electronic noise and lets us test denoising with a known ground truth.

**What is SNR?** Signal power over noise power in dB. We use `10 log10(sum x^2 / sum (x - x_hat)^2)` against the clean reference.

**What does the Kalman filter do?** Combines a simple model ("signal changes slowly") with each noisy sample, weighting by the gain `K = P/(P+R)`, giving a smoothed estimate.

**What does LMS do?** An adaptive filter that updates its weights each sample to minimise prediction error; used as a line enhancer, it learns to predict the narrowband whistle but not the random noise.

**What does the Wiener filter do?** Minimum-mean-square-error filter: keeps parts where local variance is above the noise variance and shrinks noise-like parts.

**Why Butterworth?** Maximally flat passband (no ripple); we use it low-pass to cut noise above the whistle band.

**Why use real acoustic data?** Real whistles have realistic time-frequency structure; it makes the denoising test meaningful. (OpenWhistle is external, not the paper's data.)

**What is packet loss?** A packet not received correctly, here a random draw with probability PER from the BER and packet length.

**What is propagation delay?** `d / 1500 m/s`; plus transmission time `bits/bit_rate` and processing delay. Acoustic delay is ~200,000x radio's.

**How does routing work?** Dijkstra shortest path where link cost is ETX = 1/(1-PER), among available, in-range links.

**What happens if a relay fails?** Its links vanish from the graph; Dijkstra finds another path (Explorer-01 via Relay-02). If a node has no other relay in range (Explorer-02) it becomes unreachable - we report that.

**Simulation vs real test-bed?** We model a simplified link budget; we omit multipath, Doppler, ray bending, MAC collisions and hardware; results are not sea-trial data.

**Why suitable for engineering applications?** It integrates networking, signal processing and simulation, supports reproducible what-if studies (noise, failures) before costly sea trials.

**Likely trap questions.** *"Did you reproduce the paper's results?"* No - we reproduce concepts; results are ours. *"Why did filtering not improve at 15 dB?"* Smoothing also removes signal detail; benefit is regime-dependent (Exp 6). *"Is the dataset from the paper?"* No, it is the external OpenWhistle dataset. *"Is SNR measurable in the real ocean?"* Not against a clean reference; real systems estimate it from noise-only intervals.
