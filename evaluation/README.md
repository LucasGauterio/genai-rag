# RAG System Evaluation

This folder contains the evaluation framework for testing the RAG (Retrieval-Augmented Generation) system's performance.

> [!NOTE]
> **Evaluation Scope:** This evaluation focuses on the **RAG retrieval and answer generation system** using objective metrics (Recall, MRR, Keyword Recall). Flashcard quality is not evaluated as it requires subjective assessment of pedagogical value, which is outside the scope of quantitative evaluation.

## Structure

```
evaluation/
├── evaluate_system.py        # Main evaluation script
├── generate_plots.py         # Visualization generator
├── metrics.py                # Metric calculations
├── evaluation_results.json   # Raw results (generated)
├── evaluation_report.md      # Detailed report (generated)
├── visual_results.md         # Visual analysis
├── plots/                    # Generated visualizations
└── dataset/
    ├── ground_truth.json     # Test queries with expected answers
    └── test_documents/       # PDF files for evaluation
```

## Quick Start

**Prerequisites:** Backend environment set up, Ollama running, `.env` file configured

**Run evaluation:**
```bash
cd evaluation
python evaluate_system.py
```

**Generate visualizations:**
```bash
python generate_plots.py  # requires matplotlib, numpy
```

## Output Files

After running, two files are generated:

- **evaluation_results.json** - Raw JSON results for programmatic access
- **evaluation_report.md** - Formatted markdown report with tables and summaries
- **VISUAL_RESULTS.md** - Visual analysis with performance plots

### Generating Visualizations

**Plots generated:** `metrics_summary.png`, `metric_distributions.png`, `metrics_by_query.png`, `latency_distribution.png`

See [VISUAL_RESULTS.md](VISUAL_RESULTS.md) for visual analysis.

## Key Files

**evaluate_system.py** - Ingests test documents, runs queries, measures performance, generates reports

**metrics.py** - Functions: `calculate_retrieval_metrics()`, `calculate_keyword_recall()`, `LatencyTimer`

**generate_plots.py** - Creates visualizations from evaluation results

### dataset/ground_truth.json

JSON file containing test queries with ground truth data:

```json
{
  "queries": [
    {
      "id": "q01",
      "query": "What are the two main architectures...",
      "type": "chat",
      "document": "paper1.pdf",
      "relevant_pages": [6],
      "expected_keywords": ["Match-on-Card", "MoC", ...],
      "expected_behavior": "normal"
    }
  ]
}
```

**Fields:**
- `id` - Unique identifier (use `q_neg_*` prefix for negative tests)
- `query` - The question to ask
- `type` - Query type (`chat`)
- `document` - Source PDF filename
- `relevant_pages` - Page numbers containing the answer
- `expected_keywords` - Keywords that should appear in the response
- `expected_behavior` - `"normal"` or `"should_refuse"` for negative tests

## Metrics Explained

| Metric | Description |
|--------|-------------|
| **Recall@K** | % of relevant pages retrieved
| **MRR** | How early the first relevant result appears (1.0 = first)
| **Keyword Recall** | % of expected keywords in generated answer
| **Negative Test Pass** | System correctly refuses off-topic queries

## Adding New Test Cases

1. Add the PDF to `dataset/test_documents/`
2. Add query entries to `ground_truth.json`:

```json
{
  "id": "q_new",
  "query": "Your question here?",
  "type": "chat",
  "document": "your_document.pdf",
  "relevant_pages": [1, 2],
  "expected_keywords": ["keyword1", "keyword2"]
}
```

For negative tests (should refuse):

```json
{
  "id": "q_neg_new",
  "query": "Off-topic question not in any document?",
  "type": "chat",
  "document": null,
  "relevant_pages": [],
  "expected_keywords": [],
  "expected_behavior": "should_refuse"
}
```

## Keyword Matching

The evaluation uses flexible keyword matching:
- Case insensitive
- Hyphen/space insensitive (`"Match-on-Card"` matches `"match on card"`)
- Simple plural handling (`"CNN"` matches `"CNNs"`)

## Known Limitations

The following limitations are known and expected, given the scope of this project:

### Sample Size
The evaluation runs on 8 positive queries and 3 negative test cases. While sufficient for demonstrating system functionality and identifying major issues, this sample size is small for statistically significant conclusions.

### Keyword Recall as Generation Metric
We use keyword recall (presence of expected terms in the generated answer) as a proxy for answer quality. This is a practical heuristic but has limitations:
- A keyword being present doesn't guarantee the answer is correct (e.g., "X is NOT used" contains X but contradicts the expected answer)
- Good paraphrased answers may score lower if they use different terminology

### Negative Test Detection
Negative tests rely on detecting refusal phrases in the LLM response. This is heuristic-based and may not catch all failure modes (e.g., if the LLM confidently hallucinates an answer without using refusal language).

### Single k Value
The evaluation uses a fixed `k=5` for retrieval. Production systems may use different values, and performance can vary significantly with k.

---

## Troubleshooting

**Import errors:**
- Ensure you're running from the `evaluation/` directory
- Check that `backend/app/` is in the Python path

**No documents found:**
- Verify PDFs exist in `dataset/test_documents/`