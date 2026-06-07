import re
import fitz  # PyMuPDF
import json


def parse_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    metadata = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        size = span.get("size", 12)
                        flags = span.get("flags", 0)
                        is_bold = bool(flags & 2**4)
                        if text:
                            metadata.append({
                                "text": text,
                                "size": size,
                                "bold": is_bold,
                                "page": page_num
                            })
                            full_text += text + " "
    doc.close()
    return full_text.strip(), metadata


SECTION_KEYWORDS = [
    "abstract", "introduction", "related work", "literature review",
    "background", "methodology", "methods", "materials and methods",
    "proposed method", "system design", "approach",
    "experiments", "results", "experimental results",
    "discussion", "conclusion", "conclusions", "future work",
    "references", "bibliography", "acknowledgements", "acknowledgments"
]


def segment_by_heading(metadata):
    sections = {}
    current_section = "preamble"
    current_text = []
    avg_body_size = 12.0

    sizes = [m["size"] for m in metadata if len(m["text"]) > 3]
    if sizes:
        avg_body_size = sorted(sizes)[len(sizes) // 2]

    for item in metadata:
        text = item["text"]
        size = item["size"]
        is_bold = item["bold"]
        text_lower = text.lower().strip()

        is_heading = False
        matched_section = None

        for kw in SECTION_KEYWORDS:
            if text_lower.startswith(kw) and len(text_lower) < 80:
                is_heading = True
                matched_section = kw
                break

        if not is_heading and (size > avg_body_size + 1 or is_bold):
            for kw in SECTION_KEYWORDS:
                if kw in text_lower and len(text_lower) < 80:
                    is_heading = True
                    matched_section = kw
                    break

        if is_heading and matched_section:
            if current_text:
                sections[current_section] = " ".join(current_text).strip()
            current_section = matched_section
            current_text = []
        else:
            current_text.append(text)

    if current_text:
        sections[current_section] = " ".join(current_text).strip()

    return sections


def truncate_text(text, max_chars=8000):
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [truncated for length]"


def safe_parse_json(text):
    text = text.strip()
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        try:
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
    return None