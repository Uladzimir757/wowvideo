from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import subprocess

app = FastAPI()

app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")

Path("videos").mkdir(exist_ok=True)
Path("thumbnails").mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index():
    video_items = ""
    for file in Path("videos").iterdir():
        name = file.name
        thumb = f"/thumbnails/{name}.jpg"
        video_link = f"/videos/{name}"
        video_items += f"""
        <div class='bg-white rounded-lg shadow hover:shadow-lg transition p-4'>
            <img src='{thumb}' alt='Превью' class='w-full h-48 object-cover rounded-md mb-4 border' />
            <p class='text-gray-800 font-medium mb-2 truncate'>{name}</p>
            <div class='flex justify-between'>
                <a href='{video_link}' target='_blank' class='bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm'>
                    ▶️ Смотреть
                </a>
                <form method='post' action='/delete/{name}'>
                    <button type='submit' class='bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded text-sm'>
                        🗑 Удалить
                    </button>
                </form>
            </div>
        </div>
        """

    return HTMLResponse(f"""    <!DOCTYPE html>
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
    """")


@app.get("/upload", response_class=HTMLResponse)
async def upload_form():
    return """    <html>
    <head>
        <title>Загрузка видео</title>
    </head>
    <body style='font-family:sans-serif; padding:40px;'>
        <h2>Загрузить видео</h2>
        <form action='/upload' enctype='multipart/form-data' method='post'>
            <input name='file' type='file' accept='video/*' required><br><br>
            <input type='submit' value='Загрузить'>
        </form>
        <br><a href='/'>Назад к списку</a>
    </body>
    </html>
    """


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_path = Path("videos") / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    thumbnail_path = Path("thumbnails") / f"{file.filename}.jpg"
    subprocess.run([
        "ffmpeg",
        "-i", str(file_path),
        "-ss", "00:00:01.000",
        "-vframes", "1",
        str(thumbnail_path)
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
