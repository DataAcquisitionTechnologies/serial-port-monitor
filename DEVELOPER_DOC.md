# SerialSniffer Developer Documentation

SerialSniffer is a PySide6 desktop application that bridges serial traffic between a virtual COM port and a physical COM port while displaying captured packets in real time.

The project currently has two practical variants:

- Version 1 without SCPI viewer: main packet capture table only.
- Version 1 with SCPI viewer: main packet capture table plus `ui/scpi_commands_viewer.py` embedded below the log table.

## Runtime Behavior

The app is intended to be placed between existing control software and hardware:

```text
Control software
    <-> com0com virtual pair
SerialSniffer
    <-> Physical serial device
```

Example:

```text
Control software: COM8
SerialSniffer virtual port: COM7
SerialSniffer physical port: COM3
Device: COM3
```

The app opens both selected ports and forwards bytes in both directions:

- `TX`: virtual port to physical port.
- `RX`: physical port to virtual port.

Forwarding happens immediately for every byte chunk read from the source port. Capture display is buffered separately: line-based ASCII traffic is grouped until a `\n` byte is seen, with a short idle flush for traffic that does not include a line ending. This keeps commands such as `Command Error! Please retry!\r\n` on one packet-log row without changing or delaying the bytes written to the target port.

## Source Layout

```text
serial_sniffer/
  main.py
  requirements.txt
  build.bat
  SETUP.md
  USER_GUIDE.md
  DEVELOPER_DOC.md
  core/
    bridge.py
    exporter.py
    packet.py
  ui/
    main_window.py
    log_table.py
    scpi_commands_viewer.py
```

## Key Modules

### `main.py`

Creates the `QApplication`, applies the global dark stylesheet, creates `MainWindow`, and starts the Qt event loop.

### `ui/main_window.py`

Owns the main UI and user workflow:

- COM port selection.
- Serial settings.
- Start and stop actions.
- Filtering controls.
- Capture log.
- CSV export.
- Status labels.
- SCPI viewer integration in the SCPI-enabled build.

`MainWindow.on_packet_ready()` is the fan-out point for received packets. It updates the log table, SCPI viewer, packet count, byte count, and active filters.

### `ui/log_table.py`

Displays all captured packets in a `QTableWidget`.

It supports:

- Hex and ASCII display.
- TX/RX coloring.
- Filtering by direction and search text.
- Copy selected rows.
- Raw byte tooltips.
- CSV export for visible rows.
- Automatic row trimming after `MAX_ROWS`.

### `ui/scpi_commands_viewer.py`

SCPI-enabled build only.

Displays a secondary live table of SCPI-like ASCII commands extracted from packets.

The viewer:

- Decodes packet bytes as ASCII with invalid bytes ignored.
- Removes STX/ETX framing bytes.
- Splits commands on CR/LF.
- Keeps printable command-like text that starts with a letter or `*`.
- Displays direction, timestamp, and command text.
- Supports copy selected rows.
- Trims old rows after `MAX_ROWS`.

This is a live convenience view. It does not replace the raw packet log.

### `core/bridge.py`

Contains `SerialBridge`, a `QThread` that owns serial forwarding.

Responsibilities:

- Open virtual and physical serial ports.
- Start one reader thread per direction.
- Forward bytes from source to target.
- Buffer captured display rows until line endings, idle timeout, or the safety buffer limit.
- Emit `Packet` objects to the UI.
- Emit user-readable error/status messages.
- Close serial ports on stop or failure.

The bridge uses `pyserial` for serial I/O and Qt signals for UI communication.

### `core/packet.py`

Defines the `Packet` dataclass:

- `timestamp`
- `wall_time`
- `direction`
- `raw`

Computed properties provide:

- `hex_str`
- `ascii_str`
- `byte_count`

### `core/exporter.py`

Contains an older standalone CSV export helper. The current UI exports directly from `LogTable.export_to_csv()`.

## Dependencies

Python dependencies are listed in `requirements.txt`:

```text
PySide6>=6.6.0
pyserial>=3.5
pyinstaller>=6.0
```

End users who receive the built `SerialSniffer.exe` do not need these Python packages.

Windows users still need:

- A virtual COM pair provider, usually com0com.
- Device-specific USB-to-serial drivers if the physical instrument or adapter needs them.

Useful com0com pages:

- https://com0com.com/download/
- https://sourceforge.net/projects/com0com/

## Run From Source

Install dependencies:

```bat
pip install -r requirements.txt
```

Run:

```bat
python main.py
```

## Build The EXE

Use the existing build script:

```bat
build.bat
```

It installs Python dependencies and runs PyInstaller:

```bat
pyinstaller --noconsole --onefile --name SerialSniffer --windowed main.py
```

The output is:

```text
dist\SerialSniffer.exe
```

Share this EXE with users together with `USER_GUIDE.md`.

## Releasing The Two Variants

For a Version 1 build without SCPI viewer, use the codebase before the SCPI viewer integration or remove these integration points:

- `from ui.scpi_commands_viewer import ScpiCommandsViewer`
- `self.scpi_viewer = ScpiCommandsViewer()`
- the `QSplitter` section that embeds the SCPI viewer
- `self.scpi_viewer.add_packet(packet)`
- `self.scpi_viewer.clear_all()`
- the `scpiViewerFrame` and `scpiViewerTitle` stylesheet selectors

For a Version 1 build with SCPI viewer, build the current codebase.

Recommended output naming:

```text
SerialSniffer-v1.exe
SerialSniffer-v1-scpi.exe
```

## Manual Test Checklist

Before sharing a build:

1. Install or confirm com0com virtual pair exists.
2. Confirm the physical device appears in Device Manager.
3. Start the app.
4. Refresh ports.
5. Select one virtual COM port and one physical COM port.
6. Use the device's correct serial settings.
7. Click `Start`.
8. Connect the existing control software to the other side of the virtual COM pair.
9. Confirm TX and RX rows appear in the packet log.
10. Confirm filtering works.
11. Confirm `Show Raw Bytes` tooltips work.
12. Export a CSV and open it.
13. For the SCPI build, confirm SCPI-like ASCII commands appear in the lower viewer.
14. Click `Stop`, then close the app cleanly.

## Known Limitations

- Hardware flow control is not exposed in the UI.
- CSV export covers the packet log, not a separate SCPI command export.
- SCPI extraction is best-effort. Normal CR/LF-ended commands are grouped before extraction, but unusual protocols without line endings may still be shown by idle-time chunks.
- Binary protocols are fully visible in the packet log but may not produce SCPI viewer entries.
