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
    
    # بەکارهێنانی کڵاینتی فەرمی پەخشی ئەندرۆید بەبێ بلۆک
    payload = {
        "videoId": video_id,
        "context": {
            "client": {
                "clientName": "ANDROID",
                "clientVersion": "19.09.37",
                "androidSdkVersion": 30,
                "hl": "en",
                "gl": "US"
            }
        }
    }
    
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        "https://www.youtube.com/youtubei/v1/player?prettyPrint=false",
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            streaming_data = res_data.get("streamingData", {})
            formats = streaming_data.get("adaptiveFormats", [])
            
            # دەرهێنانی تەنها لینکی دەنگ
            for f in formats:
                if "audio" in f.get("mimeType", "") and f.get("url"):
                    return {
                        "status": "success",
                        "title": res_data.get("videoDetails", {}).get("title", "YouTube Audio"),
                        "audio_url": f.get("url")
                    }
                    
            # ئەگەر لە adaptive نەبوو لە فۆرماتی گشتی بگەڕێ
            for f in streaming_data.get("formats", []):
                if f.get("url"):
                    return {
                        "status": "success",
                        "title": res_data.get("videoDetails", {}).get("title", "YouTube Audio"),
                        "audio_url": f.get("url")
                    }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Extraction error: {str(e)}")

    raise HTTPException(status_code=500, detail="Audio stream not found.")
