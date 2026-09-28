"""
AI-Powered Skin & Nail Disease Detection API
Built with Flask + Groq Vision API
"""

import os
import re
import json
import base64
import logging
import threading
from datetime import datetime
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
# Verify the exact model ID on the GroqCloud models page
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not set. The /analyze endpoints will fail.")

client = groq.Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ── Allowed image types & max size (10 MB) ────────────────────────
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_image(image_bytes: bytes, max_dim: int = 1536) -> bytes:
    """Resize image so longest side <= max_dim and re-encode as JPEG."""
    img = Image.open(BytesIO(image_bytes))
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# ── History (JSON file, guarded by a lock) ────────────────────────
HISTORY_FILE = "analysis_history.json"
history_lock = threading.Lock()


def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_analysis(data: dict, analysis_type: str) -> None:
    try:
        record = {
            "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "type": analysis_type,
            "disease": data.get("disease_name"),
            "probability": data.get("probability"),
            "confidence": data.get("confidence"),
            "severity": data.get("severity"),
        }
        with history_lock:
            history = load_history()
            history.append(record)
            with open(HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=4)
    except Exception as e:
        logger.error(f"Could not save history: {e}")


# ── Skin analysis prompt ──────────────────────────────────────────
SKIN_PROMPT = """Output ONLY a valid JSON object. No markdown, no code fences, no extra text.

You are a dermatology assistant. Carefully examine the skin image. Before naming any condition, describe what you actually see (lesion type, color, size, distribution, borders, texture, stage such as papules/vesicles/pustules/crusts). Base your answer only on these visible features, not on which conditions are most common.

Consider a broad differential, including infectious (viral such as chickenpox/varicella, measles, shingles, hand-foot-mouth, herpes simplex; bacterial such as impetigo, cellulitis; fungal such as ringworm, tinea), inflammatory (eczema, psoriasis, dermatitis, urticaria), acne/rosacea, pigmentary (vitiligo, melasma), and neoplastic (actinic keratosis, basal cell carcinoma, melanoma) conditions.

Key distinguishing hints:
- Chickenpox: widespread itchy lesions at DIFFERENT stages at once (red spots, fluid-filled vesicles "dewdrop on a rose petal", crusted scabs) across trunk, face and limbs.
- Herpes simplex: localized cluster of vesicles, usually around lips or genitals.
- Acne: comedones, papules and pustules on face, chest or back, without fluid-filled vesicles or crusting in multiple stages.

Schema (keys in this order):
{
  "visual_findings": "string - 2-3 sentences describing only what is visible",
  "disease_name": "string - most likely condition based on the findings",
  "alternatives": ["array of 1-3 other possible conditions"],
  "probability": integer 0-100,
  "confidence": integer 0-100,
  "description": "string - 1-2 sentences",
  "symptoms": ["3-5 items"],
  "causes": ["2-4 items"],
  "treatments": ["2-4 items"],
  "severity": "Mild" | "Moderate" | "Severe" | "Unknown",
  "contagious": boolean,
  "consult_doctor": boolean
}

Rules:
- If the image is not skin, use disease_name 'No Skin Condition Detected' and confidence 0.
- If the skin looks healthy, use 'Normal Skin — No Disease Detected'.
- Low-quality images get low confidence. If unsure, use 'Uncertain — Consult a Dermatologist' and consult_doctor true.
- Do not default to a common diagnosis; commit only if the visible features support it."""


# ── Nail analysis prompt ──────────────────────────────────────────
NAIL_PROMPT = """Output ONLY a valid JSON object. No markdown, no code fences, no extra text.

You are a dermatology assistant specializing in nails. Carefully examine the nail image. Before naming any condition, describe what you actually see (color, thickness, surface texture, shape/curvature, lines or pits, separation from the nail bed, surrounding skin swelling or redness). Base your answer only on these visible features.

Do NOT default to fungal infection. Onychomycosis requires thickened, discolored (yellow/brown), crumbly nails, often with debris under the nail. Consider the full range: fungal, bacterial paronychia, psoriasis (pitting, oil-drop spots), onycholysis, Beau's lines (transverse grooves), koilonychia (spoon shape), clubbing, leukonychia (white spots/bands), melanonychia (dark streak, consider melanoma), splinter hemorrhages, subungual hematoma, ingrown nail, brittle nails, trauma, or a healthy nail.

Schema (keys in this order):
{
  "visual_findings": "string - 2-3 sentences describing only what is visible",
  "disease_name": "string - most likely condition based on the findings",
  "alternatives": ["array of 1-3 other possible conditions"],
  "probability": integer 0-100,
  "confidence": integer 0-100,
  "description": "string - 1-2 sentences",
  "symptoms": ["3-5 items"],
  "causes": ["2-4 items"],
  "treatments": ["2-4 items"],
  "severity": "Mild" | "Moderate" | "Severe" | "Unknown",
  "contagious": boolean,
  "consult_doctor": boolean
}

Rules:
- If the image is not a nail, use disease_name 'No Nail Condition Detected' and confidence 0.
- If the nail looks healthy, use 'Normal Nail — No Disease Detected'.
- Low-quality images get low confidence. If unsure, use 'Uncertain — Consult a Dermatologist' and consult_doctor true.
- Do not default to a common diagnosis; commit only if the visible features support it."""


REQUIRED_FIELDS = [
    "visual_findings", "disease_name", "alternatives", "probability",
    "confidence", "description", "symptoms", "causes", "treatments",
    "severity", "contagious", "consult_doctor",
]


# ── JSON extraction helpers ───────────────────────────────────────
def extract_json(raw: str):
    """Extract a JSON object from a model response, tolerating <think> blocks
    and truncated output. Returns a dict or None."""
    # Remove reasoning blocks so braces inside them don't confuse parsing
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    # Handle an unclosed <think> (truncated output)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL) if "<think>" in cleaned else cleaned
    # Remove code fences if the model added them anyway
    cleaned = re.sub(r"```(?:json)?", "", cleaned).strip()

    # If cleaning removed everything, fall back to the raw text
    if "{" not in cleaned:
        cleaned = raw

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    json_str = cleaned[start:end + 1]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Attempt to repair truncated JSON by trimming and closing brackets
    for trim_end in range(len(json_str), 0, -1):
        candidate = json_str[:trim_end]
        open_braces = candidate.count("{") - candidate.count("}")
        open_brackets = candidate.count("[") - candidate.count("]")
        candidate += "]" * max(open_brackets, 0)
        candidate += "}" * max(open_braces, 0)
        candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def normalize_result(result: dict) -> dict:
    """Fill missing fields and coerce types."""
    for field in REQUIRED_FIELDS:
        if field not in result:
            result[field] = None

    for key in ("probability", "confidence"):
        try:
            result[key] = int(result[key])
        except (TypeError, ValueError):
            result[key] = None

    for key in ("alternatives", "symptoms", "causes", "treatments"):
        if not isinstance(result[key], list):
            result[key] = [] if result[key] is None else [str(result[key])]

    return result


# ── Routes ────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    """Simple health-check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "Skin & Nail Disease Detection API is running",
        "model": GROQ_MODEL,
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    """Accept a skin image file, send to Groq Vision, return structured JSON."""
    return _analyze_image(SKIN_PROMPT, "Skin")


@app.route("/analyze-nail", methods=["POST"])
def analyze_nail():
    """Accept a nail image file, send to Groq Vision, return structured JSON."""
    return _analyze_image(NAIL_PROMPT, "Nail")


def _analyze_image(prompt: str, analysis_type: str):
    """Shared logic for analyzing an image with a given prompt."""
    # ── Validate request ──────────────────────────────────────────
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
    raw = ""
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            temperature=0.2,
            max_tokens=4096,
        )

        raw = (completion.choices[0].message.content or "").strip()
        logger.info(f"Groq raw response (first 300 chars): {raw[:300]}")

        result = extract_json(raw)
        if result is None:
            raise json.JSONDecodeError("Could not extract valid JSON from response", raw, 0)

        result = normalize_result(result)
        save_analysis(result, analysis_type)

        return jsonify(result), 200

    except json.JSONDecodeError:
        logger.error(f"Failed to parse Groq response as JSON: {raw}")
        return jsonify({
            "error": "Failed to parse AI response. Please try again.",
            "raw_response": raw,
        }), 500
    except Exception as e:
        logger.exception("Groq API call failed")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


# ── Dashboard statistics ──────────────────────────────────────────
@app.route("/dashboard-stats", methods=["GET"])
def dashboard_stats():
    try:
        with history_lock:
            history = load_history()

        today = datetime.now().strftime("%d-%m-%Y")

        return jsonify({
            "total_analyses": len(history),
            "skin_analyses": sum(1 for i in history if i.get("type") == "Skin"),
            "nail_analyses": sum(1 for i in history if i.get("type") == "Nail"),
            "today_analyses": sum(1 for i in history if i.get("date", "").startswith(today)),
            "history": history,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)