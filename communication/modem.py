"""Software acoustic modem: BPSK mapping used to validate the BER formula."""
import numpy as np
from math import erfc, sqrt


def bpsk_modulate(bits):
    return 2.0 * np.asarray(bits, dtype=float) - 1.0


def bpsk_demodulate(symbols):
    return (np.asarray(symbols) > 0).astype(int)


def measured_ber(snr_db, n_bits=200_000, rng=None):
    """Simulate BPSK over AWGN with Eb/N0 = SNR; returns (measured, theoretical)."""
    rng = rng or np.random.default_rng(0)
    bits = rng.integers(0, 2, n_bits)
    sigma = sqrt(1.0 / (2 * 10 ** (snr_db / 10)))      # unit-energy symbols: sigma^2 = 1/(2*SNR)
    rx = bpsk_modulate(bits) + rng.normal(0, sigma, n_bits)
    return float(np.mean(bpsk_demodulate(rx) != bits)), 0.5 * erfc(sqrt(10 ** (snr_db / 10)))
