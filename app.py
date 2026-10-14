"""Virtual Underwater Acoustic Sensor Network test-bed - Streamlit application."""
import math, time
import numpy as np
import pandas as pd
import streamlit as st

from config.config import ChannelConfig, GATEWAY_ID, EXPLORER, RELAY, SENSOR, DEFAULT_SEED
from simulation.environment import Environment
from simulation.routing import build_links
from signal_processing.dataset import (default_signal, synthetic_whistle, load_wav_bytes, list_local_samples,
                                       load_local_sample, fetch_openwhistle_samples)
from signal_processing.noise import add_gaussian_noise
from signal_processing.pipeline import denoise_pipeline, STAGES
from signal_processing.snr import snr_db
from experiments.experiments import run_all
from visualization.network_3d import build_network_figure
from visualization.waveforms import plot_stage_waveforms, plot_overlay
from visualization.spectrogram import plot_spectrograms
from visualization.dashboard import inject_css, note, show_plot, show_df, kpis
from ui.common import ensure_clip, set_clip, mode_banner, dashboard_summary
from ui import pages_new as pn
import time as _time
from audio.io import playback_bytes
from signal_processing.snr import intrinsic_snr_estimate
from signal_processing.kalman import kalman_filter
from signal_processing.adaptive_filter import lms_filter
from signal_processing.wiener import wiener_filter
from signal_processing.butterworth import butterworth_lowpass, auto_cutoff_hz

st.set_page_config(page_title="UASN Virtual Test-bed", layout="wide", page_icon=None)
inject_css()
PAGES = ["Dashboard", "Ocean Environment", "Acoustic Data Explorer", "Noise Classification", "Acoustic Signal Lab", "Network Simulation",
         "Connection Establishment", "Node Details", "Routing and Packet Flow", "Results and Experiments", "Faculty Demo Mode",
         "About and Research Comparison"]


# ------------------------------------------------------------------ state
def new_env():
    s = st.session_state
    cfg = s.get("cfg") or ChannelConfig()
    s.cfg = cfg
    s.env = Environment(cfg, seed=s.get("seed", DEFAULT_SEED), n_explorers=s.get("n_exp", 3),
                        n_relays=s.get("n_rel", 2), n_sensors=s.get("n_sen", 4))
    s.patrol_on = False


def init():
    s = st.session_state
    if "cfg" not in s: s.cfg = ChannelConfig()
    if "env" not in s: new_env()
    ensure_clip()


def sidebar():
    s = st.session_state
    st.sidebar.title("UASN Test-bed")
    st.sidebar.caption("Virtual underwater acoustic network - software simulation")
    page = st.sidebar.radio("Navigation", PAGES, label_visibility="collapsed")
    with st.sidebar.expander("Network setup"):
        n_exp = st.number_input("Explorer AUVs", 1, 5, s.get("n_exp", 3))
        n_rel = st.number_input("Relay AUVs", 1, 4, s.get("n_rel", 2))
        n_sen = st.number_input("Sensor nodes", 0, 8, s.get("n_sen", 4))
        seed = st.number_input("Random seed", 0, 9999, s.get("seed", DEFAULT_SEED))
        if st.button("Rebuild network"):
            s.n_exp, s.n_rel, s.n_sen, s.seed = int(n_exp), int(n_rel), int(n_sen), int(seed)
            new_env(); st.rerun()
    with st.sidebar.expander("Acoustic channel"):
        c = s.cfg
        c.noise_model = "wenz" if st.checkbox("Wenz-type ambient noise (instead of fixed in-band level)", c.noise_model == "wenz",
                                              help="Fixed legacy level (default) is ~36 dB above a calm-sea empirical estimate; see docs/CHANNEL.md") else "fixed"
        if c.noise_model == "wenz":
            c.wind_mps = st.slider("Wind speed (m/s)", 0.0, 20.0, float(c.wind_mps), 0.5); c.shipping = st.slider("Shipping factor", 0.0, 1.0, float(c.shipping), 0.1)
        else:
            c.noise_level_db = st.slider("Ambient noise level (dB re 1 uPa, in-band)", 95.0, 125.0, float(c.noise_level_db), 0.5)
        c.source_level_db = st.slider("Source level (dB re 1 uPa @ 1 m)", 150.0, 190.0, float(c.source_level_db), 1.0)
        on = st.checkbox("Add interference", value=c.interference_db > 0)
        c.interference_db = st.slider("Interference level (dB)", 90.0, 130.0, max(90.0, float(c.interference_db or 110.0))) if on else 0.0
    st.sidebar.caption("Choose the acoustic source on the 'Acoustic Data Explorer' page.")
    st.sidebar.caption(f"Signal: {s.signal[2]}")
    mode_banner()
    return page


# ------------------------------------------------------------------ pages
def page_dashboard(env):
    st.header("Dashboard")
    dashboard_summary(env)
    note("All node positions, sensor values, noise and network statistics are <b>simulated</b>. Only the waveform may come from a real public dataset (see sidebar).")
    pk = env.packets; dl = [p for p in pk if p.status == "DELIVERED"]; lost = [p for p in pk if p.status == "LOST"]
    n_links = sum(len(v) for v in build_links(env.nodes, env.channel).values())
    avg = np.mean([p.signal_snr_db for p in dl]) if dl else float("nan")
    kpis([("AUVs", len([n for n in env.nodes.values() if n.node_type != SENSOR and n.node_type != 'GATEWAY'])),
          ("Sensor nodes", len(env.ids(SENSOR))), ("Active links", n_links), ("Sim. time (s)", f"{env.time:.0f}")])
    kpis([("Packets created", len(pk)), ("Delivered (end-to-end)", len(dl)), ("Lost", len(lost)),
          ("Packet loss", f"{100 * len(lost) / len(pk):.1f}%" if pk else "-"),
          ("Avg final SNR (dB)", "-" if math.isnan(avg) else f"{avg:.1f}")])
    kpis([("Hop transmissions", sum(n.packets_sent for n in env.nodes.values())),
          ("Hop receptions", sum(n.packets_received for n in env.nodes.values())),
          ("Ambient noise (dB)", f"{env.channel.noise_db():.1f}")])
    st.subheader("Nodes"); show_df(env.node_table())
    st.subheader("Event log")
    show_df(pd.DataFrame(env.events[::-1]) if env.events else pd.DataFrame({"event": ["No events yet. Send a packet in 'Network Simulation'."]}))


def page_network(env):
    st.header("Network Simulation")
    s = st.session_state
    c1, c2, c3, c4 = st.columns([2, 1.2, 1.4, 1.4])
    srcs = env.ids(EXPLORER) + env.ids(SENSOR)
    src = c1.selectbox("Source node", srcs)
    process = c2.checkbox("Relay denoising", True)
    force = c3.checkbox("Ignore random loss", False, help="Isolates signal quality from random packet loss.")
    sel = c4.selectbox("Show range of", ["(none)"] + list(env.nodes))
    failed_opts = env.ids(RELAY) + env.ids("MASTER")
    failed = st.multiselect("Failed nodes (simulated outage)", failed_opts, default=[n for n in failed_opts if env.nodes[n].state == "FAILED"])
    for n in failed_opts:
        want = "FAILED" if n in failed else "ACTIVE"
        if env.nodes[n].state != want: env.set_state(n, want)
    b1, b2, _ = st.columns([1, 1, 4])
    if b1.button("Send packet", type="primary"):
        x, fs, _ = s.signal
        s.last = env.transmit(src, x, fs, process=process, ignore_loss=force)
    if b2.button("Advance 30 s"):
        env.step(30.0)
    res = s.get("last") or env.last_result
    route = env.route(src)
    show_plot(build_network_figure(env, route=route, alt_route=env.alt_route(src) if route else None,
                                   selected=None if sel == "(none)" else sel, animate=route is not None), key="net3d")
    st.caption("Drag to rotate, scroll to zoom, hover a node for details. Use 'Send packet (animate)' on the plot to replay the hop-by-hop transmission.")
    if route is None:
        st.warning("No route from this source to the gateway (relays failed or out of range).")
    if res:
        pk = res.packet
        st.subheader(f"Packet {pk.packet_id} - {pk.status}")
        a, b = st.columns(2)
        with a:
            st.json({**pk.to_dict(), "signal_snr_db": None if math.isnan(pk.signal_snr_db) else round(pk.signal_snr_db, 2),
                     "noise_level_db": round(pk.noise_level_db, 1)})
        with b:
            show_df(pd.DataFrame([{"Hop": f"{h.tx} -> {h.rx}", "Dist (m)": round(h.distance_m), "Link SNR (dB)": round(h.link_snr_db, 1),
                                   "PER": f"{h.per:.2e}", "Delivered/ACK": "yes" if h.delivered else "NO", "SNR rx (dB)": None if math.isnan(h.snr_rx_db) else round(h.snr_rx_db, 2),
                                   "SNR after proc (dB)": None if math.isnan(h.snr_out_db) else round(h.snr_out_db, 2), "Denoised": h.processed}
                                  for h in res.hops]))
            st.caption(f"End-to-end delay (propagation + transmission + processing): {res.delay_s:.3f} s")


def _pipeline(x, fs, snr_in, seed, smooth, taps, mu, cutoff):
    y, _, sigma = add_gaussian_noise(x, snr_in, np.random.default_rng(seed))
    return y, sigma, denoise_pipeline(y, sigma ** 2, fs, cutoff_hz=cutoff, kalman_smooth=smooth, lms_taps=taps, lms_mu=mu)


def page_lab():
    st.header("Acoustic Signal Lab")
    s = st.session_state
    x, fs, lab = s.signal
    clip = s.clip
    ref_mode = st.radio("Reference mode", ["Treat the loaded signal as the clean reference and add simulated noise (SNR is exact)",
                                           "Process the loaded signal as-is (no clean reference: estimates only)"])
    with_ref = ref_mode.startswith("Treat")
    note(f"Signal source: <b>{lab}</b>. " + ("Noise is our simulated Gaussian noise; SNR is computed against the loaded signal, which is only a true clean reference if it is clean "
                                             "(true for synthetic signals; an approximation for real recordings that already contain noise)."
                                             if with_ref else "No ground truth exists, so SNR is NOT shown. Shown instead: heuristic SNR estimates (loud vs quiet frames), noise-floor and flatness changes."))
    c = st.columns(5)
    snr_in = c[0].slider("Input SNR (dB)", -10.0, 25.0, 5.0, 0.5) if with_ref else None
    seed = c[1].number_input("Seed", 0, 9999, 42)
    smooth = c[2].checkbox("Kalman RTS smoothing", True)
    taps = c[3].select_slider("LMS taps", [8, 16, 32, 64], 32)
    manual = c[4].checkbox("Manual cutoff")
    c = st.columns(3)
    mu = c[0].select_slider("LMS step size mu", [0.01, 0.02, 0.05, 0.1, 0.2], 0.05)
    wwin = c[1].select_slider("Wiener window", [5, 9, 15, 25, 41], 15)
    order = c[2].select_slider("Butterworth order", [2, 4, 6, 8], 4)
    cutoff = st.slider("Butterworth cutoff (Hz)", 100, int(fs * 0.45), int(fs * 0.25)) if manual else None
    if clip.duration_s * clip.fs > len(x) + 10:
        st.caption(f"Using {len(x)} samples ({len(x) / fs:.2f} s) of a {clip.duration_s:.2f} s recording. Choose another segment on the Data Explorer page.")
    try:
        if with_ref:
            y, _, sigma = add_gaussian_noise(x, snr_in, np.random.default_rng(int(seed)))
            nv = sigma ** 2
        else:
            y = x
            nv = float(np.var(x[: max(256, len(x) // 20)])) * 0.1          # crude noise-variance guess from the first 5% (labelled estimate)
        t0 = _time.perf_counter(); out = denoise_pipeline(y, nv, fs, cutoff_hz=cutoff, kalman_smooth=smooth, lms_taps=taps, lms_mu=mu, wiener_window=wwin, order=order); t_all = _time.perf_counter() - t0
    except Exception as e:
        st.error(f"Pipeline failed: {e}"); return
    timing = {}
    for nm, fn in (("Kalman", lambda: kalman_filter(y, nv, smooth=smooth)), ("LMS (adaptive)", lambda: lms_filter(out["Kalman"], taps=taps, mu=mu)),
                   ("Wiener", lambda: wiener_filter(out["LMS (adaptive)"], nv * 0.25, window=wwin)), ("Butterworth (final)", lambda: butterworth_lowpass(out["Wiener"], fs, out["_cutoff_hz"], order))):
        t0 = _time.perf_counter(); fn(); timing[nm] = (_time.perf_counter() - t0) * 1000
    if with_ref:
        snrs = {"Original": float("inf"), **{k: snr_db(x, out[k]) for k in STAGES}}
        s.snr_in, s.snr_out = snrs["Noisy"], snrs["Butterworth (final)"]
        kpis([("SNR after noise", f"{snrs['Noisy']:.2f} dB"), ("Final SNR", f"{snrs['Butterworth (final)']:.2f} dB"),
              ("SNR improvement = out - in", f"{snrs['Butterworth (final)'] - snrs['Noisy']:+.2f} dB"), ("Pipeline time", f"{t_all * 1000:.0f} ms")])
        rows = [{"Stage": k, "SNR (dB)": round(v, 2), "Change vs noisy (dB)": round(v - snrs["Noisy"], 2), "Time (ms)": round(timing.get(k, 0.0), 1),
                 "MSE vs ref": float(np.mean((x - out[k]) ** 2)), "Correlation": float(np.corrcoef(x, out[k])[0, 1])} for k, v in snrs.items() if k != "Original"]
    else:
        snrs = None
        est = {k: intrinsic_snr_estimate(out[k]) for k in STAGES}
        kpis([("Heuristic SNR estimate, input", f"{est['Noisy']:.1f} dB"), ("Heuristic SNR estimate, output", f"{est['Butterworth (final)']:.1f} dB"), ("Pipeline time", f"{t_all * 1000:.0f} ms")])
        rows = [{"Stage": k, "Heuristic SNR estimate (dB)": round(est[k], 2), "RMS": round(float(np.sqrt(np.mean(out[k] ** 2))), 4), "Time (ms)": round(timing.get(k, 0.0), 1)} for k in STAGES]
        st.warning("Estimates only: there is no clean reference, so these numbers are not ground-truth SNR.")
    t1, t2, t3, t4 = st.tabs(["Waveforms", "Spectrograms", "Metrics and equation", "Audio playback"])
    with t1:
        sig = {"Original": x, **{k: out[k] for k in STAGES}} if with_ref else {k: out[k] for k in STAGES}
        show_plot(plot_stage_waveforms(sig, fs, snrs=snrs), key="wave")
        show_plot(plot_overlay(x, out["Butterworth (final)"], fs, "Input signal", "Denoised (final)"), key="ovl")
    with t2:
        show_plot(plot_spectrograms({"Input": x, "Noisy": out["Noisy"], "Denoised": out["Butterworth (final)"]}, fs), key="spec")
    with t3:
        show_df(pd.DataFrame(rows))
        st.latex(r"\mathrm{SNR_{dB}} = 10\log_{10}\frac{\sum_n x[n]^2}{\sum_n (x[n]-\hat{x}[n])^2}\qquad \Delta\mathrm{SNR}=\mathrm{SNR_{out}}-\mathrm{SNR_{in}}")
        st.caption("Filters do not always improve quality: at high input SNR the cascade can lower SNR (see Experiments). Role of each filter: Kalman - state-space smoothing; LMS - adaptive line enhancer for narrowband content; "
                   "Wiener - local adaptive noise reduction; Butterworth - zero-phase low-pass.")
    with t4:
        for nm, sig_ in (("Input", x), ("Noisy", out["Noisy"]), ("Denoised", out["Butterworth (final)"])):
            wav, nt = playback_bytes(sig_, fs); st.write(nm); st.audio(wav, format="audio/wav")
        st.caption("Playback is peak-normalised; very short or very high-rate clips may sound unusual.")


def page_node(env):
    st.header("Node Details")
    nid = st.selectbox("Select node", list(env.nodes)); n = env.nodes[nid]
    kpis([("Role", n.node_type), ("Depth (m)", f"{n.depth:.0f}"), ("Battery", f"{n.battery:.2f}%"), ("State", n.state)])
    kpis([("Packets sent", n.packets_sent), ("Packets received", n.packets_received), ("Packets lost", n.packets_lost),
          ("Last SNR (dB)", "-" if math.isnan(n.last_snr_db) else f"{n.last_snr_db:.1f}")])
    st.write(f"**Coordinates (m):** x={n.position[0]:.0f}, y={n.position[1]:.0f}, z={n.position[2]:.0f} &nbsp; | &nbsp; **Comm. range:** {n.comm_range:.0f} m &nbsp; | &nbsp; **Activity:** {n.activity}")
    r = env.route(nid) if n.node_type not in ("GATEWAY",) else None
    st.write("**Current route:** " + (" -> ".join(r.path) if r else "n/a"))
    if n.sensors:
        st.subheader("Sensor readings (SIMULATED)"); st.json(n.read_sensors())
    show_plot(build_network_figure(env, route=r, selected=nid, show_links=False), key="nd3d")


def page_routing(env):
    st.header("Routing - best-link multi-hop (Dijkstra on ETX)")
    src = st.selectbox("Source", env.ids(EXPLORER) + env.ids(SENSOR))
    r, alt = env.route(src), env.alt_route(src)
    if r is None:
        st.error("No route available."); return
    kpis([("Hop count", r.hops), ("Route cost (sum ETX)", f"{r.cost:.3f}"), ("Min link SNR (dB)", f"{min(l['snr_db'] for l in r.links):.1f}")])
    st.write("**Primary route:** " + " -> ".join(r.path))
    show_df(pd.DataFrame([{"Link": f"{l['tx']} -> {l['rx']}", "Distance (m)": round(l["distance_m"]), "SNR (dB)": round(l["snr_db"], 1),
                           "PER": f"{l['per']:.2e}", "ETX": round(l["etx"], 4), "Delay (s)": round(l["delay_s"], 3)} for l in r.links]))
    st.write("**Alternative route (avoids one intermediate node):** " + (" -> ".join(alt.path) + f"  (cost {alt.cost:.3f})" if alt else "none available - single point of failure"))
    mids = r.path[1:-1]
    if mids:
        c1, c2 = st.columns(2)
        if c1.button(f"Fail {mids[0]} and re-route"):
            env.set_state(mids[0], "FAILED"); st.rerun()
        if c2.button("Restore all nodes"):
            for n in env.nodes: env.set_state(n, "ACTIVE")
            st.rerun()
    show_plot(build_network_figure(env, route=r, alt_route=alt), key="rt3d")


@st.cache_data(show_spinner="Running experiments (about 30-60 s)...")
def cached_results(x, fs, label, seed, fast):
    return run_all(x, fs, label, seed, fast)


def page_results():
    st.header("Results and Experiments")
    page_results_ext()
    st.subheader("Original experiments 1-8")
    note("Everything here is computed live by our code under our simulation assumptions. These are <b>our experimental results</b>, not figures from the research paper.")
    c1, c2 = st.columns(2)
    fast = c1.checkbox("Fast mode (fewer Monte-Carlo trials)", True); seed = c2.number_input("Seed", 0, 9999, 42, key="rseed")
    if st.button("Run experiments", type="primary"):
        x, fs, lab = st.session_state.signal
        st.session_state.results = cached_results(x, fs, lab, int(seed), fast)
    res = st.session_state.get("results")
    if not res:
        st.info("Press 'Run experiments' to generate Experiments 1-8."); return
    import plotly.express as px
    e6, e7, e4 = res["Exp 6 - Noise levels (denoising chain)"], res["Exp 7 - Communication performance"], res["Exp 4 - Single-hop vs multi-hop (packet level)"]
    long = e6.melt(id_vars="Noise level", value_vars=["SNR after noise", "After Kalman", "After LMS", "After Wiener", "Final (Butterworth)"], var_name="Stage", value_name="SNR (dB)")
    show_plot(px.bar(long, x="Noise level", y="SNR (dB)", color="Stage", barmode="group", template="plotly_dark", title="SNR after each stage"), key="r1")
    g = e4.groupby(["Noise level (dB)", "Scheme"], as_index=False)["PDR"].mean()
    show_plot(px.line(g, x="Noise level (dB)", y="PDR", color="Scheme", markers=True, template="plotly_dark", title="Mean packet delivery ratio vs ambient noise"), key="r2")
    show_plot(px.bar(e7, x="Source", y="PDR", color="Noise level (dB)", barmode="group", template="plotly_dark", title="Packet delivery ratio per explorer"), key="r3")
    for name, df in res.items():
        with st.expander(name, expanded=name.startswith(("Exp 3", "Exp 5", "Exp 6"))):
            show_df(df)
    csv = "\n\n".join(f"# {k}\n{v.to_csv(index=False)}" for k, v in res.items())
    st.download_button("Download all results (CSV text)", csv, "uasn_results.csv", "text/csv")


def page_results_ext():
    import glob, os
    from pathlib import Path
    from experiments.extended import run_extended, OUT
    st.subheader("Extended experiments (CSV + graphs)")
    st.caption("Waveform-level link, filters alone vs pipeline, source categories, relay failure, direct vs multi-hop, ship noise. Every row carries a data_mode column (SYNTHETIC / SIMULATED).")
    c = st.columns(3); fast = c[0].checkbox("Fast mode", True, key="extfast"); seed = c[1].number_input("Seed", 0, 9999, 42, key="extseed")
    if c[2].button("Run extended experiments"):
        with st.spinner("Running (about 15-60 s)..."):
            try:
                st.session_state.ext = run_extended(OUT, fast, int(seed), log=lambda m: None); st.success("Finished. CSVs and figures written to results/ and results/figures/.")
            except Exception as e:
                st.error(f"Experiment failed: {e}")
    for f in sorted(Path(OUT / "figures").glob("*.png")): st.image(str(f), caption=f.name)
    for f in sorted(Path(OUT).glob("ext_*.csv")):
        with st.expander(f.name): show_df(pd.read_csv(f))


def page_demo():
    st.header("Faculty Demo Mode")
    from pathlib import Path as _P
    _f = _P(__file__).parent / "docs" / "FACULTY_DEMO.md"
    with st.expander("8-12 minute presentation script (docs/FACULTY_DEMO.md)"):
        st.markdown(_f.read_text(encoding="utf-8") if _f.exists() else "Script file missing: docs/FACULTY_DEMO.md")
    st.caption("Runs the full chain Explorer -> Relay -> Master -> Gateway step by step, using the real code (no pre-computed values). About 5 minutes.")
    c1, c2, c3 = st.columns(3)
    delay = c1.slider("Pause between steps (s)", 0.0, 6.0, 2.0, 0.5); snr_in = c2.slider("Input SNR for the Signal Lab steps (dB)", -5.0, 20.0, 5.0, 0.5)
    fail = c3.checkbox("Finish with relay-failure demo", True)
    if not st.button("Start demo", type="primary"): return
    s = st.session_state; x, fs, lab = s.signal
    cfg = ChannelConfig(**s.cfg.__dict__); prog = st.progress(0.0); N = 15

    def step(i, title):
        prog.progress(i / N); st.markdown(f"#### Step {i}/{N} - {title}")

    def pause(): time.sleep(delay)

    step(1, "Initialize underwater environment")
    env = Environment(cfg, seed=int(s.get("seed", DEFAULT_SEED)), n_explorers=s.get("n_exp", 3), n_relays=s.get("n_rel", 2), n_sensors=s.get("n_sen", 4))
    show_df(pd.DataFrame({"Parameter": ["Carrier (kHz)", "Source level (dB)", "Ambient noise (dB)", "Spreading k", "Packet bits", "Bit rate (bps)"],
                          "Value": [cfg.carrier_khz, cfg.source_level_db, cfg.noise_level_db, cfg.spreading_k, cfg.packet_bits, cfg.bit_rate_bps]})); pause()
    step(2, "Deploy AUVs")
    tab = env.node_table(); show_df(tab[tab["Type"].isin(["MASTER", "RELAY", "EXPLORER", "GATEWAY"])].iloc[:, :8])
    show_plot(build_network_figure(env), key="d2"); pause()
    step(3, "Initialize sensor nodes")
    show_df(tab[tab["Type"] == "SENSOR"].iloc[:, :8]); pause()
    src = "EXPLORER-01"
    step(4, "Generate sensor data (SIMULATED)")
    st.json(env.nodes[src].read_sensors()); pause()
    step(5, "Select acoustic signal")
    st.write(f"{lab} | fs = {fs} Hz | {len(x)} samples"); show_plot(plot_overlay(x, x, fs, "Original", "Original (copy)"), key="d5"); pause()
    step(6, "Add Gaussian noise")
    y, sigma, out = _pipeline(x, fs, snr_in, 42, True, 32, 0.05, None)
    st.write(f"Noise sigma = {sigma:.4f}; measured SNR after noise = {snr_db(x, y):.2f} dB")
    show_plot(plot_overlay(x, y, fs, "Original", "Noisy"), key="d6"); pause()
    step(7, "Transmit from Explorer")
    res = None
    for attempt in range(1, 6):
        res = env.transmit(src, x, fs, process=True)
        if res.delivered: break
        st.warning(f"Attempt {attempt}: packet lost - retransmitting (simple ARQ).")
    show_plot(build_network_figure(env, route=res.route, animate=True), key="d7"); pause()
    h = res.hops
    step(8, "Receive at Relay")
    st.write(f"{h[0].tx} -> {h[0].rx}: distance {h[0].distance_m:.0f} m, link SNR {h[0].link_snr_db:.1f} dB, received waveform SNR {h[0].snr_rx_db:.2f} dB"); pause()
    step(9, "Apply signal processing at the Relay")
    stg = next((v for k, v in res.signals.items() if k.startswith("RELAY") and k.endswith("stages")), None)
    if stg:
        sn = {k: snr_db(x, v) for k, v in stg.items()}
        show_plot(plot_stage_waveforms({"Original": x, **stg}, fs, snrs=sn), key="d9")
        show_df(pd.DataFrame([{"Stage": k, "SNR (dB)": round(v, 2)} for k, v in sn.items()]))
    pause()
    step(10, "Forward to Master")
    st.write(f"{h[1].tx} -> {h[1].rx}: distance {h[1].distance_m:.0f} m, link SNR {h[1].link_snr_db:.1f} dB, waveform SNR {h[1].snr_rx_db:.2f} dB"); pause()
    step(11, "Send to Surface Gateway")
    st.write(f"{h[2].tx} -> {h[2].rx}: distance {h[2].distance_m:.0f} m, link SNR {h[2].link_snr_db:.1f} dB, waveform SNR {h[2].snr_rx_db:.2f} dB"); pause()
    step(12, "Display recovered signal")
    show_plot(plot_overlay(x, res.signals["Recovered"], fs, "Original", "Recovered at gateway"), key="d12"); pause()
    step(13, "Show SNR improvement (same network, denoising OFF vs ON)")
    mk = lambda: Environment(cfg, seed=int(s.get("seed", DEFAULT_SEED)), n_explorers=s.get("n_exp", 3), n_relays=s.get("n_rel", 2), n_sensors=s.get("n_sen", 4))
    off = mk().transmit(src, x, fs, process=False, ignore_loss=True).final_snr_db
    on = mk().transmit(src, x, fs, process=True, ignore_loss=True).final_snr_db
    kpis([("Final SNR, denoising OFF", f"{off:.2f} dB"), ("Final SNR, denoising ON", f"{on:.2f} dB"), ("Improvement", f"{on - off:+.2f} dB")]); pause()
    step(14, "Show packet delivery")
    mc = env.simulate_delivery(src, 2000)
    kpis([("Packet delivery ratio", f"{mc['pdr']:.3f}"), ("Packet loss", f"{mc['loss']:.3f}"), ("Hops", mc["hops"]), ("End-to-end delay", f"{mc['mean_delay_s']:.2f} s")]); pause()
    step(15, "Final results")
    show_df(pd.DataFrame([{"Route": mc["route"], "Hops": mc["hops"], "Waveform SNR OFF (dB)": round(off, 2), "Waveform SNR ON (dB)": round(on, 2),
                           "PDR": round(mc["pdr"], 3), "Delay (s)": round(mc["mean_delay_s"], 3)}]))
    prog.progress(1.0)
    if fail:
        st.markdown("#### Bonus - relay failure and route recovery")
        before = env.route(src); env.set_state(before.path[1], "FAILED"); after = env.route(src)
        st.write("Before: " + " -> ".join(before.path)); st.write(f"{before.path[1]} FAILED"); st.write("After: " + (" -> ".join(after.path) if after else "no route"))
        show_plot(build_network_figure(env, route=after, animate=bool(after)), key="dfail")
    st.success("Demo complete.")


def page_about():
    st.header("About and Research Comparison")
    st.markdown("""**Research basis:** Underwater Acoustic Sensor Network demonstration, *2024 IEEE Applied Sensing Conference (APSCON)*, Goa, India, 22-24 Jan 2024, DOI 10.1109/APSCON60364.2024.10465917.
This project is a **software re-creation of the concepts**, not a reproduction of the paper's measurements.""")
    show_df(pd.DataFrame([
        ["UASN", "Virtual UASN", "Simulated"], ["Physical underwater nodes", "Software nodes (Node class)", "Simulated"],
        ["Transducer", "VirtualTransducer", "Simulated"], ["Hydrophone", "VirtualHydrophone", "Simulated"],
        ["Underwater modem", "Software modem (BPSK BER model)", "Simulated"], ["Acoustic channel", "Link-budget channel (Thorp + spreading + noise)", "Simulated"],
        ["Multi-hop communication", "Explorer -> Relay -> Master -> Gateway, ETX routing", "Reproduced concept"],
        ["Oceanographic sensors", "Simulated sensor suite", "Simulated"], ["Physical test-bed", "Streamlit virtual test-bed", "Simulated"],
        ["Noise", "Gaussian noise at link SNR", "Simulated"], ["Signal processing", "Kalman, LMS, Wiener, Butterworth, SNR in Python", "Extended (our addition)"],
        ["Real acoustic data", "OpenWhistle dolphin clips (external dataset)", "Extended (not the paper's data)"],
        ["NS-3 / Aqua-Sim NG", "Optional topology export only (ns3/)", "Not run here"],
        ["(not in paper) passive monitoring + classification", "Heuristic baseline classifier on uploaded/dataset/synthetic audio", "Extended (our addition)"],
        ["(not in paper) waveform-level acoustic channel", "Spreading, Thorp absorption, Wenz noise, image-method multipath, Doppler, interference, BPSK+CRC", "Extended (our addition)"],
        ["(not in paper) connection establishment", "Proposed simulator handshake with retries/timeouts", "Extended (proposal, not a standard)"]],
        columns=["Research concept", "Our implementation", "Status"]))
    st.markdown("""**Limitations:** simplified channel (no multipath/Doppler/stratification); BPSK error model with Eb/N0 = SNR; hand-chosen filter parameters;
the denoising chain can reduce SNR when input SNR is already high; flat seabed; no real hardware or sea trials.""")


def main():
    init(); page = sidebar(); env = st.session_state.env

    def rebuild():
        new_env()
    {"Dashboard": lambda: page_dashboard(env), "Ocean Environment": lambda: pn.page_ocean(env, rebuild), "Acoustic Data Explorer": pn.page_data,
     "Noise Classification": pn.page_classify, "Acoustic Signal Lab": page_lab, "Network Simulation": lambda: page_network(env),
     "Connection Establishment": lambda: pn.page_connection(env), "Node Details": lambda: page_node(env),
     "Routing and Packet Flow": lambda: pn.page_routing_flow(env), "Results and Experiments": page_results,
     "Faculty Demo Mode": page_demo, "About and Research Comparison": page_about}[page]()


main()
