import sys
import configparser
import logging
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                              QPushButton, QTextEdit, QLineEdit, QCheckBox, QLabel,
                              QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QThread, Signal
from crawler import SiteCrawler
from auth import AuthManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class CrawlerThread(QThread):
    """Thread to run SiteCrawler and emit signals for GUI updates."""
    new_posts_signal = Signal(list)
    status_signal = Signal(str)

    def __init__(self, config_path='config.ini'):
        super().__init__()
        self.crawler = None
        self.config_path = config_path

    def run(self):
        """Run the SiteCrawler."""
        self.crawler = SiteCrawler(
            config_path=self.config_path,
            on_new_callback=self.on_new_posts,
            on_status_callback=self.on_status
        )
        self.crawler.join()

    def on_new_posts(self, posts):
        """Emit new posts signal."""
        self.new_posts_signal.emit(posts)

    def on_status(self, message):
        """Emit status signal."""
        self.status_signal.emit(message)

    def stop(self):
        """Stop the crawler and ensure cleanup."""
        if self.crawler:
            self.crawler.stop()
            self.crawler.join()  # Wait for crawler to fully stop
        self.quit()  # Stop the QThread

from export import DataExporter

class MainWindow(QMainWindow):
    """Main GUI window for JOBKOREA crawler."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JOBKOREA Crawler")
        self.setGeometry(100, 100, 900, 650)
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.auth = AuthManager(config_path='config.ini')
        self.crawler_thread = None
        self.logger = logging.getLogger(__name__)
        self.all_posts = []  # Store cumulative list of posts
        self.post_ids = set()  # Track post IDs to avoid duplicates

        # Set up tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Initialize tabs
        self.setup_crawling_tab()
        self.setup_settings_tab()
        self.setup_logs_tab()
        self.exporter = DataExporter(self.config.get('crawling', 'output_folder', fallback='output'))

        # Apply modern dark theme stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c2f33, stop:1 #23272a);
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #3a3f44;
                background: #2c2f33;
                border-radius: 10px;
            }
            QTabBar::tab {
                background: #3a3f44;
                color: #b0b3b8;
                padding: 14px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #5865f2;
                color: #ffffff;
                border-bottom: 3px solid #7289da;
            }
            QTabBar::tab:hover {
                background: #4a5056;
                color: #ffffff;
                transition: all 0.2s ease;
            }
            QPushButton {
                background-color: #5865f2;
                color: #ffffff;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #4752c4;
                transform: scale(1.02);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            QPushButton:pressed {
                background-color: #3e46a3;
                transform: scale(0.98);
            }
            QPushButton:disabled {
                background-color: #4a5056;
                color: #6c757d;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #3a3f44;
                border-radius: 8px;
                padding: 10px;
                background-color: #36393f;
                color: #e0e0e0;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #5865f2;
                background-color: #40444b;
            }
            QCheckBox {
                font-size: 14px;
                color: #b0b3b8;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3a3f44;
                border-radius: 4px;
                background-color: #36393f;
            }
            QCheckBox::indicator:checked {
                background-color: #5865f2;
                border: 1px solid #5865f2;
            }
            QLabel {
                font-size: 14px;
                color: #b0b3b8;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTableWidget {
                border: 1px solid #3a3f44;
                border-radius: 8px;
                background-color: #36393f;
                color: #e0e0e0;
                gridline-color: #3a3f44;
                selection-background-color: #4a5056;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:alternate {
                background-color: #2f3136;
            }
            QHeaderView::section {
                background-color: #3a3f44;
                color: #b0b3b8;
                padding: 10px;
                border: 1px solid #2c2f33;
                font-weight: 600;
                font-size: 14px;
            }
            QWidget#tabContent {
                background: #2c2f33;
                border-radius: 10px;
                padding: 20px;
                margin: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #2c2f33;
                border: none;
                border-radius: 4px;
            }
            QScrollBar::handle {
                background: #5865f2;
                border-radius: 4px;
            }
            QScrollBar::handle:hover {
                background: #4752c4;
            }
        """)

    def setup_crawling_tab(self):
        """Set up the Crawling tab."""
        crawling_tab = QWidget()
        crawling_tab.setObjectName("tabContent")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Start/Stop buttons
        self.start_button = QPushButton("Start Crawler")
        self.start_button.clicked.connect(self.start_crawler)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Crawler")
        self.stop_button.clicked.connect(self.stop_crawler)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        # Export button
        self.export_button = QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        layout.addWidget(self.export_button)

        # Status label
        self.status_label = QLabel("Status: Idle")
        layout.addWidget(self.status_label)

        # Table for crawled posts
        self.posts_table = QTableWidget()
        self.posts_table.setColumnCount(3)
        self.posts_table.setHorizontalHeaderLabels(["ID", "Title", "Company"])
        self.posts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.posts_table.setAlternatingRowColors(True)
        layout.addWidget(self.posts_table)

        crawling_tab.setLayout(layout)
        self.tabs.addTab(crawling_tab, "Crawling")

    def export_to_excel(self):
        """Export accumulated posts to Excel."""
        try:
            if not self.all_posts:
                self.logger.info("No posts to export")
                self.status_label.setText("Status: No posts to export")
                return

            output_path = self.exporter.export_to_excel(self.all_posts)
            self.logger.info(f"Exported posts to {output_path}")
            self.status_label.setText(f"Status: Exported to {output_path}")
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            self.status_label.setText(f"Status: Export failed - {str(e)}")

    def setup_settings_tab(self):
        """Set up the Settings tab."""
        settings_tab = QWidget()
        settings_tab.setObjectName("tabContent")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Headless mode
        self.headless_check = QCheckBox("Run in Headless Mode")
        self.headless_check.setChecked(self.config.getboolean('crawling', 'headless', fallback=True))
        layout.addWidget(self.headless_check)

        # Output folder
        layout.addWidget(QLabel("Output Folder:"))
        self.output_folder_input = QLineEdit(self.config.get('crawling', 'output_folder', fallback='output'))
        layout.addWidget(self.output_folder_input)

        # Save settings button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        layout.addStretch()  # Add stretch to push content up
        settings_tab.setLayout(layout)
        self.tabs.addTab(settings_tab, "Settings")

    def setup_logs_tab(self):
        """Set up the Logs tab."""
        logs_tab = QWidget()
        logs_tab.setObjectName("tabContent")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        # Load initial logs
        try:
            with open('crawler.log', 'r', encoding='utf-8') as f:
                self.log_display.setText(f.read())
        except FileNotFoundError:
            self.log_display.setText("No logs found.")

        logs_tab.setLayout(layout)
        self.tabs.addTab(logs_tab, "Logs")

    def start_crawler(self):
        """Start the crawler in a background thread."""
        try:
            # Verify login
            driver = self.auth.login()
            driver.quit()  # Close test driver
            self.logger.info("Login verified, starting crawler")

            # Start crawler thread
            self.crawler_thread = CrawlerThread(config_path='config.ini')
            self.crawler_thread.new_posts_signal.connect(self.update_posts)
            self.crawler_thread.status_signal.connect(self.update_status)
            self.crawler_thread.start()

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Status: Crawling")
        except Exception as e:
            self.logger.error(f"Failed to start crawler: {e}")
            self.status_label.setText(f"Status: Error - {str(e)}")

    def stop_crawler(self):
        """Stop the crawler."""
        try:
            if self.crawler_thread:
                self.crawler_thread.stop()
                self.crawler_thread.wait()  # Wait for thread to terminate
                self.crawler_thread = None
                self.logger.info("Crawler thread stopped successfully")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Status: Stopped")
        except Exception as e:
            self.logger.error(f"Error stopping crawler: {e}")
            self.status_label.setText(f"Status: Error stopping crawler - {str(e)}")

    def update_posts(self, posts):
        """Append new posts to the table, preserving existing posts."""
        # Filter out duplicates based on post ID
        new_posts = [post for post in posts if post['id'] not in self.post_ids]
        if not new_posts:
            self.logger.info("No new unique posts to append")
            return

        # Add new posts to cumulative list and ID set
        self.all_posts.extend(new_posts)
        for post in new_posts:
            self.post_ids.add(post['id'])

        # Update table with all posts
        self.posts_table.setRowCount(len(self.all_posts))
        for i, post in enumerate(self.all_posts):
            self.posts_table.setItem(i, 0, QTableWidgetItem(post['id']))
            self.posts_table.setItem(i, 1, QTableWidgetItem(post['title']))
            self.posts_table.setItem(i, 2, QTableWidgetItem(post['company']))

        self.logger.info(f"Appended {len(new_posts)} new posts to GUI (total: {len(self.all_posts)})")

    def update_status(self, message):
        """Update the status label and logs."""
        self.status_label.setText(f"Status: {message}")
        try:
            with open('crawler.log', 'r', encoding='utf-8') as f:
                self.log_display.setText(f.read())
        except FileNotFoundError:
            self.log_display.setText("No logs found.")
        self.logger.info(f"Status updated: {message}")

    def save_settings(self):
        """Save settings to config.ini."""
        try:
            self.config['crawling'] = {
                'headless': str(self.headless_check.isChecked()),
                'output_folder': self.output_folder_input.text()
            }
            with open('config.ini', 'w') as f:
                self.config.write(f)
            self.logger.info("Settings saved to config.ini")
            self.status_label.setText("Status: Settings saved")
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            self.status_label.setText(f"Status: Error saving settings - {str(e)}")

    def closeEvent(self, event):
        """Handle window close event."""
        try:
            if self.crawler_thread:
                self.crawler_thread.stop()
                self.crawler_thread.wait()
            self.auth.close()
            self.logger.info("Application closed")
        except Exception as e:
            self.logger.error(f"Error closing application: {e}")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())