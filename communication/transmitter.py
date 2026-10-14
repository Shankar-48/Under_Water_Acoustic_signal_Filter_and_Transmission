"""Virtual transducer: electrical signal -> simulated acoustic transmission."""
from dataclasses import dataclass
import numpy as np


@dataclass
class AcousticTransmission:
    waveform: np.ndarray
    fs: int
    source_level_db: float
    tx_id: str


class VirtualTransducer:
    def __init__(self, node_id, source_level_db):
        self.node_id, self.source_level_db = node_id, source_level_db

    def transmit(self, signal, fs):
        x = np.asarray(signal, dtype=float)
        if x.ndim != 1 or len(x) == 0:
            raise ValueError("signal must be a non-empty 1-D array")
        return AcousticTransmission(x.copy(), int(fs), self.source_level_db, self.node_id)
