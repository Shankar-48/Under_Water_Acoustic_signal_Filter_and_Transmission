"""Central configuration. Every number here is an ASSUMPTION of our simulation,
not a value taken from the research paper. Change them from the UI or here."""
from dataclasses import dataclass

SPEED_OF_SOUND = 1500.0   # m/s, typical seawater value (assumption)
DEFAULT_SEED = 42
MAX_SAMPLES = 16384       # cap on waveform length so the pure-Python LMS stays fast
GATEWAY_ID = "GW-01"

# Node types
GATEWAY, MASTER, RELAY, EXPLORER, SENSOR = "GATEWAY", "MASTER", "RELAY", "EXPLORER", "SENSOR"

# Modem design range (m) per node type (assumption)
COMM_RANGE = {GATEWAY: 2500.0, MASTER: 2000.0, RELAY: 1500.0, EXPLORER: 1200.0, SENSOR: 400.0}

# Energy model (arbitrary battery units = % of full battery per packet)
TX_COST, RX_COST, IDLE_COST_PER_S = 0.20, 0.05, 0.001


@dataclass
class ChannelConfig:
    """Parameters of the simplified acoustic channel (see docs/methodology.md)."""
    carrier_khz: float = 10.0        # carrier frequency used for absorption
    source_level_db: float = 170.0   # dB re 1 uPa @1 m (assumption)
    noise_level_db: float = 112.0    # in-band ambient noise level, dB re 1 uPa (assumption)
    spreading_k: float = 1.5         # 1 = cylindrical, 2 = spherical, 1.5 = practical
    interference_db: float = 0.0     # extra interference level; 0 = disabled
    packet_bits: int = 256           # packet length in bits
    bit_rate_bps: float = 2000.0     # modem bit rate (assumption)
    processing_delay_s: float = 0.05 # delay for denoising at a relay (assumption)
    min_decode_snr_db: float = -10.0 # below this a link is considered unusable for routing
    noise_model: str = "fixed"       # "fixed" = legacy in-band level above | "wenz" = Stojanovic empirical ambient noise
    shipping: float = 0.5            # Wenz shipping factor 0..1 (used when noise_model == 'wenz')
    wind_mps: float = 5.0            # wind speed (m/s) (used when noise_model == 'wenz')
