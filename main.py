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

# بەکارهێنانی Piped کە زۆر خێرا و جێگیرە بۆ دەرهێنانی دەنگ
def fetch_from_piped(video_id: str):
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.tokhmi.xyz",
        "https://pipedapi.smnz.de",
        "https://piped-api.garudalinux.org"
    ]
    for instance in instances:
        try:
            req = urllib.request.Request(
                f"{instance}/streams/{video_id}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    audio_streams = data.get("audioStreams", [])
                    if audio_streams:
                        return {
                            "status": "success",
                            "title": "YouTube Audio",
                            "audio_url": audio_streams[0].get("url")
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

    # 1. هەوڵی یەکەم لە ڕێگەی Piped API دەدەین چونکە بلۆک ناکرێت و زۆر خێرایە
    piped_result = fetch_from_piped(video_id)
    if piped_result:
        return piped_result

    # 2. ئەگەر Piped کاری نەکرد، ئینجا پەنا دەبەینە بەر yt-dlp وەک یەدەگ
    ydl_opts = {
        'format': 'ba/b',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
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

    raise HTTPException(status_code=500, detail="Could not extract audio via direct or backup stream.")
