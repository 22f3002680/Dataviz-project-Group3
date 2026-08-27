# Dataviz-project-Group3

## Project Scope

See `docs/project_scope.md` for the business goal, final analysis questions,
core metrics, planned visuals, and dashboard/report mapping.

## Dashboard

Live dashboard: https://22f3002680.github.io/Dataviz-project-Group3/

The dashboard is a static GitHub Pages site in `dashboard/`.

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
