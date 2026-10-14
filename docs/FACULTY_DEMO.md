# Faculty demonstration script (about 10 minutes)

Start: `streamlit run app.py`. Keep the sidebar open: it always shows the **source mode** (synthetic / uploaded / downloaded / recorded) and that channel and network are **simulated**.

**1. Framing (1 min).** "This is a virtual testbed for underwater acoustic monitoring and AUV communication. Nothing here is a real ocean measurement unless I upload a real recording; the sidebar says which mode we are in."

**2. Ocean Environment (2 min).** Press *Run / re-run simulation* (60 s, patrol on). Press **Play** under the 3-D plot. Point out: AUVs following waypoints (turning, changing depth), ships (diamonds) moving, fish and dolphins (illustrative), packets (white dots) travelling along the real route, link colours (green/amber/red = SNR from the link budget). Say: "Sound waves are not drawn; link colours come from the numerical model." Tick *Ships emit noise*, enable *Wenz-type noise* in the sidebar and set *Ship noise boost* to about 30 dB (our test: with Wenz noise and 0 dB boost ships have no visible effect; at 30 dB most links drop from green to amber/red), run again and watch the link colours. Then set *Inject failure on* RELAY-01 at t=30 and run: connection lines turn dashed red and routes change in the log. Hover a node for tooltip; use *Selected node details*.

**3. Acoustic Data Explorer (1 min).** Show *Dataset status* (what is and is not downloaded; failures are shown, not hidden). Load a synthetic example or upload a WAV; show waveform, spectrogram, PSD, sampling rate, playback. Mention the hydrophone-vs-microphone note.

**4. Noise Classification (1.5 min).** Classify an impulsive and a vessel example. Read out: engine = heuristic baseline, scores are relative, limitations list, "Biological" is not a species. Say: "No trained model exists yet because I have no labelled real data; the training panel will refuse unless there are enough distinct recordings."

**5. Acoustic Signal Lab (1.5 min).** Input SNR 0 dB: show Kalman -> LMS -> Wiener -> Butterworth waveforms/spectrograms and SNR table. Then 20 dB: improvement becomes negative. "Filters do not always help." Switch to *no clean reference*: SNR disappears and only estimates appear.

**6. Connection Establishment (2 min).** Handshake tab: EXPLORER-01 -> RELAY-01 *Initiate*, read the sequence diagram. Use fault injection "lose CONN_REQ x2" to show retries; "lose BEACON x99" to show FAILED then *Retry*. Send data, disconnect. Transmit tab: send "UASN-test-01" at 3000 m, show transmitted vs noisy received waveform, CRC, BER vs theory; enable multipath, then Doppler 3 m/s, and show failure. Explain passive monitoring vs digital communication.

**7. Routing and Packet Flow (1 min).** Fail the first relay: alternative route or "unreachable" with reason; routing-table log.

**8. Results (30 s).** Run extended experiments; open the relay-failure and waveform-link graphs.

**What each graph means:** filters_vs_noise = SNR gain per filter vs input SNR (synthetic signal); waveform_link_pdr = delivery vs distance per channel condition; relay_failure = PDR per explorer before/after failures; direct_vs_multihop = benefit of relays; ship_noise = receiver noise as ships pass.

**Be ready to say:** the protocol is our proposal; ship source levels are assumptions; classification is a heuristic baseline; the 3-D animation is a playback of computed states.
