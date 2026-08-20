from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import urllib.request
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_video_id(url: str) -> str:
    match = re.search(r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else url.strip()

@app.get("/")
def home():
    return {"message": "API is live and running"}

@app.get("/get-audio")
def get_audio(url: str = Query(..., description="YouTube video URL")):
    video_id = get_video_id(url)
    
    # لیستی بەهێزترین سێرڤەرە جیهانییەکان کە بلۆک ناکرێن و فایلی دەنگ ڕێک دەدەن
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.privacydev.net",
        "https://pipedapi.leptons.xyz",
        "https://piped-api.lunar.icu"
    ]
    
    for instance in instances:
        try:
            req = urllib.request.Request(
                f"{instance}/streams/{video_id}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    audio_streams = data.get("audioStreams", [])
                    if audio_streams:
                        # وەرگرتنی یەکەمین لینکی ڕوون و ئامادەکراوی دەنگ
                        return {
                            "status": "success",
                            "title": data.get("title", "YouTube Audio"),
                            "audio_url": audio_streams[0].get("url")
                        }
        except Exception:
            continue

    raise HTTPException(status_code=500, detail="Unable to extract audio stream from providers.")
