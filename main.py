import os
import shutil
import json
import time
from uuid import uuid4
from pathlib import Path
from fastapi import FastAPI, Request, Form, File, UploadFile, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import subprocess
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from collections import defaultdict

# === Папки и константы ===
BASE_DIR = Path(__file__).parent
VIDEOS_DIR = BASE_DIR / "videos"
THUMBS_DIR = BASE_DIR / "thumbnails"
STATIC_DIR = BASE_DIR / "static"
META_FILE = BASE_DIR / "videos.json"

for d in [VIDEOS_DIR, THUMBS_DIR, STATIC_DIR]:
    d.mkdir(exist_ok=True)
if not META_FILE.exists():
    META_FILE.write_text("[]", encoding="utf-8")

LANGS = {
    "en": "English",
    "ru": "Русский",
    "uk": "Українська",
    "pl": "Polski",
}
DEFAULT_LANG = "en"
MAX_UPLOADS = 5

translations = {
    "en": {
        
        "title": "Video Share",
        "upload": "Upload Video",
        "record": "Record Video",
        'video_quality': "Video quality",
        'quality_sd': "SD (640x480)",
        'quality_hd': "HD (1280x720)",
        'quality_fhd': "Full HD (1920x1080)",
        "start_record": "Record video",
        "stop_record": "Stop",
        "upload_btn": "Upload",
        "download_btn": "Download",
        "upload_success": "Video uploaded!",
        "upload_error": "Upload error.",
        "f2f": "Online Video Chat",
        "videochat": "Videochat",
        "enter_room": "Enter room name",
        "join": "Join",
        "copy_link": "Copy link",
        "start_call": "Start call",
        "end_call": "End call",
        "back_main": "Back to main",
        "link_copied": "Link copied!",
        "enter_room_alert": "Please enter a room name!",
        "call_ended": "Call ended",
        "stat": "Statistics",
        "feedback": "Feedback",
        "lang": "Language",
        "statistics": "Statistics",
        "mainpage": "Main Page",
        "select_file": "Select video file",
        "ttl": "Storage time (hours)",
        "upload_btn": "Upload",
        "record_btn": "Start Recording",
        "stop_btn": "Stop",
        "send_record_btn": "Send Video",
        "back_main": "Back to Main",
        "your_videos": "Your Videos",
        "copy": "Copy Link",
        "delete": "Delete",
        "copied": "Link copied!",
        "no_videos": "No videos uploaded yet.",
        "limit_reached": "Upload limit reached (max 5).",
        "question": "Your question...",
        "choose_lang": "Choose language:",
        "without_reg": "without registration, without ads",
        "subscribe": "Subscribe",
        
        'legal_notice': 'By using this site, you agree to the <a href="#">Terms of Use</a> '
        'and <a href="#">Privacy Policy</a>.<br>Do not upload personal data unless you agree '
        'to its processing.<br>Contact: <a href="mailto: wowvideoko@gmail.com"> wowvideoko@gmail.com</a>'

        

    },
    "ru": {
        
        "title": "Видеообменник",
        "upload": "Загрузить видео",
        "record": "Записать видео",
        'video_quality': "Качество видео",
        'quality_sd': "SD (640x480)",
        'quality_hd': "HD (1280x720)",
        'quality_fhd': "Full HD (1920x1080)",
        "start_record": "Записать видео",               
        "stop_record": "Стоп",
        "upload_btn": "Отправить",
        "download_btn": "Скачать",
        "upload_success": "Видео успешно загружено!",
        "upload_error": "Ошибка загрузки.",
        "f2f": "Онлайн-видеочат",
        "videochat": "Видеочат",
        "enter_room": "Введите имя комнаты",
        "join": "Войти",
        "copy_link": "Скопировать ссылку",
        "start_call": "Начать звонок",
        "end_call": "Завершить звонок",
        "back_main": "На главную",
        "link_copied": "Ссылка скопирована!",
        "enter_room_alert": "Пожалуйста, укажите имя комнаты!",
        "call_ended": "Звонок завершён",
        "statistics": "Статистика",
        "stat": "Статистика",
        "feedback": "Обратная связь",
        "lang": "Язык",
        "mainpage": "На главную",
        "select_file": "Выберите видеофайл",
        "ttl": "Время хранения (часов)",
        "upload_btn": "Загрузить",
        "record_btn": "Записать",
        "stop_btn": "Стоп",
        "send_record_btn": "Отправить видео",
        "back_main": "На главную",
        "your_videos": "Ваши видео",
        "copy": "Копировать ссылку",
        "delete": "Удалить",
        "copied": "Ссылка скопирована!",
        "no_videos": "Вы ещё не загрузили видео.",
        "limit_reached": "Достигнут лимит загрузок (максимум 5).",
        "question": "Ваш вопрос...",
        "choose_lang": "Выберите язык:",
        "without_reg": "без регистрации, без рекламы",
        "subscribe": "Подписаться",
        'legal_notice': 'Используя этот сайт, вы соглашаетесь с <a href="#">Правилами использования</a> '
        'и <a href="#">Политикой конфиденциальности</a>.<br>Не размещайте персональные данные, '
        'если не согласны с их обработкой.<br>Контакт для связи: <a href="mailto: wowvideoko@gmail.com"> wowvideoko@gmail.com</a>'

       

    },
    "uk": {
        
        "title": "Відеообмінник",
        "upload": "Завантажити відео",
        "record": "Записати відео",
        'video_quality': "Якість відео",
        'quality_sd': "SD (640x480)",
        'quality_hd': "HD (1280x720)",
        'quality_fhd': "Full HD (1920x1080)",
        "start_record": "Записати відео",
        "stop_record": "Стоп",
        "upload_btn": "Відправити",
        "download_btn": "Завантажити",
        "upload_success": "Відео завантажено!",
        "upload_error": "Помилка завантаження.",
        "f2f": "Онлайн-відеочат",
        "videochat": "Відеочат",
        "enter_room": "Введіть назву кімнати",
        "join": "Увійти",
        "copy_link": "Скопіювати посилання",
        "start_call": "Почати дзвінок",
        "end_call": "Завершити дзвінок",
        "back_main": "На головну",
        "link_copied": "Посилання скопійовано!",
        "enter_room_alert": "Будь ласка, введіть назву кімнати!",
        "call_ended": "Дзвінок завершено",
        "stat": "Статистика",
        "feedback": "Зворотний зв'язок",
        "lang": "Мова",
        "statistics": "Статiстiка",
        "mainpage": "На головну",
        "select_file": "Виберіть відеофайл",
        "ttl": "Час зберігання (годин)",
        "upload_btn": "Завантажити",
        "record_btn": "Записати",
        "stop_btn": "Стоп",
        "send_record_btn": "Відправити відео",
        "back_main": "На головну",
        "your_videos": "Ваші відео",
        "copy": "Копіювати посилання",
        "delete": "Видалити",
        "copied": "Посилання скопійоване!",
        "no_videos": "Ви ще не завантажили відео.",
        "limit_reached": "Досягнуто ліміту завантажень (максимум 5).",
        "question": "Ваше запитання...",
        "choose_lang": "Оберіть мову:",
        "without_reg": "без реєстрації, без реклами",
        "subscribe": "Підписатися",
        'legal_notice': 'Використовуючи цей сайт, ви погоджуєтеся з <a href="#">Правилами користування</a> '
        'та <a href="#">Політикою конфіденційності</a>.<br>Не розміщуйте персональні дані, '
        'якщо не погоджуєтесь з їх обробкою.<br>Контакт для звʼязку: <a href=" wowvideoko@gmail.comm">contact@wowvideo.com</a>'

    },
    "pl": {
        
        "title": "Wymiana Wideo",
        "upload": "Wyślij wideo",
        "record": "Nagraj wideo",
        'video_quality': "Jakość wideo",
        'quality_sd': "SD (640x480)",
        'quality_hd': "HD (1280x720)",
        'quality_fhd': "Full HD (1920x1080)",
        "start_record": "Nagraj wideo",
        "stop_record": "Stop",
        "upload_btn": "Wyślij",
        "download_btn": "Pobierz",
        "upload_success": "Wideo przesłane!",
        "upload_error": "Błąd przesyłania.",
        "f2f": "Wideoczat online",
        "videochat": "Wideoczat",
        "enter_room": "Wprowadź nazwę pokoju",
        "join": "Dołącz",
        "copy_link": "Kopiuj link",
        "start_call": "Rozpocznij rozmowę",
        "end_call": "Zakończ rozmowę",
        "back_main": "Powrót do głównej",
        "link_copied": "Link skopiowany!",
        "enter_room_alert": "Podaj nazwę pokoju!",
        "call_ended": "Rozmowa zakończona",
        "stat": "Statystyki",
        "feedback": "Kontakt",
        "lang": "Język",
        "statistics": "Statystyka",
        "mainpage": "Strona główna",
        "select_file": "Wybierz plik wideo",
        "ttl": "Czas przechowywania (godzin)",
        "upload_btn": "Wyślij",
        "record_btn": "Nagraj",
        "stop_btn": "Stop",
        "send_record_btn": "Wyślij wideo",
        "back_main": "Powrót",
        "your_videos": "Twoje filmy",
        "copy": "Kopiuj link",
        "delete": "Usuń",
        "copied": "Skopiowano!",
        "no_videos": "Jeszcze nie wysłałeś żadnych filmów.",
        "limit_reached": "Osiągnięto limit (max 5).",
        "question": "Twoje pytanie...",
        "choose_lang": "Wybierz język:",
        "without_reg": "bez rejestracji, bez reklam",
        "subscribe": "Subskrybuj",
        'legal_notice': 'Korzystając z tej strony, akceptujesz <a href="#">Regulamin</a> '
        'i <a href="#">Politykę prywatności</a>.<br>Nie przesyłaj danych osobowych, '
        'jeśli nie wyrażasz zgody na ich przetwarzanie.<br>Kontakt: <a href="mailto: wowvideoko@gmail.com"> wowvideoko@gmail.com</a>'

    }
}

# === App и куки ===
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="wowvideo_secret_key_2024")
rooms = defaultdict(list)

def get_lang(request: Request) -> str:
    lang = request.query_params.get("lang")
    if not lang or lang not in LANGS:
        lang = request.cookies.get("lang", DEFAULT_LANG)
    if lang not in LANGS:
        lang = DEFAULT_LANG
    return lang

def url_with_lang(path: str, lang: str) -> str:
    if "?" in path:
        return f"{path}&lang={lang}"
    return f"{path}?lang={lang}"

def get_cookie_uploads(request: Request):
    cookie = request.cookies.get("uploads")
    if not cookie:
        return []
    try:
        return json.loads(cookie)
    except:
        return []

def set_cookie_uploads(resp: Response, uploads):
    resp.set_cookie("uploads", json.dumps(uploads), max_age=60*60*24*60)

# === Маршруты ===
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(ws: WebSocket, room_id: str):
    await ws.accept()
    rooms[room_id].append(ws)
    try:
        while True:
            data = await ws.receive_text()
            # Передаём ВСЕМ кроме себя (но если hangup — всем)
            for user in rooms[room_id]:
                if '"hangup": true' in data:
                    await user.send_text(data)
                elif user is not ws:
                    await user.send_text(data)
    except WebSocketDisconnect:
        rooms[room_id].remove(ws)
        if not rooms[room_id]:
            del rooms[room_id]

@app.get("/", response_class=HTMLResponse)
async def main_landing(request: Request):
    lang = get_lang(request)
    tr = translations[lang]
    page = request.query_params.get("page", "")
    if page == "":
        return f"""
        # --- Главная
<html>
<head>
<meta charset='utf-8'><title>{tr['mainpage']}</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen flex flex-col justify-center items-center bg-gradient-to-br from-blue-200 to-purple-100"
      style="background-image: url('/static/1.jpg'); background-size: cover; background-position: center;">
<div class="flex gap-2 justify-end w-full max-w-md p-2">
  <a href='/?lang=en' class="px-2 py-1 rounded bg-blue-500 text-white hover:bg-blue-700">EN</a>
  <a href='/?lang=ru' class="px-2 py-1 rounded bg-green-500 text-white hover:bg-green-700">RU</a>
  <a href='/?lang=pl' class="px-2 py-1 rounded bg-red-500 text-white hover:bg-red-700">PL</a>
  <a href='/?lang=uk' class="px-2 py-1 rounded bg-yellow-400 text-white hover:bg-yellow-700">UK</a>
</div>
<div class="bg-white rounded-xl shadow-lg p-8 w-full max-w-md text-center">
    <h1 class="text-3xl font-bold mb-4">{tr['mainpage']}</h1>
    <div class="space-y-4">
         <a href='/?page=f2f&lang={lang}' class="block bg-pink-500 hover:bg-pink-700 text-white px-4 py-2 rounded">{tr['f2f']}</a>
        
        <a href='/?page=record&lang={lang}' class="block bg-green-500 hover:bg-green-700 text-white px-4 py-2 rounded">{tr['record']}</a>
        <a href='/?page=send&lang={lang}' class="block bg-blue-500 hover:bg-blue-700 text-white px-4 py-2 rounded">{tr['upload']}</a>

        <a href='/?page=list&lang={lang}' class="block bg-purple-500 hover:bg-purple-700 text-white px-4 py-2 rounded">{tr['your_videos']}</a>
        <a href='/?page=stat&lang={lang}' class="block bg-gray-400 hover:bg-gray-600 text-white px-4 py-2 rounded">{tr['statistics']}</a>

            </div>
        </div>
            <div class="fixed bottom-4 left-0 w-full flex justify-center pointer-events-none z-50">
            <div class="bg-white bg-opacity-90 text-gray-800 text-xs rounded-lg px-4 py-2 shadow pointer-events-auto max-w-xl 
            text-center border border-gray-300" style="backdrop-filter: blur(3px);">
                {tr['legal_notice']}
            </div>
            </div>

</body>
</html>
"""

    if page == "list":
        uploads = get_cookie_uploads(request)
        if META_FILE.exists():
            try:
                meta = json.loads(META_FILE.read_text(encoding="utf-8"))
            except:
                meta = []
        else:
            meta = []
        myvideos = [m for m in meta if m["id"] in uploads]
        videos_html = ""
        for v in myvideos:
            url = f"/videos/{v['file']}"
            thumb_url = f"/thumbnails/{v['thumb']}" if v.get('thumb') else ""
            videos_html += f"""
            <div class='bg-white rounded-lg shadow p-4 flex items-center mb-4'>
              <img src='{thumb_url}' class='w-24 h-16 object-cover rounded mr-4' onerror="this.style.display='none'">
              <div class='flex-1'>
                <a href='{url}' target='_blank' class='font-bold text-blue-700 hover:underline'>{v["filename"]}</a>
                <div class='text-xs text-gray-500 mb-2'>{time.strftime('%d.%m.%Y %H:%M', time.localtime(v["created"]))}</div>
                <form action='/delete?lang={lang}' method='post' style='display:inline'>
                  <input type='hidden' name='id' value='{v["id"]}'>
                  <button type='submit' class='bg-red-500 hover:bg-red-700 text-white px-3 py-1 rounded text-xs ml-1'>{tr["delete"]}</button>
                </form>
              </div>
            </div>
            """
        return f"""
        <html>
        <head>
            <meta charset='utf-8'>
            <title>{tr['your_videos']}</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="min-h-screen flex flex-col justify-center items-center"
                style="background-image: url('/static/4.jpg'); background-size: cover; background-position: center;">
            <div class='max-w-xl mx-auto bg-white/80 rounded-xl shadow-lg p-8 mt-12'>
            <h2 class='text-2xl font-bold mb-6 text-center'>{tr['your_videos']}</h2>
            {videos_html or f"<div class='text-center text-gray-500 mb-4'>{tr['no_videos']}</div>"}
            <div class='mt-8 text-center'>
                <a href='/?lang={lang}' class='bg-blue-600 hover:bg-blue-800 text-white px-4 py-2 rounded font-bold transition'>
                {tr['mainpage']}
                </a>
            </div>
            </div>
            <div class="fixed bottom-4 left-0 w-full flex justify-center pointer-events-none z-50">
            <div class="bg-white bg-opacity-90 text-gray-800 text-xs rounded-lg px-4 py-2 shadow pointer-events-auto max-w-xl 
            text-center border border-gray-300" style="backdrop-filter: blur(3px);">
                {tr['legal_notice']}
            </div>
            </div>
        </body>
        </html>
        """

    # --- Загрузка
    if page == "send":
        return f"""
        <html lang="{lang}">
        <head>
        <meta charset="utf-8">
        <title>{tr['upload']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body>
        <div class="min-h-screen flex flex-col justify-center items-center"
                style="background-image: url('/static/3.jpg'); background-size: cover; background-position: center;">
            <form class="bg-white rounded-xl shadow-lg p-8 w-full max-w-md text-center" method="post" enctype="multipart/form-data" action="/upload?lang={lang}">
                <h2 class="text-2xl font-bold mb-4">{tr['upload']}</h2>
                <input type="file" name="file" accept="video/*" class="mb-3" required><br>
                <label class="block mb-2">{tr['ttl']}
                <select name="ttl" class="border rounded px-2 w-28">
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="7" selected>7</option>
                    <option value="12">12</option>
                    <option value="24">24</option>
                    <option value="48">48</option>
                </select>
                </label>
                <button type="submit" class="bg-blue-700 text-white px-4 py-2 rounded">{tr['upload_btn']}</button>
                <div class="mt-10">
                    <a href='/?lang={lang}' class='bg-blue-600 hover:bg-blue-800 text-white px-4 py-2 rounded font-bold transition'>{tr['mainpage']}</a>
                </div>
            </div>
        </div>
            <div class="fixed bottom-4 left-0 w-full flex justify-center pointer-events-none z-50">
            <div class="bg-white bg-opacity-90 text-gray-800 text-xs rounded-lg px-4 py-2 shadow pointer-events-auto max-w-xl 
            text-center border border-gray-300" style="backdrop-filter: blur(3px);">
                {tr['legal_notice']}
            </div>
            </div>
        </body>
        </html>
        """

    # --- Страница обратной связи
    if page == "feedback":
        return f"""
        <html lang="{lang}">
        <head>
        <meta charset="utf-8"><title>{tr['feedback']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="min-h-screen flex flex-col justify-center items-center bg-gray-50">
            <div class="bg-white rounded-xl shadow-lg p-8 w-full max-w-md text-center">
                <h2 class="text-2xl font-bold mb-4">{tr['feedback']}</h2>
                <p class="mb-4">Email: <a href="mailto:wowvideoko@gmail.com" class="text-blue-600 hover:underline">wowvideoko@gmail.com</a></p>
                <div class="mt-6"><a href='/?lang={lang}' class='text-blue-600 hover:underline'>{tr['mainpage']}</a></div>
            </div>
            <div class="fixed bottom-4 left-0 w-full flex justify-center pointer-events-none z-50">
            <div class="bg-white bg-opacity-90 text-gray-800 text-xs rounded-lg px-4 py-2 shadow pointer-events-auto max-w-xl 
            text-center border border-gray-300" style="backdrop-filter: blur(3px);">
                {tr['legal_notice']}
            </div>
            </div>            
        </body></html>
        """
    # --- Список видео (страница list)
    if page == "list":
        uploads = get_cookie_uploads(request)
        if META_FILE.exists():
            try:
                meta = json.loads(META_FILE.read_text(encoding="utf-8"))
            except:
                meta = []
        else:
            meta = []
        myvideos = [m for m in meta if m["id"] in uploads]
        videos_html = ""
        for v in myvideos:
            url = f"/videos/{v['file']}"
            thumb_url = f"/thumbnails/{v['thumb']}" if v.get('thumb') else ""
            videos_html += f"""
            <div class='bg-white rounded-lg shadow p-4 flex items-center mb-4'>
              <img src='{thumb_url}' class='w-24 h-16 object-cover rounded mr-4' onerror="this.style.display='none'">
              <div class='flex-1'>
                <a href='{url}' target='_blank' class='font-bold text-blue-700 hover:underline'>{v["filename"]}</a>
                <div class='text-xs text-gray-500 mb-2'>{time.strftime('%d.%m.%Y %H:%M', time.localtime(v["created"]))}</div>
                <form action='/delete?lang={lang}' method='post' style='display:inline'>
                  <input type='hidden' name='id' value='{v["id"]}'>
                  <button type='submit' class='bg-red-500 hover:bg-red-700 text-white px-3 py-1 rounded text-xs ml-1'>{tr["delete"]}</button>
                </form>
              </div>
            </div>
            """
        return f"""
        <html><head><meta charset='utf-8'><title>{tr['your_videos']}</title>
        <script src="https://cdn.tailwindcss.com"></script></head>
        <body class="min-h-screen bg-gray-50 py-8">
          <div class='max-w-xl mx-auto'>
            <h2 class='text-2xl font-bold mb-6 text-center'>{tr['your_videos']}</h2>
            {videos_html or f"<div class='text-center text-gray-500'>{tr['no_videos']}</div>"}
            <div class='mt-8 text-center'><a href='/?lang={lang}' class='text-blue-600 hover:underline'>{tr['mainpage']}</a></div>
          </div>
            <div class="fixed bottom-4 left-0 w-full flex justify-center pointer-events-none z-50">
            <div class="bg-white bg-opacity-90 text-gray-800 text-xs rounded-lg px-4 py-2 shadow pointer-events-auto max-w-xl 
            text-center border border-gray-300" style="backdrop-filter: blur(3px);">
                {tr['legal_notice']}
            </div>
            </div>
        </body></html>
        """


    # --- Статистика
    if page == "stat":
        try:
            import geoip2.database
            geo_reader = geoip2.database.Reader(str(BASE_DIR / "geoip2.mmdb"))
        except Exception:
            geo_reader = None
        stats = {}
        if META_FILE.exists():
            try:
                meta = json.loads(META_FILE.read_text(encoding="utf-8"))
            except:
                meta = []
        else:
            meta = []
        for v in meta:
            ip = v.get("ip", "")
            if geo_reader and ip:
                try:
                    country = geo_reader.country(ip).country.name
                except:
                    country = "Other"
            else:
                country = "Unknown"
            stats[country] = stats.get(country, 0) + 1
        stats_html = "<ul class='mb-4'>" + "".join(f"<li>{c}: {n}</li>" for c, n in sorted(stats.items(), key=lambda x: -x[1])) + "</ul>"
        return f"""
        <html><head><meta charset='utf-8'><title>{tr['stat']}</title>
        <script src="https://cdn.tailwindcss.com"></script></head>
        
        <body class="min-h-screen flex flex-col justify-center items-center bg-gradient-to-br from-blue-200 to-purple-100"
         style="background-image: url('/static/6.jpg'); background-size: cover; background-position: center;">
          <div class='max-w-xl mx-auto'>
            <h2 class='text-2xl font-bold mb-6 text-center'>{tr['stat']}</h2>
            {stats_html or "<div class='text-center text-gray-500'>No data</div>"}
            <div class="mt-6 flex justify-center">
                <a href='/?lang={lang}' class='bg-blue-600 hover:bg-blue-800 text-white px-4 py-2 rounded font-bold transition'>
                    {tr['mainpage']}
                </a>
            </div>
            <div class="fixed bottom-4 left-0 w-full flex justify-center pointer-events-none z-50">
            <div class="bg-white bg-opacity-90 text-gray-800 text-xs rounded-lg px-4 py-2 shadow pointer-events-auto max-w-xl 
            text-center border border-gray-300" style="backdrop-filter: blur(3px);">
                {tr['legal_notice']}
            </div>
            </div>

        </body></html>
        """
    # --- Онлайн запись видео
    if page == "record":
        return f"""
        <html lang="{lang}">
        <head>
        <meta charset="utf-8">
        <title>{tr['record']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="min-h-screen flex flex-col justify-center items-center"
            style="background-image: url('/static/5.jpg'); background-size: cover; background-position: center;">
        <div class="bg-white rounded-xl shadow-lg p-8 w-full max-w-md text-center">
            <h2 class="text-2xl font-bold mb-4">{tr['record']}</h2>
            <div class="mb-2">
                <label for="quality" class="block mb-1">{tr['video_quality']}</label>
                <select id="quality" class="border rounded px-2 w-40 mb-2">
                    <option value="sd">{tr['quality_sd']}</option>
                    <option value="hd">{tr['quality_hd']}</option>
                    <option value="fhd">{tr['quality_fhd']}</option>
                </select>
            </div>
            <div class="mb-2">
                <label for="ttl" class="block mb-1">{tr['ttl']}</label>
                <select id="ttl" class="border rounded px-2 w-28">
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="7" selected>7</option>
                    <option value="12">12</option>
                    <option value="24">24</option>
                    <option value="48">48</option>
                </select>
            </div>
            <video id="recvideo" width="320" height="240" autoplay muted class="rounded mb-2"></video>
            <div class="mb-4">
                <button id="startBtn" class="bg-green-600 text-white px-4 py-2 rounded">{tr['start_record']}</button>
                <button id="stopBtn" class="bg-gray-400 text-white px-4 py-2 rounded ml-2" style="display:none">{tr['stop_record']}</button>
            </div>
            <div class="mb-4">
                <button id="uploadBtn" class="bg-blue-700 text-white px-4 py-2 rounded" style="display:none">{tr['upload_btn']}</button>
                <button id="downloadBtn" class="bg-blue-400 text-white px-4 py-2 rounded ml-2" style="display:none">{tr['download_btn']}</button>
            </div>
            <div class="mt-6 flex justify-center">
                <a href='/?lang={lang}' class='bg-blue-600 hover:bg-blue-800 text-white px-4 py-2 rounded font-bold transition'>
                    {tr['mainpage']}
                </a>
            </div>
        </div>
        <script>
        let stream, recorder, chunks = [], recordedBlob = null;
        let startBtn = document.getElementById('startBtn');
        let stopBtn = document.getElementById('stopBtn');
        let uploadBtn = document.getElementById('uploadBtn');
        let downloadBtn = document.getElementById('downloadBtn');
        let video = document.getElementById('recvideo');
        let qualitySel = document.getElementById('quality');
        let ttlSel = document.getElementById('ttl');

        function getConstraints() {{
            const val = qualitySel.value;
            if (val === 'hd') {{
                return {{ video: {{width:1280, height:720}}, audio:true }};
            }} else if (val === 'fhd') {{
                return {{ video: {{width:1920, height:1080}}, audio:true }};
            }} else {{
                return {{ video: {{width:640, height:480}}, audio:true }};
            }}
        }}

        startBtn.onclick = async function() {{
            stream = await navigator.mediaDevices.getUserMedia(getConstraints());
            video.srcObject = stream;
            recorder = new MediaRecorder(stream);
            chunks = [];
            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = function() {{
                recordedBlob = new Blob(chunks, {{type: "video/webm"}});
                video.srcObject = null;
                video.src = URL.createObjectURL(recordedBlob);
                uploadBtn.style.display = '';
                downloadBtn.style.display = '';
            }};
            recorder.start();
            startBtn.style.display = 'none';
            stopBtn.style.display = '';
            qualitySel.disabled = true;
            ttlSel.disabled = true;
        }};

        stopBtn.onclick = function() {{
            recorder.stop();
            stream.getTracks().forEach(t => t.stop());
            stopBtn.style.display = 'none';
            qualitySel.disabled = false;
            ttlSel.disabled = false;
        }};

        uploadBtn.onclick = function() {{
            if (!recordedBlob) return;
            let formData = new FormData();
            formData.append("file", recordedBlob, "recorded_video.webm");
            let ttlValue = ttlSel.value;
            formData.append("ttl", ttlValue);

            fetch("/upload?lang={lang}", {{
                method: "POST",
                body: formData
            }}).then(resp => {{
                if(resp.ok) {{
                    alert("{tr['upload_success']}");
                }} else {{
                    alert("{tr['upload_error']}");
                }}
            }});
        }};

        downloadBtn.onclick = function() {{
            if (!recordedBlob) return;
            let url = URL.createObjectURL(recordedBlob);
            let a = document.createElement('a');
            a.href = url;
            a.download = 'recorded_video.webm';
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        }};
        </script>
            <div class="fixed bottom-4 left-0 w-full flex justify-center pointer-events-none z-50">
            <div class="bg-white bg-opacity-90 text-gray-800 text-xs rounded-lg px-4 py-2 shadow pointer-events-auto max-w-xl 
            text-center border border-gray-300" style="backdrop-filter: blur(3px);">
                {tr['legal_notice']}
            </div>
            </div>
        </body>
        </html>
        """


    if page == "f2f":
        return f"""
        <html lang="{lang}">
        <head>
        <meta charset="utf-8">
        <title>{tr['f2f']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="min-h-screen flex flex-col justify-center items-center"
            style="background-image: url('/static/2.jpg'); background-size: cover; background-position: center;">
        <div class="bg-white rounded-xl shadow-lg p-8 w-full max-w-lg text-center">
            <h1 class="text-2xl font-bold mb-4">{tr['videochat']}</h1>
            <div class="mb-4">
                <input id="room" type="text" placeholder="{tr['enter_room']}" class="border p-2 rounded mb-2 w-1/2"/>
                <button id="joinBtn" class="bg-blue-600 text-white px-4 py-2 rounded mb-4 ml-2">{tr['join']}</button>
            </div>
            <div class="mb-4 flex justify-center items-center">
                <input id="invite-link" type="text" readonly class="border px-2 py-1 rounded w-3/4" value="" />
                <button onclick="copyInvite()" class="bg-blue-500 text-white px-3 py-1 rounded ml-2">{tr['copy_link']}</button>
            </div>
            <div id="chatArea" style="display:none;">
                <div class="flex gap-4 justify-center mb-4">
                    <video id="localVideo" autoplay muted playsinline class="rounded-lg border"></video>
                    <video id="remoteVideo" autoplay playsinline class="rounded-lg border"></video>
                </div>
                <button id="startBtn" class="bg-green-600 text-white px-4 py-2 rounded">{tr['start_call']}</button>
                <button id="hangupBtn" class="bg-gray-400 text-white px-4 py-2 rounded ml-2" disabled>{tr['end_call']}</button>
            </div>
            <div class="mt-6 flex justify-center">
                <a href='/?lang={lang}' class='bg-blue-600 hover:bg-blue-800 text-white px-4 py-2 rounded font-bold transition'>
                    {tr['mainpage']}
                </a>
            </div>
        </div>
        <script>
        function copyInvite() {{
            const url = location.origin + "/?page=f2f&lang={lang}&room=" + encodeURIComponent(document.getElementById('room').value);
            document.getElementById('invite-link').value = url;
            navigator.clipboard.writeText(url);
            alert("{tr['link_copied']}");
        }}
        let ws, pc, localStream;
        let started = false;

        document.getElementById('joinBtn').onclick = function() {{
            const room = document.getElementById('room').value.trim();
            if (!room) return alert("{tr['enter_room_alert']}");
           let wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
            ws = new WebSocket(wsProtocol + window.location.host + "/ws/" + encodeURIComponent(room));

            ws.onmessage = async (evt) => {{
                let msg = JSON.parse(evt.data);
                if (msg.sdp) {{
                    await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp));
                    if (msg.sdp.type === "offer") {{
                        let answer = await pc.createAnswer();
                        await pc.setLocalDescription(answer);
                        ws.send(JSON.stringify({{sdp: pc.localDescription}}));
                    }}
                }}
                if (msg.candidate) {{
                    await pc.addIceCandidate(msg.candidate);
                }}
                if (msg.hangup) {{
                    if (pc) pc.close();
                    if (localStream) {{
                        localStream.getTracks().forEach(t => t.stop());
                        document.getElementById('localVideo').srcObject = null;
                        document.getElementById('remoteVideo').srcObject = null;
                    }}
                    started = false;
                    document.getElementById('hangupBtn').disabled = true;
                    alert("{tr['call_ended']}");
                }}
            }};
            document.getElementById('chatArea').style.display = '';
        }};

        document.getElementById('startBtn').onclick = async function () {{
            if (started) return;
            pc = new RTCPeerConnection();
            pc.onicecandidate = (event) => {{
                if (event.candidate) ws.send(JSON.stringify({{candidate: event.candidate}}));
            }};
            pc.ontrack = (event) => {{
                document.getElementById('remoteVideo').srcObject = event.streams[0];
            }};
            localStream = await navigator.mediaDevices.getUserMedia({{video:true, audio:true}});
            document.getElementById('localVideo').srcObject = localStream;
            localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
            let offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            ws.send(JSON.stringify({{sdp: pc.localDescription}}));
            started = true;
            document.getElementById('hangupBtn').disabled = false;
        }};

        document.getElementById('hangupBtn').onclick = function () {{
            if (ws) ws.send(JSON.stringify({{hangup: true}}));
            if (pc) pc.close();
            if (localStream) {{
                localStream.getTracks().forEach(t => t.stop());
                document.getElementById('localVideo').srcObject = null;
                document.getElementById('remoteVideo').srcObject = null;
            }}
            started = false;
            document.getElementById('hangupBtn').disabled = true;
        }};
        </script>
                <div class="fixed bottom-4 left-0 w-full flex justify-center pointer-events-none z-50">
            <div class="bg-white bg-opacity-90 text-gray-800 text-xs rounded-lg px-4 py-2 shadow pointer-events-auto max-w-xl 
            text-center border border-gray-300" style="backdrop-filter: blur(3px);">
                {tr['legal_notice']}
            </div>
            </div>
        </body>
        </html>
        """




   # --- Fallback
    return RedirectResponse(f"<h1>Страница не найдена</h1><a href='/?lang={lang}'>На главную</a>", status_code=404)

# ------ Загрузка файла ------
@app.post("/upload", response_class=HTMLResponse)
async def upload_video(request: Request, file: UploadFile = File(...), ttl: int = Form(...)):
    lang = get_lang(request)
    tr = translations[lang]
    uploads = get_cookie_uploads(request)
    if len(uploads) >= MAX_UPLOADS:
        return HTMLResponse(f"<script>alert('{tr['limit_reached']}');window.location='/?lang={lang}';</script>")
    id = str(uuid4())[:12]
    filename = f"{id}_{file.filename.replace(' ', '_')}"
    file_path = VIDEOS_DIR / filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # Превью через ffmpeg
    thumb_name = f"{id}.jpg"
    thumb_path = THUMBS_DIR / thumb_name
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(file_path),
            "-ss", "00:00:02", "-vframes", "1",
            "-vf", "scale=400:-1", str(thumb_path)
        ], check=True)
    except Exception:
        thumb_name = ""
    # Метаданные
    if META_FILE.exists():
        try:
            meta = json.loads(META_FILE.read_text(encoding="utf-8"))
            if not isinstance(meta, list): meta = []
        except: meta = []
    else:
        meta = []
    meta.append({
        "id": id,
        "file": filename,
        "filename": file.filename,
        "thumb": thumb_name,
        "created": time.time(),
        "ttl": int(ttl),
        "ip": request.client.host,
    })
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    uploads.append(id)
    resp = RedirectResponse(url_with_lang("/?page=list", lang), status_code=303)
    set_cookie_uploads(resp, uploads)
    return resp

# ------ Удаление ------
@app.post("/delete", response_class=HTMLResponse)
async def delete_video(request: Request, id: str = Form(...)):
    lang = get_lang(request)
    uploads = get_cookie_uploads(request)
    if id not in uploads:
        return RedirectResponse(url_with_lang("/?page=list", lang), status_code=303)
    if META_FILE.exists():
        try:
            meta = json.loads(META_FILE.read_text(encoding="utf-8"))
        except:
            meta = []
    else:
        meta = []
    newmeta = []
    for v in meta:
        if v["id"] == id:
            try:
                (VIDEOS_DIR / v["file"]).unlink(missing_ok=True)
                if v.get("thumb"):
                    (THUMBS_DIR / v["thumb"]).unlink(missing_ok=True)
            except:
                pass
        else:
            newmeta.append(v)
    META_FILE.write_text(json.dumps(newmeta, ensure_ascii=False, indent=2), encoding="utf-8")
    uploads = [x for x in uploads if x != id]
    resp = RedirectResponse(url_with_lang("/?page=list", lang), status_code=303)
    set_cookie_uploads(resp, uploads)
    return resp

# ------ Видео и статика ------
app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")
app.mount("/thumbnails", StaticFiles(directory=THUMBS_DIR), name="thumbnails")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ------ Record upload ------
@app.post("/record_upload", response_class=HTMLResponse)
async def record_upload(request: Request, file: UploadFile = File(...), ttl: int = Form(...), filename: str = Form(...)):
    lang = get_lang(request)
    uploads = get_cookie_uploads(request)
    if len(uploads) >= MAX_UPLOADS:
        return RedirectResponse(url_with_lang("/", lang), status_code=303)
    id = str(uuid4())[:12]
    safe_fn = filename.replace(' ', '_')
    file_path = VIDEOS_DIR / f"{id}_{safe_fn}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # Превью через ffmpeg
    thumb_name = f"{id}.jpg"
    thumb_path = THUMBS_DIR / thumb_name
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(file_path),
            "-ss", "00:00:02", "-vframes", "1",
            "-vf", "scale=400:-1", str(thumb_path)
        ], check=True)
    except Exception:
        thumb_name = ""
    # Метаданные
    if META_FILE.exists():
        try:
            meta = json.loads(META_FILE.read_text(encoding="utf-8"))
            if not isinstance(meta, list): meta = []
        except: meta = []
    else:
        meta = []
    meta.append({
        "id": id,
        "file": f"{id}_{safe_fn}",
        "filename": filename,
        "thumb": thumb_name,
        "created": time.time(),
        "ttl": int(ttl),
        "ip": request.client.host,
    })
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    uploads.append(id)
    resp = RedirectResponse(url_with_lang("/?page=list", lang), status_code=303)
    set_cookie_uploads(resp, uploads)
    return resp

# ------ F2F upload ------
@app.post("/f2f_upload", response_class=HTMLResponse)
async def f2f_upload(request: Request, file: UploadFile = File(...), ttl: int = Form(...), filename: str = Form(...), question: str = Form("")):
    lang = get_lang(request)
    uploads = get_cookie_uploads(request)
    if len(uploads) >= MAX_UPLOADS:
        return RedirectResponse(url_with_lang("/", lang), status_code=303)
    id = str(uuid4())[:12]
    safe_fn = filename.replace(' ', '_')
    file_path = VIDEOS_DIR / f"{id}_{safe_fn}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # Превью через ffmpeg
    thumb_name = f"{id}.jpg"
    thumb_path = THUMBS_DIR / thumb_name
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(file_path),
            "-ss", "00:00:02", "-vframes", "1",
            "-vf", "scale=400:-1", str(thumb_path)
        ], check=True)
    except Exception:
        thumb_name = ""
    # Метаданные
    if META_FILE.exists():
        try:
            meta = json.loads(META_FILE.read_text(encoding="utf-8"))
            if not isinstance(meta, list): meta = []
        except: meta = []
    else:
        meta = []
    meta.append({
        "id": id,
        "file": f"{id}_{safe_fn}",
        "filename": filename,
        "question": question,
        "thumb": thumb_name,
        "created": time.time(),
        "ttl": int(ttl),
        "ip": request.client.host,
    })
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    uploads.append(id)
    resp = RedirectResponse(url_with_lang("/?page=list", lang), status_code=303)
    set_cookie_uploads(resp, uploads)
    return resp
