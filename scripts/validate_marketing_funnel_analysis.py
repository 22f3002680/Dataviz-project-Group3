"""Validate Issue #10 source metrics and generated report artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from build_marketing_funnel_analysis import (
    DEFAULT_WORKBOOK,
    POST_WIN_DAYS,
    ROOT_DIR,
    UNKNOWN_ORIGIN,
    analyze,
    load_tables,
    validate_analysis,
)


REPORT_PATH = ROOT_DIR / "docs" / "eda" / "marketing_funnel_analysis.md"
CHART_PATH = ROOT_DIR / "docs" / "eda" / "marketing_funnel_conversion_by_origin.png"
LIVE_REPORT_PATH = ROOT_DIR / "dashboard" / "reports" / "marketing-funnel.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the generated Issue #10 marketing-funnel analysis."
    )
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--source-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = analyze(load_tables(args.workbook, args.source_dir))
    summary = result["summary"]
    events = result["events"]
    by_origin = result["by_origin"]
    checks = validate_analysis(result)

    def check(condition: bool, label: str) -> None:
        if not condition:
            raise AssertionError(f"Marketing-funnel validation failed: {label}")
        checks.append(label)

    check(summary["mqls"] == 8000, "committed dataset has 8,000 MQLs")
    check(summary["closed_deals"] == 842, "committed dataset has 842 closed deals")
    check(
        summary["overall_conversion_rate_pct"] == 10.53,
        "overall observed conversion uses half-up rounding",
    )
    check(summary["linked_sellers"] == 380, "marketplace linkage count is 380")
    check(
        UNKNOWN_ORIGIN in set(by_origin["origin"]),
        "missing and literal unknown origins use the canonical label",
    )
    check(
        not set(by_origin["origin"]).intersection({"unknown", "", None}),
        "raw unknown labels do not leak into output",
    )
    check(
        events["order_purchase_timestamp"].ge(events["won_date"]).all(),
        "seller events do not precede won date",
    )
    check(
        events["order_purchase_timestamp"]
        .lt(events["won_date"] + pd.Timedelta(days=POST_WIN_DAYS))
        .all(),
        "seller events stay inside the fixed post-win window",
    )
    check(REPORT_PATH.exists(), "generated Markdown report exists")
    report = REPORT_PATH.read_text(encoding="utf-8")
    normalized_report = " ".join(report.split())
    check(
        "Observed conversion rate | 10.53%" in normalized_report,
        "report contains validated conversion",
    )
    check(
        "380 of 842 closed sellers" in normalized_report,
        "report contains validated linkage",
    )
    check(CHART_PATH.exists() and CHART_PATH.stat().st_size > 10_000, "chart is non-empty")
    check(LIVE_REPORT_PATH.exists(), "published report page exists")
    live_report = LIVE_REPORT_PATH.read_text(encoding="utf-8")
    check(
        "Marketing Funnel and Seller Acquisition Analysis" in live_report,
        "published report contains the analysis title",
    )
    check(
        "assets/marketing_funnel_conversion_by_origin.png" in live_report,
        "published report references the generated chart",
    )

    print(f"Passed {len(checks)} marketing-funnel checks.")


if __name__ == "__main__":
    main()
