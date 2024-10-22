from playwright.sync_api import sync_playwright
import requests
import logging
import re
import os
import sys
import tempfile
import time
import random
def setup_logging():
    try:
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, use the temporary directory
            log_dir = tempfile.gettempdir()
        else:
            # If the application is run from a Python interpreter, use the script's directory
            log_dir = os.path.dirname(os.path.abspath(__file__))
        
        log_path = os.path.join(log_dir, 'instagram_processor.log')
        logging.basicConfig(
            filename=log_path,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info(f"Logging initialized. Log file: {log_path}")
    except Exception as e:
        print(f"Failed to set up logging: {str(e)}")

setup_logging()

def extract_instagram_shortcode(url):
    logging.debug(f"Extracting shortcode from URL: {url}")
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?instagram\.com(?:\/p\/|\/tv\/|\/reel\/|\/reels\/|\/stories\/[^\/]+\/)([^\/?]+)',
        r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/([^\/]+)\/(?:p|tv|reel)\/([^\/?]+)',
        r'(?:https?:\/\/)?(?:www\.)?instagr\.am\/p\/([^\/?]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            shortcode = match.group(2) if len(match.groups()) > 1 else match.group(1)
            logging.debug(f"Shortcode extracted: {shortcode}")
            return shortcode
    
    logging.error(f"Could not extract shortcode from the URL: {url}")
    raise ValueError("Could not extract shortcode from the provided URL")

def get_instagram_video_url(post_url):
    logging.info(f"Attempting to get video URL for post: {post_url}")
    with sync_playwright() as p:
        try:
            browser_path = os.path.join(tempfile.gettempdir(), 'playwright_browsers', 'chromium-1134', 'chrome-win', 'chrome.exe')
            browser = p.chromium.launch(executable_path=browser_path)
            logging.debug("Chromium browser launched")
            context = browser.new_context()
            page = context.new_page()
            
            logging.debug(f"Navigating to page: {post_url}")
            page.goto(post_url, wait_until="networkidle")
            logging.debug("Page loaded, waiting for video element")
            video_element = page.wait_for_selector('video', state='attached', timeout=20000)
            if not video_element:
                logging.error("Video element not found on the page")
                raise ValueError("Video element not found on the page")
            
            video_url = video_element.get_attribute('src')
            if not video_url:
                logging.debug("Video URL not found in video element, searching in page content")
                content = page.content()
                video_url_match = re.search(r'"video_url":"([^"]+)"', content)
                if video_url_match:
                    video_url = video_url_match.group(1).replace('\\u0026', '&')
                else:
                    logging.error("Video URL not found in video element or page content")
                    raise ValueError("Video URL not found in video element or page content")
            
            logging.info(f"Video URL extracted successfully: {video_url}")
            return video_url
        except Exception as e:
            logging.error(f"Failed to extract video URL: {str(e)}", exc_info=True)
            raise
        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()


def process_instagram_video(url, save_path):
    logging.info(f"Attempting to download Instagram video from {url} to {save_path}")
    try:
        video_url = get_instagram_video_url(url)
        logging.debug(f"Sending GET request to video URL: {video_url}")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        logging.debug(f"Response status code: {response.status_code}")
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            logging.info(f"Instagram video downloaded successfully to {save_path}")
            return save_path
        else:
            logging.error(f"Downloaded file is empty or does not exist: {save_path}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error while downloading video: {str(e)}", exc_info=True)
        return None
    except IOError as e:
        logging.error(f"IO error while saving video: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logging.error(f"Unexpected error while processing Instagram video: {str(e)}", exc_info=True)
        return None


