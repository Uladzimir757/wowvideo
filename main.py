from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
import subprocess

app = FastAPI()

# Папка для хранения видео
UPLOAD_DIR = "videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/videos", StaticFiles(directory=UPLOAD_DIR), name="videos")

# Папка для превью
THUMB_DIR = "thumbnails"
os.makedirs(THUMB_DIR, exist_ok=True)
app.mount("/thumbnails", StaticFiles(directory=THUMB_DIR), name="thumbnails")

# 🌐 HTML-форма загрузки
@app.get("/", response_class=HTMLResponse)
def upload_form():
    return """
    <html>
        <head><title>Загрузка видео</title></head>
        <body>
            <h1>Загрузить видео</h1>
            <form action="/upload" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept="video/*" required><br><br>
                <input type="submit" value="Загрузить">
            </form>
        </body>
    </html>
    """

# 📤 Обработчик загрузки + генерация превью
@app.post("/upload")
async def upload_video(request: Request, file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Генерация превью с помощью ffmpeg (5-я секунда)
    thumb_name = f"{os.path.splitext(file.filename)[0]}.jpg"
    thumb_path = os.path.join(THUMB_DIR, thumb_name)
    subprocess.run([
        "ffmpeg",
        "-i", file_path,
        "-ss", "00:00:05.000",
        "-vframes", "1",
        "-q:v", "2",
        thumb_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return HTMLResponse(f"""
        <html>
            <body>
                <h2>Видео загружено!</h2>
                <p><a href="/videos/{file.filename}">Смотреть видео</a></p>
                <p>Превью:</p>
                <img src="/thumbnails/{thumb_name}" width="320"><br><br>
                <p><a href="/">Загрузить другое</a></p>
            </body>
        </html>
    """)

# ▶️ Просмотр видео
@app.get("/videos/{filename}")
async def serve_video(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4")
    return HTMLResponse("<h2>Видео не найдено</h2>", status_code=404)
