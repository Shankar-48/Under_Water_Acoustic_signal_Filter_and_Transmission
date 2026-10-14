"""End-to-end digital acoustic link: payload -> frame -> BPSK -> channel -> sync -> demod -> CRC.
Keep this separate from passive sound classification: here WE transmit known bits."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from communication.framing import build_frame, parse_frame_bits, PREAMBLE_BITS, frame_length_bits
from communication.bpsk import ModemConfig, modulate, demodulate, ebn0_db_from_rx, ber_theory
from simulation.waveform_channel import ChannelEffects, propagate, C_SOUND


@dataclass
class LinkResult:
    delivered: bool
    payload_tx: bytes
    payload_rx: bytes
    crc_ok: bool
    sync_ok: bool
    bit_errors: int
    n_bits: int
    ebn0_db: float
    ber_theory: float
    delay_s: float
    tx_wave: np.ndarray
    rx_wave: np.ndarray
    fs: int
    reason: str
    attempts: int = 1
    info: dict = field(default_factory=dict)

    @property
    def ber(self):
        return self.bit_errors / max(self.n_bits, 1)


def send_once(payload: bytes, distance_m, source_level_db, fx: ChannelEffects, cfg: ModemConfig, rng,
              src_depth=50.0, rcv_depth=50.0):
    frame = build_frame(payload)
    tx = modulate(frame, cfg)
    ch = propagate(tx, cfg.fs, distance_m, source_level_db, cfg.fc_hz, fx, rng, src_depth, rcv_depth, bit_rate=cfg.bit_rate)
    n_after = len(frame) - len(PREAMBLE_BITS)
    bits, info = demodulate(ch.rx, cfg, len(frame))
    if not info.get("sync_ok"):
        return LinkResult(False, payload, b"", False, False, len(frame), len(frame), float("nan"), float("nan"), 0.0, tx, ch.rx, cfg.fs, info.get("reason", "no sync"), info=info)
    errs = int(np.sum(bits[: len(frame)] != frame[: len(bits)])) + max(0, len(frame) - len(bits))
    parsed = parse_frame_bits(bits[len(PREAMBLE_BITS):])
    eb = ebn0_db_from_rx(ch.rx_signal_rms_upa, ch.noise_psd_at_fc_db, cfg.bit_rate) if ch.rx_signal_rms_upa > 0 else float("-inf")
    delay = ch.paths[0][0] / C_SOUND + len(frame) / cfg.bit_rate
    ok = bool(parsed["ok"]) and parsed["payload"] == payload
    return LinkResult(ok, payload, parsed.get("payload", b"") if parsed["ok"] else b"", bool(parsed["ok"]), True, errs, len(frame),
                      float(eb), ber_theory(eb) if np.isfinite(eb) else 0.5, delay, tx, ch.rx, cfg.fs, parsed["reason"],
                      info={**info, "tl_db": ch.tl_db, "rx_level_db": ch.rx_level_db, "noise_psd_db": ch.noise_psd_at_fc_db,
                            "paths": ch.paths, "doppler_factor": ch.doppler_factor})


def send_with_arq(payload, distance_m, source_level_db, fx, cfg, rng, max_attempts=3, **kw):
    """Stop-and-wait ARQ: retransmit until the CRC passes or attempts are exhausted."""
    last = None
    for a in range(1, max_attempts + 1):
        last = send_once(payload, distance_m, source_level_db, fx, cfg, rng, **kw)
        last.attempts = a
        if last.delivered:
            break
    return last


def measure_per(distance_m, source_level_db, fx, cfg, rng, n_packets=50, payload_len=16, **kw):
    """Monte Carlo packet error rate at one distance using the real waveform chain."""
    ok = errs = bits = 0
    for _ in range(n_packets):
        r = send_once(rng.bytes(payload_len), distance_m, source_level_db, fx, cfg, rng, **kw)
        ok += r.delivered; errs += r.bit_errors; bits += r.n_bits
    return {"distance_m": distance_m, "packets": n_packets, "pdr": ok / n_packets, "per": 1 - ok / n_packets, "ber": errs / max(bits, 1)}
