"""Passband coherent BPSK modem with preamble synchronisation (timing + carrier phase).

tx:  bits -> +/-1 -> rectangular pulses (sps samples/bit) -> x cos(2 pi fc t)
rx:  down-convert, correlate with the known preamble to find the start sample and carrier phase,
     integrate-and-dump per bit, hard decision. Timing is integer-sample; no equaliser, no
     Doppler tracking - so multipath ISI and Doppler genuinely degrade the result."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from math import erfc, sqrt
from communication.framing import PREAMBLE_BITS, build_frame, parse_frame_bits, frame_length_bits


@dataclass
class ModemConfig:
    fs: int = 48000
    fc_hz: float = 12000.0
    bit_rate: float = 1000.0
    track_phase: bool = True     # decision-directed 2nd-order phase/frequency tracking loop (handles small Doppler offsets)
    loop_alpha: float = 0.15
    loop_beta: float = 0.006

    @property
    def sps(self):
        s = int(round(self.fs / self.bit_rate))
        if s < 4:
            raise ValueError("need at least 4 samples per bit (raise fs or lower bit rate)")
        return s


def modulate(bits, cfg: ModemConfig):
    sym = np.repeat(2.0 * np.asarray(bits, float) - 1.0, cfg.sps)
    t = np.arange(len(sym)) / cfg.fs
    return sym * np.sqrt(2) * np.cos(2 * np.pi * cfg.fc_hz * t)         # unit RMS


def _baseband(rx, cfg):
    t = np.arange(len(rx)) / cfg.fs
    return rx * np.exp(-2j * np.pi * cfg.fc_hz * t)


def demodulate(rx, cfg: ModemConfig, n_bits):
    """Return (bits, info). Raises nothing; info['sync_ok'] False if the preamble is not found."""
    sps = cfg.sps
    z = _baseband(np.asarray(rx, float), cfg)
    tmpl = np.repeat(2.0 * PREAMBLE_BITS - 1.0, sps)
    if len(z) < len(tmpl) + sps:
        return np.zeros(0, np.int8), {"sync_ok": False, "reason": "received signal shorter than preamble"}
    c = np.correlate(z, tmpl.astype(complex), mode="valid")
    mag = np.abs(c)
    k = int(np.argmax(mag))
    peak, floor = mag[k], np.median(mag) + 1e-30
    h = c[k] / np.sum(tmpl ** 2)
    phase = np.angle(h)
    info = {"start": k, "phase_rad": float(phase), "sync_metric": float(peak / floor)}
    if peak / floor < 4.0:
        info.update(sync_ok=False, reason="preamble not detected (correlation peak too weak)")
        return np.zeros(0, np.int8), info
    avail = (len(z) - k) // sps
    nb = min(n_bits, avail)
    seg = z[k:k + nb * sps].reshape(nb, sps).sum(axis=1) * np.exp(-1j * phase)
    info.update(sync_ok=True, reason="ok", tracked=False)
    if cfg.track_phase and nb > 0:
        ph, om, out = 0.0, 0.0, np.empty(nb, complex)
        for i in range(nb):                                   # decision-directed loop: error = Im(r)*sign(Re(r))/|r|
            r = seg[i] * np.exp(-1j * ph); out[i] = r
            e = np.imag(r) * np.sign(np.real(r)) / (abs(r) + 1e-30)
            om += cfg.loop_beta * e; ph += om + cfg.loop_alpha * e
        seg = out; info.update(tracked=True, freq_offset_rad_per_bit=float(om))
    return (seg.real > 0).astype(np.int8), info


def ber_theory(ebn0_db):
    return 0.5 * erfc(sqrt(10 ** (ebn0_db / 10)))


def ebn0_db_from_rx(rx_rms_upa, noise_psd_db_fc, bit_rate):
    """Eb/N0 for BPSK: Eb = P/Rb with P = RMS^2 (uPa^2), N0 = one-sided noise PSD at the carrier (uPa^2/Hz)."""
    return 10 * np.log10(rx_rms_upa ** 2 / bit_rate) - noise_psd_db_fc
