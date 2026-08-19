from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import json
import urllib.request
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_video_id(url: str) -> str:
    match = re.search(r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else url.strip()

def fetch_from_invidious(video_id: str):
    instances = [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://invidious.protokolla.fi",
        "https://yt.artemislena.eu"
    ]
    for instance in instances:
        try:
            req = urllib.request.Request(
                f"{instance}/api/v1/videos/{video_id}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    audio_streams = data.get("adaptiveFormats", [])
                    for stream in audio_streams:
                        if stream.get("type", "").startswith("audio/"):
                            return {
                                "status": "success",
                                "title": data.get("title"),
                                "audio_url": stream.get("url")
                            }
        except Exception:
            continue
    return None

@app.get("/")
def home():
    return {"message": "API is live and running"}

@app.get("/get-audio")
def get_audio(url: str = Query(..., description="YouTube video URL")):
    clean_url = url.strip()
    video_id = extract_video_id(clean_url)
    
    if not clean_url.startswith("http"):
        clean_url = f"https://www.youtube.com/watch?v={video_id}"

    # 1. تاقیکردنەوە لە ڕێگەی yt-dlp
    ydl_opts = {
        'format': 'ba/b',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            audio_url = info.get('url')
            if not audio_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('acodec') != 'none' and f.get('url'):
                        audio_url = f.get('url')
                        break
            
            if audio_url:
                return {
                    "status": "success",
                    "title": info.get('title'),
                    "audio_url": audio_url
                }
    except Exception:
        pass

    # 2. Fallback لە کاتی بوونی بلۆکی IP
    backup_result = fetch_from_invidious(video_id)
    if backup_result:
        return backup_result

    raise HTTPException(status_code=500, detail="Could not extract audio via direct or backup stream.")
