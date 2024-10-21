import sys
import os
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import json
import tempfile
from PyQt5 import QtWidgets, QtGui, QtCore
import portalocker
import time
from playwright.sync_api import sync_playwright
import requests
import zipfile
import urllib
import glob

class SetupManager:
    def __init__(self):
        self.logger = logging.getLogger('InstagramProcessor.SetupManager')
        self.playwright_path = os.path.join(tempfile.gettempdir(), 'playwright_browsers')
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self.playwright_path
        self.chromium_version = "1134"  # Update this to match the version Playwright expects

    def setup_playwright(self):
        self.logger.info("Starting Playwright setup...")
        
        if self.check_playwright_browsers():
            self.logger.info("Playwright browsers already installed.")
            return True
        
        self.logger.info("Playwright browsers not found. Attempting to download...")
        return self.download_playwright_browsers()

    def check_playwright_browsers(self):
        expected_path = os.path.join(self.playwright_path, f'chromium-{self.chromium_version}', 'chrome-win', 'chrome.exe')
        return os.path.exists(expected_path)

    def download_playwright_browsers(self):
        try:
            # URL for the Chromium browser package
            url = f"https://playwright.azureedge.net/builds/chromium/{self.chromium_version}/chromium-win64.zip"
            
            # Download the zip file
            self.logger.info(f"Downloading Chromium from {url}")
            response = requests.get(url)
            if response.status_code != 200:
                self.logger.error(f"Failed to download Chromium: HTTP {response.status_code}")
                return False

            # Save and extract the zip file
            zip_path = os.path.join(tempfile.gettempdir(), "chromium-win64.zip")
            with open(zip_path, 'wb') as f:
                f.write(response.content)

            extract_path = os.path.join(self.playwright_path, f'chromium-{self.chromium_version}')
            self.logger.info(f"Extracting Chromium to {extract_path}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # Clean up the zip file
            os.remove(zip_path)

            self.logger.info("Playwright browsers installed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to download and install Playwright browsers: {str(e)}")
            return False

from youtube_processor import process_youtube_video, is_youtube_url
from instagram_processor import process_instagram_video
from processor import adjust_media

class WorkerThread(QtCore.QThread):
    progress_signal = QtCore.pyqtSignal(str, int)
    finished_signal = QtCore.pyqtSignal(str, str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.logger = logging.getLogger('InstagramProcessor.WorkerThread')

    def run(self):
        progress_messages = [
            "Starting download... Preparing the magic potion",
            "Breaking into Instagram... Distracting the guards",
            "Sneaking past YouTube algorithms...",
            "Mixing colors and adjusting brightness...",
        ]

        try:
            self.progress_signal.emit(progress_messages[0], 5)
            time.sleep(1)

            if is_youtube_url(self.url):
                self.progress_signal.emit(progress_messages[2], 20)
                time.sleep(1)
                downloaded_file = process_youtube_video(self.url, self.save_path)
            elif 'instagram.com' in self.url:
                self.progress_signal.emit(progress_messages[1], 20)
                time.sleep(1)
                downloaded_file = process_instagram_video(self.url, self.save_path)
            else:
                logging.error(f"Unsupported URL format: {self.url}")
                self.finished_signal.emit("error", "Unsupported URL format. Please enter a valid YouTube or Instagram URL.")
                return

            if downloaded_file:
                self.progress_signal.emit("Download complete. Processing video...", 40)
                output_filename = f"{os.path.splitext(os.path.basename(downloaded_file))[0]}_processed.mp4"
                processed_file, adjustments = adjust_media(downloaded_file, output_filename)
                if processed_file:
                    self.progress_signal.emit("Video processed successfully", 80)
                    time.sleep(1)
                    logging.info(f"Video processed successfully: {processed_file}")
                    adjustments_str = '\n'.join([f"{key}: {value}" for key, value in adjustments.items()])
                    self.finished_signal.emit("success", f"Video processed successfully and saved to: {processed_file}\nAdjustments made:\n{adjustments_str}")
                else:
                    logging.error("Failed to process the video")
                    self.finished_signal.emit("error", "Failed to process the video")
            else:
                logging.error("Failed to download the video")
                self.finished_signal.emit("error", "Failed to download the video")

            self.progress_signal.emit("Finalizing...", 100)
            time.sleep(1)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            self.finished_signal.emit("error", f"An error occurred: {e}")

class VideoProcessorApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Window Setup
        self.setWindowTitle('Video Processor YOU 2323233(YouTube & Instagram)')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #4B0082, stop:1 #8A2BE2);")

        # URL Label and Entry
        self.url_label = QtWidgets.QLabel('Enter YouTube or Instagram URL:', self)
        self.url_label.setFont(QtGui.QFont('Arial', 12))
        self.url_label.move(20, 20)
        self.url_label.setStyleSheet("color: white;")

        self.url_entry = QtWidgets.QLineEdit(self)
        self.url_entry.setFont(QtGui.QFont('Arial', 12))
        self.url_entry.setGeometry(20, 50, 740, 30)
        self.url_entry.setStyleSheet("border: 2px solid #8A2BE2; border-radius: 5px; padding: 5px; color: white;")

        # Process Button
        self.process_button = QtWidgets.QPushButton('Process Video', self)
        self.process_button.setFont(QtGui.QFont('Arial', 14, QtGui.QFont.Bold))
        self.process_button.setGeometry(310, 100, 180, 40)
        self.process_button.setStyleSheet("background-color: #6A0DAD; color: white; border-radius: 10px; padding: 10px;")
        self.process_button.clicked.connect(self.start_processing)

        # Progress Label
        self.progress_label = QtWidgets.QLabel('', self)
        self.progress_label.setFont(QtGui.QFont('Arial', 10))
        self.progress_label.setGeometry(20, 160, 740, 30)
        self.progress_label.setAlignment(QtCore.Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: white;")

        # Progress Bar
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setGeometry(20, 200, 740, 25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #6A0DAD;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #8A2BE2;
                width: 20px;
            }
        """)
        self.progress_bar.setValue(0)

    def start_processing(self):
        url = self.url_entry.text().strip()
        logging.info(f"Processing video from URL: {url}")
        if not url:
            logging.warning("No URL provided")
            QtWidgets.QMessageBox.critical(self, "Error", "Please enter a video URL")
            return

        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Video As", "downloaded_video.mp4", "MP4 Files (*.mp4)")
        logging.info(f"Save path selected: {save_path}")

        if not save_path:
            logging.warning("No save path selected")
            return

        # Create and start the worker thread
        self.worker_thread = WorkerThread(url, save_path)
        self.worker_thread.progress_signal.connect(self.update_progress)
        self.worker_thread.finished_signal.connect(self.processing_finished)
        self.worker_thread.start()

    def update_progress(self, message, value):
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)
        QtWidgets.QApplication.processEvents()

    def processing_finished(self, status, message):
        if status == "success":
            QtWidgets.QMessageBox.information(self, "Success", message)
        else:
            QtWidgets.QMessageBox.critical(self, "Error", message)
        self.progress_label.setText('')
        self.progress_bar.setValue(0)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('InstagramProcessor.Main')
    logger.info("Application starting")
    
    app = QtWidgets.QApplication(sys.argv)
    
    try:
        setup_manager = SetupManager()
        
        if setup_manager.setup_playwright():
            logger.info("Playwright setup successful, initializing main application")
            video_processor = VideoProcessorApp()
            video_processor.show()
            logger.info("Application GUI displayed, entering main event loop")
            exit_code = app.exec_()
            logger.info(f"Application exiting with code: {exit_code}")
            sys.exit(exit_code)
        else:
            logger.error("Playwright setup failed")
            QtWidgets.QMessageBox.critical(None, "Setup Error", 
                                           "Failed to set up required components. "
                                           "Please check the log file for more details.")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Unhandled exception in main: {e}")
        QtWidgets.QMessageBox.critical(None, "Unexpected Error", 
                                       f"An unexpected error occurred: {str(e)}\n"
                                       "Please check the log file for more details.")
        sys.exit(1)
