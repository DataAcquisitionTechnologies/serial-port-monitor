# SerialSniffer User Guide

SerialSniffer is a Windows desktop tool for capturing and forwarding serial traffic between an existing serial application and a real hardware device.

You can use either build:

- Version 1 without SCPI viewer: shows the full packet log only.
- Version 1 with SCPI viewer: shows the full packet log plus a separate SCPI command list on the main screen.

If you receive `SerialSniffer.exe`, you do not need to install Python or any Python packages.

## What You Need

- Windows PC.
- `SerialSniffer.exe`.
- A physical serial device, usually exposed as a COM port such as `COM3`.
- The correct USB-to-serial driver for your adapter or instrument, if Windows does not install it automatically.
- A virtual serial port pair created with com0com.

Common USB-to-serial chip drivers include FTDI, Silicon Labs CP210x, WCH CH340/CH341, and Prolific. Install the driver that matches your adapter or instrument.

## Install com0com

SerialSniffer sits between two COM ports:

```text
Your existing software <-> Virtual COM port <-> SerialSniffer <-> Physical COM port <-> Hardware device
```

To create the virtual COM port side, install com0com.

1. Download a signed com0com build.
   - Official support/download page: https://com0com.com/download/
   - SourceForge project page: https://sourceforge.net/projects/com0com/
2. Run the installer as Administrator.
3. Install the virtual serial port driver when Windows asks for permission.
4. Open the com0com setup utility.
5. Create one virtual COM pair, for example:

   ```text
   COM7 <-> COM8
   ```

6. Open Windows Device Manager and confirm the new COM ports appear under `Ports (COM & LPT)`.

Use normal COM names like `COM7` and `COM8`. If a tool shows internal names like `CNCA0` or `CNCB0`, rename them to COM names in the com0com setup utility.

## Typical Connection Setup

Example:

- Your instrument is connected to Windows as `COM3`.
- com0com creates `COM7` and `COM8`.
- Your existing control software will connect to `COM8`.
- SerialSniffer will bridge `COM7` to `COM3`.

The data path becomes:

```text
Control software on COM8
    <-> com0com virtual pair
SerialSniffer on COM7
    <-> Physical device on COM3
```

## Start Capturing

1. Close any application that is already using the physical COM port.
2. Start `SerialSniffer.exe`.
3. Click the refresh button if the COM ports are not listed.
4. Select the virtual COM port in `Virtual Port`.
   - In the example above, select `COM7`.
5. Select the real device port in `Physical Port`.
   - In the example above, select `COM3`.
6. Match the serial settings used by the device:
   - Baud rate
   - Data bits
   - Parity
   - Stop bits
7. Click `Start`.
8. Open your existing control software and connect it to the other side of the virtual pair.
   - In the example above, connect it to `COM8`.

When traffic starts, rows appear in the packet log.

## Reading The Packet Log

The main packet log is available in both versions.

- `#`: packet number.
- `Time`: local time when the packet was captured.
- `Dir`: direction.
  - `TX`: traffic from the virtual port toward the physical device.
  - `RX`: traffic from the physical device back toward the virtual port.
- `Hex Data`: captured bytes in hexadecimal.
- `ASCII`: printable text version of the bytes.
- `Bytes`: number of bytes in the packet.
- `Delta (ms)`: time since the previous packet.

For line-based ASCII traffic, SerialSniffer groups bytes until a line ending such as CR/LF is received. This keeps responses like `Command Error! Please retry!` on one row even if the serial driver delivered the bytes in smaller chunks. The forwarded serial data is not modified.

Use the filter box to search visible packets by hex or ASCII text.

Use the checkboxes to show or hide TX and RX rows.

Enable `Show Raw Bytes` if you want detailed byte values in row tooltips.

## SCPI Commands Viewer

This section applies only to Version 1 with SCPI viewer.

The SCPI viewer appears below the packet log on the main screen. It extracts readable ASCII command-like messages from the captured serial data and lists them separately.

It shows:

- `#`: SCPI command number.
- `Time`: local time when the packet was captured.
- `Dir`: TX or RX.
- `Command`: extracted command text.

Examples of commands that may appear:

```text
*IDN?
:MEAS:VOLT?
VOLT 5
INIT
```

The SCPI viewer is only a convenience view. The complete raw capture is still preserved in the packet log above it.

If the device protocol is binary, compressed, encrypted, or not SCPI-like ASCII text, the SCPI viewer may show little or nothing.

## Export Capture

Click `Export Capture to CSV` to save the visible packet capture to a CSV file.

The exported CSV contains the packet log columns. The SCPI viewer is currently for live viewing on the main screen and is not exported separately.

## Stop And Clear

- Click `Stop` before disconnecting devices or changing port settings.
- Click `Clear Log` to clear the packet log and, in the SCPI build, the SCPI viewer.

## Troubleshooting

### Port does not appear

- Click refresh.
- Check Device Manager.
- Reconnect the USB serial adapter or instrument.
- Install the correct USB-to-serial driver.
- Reinstall or repair com0com if the virtual pair is missing.

### Access is denied

Another application is already using that COM port.

- Close other serial tools, terminals, and control software.
- Run SerialSniffer as Administrator if needed.
- Make sure the control software is connected to the other side of the com0com pair, not the same virtual COM port selected in SerialSniffer.

### No data appears

- Confirm the control software is connected to the opposite virtual COM port.
- Confirm SerialSniffer is bridging one virtual COM port to the physical hardware COM port.
- Confirm baud rate, data bits, parity, and stop bits match the device.
- Confirm the hardware is powered and connected.

### Device does not respond

- Stop the capture.
- Swap which side of the com0com pair is used by SerialSniffer and the control software.
- Check serial settings.
- Check whether the device requires hardware flow control. SerialSniffer currently exposes baud rate, data bits, parity, and stop bits in the UI.

### SCPI viewer is empty

- Check the packet log first. If the packet log has data, capture is working.
- The traffic may not be SCPI or may be binary.
- The command may not end with a normal CR/LF line ending, or it may not look like a SCPI-style ASCII command.
