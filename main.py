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

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            
            # 1. سەیرکردنی لینکی ڕاستەوخۆی سەرەکی
            audio_url = info.get('url')

            # 2. ئەگەر نەبوو، گەڕان لە ناو تەواوی لیستەکانی فۆرمات
            if not audio_url and 'formats' in info:
                # گەڕان بەدوای تەنها فایلی دەنگ (acodec هەبێت و vcodec نەبێت)
                for f in reversed(info['formats']):
                    if f.get('acodec') != 'none' and f.get('url'):
                        audio_url = f.get('url')
                        break
                
                # ئەگەر هەر دەنگ بە تەنها نەدۆزرایەوە، هەڵبژاردنی نزمترین فۆرماتی ڤیدیۆکە بۆ وەرگرتنی دەنگ
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
