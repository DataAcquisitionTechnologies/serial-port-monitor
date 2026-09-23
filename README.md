# SerialSniffer

[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)](https://github.com/jay-raskar10/serial-port-monitor)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![Release](https://img.shields.io/badge/Release-v1.2-orange.svg)](https://github.com/jay-raskar10/serial-port-monitor/releases)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

**SerialSniffer** is a Windows desktop application for non-intrusively capturing, monitoring, and forwarding serial (RS-232 / UART / COM port) communications between third-party PC control software and real physical hardware devices.

It bridges a virtual COM port (provided by [com0com](https://sourceforge.net/projects/com0com/)) to a physical COM port in real time, displaying all bidirectional packets without altering byte streams or introducing transmission lag.

---

## 🌟 Key Features

- **Transparent Bidirectional Forwarding**:
  - `TX`: Virtual COM $\to$ Physical COM (Commands from software to hardware).
  - `RX`: Physical COM $\to$ Virtual COM (Telemetry/Responses from hardware to software).
  - Forwarding executes immediately on raw byte chunks with zero modification.

- **Intelligent ASCII & SCPI Line Grouping**:
  - Groups fragmented serial frames into clean, single-line log entries when terminated by `\r\n` or `\n`.
  - Employs a 100 ms idle flush timer to display non-terminated binary frames or partial ASCII bursts cleanly without breaking line integrity.

- **Dual-Pane Real-Time Inspection**:
  - **Live Packet Log**: Shows Timestamp, Direction (`TX` / `RX`), Byte Count, Hexadecimal dump, and printable ASCII representation.
  - **SCPI Commands Panel**: Dedicated lower pane that isolates and catalogs SCPI and ASCII query/response commands.

- **Real-Time Filtering & Search**:
  - Filter by traffic direction: `All`, `TX Only`, or `RX Only`.
  - Instant text filter supporting ASCII text search and Hex pattern matching.

- **Bitwise Byte Inspection**:
  - Optional raw byte tooltips display exact Decimal, Hexadecimal, and Binary (bitmask) values upon hovering over any cell.

- **Data Export**:
  - One-click export of captured packet tables directly to standard `.csv` for post-test analysis.

- **Persistent Configuration**:
  - Automatically remembers window geometry, selected baud rates, parity, data bits, and port selections across restarts via `QSettings`.

---

## 🏗️ Architecture & How It Works

SerialSniffer inserts itself seamlessly into the serial communication loop using a virtual null-modem pair:

```text
┌─────────────────────────────────┐
│     Existing Control Software   │ (LabVIEW, MATLAB, Custom App, Terminal)
└───────────────┬─────────────────┘
                │ Opens COM8
                ▼
┌─────────────────────────────────┐
│     com0com Virtual Pair        │
│          COM8 ◄──► COM7         │
└──────────────────┬──────────────┘
                   │ Opens COM7
                   ▼
┌─────────────────────────────────┐
│          SerialSniffer          │ <── Live Packet Logger & SCPI Analyzer
│     (Virtual ◄──► Physical)     │
└──────────────────┬──────────────┘
                   │ Opens COM3
                   ▼
┌─────────────────────────────────┐
│     Physical COM Port (COM3)    │ (FTDI, CP2102, CH340, Prolific USB-UART)
└──────────────────┬──────────────┘
                   │ RS-232 / TTL
                   ▼
┌─────────────────────────────────┐
│     Target Hardware Device      │ (Instrument, Microcontroller, PLC, Sensor)
└─────────────────────────────────┘
```

> **Note**: Forwarded bytes are delivered instantaneously. The internal buffering only affects the visual presentation in the GUI and exported CSV records.

---

## 📋 Requirements

### For End Users
- **Operating System**: Windows 10 / 11 (64-bit).
- **Virtual Port Driver**: [com0com](https://sourceforge.net/projects/com0com/) (Null-modem emulator for Windows).
- **Hardware Drivers**: USB-to-UART drivers (FTDI, Silicon Labs CP210x, WCH CH340, Prolific) appropriate for your hardware.
- **Application**: Pre-compiled `SerialSniffer.exe` from [GitHub Releases](https://github.com/jay-raskar10/serial-port-monitor/releases) *(no Python setup required)*.

### For Developers
- **Python**: 3.10 or newer.
- **Dependencies**: Listed in [`requirements.txt`](requirements.txt).

---

## 🚀 Quick Start

### Option 1: Run the Standalone Binary (Recommended)

1. Download the latest `SerialSniffer_V1.2.exe` from the [Releases](https://github.com/jay-raskar10/serial-port-monitor/releases) tab.
2. Launch the `.exe` directly.

### Option 2: Run from Source

1. **Clone the repository:**
   ```bat
   git clone https://github.com/jay-raskar10/serial-port-monitor.git
   cd serial-port-monitor
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bat
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```bat
   python main.py
   ```

---

## ⚙️ Step-by-Step Setup Guide

### 1. Configure com0com
1. Download a signed build of com0com ([com0com on SourceForge](https://sourceforge.net/projects/com0com/)).
2. Launch **Setup Command Prompt** or **Setup GUI** as Administrator.
3. Add a pair with standard COM names (e.g., `COM7` and `COM8`).
4. Verify in **Windows Device Manager** under `Ports (COM & LPT)` that both virtual ports are visible.

### 2. Connect Your Hardware
1. Plug your serial device into your PC. Note its COM port (e.g., `COM3`).

### 3. Start Monitoring
1. Configure your external control software to connect to **`COM8`**.
2. Open **SerialSniffer**:
   - **Virtual Port**: Select `COM7`.
   - **Physical Port**: Select `COM3`.
   - **Baud Rate & Parameters**: Match your hardware settings (e.g., `9600`, `8`, `None`, `1`).
3. Click **Start Sniffing** (or press `Ctrl+S`).
4. Connect the external control software to `COM8`. Traffic will immediately flow through and appear in the live table.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action | Description |
|:---|:---|:---|
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | **Start** | Start bridge and packet capture |
| <kbd>Ctrl</kbd> + <kbd>Q</kbd> | **Stop** | Stop bridge and release COM ports |
| <kbd>Ctrl</kbd> + <kbd>E</kbd> | **Export** | Export captured log to CSV file |
| <kbd>Ctrl</kbd> + <kbd>L</kbd> | **Clear** | Clear live packet and SCPI tables |
| <kbd>Ctrl</kbd> + <kbd>F</kbd> | **Search** | Jump focus to the Filter / Search bar |
| <kbd>Ctrl</kbd> + <kbd>C</kbd> | **Copy** | Copy selected row(s) or SCPI command text |

---

## 🛠️ Building the Standalone Executable

To compile a single-file executable using PyInstaller:

```bat
build.bat
```

The compiled binary will be produced in the `dist\` folder:
```text
dist\SerialSniffer.exe
```

---

## 📁 Repository Structure

```text
serial_sniffer/
├── core/
│   ├── bridge.py                # Bidirectional serial forwarding thread & buffer engine
│   ├── exporter.py              # CSV export formatting routines
│   └── packet.py                # Packet data model (hex/ASCII conversion, timing)
├── ui/
│   ├── log_table.py             # Main interactive packet table widget
│   ├── main_window.py           # Application window, toolbars, settings management
│   └── scpi_commands_viewer.py  # SCPI / ASCII protocol command extraction panel
├── build.bat                    # PyInstaller one-click build automation script
├── main.py                      # Application entry point and theme styling
├── requirements.txt             # Python runtime dependencies
├── SerialSniffer.spec           # PyInstaller build specification
├── DEVELOPER_DOC.md             # Developer architecture and test checklist
├── USER_GUIDE.md                # Comprehensive end-user operational manual
├── SETUP.md                     # Quick setup notes
└── .gitignore                   # Git exclusion rules
```

---

## 📚 Additional Documentation

- [User Guide](USER_GUIDE.md): In-depth instructions, com0com configuration tips, and troubleshooting common serial driver issues.
- [Developer Documentation](DEVELOPER_DOC.md): Architectural deep dive, threading model, and verification test checklists.
- [Setup Notes](SETUP.md): Quick setup instructions for developers and lab technicians.

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome!
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my-feature`).
3. Commit your changes (`git commit -m "Add my feature"`).
4. Push to the branch (`git push origin feature/my-feature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) (or your designated organizational license).
