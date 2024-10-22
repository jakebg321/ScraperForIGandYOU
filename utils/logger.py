import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger('InstagramProcessor')
    logger.setLevel(logging.DEBUG)
    
    # Create a rotating file handler
    handler = RotatingFileHandler('instagram_processor.log', maxBytes=5*1024*1024, backupCount=2)
    handler.setLevel(logging.DEBUG)
    
    # Formatter for logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Adding handler to the logger
    if not logger.hasHandlers():
        logger.addHandler(handler)
    
    return logger