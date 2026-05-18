from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.packet import Packet


class ScpiCommandsTable(QTableWidget):
    def __init__(self, copy_callback, parent=None) -> None:
        super().__init__(parent)
        self._copy_callback = copy_callback

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.Copy):
            self._copy_callback()
            return
        super().keyPressEvent(event)


class ScpiCommandsViewer(QFrame):
    MAX_ROWS = 2_000
    TRIM_ROWS = 200
    _COMMAND_SPLITTER = re.compile(r"[\r\n]+")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._command_count = 0

        self.setObjectName("scpiViewerFrame")
        self.setMinimumHeight(150)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 6, 8, 8)
        root_layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("SCPI Commands")
        title.setObjectName("scpiViewerTitle")
        self.count_label = QLabel("0 commands")
        self.count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.count_label)

        self.table = ScpiCommandsTable(self._copy_selection)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Time", "Dir", "Command"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        self._mono_font = QFont("Consolas", 11)

        root_layout.addLayout(header_layout)
        root_layout.addWidget(self.table)

    def add_packet(self, packet: Packet) -> None:
        commands = self._commands_from_packet(packet)
        if not commands:
            return

        should_scroll = self._is_at_bottom()
        for command in commands:
            self._append_command(packet, command)

        self._trim_if_needed()
        if should_scroll:
            self.table.scrollToBottom()

    def clear_all(self) -> None:
        self.table.setRowCount(0)
        self._command_count = 0
        self._update_count_label()

    def _append_command(self, packet: Packet, command: str) -> None:
        self._command_count += 1
        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [str(self._command_count), packet.wall_time, packet.direction, command]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if column == 2:
                item.setForeground(QColor("#569cd6" if packet.direction == "TX" else "#ce9178"))
            if column == 3:
                item.setFont(self._mono_font)
            self.table.setItem(row, column, item)

        self._update_count_label()

    def _commands_from_packet(self, packet: Packet) -> list[str]:
        text = packet.raw.decode("ascii", errors="ignore")
        text = text.replace("\x02", "").replace("\x03", "").strip()
        if not text:
            return []

        commands: list[str] = []
        for part in self._COMMAND_SPLITTER.split(text):
            command = part.strip()
            if self._looks_like_scpi(command):
                commands.append(command)
        return commands

    def _looks_like_scpi(self, command: str) -> bool:
        if not command or len(command) > 240:
            return False
        if any(ord(char) < 32 or ord(char) > 126 for char in command):
            return False
        first_char = command[0]
        return (first_char.isalpha() or first_char == "*") and any(char.isalpha() for char in command)

    def _copy_selection(self) -> None:
        ranges = self.table.selectedRanges()
        if not ranges:
            return

        lines: list[str] = []
        for selection in ranges:
            for row in range(selection.topRow(), selection.bottomRow() + 1):
                values = []
                for column in range(selection.leftColumn(), selection.rightColumn() + 1):
                    item = self.table.item(row, column)
                    values.append(item.text() if item else "")
                lines.append("\t".join(values))
        QGuiApplication.clipboard().setText("\n".join(lines))

    def _trim_if_needed(self) -> None:
        if self.table.rowCount() <= self.MAX_ROWS:
            return
        remove_count = min(self.TRIM_ROWS, self.table.rowCount())
        for _ in range(remove_count):
            self.table.removeRow(0)

    def _is_at_bottom(self) -> bool:
        scroll_bar = self.table.verticalScrollBar()
        return scroll_bar.value() >= scroll_bar.maximum() - 2

    def _update_count_label(self) -> None:
        suffix = "command" if self._command_count == 1 else "commands"
        self.count_label.setText(f"{self._command_count} {suffix}")
