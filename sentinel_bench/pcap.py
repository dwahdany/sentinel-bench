"""A minimal libpcap reader. Reads from a file and nothing else.

Deliberately tiny: the suite only ever replays recorded captures, so there is no live
capture path here and there must not be one. See docs/conventions.md.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

MAGIC_LE = 0xA1B2C3D4
MAGIC_BE = 0xD4C3B2A1
LINKTYPE_RAW = 101


@dataclass(frozen=True)
class Packet:
    """One recorded packet."""

    index: int
    ts_us: int
    payload: bytes

    @property
    def text(self) -> str:
        """Payload decoded leniently -- captures are bytes, rules are written over text."""
        return self.payload.decode("utf-8", "replace")


class PcapError(ValueError):
    """Raised on a file that is not a capture we can read."""


def read_packets(path):
    """Yield :class:`Packet` for every record in the capture at ``path``."""
    with open(path, "rb") as handle:
        header = handle.read(24)
        if len(header) < 24:
            raise PcapError(f"{path}: truncated global header")
        (magic,) = struct.unpack("<I", header[:4])
        if magic == MAGIC_LE:
            endian = "<"
        elif magic == MAGIC_BE:
            endian = ">"
        else:
            raise PcapError(f"{path}: bad magic 0x{magic:08x}")
        (linktype,) = struct.unpack(endian + "I", header[20:24])
        if linktype != LINKTYPE_RAW:
            raise PcapError(f"{path}: linktype {linktype}, only RAW ({LINKTYPE_RAW}) is supported")
        index = 0
        while True:
            record = handle.read(16)
            if not record:
                return
            if len(record) < 16:
                raise PcapError(f"{path}: truncated record header at packet {index}")
            ts_sec, ts_usec, caplen, _origlen = struct.unpack(endian + "IIII", record)
            payload = handle.read(caplen)
            if len(payload) < caplen:
                raise PcapError(f"{path}: truncated packet {index}")
            yield Packet(index=index, ts_us=ts_sec * 1_000_000 + ts_usec, payload=payload)
            index += 1


def write_packets(path, payloads, first_ts=1754000000):
    """Write ``payloads`` as a RAW-linktype capture. Used to build test fixtures."""
    with open(path, "wb") as handle:
        handle.write(struct.pack("<IHHiIII", MAGIC_LE, 2, 4, 0, 0, 262144, LINKTYPE_RAW))
        for offset, payload in enumerate(payloads):
            handle.write(struct.pack("<IIII", first_ts + offset, offset * 1000,
                                     len(payload), len(payload)))
            handle.write(payload)
