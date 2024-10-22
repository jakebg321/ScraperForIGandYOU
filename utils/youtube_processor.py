import logging
import os
import re
from urllib.parse import parse_qs, urlparse
import json
import yt_dlp
from yt_dlp import YoutubeDL
from PyQt5 import QtCore

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
        return download_with_ytdlp(url, save_path)
    except Exception as e:
        logging.error(f"Download method failed. Error: {str(e)}")
        return None

def download_with_ytdlp(url, save_path):
    ydl_opts = {
        'outtmpl': save_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    logging.info(f"YouTube video downloaded successfully to {save_path} using yt-dlp")
    return save_path

def is_youtube_channel_url(url):
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/(?:c\/|channel\/|user\/)?([a-zA-Z0-9_-]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    return False

def fetch_channel_videos(channel_url):
    """
    Fetch video information from a YouTube channel
    Returns a list of dictionaries containing video information
    """
    logging.info(f"Fetching videos from channel: {channel_url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': True,
        'flat_playlist': True,
        'playlist_items': '1-50',  # Limit to 50 videos
        'skip_download': True,
        'force_generic_extractor': False,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Get the playlist data
            playlist_info = ydl.extract_info(channel_url, download=False)
            if not playlist_info:
                logging.error("No results found for channel")
                return []

            videos = []
            entries = playlist_info.get('entries', [])
            
            # Configure YoutubeDL for individual video extraction
            video_opts = {
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'skip_download': True,
            }

            with YoutubeDL(video_opts) as video_ydl:
                for entry in entries:
                    if not entry:
                        continue
                    
                    try:
                        # Get detailed info for each video
                        video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                        video_info = video_ydl.extract_info(video_url, download=False)
                        
                        if video_info:
                            video_data = {
                                'title': video_info.get('title', 'Unknown Title'),
                                'url': video_url,
                                'view_count': video_info.get('view_count', 0),
                                'like_count': video_info.get('like_count', 0),
                                'comment_count': video_info.get('comment_count', 0),
                                'duration': video_info.get('duration', 0),
                                'upload_date': video_info.get('upload_date', 'Unknown'),
                            }
                            videos.append(video_data)
                            logging.info(f"Fetched info for video: {video_data['title']}")
                    except Exception as e:
                        logging.error(f"Error fetching video details: {str(e)}")
                        continue

            logging.info(f"Successfully fetched {len(videos)} videos")
            return videos

    except Exception as e:
        logging.error(f"Error fetching channel videos: {str(e)}")
        return []

import logging
import os
import re
from urllib.parse import parse_qs, urlparse
import yt_dlp
from PyQt5 import QtCore

class YoutubeChannelWorkerThread(QtCore.QThread):
    progress_signal = QtCore.pyqtSignal(str, int)
    video_found_signal = QtCore.pyqtSignal(dict)
    error_signal = QtCore.pyqtSignal(str)
    finished_signal = QtCore.pyqtSignal()

    def __init__(self, channel_url):
        super().__init__()
        self.channel_url = channel_url
        self.logger = logging.getLogger('YoutubeProcessor.ChannelWorker')
        self.video_count = 0
        self.should_stop = False
        self.is_paused = False
        self.pause_condition = QtCore.QWaitCondition()
        self.mutex = QtCore.QMutex()

    def run(self):
        try:
            self.progress_signal.emit("Initializing channel fetch...", 0)
            
            if not is_youtube_channel_url(self.channel_url):
                self.error_signal.emit("Invalid YouTube channel URL")
                return

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'force_generic_extractor': False,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    self.progress_signal.emit("Fetching channel information...", 5)
                    playlist_info = ydl.extract_info(self.channel_url, download=False)
                    
                    if not playlist_info or 'entries' not in playlist_info:
                        self.error_signal.emit("No videos found in channel")
                        return

                    total_videos = len(playlist_info['entries'])
                    self.progress_signal.emit(f"Found {total_videos} videos. Starting fetch...", 10)

                    video_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False,
                    }

                    with yt_dlp.YoutubeDL(video_opts) as video_ydl:
                        for idx, entry in enumerate(playlist_info['entries'], 1):
                            # Check for pause
                            self.mutex.lock()
                            while self.is_paused and not self.should_stop:
                                self.progress_signal.emit("Paused...", -1)  # -1 indicates paused state
                                self.pause_condition.wait(self.mutex)
                            self.mutex.unlock()

                            # Check for stop
                            if self.should_stop:
                                self.progress_signal.emit("Stopped", 0)
                                break

                            if not entry:
                                continue

                            try:
                                video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                                self.progress_signal.emit(
                                    f"Fetching video {idx}/{total_videos}...", 
                                    int(10 + (idx/total_videos * 90))
                                )
                                
                                video_info = video_ydl.extract_info(video_url, download=False)
                                
                                if video_info:
                                    video_data = {
                                        'title': video_info.get('title', 'Unknown Title'),
                                        'url': video_url,
                                        'view_count': video_info.get('view_count', 0),
                                        'like_count': video_info.get('like_count', 0),
                                        'comment_count': video_info.get('comment_count', 0),
                                        'duration': video_info.get('duration', 0),
                                        'upload_date': self._format_date(video_info.get('upload_date', 'Unknown')),
                                        'thumbnail': video_info.get('thumbnail', '')
                                    }
                                    
                                    self.video_count += 1
                                    self.video_found_signal.emit(video_data)
                                    
                            except Exception as e:
                                self.logger.error(f"Error fetching video details: {str(e)}")
                                continue

            except Exception as e:
                self.error_signal.emit(f"Error fetching channel: {str(e)}")
                return

            if not self.should_stop:
                self.progress_signal.emit(f"Completed fetching {self.video_count} videos", 100)
            self.finished_signal.emit()

        except Exception as e:
            self.logger.error(f"Error in worker thread: {str(e)}")
            self.error_signal.emit(f"An error occurred: {str(e)}")

    def pause(self):
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()

    def resume(self):
        self.mutex.lock()
        self.is_paused = False
        self.pause_condition.wakeAll()
        self.mutex.unlock()

    def stop(self):
        self.should_stop = True
        self.resume()  # Wake up the thread if it's paused

    def _format_date(self, date_str):
        """Format YYYYMMDD to YYYY-MM-DD"""
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        return date_str