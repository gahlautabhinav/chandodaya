<<<<<<< HEAD
# chands_identier

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
=======
# Vedic + Classical Sanskrit Chandas Identification System

## Quickstart

```bash
pip install -r requirements.txt
# or: pip install -e .

PROJECT STRUCTURE
Chandodaya Project directory is organized as follows:

Chandodaya/
│
├── server/                                    # Backend REST API
│   └── main.py                                # FastAPI entrypoint (POST /api/analyze/*)
│
├── OCR/                                       # OCR + Cleaning + Gemini pipeline
│   └── user_input.py                          # Extract clean shloka text from Image/PDF/Text
│
├── vedic_chandas_engine/                      # Core Prosody Engine
│   ├── analyze_text.py                        # CLI + printing engine demo
│   ├── api.py                                 # Programmatic API returning JSON
│   ├── normalization.py                        # Unicode + swara normalization rules
│   ├── svara_parser.py                         # Accent alignment with aksharas
│   ├── pada_sandhi.py                         # Pratishakhya-based pada segmentation
│   ├── syllabifier.py                         # Akshara segmentation + L/G calculation
│   ├── feature_extractor.py                   # Global features, gana sequences
│   ├── rule_classifier.py                     # Rule-based chanda identification
│   ├── gana_utils.py                           # Pingala gana computation helpers
│   ├── model_utils.py                         # ML model loading and prediction (optional)
│   ├── data_rules.json                        # Rule datasets of chandas patterns
│   └── __init__.py
│
├── datasets/
│   ├── dataset_enriched.csv                   # Vedic mantra reference with padapatha support
│   ├── chandas_rulebook.csv                   # Canonical meters and deviations
│   └── examples/
│
├── models/                                    # Saved ML models (optional)
│   ├── baseline.pkl
│   └── mlp.pkl
│
├── requirements.txt                           # Python dependency list
│
├── README.md                                  # Project overview and documentation
│
├── .env                                       # Keys (Gemini, Tesseract, Poppler)
│
└── start.py                                   # Render start command wrapper

PROJECT PIPELINE
From input to analysis, the system follows this sequence:

User provides Text / Image / PDF / Romanized Sanskrit.

If Image or PDF: OCR is performed using EasyOCR + Tesseract.

Gemini pipeline cleans and restores accents and extracts only the mantra lines.

Normalization removes unnecessary characters and standardizes text.

Padapatha segmentation using Vedic Pratishakhya rules.

Akshara segmentation splits each syllable.

Laghu–Guru classification using classical prosodic rules.

Gana sequence generation using Pingala formula.

Meter identification using rule-based engine and optional ML.

Final JSON output is returned to frontend with explanation.

LIBRARIES USED
FastAPI – Backend API server
Uvicorn – Runs the web service
OpenCV – Image processing (enhancement, deskewing)
EasyOCR – OCR engine for Hindi/Sanskrit scripts
Tesseract OCR – Secondary OCR engine
pdf2image – Convert PDF to images
Pillow (PIL) – Image manipulation
Numpy – Numerical operations
Google Generative AI SDK – Gemini text cleanup and reconstruction
python-docx – DOCX input support
pandas – Dataset management
scikit-learn – ML models for meter classification (optional)
python-dotenv – Manage environment variables (.env)

TECHNICAL REQUIREMENTS

Python 3.10

Minimum 1 GB RAM recommended (OCR heavy)

Linux / Windows / Mac support

Can run local or cloud deploy

REQUIREMENTS.TXT CONTENT
fastapi
uvicorn
opencv-python-headless
numpy
pillow
pytesseract
easyocr
pdf2image
python-docx
google-generativeai
python-dotenv
pandas
scikit-learn

BACKEND START COMMAND (Render or Local)
uvicorn server.main:app --host 0.0.0.0 --port 8000

BACKEND API ENDPOINTS
POST /api/analyze/text
Input: JSON containing a Devanagari mantra string
Output: Full chandas analysis in JSON format

POST /api/analyze/file
Input: image or PDF upload
Output: OCR + Chandas analysis JSON
>>>>>>> 7cb7c89473299fb8042bc2bfc58c62541e4c9508
