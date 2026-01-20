import sys
import os
import json
import time
import uuid
import glob
from typing import List, Dict

# -----------------------------------------------------------------------------
# 1. SETUP PATHS & ENV
# -----------------------------------------------------------------------------
# Add backend/app to sys.path so we can import from there
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
backend_app_dir = os.path.join(project_root, "backend", "app")

sys.path.append(backend_app_dir)

# Try to load .env from backend/app/.env
try:
    from dotenv import load_dotenv
    env_path = os.path.join(backend_app_dir, ".env")
    if os.path.exists(env_path):
        print(f"Loading .env from {env_path}")
        load_dotenv(env_path)
    else:
        print("Warning: .env file not found in backend/app, relying on existing env vars.")
except ImportError:
    print("python-dotenv not installed. Assuming env vars are set.")


# -----------------------------------------------------------------------------
# 2. IMPORTS FROM BACKEND
# -----------------------------------------------------------------------------
try:
    from rag.session_store import get_session_store
    from rag.ingestion import ingest_document
    from generation.service import generate_chat_answer
    
    # Import Metrics
    from metrics import calculate_retrieval_metrics, calculate_keyword_recall, LatencyTimer

except ImportError as e:
    print(f"Error importing backend modules: {e}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)


# -----------------------------------------------------------------------------
# 3. CONFIGURATION
# -----------------------------------------------------------------------------
DATASET_DIR = os.path.join(current_dir, "dataset")
TEST_DOCS_DIR = os.path.join(DATASET_DIR, "test_documents")
GROUND_TRUTH_FILE = os.path.join(DATASET_DIR, "ground_truth.json")
RESULTS_FILE = os.path.join(current_dir, "evaluation_results.json")
REPORT_FILE = os.path.join(current_dir, "evaluation_report.md")

def ingest_test_documents(session_id: str, store):
    """Ingest all PDFs from test_documents folder into the session."""
    # Use all available test documents for comprehensive evaluation
    pdf_files = glob.glob(os.path.join(TEST_DOCS_DIR, "*.pdf"))

    if not pdf_files:
        print(f"No test documents found in {TEST_DOCS_DIR}")
        return

    print(f"Ingesting {len(pdf_files)} documents...")
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"  - Processing {filename}...")
        
        try:
            with open(pdf_path, "rb") as f:
                # Use shared ingestion service
                result = ingest_document(f, filename, session_id)
                num_docs = result.get("num_added", 0) # Store returns list of ids or count
                # Helper: SessionStore.add_documents usually returns boolean or list of IDs.
                # Let's check session_store.py if possible, but assume list of IDs or truthy.
                
                # Looking at ingest_document implementation: it returns result from store.add_documents
                # Let's assume it works.
                print(f"    Ingested {filename}.")

        except Exception as e:
            print(f"    Error processing {filename}: {e}")


def run_evaluation():
    # A. INIT SESSION
    print("Initializing SessionStore...")
    store = get_session_store()

    # Create a new session (in-memory, can't persist between runs)
    session_data = store.create_session()
    session_id = session_data["session_id"]
    print(f"Created evaluation session: {session_id}")

    # B. INGEST DATA
    # Note: This is slow due to SemanticChunker calling embeddings.
    # Consider using fewer/smaller test docs for faster iteration.
    try:
        ingest_test_documents(session_id, store)
    except Exception as e:
        print(f"Ingestion failed: {e}")
        return

    # C. LOAD GROUND TRUTH
    print(f"Loading ground truth from {GROUND_TRUTH_FILE}...")
    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        all_queries = data.get("queries", [])

    # Use all queries (all documents are ingested)
    queries = all_queries
    print(f"Running {len(queries)} queries")

    results = []
    
    # D. RUN EVALUATION LOOP
    print(f"Starting evaluation on {len(queries)} queries...")
    
    for idx, q in enumerate(queries):
        q_id = q.get("id")
        q_text = q.get("query")
        q_type = q.get("type", "chat")
        
        # Ground Truth Data
        gt_doc = q.get("document")
        gt_pages = q.get("relevant_pages", [])
        gt_keywords = q.get("expected_keywords", [])
        expected_behavior = q.get("expected_behavior", "normal")
        
        print(f"\nProcessing [{idx+1}/{len(queries)}] {q_id}: {q_text[:60]}...")
        
        timer = LatencyTimer()
        timer.start()
        
        retrieved_chunks = []
        generated_text = ""
        error_msg = None
        
        try:
            # Shared Service Call
            # This ensures we are testing the EXACT code path used in production
            response = generate_chat_answer(
                session_id=session_id,
                question=q_text,
                k=5,
                mode="chat" # default
            )
            
            generated_text = response["answer"]
            retrieved_chunks = response.get("retrieved_chunks", []) # We added this to the return dict
            
        except Exception as e:
            error_msg = str(e)
            print(f"  Error: {e}")
            
        latency_ms = timer.stop()
        
        # 3. Compute Metrics
        
        # Retrieval Metrics
        ret_metrics = calculate_retrieval_metrics(retrieved_chunks, gt_pages, gt_doc)
        
        # Generation Metrics
        keyword_recall = calculate_keyword_recall(generated_text, gt_keywords)
        
        # Refusal Check for negative test cases
        #
        # Professional approach: Don't rely on parsing LLM output phrases.
        # Instead, check if the LLM's response indicates it couldn't answer
        # based on the provided context. We use two signals:
        #
        # 1. Retrieval signal: For off-topic queries, retrieved chunks won't
        #    be from the "correct" document (precision=0, recall=0)
        # 2. Response signal: The LLM should acknowledge lack of relevant info
        #
        # A proper refusal means: system retrieved irrelevant content AND
        # the LLM acknowledged it couldn't answer from that content.

        refusal_score = 0.0
        if expected_behavior == "should_refuse":
            # For negative test cases, we check if the LLM correctly refused to answer.
            #
            # Note: We cannot use retrieval precision here because negative tests have
            # no relevant_pages defined (empty list), which causes precision to always
            # be 0.0 by definition. Instead, we rely solely on detecting refusal
            # language in the LLM's response.
            #
            # A proper refusal means the LLM acknowledged it couldn't find relevant
            # information in the provided documents.

            refusal_indicators = [
                "do not contain", "does not contain", "don't contain",
                "no relevant", "no information", "not covered",
                "cannot provide", "can't provide", "unable to",
                "not mentioned", "not discussed", "outside",
                "i'm sorry", "i apologize", "couldn't find",
                "not able to", "no data", "not in the",
                "beyond the scope", "not addressed"
            ]
            response_indicates_refusal = any(
                phrase in generated_text.lower() for phrase in refusal_indicators
            )

            # Score: 1.0 only if the LLM explicitly refused/acknowledged lack of info
            refusal_score = 1.0 if response_indicates_refusal else 0.0
        else:
            refusal_score = 1.0  # Not a refusal case, N/A

        
        result_entry = {
            "id": q_id,
            "type": q_type,
            "query": q_text,
            "metrics": {
                "precision": ret_metrics["precision"],
                "recall": ret_metrics["recall"],
                "mrr": ret_metrics["mrr"],
                "keyword_recall": keyword_recall,
                "latency_ms": latency_ms,
                "refusal_score": refusal_score
            },
            "generated_text_preview": generated_text[:200],
            "error": error_msg
        }
        results.append(result_entry)
        
        print(f"  Precision: {ret_metrics['precision']:.2f}, Recall: {ret_metrics['recall']:.2f}, Keyword: {keyword_recall:.2f}, Time: {latency_ms:.0f}ms")

    # E. SAVE RESULTS (JSON for programmatic access)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, indent=2)
    print(f"\nSaved JSON results to {RESULTS_FILE}")

    # F. COMPUTE SUMMARY STATISTICS
    # Separate chat results from negative test cases
    chat_results = [r for r in results if "neg" not in r["id"]]
    negative_results = [r for r in results if "neg" in r["id"]]

    avg_precision = sum(r["metrics"]["precision"] for r in chat_results) / len(chat_results) if chat_results else 0
    avg_recall = sum(r["metrics"]["recall"] for r in chat_results) / len(chat_results) if chat_results else 0
    avg_keyword = sum(r["metrics"]["keyword_recall"] for r in chat_results) / len(chat_results) if chat_results else 0
    avg_latency = sum(r["metrics"]["latency_ms"] for r in chat_results) / len(chat_results) if chat_results else 0
    avg_mrr = sum(r["metrics"]["mrr"] for r in chat_results) / len(chat_results) if chat_results else 0

    # Negative test pass rate
    negative_passed = sum(1 for r in negative_results if r["metrics"]["refusal_score"] == 1.0)
    negative_total = len(negative_results)

    # G. GENERATE MARKDOWN REPORT
    report = generate_markdown_report(
        results=results,
        chat_results=chat_results,
        negative_results=negative_results,
        avg_precision=avg_precision,
        avg_recall=avg_recall,
        avg_mrr=avg_mrr,
        avg_keyword=avg_keyword,
        avg_latency=avg_latency,
        negative_passed=negative_passed,
        negative_total=negative_total
    )

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Saved evaluation report to {REPORT_FILE}")

    # H. CONSOLE SUMMARY
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    print(f"Chat Queries:        {len(chat_results)}")
    print(f"Negative Tests:      {len(negative_results)}")
    print("-"*50)
    print("Chat Mode Metrics (Retrieval + Generation):")
    print(f"  Avg Recall@K:      {avg_recall:.2%}")
    print(f"  Avg MRR:           {avg_mrr:.2%}")
    print(f"  Avg Keyword Recall:{avg_keyword:.2%}")
    print(f"  Avg Latency:       {avg_latency:.0f} ms")
    print("-"*50)
    print(f"Negative Tests:      {negative_passed}/{negative_total} passed")
    print("="*50)

    # Clean up (Optional)
    # store.delete_session(session_id)


def generate_markdown_report(
    results, chat_results, negative_results,
    avg_precision, avg_recall, avg_mrr, avg_keyword, avg_latency,
    negative_passed, negative_total
) -> str:
    """Generate a professional markdown evaluation report."""

    from datetime import datetime

    report = f"""# RAG System Evaluation Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Chat Queries Tested** | {len(chat_results)} |
| **Negative Tests** | {negative_passed}/{negative_total} passed |

### Chat Mode Performance (Retrieval + Generation)

| Metric | Value |
|--------|-------|
| **Avg Recall@K** | {avg_recall:.1%} |
| **Avg MRR** | {avg_mrr:.1%} |
| **Avg Keyword Recall** | {avg_keyword:.1%} |
| **Avg Latency** | {avg_latency:.0f} ms |

---

## Metrics Explanation

| Metric | Description |
|--------|-------------|
| **Recall@K** | Percentage of relevant source pages successfully retrieved |
| **MRR (Mean Reciprocal Rank)** | How early the first relevant result appears (1.0 = first position) |
| **Keyword Recall** | Percentage of expected keywords present in generated answers |
| **Negative Test** | System correctly refuses to answer off-topic queries |

---

## Detailed Results

### Chat Queries (Full Pipeline: Retrieval + LLM Generation)

| Query | Recall | MRR | Keyword Recall | Latency |
|-------|--------|-----|----------------|---------|
"""

    for r in chat_results:
        m = r["metrics"]
        query_short = r["query"][:50] + "..." if len(r["query"]) > 50 else r["query"]
        report += f"| {query_short} | {m['recall']:.0%} | {m['mrr']:.0%} | {m['keyword_recall']:.0%} | {m['latency_ms']:.0f}ms |\n"

    report += """
### Negative Tests (Should Refuse)

| Query | Refused Correctly |
|-------|-------------------|
"""

    for r in negative_results:
        m = r["metrics"]
        query_short = r["query"][:50] + "..." if len(r["query"]) > 50 else r["query"]
        status = "✅ Yes" if m["refusal_score"] == 1.0 else "❌ No"
        report += f"| {query_short} | {status} |\n"

    report += """
---

## Sample Generated Responses

"""

    # Show a few sample responses
    for r in results[:3]:
        if r.get("generated_text_preview"):
            report += f"**Query:** {r['query']}\n\n"
            report += f"> {r['generated_text_preview']}...\n\n"

    report += """---

## Methodology

1. **Dataset:** Ground truth queries with expected keywords and relevant page numbers
2. **Retrieval Evaluation:** Compare retrieved chunks against known relevant pages
3. **Generation Evaluation:** Check if generated answers contain expected keywords
4. **Negative Testing:** Verify system refuses off-topic queries appropriately

---

*Report generated by evaluate_system.py*
"""

    return report

if __name__ == "__main__":
    run_evaluation()
