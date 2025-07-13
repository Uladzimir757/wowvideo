from fastapi import FastAPI, Request, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import json, shutil
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent           # это /opt/render/project/src
TEMPLATES_DIR = BASE_DIR.parent / "templates"  
STATIC    = BASE_DIR  / "static"
JS_DIR    = STATIC / "js"
IMG_DIR   = STATIC / "img"
UPLOADS   = STATIC / "uploads"
RECORDS   = STATIC / "records"
TEMPLATES = Jinja2Templates(directory=str(TEMPLATES_DIR))
STATS     = BASE_DIR  / "stats.json"
META      = BASE_DIR  / "videos.json"

# создаём папки и файлы
for d in (STATIC, JS_DIR, IMG_DIR, UPLOADS, RECORDS):
    d.mkdir(parents=True, exist_ok=True)
if not STATS.exists():  STATS.write_text("{}", encoding="utf-8")
if not META.exists():   META.write_text("[]", encoding="utf-8")

# переводы
translations = {
    
    "en": {
        "title":"Video Exchange","upload":"Upload Video","videos":"Your Videos","delete":"Delete",
        "f2f":"Video Chat","record":"Record Video","stop":"Stop","send":"Send Recording",
        "back":"Main","enter_room":"Enter room","join":"Join","copy_link":"Copy link",
        "start_call":"Start call","end_call":"End call","link_copied":"Link copied!",
        "media_error":"Camera access denied","ttl_label":"Storage hours","no_videos":"No videos","statistics":"Statistics", 
        "legal_notice": "By using this site, you agree to the Terms of Service and Cookie Policy.",
        "hide_notice":  "Hide notice", "contact_label": "Contact us",
    },"ru": {
        "title":"Видеообменник","upload":"Загрузить видео","videos":"Ваши видео","delete":"Удалить",
        "f2f":"Онлайн-видеочат","record":"Записать видео","stop":"Стоп","send":"Отправить запись",
        "back":"На главную","enter_room":"Введите комнату","join":"Войти","copy_link":"Скопировать ссылку",
        "start_call":"Начать звонок","end_call":"Завершить звонок","link_copied":"Ссылка скопирована!",
        "media_error":"Нет доступа к камере","ttl_label":"Часы хранения","no_videos":"Нет видео","statistics":"Статистика",
        "legal_notice": "Используя этот сайт, вы соглашаетесь с условиями использования и политикой cookie.",
        "hide_notice":  "Скрыть уведомление","contact_label": "Обратная связь",
        
    },
    "pl": {
        "title":"Wymiana Wideo","upload":"Prześlij wideo","videos":"Twoje filmy","delete":"Usuń",
        "f2f":"Czat wideo","record":"Nagraj wideo","stop":"Stop","send":"Wyślij nagranie",
        "back":"Główna","enter_room":"Podaj pokój","join":"Dołącz","copy_link":"Kopiuj link",
        "start_call":"Rozpocznij","end_call":"Zakończ","link_copied":"Link skopiowany!",
        "media_error":"Brak dostępu do kamery","ttl_label":"Godz. przech.","no_videos":"Brak wideo","statistics":"Statystyki",
        "legal_notice": "Korzystając z tej strony, akceptujesz Regulamin i Politykę plików cookie.",
        "hide_notice":  "Ukryj powiadomienie","contact_label": "Kontakt",
    },
    "uk": {
        "title":"Відеообмінник","upload":"Завантажити відео","videos":"Ваші відео","delete":"Видалити",
        "f2f":"Відеочат","record":"Записати відео","stop":"Стоп","send":"Відправити запис",
        "back":"На головну","enter_room":"Введіть кімнату","join":"Вхід","copy_link":"Копіювати лінк",
        "start_call":"Почати дзвінок","end_call":"Закінчити дзвінок","link_copied":"Лінк скопійовано!",
        "media_error":"Нема доступу до камери","ttl_label":"Год. збер.","no_videos":"Нема відео","statistics":"Статистика",
        "legal_notice": "Використовуючи цей сайт, ви погоджуєтесь з Умовами використання та Політикою cookie.",
        "hide_notice":  "Приховати повідомлення","contact_label": "Зв’язатися",
    }
}
LANGS = list(translations.keys())
DEFAULT_LANG = LANGS[0]
rooms = defaultdict(list)

def get_lang(req: Request):
    lang = req.query_params.get("lang") or req.cookies.get("lang") or DEFAULT_LANG
    return lang if lang in LANGS else DEFAULT_LANG

def save_stat(path: str):
    data = json.loads(STATS.read_text())
    rec = data.get(path,{"count":0,"last":None})
    rec["count"] += 1
    rec["last"] = datetime.utcnow().isoformat()
    data[path] = rec
    STATS.write_text(json.dumps(data, ensure_ascii=False, indent=2))

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS)), name="uploads")
app.mount("/records", StaticFiles(directory=str(RECORDS)), name="records")

@app.middleware("http")
async def stats_mw(req: Request, call_next):
    if not req.url.path.startswith(("/static","/uploads","/records","/ws")):
        save_stat(req.url.path)
    return await call_next(req)

@app.websocket("/ws/{room_id}")
async def ws_endpoint(ws: WebSocket, room_id: str):
    await ws.accept()
    rooms[room_id].append(ws)
    try:
        while True:
            msg = await ws.receive_text()
            for p in rooms[room_id]:
                if p is not ws:
                    await p.send_text(msg)
    except WebSocketDisconnect:
        rooms[room_id].remove(ws)
        if not rooms[room_id]:
            del rooms[room_id]

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    lang = get_lang(request); tr = translations[lang]
    page = request.query_params.get("page","")
    ctx  = {"request":request,"lang":lang,"tr":tr,"tr_json":json.dumps(tr,ensure_ascii=False)}
    if page=="f2f":
        return TEMPLATES.TemplateResponse("f2f.html", ctx)
    if page=="record":
        return TEMPLATES.TemplateResponse("record.html", ctx)
    if page=="upload":
        return TEMPLATES.TemplateResponse("upload.html", ctx)
    if page=="list":
        vids = sorted(p.name for p in UPLOADS.iterdir() if p.is_file())
        return TEMPLATES.TemplateResponse("list.html", {**ctx,"videos":vids})
    if page=="stat":
        stats = json.loads(STATS.read_text())
        return TEMPLATES.TemplateResponse("stat.html", {**ctx,"stats":stats})
    vids = sorted(p.name for p in UPLOADS.iterdir() if p.is_file())
    return TEMPLATES.TemplateResponse("main.html", {**ctx,"videos":vids})

@app.post("/upload")
async def upload_video(file: UploadFile=File(...), ttl:int=Form(24), lang:str=Form(DEFAULT_LANG)):
    name = f"{uuid4().hex}_{file.filename}"
    dst  = UPLOADS/name
    with dst.open("wb") as f: shutil.copyfileobj(file.file, f)
    return RedirectResponse(f"/?page=list&lang={lang}",303)

@app.post("/f2f_upload")
async def f2f_upload(file: UploadFile=File(...), ttl:int=Form(24), lang:str=Form(DEFAULT_LANG)):
    name = f"{uuid4().hex}_{file.filename}"
    dst  = RECORDS/name
    with dst.open("wb") as f: shutil.copyfileobj(file.file, f)
    return RedirectResponse(f"/?page=f2f&lang={lang}",303)

@app.delete("/videos/{fname}")
async def delete_video(fname:str):
    (UPLOADS/fname).unlink(missing_ok=True)
    return JSONResponse({"ok":True})
