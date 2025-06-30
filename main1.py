import shutil
import json
import time
import os
import asyncio
import sqlite3
from uuid import uuid4
from pathlib import Path
from fastapi import FastAPI, Request, Form, File, UploadFile, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# --- БАЗОВАЯ НАСТРОЙКА ---

# Рекомендуется хранить секретный ключ в переменных окружения, а не в коде
SECRET_KEY = os.environ.get("SECRET_KEY", "wowvideo_secret_key_2024_is_now_much_safer")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Пути к директориям
BASE_DIR = Path(__file__).parent
VIDEOS_DIR = BASE_DIR / "videos"
THUMBS_DIR = BASE_DIR / "thumbnails"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
DB_FILE = BASE_DIR / "videos.db"

# Создаем директории, если они не существуют
VIDEOS_DIR.mkdir(exist_ok=True)
THUMBS_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)


# Настройка шаблонизатора Jinja2
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

MAX_UPLOADS = 5

# --- ЛОКАЛИЗАЦИЯ ---
LANGS = {"en": "English", "ru": "Русский", "uk": "Українська", "pl": "Polski"}
DEFAULT_LANG = "en"
translations = {
    "en": {
        "title": "Video Share", "upload": "Upload Video", "record": "Record Video", "f2f": "Interview (F2F)",
        "stat": "Statistics", "feedback": "Feedback", "lang": "Language", "mainpage": "Main Page",
        "select_file": "Select video file", "ttl": "Storage time (days)", "upload_btn": "Upload",
        "record_btn": "Start Recording", "stop_btn": "Stop", "send_record_btn": "Send Video",
        "back_main": "Back", "your_videos": "Your Videos", "copy": "Copy Link", "delete": "Delete",
        "copied": "Link copied!", "no_videos": "You haven't uploaded any videos yet.",
        "limit_reached": "Upload limit reached (max 5).", "question": "Your question...",
        "choose_lang": "Choose language:", "without_reg": "without registration, without ads",
        "subscribe": "Subscribe",
        "stat_total_videos": "Total videos", "stat_total_size": "Total size (MB)", "stat_avg_ttl": "Average TTL (days)"
    },
    # Здесь можно добавить русские, украинские и польские переводы
}

# --- РАБОТА С СЕССИЕЙ И ЯЗЫКОМ ---

def get_lang(request: Request) -> str:
    lang = request.query_params.get("lang")
    if not lang or lang not in LANGS:
        lang = request.cookies.get("lang", DEFAULT_LANG)
    if lang not in LANGS:
        lang = DEFAULT_LANG
    return lang

def set_lang_cookie(response: Response, lang: str):
    response.set_cookie(key="lang", value=lang, max_age=365 * 24 * 60 * 60) # 1 year

def get_user_uploads(request: Request) -> list:
    return request.session.get("uploads", [])

def add_upload_to_session(request: Request, video_id: str):
    uploads = get_user_uploads(request)
    uploads.append(video_id)
    request.session["uploads"] = uploads

def remove_upload_from_session(request: Request, video_id: str):
    uploads = get_user_uploads(request)
    if video_id in uploads:
        uploads.remove(video_id)
        request.session["uploads"] = uploads

# --- РАБОТА С БАЗОЙ ДАННЫХ (SQLite) ---

def get_db():
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def init_db():
    with sqlite3.connect(DB_FILE) as db:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                saved_filename TEXT NOT NULL,
                thumb_filename TEXT,
                created_at REAL NOT NULL,
                ttl_days INTEGER NOT NULL,
                ip_address TEXT,
                question TEXT,
                size_bytes INTEGER
            )
        """)
        db.commit()

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ОБРАБОТКИ ВИДЕО ---

async def process_and_save_video(request: Request, file: UploadFile, ttl: int, question: str = None):
    ext = Path(file.filename).suffix or ".mp4"
    video_id = str(uuid4())[:12]
    saved_filename = f"{video_id}{ext}"
    file_path = VIDEOS_DIR / saved_filename
    file_size = 0

    import aiofiles
    async with aiofiles.open(file_path, "wb") as out_f:
        content = await file.read()
        await out_f.write(content)
        file_size = len(content)

    thumb_filename = f"{video_id}.jpg"
    thumb_path = THUMBS_DIR / thumb_filename
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", str(file_path),
            "-ss", "00:00:02", "-vframes", "1",
            "-vf", "scale=400:-1", str(thumb_path),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"FFMPEG Error: {stderr.decode()}")
            thumb_filename = ""
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        thumb_filename = ""

    db = next(get_db())
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO videos (id, original_filename, saved_filename, thumb_filename, created_at, ttl_days, ip_address, question, size_bytes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            video_id,
            file.filename,
            saved_filename,
            thumb_filename,
            time.time(),
            int(ttl),
            request.client.host,
            question,
            file_size
        )
    )
    db.commit()

    add_upload_to_session(request, video_id)
    return video_id

# --- ЭНДПОИНТЫ (Маршруты) ---

@app.get("/", response_class=HTMLResponse)
async def main_landing(request: Request):
    lang = get_lang(request)
    # Предполагается, что в static лежат картинки 1.jpg, 2.jpg, 3.jpg
    bg_list = ["1.jpg", "2.jpg", "3.jpg"]
    bg_idx = int(time.time()) % len(bg_list)
    context = {
        "request": request,
        "tr": translations.get(lang, translations[DEFAULT_LANG]),
        "langs": LANGS,
        "lang": lang,
        "bg_url": f"/static/{bg_list[bg_idx]}"
    }
    response = templates.TemplateResponse("index.html", context)
    set_lang_cookie(response, lang)
    return response

@app.get("/send", response_class=HTMLResponse)
async def send_page(request: Request):
    lang = get_lang(request)
    context = {"request": request, "tr": translations.get(lang, translations[DEFAULT_LANG]), "lang": lang}
    return templates.TemplateResponse("send.html", context)

@app.post("/upload")
async def upload_video(request: Request, file: UploadFile = File(...), ttl: int = Form(...)):
    lang = get_lang(request)
    if len(get_user_uploads(request)) >= MAX_UPLOADS:
        return HTMLResponse(f"<script>alert('{translations[lang]['limit_reached']}'); window.location.href='/?lang={lang}';</script>")

    await process_and_save_video(request, file, ttl)
    return RedirectResponse(url=f"/list?lang={lang}", status_code=303)

@app.get("/list", response_class=HTMLResponse)
async def list_videos(request: Request, db: sqlite3.Connection = Depends(get_db)):
    lang = get_lang(request)
    user_uploads_ids = get_user_uploads(request)
    
    videos = []
    if user_uploads_ids:
        placeholders = ','.join('?' for _ in user_uploads_ids)
        cursor = db.cursor()
        cursor.execute(f"SELECT id, saved_filename FROM videos WHERE id IN ({placeholders}) ORDER BY created_at DESC", user_uploads_ids)
        videos = cursor.fetchall()

    context = {
        "request": request,
        "tr": translations.get(lang, translations[DEFAULT_LANG]),
        "lang": lang,
        "videos": videos,
        "host": request.url.netloc,
        "scheme": request.url.scheme
    }
    return templates.TemplateResponse("list.html", context)

@app.post("/delete")
async def delete_video(request: Request, id: str = Form(...), db: sqlite3.Connection = Depends(get_db)):
    lang = get_lang(request)
    user_uploads_ids = get_user_uploads(request)

    if id in user_uploads_ids:
        cursor = db.cursor()
        cursor.execute("SELECT saved_filename, thumb_filename FROM videos WHERE id = ?", (id,))
        record = cursor.fetchone()

        if record:
            import aiofiles.os
            try:
                if record["saved_filename"]: await aiofiles.os.remove(VIDEOS_DIR / record["saved_filename"])
                if record["thumb_filename"]: await aiofiles.os.remove(THUMBS_DIR / record["thumb_filename"])
            except OSError as e:
                print(f"Error deleting files for video {id}: {e}")

            cursor.execute("DELETE FROM videos WHERE id = ?", (id,))
            db.commit()
            remove_upload_from_session(request, id)
    
    return RedirectResponse(url=f"/list?lang={lang}", status_code=303)

@app.get("/record", response_class=HTMLResponse)
async def record_page(request: Request):
    lang = get_lang(request)
    context = {"request": request, "tr": translations.get(lang, translations[DEFAULT_LANG]), "lang": lang}
    return templates.TemplateResponse("record.html", context)

@app.post("/record_upload")
async def record_upload(request: Request, file: UploadFile = File(...), ttl: int = Form(...)):
    lang = get_lang(request)
    await process_and_save_video(request, file, ttl)
    return RedirectResponse(url=f"/list?lang={lang}", status_code=303)

@app.get("/f2f", response_class=HTMLResponse)
async def f2f_page(request: Request):
    lang = get_lang(request)
    context = {"request": request, "tr": translations.get(lang, translations[DEFAULT_LANG]), "lang": lang}
    return templates.TemplateResponse("f2f.html", context)

@app.post("/f2f_upload")
async def f2f_upload(request: Request, file: UploadFile = File(...), ttl: int = Form(...), question: str = Form("")):
    lang = get_lang(request)
    await process_and_save_video(request, file, ttl, question)
    return RedirectResponse(url=f"/list?lang={lang}", status_code=303)


@app.get("/stat", response_class=HTMLResponse)
async def show_stats(request: Request, db: sqlite3.Connection = Depends(get_db)):
    lang = get_lang(request)
    tr = translations.get(lang, translations[DEFAULT_LANG])
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*), SUM(size_bytes), AVG(ttl_days) FROM videos")
    count, total_size, avg_ttl = cursor.fetchone()
    
    stats = {
        tr["stat_total_videos"]: count or 0,
        tr["stat_total_size"]: round(total_size / (1024*1024), 2) if total_size else 0,
        tr["stat_avg_ttl"]: round(avg_ttl, 1) if avg_ttl else 0
    }
    
    context = {"request": request, "tr": tr, "lang": lang, "stats": stats}
    return templates.TemplateResponse("stat.html", context)


@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request):
    lang = get_lang(request)
    context = {"request": request, "tr": translations.get(lang, translations[DEFAULT_LANG]), "lang": lang}
    return templates.TemplateResponse("feedback.html", context)

# --- СТАТИКА И МЕДИА ---
app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")
app.mount("/thumbnails", StaticFiles(directory=THUMBS_DIR), name="thumbnails")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- ЗАПУСК ПРИЛОЖЕНИЯ ---
if __name__ == "__main__":
    import uvicorn
    print("Initializing database...")
    init_db()
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)