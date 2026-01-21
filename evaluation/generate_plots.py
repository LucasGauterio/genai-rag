"""
Generate evaluation plots following data visualization best practices.

Best practices applied:
- Clear, descriptive titles
- Labeled axes with units
- Consistent color palette (colorblind-friendly)
- Appropriate chart types for data
- No chartjunk (unnecessary decorations)
- High contrast for readability
- Sorted data where meaningful
- Reference lines for targets/thresholds
"""

import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(CURRENT_DIR, "evaluation_results.json")
PLOTS_DIR = os.path.join(CURRENT_DIR, "plots")

# Colorblind-friendly palette (IBM Design Library)
COLORS = {
    "blue": "#648FFF",
    "purple": "#785EF0",
    "pink": "#DC267F",
    "orange": "#FE6100",
    "yellow": "#FFB000",
    "green": "#009E73",
    "gray": "#999999",
    "dark": "#333333",
    "light_bg": "#F4F4F4",
}

def setup_style():
    """Set up matplotlib style for clean, professional plots."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 14,
        "figure.dpi": 300,  # High resolution
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.alpha": 0.3,
    })


def load_results():
    """Load evaluation results from JSON file."""
    if not os.path.exists(RESULTS_FILE):
        return []
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("results", [])


def plot_metrics_by_query(results, output_path):
    """Grouped bar chart showing Recall, MRR, and Keyword Recall per query."""
    # Filter to chat results with valid keyword_recall (not None)
    chat_results = [r for r in results if "neg" not in r["id"] and r["metrics"]["keyword_recall"] is not None]

    if not chat_results:
        return

    # Sort by average metric (ascending - worst first)
    chat_results = sorted(
        chat_results,
        key=lambda r: (r["metrics"]["recall"] + r["metrics"]["mrr"] + r["metrics"]["keyword_recall"]) / 3
    )

    queries = [r["id"] for r in chat_results]

    recall = [r["metrics"]["recall"] * 100 for r in chat_results]
    mrr = [r["metrics"]["mrr"] * 100 for r in chat_results]
    keyword = [r["metrics"]["keyword_recall"] * 100 for r in chat_results]

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(queries))
    width = 0.25

    ax.bar(x - width, recall, width, label="Recall@K", color=COLORS["blue"])
    ax.bar(x, mrr, width, label="MRR", color=COLORS["purple"])
    ax.bar(x + width, keyword, width, label="Keyword Recall", color=COLORS["orange"])

    # Target line
    ax.axhline(y=80, color=COLORS["gray"], linestyle="--", linewidth=1, alpha=0.7)
    
    ax.set_xlabel("Query ID")
    ax.set_ylabel("Score (%)")
    ax.set_title("Retrieval and Generation Metrics by Query")
    ax.set_xticks(x)
    ax.set_xticklabels(queries, rotation=0)
    ax.set_ylim(0, 115) # More space for legend/text
    ax.legend(loc="upper left", ncol=3)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def plot_metric_distributions(results, output_path):
    """Box plot showing the distribution of key metrics."""
    # Filter to chat results with valid keyword_recall (not None)
    chat_results = [r for r in results if "neg" not in r["id"] and r["metrics"]["keyword_recall"] is not None]
    if not chat_results:
        return

    data = [
        [r["metrics"]["recall"] * 100 for r in chat_results],
        [r["metrics"]["mrr"] * 100 for r in chat_results],
        [r["metrics"]["keyword_recall"] * 100 for r in chat_results]
    ]
    labels = ["Recall@K", "MRR", "Keyword Recall"]

    fig, ax = plt.subplots(figsize=(8, 6))

    # Box plot
    bplot = ax.boxplot(data, patch_artist=True, labels=labels, medianprops=dict(color="black"))

    # Colorize
    colors = [COLORS["blue"], COLORS["purple"], COLORS["orange"]]
    for patch, color in zip(bplot['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    # Jittered data points
    for i, d in enumerate(data):
        y = d
        x = np.random.normal(1 + i, 0.04, size=len(y))
        ax.plot(x, y, 'o', alpha=0.6, color=COLORS["dark"], markersize=4)

    ax.set_ylabel("Score (%)")
    ax.set_title("Distribution of Performance Metrics")
    ax.set_ylim(-5, 105)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def plot_latency_distribution(results, output_path):
    """Horizontal bar chart showing latency per query."""
    chat_results = [r for r in results if "neg" not in r["id"]]
    if not chat_results:
        return

    # Sort descending
    chat_results = sorted(chat_results, key=lambda r: r["metrics"]["latency_ms"], reverse=False) # Fastest at top now

    queries = [r["id"] for r in chat_results]
    latencies = [r["metrics"]["latency_ms"] / 1000 for r in chat_results]

    colors = [COLORS["green"] if lat < 5 else COLORS["orange"] for lat in latencies]

    fig, ax = plt.subplots(figsize=(10, len(queries) * 0.6 + 2))

    y_pos = np.arange(len(queries))
    bars = ax.barh(y_pos, latencies, color=colors, height=0.6)

    # Values
    for bar, latency in zip(bars, latencies):
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f"{latency:.1f}s", 
                va='center', fontsize=9)

    ax.axvline(x=5, color=COLORS["gray"], linestyle="--", alpha=0.5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(queries)
    ax.set_xlabel("Latency (seconds)")
    ax.set_title("Response Latency by Query (Lower is Better)")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def plot_metrics_summary_bar(results, output_path):
    """Combined bar chart for average performance."""
    chat_results = [r for r in results if "neg" not in r["id"]]
    negative_results = [r for r in results if "neg" in r["id"]]

    if not chat_results:
        return

    # Filter out None keyword_recall values
    keyword_values = [r["metrics"]["keyword_recall"] for r in chat_results if r["metrics"]["keyword_recall"] is not None]

    metrics = {
        "Recall@K": np.mean([r["metrics"]["recall"] for r in chat_results]),
        "MRR": np.mean([r["metrics"]["mrr"] for r in chat_results]),
        "Keyword Recall": np.mean(keyword_values) if keyword_values else 0.0,
        "Negative Tests": (sum(1 for r in negative_results if r["metrics"]["refusal_score"] == 1.0) / len(negative_results)) if negative_results else 1.0,
    }

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(metrics))
    width = 0.5

    vals = list(metrics.values())

    bars = ax.bar(x, [v*100 for v in vals], width, color=COLORS["blue"])

    # Labels on top of bars
    for i, v in enumerate(vals):
        ax.text(i, v*100 + 1, f"{v:.0%}", ha='center', fontweight='bold', color=COLORS["dark"])

    ax.set_xticks(x)
    ax.set_xticklabels(list(metrics.keys()))
    ax.set_ylabel("Score (%)")
    ax.set_title("Average Performance Metrics")
    ax.set_ylim(0, 115)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def main():
    """Generate all evaluation plots."""
    print("Generating evaluation plots...")
    setup_style()
    os.makedirs(PLOTS_DIR, exist_ok=True)

    results = load_results()
    if not results:
        print("No results found. Run evaluate_system.py first.")
        return

    print(f"Loaded {len(results)} results")

    # Generate plots
    plot_metrics_by_query(results, os.path.join(PLOTS_DIR, "metrics_by_query.png"))
    plot_metric_distributions(results, os.path.join(PLOTS_DIR, "metric_distributions.png"))
    plot_latency_distribution(results, os.path.join(PLOTS_DIR, "latency_distribution.png"))
    plot_metrics_summary_bar(results, os.path.join(PLOTS_DIR, "metrics_summary.png"))

    print(f"\nAll plots saved to {PLOTS_DIR}/")


if __name__ == "__main__":
    main()
