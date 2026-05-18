from __future__ import annotations

import threading
import time
from datetime import datetime

import serial
from PySide6.QtCore import QThread, Signal
from serial import SerialException
from serial.tools import list_ports

from core.packet import Packet


class SerialBridge(QThread):
    MAX_CAPTURE_BUFFER_SIZE = 4096
    CAPTURE_IDLE_FLUSH_SECONDS = 0.100

    packet_ready = Signal(Packet)
    error_occurred = Signal(str)
    status_changed = Signal(str)
    bridge_stopped = Signal()

    def __init__(
        self,
        virtual_port: str,
        physical_port: str,
        baud_rate: int,
        byte_size: int = 8,
        parity: str = "N",
        stop_bits: float = 1,
        timeout: float = 0.005,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.virtual_port = virtual_port
        self.physical_port = physical_port
        self.baud_rate = baud_rate
        self.byte_size = byte_size
        self.parity = parity
        self.stop_bits = stop_bits
        self.timeout = timeout
        self._stop_event = threading.Event()
        self._virtual_serial: serial.Serial | None = None
        self._physical_serial: serial.Serial | None = None

    def run(self) -> None:
        self._stop_event.clear()
        self.status_changed.emit("Opening serial ports...")

        try:
            self._virtual_serial = self._open_port(self.virtual_port)
            self._physical_serial = self._open_port(self.physical_port)
        except SerialException as exc:
            self.error_occurred.emit(self._format_serial_error(exc))
            self._stop_event.set()
            self._close_ports()
            self.bridge_stopped.emit()
            return
        except Exception as exc:
            self.error_occurred.emit(f"Unexpected error while opening ports: {exc}")
            self._stop_event.set()
            self._close_ports()
            self.bridge_stopped.emit()
            return

        self.status_changed.emit(
            f"Sniffing on {self.virtual_port} â†” {self.physical_port} @ {self.baud_rate} baud..."
        )

        virtual_thread = threading.Thread(target=self._read_virtual, daemon=True, name="SerialBridgeVirtualReader")
        physical_thread = threading.Thread(target=self._read_physical, daemon=True, name="SerialBridgePhysicalReader")
        virtual_thread.start()
        physical_thread.start()

        while not self._stop_event.is_set():
            if not virtual_thread.is_alive() or not physical_thread.is_alive():
                self._stop_event.set()
                break
            self.msleep(20)

        virtual_thread.join(timeout=1.0)
        physical_thread.join(timeout=1.0)
        self._close_ports()
        self.status_changed.emit("Stopped.")
        self.bridge_stopped.emit()

    def stop(self) -> None:
        self._stop_event.set()
        self._close_ports()

    def _open_port(self, port_name: str) -> serial.Serial:
        return serial.Serial(
            port=port_name,
            baudrate=self.baud_rate,
            bytesize=self.byte_size,
            parity=self.parity,
            stopbits=self.stop_bits,
            timeout=self.timeout,
            write_timeout=1,
        )

    def _read_virtual(self) -> None:
        self._copy_loop(
            source_getter=lambda: self._virtual_serial,
            target_getter=lambda: self._physical_serial,
            direction="TX",
            source_name=self.virtual_port,
            target_name=self.physical_port,
        )

    def _read_physical(self) -> None:
        self._copy_loop(
            source_getter=lambda: self._physical_serial,
            target_getter=lambda: self._virtual_serial,
            direction="RX",
            source_name=self.physical_port,
            target_name=self.virtual_port,
        )

    def _copy_loop(self, source_getter, target_getter, direction: str, source_name: str, target_name: str) -> None:
        capture_buffer = bytearray()
        capture_started_at: float | None = None
        capture_wall_time = ""
        last_capture_at: float | None = None

        while not self._stop_event.is_set():
            source = source_getter()
            target = target_getter()
            if source is None or target is None:
                self._emit_capture_buffer(capture_buffer, capture_started_at, capture_wall_time, direction)
                self._stop_event.set()
                return

            try:
                bytes_waiting = source.in_waiting
                read_size = min(bytes_waiting or 1, 4096)
                data = source.read(read_size)
                if data:
                    target.write(data)
                    now = time.monotonic()
                    if not capture_buffer:
                        capture_started_at = now
                        capture_wall_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    capture_buffer.extend(data)
                    last_capture_at = now

                    capture_started_at, capture_wall_time = self._emit_complete_capture_messages(
                        capture_buffer,
                        capture_started_at,
                        capture_wall_time,
                        direction,
                    )
                    if not capture_buffer:
                        capture_started_at = None
                        capture_wall_time = ""
                        last_capture_at = None
                    elif len(capture_buffer) >= self.MAX_CAPTURE_BUFFER_SIZE:
                        self._emit_capture_buffer(capture_buffer, capture_started_at, capture_wall_time, direction)
                        capture_started_at = None
                        capture_wall_time = ""
                        last_capture_at = None
                elif (
                    capture_buffer
                    and last_capture_at is not None
                    and time.monotonic() - last_capture_at >= self.CAPTURE_IDLE_FLUSH_SECONDS
                ):
                    self._emit_capture_buffer(capture_buffer, capture_started_at, capture_wall_time, direction)
                    capture_started_at = None
                    capture_wall_time = ""
                    last_capture_at = None
            except SerialException as exc:
                self._emit_capture_buffer(capture_buffer, capture_started_at, capture_wall_time, direction)
                if not self._stop_event.is_set():
                    self.error_occurred.emit(
                        f"Serial connection lost while forwarding {source_name} â†’ {target_name}: "
                        f"{self._format_serial_error(exc)}"
                    )
                self._stop_event.set()
                return
            except OSError as exc:
                self._emit_capture_buffer(capture_buffer, capture_started_at, capture_wall_time, direction)
                if not self._stop_event.is_set():
                    self.error_occurred.emit(f"Port disconnected while reading {source_name}: {exc}")
                self._stop_event.set()
                return
            except Exception as exc:
                self._emit_capture_buffer(capture_buffer, capture_started_at, capture_wall_time, direction)
                if not self._stop_event.is_set():
                    self.error_occurred.emit(f"Unexpected bridge error on {source_name}: {exc}")
                self._stop_event.set()
                return

        self._emit_capture_buffer(capture_buffer, capture_started_at, capture_wall_time, direction)

    def _emit_complete_capture_messages(
        self,
        capture_buffer: bytearray,
        capture_started_at: float | None,
        capture_wall_time: str,
        direction: str,
    ) -> tuple[float | None, str]:
        while True:
            newline_index = capture_buffer.find(b"\n")
            if newline_index < 0:
                return capture_started_at, capture_wall_time

            raw = bytes(capture_buffer[: newline_index + 1])
            del capture_buffer[: newline_index + 1]
            self._emit_packet(capture_started_at, capture_wall_time, direction, raw)

            if capture_buffer:
                capture_started_at = time.monotonic()
                capture_wall_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            else:
                capture_started_at = None
                capture_wall_time = ""

    def _emit_capture_buffer(
        self,
        capture_buffer: bytearray,
        capture_started_at: float | None,
        capture_wall_time: str,
        direction: str,
    ) -> None:
        if not capture_buffer:
            return
        raw = bytes(capture_buffer)
        capture_buffer.clear()
        self._emit_packet(capture_started_at, capture_wall_time, direction, raw)

    def _emit_packet(
        self,
        timestamp: float | None,
        wall_time: str,
        direction: str,
        raw: bytes,
    ) -> None:
        packet = Packet(
            timestamp=timestamp if timestamp is not None else time.monotonic(),
            wall_time=wall_time or datetime.now().strftime("%H:%M:%S.%f")[:-3],
            direction=direction,
            raw=raw,
        )
        self.packet_ready.emit(packet)

    def _close_ports(self) -> None:
        for port in (self._virtual_serial, self._physical_serial):
            if port is None:
                continue
            try:
                if port.is_open:
                    port.close()
            except Exception:
                pass

    def _format_serial_error(self, exc: SerialException) -> str:
        message = str(exc)
        message_lower = message.lower()
        available_ports = ", ".join(port.device for port in list_ports.comports()) or "none"

        if "access is denied" in message_lower or "permission" in message_lower:
            return f"{message} Run SerialSniffer as administrator or close the application using the port."
        if "cannot find" in message_lower or "could not open port" in message_lower:
            return f"{message} Available ports: {available_ports}."
        if "in use" in message_lower or "permissionerror" in message_lower:
            return f"{message} The port may already be in use by another application."
        return f"{message} Available ports: {available_ports}."
