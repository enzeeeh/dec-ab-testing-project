"""
Batch Analysis Runner
=====================
Runs validation + multi-metric statistical analysis for every dataset
(internal business experiments + external benchmarks) in a single command.

Outputs
-------
- reports/statistical_results/batch_summary.csv   — machine-readable summary
- docs/BATCH_ANALYSIS_REPORT.md                   — human-readable report
- Per-dataset: result CSVs, validation reports, figures
"""
from pathlib import Path
import sys
from typing import Optional
import math

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_pipeline import analyze_dataset
from scripts.statistical_analysis import StatisticalAnalyzer


# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------

DATASETS = [
    {
        "dataset_id": "test1_menu",
        "label": "Menu Navigation",
        "source_type": "internal_decision_data",
        "path": PROJECT_ROOT / "data" / "test1_menu.csv",
        "metrics": ["added_to_cart", "bounced", "revenue", "pages_viewed"],
        "primary_metric": "added_to_cart",
        "business_question": "Does a dropdown menu improve engagement vs. horizontal menu?",
        "clean_rules": None,
    },
    {
        "dataset_id": "test2_novelty_slider",
        "label": "Novelty Slider",
        "source_type": "internal_decision_data",
        "path": PROJECT_ROOT / "data" / "test2_novelty_slider.csv",
        "metrics": ["products_added_from_novelties", "is_registered", "novelty_revenue"],
        "primary_metric": "products_added_from_novelties",
        "business_question": "Do personalized novelty recommendations outperform manual selection?",
        "clean_rules": None,
    },
    {
        "dataset_id": "test3_product_sliders",
        "label": "Product Sliders",
        "source_type": "internal_decision_data",
        "path": PROJECT_ROOT / "data" / "test3_product_sliders.csv",
        "metrics": ["revenue_from_recommendations", "add_to_cart_rate", "slider_interactions",
                    "products_per_order", "avg_product_price"],
        "primary_metric": "revenue_from_recommendations",
        "business_question": "Which product slider recommendation strategy generates the most revenue?",
        "clean_rules": None,
    },
    {
        "dataset_id": "test4_reviews",
        "label": "Reviews",
        "source_type": "internal_decision_data",
        "path": PROJECT_ROOT / "data" / "test4_reviews.csv",
        "metrics": ["converted", "added_to_cart"],
        "primary_metric": "converted",
        "business_question": "Do featured reviews improve conversion and add-to-cart rates?",
        "clean_rules": None,
    },
    {
        "dataset_id": "test5_search_engine",
        "label": "Search Engine",
        "source_type": "internal_decision_data",
        "path": PROJECT_ROOT / "data" / "test5_search_engine.csv",
        "metrics": ["converted", "added_to_cart", "interacted_with_search", "avg_revenue_per_visitor"],
        "primary_metric": "converted",
        "business_question": "Does Algolia search outperform the existing Hybris search engine?",
        "clean_rules": None,
    },
    {
        "dataset_id": "kaggle_ab_data",
        "label": "Kaggle Benchmark (cleaned)",
        "source_type": "external_benchmark_data",
        "path": PROJECT_ROOT / "data" / "external" / "kaggle_ab_data.csv",
        "metrics": ["converted"],
        "primary_metric": "converted",
        "business_question": "Does the new landing page (treatment) improve conversion vs. the old page (control)?",
        "clean_rules": {
            "user_id_col": "user_id",
            "assignment_map": {"control": "old_page", "treatment": "new_page"},
            "assignment_target_col": "landing_page",
        },
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def power_analysis(n_per_variant: int, baseline_rate: float, alpha: float = 0.05) -> dict:
    """
    Compute minimum detectable effect (MDE) and achieved power
    for a two-proportion z-test at the given sample size.
    """
    z_alpha = 1.959964  # z_{1-alpha/2} for two-sided alpha=0.05
    z_beta_80 = 0.841621  # z_{0.80} for 80% power

    # MDE: smallest absolute lift detectable at 80% power
    p = baseline_rate
    se = math.sqrt(2 * p * (1 - p) / n_per_variant)
    mde_abs = (z_alpha + z_beta_80) * se
    mde_rel = mde_abs / p if p > 0 else float("nan")

    return {
        "n_per_variant": n_per_variant,
        "baseline_rate": round(baseline_rate, 4),
        "mde_absolute": round(mde_abs, 4),
        "mde_relative_pct": round(mde_rel * 100, 2),
        "power_target": 0.80,
    }


def run_all_metrics(dataset: dict) -> list[dict]:
    """Run statistical analysis for every metric listed in the dataset config."""
    analyzer = StatisticalAnalyzer(alpha=0.05)
    df = pd.read_csv(dataset["path"])

    # Apply cleaning if needed (same logic as run_pipeline)
    if dataset["clean_rules"]:
        from scripts.run_pipeline import clean_public_dataset, detect_variant_column
        variant_col = detect_variant_column(df)
        df, _ = clean_public_dataset(df, variant_col=variant_col, **dataset["clean_rules"])
    else:
        from scripts.run_pipeline import detect_variant_column
        variant_col = detect_variant_column(df)

    metric_rows = []
    for metric in dataset["metrics"]:
        if metric not in df.columns:
            continue
        try:
            result = analyzer.select_and_run_test(df, metric, variant_col)
            metric_rows.append({
                "dataset_id": dataset["dataset_id"],
                "label": dataset["label"],
                "source_type": dataset["source_type"],
                "metric": metric,
                "is_primary": metric == dataset["primary_metric"],
                "test_type": result["test_type"],
                "p_value": result.get("p_value"),
                "significant_raw": result.get("significant"),
                "absolute_difference": result.get(
                    "absolute_difference",
                    result.get("mean_difference", result.get("median_difference")),
                ),
                "relative_lift_pct": (
                    round(result.get("relative_lift", 0) * 100, 2)
                    if result.get("relative_lift") is not None
                    else None
                ),
                "interpretation": result.get("interpretation"),
            })
        except Exception as exc:
            print(f"  WARNING: could not analyze {metric}: {exc}")

    # Holm-Bonferroni correction across all metrics in this experiment
    p_values = [r["p_value"] for r in metric_rows if r["p_value"] is not None]
    if len(p_values) > 1:
        corrected = analyzer.multiple_testing_correction(p_values, method="holm")
        for i, row in enumerate(metric_rows):
            if row["p_value"] is not None:
                row["significant_corrected"] = bool(corrected["reject_null"][i])
            else:
                row["significant_corrected"] = False
    else:
        for row in metric_rows:
            row["significant_corrected"] = row.get("significant_raw", False)

    return metric_rows


def build_primary_summary_row(dataset: dict, analysis: dict, metric_rows: list[dict]) -> dict:
    """Build one summary row for the primary metric, enriched with power analysis."""
    result = analysis["results"]
    validation = analysis["validation"]

    n_per_variant = validation.get("min_sample_per_variant") or 0
    baseline_rate = result.get("rate_A", result.get("mean_A", 0)) or 0

    # Only run proportion-style power analysis for binary metrics
    power = {}
    if result.get("metric_type") == "binary" and n_per_variant > 0 and 0 < baseline_rate < 1:
        power = power_analysis(n_per_variant, baseline_rate)

    sig_count_raw = sum(1 for r in metric_rows if r.get("significant_raw"))
    sig_count_corrected = sum(1 for r in metric_rows if r.get("significant_corrected"))

    return {
        "dataset_id": dataset["dataset_id"],
        "label": dataset["label"],
        "source_type": dataset["source_type"],
        "business_question": dataset["business_question"],
        "primary_metric": dataset["primary_metric"],
        "metrics_tested": len(metric_rows),
        "significant_raw": sig_count_raw,
        "significant_corrected": sig_count_corrected,
        "primary_p_value": result.get("p_value"),
        "primary_significant": result.get("significant"),
        "primary_absolute_diff": result.get(
            "absolute_difference",
            result.get("mean_difference", result.get("median_difference")),
        ),
        "primary_relative_lift_pct": (
            round(result.get("relative_lift", 0) * 100, 2)
            if result.get("relative_lift") is not None else None
        ),
        "mde_absolute": power.get("mde_absolute"),
        "mde_relative_pct": power.get("mde_relative_pct"),
        "n_per_variant": n_per_variant,
        "validation_status": validation["status"],
        "detectable_mde_pct": validation.get("detectable_mde_pct"),
        "data_cleaned": dataset["clean_rules"] is not None,
        "interpretation": result.get("interpretation"),
        "cleaning_summary": analysis.get("cleaning_summary"),
        "validation_report": analysis["validation_report"],
        "results_path": analysis["results_path"],
        "distribution_plot": analysis["distribution_plot"],
        "bar_plot": analysis["bar_plot"],
    }


def write_markdown_report(
    summary_df: pd.DataFrame,
    metric_df: pd.DataFrame,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    internal = summary_df[summary_df["source_type"] == "internal_decision_data"]
    external = summary_df[summary_df["source_type"] == "external_benchmark_data"]

    def sig_icon(val) -> str:
        return "Yes" if val else "No"

    with output_path.open("w", encoding="utf-8") as f:
        f.write("# A/B Testing Project — Batch Analysis Report\n\n")
        f.write("Generated by `scripts/run_batch_analysis.py`.\n\n")

        # ---- Quick summary table ----
        f.write("## At a Glance\n\n")
        f.write("| Experiment | Metrics tested | Sig (raw) | Sig (corrected) | Primary result | MDE (relative) |\n")
        f.write("|---|---|---|---|---|---|\n")
        for _, row in summary_df.iterrows():
            mde = f"{row['mde_relative_pct']}%" if pd.notna(row.get("mde_relative_pct")) else "n/a"
            primary_sig = sig_icon(row["primary_significant"])
            f.write(
                f"| {row['label']} | {row['metrics_tested']} "
                f"| {row['significant_raw']} | {row['significant_corrected']} "
                f"| {primary_sig} | {mde} |\n"
            )
        f.write("\n")

        # ---- Internal experiments ----
        f.write("## Internal Business Experiments\n\n")
        for _, row in internal.iterrows():
            f.write(f"### {row['label']}\n\n")
            f.write(f"**Business question:** {row['business_question']}\n\n")

            # All metrics table
            exp_metrics = metric_df[metric_df["dataset_id"] == row["dataset_id"]]
            if not exp_metrics.empty:
                f.write("| Metric | Test | p-value | Sig (raw) | Sig (corrected) | Lift |\n")
                f.write("|---|---|---|---|---|---|\n")
                for _, mr in exp_metrics.iterrows():
                    lift = f"{mr['relative_lift_pct']}%" if pd.notna(mr.get("relative_lift_pct")) else "—"
                    pval = f"{mr['p_value']:.4f}" if pd.notna(mr.get("p_value")) else "—"
                    f.write(
                        f"| {'**' if mr['is_primary'] else ''}{mr['metric']}{'**' if mr['is_primary'] else ''} "
                        f"| {mr['test_type']} | {pval} "
                        f"| {sig_icon(mr['significant_raw'])} "
                        f"| {sig_icon(mr['significant_corrected'])} "
                        f"| {lift} |\n"
                    )
                f.write("\n")

            # Power/MDE summary
            if pd.notna(row.get("mde_absolute")):
                f.write(
                    f"**Power analysis (primary metric):** n={row['n_per_variant']:,} per variant. "
                    f"Minimum detectable effect = {row['mde_absolute']} absolute / {row['mde_relative_pct']}% relative "
                    f"(at 80% power, α=0.05).\n\n"
                )

            f.write(f"**Validation:** {row['validation_status']}\n\n")
            f.write(f"**Interpretation:** {row['interpretation']}\n\n")
            f.write("---\n\n")

        # ---- External benchmark ----
        f.write("## External Benchmark Data\n\n")
        for _, row in external.iterrows():
            f.write(f"### {row['label']}\n\n")
            f.write(f"**Business question:** {row['business_question']}\n\n")
            if row.get("data_cleaned") and row.get("cleaning_summary"):
                cs = row["cleaning_summary"]
                f.write(
                    f"**Data cleaning applied:** removed {cs.get('duplicate_users_removed', 0)} duplicate users "
                    f"and {cs.get('assignment_mismatches_removed', 0)} assignment mismatches. "
                    f"Clean sample: {cs.get('clean_rows', 0):,} rows.\n\n"
                )

            exp_metrics = metric_df[metric_df["dataset_id"] == row["dataset_id"]]
            if not exp_metrics.empty:
                f.write("| Metric | Test | p-value | Sig (raw) | Sig (corrected) | Lift |\n")
                f.write("|---|---|---|---|---|---|\n")
                for _, mr in exp_metrics.iterrows():
                    lift = f"{mr['relative_lift_pct']}%" if pd.notna(mr.get("relative_lift_pct")) else "—"
                    pval = f"{mr['p_value']:.4f}" if pd.notna(mr.get("p_value")) else "—"
                    f.write(
                        f"| {mr['metric']} | {mr['test_type']} | {pval} "
                        f"| {sig_icon(mr['significant_raw'])} "
                        f"| {sig_icon(mr['significant_corrected'])} "
                        f"| {lift} |\n"
                    )
                f.write("\n")

            if pd.notna(row.get("mde_absolute")):
                f.write(
                    f"**Power analysis:** n={row['n_per_variant']:,} per variant. "
                    f"MDE = {row['mde_absolute']} absolute / {row['mde_relative_pct']}% relative.\n\n"
                )

            f.write(f"**Validation:** {row['validation_status']}\n\n")
            f.write(f"**Interpretation:** {row['interpretation']}\n\n")
            f.write("---\n\n")

        # ---- Comparison rule ----
        f.write("## Cross-Source Comparison Rule\n\n")
        f.write(
            "Use internal and external datasets **together** to evaluate methodology robustness "
            "and demonstrate pipeline portability. Do **not** directly compare effect sizes or winners "
            "across sources — different populations, products, and assignment strategies make that comparison invalid.\n"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    summary_rows = []
    all_metric_rows = []

    for dataset in DATASETS:
        print(f"\n{'=' * 80}")
        print(f"Analyzing: {dataset['label']}")
        print(f"{'=' * 80}")

        # Primary-metric analysis (also handles validation + plots)
        analysis = analyze_dataset(
            dataset["path"],
            metric_override=dataset["primary_metric"],
            clean_rules=dataset["clean_rules"],
        )

        # Multi-metric analysis (all listed metrics, Holm-corrected)
        print(f"  Running all {len(dataset['metrics'])} metrics...")
        metric_rows = run_all_metrics(dataset)
        all_metric_rows.extend(metric_rows)

        summary_rows.append(build_primary_summary_row(dataset, analysis, metric_rows))

    summary_df = pd.DataFrame(summary_rows)
    metric_df = pd.DataFrame(all_metric_rows)

    results_dir = PROJECT_ROOT / "reports" / "statistical_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    summary_df.to_csv(results_dir / "batch_summary.csv", index=False)
    metric_df.to_csv(results_dir / "batch_all_metrics.csv", index=False)

    report_output = PROJECT_ROOT / "docs" / "BATCH_ANALYSIS_REPORT.md"
    write_markdown_report(summary_df, metric_df, report_output)

    print(f"\nBatch summary  -> {results_dir / 'batch_summary.csv'}")
    print(f"All metrics    -> {results_dir / 'batch_all_metrics.csv'}")
    print(f"Markdown report-> {report_output}")


if __name__ == "__main__":
    main()