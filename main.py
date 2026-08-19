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
    
    # ئەگەر تەنها ID هاتبوو، دەیکاتە ناونیشانی تەواو
    if not clean_url.startswith("http"):
        clean_url = f"https://www.youtube.com/watch?v={clean_url}"

    ydl_opts = {
        'format': 'ba/b',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            
            # گەڕان بەدوای لینکی ڕاستەوخۆ
            audio_url = info.get('url')
            if not audio_url and 'formats' in info:
                # گەڕان بەناو فۆرماتەکان بۆ دەرهێنانی باشترین دەنگ
                audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none']
                if audio_formats:
                    audio_url = audio_formats[-1].get('url')

            if not audio_url:
                raise HTTPException(status_code=500, detail="Could not find streamable audio URL.")

            return {
                "status": "success",
                "title": info.get('title'),
                "audio_url": audio_url
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"yt-dlp error: {str(e)}")
