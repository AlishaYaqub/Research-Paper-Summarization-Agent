from groq import Groq
import json
from utils import safe_parse_json


def load_prompt(filepath, content):
    with open(filepath, "r", encoding="utf-8") as f:
        template = f.read()
    return template.replace("{summaries}", content).replace("{references}", content)


def call_groq(prompt_text, client):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_text}],
        max_tokens=1500,
        temperature=0.2
    )
    return response.choices[0].message.content


def run_synthesis_agent(extracted_json, api_key):
    print("\n[Agent 2] Starting Synthesis Agent...")

    client = Groq(api_key=api_key)

    summaries = {}
    for section_name, section_data in extracted_json.items():
        if section_name in ["raw_references", "full_text_length"]:
            continue
        if isinstance(section_data, dict):
            summary = section_data.get("section_summary", "")
            if summary:
                summaries[section_name] = summary

    if not summaries:
        print("[Agent 2] WARNING: No section summaries found.")
        summaries["content"] = "No section summaries could be extracted."

    summaries_str = json.dumps(summaries, indent=2)

    print("[Agent 2] Generating synthesized abstract...")
    try:
        synthesis_prompt = load_prompt("prompts/synthesis_prompt.txt", summaries_str)
        summary_text = call_groq(synthesis_prompt, client)
        print(f"[Agent 2] Abstract generated ({len(summary_text)} chars).")
    except Exception as e:
        print(f"[Agent 2] ERROR generating abstract: {e}")
        summary_text = "Summary generation failed: " + str(e)

    raw_references = extracted_json.get("raw_references", "")
    candidate_citations = []

    if raw_references.strip():
        print(f"[Agent 2] Extracting citations ({len(raw_references)} chars)...")
        try:
            citation_prompt = load_prompt(
                "prompts/citation_prompt.txt", raw_references[:4000]
            )
            citation_response = call_groq(citation_prompt, client)
            parsed_citations = safe_parse_json(citation_response)
            if isinstance(parsed_citations, list):
                candidate_citations = parsed_citations
                print(f"[Agent 2] Extracted {len(candidate_citations)} candidate citations.")
            else:
                print("[Agent 2] Citation parse returned non-list.")
                candidate_citations = []
        except Exception as e:
            print(f"[Agent 2] ERROR extracting citations: {e}")
            candidate_citations = []
    else:
        print("[Agent 2] No references section found.")

    print("[Agent 2] Synthesis complete.")
    return summary_text, candidate_citations