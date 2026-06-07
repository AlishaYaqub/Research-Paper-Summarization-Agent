from groq import Groq
import json
from utils import parse_pdf, segment_by_heading, truncate_text, safe_parse_json

SECTION_PROMPT_MAP = {
    "abstract": "prompts/abstract_prompt.txt",
    "introduction": "prompts/introduction_prompt.txt",
    "methodology": "prompts/methods_prompt.txt",
    "methods": "prompts/methods_prompt.txt",
    "materials and methods": "prompts/methods_prompt.txt",
    "proposed method": "prompts/methods_prompt.txt",
    "system design": "prompts/methods_prompt.txt",
    "approach": "prompts/methods_prompt.txt",
    "experiments": "prompts/results_prompt.txt",
    "results": "prompts/results_prompt.txt",
    "experimental results": "prompts/results_prompt.txt",
    "discussion": "prompts/conclusion_prompt.txt",
    "conclusion": "prompts/conclusion_prompt.txt",
    "conclusions": "prompts/conclusion_prompt.txt",
    "future work": "prompts/conclusion_prompt.txt",
}

REFERENCE_SECTIONS = ["references", "bibliography"]


def load_prompt(filepath, text):
    with open(filepath, "r", encoding="utf-8") as f:
        template = f.read()
    return template.replace("{text}", text)


def call_groq(prompt_text, client):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_text}],
        max_tokens=1024,
        temperature=0.2
    )
    return response.choices[0].message.content


def run_extraction_agent(pdf_path, api_key):
    print("\n[Agent 1] Starting Extraction Agent...")

    client = Groq(api_key=api_key)

    print("[Agent 1] Parsing PDF...")
    full_text, metadata = parse_pdf(pdf_path)

    print("[Agent 1] Segmenting into sections...")
    sections = segment_by_heading(metadata)

    if not sections or len(sections) <= 1:
        print("[Agent 1] Section detection failed, using fallback chunking...")
        words = full_text.split()
        chunk_size = max(1, len(words) // 5)
        sections = {
            "introduction": " ".join(words[:chunk_size]),
            "methodology": " ".join(words[chunk_size:chunk_size*2]),
            "results": " ".join(words[chunk_size*2:chunk_size*3]),
            "discussion": " ".join(words[chunk_size*3:chunk_size*4]),
            "conclusion": " ".join(words[chunk_size*4:])
        }

    detected = list(sections.keys())
    print(f"[Agent 1] Detected sections: {detected}")

    extracted = {}
    raw_references = ""

    for section_name, section_text in sections.items():
        section_lower = section_name.lower().strip()

        if section_lower in REFERENCE_SECTIONS:
            raw_references = section_text
            print(f"[Agent 1] Stored raw references ({len(section_text)} chars)")
            continue

        prompt_file = None
        for key in SECTION_PROMPT_MAP:
            if key in section_lower:
                prompt_file = SECTION_PROMPT_MAP[key]
                break

        if prompt_file is None:
            print(f"[Agent 1] Skipping unmapped section: '{section_name}'")
            continue

        truncated = truncate_text(section_text, max_chars=4000)
        prompt = load_prompt(prompt_file, truncated)

        print(f"[Agent 1] Processing section: '{section_name}' ({len(truncated)} chars)...")

        try:
            response = call_groq(prompt, client)
            parsed = safe_parse_json(response)
            if parsed:
                extracted[section_name] = parsed
                print(f"[Agent 1] Section '{section_name}' extracted successfully.")
            else:
                extracted[section_name] = {
                    "section_summary": section_text[:300],
                    "raw_response": response
                }
                print(f"[Agent 1] JSON parse failed for '{section_name}', stored raw.")
        except Exception as e:
            print(f"[Agent 1] ERROR on section '{section_name}': {e}")
            extracted[section_name] = {
                "section_summary": section_text[:300],
                "error": str(e)
            }

    extracted["raw_references"] = raw_references
    extracted["full_text_length"] = len(full_text)

    print(f"[Agent 1] Extraction complete. {len(extracted)-2} sections processed.")
    return extracted