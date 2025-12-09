"""
OCR + Gemini pipeline with preserved line breaks and text-input mode.
UPDATED: Render-ready path logic and error handling.

- Preserves Tesseract line structure.
- Cleans text with Swara (Vedic accents).
- EXTRACTS only the Mantra/Shloka into a separate file.
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import unicodedata

# Third-party imports
import cv2
import numpy as np
from PIL import Image
import pytesseract
import easyocr
from pdf2image import convert_from_path
from docx import Document

# 1. Load Environment Variables (Robust for Local vs Render)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Gemini SDK
try:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError
except Exception:
    genai = None
    ResourceExhausted = Exception
    GoogleAPICallError = Exception

# -----------------------
# CONFIG
# -----------------------
CONFIG = {
    # On Render/Linux, we want these to be None so the libraries use the System PATH.
    # Locally on Windows, we default to your hardcoded paths.
    "TESSERACT_EXE": os.getenv("TESSERACT_EXE", r"E:\Program files\Tessract-ocr\tesseract.exe"),
    "POPPLER_PATH": os.getenv("POPPLER_PATH", r"E:\Program files\Release-25.11.0-0\poppler-25.11.0\Library\bin"),
    
    "EASYOCR_LANGS": ['hi', 'en'],
    "TESS_LANGS": "hin+eng",
    
    # UPDATED: 'models/gemini-2.5-flash' does not exist yet. Using standard 1.5 flash.
    "GEMINI_MODEL": "gemini-2.5-flash", 
    "GEMINI_API_ENV": "GEMINI_API_KEY",
}

# -----------------------
# VALIDATION LOGIC (Crucial for Render)
# -----------------------

# 1. Tesseract Logic
# If the path exists (Windows), set it. If not (Linux/Render), do nothing 
# and let pytesseract find it in the global PATH.
if CONFIG.get("TESSERACT_EXE") and os.path.exists(CONFIG["TESSERACT_EXE"]):
    pytesseract.pytesseract.tesseract_cmd = CONFIG["TESSERACT_EXE"]

# 2. Poppler Logic
# If the hardcoded Windows path doesn't exist on this machine (Render), 
# set it to None so pdf2image uses the global PATH instead.
if CONFIG.get("POPPLER_PATH") and not os.path.exists(CONFIG["POPPLER_PATH"]):
    CONFIG["POPPLER_PATH"] = None

# Initialize EasyOCR reader once (CPU is safer for free-tier Render)
print("Initializing EasyOCR...")
READER = easyocr.Reader(CONFIG["EASYOCR_LANGS"], gpu=False)

# -----------------------
# Utility helpers
# -----------------------
def normalize_unicode(text: Optional[str]) -> str:
    s = (text or "")
    s = unicodedata.normalize('NFKC', s)
    s = s.replace('\u200b', '')
    return s

def load_image_cv(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"Failed to load image: {path}")
    return img

def save_img(path: Path, img: np.ndarray):
    cv2.imwrite(str(path), img)

def safe_json(x):
    if x is None or isinstance(x,(str,int,float,bool)):
        return x
    if isinstance(x,(list,tuple)):
        return [safe_json(i) for i in x]
    if isinstance(x,dict):
        return {str(k): safe_json(v) for k,v in x.items()}
    try:
        return str(x)
    except:
        return None

# -----------------------
# Image preprocessing
# -----------------------
def deskew_no_clip(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    try:
        inv = cv2.bitwise_not(gray)
        thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    except Exception:
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if coords.size == 0:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    h,w = img.shape[:2]
    center = (w//2, h//2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(M[0,0]); sin = abs(M[0,1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    M[0,2] += (new_w/2) - center[0]
    M[1,2] += (new_h/2) - center[1]
    rotated = cv2.warpAffine(img, M, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def denoise(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    den = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    return cv2.cvtColor(den, cv2.COLOR_GRAY2BGR)

def enhance_contrast(img: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l,a,b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge((l2,a,b))
    return cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)

def adjust_gamma(img: np.ndarray, gamma: float=1.0) -> np.ndarray:
    invGamma = 1.0 / gamma
    table = np.array([((i/255.0)**invGamma)*255 for i in np.arange(256)]).astype("uint8")
    return cv2.LUT(img, table)

def unsharp_mask(img: np.ndarray, radius=1, amount=0.8) -> np.ndarray:
    blurred = cv2.GaussianBlur(img, (0,0), radius)
    return cv2.addWeighted(img, 1.0 + amount, blurred, -amount, 0)

# -----------------------
# OCR ensemble
# -----------------------
def ocr_tesseract_cv_with_lines(img_cv: np.ndarray, lang: str=None):
    pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    lang = lang or CONFIG["TESS_LANGS"]
    data = pytesseract.image_to_data(pil, lang=lang, output_type=pytesseract.Output.DICT)

    words = []
    lines_map = {}
    order_keys = []
    n = len(data.get('text', []))
    for i in range(n):
        w = data['text'][i]
        if not w or str(w).strip() == "":
            continue
        conf_raw = data.get('conf', [None]*n)[i] if 'conf' in data else None
        try:
            if conf_raw is None or str(conf_raw).strip() == "":
                conf_val = -1
            else:
                conf_val = int(float(conf_raw))
        except:
            conf_val = -1
        words.append({"word": w, "conf": conf_val})

        blk = int(data.get('block_num', [0]*n)[i])
        par = int(data.get('par_num', [0]*n)[i])
        ln = int(data.get('line_num', [0]*n)[i])
        key = (blk, par, ln)
        if key not in lines_map:
            lines_map[key] = []
            order_keys.append(key)
        lines_map[key].append(w)

    lines = []
    for k in order_keys:
        lines.append(" ".join(lines_map.get(k, [])))
    text_with_lines = "\n".join(lines).strip()
    full_text = " ".join([w['word'] for w in words]).strip()
    return full_text, words, text_with_lines

def ocr_easyocr_cv(img_cv: np.ndarray):
    res = READER.readtext(img_cv)
    words=[]; parts=[]
    for bbox, txt, conf in res:
        parts.append(txt); words.append({"word":txt,"conf":float(conf)})
    return " ".join(parts), words

def merge_ensemble(tess_text, tess_words, easy_text, easy_words):
    def avg_conf(lst):
        vals = [w.get("conf",-1) for w in lst if isinstance(w.get("conf",None),(int,float)) and w.get("conf",-1)>=0]
        return float(np.mean(vals)) if vals else -1.0
    tavg=avg_conf(tess_words); eavg=avg_conf(easy_words)
    chosen = easy_text if len(easy_text)>=len(tess_text) else tess_text
    val = [c for c in [tavg,eavg] if c>=0]
    avg = float(np.mean(val)) if val else -1.0
    return {"text": normalize_unicode(chosen), "avg_confidence": avg, "tess_conf": tavg, "easy_conf": eavg}

# -----------------------
# PDF/DOCX helpers
# -----------------------
def pdf_to_images(pdf_path: str, dpi=300):
    # Uses CONFIG['POPPLER_PATH'] which is None on Render (correct) or Path on Windows
    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=CONFIG.get("POPPLER_PATH"))
    return [cv2.cvtColor(np.array(p), cv2.COLOR_RGB2BGR) for p in pages]

def docx_to_images(docx_path: str, out_folder: str):
    doc = Document(docx_path)
    imgs = []
    from PIL import Image as PILImage, ImageDraw, ImageFont
    # Simple fallback font
    font = ImageFont.load_default()
    for i,p in enumerate(doc.paragraphs):
        txt = p.text.strip()
        if not txt: continue
        lines = txt.split("\n")
        w,h = 1200, 60 + 12*len(lines)
        im = PILImage.new("RGB",(w,h),color="white")
        draw = ImageDraw.Draw(im)
        y=10
        for line in lines:
            draw.text((10,y), line, fill="black", font=font); y+=12
        path = os.path.join(out_folder, f"docx_{i}.png")
        im.save(path); imgs.append(path)
    return imgs

# -----------------------
# Gemini helpers
# -----------------------
def _init_gemini():
    if genai is None:
        raise RuntimeError("google.generativeai not installed")
    
    api_env_var = CONFIG.get("GEMINI_API_ENV", "GEMINI_API_KEY")
    
    # 1. Try to get key
    api_key = os.environ.get(api_env_var)
    
    # 2. Debugging: Check if key was found
    if not api_key:
        print(f"DEBUG: Could not find env var '{api_env_var}'")
        print(f"DEBUG: Current Env Vars: {list(os.environ.keys())}")
        raise RuntimeError(f"Set Gemini API key in env var {api_env_var}")
    
    # 3. CRITICAL FIX: Strip whitespace/newlines!
    # A common .env error is having a space at the end (e.g., "KEY=AIza... ")
    api_key = api_key.strip()

    # 4. Debugging: Print first/last 4 chars to verify it's the RIGHT key
    # (Do not print the full key for security)
    print(f"DEBUG: Loaded API Key: {api_key[:4]}...{api_key[-4:]} (Length: {len(api_key)})")
    
    genai.configure(api_key=api_key)

def _generate_with_backoff(prompt: str, model_name: str=None, max_retries:int=4, initial_backoff:float=1.0):
    model_name = model_name or CONFIG.get("GEMINI_MODEL")
    if not model_name:
        raise RuntimeError("No Gemini model configured")
    
    model = genai.GenerativeModel(model_name)
    attempt = 0; backoff = initial_backoff
    
    while attempt <= max_retries:
        try:
            resp = model.generate_content(prompt)
            return getattr(resp, "text", str(resp))
        except ResourceExhausted as e:
            print(f"Gemini quota exhausted, retrying in {backoff}s...")
            attempt += 1
            if attempt > max_retries: raise
            time.sleep(backoff); backoff = min(backoff*2, 30.0)
        except GoogleAPICallError as e:
            print(f"Gemini API error: {e}, retrying...")
            attempt += 1
            if attempt > max_retries: raise
            time.sleep(backoff); backoff = min(backoff*2, 30.0)
        except Exception as e:
             # Catch block specific errors that might occur on generate_content
             print(f"Gemini unexpected error: {e}")
             raise e

def gemini_clean_no_swara(ocr_text: str) -> str:
    prompt = f"""Task: Clean OCR errors in this Devanagari text. Output in normal orthography (NO Vedic Swara marks). PRESERVE LINE BREAKS. Output only the text.\n\nText:\n\"\"\"{ocr_text}\"\"\""""
    return _generate_with_backoff(prompt)

def gemini_clean_with_swara_vedic(ocr_text: str) -> str:
    prompt = f"""
    You are an expert Devanagari/Vedic linguist.
    Task: Clean the OCR text and ADD Vedic prosodic marks (UDATTA ◌॑ and ANUDATTA ◌॒) where appropriate.
    - PRESERVE ALL ORIGINAL LINE BREAKS.
    - Output ONLY the cleaned Devanagari text with svāra marks.
    
    Text:
    \"\"\"{ocr_text}\"\"\""""
    return _generate_with_backoff(prompt)

def gemini_romanize(devnagari_text: str) -> str:
    prompt = f"""Transliterate to IAST with diacritics. Preserve svāra marks. Preserve line breaks.\n\nText:\n\"\"\"{devnagari_text}\"\"\""""
    return _generate_with_backoff(prompt)

def gemini_translate(devnagari_text: str) -> str:
    prompt = f"Translate to English. Preserve line breaks. Output only translation.\n\n{devnagari_text}"
    return _generate_with_backoff(prompt)

def gemini_extract_only_mantra(full_text_with_swara: str) -> str:
    prompt = f"""
    You are an expert Vedic Editor.
    
    Input Text:
    \"\"\"{full_text_with_swara}\"\"\"
    
    TASK:
    1. Identify the actual Sanskrit Shloka or Mantra lines within the input text.
    2. REMOVE all Hindi/English commentary, word meanings (Padarth), Anvay, Bhashya, headers, and extraneous text.
    3. KEEP the Swara (Vedic accents) exactly as they are in the input.
    4. PRESERVE the original line structure of the Mantra.
    5. Output ONLY the extracted Mantra/Shloka text. Nothing else.
    """
    return _generate_with_backoff(prompt)

# -----------------------
# Reflow helper
# -----------------------
def reflow_to_lines(original_lines: List[str], cleaned_text: str) -> str:
    if "\n" in cleaned_text: return cleaned_text
    cleaned_text = cleaned_text.strip()
    if not original_lines: return cleaned_text
    words = cleaned_text.split()
    total_words = len(words)
    orig_word_counts = [len(l.split()) for l in original_lines]
    total_orig_words = sum(orig_word_counts) if sum(orig_word_counts) > 0 else len(original_lines)
    if total_orig_words == 0:
        per = max(1, total_words // max(1, len(original_lines)))
        lines = [" ".join(words[i:i+per]) for i in range(0, total_words, per)]
        return "\n".join(lines)
    allocated = []
    acc = 0
    for c in orig_word_counts:
        chunk = max(1, int(round((c / total_orig_words) * total_words)))
        allocated.append(chunk); acc += chunk
    if acc != total_words: allocated[-1] += (total_words - acc)
    lines = []; idx = 0
    for a in allocated:
        lines.append(" ".join(words[idx: idx + a])); idx += a
    return "\n".join(lines)

# -----------------------
# Image page processing
# -----------------------
def process_image(img_cv: np.ndarray, args) -> Tuple[np.ndarray, np.ndarray, Dict]:
    original = img_cv.copy()
    img = deskew_no_clip(original)
    if not args.no_denoise: img = denoise(img)
    img = enhance_contrast(img)
    img = adjust_gamma(img, gamma=0.9)
    img = unsharp_mask(cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR), radius=1, amount=0.8)

    tess_fulltext, tess_words, tess_lines_text = ocr_tesseract_cv_with_lines(img)
    easy_text, easy_words = ocr_easyocr_cv(img)
    merged = merge_ensemble(tess_fulltext, tess_words, easy_text, easy_words)
    ocr_text_for_gemini = tess_lines_text if tess_lines_text.strip() else merged["text"]

    result = {
        "ocr_text": merged["text"],
        "ocr_text_lines": ocr_text_for_gemini,
        "avg_confidence": merged["avg_confidence"]
    }

    cleaned_no_swara = None
    cleaned_swara = None
    only_shloka = None
    roman = None
    translated = None

    if args.use_gemini:
        try:
            _init_gemini()
            if args.force_gemini or merged["avg_confidence"] < args.gemini_threshold:
                # 1. Clean No Swara
                try:
                    raw_no = gemini_clean_no_swara(ocr_text_for_gemini)
                    raw_no = normalize_unicode(raw_no)
                    if "\n" not in raw_no:
                        orig_lines = [l for l in ocr_text_for_gemini.split("\n") if l.strip()]
                        raw_no = reflow_to_lines(orig_lines, raw_no)
                    cleaned_no_swara = raw_no
                except Exception as e:
                    result.setdefault("notes", []).append(f"clean_no_swara_failed:{str(e)}")

                # 2. Clean With Swara (Full Text)
                try:
                    raw_sw = gemini_clean_with_swara_vedic(ocr_text_for_gemini)
                    raw_sw = normalize_unicode(raw_sw)
                    if "\n" not in raw_sw:
                        orig_lines = [l for l in ocr_text_for_gemini.split("\n") if l.strip()]
                        raw_sw = reflow_to_lines(orig_lines, raw_sw)
                    cleaned_swara = raw_sw
                except Exception as e:
                    result.setdefault("notes", []).append(f"clean_with_swara_failed:{str(e)}")

                # 3. Extract ONLY Mantra
                base_for_extraction = cleaned_swara if cleaned_swara else (cleaned_no_swara or ocr_text_for_gemini)
                if base_for_extraction:
                    try:
                        only_shloka = gemini_extract_only_mantra(base_for_extraction)
                        only_shloka = normalize_unicode(only_shloka)
                    except Exception as e:
                          result.setdefault("notes", []).append(f"extract_shloka_failed:{str(e)}")

                # 4. Romanize/Translate
                base_for_roman = only_shloka if only_shloka else (cleaned_swara or cleaned_no_swara or ocr_text_for_gemini)
                if args.do_romanize and base_for_roman:
                    try:
                        roman = gemini_romanize(base_for_roman)
                    except Exception as e:
                        result.setdefault("notes", []).append(f"romanize_failed:{str(e)}")
                if args.do_translate and base_for_roman:
                    try:
                        translated = gemini_translate(base_for_roman)
                    except Exception as e:
                        result.setdefault("notes", []).append(f"translate_failed:{str(e)}")
        except Exception as e:
            result.setdefault("notes", []).append(f"gemini_init_failed:{str(e)}")

    result.update({
        "cleaned_no_swara": cleaned_no_swara,
        "cleaned_swara": cleaned_swara,
        "only_shloka": only_shloka,
        "roman_swara": roman,
        "translated": translated
    })
    return original, img, result

# -----------------------
# Process plain text (no OCR)
# -----------------------
def process_plain_text(text: str, stem: str, out_dir: Path, args) -> Dict:
    res = { "ocr_text": None, "ocr_text_lines": text, "avg_confidence": None }
    cleaned_no_swara = None
    cleaned_swara = None
    only_shloka = None
    roman = None
    translated = None

    if args.use_gemini:
        try:
            _init_gemini()
            # Clean No Swara
            try:
                raw_no = gemini_clean_no_swara(text)
                raw_no = normalize_unicode(raw_no)
                if "\n" not in raw_no:
                    orig_lines = [l for l in text.split("\n") if l.strip()]
                    raw_no = reflow_to_lines(orig_lines, raw_no)
                cleaned_no_swara = raw_no
            except Exception as e:
                res.setdefault("notes", []).append(f"clean_no_swara_failed:{str(e)}")

            # Clean With Swara
            try:
                raw_sw = gemini_clean_with_swara_vedic(text)
                raw_sw = normalize_unicode(raw_sw)
                if "\n" not in raw_sw:
                    orig_lines = [l for l in text.split("\n") if l.strip()]
                    raw_sw = reflow_to_lines(orig_lines, raw_sw)
                cleaned_swara = raw_sw
            except Exception as e:
                res.setdefault("notes", []).append(f"clean_with_swara_failed:{str(e)}")

            # Extract ONLY Mantra
            base_for_extraction = cleaned_swara if cleaned_swara else (cleaned_no_swara or text)
            if base_for_extraction:
                try:
                    only_shloka = gemini_extract_only_mantra(base_for_extraction)
                    only_shloka = normalize_unicode(only_shloka)
                except Exception as e:
                      res.setdefault("notes", []).append(f"extract_shloka_failed:{str(e)}")

            # Roman/Translate
            base_for_roman = only_shloka if only_shloka else (cleaned_swara or cleaned_no_swara or text)
            if args.do_romanize and base_for_roman:
                try: roman = gemini_romanize(base_for_roman)
                except Exception as e: res.setdefault("notes", []).append(f"romanize_failed:{str(e)}")
            if args.do_translate and base_for_roman:
                try: translated = gemini_translate(base_for_roman)
                except Exception as e: res.setdefault("notes", []).append(f"translate_failed:{str(e)}")
        except Exception as e:
            res.setdefault("notes", []).append(f"gemini_init_failed:{str(e)}")

    res.update({
        "cleaned_no_swara": cleaned_no_swara,
        "cleaned_swara": cleaned_swara,
        "only_shloka": only_shloka,
        "roman_swara": roman,
        "translated": translated
    })

    # Write files
    if cleaned_no_swara:
        with open(out_dir / f"{stem}_cleaned_no_swara.txt", "w", encoding="utf-8") as fh: fh.write(cleaned_no_swara)
    if cleaned_swara:
        with open(out_dir / f"{stem}_cleaned_swara.txt", "w", encoding="utf-8") as fh: fh.write(cleaned_swara)
    if only_shloka:
        with open(out_dir / f"{stem}_only_shloka.txt", "w", encoding="utf-8") as fh: fh.write(only_shloka)
    if roman:
        with open(out_dir / f"{stem}_roman_swara.txt", "w", encoding="utf-8") as fh: fh.write(roman)
    if translated:
        with open(out_dir / f"{stem}_eng.txt", "w", encoding="utf-8") as fh: fh.write(translated)

    summary = {"file": stem, "result": res}
    with open(out_dir / f"{stem}_summary.json", "w", encoding="utf-8") as fh:
        json.dump(safe_json(summary), fh, ensure_ascii=False, indent=2)
    return summary

# -----------------------
# Orchestration
# -----------------------
def process_path(path: Path, out_dir: Path, args):
    out_dir.mkdir(parents=True, exist_ok=True)
    items = []
    files = sorted(path.iterdir()) if path.is_dir() else [path]
    for f in files:
        if f.is_dir(): continue
        ext = f.suffix.lower()
        print("Processing:", f)
        imgs = []
        if ext == ".pdf":
            try: imgs = pdf_to_images(str(f))
            except Exception as e: print(f"PDF fail: {e}"); continue
        elif ext == ".docx":
            tmp = out_dir / "docx_imgs"; tmp.mkdir(exist_ok=True)
            img_paths = docx_to_images(str(f), str(tmp)); imgs = [load_image_cv(p) for p in img_paths]
        elif ext in [".jpg",".jpeg",".png",".tiff",".bmp",".webp",".gif"]:
            imgs = [load_image_cv(str(f))]
        else:
            print("Skip:", ext); continue

        pages_summary = []
        for i, img in enumerate(imgs, start=1):
            stem = f"{f.stem}_page{i}"
            try:
                orig, proc_img, res = process_image(img, args)
                orig_path = out_dir / f"{stem}_orig.png"
                proc_path = out_dir / f"{stem}_processed.png"
                save_img(orig_path, orig); save_img(proc_path, proc_img)

                if res.get("cleaned_no_swara"):
                    with open(out_dir / f"{stem}_cleaned_no_swara.txt", "w", encoding="utf-8") as fh: fh.write(res["cleaned_no_swara"])
                if res.get("cleaned_swara"):
                    with open(out_dir / f"{stem}_cleaned_swara.txt", "w", encoding="utf-8") as fh: fh.write(res["cleaned_swara"])
                if res.get("only_shloka"):
                    with open(out_dir / f"{stem}_only_shloka.txt", "w", encoding="utf-8") as fh: fh.write(res["only_shloka"])
                if res.get("roman_swara"):
                    with open(out_dir / f"{stem}_roman_swara.txt", "w", encoding="utf-8") as fh: fh.write(res["roman_swara"])
                if res.get("translated"):
                    with open(out_dir / f"{stem}_eng.txt", "w", encoding="utf-8") as fh: fh.write(res["translated"])

                pages_summary.append({
                    "page": i,
                    "cleaned_swara": res.get("cleaned_swara"),
                    "only_shloka": res.get("only_shloka"),
                    "notes": res.get("notes", [])
                })
            except Exception as e:
                print(f"Page error on {stem}: {e}")
                pages_summary.append({"page": i, "error": str(e)})

        summary_obj = {"file": str(f), "pages": pages_summary}
        summary_path = out_dir / f"{f.stem}_summary.json"
        with open(summary_path, "w", encoding="utf-8") as fh:
            json.dump(safe_json(summary_obj), fh, ensure_ascii=False, indent=2)
        items.append({"file": str(f), "summary": str(summary_path)})
    return items

# -----------------------
# CLI
# -----------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None)
    ap.add_argument("--input_dir", default=None)
    ap.add_argument("--text", default=None, help="Raw text input")
    ap.add_argument("--text_file", default=None, help="Text file input")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--no_denoise", action="store_true")
    ap.add_argument("--use_gemini", action="store_true")
    ap.add_argument("--force_gemini", action="store_true")
    ap.add_argument("--gemini_threshold", type=float, default=60.0)
    ap.add_argument("--do_romanize", action="store_true")
    ap.add_argument("--do_translate", action="store_true")
    args = ap.parse_args()

    if not args.file and not args.input_dir and not args.text and not args.text_file:
        print("Provide input source (--file, --input_dir, --text, or --text_file).")
        sys.exit(1)

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    if args.text or args.text_file:
        if args.text_file:
            try:
                with open(args.text_file, "r", encoding="utf-8") as fh: text = fh.read()
                stem = Path(args.text_file).stem
            except Exception as e:
                print(f"Error reading text file: {e}"); sys.exit(1)
        else:
            text = args.text
            stem = "text_input"
        print("Processing plain text...")
        process_plain_text(text, stem, out, args)
        return

    inp = Path(args.file) if args.file else Path(args.input_dir)
    process_path(inp, out, args)
    print("Done.")

if __name__ == "__main__":
    main()