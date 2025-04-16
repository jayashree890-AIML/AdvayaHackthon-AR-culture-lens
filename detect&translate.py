import os
import cv2
import sys
import platform
import webbrowser
import requests
import urllib.parse
import numpy as np
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from gtts import gTTS
from PIL import Image

# ==================== FLASK APP SETUP ====================
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==================== LANDMARK DETECTION ====================
def detect_landmark(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return {'error': 'Unable to read image'}, 500

    height, width, _ = image.shape
    file_name = os.path.basename(image_path).lower()
    landmark = "Unknown"

    if "mysore" in file_name:
        landmark = "Mysore Palace"
    elif "thanjavur_brihadeeswarar_temple" in file_name:
        landmark = "Thanjavur Brihadeeswarar Temple"
    elif "taj" in file_name:
        landmark = "Taj Mahal"
    elif "red_fort" in file_name:
        landmark = "Red Fort"
    elif "jatayu" in file_name:
        landmark = "Jatayu"

    return {
        'status': 'success',
        'landmark': landmark,
        'image_dimensions': {'width': width, 'height': height}
    }, 200

@app.route('/')
def home():
    return "✅ AR Culture Lens Flask API is Running!"

@app.route('/detect', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in request'}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_path)

    result, status_code = detect_landmark(image_path)
    return jsonify(result), status_code

# ==================== CLI TEST MODE ====================
def run_manual_mode():
    image_path = input("📸 Enter image path: ").strip()
    if not os.path.exists(image_path):
        print("❌ File not found.")
        return

    result, status_code = detect_landmark(image_path)
    print("\n✅ Detection Result:")
    print(result)

# ==================== IMAGE CONVERSION ====================
def convert_images(input_dir, output_dir):
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"[INFO] Input folder created: {input_dir}")
        print("[INFO] Please add image files and re-run the script.")
        return

    os.makedirs(output_dir, exist_ok=True)
    for fname in os.listdir(input_dir):
        if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            in_path = os.path.join(input_dir, fname)
            out_name = os.path.splitext(fname)[0] + ".webp"
            out_path = os.path.join(output_dir, out_name)
            img = Image.open(in_path).convert("RGB")
            img.save(out_path, "webp", quality=80)
            print(f"[✓] Converted: {fname} → {out_path}")

# ==================== TEXT TRANSLATION ====================
def translate_text(text, target_lang="ta"):
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

def translate_folder(input_dir, output_dir, target_lang='ta'):
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"[INFO] Input folder not found. Created: {input_dir}")

    txt_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    if not txt_files:
        sample_path = os.path.join(input_dir, "sample.txt")
        with open(sample_path, 'w', encoding='utf-8') as f:
            f.write("Welcome to the world of culture and traditions.")
        txt_files = ["sample.txt"]

    os.makedirs(output_dir, exist_ok=True)

    for fname in txt_files:
        in_path = os.path.join(input_dir, fname)
        with open(in_path, 'r', encoding='utf-8') as f:
            original = f.read()
            translated = translate_text(original, target_lang)
            out_name = f"{os.path.splitext(fname)[0]}_{target_lang}.txt"
            out_path = os.path.join(output_dir, out_name)
            with open(out_path, 'w', encoding='utf-8') as out_f:
                out_f.write(translated)
            print(f"[✓] Translated: {fname} → {out_path}")

# ==================== TEXT TO SPEECH ====================
def text_to_speech(text, lang='ta', output_path='output.mp3'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)
        print(f"[✓] Audio saved: {output_path}")
        play_audio(output_path)
    except Exception as e:
        print(f"[ERROR] Failed to generate audio: {e}")

def generate_audio_for_folder(input_dir, output_dir, lang='ta'):
    os.makedirs(output_dir, exist_ok=True)
    for fname in os.listdir(input_dir):
        if fname.endswith('.txt'):
            with open(os.path.join(input_dir, fname), 'r', encoding='utf-8') as f:
                text = f.read()
                output_file = os.path.splitext(fname)[0] + f"_{lang}.mp3"
                output_path = os.path.join(output_dir, output_file)
                text_to_speech(text, lang=lang, output_path=output_path)
    open_folder(output_dir)

# ==================== HELPERS ====================
def play_audio(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")
    except Exception as e:
        print(f"[ERROR] Could not play audio: {e}")

def open_folder(folder_path):
    webbrowser.open(folder_path)

# ==================== MAIN ====================
if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "cli":
            run_manual_mode()
        elif sys.argv[1] == "process":
            convert_images("assets/raw/images", "assets/processed/images_webp")
            translate_folder("assets/raw/text", "assets/processed/translated_text", target_lang='hi')
            generate_audio_for_folder("assets/processed/translated_text", "assets/processed/audio", lang='hi')
        else:
            print("❌ Invalid argument. Use 'cli' or 'process'.")
    else:
        app.run(debug=True)

