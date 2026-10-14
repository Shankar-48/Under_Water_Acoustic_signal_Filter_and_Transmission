"""Virtual hydrophone: receives the acoustic waveform plus channel noise.
The received level is re-normalised (like an AGC), so only the SNR matters for the
waveform; absolute attenuation is handled by the link budget in the channel."""
import numpy as np
from signal_processing.noise import noise_sigma_for_snr


class VirtualHydrophone:
    def __init__(self, node_id):
        self.node_id = node_id

    def receive(self, tx, link_snr_db, rng):
        sigma = noise_sigma_for_snr(tx.waveform, link_snr_db)
        noisy = tx.waveform + rng.normal(0.0, sigma, tx.waveform.shape)
        return noisy, sigma

    @staticmethod
    def measure_noise_floor(sigma, rng, n=4096):
        """Receiver 'listens' to ambient noise before the packet -> noise variance estimate."""
        return float(np.var(rng.normal(0.0, sigma, n)))
