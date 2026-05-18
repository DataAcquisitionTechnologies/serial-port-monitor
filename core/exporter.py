from __future__ import annotations

import csv
from pathlib import Path

from core.packet import Packet


def export_packets_to_csv(packets: list[Packet], filepath: str) -> None:
    path = Path(filepath)
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Index", "Wall Time", "Direction", "Hex Data", "ASCII", "Byte Count"])
        for index, packet in enumerate(packets, start=1):
            writer.writerow(
                [
                    index,
                    packet.wall_time,
                    packet.direction,
                    packet.hex_str,
                    packet.ascii_str,
                    packet.byte_count,
                ]
            )
