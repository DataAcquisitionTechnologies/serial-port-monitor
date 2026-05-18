from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from serial.tools import list_ports

from core.bridge import SerialBridge
from core.packet import Packet
from ui.log_table import LogTable
from ui.scpi_commands_viewer import ScpiCommandsViewer


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("InternalTools", "SerialSniffer")
        self.bridge: SerialBridge | None = None
        self.packet_count = 0
        self.byte_count = 0

        self.setWindowTitle("SerialSniffer — Idle")
        self.resize(1280, 760)
        self._build_ui()
        self._create_shortcuts()
        self._restore_settings()
        self.refresh_ports()
        self._set_sniffing_ui(False)
        self.statusBar().showMessage("Idle")

    def closeEvent(self, event) -> None:
        self._save_settings()
        if self.bridge is not None and self.bridge.isRunning():
            self.on_stop_clicked()
        super().closeEvent(event)

    def on_packet_ready(self, packet: Packet) -> None:
        self.log_table.add_packet(packet)
        self.scpi_viewer.add_packet(packet)
        self.packet_count += 1
        self.byte_count += packet.byte_count
        self._update_counts()
        self.apply_current_filter()

    def on_start_clicked(self) -> None:
        virtual_port = self.virtual_port_combo.currentText().strip()
        physical_port = self.physical_port_combo.currentText().strip()

        if not virtual_port or not physical_port:
            self._show_error("Select both a virtual COM port and a physical COM port.")
            return
        if virtual_port == physical_port:
            self._show_error("Virtual Port and Physical Port must be different.")
            return

        self._save_settings()
        self.bridge = SerialBridge(
            virtual_port=virtual_port,
            physical_port=physical_port,
            baud_rate=int(self.baud_combo.currentText()),
            byte_size=int(self.data_bits_combo.currentText()),
            parity=self.parity_combo.currentData(),
            stop_bits=float(self.stop_bits_combo.currentText()),
        )
        self.bridge.packet_ready.connect(self.on_packet_ready)
        self.bridge.error_occurred.connect(self.show_error_dialog)
        self.bridge.status_changed.connect(self.statusBar().showMessage)
        self.bridge.bridge_stopped.connect(self._on_bridge_stopped)
        self.bridge.start()

        self._set_sniffing_ui(True)
        self.setWindowTitle(f"SerialSniffer — {virtual_port} ↔ {physical_port} @ {self.baud_combo.currentText()} [LIVE]")
        self.status_label.setText("Starting...")

    def on_stop_clicked(self) -> None:
        if self.bridge is not None:
            self.bridge.stop()
            self.bridge.wait(3000)
            self.bridge = None
        self._set_sniffing_ui(False)
        self.setWindowTitle("SerialSniffer — Idle")
        self.statusBar().showMessage("Idle")

    def on_export_clicked(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Capture to CSV",
            "serial_capture.csv",
            "CSV Files (*.csv);;All Files (*.*)",
        )
        if not filepath:
            return
        try:
            self.log_table.export_to_csv(filepath)
            self.statusBar().showMessage(f"Exported capture to {filepath}", 5000)
        except Exception as exc:
            self.show_error_dialog(f"Could not export CSV: {exc}")

    def refresh_ports(self) -> None:
        previous_virtual = self.virtual_port_combo.currentText() or self.settings.value("virtual_port", "")
        previous_physical = self.physical_port_combo.currentText() or self.settings.value("physical_port", "")
        ports = [port.device for port in list_ports.comports()]

        for combo, previous in ((self.virtual_port_combo, previous_virtual), (self.physical_port_combo, previous_physical)):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(ports)
            if previous:
                index = combo.findText(previous)
                if index >= 0:
                    combo.setCurrentIndex(index)
                else:
                    combo.setEditText(previous)
            combo.blockSignals(False)

        self.statusBar().showMessage(f"Found {len(ports)} COM port(s).", 3000)

    def show_error_dialog(self, message: str) -> None:
        self.statusBar().showMessage(f"Error: {message}")
        self.status_label.setText("Error")
        QMessageBox.critical(self, "SerialSniffer Error", message)
        if self.bridge is not None:
            self.bridge.stop()

    def apply_current_filter(self) -> None:
        self.log_table.apply_filter(
            self.filter_input.text(),
            self.show_tx_checkbox.isChecked(),
            self.show_rx_checkbox.isChecked(),
        )

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        config_frame = QFrame()
        config_frame.setObjectName("configFrame")
        config_frame.setFixedHeight(64)
        config_layout = QHBoxLayout(config_frame)
        config_layout.setContentsMargins(10, 8, 10, 8)
        config_layout.setSpacing(8)

        self.virtual_port_combo = self._combo(editable=True)
        self.physical_port_combo = self._combo(editable=True)
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setToolTip("Refresh COM ports")
        self.refresh_button.clicked.connect(self.refresh_ports)

        self.baud_combo = self._combo(["300", "1200", "2400", "4800", "9600", "14400", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.data_bits_combo = self._combo(["5", "6", "7", "8"])
        self.parity_combo = self._combo()
        for label, value in [("None (N)", "N"), ("Even (E)", "E"), ("Odd (O)", "O"), ("Mark (M)", "M"), ("Space (S)", "S")]:
            self.parity_combo.addItem(label, value)
        self.stop_bits_combo = self._combo(["1", "1.5", "2"])

        self.start_button = QPushButton("▶ Start")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.on_start_clicked)
        self.stop_button = QPushButton("■ Stop")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.clear_button = QPushButton("🗑 Clear Log")
        self.clear_button.clicked.connect(self._clear_log)

        for label, widget in [
            ("Virtual Port:", self.virtual_port_combo),
            ("Physical Port:", self.physical_port_combo),
            ("Baud:", self.baud_combo),
            ("Data Bits:", self.data_bits_combo),
            ("Parity:", self.parity_combo),
            ("Stop Bits:", self.stop_bits_combo),
        ]:
            config_layout.addWidget(QLabel(label))
            config_layout.addWidget(widget)
        config_layout.addWidget(self.refresh_button)
        config_layout.addSpacing(8)
        config_layout.addWidget(self.start_button)
        config_layout.addWidget(self.stop_button)
        config_layout.addWidget(self.clear_button)

        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)
        filter_layout.addWidget(QLabel("🔍 Filter:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search hex or ASCII")
        self.filter_input.textChanged.connect(self.apply_current_filter)
        filter_layout.addWidget(self.filter_input, stretch=1)
        self.show_tx_checkbox = QCheckBox("Show TX")
        self.show_tx_checkbox.setChecked(True)
        self.show_tx_checkbox.toggled.connect(self.apply_current_filter)
        self.show_rx_checkbox = QCheckBox("Show RX")
        self.show_rx_checkbox.setChecked(True)
        self.show_rx_checkbox.toggled.connect(self.apply_current_filter)
        self.raw_bytes_checkbox = QCheckBox("Show Raw Bytes")
        self.raw_bytes_checkbox.setToolTip("Show decimal, hex, and binary raw bytes when hovering over rows")
        self.raw_bytes_checkbox.toggled.connect(self._on_raw_bytes_toggled)
        filter_layout.addWidget(self.show_tx_checkbox)
        filter_layout.addWidget(self.show_rx_checkbox)
        filter_layout.addWidget(self.raw_bytes_checkbox)

        self.log_table = LogTable()
        self.scpi_viewer = ScpiCommandsViewer()

        capture_splitter = QSplitter(Qt.Vertical)
        capture_splitter.addWidget(self.log_table)
        capture_splitter.addWidget(self.scpi_viewer)
        capture_splitter.setStretchFactor(0, 4)
        capture_splitter.setStretchFactor(1, 1)
        capture_splitter.setSizes([560, 180])

        action_frame = QFrame()
        action_frame.setObjectName("actionFrame")
        action_frame.setFixedHeight(44)
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(10, 6, 10, 6)
        self.export_button = QPushButton("💾 Export Capture to CSV")
        self.export_button.clicked.connect(self.on_export_clicked)
        action_layout.addWidget(self.export_button)
        action_layout.addStretch(1)
        self.bytes_label = QLabel("Bytes Captured: 0")
        self.packets_label = QLabel("Packets: 0")
        self.status_label = QLabel("Status: Idle")
        action_layout.addWidget(self.bytes_label)
        action_layout.addWidget(QLabel("|"))
        action_layout.addWidget(self.packets_label)
        action_layout.addWidget(QLabel("|"))
        action_layout.addWidget(self.status_label)

        root_layout.addWidget(config_frame)
        root_layout.addWidget(filter_frame)
        root_layout.addWidget(capture_splitter, stretch=1)
        root_layout.addWidget(action_frame)
        self.setCentralWidget(central)

    def _combo(self, items: list[str] | None = None, editable: bool = False) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(editable)
        combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        if items:
            combo.addItems(items)
        return combo

    def _create_shortcuts(self) -> None:
        shortcuts = [
            ("Ctrl+S", self.on_start_clicked),
            ("Ctrl+Q", self.on_stop_clicked),
            ("Ctrl+E", self.on_export_clicked),
            ("Ctrl+L", self._clear_log),
            ("Ctrl+F", self.filter_input.setFocus),
        ]
        for key_sequence, callback in shortcuts:
            action = QAction(self)
            action.setShortcut(QKeySequence(key_sequence))
            action.triggered.connect(callback)
            self.addAction(action)

    def _restore_settings(self) -> None:
        geometry = self.settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        baud = self.settings.value("baud_rate", "9600")
        data_bits = self.settings.value("data_bits", "8")
        parity = self.settings.value("parity", "N")
        stop_bits = self.settings.value("stop_bits", "1")

        self._set_combo_text(self.baud_combo, str(baud))
        self._set_combo_text(self.data_bits_combo, str(data_bits))
        self._set_combo_data(self.parity_combo, str(parity))
        self._set_combo_text(self.stop_bits_combo, str(stop_bits))

    def _save_settings(self) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("virtual_port", self.virtual_port_combo.currentText())
        self.settings.setValue("physical_port", self.physical_port_combo.currentText())
        self.settings.setValue("baud_rate", self.baud_combo.currentText())
        self.settings.setValue("data_bits", self.data_bits_combo.currentText())
        self.settings.setValue("parity", self.parity_combo.currentData())
        self.settings.setValue("stop_bits", self.stop_bits_combo.currentText())

    def _set_combo_text(self, combo: QComboBox, text: str) -> None:
        index = combo.findText(text)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _set_combo_data(self, combo: QComboBox, value: str) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return

    def _set_sniffing_ui(self, sniffing: bool) -> None:
        for widget in [
            self.virtual_port_combo,
            self.physical_port_combo,
            self.baud_combo,
            self.data_bits_combo,
            self.parity_combo,
            self.stop_bits_combo,
            self.refresh_button,
        ]:
            widget.setEnabled(not sniffing)
        self.start_button.setEnabled(not sniffing)
        self.stop_button.setEnabled(sniffing)
        self.clear_button.setEnabled(True)
        self.status_label.setText("Status: Live" if sniffing else "Status: Idle")

    def _on_bridge_stopped(self) -> None:
        self.bridge = None
        self._set_sniffing_ui(False)
        self.setWindowTitle("SerialSniffer — Idle")

    def _on_raw_bytes_toggled(self, enabled: bool) -> None:
        self.log_table.set_raw_tooltips_enabled(enabled)

    def _clear_log(self) -> None:
        self.log_table.clear_all()
        self.scpi_viewer.clear_all()
        self.packet_count = 0
        self.byte_count = 0
        self._update_counts()

    def _update_counts(self) -> None:
        self.bytes_label.setText(f"Bytes Captured: {self.byte_count}")
        self.packets_label.setText(f"Packets: {self.packet_count}")

    def _show_error(self, message: str) -> None:
        self.statusBar().showMessage(f"Error: {message}")
        QMessageBox.critical(self, "SerialSniffer Error", message)
