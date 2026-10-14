"""Packet framing with CRC-16/CCITT-FALSE.

Frame (bits, MSB first):  PREAMBLE(32) | LENGTH(8) | PAYLOAD(8*L) | CRC16(16, over LENGTH+PAYLOAD)
The preamble is fixed (an m-sequence-like pattern) so the receiver can find timing and carrier phase.
This is a SIMULATOR frame format, not a standard acoustic-modem frame."""
from __future__ import annotations
import numpy as np

PREAMBLE_BITS = np.array([int(b) for b in "11100110101110010001011010100110"], dtype=np.int8)
MAX_PAYLOAD = 255


def crc16_ccitt(data: bytes, init=0xFFFF):
    crc = init
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def bytes_to_bits(data: bytes):
    return np.unpackbits(np.frombuffer(bytes(data), dtype=np.uint8)).astype(np.int8)


def bits_to_bytes(bits):
    bits = np.asarray(bits, dtype=np.uint8)
    if len(bits) % 8:
        bits = bits[: len(bits) // 8 * 8]
    return np.packbits(bits).tobytes()


def build_frame(payload: bytes):
    if len(payload) > MAX_PAYLOAD:
        raise ValueError(f"payload too long ({len(payload)} > {MAX_PAYLOAD} bytes)")
    body = bytes([len(payload)]) + payload
    crc = crc16_ccitt(body)
    return np.concatenate([PREAMBLE_BITS, bytes_to_bits(body), bytes_to_bits(crc.to_bytes(2, "big"))]).astype(np.int8)


def frame_length_bits(payload_len):
    return len(PREAMBLE_BITS) + 8 + 8 * payload_len + 16


def parse_frame_bits(bits):
    """bits start AFTER the preamble. Returns dict(ok, payload, reason, length, crc_rx, crc_calc)."""
    bits = np.asarray(bits, dtype=np.uint8)
    if len(bits) < 8 + 16:
        return {"ok": False, "payload": b"", "reason": "frame too short"}
    L = int(np.packbits(bits[:8])[0])
    need = 8 + 8 * L + 16
    if len(bits) < need:
        return {"ok": False, "payload": b"", "reason": f"length field {L} exceeds received bits (corrupted header)"}
    body = bits_to_bytes(bits[: 8 + 8 * L])
    crc_rx = int.from_bytes(bits_to_bytes(bits[8 + 8 * L: need]), "big")
    crc_calc = crc16_ccitt(body)
    ok = crc_rx == crc_calc
    return {"ok": ok, "payload": body[1:] if ok else body[1:], "length": L, "crc_rx": crc_rx, "crc_calc": crc_calc,
            "reason": "CRC OK" if ok else "CRC mismatch (bit errors)"}
