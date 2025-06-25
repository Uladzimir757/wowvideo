from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import subprocess
import os
import json
import time

app = FastAPI()

VIDEOS_DIR = Path("videos")
THUMBS_DIR = Path("thumbnails")
META_FILE = Path("videos.json")

VIDEOS_DIR.mkdir(exist_ok=True)
THUMBS_DIR.mkdir(exist_ok=True)

app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")


def load_meta():
    if META_FILE.exists():
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_meta(meta):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f)

def cleanup_expired():
    meta = load_meta()
    now = int(time.time())
    changed = False
    for fname in list(meta.keys()):
        expire_at = meta[fname]["uploaded_at"] + meta[fname]["ttl"]
        if now > expire_at:
            # Удаляем файл и превью
            vpath = VIDEOS_DIR / fname
            tpath = THUMBS_DIR / (fname + ".jpg")
            if vpath.exists():
                vpath.unlink()
            if tpath.exists():
                tpath.unlink()
            del meta[fname]
            changed = True
    if changed:
        save_meta(meta)
    return meta

@app.get("/", response_class=HTMLResponse)
async def index():
    meta = cleanup_expired()
    now = int(time.time())

    video_items = ""
    for fname, data in meta.items():
        expire_at = data["uploaded_at"] + data["ttl"]
        left = expire_at - now
        hours = left // 3600
        minutes = (left % 3600) // 60
        thumb = f"/thumbnails/{fname}.jpg"
        video_link = f"/videos/{fname}"

        video_items += f"""
        <div class='bg-white rounded-lg shadow hover:shadow-lg transition p-4'>
            <img src='{thumb}' alt='Превью' class='w-full h-48 object-cover rounded-md mb-4 border' />
            <p class='text-gray-800 font-medium mb-2 truncate'>{fname}</p>
            <div class='text-sm text-gray-500 mb-2'>Удалится через: {hours} ч {minutes} мин</div>
            <div class='flex justify-between'>
                <a href='{video_link}' target='_blank' class='bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm'>
                    ▶️ Смотреть
                </a>
                <form method='post' action='/delete/{fname}'>
                    <button type='submit' class='bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded text-sm'>
                        🗑 Удалить
                    </button>
                </form>
            </div>
        </div>
        """

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang='ru'>
    <head>
      <meta charset='UTF-8' />
      <meta name='viewport' content='width=device-width, initial-scale=1.0' />
      <title>🎥 Видеообменник</title>
      <script src='https://cdn.tailwindcss.com'></script>
    </head>
    <body class='bg-gray-100 font-sans leading-normal tracking-normal'>
      <div class='max-w-5xl mx-auto p-4'>
        <h1 class='text-3xl font-bold text-center text-gray-800 mb-6'>🎥 Мои видео</h1>
        <div class='flex justify-center mb-6'>
          <a href='/upload'
             class='bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg shadow-md transition'>
            📤 Загрузить видео
          </a>
        </div>
        <div class='grid gap-6 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3'>
          {video_items if video_items else "<p class='text-center text-gray-500 mt-10'>Нет загруженных видео.</p>"}
        </div>
      </div>
    </body>
    </html>
    """)


@app.get("/upload", response_class=HTMLResponse)
async def upload_form():
    return """
    <!DOCTYPE html>
    <html lang='ru'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Загрузка видео</title>
        <script src='https://cdn.tailwindcss.com'></script>
    </head>
    <body class='bg-gray-100 font-sans min-h-screen flex items-center justify-center'>
        <div class='bg-white shadow-lg rounded-lg p-8 w-full max-w-md'>
            <h2 class='text-2xl font-bold mb-6 text-gray-800 text-center'>Загрузить видео</h2>
            <form action='/upload' enctype='multipart/form-data' method='post' class='space-y-4'>
                <input name='file' type='file' accept='video/*' required
                       class='block w-full text-gray-700 border border-gray-300 rounded p-2 focus:ring-2 focus:ring-blue-400'>
                <label class='block text-gray-700 mb-1'>Срок хранения:</label>
                <select name='ttl'
                        class='w-full border border-gray-300 rounded p-2 text-gray-700'>
                    <option value='10800'>3 часа</option>
                    <option value='25200'>7 часов</option>
                    <option value='54000'>15 часов</option>
                    <option value='86400' selected>1 сутки</option>
                    <option value='259200'>3 суток</option>
                </select>
                <button type='submit'
                        class='w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded mt-4 font-semibold shadow transition'>
                    📤 Загрузить
                </button>
            </form>
            <a href='/' class='block text-center text-blue-500 mt-6 hover:underline'>← Назад к списку</a>
        </div>
    </body>
    </html>
    """


@app.post("/upload")
async def upload_video(file: UploadFile = File(...), ttl: int = Form(...)):
    file_path = VIDEOS_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    thumbnail_path = THUMBS_DIR / f"{file.filename}.jpg"
    subprocess.run([
        "ffmpeg",
        "-i", str(file_path),
        "-ss", "00:00:01.000",
        "-vframes", "1",
        str(thumbnail_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Добавляем в videos.json
    meta = load_meta()
    meta[file.filename] = {
        "uploaded_at": int(time.time()),
        "ttl": ttl
    }
    save_meta(meta)

    return RedirectResponse("/", status_code=303)


@app.post("/delete/{filename}")
async def delete_video(filename: str):
    video_path = VIDEOS_DIR / filename
    thumb_path = THUMBS_DIR / f"{filename}.jpg"

    # Удаляем из файлов и мета
    if video_path.exists():
        video_path.unlink()
    if thumb_path.exists():
        thumb_path.unlink()
    meta = load_meta()
    if filename in meta:
        del meta[filename]
        save_meta(meta)

    return RedirectResponse("/", status_code=303)
