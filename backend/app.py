from flask import Flask, render_template, request, jsonify, session
import os
from docx import Document
import google.generativeai as genai
from deep_translator import GoogleTranslator
from datetime import datetime, timedelta
import json
from google.cloud import texttospeech
from gtts import gTTS
import tempfile
import requests
import time
import pyttsx3
import asyncio
import edge_tts
import re, threading
# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = "supersecurekey"  # required for session-based features

# --- Load API key ---
import config
genai.configure(api_key=config.GEMINI_API_KEY)

# --- Initialize Gemini Model ---
model = genai.GenerativeModel("gemini-2.0-flash")  # ✅ define 'model' here

# --- Global Document Text Storage ---
DOCUMENT_TEXT = ""
HISTORY_FILE = "history.json"
# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = "supersecurekey"

# --- Define History Folder ---
app.config["HISTORY_FOLDER"] = os.path.join(os.getcwd(), "history")

# Create folder if it doesn't exist
if not os.path.exists(app.config["HISTORY_FOLDER"]):
    os.makedirs(app.config["HISTORY_FOLDER"])
# ---------- ROUTES ----------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/qa')
def qa():
    return render_template('qa.html')

@app.route('/security')
def security():
    return render_template('security.html')


@app.route('/process-doc', methods=['POST'])
def process_doc():
    global DOCUMENT_TEXT
    file = request.files.get('file')

    if not file:
        return jsonify({"error": "No file uploaded."}), 400

    try:
        # ✅ Read document
        doc = Document(file)
        DOCUMENT_TEXT = " ".join([p.text for p in doc.paragraphs])

        if not DOCUMENT_TEXT.strip():
            return jsonify({"error": "The document is empty or unreadable."}), 400

        # 🔍 Enhanced AI Prompt
        prompt = (
            "You are a helpful and clear legal assistant AI. Summarize this legal document "
            "in very simple, human-friendly terms. Then identify and extract key points:\n"
            "- 📅 Due Dates or Deadlines\n"
            "- 💰 Penalties or Fees\n"
            "- ⚖️ Rights or Entitlements\n"
            "- 📄 Obligations or Responsibilities\n\n"
            "Provide the summary in structured, bullet-point format with clear sections.\n\n"
            f"Document Text:\n{DOCUMENT_TEXT}"
        )

        # ✨ Generate structured output with Gemini
        result = model.generate_content(prompt)
        summary = result.text.strip()

        # ✅ Save to session
        session['last_summary'] = summary

        # ✅ Also save to history for later view
        save_to_history(file.filename, summary)

        print(f"✅ Saved summary for: {file.filename}")

        return jsonify({"summary": summary})

    except Exception as e:
        print(f"⚠️ Document processing failed: {e}")
        return jsonify({
            "error": "Failed to process document.",
            "details": str(e)
        }), 500



# ---------- Translation ----------
@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        target_lang = data.get('target_lang', '')

        if not text or not target_lang:
            return jsonify({'error': 'Missing text or target language.'}), 400

        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return jsonify({'translated_text': translated})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

import asyncio
import edge_tts
import os
import re
from flask import jsonify, request

@app.route("/tts", methods=["POST"])
def tts():
    """
    Text-to-Speech Route
    Uses Microsoft Edge TTS voices (very natural & multilingual).
    """
    try:
        data = request.get_json()
        text = data.get("text", "").strip()
        lang = data.get("lang", "en").strip()

        if not text:
            return jsonify({"error": "No text provided."}), 400

        # 🧹 Clean text: remove emojis & unsupported chars
        clean_text = re.sub(r"[^\w\s\u0900-\u0d7f.,!?;:()\"'-]", "", text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        # 🎙 Voice mapping (you can add more if needed)
        voice_map = {
            "en": "en-IN-NeerjaNeural",      # Indian English (female)
            "hi": "hi-IN-SwaraNeural",       # Hindi (natural)
            "te": "te-IN-ShrutiNeural",      # Telugu (smooth)
            "ta": "ta-IN-PallaviNeural",     # Tamil
            "kn": "kn-IN-PriyaNeural",       # Kannada
            "bn": "bn-IN-TanishaaNeural"     # Bengali
        }
        voice = voice_map.get(lang, "en-IN-NeerjaNeural")

        # 📁 Ensure static directory exists
        os.makedirs("static", exist_ok=True)
        output_path = os.path.join("static", "tts_output.mp3")

        # 🔊 Async TTS generation
        async def generate_tts():
            communicate = edge_tts.Communicate(clean_text, voice=voice, rate="+0%")
            await communicate.save(output_path)

        asyncio.run(generate_tts())

        print(f"✅ TTS generated successfully using {voice}")
        return jsonify({"audio_url": "/static/tts_output.mp3"})

    except Exception as e:
        print("❌ TTS Error:", e)
        return jsonify({"error": f"TTS failed: {str(e)}"}), 500

# ---------- Q&A ----------
@app.route('/qa-answer', methods=['POST'])
def qa_answer():
    global DOCUMENT_TEXT
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400

    conversation = session.get('conversation', [])
    chat_prompt = (
        "You are an assistant that answers questions about a legal document.\n\n"
        f"Document Content:\n{DOCUMENT_TEXT}\n\n"
        "Previous conversation:\n"
        + "\n".join([f"Q: {q}\nA: {a}" for q, a in conversation])
        + f"\nUser question: {question}\nProvide a clear and simple answer."
    )

    try:
        response = model.generate_content(chat_prompt)
        answer = response.text.strip()
        conversation.append((question, answer))
        session['conversation'] = conversation
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# HISTORY LIST
# -----------------------------
@app.route("/history", methods=["GET", "POST"])
def history():
    history_file = os.path.join(app.config["HISTORY_FOLDER"], "history.json")

    # --- 🧹 If "Clear History" button is clicked ---
    if request.method == "POST":
        try:
            # Delete the history file safely
            if os.path.exists(history_file):
                os.remove(history_file)

            # Recreate an empty history file for future use
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

            return jsonify({"message": "🗑️ History cleared successfully!"}), 200

        except Exception as e:
            print(f"⚠️ Failed to clear history: {e}")
            return jsonify({"error": f"Failed to clear history: {e}"}), 500

    # --- 🗂 Normal GET request: Display grouped history ---
    try:
        if not os.path.exists(history_file):
            return render_template("history.html", history_groups={})

        with open(history_file, "r", encoding="utf-8") as f:
            history_data = json.load(f)

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        history_groups = {"Today": [], "Yesterday": [], "Earlier": []}

        for entry in history_data:
            entry_date = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S").date()
            if entry_date == today:
                history_groups["Today"].append(entry)
            elif entry_date == yesterday:
                history_groups["Yesterday"].append(entry)
            else:
                history_groups["Earlier"].append(entry)

        # Sort each section by most recent first
        for group in history_groups.values():
            group.sort(key=lambda x: x["timestamp"], reverse=True)

        return render_template("history.html", history_groups=history_groups)

    except Exception as e:
        print(f"⚠️ Error loading history: {e}")
        return f"<h3>⚠️ Error loading history: {e}</h3>"

# ---------- Clear Conversation ----------
@app.route('/clear-conversation', methods=['POST'])
def clear_conversation():
    session.pop('conversation', None)
    return jsonify({'message': 'Conversation cleared successfully.'})


# ---------- Security Page Data Clear ----------
@app.route('/clear-data', methods=['POST'])
def clear_data():
    try:
        for folder in ['uploads', 'history']:
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    os.remove(os.path.join(folder, f))
        session.clear()
        return jsonify({'message': 'All data cleared securely ✅'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def save_to_history(filename, summary):
    try:
        history_dir = app.config["HISTORY_FOLDER"]
        os.makedirs(history_dir, exist_ok=True)  # ✅ Ensure folder exists
        history_file = os.path.join(history_dir, "history.json")

        # Load previous history if it exists
        history = []
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

        # Add new entry
        history.append({
            "filename": filename or "Untitled",
            "summary": summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # ✅ Save file
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        print("✅ History saved successfully!")

    except Exception as e:
        print(f"⚠️ Failed to save history: {e}")


# ---------- MAIN ----------
if __name__ == '__main__':
    app.run(debug=True)
