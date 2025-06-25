from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import subprocess
import os

app = FastAPI()

# Папки и статика
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")
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
                <button class="delete-btn" type="submit">🗑 Удалить</button>
            </form>
        """
        video_list_html += f"""
        <div class="card">
            <img src="{thumb}" alt="превью" class="thumb">
            <div class="info">
                <p><strong>{name}</strong></p>
                <a href="{video_link}" target="_blank" class="watch-btn">▶ Смотреть</a>
                {delete_form}
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Мой Видеообменник</title>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: #f4f4f4;
                padding: 20px;
                max-width: 800px;
                margin: auto;
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            a.button {{
                display: inline-block;
                padding: 10px 16px;
                background: #007bff;
                color: #fff;
                text-decoration: none;
                border-radius: 8px;
                margin-bottom: 20px;
                transition: background 0.3s;
            }}
            a.button:hover {{
                background: #0056b3;
            }}
            .card {{
                background: #fff;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                padding: 16px;
                margin-bottom: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .thumb {{
                max-width: 100%;
                border-radius: 10px;
                margin-bottom: 12px;
            }}
            .info {{
                text-align: center;
            }}
            .watch-btn {{
                padding: 8px 14px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                text-decoration: none;
                margin-right: 10px;
            }}
            .watch-btn:hover {{
                background: #218838;
            }}
            .delete-btn {{
                padding: 8px 14px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }}
            .delete-btn:hover {{
                background: #c82333;
            }}
            @media (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .card {{
                    padding: 12px;
                }}
            }}
        </style>
    </head>
    <body>
        <h1>🎥 Видеообменник</h1>
        <div style="text-align:center;">
            <a href="/upload" class="button">➕ Загрузить новое видео</a>
        </div>
        {video_list_html if video_list_html else '<p style="text-align:center;">Нет загруженных видео.</p>'}
    </body>
    </html>
    """


@app.get("/upload", response_class=HTMLResponse)
async def upload_form():
    return """
    <html>
    <head>
        <title>Загрузка видео</title>
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                background: #f4f4f4;
                text-align: center;
                padding: 40px;
            }
            form {
                background: white;
                display: inline-block;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            input[type="file"] {
                margin-bottom: 20px;
            }
            input[type="submit"] {
                padding: 10px 16px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background: #0056b3;
            }
            a {
                display: block;
                margin-top: 20px;
                text-decoration: none;
                color: #007bff;
            }
        </style>
    </head>
    <body>
        <form action="/upload" enctype="multipart/form-data" method="post">
            <h2>Загрузить видео</h2>
            <input name="file" type="file" accept="video/*" required><br>
            <input type="submit" value="Загрузить">
            <a href="/">⬅ Назад к списку</a>
        </form>
    </body>
    </html>
    """


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = Path("videos") / file.filename
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Генерация превью
    thumb_path = Path("thumbnails") / f"{file.filename}.jpg"
    subprocess.run([
        "ffmpeg",
        "-i", str(file_location),
        "-ss", "00:00:01.000",
        "-vframes", "1",
        "-q:v", "2",
        str(thumb_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
