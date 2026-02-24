"""
COMTRADE Analysis Tool - Main Application Entry Point
======================================================

This is the main entry point for the COMTRADE Analysis desktop application.
Run this file to launch the application.

Usage:
    python main.py
    
Or after packaging with PyInstaller:
    COMTRADEAnalysisTool.exe
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow


def main():
    """
    Main application entry point.
    
    Initializes Qt application and displays main window.
    """
    # Enable high DPI scaling for modern displays
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("COMTRADE Analysis Tool")
    app.setOrganizationName("Power Systems Protection Engineering")
    app.setApplicationVersion("1.0.0")
    
    # Set application style (optional - system default is fine)
    # app.setStyle('Fusion')
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    # Execute application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
