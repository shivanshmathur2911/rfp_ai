import re

def extract_voltage(text: str):
    if not text:
        return None
    match = re.search(r"(\d+(\.\d+)?)\s*kV", text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def extract_conductor(text: str):
    if not text:
        return None
    t = text.lower()
    if "aluminium" in t:
        return "Aluminium"
    if "copper" in t:
        return "Copper"
    return None


def extract_insulation(text: str):
    if not text:
        return None
    t = text.lower()
    if "xlpe" in t:
        return "XLPE"
    if "pvc" in t:
        return "PVC"
    return None


def extract_cores(text: str):
    """
    Extract number of cores from unstructured text.
    Handles:
    - '3 core', '3-core'
    - 'Number of cores: 3'
    - 'three core', 'three-core'
    - 'three-core construction'
    """
    if not text:
        return None

    t = " ".join(text.lower().split())

    # 1) Numeric patterns: 3 core, 3-core, 3 cores
    m = re.search(r"\b(\d{1,2})\s*[- ]?\s*core(s)?\b", t)
    if m:
        return int(m.group(1))

    # 2) Explicit label: number of cores: 3
    m = re.search(r"\bnumber\s+of\s+cores?\b\s*[:\-]?\s*(\d{1,2})\b", t)
    if m:
        return int(m.group(1))

    # 3) Word-based cores (your case)
    word_to_num = {
        "single": 1,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
    }

    # three-core / three core
    m = re.search(
        r"\b(single|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*[- ]\s*core(s)?\b",
        t
    )
    if m:
        return word_to_num.get(m.group(1))

    # three-core construction
    m = re.search(
        r"\b(single|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*[- ]\s*core\s+construction\b",
        t
    )
    if m:
        return word_to_num.get(m.group(1))

    return None


def extract_armouring(text: str):
    if not text:
        return None

    t = text.lower()

    # Explicit yes cases
    if "armoured" in t:
        return "Yes"
    if "armouring" in t and "yes" in t:
        return "Yes"

    # Explicit no cases
    if "armouring" in t and "no" in t:
        return "No"

    return None
