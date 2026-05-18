from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


STYLE_SHEET = """
* {
    font-family: "Segoe UI";
    font-size: 10pt;
    color: #d4d4d4;
}
QMainWindow, QWidget {
    background-color: #1e1e1e;
}
QFrame#configFrame, QFrame#actionFrame, QFrame#scpiViewerFrame {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
}
QLabel#scpiViewerTitle {
    font-weight: 600;
}
QLineEdit, QComboBox {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #094771;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #569cd6;
}
QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #373737;
    border-color: #569cd6;
}
QPushButton:disabled {
    color: #858585;
    background-color: #252526;
}
QPushButton#startButton {
    background-color: #0e5a4f;
    border-color: #4ec9b0;
}
QPushButton#stopButton {
    background-color: #6e2424;
    border-color: #f44747;
}
QCheckBox {
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QCheckBox::indicator:unchecked {
    background-color: #252526;
    border: 1px solid #3c3c3c;
}
QCheckBox::indicator:checked {
    background-color: #569cd6;
    border: 1px solid #569cd6;
}
QTableWidget {
    background-color: #252526;
    alternate-background-color: #2d2d2d;
    gridline-color: #3c3c3c;
    border: 1px solid #3c3c3c;
    selection-background-color: #094771;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #1e1e1e;
    border: 1px solid #3c3c3c;
    padding: 5px;
    color: #d4d4d4;
}
QTableCornerButton::section {
    background-color: #1e1e1e;
    border: 1px solid #3c3c3c;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: #1e1e1e;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #3c3c3c;
    border-radius: 4px;
    min-height: 24px;
    min-width: 24px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #569cd6;
}
QScrollBar::add-line, QScrollBar::sub-line {
    width: 0;
    height: 0;
}
QStatusBar {
    background-color: #252526;
    color: #d4d4d4;
}
QToolTip {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
}
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("SerialSniffer")
    app.setOrganizationName("InternalTools")
    app.setStyleSheet(STYLE_SHEET)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
