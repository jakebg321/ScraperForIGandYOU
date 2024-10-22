import os
import logging
import tempfile
import requests
import zipfile
from pathlib import Path
import json
from PyQt5.QtWidgets import QProgressDialog, QApplication
from PyQt5.QtCore import Qt

class SetupManager:
    def __init__(self):
        self.logger = logging.getLogger('InstagramProcessor.SetupManager')
        self.playwright_path = os.path.join(tempfile.gettempdir(), 'playwright_browsers')
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self.playwright_path
        self.chromium_version = "1134"
        
        # Create config directory in user's home folder
        self.config_dir = os.path.join(str(Path.home()), '.instagram_processor')
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.config_file = os.path.join(self.config_dir, 'config.json')

    def setup_playwright(self):
        self.logger.info("Starting Playwright setup...")
        
        if self.check_playwright_browsers():
            self.logger.info("Playwright browsers already installed.")
            return True
            
        return self.download_playwright_browsers()

    def check_playwright_browsers(self):
        # Check if browser is installed and verified
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                if config.get('browser_installed'):
                    browser_path = os.path.join(
                        self.playwright_path, 
                        f'chromium-{self.chromium_version}', 
                        'chrome-win', 
                        'chrome.exe'
                    )
                    if os.path.exists(browser_path):
                        return True
        return False

    def download_playwright_browsers(self):
        try:
            progress_dialog = QProgressDialog("Downloading browser...", "Cancel", 0, 100)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setWindowTitle("First-time Setup")
            
            # URL for the Chromium browser package
            url = f"https://playwright.azureedge.net/builds/chromium/{self.chromium_version}/chromium-win64.zip"
            
            # Download with progress
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded = 0
            
            zip_path = os.path.join(tempfile.gettempdir(), "chromium-win64.zip")
            
            with open(zip_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    progress = int((downloaded / total_size) * 100)
                    progress_dialog.setValue(progress)
                    
                    if progress_dialog.wasCanceled():
                        return False

            progress_dialog.setLabelText("Extracting browser...")
            extract_path = os.path.join(self.playwright_path, f'chromium-{self.chromium_version}')
            os.makedirs(extract_path, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # Clean up
            os.remove(zip_path)
            
            # Save installation status
            with open(self.config_file, 'w') as f:
                json.dump({'browser_installed': True}, f)

            progress_dialog.setValue(100)
            self.logger.info("Playwright browsers installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download and install Playwright browsers: {str(e)}")
            return False