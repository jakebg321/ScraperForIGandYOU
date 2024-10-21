import subprocess
import random
import os
import logging
from datetime import datetime
import re

def sanitize_filename(filename):
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    sanitized = sanitized.replace(' ', '_')
    return sanitized

def adjust_media(file_path, output_filename):
    try:
        logging.info(f"Starting media adjustment for {file_path}")
        
        if not os.path.exists(file_path):
            logging.error(f"Input file does not exist: {file_path}")
            return None, None
        
        file_size = os.path.getsize(file_path)
        if file_size < 1024:
            logging.error(f"Input file is too small: {file_path} (Size: {file_size} bytes)")
            return None, None
        
        logging.info(f"Input file size: {file_size} bytes")

        hue = random.uniform(-10, 10)
        saturation = random.uniform(0.9, 1.1)
        brightness = random.uniform(0.9, 1.1)
        volume = random.uniform(0.9, 1.1)
        pitch = random.uniform(0.95, 1.05)
        tempo = random.uniform(0.98, 1.02)

        output_folder = os.path.dirname(file_path)
        output_file_path = os.path.join(output_folder, sanitize_filename(output_filename))
        
        ffmpeg_path = 'ffmpeg'  # Assuming ffmpeg is in PATH, otherwise provide full path

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        command = [
            ffmpeg_path,
            '-y',
            '-i', file_path,
            '-vf', f"hue=h={hue}:s={saturation}:b={brightness}",
            '-af', f"volume={volume},asetrate=44100*{pitch},atempo=1/{pitch},atempo={tempo}",
            '-metadata', f"creation_time={current_datetime}",
            '-metadata', f"modify_time={current_datetime}",
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-max_muxing_queue_size', '1024',
            output_file_path
        ]
        
        logging.info(f"Executing FFmpeg command: {' '.join(command)}")
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            logging.error(f"FFmpeg command failed with return code {result.returncode}")
            logging.error(f"FFmpeg stdout: {result.stdout}")
            logging.error(f"FFmpeg stderr: {result.stderr}")
            return None, None
        
        if os.path.exists(output_file_path):
            output_file_size = os.path.getsize(output_file_path)
            logging.info(f"Media adjusted successfully. File saved to: {output_file_path} (Size: {output_file_size} bytes)")
            
            if output_file_size < 1024:
                logging.error(f"Output file is too small: {output_file_path} (Size: {output_file_size} bytes)")
                return None, None
            
            adjustments = {
                'hue': hue,
                'saturation': saturation,
                'brightness': brightness,
                'volume': volume,
                'pitch': pitch,
                'tempo': tempo,
                'creation_time': current_datetime,
                'modify_time': current_datetime
            }
            return output_file_path, adjustments
        else:
            logging.error(f"Output file not found: {output_file_path}")
            return None, None
    except subprocess.TimeoutExpired:
        logging.error("FFmpeg process timed out after 5 minutes")
        return None, None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        logging.exception("Exception details:")
        return None, None
    finally:
        # Clean up input file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Deleted input file: {file_path}")
            except Exception as e:
                logging.error(f"Failed to delete input file {file_path}: {str(e)}")