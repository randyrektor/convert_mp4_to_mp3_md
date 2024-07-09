import os
import re
import subprocess
import json
import time
from datetime import datetime

def find_highest_numbered_subfolder(parent_folder):
    highest_number = -1
    highest_folder = None
    folder_pattern = re.compile(r'^(\d{3}) - .*')
    for folder_name in os.listdir(parent_folder):
        if os.path.isdir(os.path.join(parent_folder, folder_name)):
            match = folder_pattern.match(folder_name)
            if match:
                folder_number = int(match.group(1))
                if folder_number > highest_number:
                    highest_number = folder_number
                    highest_folder = folder_name
    return highest_folder

def extract_timestamps(video_file):
    command = f'ffprobe -v quiet -print_format json -show_chapters "{video_file}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    chapters = json.loads(result.stdout)['chapters']
    timestamps = []
    for chapter in chapters:
        start_time = chapter['start_time']  # Use start_time directly
        title = chapter['tags']['title']
        timestamps.append((start_time, title))
    return timestamps

def format_to_markdown(timestamps):
    markdown_lines = []
    for timestamp, description in timestamps:
        try:
            seconds = int(float(timestamp))  # Convert timestamp to float and then to integer seconds
            hours = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
            if hours > 0:
                formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"
            else:
                formatted_time = f"{minutes:02}:{seconds:02}"
            markdown_lines.append(f"* **[{formatted_time}](#t={formatted_time})** {description}")
        except ValueError:
            print(f"Timestamp with unexpected format: {timestamp}")
    return markdown_lines

def main():
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    syntax_edits_folder = os.path.join(desktop_path, 'Syntax Edits')

    if not os.path.exists(syntax_edits_folder):
        print("Syntax Edits folder not found on desktop.")
        return

    highest_numbered_subfolder = find_highest_numbered_subfolder(syntax_edits_folder)

    if not highest_numbered_subfolder:
        print("No subfolders matching the expected format found in Syntax Edits folder.")
        return

    highest_number_path = os.path.join(syntax_edits_folder, highest_numbered_subfolder)
    mp4_file = None
    for file_name in os.listdir(highest_number_path):
        if file_name.endswith('.mp4'):
            mp4_file = file_name
            break

    if not mp4_file:
        print("No .mp4 file found in the highest numbered subfolder.")
        return

    input_path = os.path.join(highest_number_path, mp4_file)

    ffmpeg_command = [
        'ffmpeg',
        '-i', input_path,
        '-vn',
        '-acodec', 'libmp3lame',
        '-q:a', '2',
        '-map_metadata', '0',
        '-id3v2_version', '3',
        os.path.join(highest_number_path, f"Syntax_-_{highest_numbered_subfolder.split(' ')[0]}.mp3")
    ]

    subprocess.run(ffmpeg_command)

    print("Conversion to MP3 complete. Waiting for 5 seconds before converting to Markdown...")
    time.sleep(5)  # Pause for 5 seconds before continuing to the next task

    timestamps = extract_timestamps(input_path)
    markdown_lines = format_to_markdown(timestamps)

    markdown_file_name = os.path.splitext(mp4_file)[0] + ".md"
    markdown_file_path = os.path.join(highest_number_path, markdown_file_name)

    with open(markdown_file_path, "w") as markdown_file:
        for line in markdown_lines:
            markdown_file.write(line + '\n')

    print(f"Markdown file '{markdown_file_name}' created successfully.")

if __name__ == "__main__":
    main()
