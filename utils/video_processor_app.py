import os
import time
import logging
from PyQt5 import QtWidgets, QtGui, QtCore
from youtube_processor import (
    process_youtube_video, 
    is_youtube_url, 
    is_youtube_channel_url, 
    YoutubeChannelWorkerThread
)
from PyQt5.QtWidgets import QApplication

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
            self.finished_signal.emit("error", f"An error occurred: {e}")

class VideoProcessorApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def update_progress(self, message, value):
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)

    def show_error_message(self, message):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #4B0082;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #6A0DAD;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #8A2BE2;
            }
        """)
        msg_box.exec_()
        self.progress_label.setText('')
        self.progress_bar.setValue(0)

    def add_video_to_table(self, video):
        current_row = self.videos_table.rowCount()
        self.videos_table.insertRow(current_row)
        
        # Add checkbox
        checkbox = QtWidgets.QCheckBox()
        checkbox_widget = QtWidgets.QWidget()
        checkbox_layout = QtWidgets.QHBoxLayout(checkbox_widget)
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.setAlignment(QtCore.Qt.AlignCenter)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.videos_table.setCellWidget(current_row, 0, checkbox_widget)
        
        # Add video data
        self.videos_table.setItem(current_row, 1, QtWidgets.QTableWidgetItem(video['title']))
        self.videos_table.setItem(current_row, 2, QtWidgets.QTableWidgetItem(video['url']))
        self.videos_table.setItem(current_row, 3, QtWidgets.QTableWidgetItem(str(video['view_count'])))
        self.videos_table.setItem(current_row, 4, QtWidgets.QTableWidgetItem(str(video['like_count'])))
        self.videos_table.setItem(current_row, 5, QtWidgets.QTableWidgetItem(str(video['comment_count'])))
        self.videos_table.setItem(current_row, 6, QtWidgets.QTableWidgetItem(str(video['duration']) + 's'))
        self.videos_table.setItem(current_row, 7, QtWidgets.QTableWidgetItem(video['upload_date']))
        
        # Scroll to the new row
        self.videos_table.scrollToBottom()

    def channel_fetch_completed(self):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle("Success")
        msg_box.setText(f"Fetched {self.videos_table.rowCount()} videos from the channel")
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #4B0082;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #6A0DAD;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #8A2BE2;
            }
        """)
        msg_box.exec_()
        self.progress_label.setText('')
        self.progress_bar.setValue(0)

    def download_selected_videos(self):
        selected_videos = []
        for row in range(self.videos_table.rowCount()):
            checkbox_widget = self.videos_table.cellWidget(row, 0)
            checkbox = checkbox_widget.layout().itemAt(0).widget()
            if checkbox.isChecked():
                url = self.videos_table.item(row, 2).text()
                title = self.videos_table.item(row, 1).text()
                selected_videos.append((url, title))

        if not selected_videos:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setWindowTitle("Warning")
            msg_box.setText("Please select at least one video to download")
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #4B0082;
                }
                QMessageBox QLabel {
                    color: white;
                }
                QMessageBox QPushButton {
                    background-color: #6A0DAD;
                    color: white;
                    border-radius: 5px;
                    padding: 5px 15px;
                    min-width: 80px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #8A2BE2;
                }
            """)
            msg_box.exec_()
            return

        # Ask for save directory
        save_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory to Save Videos")
        if not save_dir:
            return

        # Process each selected video
        total_videos = len(selected_videos)
        for index, (url, title) in enumerate(selected_videos, 1):
            # Create a sanitized filename from the title
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            save_path = os.path.join(save_dir, f"{safe_title}.mp4")
            
            # Update progress to show which video is being processed
            self.progress_label.setText(f"Processing video {index}/{total_videos}: {title}")
            self.progress_bar.setValue(0)
            
            # Create and start worker thread for this video
            self.worker_thread = WorkerThread(url, save_path)
            self.worker_thread.progress_signal.connect(self.update_progress)
            self.worker_thread.finished_signal.connect(
                lambda status, msg, current=index, total=total_videos: 
                self.processing_finished(status, msg, current, total)
            )
            self.worker_thread.start()
            # Wait for the current video to finish processing before starting the next one
            self.worker_thread.wait()

    def processing_finished(self, status, message, current_video=None, total_videos=None):
        msg_box = QtWidgets.QMessageBox(self)
        
        if current_video and total_videos:
            if status == "success":
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                msg_box.setWindowTitle("Success")
                msg_box.setText(f"Video {current_video}/{total_videos} processed successfully\n\n{message}")
            else:
                msg_box.setIcon(QtWidgets.QMessageBox.Critical)
                msg_box.setWindowTitle("Error")
                msg_box.setText(f"Error processing video {current_video}/{total_videos}\n\n{message}")
        else:
            if status == "success":
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                msg_box.setWindowTitle("Success")
                msg_box.setText(message)
            else:
                msg_box.setIcon(QtWidgets.QMessageBox.Critical)
                msg_box.setWindowTitle("Error")
                msg_box.setText(message)
        
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #4B0082;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #6A0DAD;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #8A2BE2;
            }
        """)
        msg_box.exec_()
        
        # Only clear progress if this is the last or only video
        if not current_video or current_video == total_videos:
            self.progress_label.setText('')
            self.progress_bar.setValue(0)

    def start_processing(self):
        url = self.url_entry.text().strip()
        if not url:
            QtWidgets.QMessageBox.critical(self, "Error", "Please enter a video URL")
            return

        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Video As", "downloaded_video.mp4", "MP4 Files (*.mp4)")
        if not save_path:
            return

        self.worker_thread = WorkerThread(url, save_path)
        self.worker_thread.progress_signal.connect(self.update_progress)
        self.worker_thread.finished_signal.connect(self.processing_finished)
        self.worker_thread.start()

    def start_fetching_channel_videos(self):
            channel_url = self.channel_entry.text().strip()
            if not channel_url:
                self.show_error_message("Please enter a YouTube channel URL")
                return

            # Clear existing table contents
            self.videos_table.setRowCount(0)
            
            self.channel_worker_thread = YoutubeChannelWorkerThread(channel_url)
            self.channel_worker_thread.progress_signal.connect(self.update_progress)
            self.channel_worker_thread.video_found_signal.connect(self.add_video_to_table)
            self.channel_worker_thread.error_signal.connect(self.show_error_message)
            self.channel_worker_thread.finished_signal.connect(self.channel_fetch_completed)
            self.channel_worker_thread.start()
    def init_ui(self):
        # Window Setup
        self.setWindowTitle('Video Processor (YouTube & Instagram)')
        self.setGeometry(100, 100, 800, 1000)
        self.setStyleSheet("background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #4B0082, stop:1 #8A2BE2);")

        # Create main layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # URL Section
        url_group = QtWidgets.QGroupBox("Video Download")
        url_group.setStyleSheet("QGroupBox { color: white; }")
        url_layout = QtWidgets.QVBoxLayout()

        self.url_label = QtWidgets.QLabel('Enter YouTube or Instagram URL:')
        self.url_label.setStyleSheet("color: white;")
        url_layout.addWidget(self.url_label)

        self.url_entry = QtWidgets.QLineEdit()
        self.url_entry.setStyleSheet("border: 2px solid #8A2BE2; border-radius: 5px; padding: 5px; color: white;")
        url_layout.addWidget(self.url_entry)

        self.process_button = QtWidgets.QPushButton('Process Video')
        self.process_button.setStyleSheet("background-color: #6A0DAD; color: white; border-radius: 10px; padding: 10px;")
        self.process_button.clicked.connect(self.start_processing)
        url_layout.addWidget(self.process_button)

        url_group.setLayout(url_layout)
        self.main_layout.addWidget(url_group)        
        progress_group = QtWidgets.QGroupBox("Progress")
        progress_group.setStyleSheet("QGroupBox { color: white; }")
        progress_layout = QtWidgets.QVBoxLayout()

        self.progress_label = QtWidgets.QLabel('')
        self.progress_label.setStyleSheet("color: white;")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #6A0DAD;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #8A2BE2;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        progress_group.setLayout(progress_layout)
        self.main_layout.addWidget(progress_group)

        # YouTube Channel Section
        channel_group = QtWidgets.QGroupBox("YouTube Channel Videos")
        channel_group.setStyleSheet("QGroupBox { color: white; }")
        channel_layout = QtWidgets.QVBoxLayout()

        self.channel_label = QtWidgets.QLabel('Enter YouTube Channel URL:')
        self.channel_label.setStyleSheet("color: white;")
        channel_layout.addWidget(self.channel_label)

        self.channel_entry = QtWidgets.QLineEdit()
        self.channel_entry.setStyleSheet("border: 2px solid #8A2BE2; border-radius: 5px; padding: 5px; color: white;")
        channel_layout.addWidget(self.channel_entry)

        # Button layout for channel controls
        channel_buttons_layout = QtWidgets.QHBoxLayout()
        
        self.fetch_videos_button = QtWidgets.QPushButton('Fetch Channel Videos')
        self.fetch_videos_button.setStyleSheet("""
            QPushButton {
                background-color: #6A0DAD;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8A2BE2;
            }
        """)
        self.fetch_videos_button.clicked.connect(self.start_fetching_channel_videos)
        channel_buttons_layout.addWidget(self.fetch_videos_button)

        self.pause_resume_button = QtWidgets.QPushButton('Pause')
        self.pause_resume_button.setStyleSheet("""
            QPushButton {
                background-color: #6A0DAD;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8A2BE2;
            }
        """)
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)
        self.pause_resume_button.setEnabled(False)
        channel_buttons_layout.addWidget(self.pause_resume_button)

        self.stop_button = QtWidgets.QPushButton('Stop')
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #FF0000;
            }
        """)
        self.stop_button.clicked.connect(self.stop_fetching)
        self.stop_button.setEnabled(False)
        channel_buttons_layout.addWidget(self.stop_button)

        self.download_selected_button = QtWidgets.QPushButton('Download Selected')
        self.download_selected_button.setStyleSheet("""
            QPushButton {
                background-color: #6A0DAD;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8A2BE2;
            }
        """)
        self.download_selected_button.clicked.connect(self.download_selected_videos)
        channel_buttons_layout.addWidget(self.download_selected_button)

        # Add the button layout to the channel layout
        channel_layout.addLayout(channel_buttons_layout)
        
        # Videos Table
        self.videos_table = QtWidgets.QTableWidget()
        self.videos_table.setColumnCount(8)  # Added column for checkbox
        self.videos_table.setHorizontalHeaderLabels(['Select', 'Title', 'URL', 'Views', 'Likes', 'Comments', 'Duration', 'Upload Date'])
        self.videos_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: black;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QCheckBox {
                margin-left: 5px;
            }
        """)
        self.videos_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.videos_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        channel_layout.addWidget(self.videos_table)

        # Set the channel group layout
        channel_group.setLayout(channel_layout)
        self.main_layout.addWidget(channel_group)


        

        # Set the main layout
        self.setLayout(self.main_layout)
    def toggle_pause_resume(self):
        if hasattr(self, 'channel_worker_thread'):
            if self.pause_resume_button.text() == 'Pause':
                self.channel_worker_thread.pause()
                self.pause_resume_button.setText('Resume')
            else:
                self.channel_worker_thread.resume()
                self.pause_resume_button.setText('Pause')

    def stop_fetching(self):
        if hasattr(self, 'channel_worker_thread'):
            self.channel_worker_thread.stop()
            self.pause_resume_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.fetch_videos_button.setEnabled(True)

    def update_progress(self, message, value):
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)

    def show_error_message(self, message):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #4B0082;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #6A0DAD;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #8A2BE2;
            }
        """)
        msg_box.exec_()
        self.progress_label.setText('')
        self.progress_bar.setValue(0)

    def add_video_to_table(self, video):
            try:
                current_row = self.videos_table.rowCount()
                self.videos_table.insertRow(current_row)
                
                # Add checkbox
                checkbox = QtWidgets.QCheckBox()
                checkbox_widget = QtWidgets.QWidget()
                checkbox_layout = QtWidgets.QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(QtCore.Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.videos_table.setCellWidget(current_row, 0, checkbox_widget)
                
                # Format numbers for better readability
                view_count = f"{video['view_count']:,}" if video['view_count'] else "0"
                like_count = f"{video['like_count']:,}" if video['like_count'] else "0"
                comment_count = f"{video['comment_count']:,}" if video['comment_count'] else "0"
                
                # Format duration
                duration = str(int(video['duration'])) + 's' if video['duration'] else "0s"
                
                # Add video data
                items = [
                    (1, video['title']),
                    (2, video['url']),
                    (3, view_count),
                    (4, like_count),
                    (5, comment_count),
                    (6, duration),
                    (7, video['upload_date'])
                ]
                
                for col, value in items:
                    item = QtWidgets.QTableWidgetItem(str(value))
                    # Make cells read-only
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                    self.videos_table.setItem(current_row, col, item)
                
                # Ensure the new row is visible
                self.videos_table.scrollToItem(self.videos_table.item(current_row, 0))
                
                # Update the application to prevent freezing
                QApplication.processEvents()
                
            except Exception as e:
                logging.error(f"Error adding video to table: {str(e)}")
    def start_fetching_channel_videos(self):
            channel_url = self.channel_entry.text().strip()
            if not channel_url:
                self.show_error_message("Please enter a YouTube channel URL")
                return

            # Clear existing table contents
            self.videos_table.setRowCount(0)
            
            self.channel_worker_thread = YoutubeChannelWorkerThread(channel_url)
            self.channel_worker_thread.progress_signal.connect(self.update_progress)
            self.channel_worker_thread.video_found_signal.connect(self.add_video_to_table)
            self.channel_worker_thread.error_signal.connect(self.show_error_message)
            self.channel_worker_thread.finished_signal.connect(self.channel_fetch_completed)
            
            # Enable/disable appropriate buttons
            self.fetch_videos_button.setEnabled(False)
            self.pause_resume_button.setEnabled(True)
            self.pause_resume_button.setText('Pause')
            self.stop_button.setEnabled(True)
            
            self.channel_worker_thread.start()
    def channel_fetch_completed(self):
        self.fetch_videos_button.setEnabled(True)
        self.pause_resume_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle("Success")
        msg_box.setText(f"Fetched {self.videos_table.rowCount()} videos from the channel")
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #4B0082;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #6A0DAD;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #8A2BE2;
            }
        """)
        msg_box.exec_()
        self.progress_label.setText('')
        self.progress_bar.setValue(0)

    def download_selected_videos(self):
        selected_videos = []
        for row in range(self.videos_table.rowCount()):
            checkbox_widget = self.videos_table.cellWidget(row, 0)
            checkbox = checkbox_widget.layout().itemAt(0).widget()
            if checkbox.isChecked():
                url = self.videos_table.item(row, 2).text()
                title = self.videos_table.item(row, 1).text()
                selected_videos.append((url, title))

        if not selected_videos:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setWindowTitle("Warning")
            msg_box.setText("Please select at least one video to download")
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #4B0082;
                }
                QMessageBox QLabel {
                    color: white;
                }
                QMessageBox QPushButton {
                    background-color: #6A0DAD;
                    color: white;
                    border-radius: 5px;
                    padding: 5px 15px;
                    min-width: 80px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #8A2BE2;
                }
            """)
            msg_box.exec_()
            return

        # Ask for save directory
        save_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory to Save Videos")
        if not save_dir:
            return

        # Process each selected video
        total_videos = len(selected_videos)
        for index, (url, title) in enumerate(selected_videos, 1):
            # Create a sanitized filename from the title
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            save_path = os.path.join(save_dir, f"{safe_title}.mp4")
            
            # Update progress to show which video is being processed
            self.progress_label.setText(f"Processing video {index}/{total_videos}: {title}")
            self.progress_bar.setValue(0)
            
            # Create and start worker thread for this video
            self.worker_thread = WorkerThread(url, save_path)
            self.worker_thread.progress_signal.connect(self.update_progress)
            self.worker_thread.finished_signal.connect(
                lambda status, msg, current=index, total=total_videos: 
                self.processing_finished(status, msg, current, total)
            )
            self.worker_thread.start()
            # Wait for the current video to finish processing before starting the next one
            self.worker_thread.wait()

    def processing_finished(self, status, message, current_video=None, total_videos=None):
        msg_box = QtWidgets.QMessageBox(self)
        
        if current_video and total_videos:
            if status == "success":
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                msg_box.setWindowTitle("Success")
                msg_box.setText(f"Video {current_video}/{total_videos} processed successfully\n\n{message}")
            else:
                msg_box.setIcon(QtWidgets.QMessageBox.Critical)
                msg_box.setWindowTitle("Error")
                msg_box.setText(f"Error processing video {current_video}/{total_videos}\n\n{message}")
        else:
            if status == "success":
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                msg_box.setWindowTitle("Success")
                msg_box.setText(message)
            else:
                msg_box.setIcon(QtWidgets.QMessageBox.Critical)
                msg_box.setWindowTitle("Error")
                msg_box.setText(message)
        
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #4B0082;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #6A0DAD;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #8A2BE2;
            }
        """)
        msg_box.exec_()
        
        # Only clear progress if this is the last or only video
        if not current_video or current_video == total_videos:
            self.progress_label.setText('')
            self.progress_bar.setValue(0)