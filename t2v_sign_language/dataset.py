import os
from yt_dlp import YoutubeDL

absolute_path = os.path.dirname(__file__)
relative_path = "video_urls.txt"
full_path = os.path.join(absolute_path, relative_path)

with open(full_path, 'r') as f:
    urls = f.readlines()

options = {
    'outtmpl': os.path.join(absolute_path, '..', 'data', 'external', '%(title)s.%(ext)s'),
    'format': 'bestvideo+bestaudio',
    'cookiefile': os.path.join(absolute_path, '..', 'cookies.txt')
}

with YoutubeDL(options) as ydl:
    ydl.download(urls)