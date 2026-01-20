# RAG System Evaluation

This folder contains the evaluation framework for testing the RAG (Retrieval-Augmented Generation) system's performance.

## Folder Structure

```
evaluation/
├── README.md                 # This file
├── evaluate_system.py        # Main evaluation script
├── generate_plots.py         # Visualization generator
├── metrics.py                # Metric calculation functions
├── evaluation_results.json   # Raw results (generated after running)
├── evaluation_report.md      # Human-readable report (generated after running)
├── plots/                    # Generated visualizations (after running generate_plots.py)
│   ├── metrics_by_query.png
│   ├── summary_radar.png
│   ├── latency_distribution.png
│   ├── negative_tests.png
│   └── metrics_summary.png
└── dataset/
    ├── ground_truth.json     # Test queries with expected answers
    └── test_documents/       # PDF files used for evaluation
        ├── paper1.pdf
        ├── paper2.pdf
        └── lecture1.pdf
```

## How to Run

### Prerequisites

1. Ensure the backend environment is set up with all dependencies
2. Make sure Ollama is running (for embeddings)
3. Ensure `.env` file exists in `backend/app/` with required API keys:
   - `OPENROUTER_API_KEY` - for LLM generation

### Running the Evaluation

From the project root:

```bash
cd evaluation
python evaluate_system.py
```

Or from the evaluation folder:

```bash
python evaluate_system.py
```

The script will:
1. Create a temporary session
2. Ingest all PDFs from `dataset/test_documents/`
3. Run each query from `ground_truth.json`
4. Calculate metrics and save results

### Output Files

After running, two files are generated:

- **evaluation_results.json** - Raw JSON results for programmatic access
- **evaluation_report.md** - Formatted markdown report with tables and summaries

## Visual Analysis

The following visualizations provide a comprehensive view of the system's performance.

### 1. Performance Summary vs Targets
A direct comparison of average system performance against the defined success criteria.
![Performance Summary](plots/metrics_summary.png)

### 2. Metric Distribution (Consistency)
This box plot reveals the consistency of the system. Tighter boxes indicate reliable performance across different queries, while wider boxes suggest variability.
![Metric Distribution](plots/metric_distributions.png)

### 3. Detailed Metrics by Query
A granular view of how each query performed. This helps identify specific topic areas where the system may struggle.
![Metrics by Query](plots/metrics_by_query.png)

### 4. Latency Analysis
Response times for each query. Green bars indicate responses under the 5-second target.
![Latency Distribution](plots/latency_distribution.png)


### Generating Visualizations

After running the evaluation, generate plots:

```bash
python generate_plots.py
```

**Requirements:** `matplotlib` and `numpy`

```bash
pip install matplotlib numpy
```

This creates the `plots/` folder with:

| Plot | Description |
|------|-------------|
| `metrics_summary.png` | Average metrics compared to target thresholds |
| `metric_distributions.png` | Box plot showing spread/consistency of scores |
| `metrics_by_query.png` | Grouped bar chart of Recall, MRR, Keyword Recall per query |
| `latency_distribution.png` | Response time analysis with fast/slow color coding |

## Files Explained

### evaluate_system.py

Main evaluation script that:
- Ingests test documents into a session
- Runs queries against the RAG system
- Measures retrieval and generation quality
- Generates reports

### metrics.py

Contains metric calculation functions:

| Function | Description |
|----------|-------------|
| `calculate_retrieval_metrics()` | Computes Precision@K, Recall@K, and MRR |
| `calculate_keyword_recall()` | Checks if expected keywords appear in generated text |
| `LatencyTimer` | Utility class for measuring response time |

### generate_plots.py

Generates visualizations

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

**API errors:**
- Check `.env` file has valid `OPENROUTER_API_KEY`
- Ensure Ollama is running for embeddings
