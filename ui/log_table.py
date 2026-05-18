from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QKeySequence
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from core.packet import Packet


class LogTable(QTableWidget):
    COLUMNS = ["#", "Time", "Dir", "Hex Data", "ASCII", "Bytes", "Delta (ms)"]
    MAX_ROWS = 10_000
    TRIM_ROWS = 1_000

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._packet_index = 0
        self._last_timestamp: float | None = None
        self._shown_packets: list[Packet] = []
        self._raw_tooltips_enabled = False

        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setWordWrap(False)
        self.verticalHeader().setVisible(False)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        mono = QFont("Consolas", 12)
        self.setFont(QFont("Segoe UI", 10))
        for column in (3, 4):
            self.horizontalHeaderItem(column).setFont(mono)

    def add_packet(self, packet: Packet) -> None:
        should_scroll = self._is_at_bottom()
        self._packet_index += 1
        delta_text = ""
        if self._last_timestamp is not None:
            delta_text = f"{(packet.timestamp - self._last_timestamp) * 1000:.3f}"
        self._last_timestamp = packet.timestamp

        row = self.rowCount()
        self.insertRow(row)
        self._shown_packets.append(packet)

        values = [
            str(self._packet_index),
            packet.wall_time,
            "TX →" if packet.direction == "TX" else "RX ←",
            packet.hex_str,
            packet.ascii_str,
            str(packet.byte_count),
            delta_text,
        ]

        is_framed = packet.raw.startswith(b"\x02") and packet.raw.endswith(b"\x03")
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, packet)
            item.setData(Qt.UserRole + 1, packet.direction)
            item.setData(Qt.UserRole + 2, packet.hex_str.lower())
            item.setData(Qt.UserRole + 3, packet.ascii_str.lower())
            item.setData(Qt.UserRole + 4, delta_text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if column in (3, 4):
                item.setFont(QFont("Consolas", 12))
            if column == 2:
                item.setForeground(QColor("#569cd6" if packet.direction == "TX" else "#ce9178"))
            if is_framed:
                item.setBackground(QColor("#1f3a32"))
            if self._raw_tooltips_enabled:
                item.setToolTip(self._raw_tooltip(packet))
            self.setItem(row, column, item)

        self._trim_if_needed()
        if should_scroll:
            self.scrollToBottom()

    def clear_all(self) -> None:
        self.setRowCount(0)
        self._packet_index = 0
        self._last_timestamp = None
        self._shown_packets.clear()

    def export_to_csv(self, filepath: str) -> None:
        path = Path(filepath)
        with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(self.COLUMNS)
            for row in range(self.rowCount()):
                if self.isRowHidden(row):
                    continue
                writer.writerow([self.item(row, column).text() if self.item(row, column) else "" for column in range(self.columnCount())])

    def set_raw_tooltips_enabled(self, enabled: bool) -> None:
        self._raw_tooltips_enabled = enabled
        for row in range(self.rowCount()):
            packet = self.item(row, 0).data(Qt.UserRole) if self.item(row, 0) else None
            tooltip = self._raw_tooltip(packet) if enabled and packet else ""
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item is not None:
                    item.setToolTip(tooltip)

    def apply_filter(self, query: str, show_tx: bool, show_rx: bool) -> None:
        query = query.strip().lower()
        for row in range(self.rowCount()):
            first_item = self.item(row, 0)
            if first_item is None:
                continue
            direction = first_item.data(Qt.UserRole + 1)
            hex_text = first_item.data(Qt.UserRole + 2) or ""
            ascii_text = first_item.data(Qt.UserRole + 3) or ""
            direction_visible = (direction == "TX" and show_tx) or (direction == "RX" and show_rx)
            query_visible = not query or query in hex_text or query in ascii_text
            self.setRowHidden(row, not (direction_visible and query_visible))

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.Copy):
            self._copy_selection()
            return
        super().keyPressEvent(event)

    def _copy_selection(self) -> None:
        ranges = self.selectedRanges()
        if not ranges:
            return

        lines: list[str] = []
        for selection in ranges:
            for row in range(selection.topRow(), selection.bottomRow() + 1):
                if self.isRowHidden(row):
                    continue
                values = []
                for column in range(selection.leftColumn(), selection.rightColumn() + 1):
                    item = self.item(row, column)
                    values.append(item.text() if item else "")
                lines.append("\t".join(values))
        QGuiApplication.clipboard().setText("\n".join(lines))

    def _trim_if_needed(self) -> None:
        if self.rowCount() <= self.MAX_ROWS:
            return
        remove_count = min(self.TRIM_ROWS, self.rowCount())
        for _ in range(remove_count):
            self.removeRow(0)
        del self._shown_packets[:remove_count]

    def _is_at_bottom(self) -> bool:
        scroll_bar = self.verticalScrollBar()
        return scroll_bar.value() >= scroll_bar.maximum() - 2

    def _raw_tooltip(self, packet: Packet) -> str:
        decimal = " ".join(str(byte) for byte in packet.raw)
        hex_text = packet.hex_str
        binary = " ".join(f"{byte:08b}" for byte in packet.raw)
        return f"Decimal: {decimal}\nHex: {hex_text}\nBinary: {binary}"
