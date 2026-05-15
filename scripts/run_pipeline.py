from pathlib import Path
import sys
from typing import Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from scripts.statistical_analysis import StatisticalAnalyzer
from scripts.validation import ExperimentValidator


def select_covariates(df: pd.DataFrame, variant_col: str) -> list[str]:
	preferred_covariates = ["device_type", "browser", "region"]
	return [column for column in preferred_covariates if column in df.columns and column != variant_col]


def select_date_column(df: pd.DataFrame) -> Optional[str]:
	if "timestamp" not in df.columns:
		return None
	timestamp_text = df["timestamp"].astype(str)
	has_calendar_date = timestamp_text.str.contains(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}", regex=True).any()
	return "timestamp" if has_calendar_date else None


def detect_variant_column(df: pd.DataFrame) -> str:
	variant_candidates = ["variant", "group", "arm", "experiment_group"]
	variant_col = next((column for column in variant_candidates if column in df.columns), None)
	if variant_col is None:
		raise ValueError(
			"No variant column found. Expected one of: "
			f"{variant_candidates}. Found columns: {list(df.columns)}"
		)
	return variant_col


def detect_metric_column(df: pd.DataFrame, variant_col: str, metric_override: Optional[str] = None) -> str:
	if metric_override:
		if metric_override not in df.columns:
			raise ValueError(f"Metric '{metric_override}' not found in dataset columns: {list(df.columns)}")
		return metric_override

	candidate_metrics = ["conversion_rate", "converted", "added_to_cart", "revenue"]
	metric = next((column for column in candidate_metrics if column in df.columns), None)
	if metric is not None:
		return metric

	numeric_cols = [
		column for column in df.columns
		if column != variant_col and pd.api.types.is_numeric_dtype(df[column])
	]
	if not numeric_cols:
		raise ValueError("No numeric metric column found for analysis.")
	return numeric_cols[0]


def save_validation_report(results: dict, output_path: Path, dataset_name: str) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8") as report_file:
		report_file.write(f"VALIDATION REPORT: {dataset_name}\n")
		report_file.write("=" * 80 + "\n\n")
		for section, values in results.items():
			report_file.write(f"[{section}]\n")
			if isinstance(values, dict):
				for key, value in values.items():
					report_file.write(f"- {key}: {value}\n")
			else:
				report_file.write(f"- {values}\n")
			report_file.write("\n")


def clean_public_dataset(
	df: pd.DataFrame,
	variant_col: str,
	user_id_col: Optional[str] = None,
	assignment_map: Optional[dict] = None,
	assignment_target_col: Optional[str] = None,
) -> tuple[pd.DataFrame, dict]:
	"""
	Remove rows that are known to corrupt A/B inference in public/tutorial datasets:
	  1. Duplicate user IDs (keep first occurrence).
	  2. Variant-assignment mismatches (e.g. group='control' but landing_page='new_page').

	Returns the cleaned DataFrame and a summary dict of what was removed.
	"""
	original_len = len(df)
	removed = {}

	# 1. Dedup by user
	if user_id_col and user_id_col in df.columns:
		before = len(df)
		df = df.drop_duplicates(subset=[user_id_col], keep="first").copy()
		removed["duplicate_users_removed"] = before - len(df)

	# 2. Assignment mismatch
	if assignment_map and assignment_target_col and assignment_target_col in df.columns:
		valid_assignments = df[variant_col].map(assignment_map)
		mismatch_mask = valid_assignments.notna() & df[assignment_target_col].notna() & (df[assignment_target_col] != valid_assignments)
		before = len(df)
		df = df[~mismatch_mask].copy()
		removed["assignment_mismatches_removed"] = before - len(df)

	removed["original_rows"] = original_len
	removed["clean_rows"] = len(df)
	return df, removed


def summarize_validation(validation_results: dict) -> dict:
	srm_passed = validation_results.get("srm", {}).get("passed", True)
	integrity_passed = validation_results.get("data_integrity", {}).get("passed", True)
	all_passed = all(section.get("passed", True) for section in validation_results.values() if isinstance(section, dict))
	if srm_passed and integrity_passed and all_passed:
		status = "passed"
	elif srm_passed and integrity_passed:
		status = "passed_with_warnings"
	else:
		status = "failed"

	issues = validation_results.get("data_integrity", {}).get("issues", [])
	sample_size = validation_results.get("sample_size", {})
	return {
		"status": status,
		"issue_count": len(issues),
		"issues": issues,
		"min_sample_per_variant": sample_size.get("min_sample"),
		"detectable_mde_pct": round(sample_size.get("detectable_mde", float("nan")) * 100, 2),
		"sample_size_passed": sample_size.get("passed", True),
	}


def analyze_dataset(
	data_path: Path,
	metric_override: Optional[str] = None,
	alpha: float = 0.05,
	clean_rules: Optional[dict] = None,
) -> dict:
	"""
	Run validation + statistical analysis for one dataset.

	Parameters
	----------
	data_path : Path
	metric_override : str, optional
	    Force a specific metric column.
	alpha : float
	    Significance level (default 0.05).
	clean_rules : dict, optional
	    If provided, public-dataset cleaning is applied before analysis.
	    Keys: ``user_id_col``, ``assignment_map``, ``assignment_target_col``.
	    Example for Kaggle dataset::

	        clean_rules={
	            "user_id_col": "user_id",
	            "assignment_map": {"control": "old_page", "treatment": "new_page"},
	            "assignment_target_col": "landing_page",
	        }
	"""
	data_path = data_path.resolve()
	df = pd.read_csv(data_path)
	variant_col = detect_variant_column(df)
	metric = detect_metric_column(df, variant_col, metric_override)

	cleaning_summary: Optional[dict] = None
	if clean_rules:
		df, cleaning_summary = clean_public_dataset(
			df,
			variant_col=variant_col,
			user_id_col=clean_rules.get("user_id_col"),
			assignment_map=clean_rules.get("assignment_map"),
			assignment_target_col=clean_rules.get("assignment_target_col"),
		)
		print(f"Data cleaning applied: {cleaning_summary}")

	analyzer = StatisticalAnalyzer(alpha=alpha)
	validator = ExperimentValidator()

	covariates = select_covariates(df, variant_col)
	date_col = select_date_column(df)

	print("Running validation...")
	validation_results = validator.run_all_validations(
		df=df,
		variant_col=variant_col,
		covariates=covariates if covariates else None,
		date_col=date_col,
	)

	validation_dir = PROJECT_ROOT / "reports" / "validation_reports"
	validation_path = validation_dir / f"{data_path.stem}_validation_report.txt"
	save_validation_report(validation_results, validation_path, data_path.name)
	print(f"Validation report saved to {validation_path}")

	results = analyzer.select_and_run_test(df, metric, variant_col)
	print("Statistical Analysis Results:")
	print(results)

	print("Generating visualizations...")
	fig_dir = PROJECT_ROOT / "reports" / "figures"
	fig_dir.mkdir(parents=True, exist_ok=True)
	distribution_plot = fig_dir / f"{data_path.stem}_{metric}_distribution.png"
	bar_plot = fig_dir / f"{data_path.stem}_{metric}_bar.png"
	analyzer.plot_metric_distribution(df, metric, variant_col, save_path=str(distribution_plot), show=False)
	analyzer.plot_metric_bar_chart(df, metric, variant_col, save_path=str(bar_plot), show=False)

	results_dir = PROJECT_ROOT / "reports" / "statistical_results"
	results_dir.mkdir(parents=True, exist_ok=True)
	results_path = results_dir / f"{data_path.stem}_results.csv"
	pd.DataFrame([results]).to_csv(results_path, index=False)
	print(f"Results saved to {results_path}")
	print(f"Distribution plot saved to {distribution_plot}")
	print(f"Bar chart saved to {bar_plot}")

	return {
		"data_path": str(data_path),
		"metric": metric,
		"variant_col": variant_col,
		"cleaning_summary": cleaning_summary,
		"validation": summarize_validation(validation_results),
		"validation_report": str(validation_path),
		"results": results,
		"results_path": str(results_path),
		"distribution_plot": str(distribution_plot),
		"bar_plot": str(bar_plot),
	}


def main() -> None:
	default_path = PROJECT_ROOT / "data" / "test1_menu.csv"
	data_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default_path
	metric_override = sys.argv[2] if len(sys.argv) > 2 else None
	analyze_dataset(data_path, metric_override=metric_override)


if __name__ == "__main__":
	main()