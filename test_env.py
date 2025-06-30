import sys
import importlib.metadata

try:
    from PySide6.QtWidgets import QApplication
    print("PySide6 installed successfully")
except ImportError:
    print("PySide6 not found")
try:
    import pandas
    print("Pandas installed successfully")
except ImportError:
    print("Pandas not found")
try:
    import openpyxl
    print("openpyxl installed successfully")
except ImportError:
    print("openpyxl not found")
try:
    importlib.metadata.version("pyinstaller")
    print("PyInstaller installed successfully")
except importlib.metadata.PackageNotFoundError:
    print("PyInstaller not found")
try:
    import playwright
    print("Playwright installed successfully")
except ImportError:
    print("Playwright not found")
try:
    import selenium
    import webdriver_manager
    print("Selenium and webdriver-manager installed successfully")
except ImportError:
    print("Selenium or webdriver-manager not found")
print(f"Python version: {sys.version}")
print("Library check complete.")