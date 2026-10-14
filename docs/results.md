# Results (generated)

Generated 2026-10-07 09:19 | seed=42 | fast=False

Signal source: **SYNTHETIC whistle-like chirp (no dataset clip found in data/samples/)**

> These are OUR experimental results from OUR simulation under the assumptions in docs/methodology.md. They are not results reported in the research paper.


## Exp 1 - Clean signal

| Source                                                                |   Samples |   fs (Hz) |   Duration (s) |    RMS |   Baseline SNR estimate (dB, heuristic) |
|:----------------------------------------------------------------------|----------:|----------:|---------------:|-------:|----------------------------------------:|
| SYNTHETIC whistle-like chirp (no dataset clip found in data/samples/) |     16384 |     48000 |          0.341 | 0.4303 |                                   15.69 |

## Exp 2 - Gaussian noise

|   Target SNR (dB) |   Noise sigma |   Measured SNR after noise (dB) |
|------------------:|--------------:|--------------------------------:|
|                20 |        0.043  |                           19.97 |
|                10 |        0.1361 |                            9.97 |
|                 5 |        0.242  |                            4.97 |
|                 0 |        0.4303 |                           -0.03 |
|                -5 |        0.7652 |                           -5.03 |

## Exp 3 - Denoising (input SNR 5 dB)

| Stage               |   SNR (dB) |   Change vs noisy (dB) |
|:--------------------|-----------:|-----------------------:|
| Noisy               |       4.97 |                   0    |
| Kalman              |       6.18 |                   1.21 |
| LMS (adaptive)      |       8.3  |                   3.33 |
| Wiener              |       7.26 |                   2.28 |
| Butterworth (final) |       7.28 |                   2.31 |

## Exp 4 - Single-hop vs multi-hop (packet level)

|   Noise level (dB) | Source      | Scheme                           |   Hops |    PDR |   Min link SNR (dB) |   Mean delay (s) |
|-------------------:|:------------|:---------------------------------|-------:|-------:|--------------------:|-----------------:|
|                105 | EXPLORER-01 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                105 | EXPLORER-01 | Single-hop (range limit ignored) |      1 | 1      |                14.7 |            1.244 |
|                105 | EXPLORER-01 | Multi-hop                        |      3 | 1      |                18   |            1.958 |
|                105 | EXPLORER-02 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                105 | EXPLORER-02 | Single-hop (range limit ignored) |      1 | 1      |                14.6 |            1.247 |
|                105 | EXPLORER-02 | Multi-hop                        |      3 | 1      |                19.2 |            1.696 |
|                105 | EXPLORER-03 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                105 | EXPLORER-03 | Single-hop (range limit ignored) |      1 | 1      |                14.7 |            1.241 |
|                105 | EXPLORER-03 | Multi-hop                        |      3 | 1      |                19.2 |            1.692 |
|                112 | EXPLORER-01 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                112 | EXPLORER-01 | Single-hop (range limit ignored) |      1 | 0.9285 |                 7.7 |            1.244 |
|                112 | EXPLORER-01 | Multi-hop                        |      3 | 1      |                11   |            1.958 |
|                112 | EXPLORER-02 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                112 | EXPLORER-02 | Single-hop (range limit ignored) |      1 | 0.9175 |                 7.6 |            1.247 |
|                112 | EXPLORER-02 | Multi-hop                        |      3 | 1      |                12.2 |            1.696 |
|                112 | EXPLORER-03 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                112 | EXPLORER-03 | Single-hop (range limit ignored) |      1 | 0.9265 |                 7.7 |            1.241 |
|                112 | EXPLORER-03 | Multi-hop                        |      3 | 1      |                12.2 |            1.692 |
|                118 | EXPLORER-01 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                118 | EXPLORER-01 | Single-hop (range limit ignored) |      1 | 0      |                 1.7 |            1.244 |
|                118 | EXPLORER-01 | Multi-hop                        |      3 | 0.129  |                 5   |            1.958 |
|                118 | EXPLORER-02 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                118 | EXPLORER-02 | Single-hop (range limit ignored) |      1 | 0      |                 1.6 |            1.247 |
|                118 | EXPLORER-02 | Multi-hop                        |      3 | 0.593  |                 6.2 |            1.696 |
|                118 | EXPLORER-03 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                118 | EXPLORER-03 | Single-hop (range limit ignored) |      1 | 0      |                 1.7 |            1.241 |
|                118 | EXPLORER-03 | Multi-hop                        |      3 | 0.596  |                 6.2 |            1.692 |
|                122 | EXPLORER-01 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                122 | EXPLORER-01 | Single-hop (range limit ignored) |      1 | 0      |                -2.3 |            1.244 |
|                122 | EXPLORER-01 | Multi-hop                        |      3 | 0      |                 1   |            1.958 |
|                122 | EXPLORER-02 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                122 | EXPLORER-02 | Single-hop (range limit ignored) |      1 | 0      |                -2.4 |            1.247 |
|                122 | EXPLORER-02 | Multi-hop                        |      3 | 0      |                 2.2 |            1.696 |
|                122 | EXPLORER-03 | Single-hop (range-limited)       |      0 | 0      |               nan   |          nan     |
|                122 | EXPLORER-03 | Single-hop (range limit ignored) |      1 | 0      |                -2.3 |            1.241 |
|                122 | EXPLORER-03 | Multi-hop                        |      3 | 0      |                 2.2 |            1.692 |

## Exp 4b - Waveform SNR at gateway

|   Noise level (dB) | Relay/gateway denoising   |   Mean SNR at gateway (dB) |   Std (dB) |   Trials |
|-------------------:|:--------------------------|---------------------------:|-----------:|---------:|
|                112 | OFF                       |                       8.27 |       0    |        3 |
|                112 | ON                        |                       9.99 |       0.02 |        3 |
|                118 | OFF                       |                       1.82 |       0.01 |        3 |
|                118 | ON                        |                       6.06 |       0.04 |        3 |
|                122 | OFF                       |                      -2.98 |       0.02 |        3 |
|                122 | ON                        |                       2.74 |       0.09 |        3 |

## Exp 5 - Link failure and route recovery

| Failed node   | Source      | Route before                               | Route after                                | Recovered   |   PDR before |   PDR after |
|:--------------|:------------|:-------------------------------------------|:-------------------------------------------|:------------|-------------:|------------:|
| RELAY-01      | EXPLORER-01 | EXPLORER-01 > RELAY-01 > MASTER-01 > GW-01 | EXPLORER-01 > RELAY-02 > MASTER-01 > GW-01 | True        |            1 |           1 |
| RELAY-01      | EXPLORER-02 | EXPLORER-02 > RELAY-01 > MASTER-01 > GW-01 | NO ROUTE (unreachable)                     | False       |            1 |           0 |
| RELAY-01      | EXPLORER-03 | EXPLORER-03 > RELAY-02 > MASTER-01 > GW-01 | EXPLORER-03 > RELAY-02 > MASTER-01 > GW-01 | True        |            1 |           1 |
| RELAY-02      | EXPLORER-01 | EXPLORER-01 > RELAY-01 > MASTER-01 > GW-01 | EXPLORER-01 > RELAY-01 > MASTER-01 > GW-01 | True        |            1 |           1 |
| RELAY-02      | EXPLORER-02 | EXPLORER-02 > RELAY-01 > MASTER-01 > GW-01 | EXPLORER-02 > RELAY-01 > MASTER-01 > GW-01 | True        |            1 |           1 |
| RELAY-02      | EXPLORER-03 | EXPLORER-03 > RELAY-02 > MASTER-01 > GW-01 | NO ROUTE (unreachable)                     | False       |            1 |           0 |

## Exp 6 - Noise levels (denoising chain)

| Noise level   |   Input SNR (dB) |   Baseline clip SNR (est.) |   SNR after noise |   After Kalman |   After LMS |   After Wiener |   Final (Butterworth) |   Improvement (dB) |   Std of final (dB) |   Trials |
|:--------------|-----------------:|---------------------------:|------------------:|---------------:|------------:|---------------:|----------------------:|-------------------:|--------------------:|---------:|
| Low           |               15 |                       15.7 |             14.99 |          15.19 |       15.08 |          14.96 |                 14.97 |              -0.02 |                0.05 |        5 |
| Medium        |                5 |                       15.7 |              4.99 |           6.26 |        8.42 |           7.41 |                  7.43 |               2.44 |                0.09 |        5 |
| High          |               -5 |                       15.7 |             -5.01 |          -0.48 |        0.1  |          -0.36 |                 -0.4  |               4.61 |                0.02 |        5 |

## Exp 7 - Communication performance

|   Noise level (dB) | Source      | Route                                         |   Hops |    PDR |   Packet loss |   Min link SNR (dB) |   End-to-end delay (s) |   Success rate (%) |
|-------------------:|:------------|:----------------------------------------------|-------:|-------:|--------------:|--------------------:|-----------------------:|-------------------:|
|                105 | EXPLORER-01 | EXPLORER-01 -> RELAY-01 -> MASTER-01 -> GW-01 |      3 | 1      |        0      |                18   |                  1.958 |             100    |
|                105 | EXPLORER-02 | EXPLORER-02 -> RELAY-01 -> MASTER-01 -> GW-01 |      3 | 1      |        0      |                19.2 |                  1.696 |             100    |
|                105 | EXPLORER-03 | EXPLORER-03 -> RELAY-02 -> MASTER-01 -> GW-01 |      3 | 1      |        0      |                19.2 |                  1.692 |             100    |
|                112 | EXPLORER-01 | EXPLORER-01 -> RELAY-01 -> MASTER-01 -> GW-01 |      3 | 1      |        0      |                11   |                  1.958 |             100    |
|                112 | EXPLORER-02 | EXPLORER-02 -> RELAY-01 -> MASTER-01 -> GW-01 |      3 | 1      |        0      |                12.2 |                  1.696 |             100    |
|                112 | EXPLORER-03 | EXPLORER-03 -> RELAY-02 -> MASTER-01 -> GW-01 |      3 | 1      |        0      |                12.2 |                  1.692 |             100    |
|                118 | EXPLORER-01 | EXPLORER-01 -> RELAY-01 -> MASTER-01 -> GW-01 |      3 | 0.1325 |        0.8675 |                 5   |                  1.958 |              13.25 |
|                118 | EXPLORER-02 | EXPLORER-02 -> RELAY-01 -> MASTER-01 -> GW-01 |      3 | 0.589  |        0.411  |                 6.2 |                  1.696 |              58.9  |
|                118 | EXPLORER-03 | EXPLORER-03 -> RELAY-02 -> MASTER-01 -> GW-01 |      3 | 0.595  |        0.405  |                 6.2 |                  1.692 |              59.5  |

## Exp 8 - BER model validation

|   SNR (dB) |   Measured BER (BPSK sim) |   Theory 0.5*erfc(sqrt(SNR)) |
|-----------:|--------------------------:|-----------------------------:|
|          0 |                  0.07924  |                     0.07865  |
|          2 |                  0.03777  |                     0.037506 |
|          4 |                  0.012705 |                     0.012501 |
|          6 |                  0.00248  |                     0.002388 |
|          8 |                  0.00017  |                     0.000191 |
