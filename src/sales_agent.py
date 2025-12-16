import os
import json
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader


# -------------------------------------------------
# Date parsing
# -------------------------------------------------
def parse_date(date_str: str) -> datetime:
    for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    return None


# -------------------------------------------------
# Parsers
# -------------------------------------------------
def parse_pdf(path: str) -> dict:
    reader = PdfReader(path)
    text = "\n".join(p.extract_text() for p in reader.pages if p.extract_text())

    rfp_id = re.search(r"RFP\s*NO\.?\s*[:\-]?\s*(.+)", text)
    due_date = re.search(r"Last date.*submission.*(\d{2}[/-]\d{2}[/-]\d{4})", text)

    return {
        "rfp_id": rfp_id.group(1).strip() if rfp_id else "UNKNOWN_PDF",
        "due_date": parse_date(due_date.group(1)) if due_date else None,
        "source": "PDF",
        "path": path
    }


def parse_html(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    text = soup.get_text(" ")

    rfp_id = re.search(r"RFP ID:\s*(\S+)", text)
    due_date = re.search(r"Due Date:\s*(\d{2}-\d{2}-\d{4})", text)

    return {
        "rfp_id": rfp_id.group(1) if rfp_id else "UNKNOWN_HTML",
        "due_date": parse_date(due_date.group(1)) if due_date else None,
        "source": "HTML",
        "path": path
    }


def parse_email(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    rfp_id = re.search(r"RFP ID:\s*(\S+)", text)
    due_date = re.search(r"Due Date:\s*(\d{2}-\d{2}-\d{4})", text)

    return {
        "rfp_id": rfp_id.group(1) if rfp_id else "UNKNOWN_EMAIL",
        "due_date": parse_date(due_date.group(1)) if due_date else None,
        "source": "EMAIL",
        "path": path
    }


def parse_json_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "rfp_id": data.get("rfp_id", "UNKNOWN_JSON"),
        "due_date": datetime.strptime(data["due_date"], "%Y-%m-%d"),
        "source": "JSON",
        "path": path
    }


# -------------------------------------------------
# Sales Agent logic
# -------------------------------------------------
def scan_rfps(folder: str) -> list:
    rfps = []

    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        try:
            if file.endswith(".pdf"):
                rfps.append(parse_pdf(path))
            elif file.endswith(".html"):
                rfps.append(parse_html(path))
            elif file.endswith(".txt"):
                rfps.append(parse_email(path))
            elif file.endswith(".json"):
                rfps.append(parse_json_file(path))
        except Exception as e:
            print(f"[Sales Agent] Failed to parse {file}: {e}")

    return rfps


def prioritize_rfps(rfps: list, days: int = 90) -> list:
    today = datetime.today()
    cutoff = today + timedelta(days=days)

    eligible = [
        r for r in rfps
        if r["due_date"] and r["due_date"] <= cutoff
    ]

    return sorted(eligible, key=lambda r: r["due_date"])


# -------------------------------------------------
# SALES AGENT SUMMARY (THIS IS THE KEY ADDITION)
# -------------------------------------------------
def prepare_sales_summary(rfp: dict) -> dict:
    """
    Simulated Sales Agent summary for downstream agents
    """

    technical_summary = {
        "rfp_id": rfp["rfp_id"],
        "product_category": "LT Power Cables",
        "scope_hint": "Power / Control Cables",
        "document_path": rfp["path"]
    }

    pricing_summary = {
        "rfp_id": rfp["rfp_id"],
        "tests_required": [
            "Routine Test",
            "Type Test",
            "Acceptance Test"
        ],
        "quantity_km": 10
    }

    return {
        "technical_summary": technical_summary,
        "pricing_summary": pricing_summary
    }
