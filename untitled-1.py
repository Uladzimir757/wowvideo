from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import subprocess
import os

app = FastAPI()

# Статические файлы
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")

# Создание папок
Path("videos").mkdir(exist_ok=True)
Path("thumbnails").mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def list_videos():
    video_list_html = ""
    for file in Path("videos").iterdir():
        name = file.name
        thumb = f"/thumbnails/{name}.jpg"
        video_link = f"/videos/{name}"
        delete_form = f"""
            <form action="/delete/{name}" method="post" style="display:inline;">
                <button type="submit">Удалить</button>
            </form>
        """
        video_list_html += f"""
        <div style="margin-bottom: 20px;">
            <p><strong>{name}</strong></p>
            <a href="{video_link}" target="_blank">Смотреть видео</a><br>
            <img src="{thumb}" alt="превью" style="max-height:180px;"><br>
            {delete_form}
        </div>
        <hr>
        """
    return f"""
        <html>
        <head><title>Мои видео</title></head>
        <body>
            <h1>Загруженные видео</h1>
            <a href="/upload">Загрузить новое видео</a><br><br>
            {video_list_html if video_list_html else '<p>Нет загруженных видео.</p>'}
        </body>
        </html>
    """


@app.get("/upload", response_class=HTMLResponse)
async def upload_form():
    return """
        <html>
        <body>
            <h2>Загрузить видео</h2>
            <form action="/upload" enctype="multipart/form-data" method="post">
                <input name="file" type="file">
                <input type="submit" value="Загрузить">
            </form>
            <br><a href="/">Назад к списку</a>
        </body>
        </html>
    """


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(file: UploadFile = File(...)):
    file_location = Path("videos") / file.filename
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Генерация превью через ffmpeg
    thumbnail_path = Path("thumbnails") / f"{file.filename}.jpg"
    subprocess.run([
        "ffmpeg",
        "-i", str(file_location),
        "-ss", "00:00:01.000",
        "-vframes", "1",
        str(thumbnail_path)
    ])

    return RedirectResponse("/", status_code=303)


@app.post("/delete/{filename}")
async def delete_video(filename: str):
    video_path = Path("videos") / filename
    thumb_path = Path("thumbnails") / f"{filename}.jpg"

    if video_path.exists():
        video_path.unlink()
    if thumb_path.exists():
        thumb_path.unlink()

    return RedirectResponse("/", status_code=303)
