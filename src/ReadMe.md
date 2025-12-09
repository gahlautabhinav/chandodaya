PROJECT STRUCTURE
Chandodaya Project directory is organized as follows:

Chandodaya/

server/ : Backend API service

main.py : FastAPI server with endpoints /api/analyze/text and /api/analyze/file

OCR/ : OCR and Gemini cleanup pipeline

user_input.py : Handles text, image, PDF, DOCX input and extracts the clean mantra

vedic_chandas_engine/ : Core Sanskrit Chandas analysis engine

analyze_text.py : Command-line runner for testing full pipeline

api.py : Main function used by backend to get JSON response

normalization.py : Unicode normalization, danda and whitespace cleanup

svara_parser.py : Parses and aligns accents (udatta, anudatta, svarita)

pada_sandhi.py : Pratishakhya-based padapatha segmentation

syllabifier.py : Akshara segmentation and Laghu–Guru computation

feature_extractor.py : Extracts global features of the verse

rule_classifier.py : Rule-based meter classifier

gana_utils.py : Computes gana groups using Pingala rules

model_utils.py : Loads ML models for optional predictions

data_rules.json : Stored list of classical meter rules

datasets/

dataset_enriched.csv : Mantra lookup with padapatha reference

chandas_rulebook.csv : Canonical chandas patterns

models/

baseline.pkl, mlp.pkl : Saved ML models (optional)

requirements.txt

README.md

.env file for API keys

start.py entry script for Render deployment

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