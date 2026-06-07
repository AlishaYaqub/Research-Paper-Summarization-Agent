# Research Paper Summarization Agent
## Three-Agent Architecture for Bias Mitigation
Course: Artificial Intelligence | Instructor: Dr. Kanwal Yousaf  
Group Members: Alisha Yaqub (23-SE-65) | Izza Maqbool (23-SE-89)

---

## What This System Does

This system accepts a research paper in PDF format and produces a verified summary, a citation list cross-checked against the source document, a hallucination report, and a ROUGE-L score measuring summary quality.

It addresses two documented failure modes in large language model summarization:

1. **Positional Bias** — models over-summarize the introduction and conclusion while ignoring the methods and results sections which contain the actual contributions.

2. **Citation Hallucination** — models generate fake references that look real but do not exist in any database.

---

## System Architecture

Three agents run sequentially. The output of each becomes the input of the next.

```
PDF Input
    |
    v
Agent 1: Extraction Agent
    - Parses PDF using PyMuPDF
    - Detects section headings using font-weight and keyword matching
    - Sends each section independently to Groq API (equal token budget)
    - Outputs structured JSON summary per section
    |
    v
Agent 2: Synthesis Agent
    - Receives section-level JSON from Agent 1
    - Generates a coherent 200-250 word abstract
    - Extracts candidate citations from the raw references text
    |
    v
Agent 3: Verification Agent
    - Checks every citation against the source document
    - Pass 1: Exact string matching (author surname + year)
    - Pass 2: Semantic similarity using all-MiniLM-L6-v2 (threshold 0.85)
    - Removes hallucinated citations before final output
    |
    v
Verified Output (JSON file + terminal summary)
```

---

## Project File Structure

```
## Project File Structure

```
research_summarizer/
├── __pycache__/                 Auto-generated Python cache (ignore)
├── prompts/
│   ├── abstract_prompt.txt      Prompt template for abstract section
│   ├── citation_prompt.txt      Prompt template for citation extraction
│   ├── conclusion_prompt.txt    Prompt template for conclusion section
│   ├── introduction_prompt.txt  Prompt template for introduction section
│   ├── methods_prompt.txt       Prompt template for methods section
│   ├── results_prompt.txt       Prompt template for results section
│   └── synthesis_prompt.txt     Prompt template for full summary generation
├── agent1_extraction.py         Agent 1: PDF parsing and section extraction
├── agent2_synthesis.py          Agent 2: Summary generation and citation extraction
├── agent3_verification.py       Agent 3: Citation verification and hallucination removal
├── app.py                       Optional web UI built with Flask
├── baselineTest.py              Baseline single-prompt comparison script
├── demo.html                    Demo HTML file
├── main.py                      Entry point — run this file
├── utils.py                     Shared utilities for PDF parsing and JSON handling
├── requirements.txt             Required Python libraries
└── README.md                    Project documentation
```

---

## Setup Instructions

### Step 1 — Get a Free Groq API Key

Go to **https://console.groq.com** and sign up with any email.  
Click **API Keys** on the left sidebar, then click **Create API Key**.  
Copy the key. It starts with `gsk_` and requires no credit card.  
The free tier gives 14,400 requests per day.

### Step 2 — Install Python

Requires Python 3.8 or higher.  
Download from https://python.org if not already installed.  
On Windows, tick **"Add Python to PATH"** during installation.

### Step 3 — Install Required Libraries

```bash
pip install groq pymupdf sentence-transformers numpy flask
```

### Step 4 — Navigate to the Project Folder

On Windows:

```cmd
cd C:\Users\YourName\Desktop\AI PROJECT\research_summarizer
```


### Step 5 — Set Your API Key

On Windows CMD:

set GROQ_API_KEY=gsk_your_actual_key_here


### Step 6 — Run on a PDF

Place your PDF inside the `research_summarizer` folder, then run:

python main.py your_paper.pdf

---

## Expected Terminal Output

```
=================================================================
  Research Paper Summarization Agent
  Three-Agent Architecture with Bias Mitigation
  UET Taxila - AI Course Project
=================================================================

[Agent 1] Starting Extraction Agent...
[Agent 1] Parsing PDF...
[Agent 1] Segmenting into sections...
[Agent 1] Detected sections: ['preamble', 'approach', 'abstract', 'introduction', 'discussion', 'related work', 'conclusion', 'references']
[Agent 1] Skipping unmapped section: 'preamble'
[Agent 1] Processing section: 'approach' (4026 chars)...
[Agent 1] Section 'approach' extracted successfully.
[Agent 1] Processing section: 'abstract' (993 chars)...
[Agent 1] Section 'abstract' extracted successfully.
[Agent 1] Processing section: 'introduction' (2010 chars)...
[Agent 1] Section 'introduction' extracted successfully.
[Agent 1] Processing section: 'discussion' (514 chars)...
[Agent 1] Section 'discussion' extracted successfully.
[Agent 1] Skipping unmapped section: 'related work'
[Agent 1] Processing section: 'conclusion' (1052 chars)...
[Agent 1] Section 'conclusion' extracted successfully.
[Agent 1] Stored raw references (6074 chars)
[Agent 1] Extraction complete. 5 sections processed.

[Agent 2] Starting Synthesis Agent...
[Agent 2] Generating synthesized abstract...
[Agent 2] Abstract generated (1140 chars).
[Agent 2] Extracting citations (6074 chars)...
[Agent 2] Extracted 18 candidate citations.
[Agent 2] Synthesis complete.

[Agent 3] Starting Verification Agent...
[Agent 3] Verifying 18 candidate citations...
[Agent 3] Loading sentence-transformer model (all-MiniLM-L6-v2)...
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|█████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 1925.97it/s]
[Agent 3] Model loaded.
[Agent 3] Citation 1: VERIFIED (exact match) — Bruce Middleton
[Agent 3] Citation 2: VERIFIED (exact match) — Saloni Khurana
[Agent 3] Citation 3: VERIFIED (exact match) — Ashwini Sheth, Sachin Bhosale, and Adnan
[Agent 3] Citation 4: VERIFIED (exact match) — Muqbil
[Agent 3] Citation 5: VERIFIED (exact match) — Alex Andrew, Sam Spillard, Joshua Collye
[Agent 3] Citation 6: VERIFIED (exact match) — Shah Md Istiaque, Md Toki Tahmid, Asif I
[Agent 3] Citation 7: VERIFIED (exact match) — Gautam Srivastava, Rutvij H. Jhaveri, Sw
[Agent 3] Citation 8: VERIFIED (exact match) — IANS
[Agent 3] Citation 9: VERIFIED (exact match) — Chuyi, Yan, Chen Zhang, Zhigang Lu, Zehu
[Agent 3] Citation 10: VERIFIED (exact match) — Victor Mayoral-Vilches, Ruffin White, Gi
[Agent 3] Citation 11: VERIFIED (exact match) — Ricardo M. Czekster, Roberto Metere, and
[Agent 3] Citation 12: VERIFIED (exact match) — Carsten Maple, Matthew Bradbury, Anh Tua
[Agent 3] Citation 13: VERIFIED (exact match) — Rahul K. Vigneswaran, R. Vinayakumar, K.
[Agent 3] Citation 14: VERIFIED (exact match) — Yuqi Chen, Bohan Xuan, Christopher M. Po
[Agent 3] Citation 15: VERIFIED (exact match) — Elhaam Abdulrahman Debas, Razan Sulaiman
[Agent 3] Citation 16: VERIFIED (exact match) — Mohammad Kamrul Hasan, AKM Ahasan Habib,
[Agent 3] Citation 17: VERIFIED (exact match) — Aušrius Juozapavičius, Agnė Brilingaitė,
[Agent 3] Citation 18: HALLUCINATED (score=0.00) — ?

[Agent 3] Results: 17 verified, 0 uncertain, 1 hallucinated.
[Agent 3] Hallucination rate: 5.56% (1/18)
[Agent 3] Verification complete.

=================================================================
PIPELINE RESULTS SUMMARY
=================================================================

--- VERIFIED SUMMARY ---
This study addresses the pressing issue of cyber security, driven by the escalating threat of cybercrime and the increasing reliance on technology. The core research problem revolves around protecting internet-based systems from various cyber threats, including illicit activities, malware, and vandalism. To tackle this issue, the proposed methodology involves conducting a comprehensive literature review and a SWOT analysis to identify strengths, weaknesses, opportunities, and threats in the field of cyber security. The experimental setup is based on a review of current research and trends, without specific datasets. The main findings suggest that the probability of cyber attacks will continue to rise with the advancement of technologies such as 5G and AI. The primary conclusion of this study emphasizes the importance of cyber security and highlights the need for further research to mitigate the growing threat of cybercrime, ultimately aiming to promote a safer online environment. The study contributes to the discussion of cyber security and its applications, paving the way for potential future paths in this critical field.

--- SECTIONS EXTRACTED ---
  - approach
  - abstract
  - introduction
  - discussion
  - conclusion

--- CITATION VERIFICATION REPORT ---
  Total citations generated : 18
  Verified citations        : 17
  Uncertain citations       : 0
  Hallucinated citations    : 1
  Hallucination rate        : 5.56%
[Main] Full output saved to: output_paper_20250607_143022.json
```

---

## Web Interface (Optional)

A browser-based UI is included for easier use without the terminal.

```cmd
python app.py
```

Then open your browser and go to **http://localhost:5000**

- Enter your Groq API key and click **Save**
- Select a PDF file
- Click **Run Pipeline**
- Results appear across four tabs: Summary, Citations, Stats, Raw JSON

---

## Output File

After each run, a JSON file is saved in the project folder:

```
output_papername_20250607_143022.json
```

The file contains:

- `verified_summary` — the generated abstract
- `verified_citations` — citations confirmed against the source document
- `hallucinated_citations` — citations that were removed
- `uncertain_citations` — low-confidence matches flagged for review
- `hallucination_rate_percent` — percentage of citations that were hallucinated
- `sections_extracted` — list of sections successfully processed

---

## Evaluation Results

Tested on three research papers from the computer science and AI domains.

Paper	                      Single promp (Baseline)	Three-Agent System	Improvement
Paper 1 (Cybersecurity)           	0.0837	                  0.225	           +169%
Paper 2 (Quantum Computing)	        0.0660	                  0.216	           +227%
Paper 3 (Multi-Agent LLM)	        0.1152	                  0.275	           +139%
Average	                            0.0883	                  0.239	           +170%

The three-agent system achieved an average improvement of **170%** in ROUGE-L score.

---

## Dependencies

| Library | Purpose |
|---|---|
| `groq` | Llama-3.3-70b-versatile API (free tier) |
| `pymupdf` | PDF parsing and text extraction |
| `sentence-transformers` | Semantic similarity for citation verification |
| `numpy` | Numerical operations |
| `flask` | Web UI (optional) |

---

## Troubleshooting

**"No module named groq"**  
Run: `pip install groq`

**"No module named fitz"**  
Run: `pip install pymupdf` — fitz is the internal name for pymupdf

**"Section detection found only 1 section"**  
The PDF uses non-standard formatting. The system automatically switches to fallback chunking.

**"429 rate limit error"**  
You hit the Groq free tier per-minute limit. Wait 60 seconds and run again.

**"sentence-transformers is slow on first run"**  
It downloads the all-MiniLM-L6-v2 model (~80MB) once and caches it. Subsequent runs are fast.

**Buttons not working in the web UI**  
Save your API key first by clicking the Save button, then click Run Pipeline.

---

## Model Used

This system uses **Llama-3.3-70b-versatile** served through the Groq API.  
Free access with no credit card required — sign up at https://console.groq.com

---

## References

- Inoue et al. (2025). DrugAgent. arXiv:2408.13378 — https://arxiv.org/abs/2408.13378  
- Sun et al. (2024). Prompt Chaining or Stepwise Prompt? ACL 2024.  
- Wu et al. (2023). AutoGen. arXiv:2308.08155 — https://arxiv.org/abs/2308.08155