from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os, uuid, urllib.parse, requests
from gtts import gTTS

app = FastAPI()

# CORS setup for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Detect landmark by filename
def detect_landmark(image_path: str) -> str:
    fname = os.path.basename(image_path).lower()
    if "mysore" in fname:
        return "Mysore Palace"
    elif "thanjavur" in fname:
        return "Thanjavur Brihadeeswarar Temple"
    elif "taj" in fname:
        return "Taj Mahal"
    elif "red_fort" in fname:
        return "Red Fort"
    elif "jatayu" in fname:
        return "Jatayu"
    return "Unknown"

# Translate using Google Translate API (free endpoint)
def translate_text(text: str, target_lang: str = "ta") -> str:
    base_url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target_lang,
        "dt": "t",
        "q": text,
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    response = requests.get(url)
    result = response.json()
    return ''.join([item[0] for item in result[0]])

# TTS with gTTS
def text_to_speech(text: str, lang: str, output_path: str):
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)

@app.get("/")
def root():
    return {"message": "✅ FastAPI Landmark Detection with Text is running"}

@app.post("/api/detect")
async def detect(
    image: UploadFile = File(...),
    textfile: UploadFile = File(...),
    lang: str = Form("ta")
):
    # Save image
    image_filename = f"{uuid.uuid4()}_{image.filename}"
    image_path = os.path.join(UPLOAD_FOLDER, image_filename)
    with open(image_path, "wb") as f:
        f.write(await image.read())

    # Save text
    text_filename = f"{uuid.uuid4()}_{textfile.filename}"
    text_path = os.path.join(UPLOAD_FOLDER, text_filename)
    with open(text_path, "wb") as f:
        f.write(await textfile.read())

    # Detect landmark
    landmark = detect_landmark(image_path)
    if landmark == "Unknown":
        return JSONResponse(status_code=200, content={"landmark": "Unknown"})

    # Read and translate text file
    with open(text_path, "r", encoding="utf-8") as tf:
        original_text = tf.read()
    translated_text = translate_text(original_text, target_lang=lang)

    # Convert to speech
    audio_filename = os.path.splitext(image_filename)[0] + f"_{lang}.mp3"
    audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)
    text_to_speech(translated_text, lang=lang, output_path=audio_path)

    return {
        "landmark": landmark,
        "original_text": original_text,
        "translation": translated_text,
        "audio_file": audio_filename
    }

@app.get("/uploads/{filename}")
def serve_file(filename: str):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
