from flask import Flask, render_template, request, jsonify
import re
import google.generativeai as genai
import pandas as pd
from PIL import Image
import io
import json
import os
from datetime import datetime
import base64
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY").strip()

# Set up Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        "gemini-2.5-flash"  # DO NOT FUCKING CHANGE THIS FROM 2.5 FLASH NO MATTER WHAT NO EXCEPTIONS!
    )  # DO NOT FUCKING CHANGE THIS FROM 2.5 FLASH NO MATTER WHAT NO EXCEPTIONS!
else:
    raise ValueError("GEMINI_API_KEY not found. Please set it in web_app/.env")

# Define custom prompts for different document types
PROMPTS = {
    "US Passport": """You are an expert at extracting structured data from US passports. Analyze this passport image and return ONLY a valid JSON object with the following fields, no extra text or markdown:
{
  "passport_type": "string",
  "passport_number": "string",
  "surname": "string",
  "given_names": "string",
  "nationality": "string",
  "date_of_birth": "YYYY-MM-DD",
  "place_of_birth": "string",
  "sex": "string",
  "date_of_issue": "YYYY-MM-DD",
  "date_of_expiration": "YYYY-MM-DD",
  "issuing_authority": "string",
  "machine_readable_zone": "string"
}""",
    "Japanese Passport": """You are an expert at extracting structured data from Japanese passports. Analyze this passport image and return ONLY a valid JSON object with the following fields, no extra text or markdown:
{
  "passport_type": "string",
  "passport_number": "string",
  "surname": "string",
  "given_names": "string",
  "nationality": "string",
  "date_of_birth": "YYYY-MM-DD",
  "place_of_birth": "string",
  "sex": "string",
  "date_of_issue": "YYYY-MM-DD",
  "date_of_expiration": "YYYY-MM-DD",
  "issuing_authority": "string",
  "machine_readable_zone": "string",
  "signature": "boolean",
  "note_from_issuing_authority": "string",
  "annotations_endorsements": "string"
}""",
    "US Driver's License": """You are an expert at extracting structured data from US driver's licenses. Analyze this driver's license image and return ONLY a valid JSON object with the following fields, no extra text or markdown:
{
  "state": "string",
  "document_type": "string",
  "license_number": "string",
  "surname": "string",
  "given_names": "string",
  "date_of_birth": "YYYY-MM-DD",
  "sex": "string",
  "date_of_issue": "YYYY-MM-DD",
  "date_of_expiration": "YYYY-MM-DD",
  "issuing_authority": "string",
  "address": "string",
  "class": "string",
  "endorsements": "string",
  "restrictions": "string",
  "signature": "boolean",
  "document_discriminator": "string",
  "height": "string",
  "eye_color": "string",
  "real_id_indicator": "boolean"
}""",
    "US Permanent Resident Card": """You are an expert at extracting structured data from US Permanent Resident Cards (Green Cards). Analyze this card image and return ONLY a valid JSON object with the following fields, no extra text or markdown:
{
  "category": "string",
  "card_number": "string",
  "surname": "string",
  "given_names": "string",
  "sex": "string",
  "date_of_birth": "YYYY-MM-DD",
  "country_of_birth": "string",
  "date_of_issue": "YYYY-MM-DD",
  "date_of_expiration": "YYYY-MM-DD",
  "cardholder_signature": "boolean"
}""",
}


def image_to_base64(image):
    """Convert PIL image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def extract_with_gemini(image, document_type):
    """Extract data using Gemini 1.5 Flash"""
    prompt = PROMPTS[document_type]
    try:
        image_content = {"mime_type": "image/png", "data": image_to_base64(image)}
        response = model.generate_content([prompt, image_content])
        response_text = response.text.strip()
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
        extracted_data = json.loads(cleaned_text)
        return extracted_data, True
    except (json.JSONDecodeError, ValueError) as e:
        return {"error": str(e)}, False


def preprocess_image(image):
    """Preprocess image for better analysis"""
    if image.mode != "RGB":
        image = image.convert("RGB")
    max_size = (1024, 1024)
    image.thumbnail(max_size, Image.LANCZOS)
    return image


@app.route("/")
def index():
    return render_template("index.html", doc_types=PROMPTS.keys())


@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    files = request.files.getlist("file")
    if not files or all(file.filename == "" for file in files):
        return jsonify({"error": "No selected files"}), 400

    doc_type = request.form.get("doc_type")
    if not doc_type or doc_type not in PROMPTS:
        return jsonify({"error": "Invalid document type"}), 400

    results = []
    
    for file in files:
        if file.filename:
            try:
                image = Image.open(file.stream)
                image = preprocess_image(image)

                extracted_data, success = extract_with_gemini(image, doc_type)

                if success:
                    if isinstance(extracted_data, dict):
                        extracted_data["document_type"] = doc_type
                        extracted_data["filename"] = file.filename
                        extracted_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        results.append(extracted_data)
                    else:
                        results.append({
                            "filename": file.filename,
                            "error": "Invalid data format"
                        })
                else:
                    results.append({
                        "filename": file.filename,
                        "error": extracted_data.get("error", "Failed to extract data")
                    })
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "error": str(e)
                })

    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=False)
