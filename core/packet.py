from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Packet:
    timestamp: float
    wall_time: str
    direction: str
    raw: bytes

    @property
    def hex_str(self) -> str:
        return " ".join(f"{byte:02X}" for byte in self.raw)

    @property
    def ascii_str(self) -> str:
        return "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in self.raw)

    @property
    def byte_count(self) -> int:
        return len(self.raw)
