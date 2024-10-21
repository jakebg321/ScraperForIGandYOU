import logging
import os
import re
from urllib.parse import parse_qs, urlparse
import json
from playwright.sync_api import sync_playwright
import yt_dlp

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def is_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
    return re.match(youtube_regex, url) is not None

def extract_video_id(url):
    query = urlparse(url).query
    params = parse_qs(query)
    if 'v' in params:
        return params['v'][0]
    path = urlparse(url).path
    if path.startswith('/shorts/'):
        return path.split('/')[2]
    return None

def process_youtube_video(url, save_path):
    logging.info(f"Attempting to download YouTube video from {url} to {save_path}")
    video_id = extract_video_id(url)
    if not video_id:
        logging.error("Could not extract video ID from URL")
        return None

    try:
        return download_with_playwright(video_id, save_path)
    except Exception as e:
        logging.warning(f"Playwright method failed: {str(e)}. Trying yt-dlp fallback.")
        try:
            return download_with_ytdlp(url, save_path)
        except Exception as e:
            logging.error(f"Both download methods failed. Error: {str(e)}")
            return None

def download_with_playwright(video_id, save_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"https://www.youtube.com/watch?v={video_id}")

        page.wait_for_selector('video', state='attached', timeout=30000)

        video_info = page.evaluate('''() => {
            var ytInitialPlayerResponse = window.ytInitialPlayerResponse;
            if (ytInitialPlayerResponse && ytInitialPlayerResponse.streamingData) {
                return JSON.stringify(ytInitialPlayerResponse.streamingData);
            }
            return null;
        }''')

        if not video_info:
            raise ValueError("Could not find video information")

        video_data = json.loads(video_info)
        formats = video_data.get('formats', []) + video_data.get('adaptiveFormats', [])
        
        logging.debug(f"Available formats: {json.dumps(formats, indent=2)}")

        # Try to find a format with both video and audio
        best_format = next((f for f in formats if f.get('mimeType', '').startswith('video/mp4') and 'audio' in f.get('mimeType', '')), None)

        # If not found, look for the highest quality video format
        if not best_format:
            best_format = max(formats, key=lambda x: x.get('width', 0) * x.get('height', 0), default=None)

        if not best_format:
            raise ValueError("Could not find a suitable video format")

        video_url = best_format['url']
        logging.info(f"Selected format: {json.dumps(best_format, indent=2)}")

        context.close()
        browser.close()

        # Download the video
        ydl_opts = {
            'outtmpl': save_path,
            'format': 'best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        logging.info(f"YouTube video downloaded successfully to {save_path}")
        return save_path

def download_with_ytdlp(url, save_path):
    ydl_opts = {
        'outtmpl': save_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    logging.info(f"YouTube video downloaded successfully to {save_path} using yt-dlp")
    return save_path
