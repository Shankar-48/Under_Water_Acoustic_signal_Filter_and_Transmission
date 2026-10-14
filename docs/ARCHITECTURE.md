# System architecture

```mermaid
flowchart LR
  subgraph UI[Streamlit app.py + ui/]
    P1[Ocean Environment] --- P2[Data Explorer] --- P3[Noise Classification] --- P4[Signal Lab]
    P5[Network / Routing] --- P6[Connection Establishment] --- P7[Results] --- P8[Faculty Demo]
  end
  subgraph AUD[audio/ + classification/]
    IO[io.py WAV load/validate/playback] --> FE[features.py]
    DS[datasets.py manifest + registry] --> IO
    SY[synth.py labelled SYNTHETIC signals] --> IO
    FE --> BL[baseline.py heuristic]
    FE --> TR[trained.py grouped-split RF]
  end
  subgraph SIG[signal_processing/]
    N[noise] --> K[Kalman] --> L[LMS] --> W[Wiener] --> B[Butterworth]
  end
  subgraph COM[communication/ + simulation/waveform_channel.py]
    FR[framing CRC16] --> BP[BPSK modem + phase tracking] --> WC[Waveform channel: spreading, Thorp, Wenz noise, multipath, Doppler, interference]
  end
  subgraph NET[simulation/]
    ENV[environment.py] --> RT[routing.py Dijkstra+ETX]
    ENV --> HS[handshake.py state machine]
    ENV --> SC[scene.py ships, fish, dolphins]
    ENV --> CH[acoustic_channel.py link budget]
    RUN[run.py snapshots]
  end
  UI --> AUD
  UI --> SIG
  UI --> COM
  UI --> NET
  NET --> VIS[visualization/ ocean_3d, sequence, audio_plots]
  EXP[experiments/extended.py] --> COM & SIG & NET
```

Two channel models coexist on purpose:

| Model | Where | Used for | Detail |
|---|---|---|---|
| Link budget (`acoustic_channel.py`) | network simulation | per-hop SNR, PER, ETX, routing | SNR = SL - TL - NL; Eb/N0 := SNR (valid when noise bandwidth = bit rate) |
| Waveform channel (`waveform_channel.py`) | Connection Establishment page, experiments | actual BPSK waveforms, BER/PER | measured at sample level; validated against AWGN BPSK theory |

`experiments/extended.py::exp_model_vs_waveform` compares them.

## Connection-establishment sequence (proposed simulator protocol)

```mermaid
sequenceDiagram
  participant A as Initiator (e.g. EXPLORER-01)
  participant B as Peer (e.g. RELAY-01)
  A->>B: 1 BEACON (discovery)
  Note over B: 2 NEIGHBOUR_DETECTED
  A->>B: 3 LQ_PROBE
  B->>A: 4 LQ_REPORT (SNR, PER, ETX)
  Note over A: reject if SNR < threshold or ETX > max
  A->>B: 5 CONN_REQ
  B->>A: 6 CONN_RESP (accept/reject)
  A->>B: 7 LINK_ACK
  Note over A,B: ESTABLISHED
  A->>B: 8 DATA
  Note over B: 9 CRC check
  B->>A: 10 DATA_ACK / DATA_NACK
  Note over A,B: no ACK after retries -> LINK_TIMEOUT -> DOWN -> retry()
```

Every arrow takes propagation delay (distance / 1500 m/s) plus transmission time and may be lost with the packet-error probability of its frame size.
