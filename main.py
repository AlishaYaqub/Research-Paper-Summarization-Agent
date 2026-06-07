import os
import sys
import json
import argparse
from datetime import datetime

from agent1_extraction import run_extraction_agent
from agent2_synthesis import run_synthesis_agent
from agent3_verification import run_verification_agent


def compute_rouge_l(hypothesis, reference):
    if not hypothesis or not reference:
        return 0.0
    hyp_tokens = hypothesis.lower().split()
    ref_tokens = reference.lower().split()
    m, n = len(ref_tokens), len(hyp_tokens)
    if m == 0 or n == 0:
        return 0.0
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_tokens[i-1] == hyp_tokens[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    lcs = dp[m][n]
    precision = lcs / n if n > 0 else 0
    recall = lcs / m if m > 0 else 0
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def print_banner():
    print("=" * 65)
    print("  Research Paper Summarization Agent")
    print("  Three-Agent Architecture with Bias Mitigation")
    print("  UET Taxila — AI Course Project")
    print("=" * 65)


def save_output(final_output, extracted, pdf_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_filename = f"output_{base_name}_{timestamp}.json"

    full_result = {
        "input_pdf": pdf_path,
        "timestamp": timestamp,
        "pipeline_output": final_output,
        "sections_extracted": list(k for k in extracted.keys()
                                   if k not in ["raw_references", "full_text_length"])
    }

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_result, f, indent=2, ensure_ascii=False)

    print(f"\n[Main] Full output saved to: {output_filename}")
    return output_filename


def print_results(final_output, extracted):
    print("\n" + "=" * 65)
    print("PIPELINE RESULTS SUMMARY")
    print("=" * 65)

    print("\n--- VERIFIED SUMMARY ---")
    summary = final_output.get("verified_summary", "No summary generated.")
    print(summary)

    print("\n--- SECTIONS EXTRACTED ---")
    sections = [k for k in extracted.keys()
                if k not in ["raw_references", "full_text_length"]]
    for s in sections:
        print(f"  - {s}")

    print("\n--- CITATION VERIFICATION REPORT ---")
    print(f"  Total citations generated : {final_output['total_citations_generated']}")
    print(f"  Verified citations        : {final_output['total_verified']}")
    print(f"  Uncertain citations       : {len(final_output.get('uncertain_citations', []))}")
    print(f"  Hallucinated citations    : {final_output['total_hallucinated']}")
    print(f"  Hallucination rate        : {final_output['hallucination_rate_percent']}%")

    print("\n--- VERIFIED CITATIONS (first 5) ---")
    for i, c in enumerate(final_output.get("verified_citations", [])[:5]):
        author = c.get("author_list", "Unknown")[:50]
        year = c.get("year", "?")
        title = (c.get("title", "No title") or "No title")[:60]
        status = c.get("verification_status", "?")
        print(f"  [{i+1}] {author} ({year})")
        print(f"       Title : {title}")
        print(f"       Status: {status}")

    if final_output.get("hallucinated_citations"):
        print("\n--- HALLUCINATED CITATIONS (flagged and removed) ---")
        for i, c in enumerate(final_output["hallucinated_citations"][:3]):
            author = c.get("author_list", "Unknown")[:50]
            title = (c.get("title", "No title") or "No title")[:60]
            print(f"  [H{i+1}] {author} — {title}")

    rouge_l = compute_rouge_l(
        final_output.get("verified_summary", ""),
        " ".join([
            v.get("section_summary", "") for v in extracted.values()
            if isinstance(v, dict) and "section_summary" in v
        ])
    )
    print(f"\n--- ROUGE-L (summary vs extracted content) ---")
    print(f"  ROUGE-L score: {rouge_l}")

    print("\n" + "=" * 65)


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="Research Paper Summarization Agent — Three-Agent Pipeline"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the research paper PDF file"
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Anthropic API key (or set ANTHROPIC_API_KEY env variable)"
    )
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("\nERROR: No API key provided.")
        print("Set it via:  set GROQ_API_KEY=your_key_here")
        print("Or pass it:  python main.py paper.pdf --api-key your_key_here")
        sys.exit(1)

    pdf_path = args.pdf_path
    if not os.path.exists(pdf_path):
        print(f"\nERROR: File not found: {pdf_path}")
        sys.exit(1)

    print(f"\n[Main] Input PDF  : {pdf_path}")
    print(f"[Main] API Model  : claude-haiku-4-5-20251001 (free tier)")
    print(f"[Main] Pipeline   : Extraction -> Synthesis -> Verification")

    extracted = run_extraction_agent(pdf_path, api_key)

    summary_text, candidate_citations = run_synthesis_agent(extracted, api_key)

    raw_references = extracted.get("raw_references", "")
    final_output = run_verification_agent(summary_text, candidate_citations, raw_references)

    print_results(final_output, extracted)

    save_output(final_output, extracted, pdf_path)

    print("\n[Main] Pipeline completed successfully.")


if __name__ == "__main__":
    main()