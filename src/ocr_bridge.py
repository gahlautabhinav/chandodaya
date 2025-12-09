# src/ocr_bridge.py

"""
ocr_bridge.py

Bridge between user_input.py (OCR + Gemini) and the chandas engine API.

Use cases:
----------
1) Direct text (from UI)
    -> call api.analyze_text_to_dict(text)

2) File input (image/pdf/docx)
    -> user_input.process_path(...)
    -> read *_only_shloka.txt produced
    -> run api.analyze_text_to_dict(...) for each extracted mantra
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Any

import user_input  # user_input.py at project root

from .api import analyze_text_to_dict


def _build_args_for_ocr(
    out_dir: str,
    use_gemini: bool = True,
    force_gemini: bool = False,
    gemini_threshold: float = 60.0,
    do_romanize: bool = False,
    do_translate: bool = False,
    no_denoise: bool = False,
):
    """
    Build a SimpleNamespace mimicking argparse.Namespace for user_input.process_path.
    """
    return SimpleNamespace(
        file=None,
        input_dir=None,
        text=None,
        text_file=None,
        out_dir=out_dir,
        no_denoise=no_denoise,
        use_gemini=use_gemini,
        force_gemini=force_gemini,
        gemini_threshold=gemini_threshold,
        do_romanize=do_romanize,
        do_translate=do_translate,
    )


def analyze_file_to_dicts(
    input_path: str,
    out_dir: str,
    use_gemini: bool = True,
    force_gemini: bool = False,
    gemini_threshold: float = 60.0,
    do_romanize: bool = False,
    do_translate: bool = False,
    no_denoise: bool = False,
) -> List[Dict[str, Any]]:
    """
    High-level function:

    1. Runs user_input.process_path(...) on the given file (image/pdf/docx).
    2. Looks in out_dir for *_only_shloka.txt files.
    3. For each extracted mantra/shloka:
         - read text
         - call analyze_text_to_dict(text)
         - collect results in a list.

    Returns
    -------
    List[dict]
        Each element:
        {
          "source_file": "<only_shloka filename>",
          "text": "<extracted mantra>",
          "analysis": { ... output of analyze_text_to_dict ... }
        }
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    args = _build_args_for_ocr(
        out_dir=out_dir,
        use_gemini=use_gemini,
        force_gemini=force_gemini,
        gemini_threshold=gemini_threshold,
        do_romanize=do_romanize,
        do_translate=do_translate,
        no_denoise=no_denoise,
    )

    input_path = Path(input_path)

    # Invoke the existing OCR pipeline
    user_input.process_path(input_path, out, args)

    # Now parse the *_only_shloka.txt files as inputs to the chandas engine.
    results: List[Dict[str, Any]] = []
    shloka_files = sorted(out.glob("*_only_shloka.txt"))

    if not shloka_files:
        # Optional: fall back to *_cleaned_swara.txt if needed
        return results

    for f in shloka_files:
        try:
            text = f.read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue

        if not text:
            print(f"Empty shloka in {f}, skipping.")
            continue

        analysis = analyze_text_to_dict(text)
        results.append(
            {
                "source_file": f.name,
                "text": text,
                "analysis": analysis,
            }
        )

    return results
