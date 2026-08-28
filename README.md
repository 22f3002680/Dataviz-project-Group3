# Dataviz-project-Group3

## Project Scope

See `docs/project_scope.md` for the business goal, final analysis questions,
core metrics, planned visuals, and dashboard/report mapping.

## Dashboard

Live dashboard: https://22f3002680.github.io/Dataviz-project-Group3/

The dashboard is a static GitHub Pages site in `dashboard/`.

## Final Deliverables

- [Final technical report (Google Docs)](https://docs.google.com/document/d/10zrbGT52cCArMm5L8SqdSxQ9qCn2YxASzopuL5tOMks/edit)
- [Final technical report (PDF)](docs/final_report.pdf)
- [Final technical report source](docs/final_report.md)
- [Interactive dashboard](https://22f3002680.github.io/Dataviz-project-Group3/)
- [Supporting analysis reports](https://22f3002680.github.io/Dataviz-project-Group3/reports/index.html)

The report includes placeholders for team names, roll numbers, roles, and
individual contribution logs. Complete these fields before submission.

## Rebuild Dashboard Data

The dashboard reads precomputed data from `dashboard/data.js`. Rebuild it from the
committed workbook with:

```bash
python3 scripts/build_dashboard_data.py
```

For faster local reruns from extracted CSV files:

```bash
python3 scripts/build_dashboard_data.py --source-dir /path/to/raw_csvs
```

See `docs/data_pipeline.md` for the cleaning, joins, and derived field definitions.
See `docs/metric_dictionary.md` for metric definitions and validation rules.
See `docs/data_quality_audit.md` for schema joins, quality findings, and
cleaning decisions.
See `docs/eda/order_journey_eda.md` for the baseline order-journey EDA and
reusable visuals.
See `docs/eda/delivery_delay_impact.md` for the delivery delay and review
impact analysis.
See `docs/eda/marketing_funnel_analysis.md` for the reproducible MQL conversion,
seller linkage, and equal-window post-acquisition analysis.
See `docs/dashboard_qa.md` for the dashboard viewport, interaction,
accessibility, and deployment acceptance checks.

Live reports: https://22f3002680.github.io/Dataviz-project-Group3/reports/index.html

Rebuild and validate the Issue #10 report with:

```bash
python3 scripts/build_marketing_funnel_analysis.py
python3 scripts/build_live_report_pages.py
python3 scripts/validate_marketing_funnel_analysis.py
```
