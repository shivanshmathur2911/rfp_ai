import re

def extract_voltage(text: str):
    match = re.search(r"(\d+(\.\d+)?)\s*kV", text, re.IGNORECASE)
    return float(match.group(1)) if match else None

def extract_conductor(text: str):
    t = text.lower()
    if "aluminium" in t:
        return "Aluminium"
    if "copper" in t:
        return "Copper"
    return None

def extract_insulation(text: str):
    t = text.lower()
    if "xlpe" in t:
        return "XLPE"
    if "pvc" in t:
        return "PVC"
    return None
def extract_cores(text: str):
    match = re.search(r"(\d+)\s*core", text.lower())
    return int(match.group(1)) if match else None

def extract_armouring(text: str):
    t = text.lower()

    # Explicit yes cases
    if "armouring" in t and "yes" in t:
        return "Yes"
    if "armoured" in t:
        return "Yes"

    # Explicit no cases
    if "armouring" in t and "no" in t:
        return "No"

    return None

