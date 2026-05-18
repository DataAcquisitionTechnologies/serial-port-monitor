# SerialSniffer Setup

1. Install com0com and create a virtual COM pair, for example `COM7` and `COM8`.
2. Connect the external software to one side of the virtual pair, then select that virtual port in SerialSniffer.
3. Connect the hardware device to the physical COM port, for example `COM3`, then select that physical port in SerialSniffer.
4. Install Python dependencies:

   ```bat
   pip install -r requirements.txt
   ```

5. Run from source:

   ```bat
   python main.py
   ```

6. Build a single Windows executable:

   ```bat
   build.bat
   ```

The built executable is created at `dist\SerialSniffer.exe`.
