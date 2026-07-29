"""
AI-Powered Skin & Nail Disease Detection API
Built with Flask + Groq Vision API
"""

import os
import json
import base64
import logging
from io import BytesIO

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from PIL import Image
import groq

# ── Load environment ──────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Groq client ───────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not set. The /analyze endpoint will fail.")

client = groq.Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ── Allowed image types & max size (10 MB) ────────────────────────
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_image(image_bytes: bytes, max_dim: int = 1024) -> bytes:
    """Resize image so longest side ≤ max_dim and re-encode as JPEG."""
    img = Image.open(BytesIO(image_bytes))
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()
# history file-save analysis record
HISTORY_FILE = "analysis_history.json"

def save_analysis(data, analysis_type):
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        else:
            history = []

        from datetime import datetime

        record = {
            "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "type": analysis_type,
            "disease": data.get("disease_name"),
            "probability": data.get("probability"),
            "confidence": data.get("confidence"),
            "severity": data.get("severity")
        }

        history.append(record)

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

    except Exception as e:
        logger.error(f"Could not save history: {e}")

# ── Skin analysis prompt ──────────────────────────────────────────
SKIN_PROMPT = """IMPORTANT: Do NOT use <think> tags or any reasoning. Output ONLY the JSON object with no other text.

You are a board-certified dermatology AI assistant. Analyze the provided skin image and return a **valid JSON object only** — no markdown, no code fences, no extra text, no thinking.

The JSON must follow this exact schema:
{
  "disease_name": "string — the most likely skin condition (e.g., 'Actinic Keratosis', 'Basal Cell Carcinoma', 'Melanoma', 'Psoriasis', 'Eczema', 'Acne Vulgaris', 'Rosacea', 'Vitiligo', 'Fungal Infection', 'Herpes Simplex', 'Urticaria', 'Normal Skin — No Disease Detected')",
  "probability": "integer — the likelihood that this specific condition is present (0–100)",
  "confidence": "integer — your overall confidence in the analysis/assessment (0–100)",
  "description": "string — a brief 1-2 sentence description of the condition",
  "symptoms": ["array of strings — common symptoms, 3-5 items"],
  "causes": ["array of strings — common causes or risk factors, 2-4 items"],
  "treatments": ["array of strings — common treatments or management strategies, 2-4 items"],
  "severity": "string — one of: 'Mild', 'Moderate', 'Severe', or 'Unknown'",
  "contagious": "boolean — whether the condition is contagious",
  "consult_doctor": "boolean — true if the user should consult a dermatologist"
}
IMPORTANT RULES:
- If the image does not appear to be a skin lesion/rash/condition, set disease_name to 'No Skin Condition Detected' and confidence to 0.
- Always err on the side of recommending a doctor visit when uncertain.
- Be honest about confidence — low-quality images should get low confidence scores.
- Never fabricate a diagnosis — if unsure, set disease_name to 'Uncertain — Consult a Dermatologist' and consult_doctor to true."""


# ── Nail analysis prompt ──────────────────────────────────────────
NAIL_PROMPT = """IMPORTANT: Do NOT use <think> tags or any reasoning. Output ONLY the JSON object with no other text.

You are a board-certified dermatology AI assistant specializing in nail disorders. Analyze the provided nail image and return a **valid JSON object only** — no markdown, no code fences, no extra text, no thinking.

The JSON must follow this exact schema:
{
  "disease_name": "string — the most likely nail condition (e.g., 'Onychomycosis (Fungal Nail Infection)', 'Ingrown Toenail', 'Nail Psoriasis', 'Paronychia', 'Leukonychia', 'Beau Lines', 'Onycholysis', 'Clubbing', 'Koilonychia (Spoon Nails)', 'Melanonychia', 'Subungual Hematoma', 'Yellow Nail Syndrome', 'Normal Nail — No Disease Detected')",
  "probability": "integer — the likelihood that this specific condition is present (0–100)",
  "confidence": "integer — your overall confidence in the analysis/assessment (0–100)",
  "description": "string — a brief 1-2 sentence description of the condition",
  "symptoms": ["array of strings — common symptoms, 3-5 items"],
  "causes": ["array of strings — common causes or risk factors, 2-4 items"],
  "treatments": ["array of strings — common treatments or management strategies, 2-4 items"],
  "severity": "string — one of: 'Mild', 'Moderate', 'Severe', or 'Unknown'",
  "contagious": "boolean — whether the condition is contagious",
  "consult_doctor": "boolean — true if the user should consult a dermatologist"
}
IMPORTANT RULES:
- If the image does not appear to be a nail or nail condition, set disease_name to 'No Nail Condition Detected' and confidence to 0.
- Always err on the side of recommending a doctor visit when uncertain.
- Be honest about confidence — low-quality images should get low confidence scores.
- Never fabricate a diagnosis — if unsure, set disease_name to 'Uncertain — Consult a Dermatologist' and consult_doctor to true."""


@app.route("/health", methods=["GET"])
def health():
    """Simple health-check endpoint."""
    return jsonify({"status": "ok", "message": "Skin & Nail Disease Detection API is running"})


@app.route("/analyze", methods=["POST"])
def analyze():
    """Accept a skin image file, send to Groq Vision, return structured JSON."""
    return _analyze_image(SKIN_PROMPT)


@app.route("/analyze-nail", methods=["POST"])
def analyze_nail():
    """Accept a nail image file, send to Groq Vision, return structured JSON."""
    return _analyze_image(NAIL_PROMPT)

def _analyze_image(prompt: str):
    """Shared logic for analyzing an image with a given prompt."""
    # ── Validate request ───────────────────────────────────────────
    if "image" not in request.files:
        return jsonify({"error": "No image file provided. Use field name 'image'."}), 400

    file = request.files["image"]

    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, webp."}), 400

    image_bytes = file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        return jsonify({"error": "Image too large. Maximum size is 10 MB."}), 400

    if not client:
        return jsonify({"error": "Server misconfigured: GROQ_API_KEY not set."}), 500

    # ── Compress & encode ─────────────────────────────────────────
    try:
        compressed = compress_image(image_bytes)
        b64_image = base64.b64encode(compressed).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{b64_image}"
    except Exception as e:
        logger.exception("Image processing failed")
        return jsonify({"error": f"Image processing failed: {str(e)}"}), 400

    # ── Call Groq Vision ──────────────────────────────────────────
    try:
        completion = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url, "detail": "high"},
                        },
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        raw = completion.choices[0].message.content.strip()
        logger.info(f"Groq raw response (first 200 chars): {raw[:200]}")

        # ── Parse JSON from response ──────────────────────────────
        import re

        # Strategy: The Qwen model outputs <think> reasoning blocks.
        # The JSON may be embedded inside or after the think block.
        # We directly find the outermost JSON object in the raw response.

        # Find the first '{' and last '}' in the entire response
        json_start = raw.find('{')
        json_end = raw.rfind('}')

        result = None
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = raw[json_start:json_end + 1]
            # Try to parse the JSON directly first
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError:
                # JSON might be truncated - try to find the last valid JSON
                # by progressively trimming from the end
                for trim_end in range(len(json_str), json_start, -1):
                    candidate = json_str[:trim_end]
                    # Try to close any open brackets/braces
                    open_braces = candidate.count('{') - candidate.count('}')
                    open_brackets = candidate.count('[') - candidate.count(']')
                    if open_braces > 0:
                        candidate += '}' * open_braces
                    if open_brackets > 0:
                        candidate += ']' * open_brackets
                    # Remove trailing comma before closing
                    candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
                    try:
                        result = json.loads(candidate)
                        break
                    except json.JSONDecodeError:
                        continue

        if result is None:
            raise json.JSONDecodeError("Could not extract valid JSON from response", raw, 0)

        # Validate required fields
        required = [
            "disease_name", "probability", "confidence", "description", "symptoms",
            "causes", "treatments", "severity", "contagious", "consult_doctor"
        ]
        for field in required:
            if field not in result:
                result[field] = None
        # Determine whether this is a skin or nail analysis
        if prompt == SKIN_PROMPT:
           analysis_type = "Skin"
        else:
           analysis_type = "Nail"

        # Save analysis history
        save_analysis(result, analysis_type)

        return jsonify(result), 200
        
    except json.JSONDecodeError:
        logger.error(f"Failed to parse Groq response as JSON: {raw}")
        return jsonify({
            "error": "Failed to parse AI response. Please try again.",
            "raw_response": raw
        }), 500
    except Exception as e:
        logger.exception("Groq API call failed")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500
        
# Dashboard Statistics API
@app.route("/dashboard-stats", methods=["GET"])
def dashboard_stats():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        else:
            history = []

        from datetime import datetime

        today = datetime.now().strftime("%d-%m-%Y")

        total_analyses = len(history)

        skin_analyses = sum(
            1 for item in history if item["type"] == "Skin"
        )

        nail_analyses = sum(
            1 for item in history if item["type"] == "Nail"
        )

        today_analyses = sum(
            1 for item in history
            if item["date"].startswith(today)
        )

        return jsonify({
            "total_analyses": total_analyses,
            "skin_analyses": skin_analyses,
            "nail_analyses": nail_analyses,
            "today_analyses": today_analyses,
            "history": history
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
