# SerialSniffer

SerialSniffer is a Windows desktop tool for capturing and forwarding serial traffic between an existing serial application and a real hardware device.

It is useful when you need to inspect RS-232/COM-port traffic without changing the software or device being tested.

## Features

- Bridges one virtual COM port to one physical COM port.
- Captures TX and RX traffic in a live packet table.
- Shows hex, printable ASCII, byte count, and packet timing.
- Groups normal CR/LF-ended ASCII messages into one displayed row, even when Windows or the serial driver delivers the bytes in smaller chunks.
- Includes a SCPI Commands panel for command-like ASCII traffic.
- Filters visible rows by TX/RX direction or hex/ASCII search text.
- Shows optional raw byte tooltips in decimal, hex, and binary.
- Exports the visible packet log to CSV.

Forwarded serial bytes are not modified. Display grouping only affects how captured rows appear in the UI and CSV export.

## Current Version

This source tree matches the V1.2-style build:

- SCPI Commands panel included.
- Line-based command grouping included.
- No special handling that separates `@` ACK bytes from following command text.

The built executable can be distributed separately through GitHub Releases.

## Requirements For Users

- Windows.
- A virtual COM pair provider such as com0com.
- The correct USB-to-serial driver for the physical device, if needed.
- A built `SerialSniffer.exe` from the Releases page.

End users do not need Python when using the packaged EXE.

## Typical Setup

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

## Run From Source

Install dependencies:

```bat
pip install -r requirements.txt
```

Run the app:

```bat
python main.py
```

## Build The EXE

From this folder:

```bat
build.bat
```

The default build output is:

```text
dist\SerialSniffer.exe
```

For versioned releases, rename the generated EXE, for example:

```text
dist\SerialSniffer_V1.2.exe
```

## GitHub Release Workflow

Keep source code in Git. Upload built EXE files to GitHub Releases instead of committing them to the repository.

Suggested release flow:

```bat
git add .
git commit -m "Release SerialSniffer v1.2 source"
git tag v1.2
git push
git push --tags
```

Then create a GitHub Release for tag `v1.2` and upload `dist\SerialSniffer_V1.2.exe` as the release asset.

## Documentation

- `USER_GUIDE.md`: setup and usage instructions.
- `SETUP.md`: developer setup and build notes.
- `DEVELOPER_DOC.md`: architecture and manual test checklist.
