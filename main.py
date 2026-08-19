from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API is live and running"}

@app.get("/get-audio")
def get_audio(url: str = Query(..., description="YouTube video URL")):
    clean_url = url.strip()
    if not clean_url.startswith("http"):
        clean_url = f"https://www.youtube.com/watch?v={clean_url}"

    # بایپاسکردنی توندی بلۆکی بۆت لە ڕێگەی کڵاینتە دەستکاریکراوەکان
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'tv_embedded'],
                'player_skip': ['configs', 'webpage']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
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
                
                if not audio_url:
                    for f in info['formats']:
                        if f.get('url'):
                            audio_url = f.get('url')
                            break

            if not audio_url:
                raise HTTPException(status_code=500, detail="Could not find streamable audio URL.")

            return {
                "status": "success",
                "title": info.get('title'),
                "audio_url": audio_url
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"yt-dlp error: {str(e)}")
