# src/padapatha.py

"""
padapatha.py

Utilities for working with padapāṭha / Prātiśākhya-style segmentation.

We assume that the Padpath column from your Rig/Yajur/Sama CSVs encodes
a padapāṭha-style segmentation, typically using Devanagari danda signs
(।, ॥) to mark segment boundaries.

We provide:
- PadaUnit dataclass
- split_pratishakhya_padas: split a padapāṭha string into small padas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class PadaUnit:
    index: int            # zero-based index
    text: str             # raw Devanagari text for this small pada
    sandhi_profile: Dict[str, Any]


def split_pratishakhya_padas(padapatha_text: str) -> List[PadaUnit]:
    """
    Split a padapāṭha-like string into Prātiśākhya-style padas.

    Example
    -------
    Input:
        "अ॒ग्निम्। ई॒ळे॒। पु॒रःऽहि॑तम्। य॒ज्ञस्य॑। दे॒वम्। ऋ॒त्विज॑म्।
         होता॑रम्। र॒त्न॒ऽधात॑मम् ॥"

    Output:
        [
          PadaUnit(index=0, text="अ॒ग्निम्", ...),
          PadaUnit(index=1, text="ई॒ळे॒", ...),
          PadaUnit(index=2, text="पु॒रःऽहि॑तम्", ...),
          ...
        ]

    For now, sandhi_profile is left empty.
    """
    if not padapatha_text:
        return []

    # Normalize whitespace
    text = " ".join(str(padapatha_text).split())

    # Split on danda signs '।' and '॥'
    raw_parts = re.split(r"[।॥]", text)
    padas: List[PadaUnit] = []

    idx = 0
    for part in raw_parts:
        part = part.strip()
        if not part:
            continue
        padas.append(
            PadaUnit(
                index=idx,
                text=part,
                sandhi_profile={},
            )
        )
        idx += 1

    return padas
