import re
import json

try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[Agent 3] WARNING: sentence-transformers not installed. Semantic pass disabled.")


SIMILARITY_THRESHOLD = 0.85


def normalize_author(author_str):
    if not author_str:
        return ""
    parts = re.split(r"[,;]", author_str)
    if parts:
        first_author = parts[0].strip()
        surnames = first_author.split()
        if surnames:
            return surnames[-1].lower()
    return author_str.lower().strip()


def extract_year(text):
    match = re.search(r"\b(19|20)\d{2}\b", str(text))
    if match:
        return match.group()
    return None


def exact_match_check(candidate, raw_references):
    author = normalize_author(candidate.get("author_list", ""))
    year = str(candidate.get("year", "") or "")

    if not author:
        return False

    ref_lower = raw_references.lower()

    if author and author in ref_lower:
        if not year or year in raw_references:
            return True

    title = candidate.get("title", "") or ""
    if title and len(title) > 10:
        title_words = title.lower().split()[:4]
        if all(w in ref_lower for w in title_words if len(w) > 3):
            return True

    return False


def semantic_match_check(candidate, ref_entries, model):
    title = candidate.get("title", "") or ""
    if not title or len(title) < 10:
        return False, 0.0

    try:
        candidate_embedding = model.encode(title, convert_to_tensor=True)
        ref_embeddings = model.encode(ref_entries, convert_to_tensor=True)
        similarities = util.cos_sim(candidate_embedding, ref_embeddings)[0]
        max_score = float(similarities.max())
        return max_score >= SIMILARITY_THRESHOLD, max_score
    except Exception as e:
        print(f"[Agent 3] Semantic match error: {e}")
        return False, 0.0


def parse_ref_titles(raw_references):
    lines = raw_references.split("\n")
    titles = []
    for line in lines:
        line = line.strip()
        if len(line) > 20:
            cleaned = re.sub(r"^\[?\d+\]?\.?\s*", "", line)
            cleaned = re.sub(r"\b(19|20)\d{2}\b.*", "", cleaned).strip()
            if len(cleaned) > 10:
                titles.append(cleaned)
    return titles if titles else [raw_references[:500]]


def run_verification_agent(summary_text, candidate_citations, raw_references):
    print("\n[Agent 3] Starting Verification Agent...")
    print(f"[Agent 3] Verifying {len(candidate_citations)} candidate citations...")

    model = None
    if SENTENCE_TRANSFORMERS_AVAILABLE and candidate_citations:
        try:
            print("[Agent 3] Loading sentence-transformer model (all-MiniLM-L6-v2)...")
            model = SentenceTransformer("all-MiniLM-L6-v2")
            print("[Agent 3] Model loaded.")
        except Exception as e:
            print(f"[Agent 3] Model load failed: {e}")
            model = None

    ref_titles = parse_ref_titles(raw_references) if raw_references else []

    verified = []
    hallucinated = []
    uncertain = []

    # Verify each citation
    for i, citation in enumerate(candidate_citations):
        result = {
            "citation": citation,
            "verification_status": "uncertain",
            "confidence": 0.0
        }
        
        # Safe extraction with None handling
        author_info = citation.get('author_list')
        if author_info is None:
            author_info = '?'
        elif isinstance(author_info, str) and len(author_info) > 40:
            author_info = author_info[:40]
        
        # Check for exact match in references
        if exact_match_check(citation, raw_references):
            result["verification_status"] = "verified"
            result["confidence"] = 0.95
            verified.append(result)
            print(f"[Agent 3] Citation {i+1}: VERIFIED (exact match) — {author_info}")
        
        # Try semantic match if model is available and not already verified
        elif model and ref_titles:
            is_match, score = semantic_match_check(citation, ref_titles, model)
            if is_match:
                result["verification_status"] = "verified"
                result["confidence"] = score
                verified.append(result)
                print(f"[Agent 3] Citation {i+1}: VERIFIED (semantic, score={score:.2f}) — {author_info}")
            else:
                # Check if it's uncertain (medium confidence)
                if score > 0.5:
                    result["verification_status"] = "uncertain"
                    result["confidence"] = score
                    uncertain.append(result)
                    print(f"[Agent 3] Citation {i+1}: UNCERTAIN (score={score:.2f}) — {author_info}")
                else:
                    result["verification_status"] = "hallucinated"
                    result["confidence"] = score
                    hallucinated.append(result)
                    print(f"[Agent 3] Citation {i+1}: HALLUCINATED (score={score:.2f}) — {author_info}")
        
        # No model available, use basic check
        elif model is None:
            # Simple text overlap check
            title = citation.get("title", "") or ""
            if title and len(title) > 10 and title.lower() in raw_references.lower():
                result["verification_status"] = "verified"
                result["confidence"] = 0.7
                verified.append(result)
                print(f"[Agent 3] Citation {i+1}: VERIFIED (title match) — {author_info}")
            else:
                result["verification_status"] = "uncertain"
                result["confidence"] = 0.3
                uncertain.append(result)
                print(f"[Agent 3] Citation {i+1}: UNCERTAIN (no model) — {author_info}")

    print(f"\n[Agent 3] Results: {len(verified)} verified, {len(uncertain)} uncertain, {len(hallucinated)} hallucinated.")

    hallucination_rate = 0.0
    total = len(candidate_citations)
    if total > 0:
        hallucination_rate = round(len(hallucinated) / total * 100, 2)
        print(f"[Agent 3] Hallucination rate: {hallucination_rate}% ({len(hallucinated)}/{total})")

    final_output = {
        "verified_summary": summary_text,
        "verified_citations": verified,
        "uncertain_citations": uncertain,
        "hallucinated_citations": hallucinated,
        "hallucination_rate_percent": hallucination_rate,
        "total_citations_generated": total,
        "total_verified": len(verified),
        "total_hallucinated": len(hallucinated),
        "total_uncertain": len(uncertain)
    }

    print("[Agent 3] Verification complete.")
    return final_output