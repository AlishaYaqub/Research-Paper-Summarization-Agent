from groq import Groq
import fitz
import sys
import re

def compute_rouge_l(hyp, ref):
    h = hyp.lower().split()
    r = ref.lower().split()
    if not h or not r: return 0.0
    m, n = len(r), len(h)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1,m+1):
        for j in range(1,n+1):
            dp[i][j] = dp[i-1][j-1]+1 if r[i-1]==h[j-1] else max(dp[i-1][j],dp[i][j-1])
    lcs = dp[m][n]
    p = lcs/n if n else 0
    rc = lcs/m if m else 0
    return round(2*p*rc/(p+rc),4) if p+rc else 0.0

def run_baseline(pdf_path, api_key):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()

    full_text = full_text[:12000]

    client = Groq(api_key=api_key)

    prompt = f"""You are an academic summarizer. Read the following research paper text and:
1. Write a summary of 200-250 words covering the problem, method, results, and conclusion.
2. List all references you can find in the text as a numbered list.

PAPER TEXT:
{full_text}

Output format:
SUMMARY:
[your summary here]

REFERENCES:
[numbered list of references]
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.2
    )

    output = response.choices[0].message.content

    summary = ""
    refs = ""
    if "SUMMARY:" in output and "REFERENCES:" in output:
        parts = output.split("REFERENCES:")
        summary = parts[0].replace("SUMMARY:", "").strip()
        refs = parts[1].strip() if len(parts) > 1 else ""
    else:
        summary = output[:800]

    ref_lines = [l.strip() for l in refs.split("\n") if len(l.strip()) > 10]
    num_refs = len(ref_lines)

    print("\n" + "="*60)
    print("BASELINE (Single Prompt) RESULTS")
    print("="*60)
    print(f"\nSUMMARY:\n{summary}")
    print(f"\nTotal references listed: {num_refs}")
    print(f"ROUGE-L (vs first 500 chars of text): {compute_rouge_l(summary, full_text[:500])}")
    print("\nNOTE: Baseline does NOT verify citations against source.")
    print("All listed references are unverified — hallucination rate unknown.")

if __name__ == "__main__":
    import os
    key = os.environ.get("GROQ_API_KEY","")
    if not key:
        key = input("Enter Groq API key: ").strip()
    pdf = sys.argv[1] if len(sys.argv) > 1 else input("Enter PDF path: ").strip()
    run_baseline(pdf, key)