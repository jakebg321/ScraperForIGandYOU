import sys
import logging
from PyQt5 import QtWidgets
from logger import setup_logger
from playwright_setup import SetupManager
from video_processor_app import VideoProcessorApp

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = setup_logger()
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
