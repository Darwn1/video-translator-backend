from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import urllib.request
import urllib.parse
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPID_API_KEY = "f7ed1eef7fmsh35b52675f767b3dp11c807jsna3c3452b5131"
RAPID_API_HOST = "youtube-mp310.p.rapidapi.com"

def extract_video_id(url: str) -> str:
    match = re.search(r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else url.strip()

@app.get("/")
def home():
    return {"message": "API is live and running"}

@app.get("/get-audio")
def get_audio(url: str = Query(..., description="YouTube video URL")):
    clean_url = url.strip()
    video_id = extract_video_id(clean_url)
    full_url = f"https://www.youtube.com/watch?v={video_id}"

    encoded_url = urllib.parse.quote(full_url, safe='')
    api_url = f"https://{RAPID_API_HOST}/download/mp3?url={encoded_url}"

    req = urllib.request.Request(
        api_url,
        headers={
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": RAPID_API_HOST,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            
            # دەرهێنانی لینکی داگرتنی دەنگەکە
            download_url = (
                res_data.get("downloadUrl") 
                or res_data.get("link") 
                or res_data.get("url")
            )
            
            if download_url:
                return {
                    "status": "success",
                    "title": res_data.get("title", "YouTube Audio"),
                    "audio_url": download_url
                }
            else:
                raise HTTPException(status_code=500, detail=f"Response missing link: {res_data}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RapidAPI extraction error: {str(e)}")
