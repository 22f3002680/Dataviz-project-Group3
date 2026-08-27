# Dataviz Project - Group 3

End-to-end exploratory analysis and dashboard for a Brazilian e-commerce
marketplace dataset. The project studies order growth, delivery reliability,
customer reviews, product categories, seller performance, and regional demand
to identify growth opportunities that do not compromise customer satisfaction.

## Project Links

- [Live dashboard](https://22f3002680.github.io/Dataviz-project-Group3/)
- [Live analysis reports](https://22f3002680.github.io/Dataviz-project-Group3/reports/index.html)
- [Implementation branch](https://github.com/22f3002680/Dataviz-project-Group3/tree/project-materials)
- [Project scope](https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/docs/project_scope.md)
- [Data pipeline documentation](https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/docs/data_pipeline.md)
- [Metric dictionary](https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/docs/metric_dictionary.md)
- [Data quality audit](https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/docs/data_quality_audit.md)
- [GitHub issues](https://github.com/22f3002680/Dataviz-project-Group3/issues)

> The default `main` branch provides this project overview. The datasets,
> notebooks, dashboard source, scripts, and detailed documentation are maintained
> on the [`project-materials`](https://github.com/22f3002680/Dataviz-project-Group3/tree/project-materials)
> branch and published to GitHub Pages after reviewed pull requests are merged.

## Business Objective

The marketplace needs to grow order value and seller activity while maintaining
delivery reliability and customer satisfaction. The analysis addresses five
connected questions:

1. How do order volume, status, and customer reviews change over time?
2. How strongly are delivery delays associated with poor reviews?
3. Which product categories combine demand, revenue, growth, and manageable risk?
4. Which sellers need intervention, and which provide useful benchmarks?
5. Which states offer attractive demand while requiring delivery improvement?

The work reports associations in the observed data. It does not interpret them
as causal effects without a suitable experiment or causal design.

## Dataset

The committed workbook is
[`Dataviz_proj_all_datasets.xlsx`](https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/Dataviz_proj_all_datasets.xlsx).
It contains the marketplace tables used by the reproducible pipeline:

| Data area | Main contents |
| --- | --- |
| Orders | Purchase, approval, carrier, delivery, estimated delivery, and status fields |
| Order items | Products, sellers, prices, freight values, and shipping deadlines |
| Customers | Customer identifiers, ZIP prefixes, cities, and states |
| Sellers | Seller identifiers and locations |
| Products | Category, dimensions, weight, and descriptive attributes |
| Reviews | Review score, title, message, and response timestamps |
| Category translation | Portuguese-to-English product category mapping |
| Marketing funnel | Qualified leads and closed-deal attributes for optional funnel analysis |

The source data is relational. Order-level measures and item-level measures are
kept separate to prevent multi-item orders from inflating order KPIs.

## Repository Structure

The implementation branch is organized as follows:

```text
.
|-- dashboard/
|   |-- index.html                 # Main interactive dashboard
|   |-- app.js                     # Filtering, rendering, and UI behavior
|   |-- styles.css                 # Responsive dashboard styling
|   |-- data.js                    # Deterministic precomputed dashboard data
|   `-- reports/                   # Published HTML reports and report assets
|-- docs/
|   |-- project_scope.md           # Business questions and deliverable scope
|   |-- data_pipeline.md           # Cleaning, joins, and derived fields
|   |-- metric_dictionary.md       # Canonical KPI definitions and grain
|   |-- data_quality_audit.md      # Schema and anomaly audit
|   `-- eda/                       # Reproducible EDA narratives and figures
|-- scripts/
|   |-- build_dashboard_data.py    # Workbook/CSV to dashboard data pipeline
|   |-- validate_dashboard_metrics.py
|   |-- build_order_journey_eda.py
|   |-- build_delivery_delay_analysis.py
|   |-- build_regional_analysis.py
|   `-- build_live_report_pages.py
|-- DVD_project_EDA1.ipynb         # Initial team EDA notebook
|-- EDA order data set.ipynb       # Order-focused exploratory notebook
|-- issue7_eda.ipynb               # Product category analysis
|-- Issue_8_Seller_Analysis_Sourish.ipynb
|-- Dataviz_proj_all_datasets.xlsx
`-- .github/workflows/deploy-pages.yml
```

## Analysis Completed

### 1. Scope and metric design

The team defined the business objective, analysis questions, dashboard mapping,
data grain, KPI rules, and interpretation boundaries. The metric dictionary is
the source of truth when notebooks and comments disagree.

- [Issue #1](https://github.com/22f3002680/Dataviz-project-Group3/issues/1)
- [Pull request #18](https://github.com/22f3002680/Dataviz-project-Group3/pull/18)

### 2. Data quality audit

The audit verifies table relationships, missingness, timestamp consistency,
category translation coverage, and the construction of the item-level master
table. Important findings include:

- 278 unmatched customer geolocation ZIP prefixes and 7 unmatched seller ZIP prefixes.
- 2 missing category translations affecting 13 product rows.
- 166 carrier timestamps earlier than purchase time; 160 differ by no more than
  two hours, while 6 require stronger anomaly handling.
- The item-level analytical table contains 112,650 rows.

Invalid event sequences are flagged rather than silently overwritten. Analyses
that require elapsed delivery time exclude invalid timestamps from that metric
while preserving usable fields from the row.

- [Issue #2](https://github.com/22f3002680/Dataviz-project-Group3/issues/2)
- [Pull request #20](https://github.com/22f3002680/Dataviz-project-Group3/pull/20)

### 3. Reproducible data pipeline

`scripts/build_dashboard_data.py` reads the committed workbook or an extracted
CSV directory, validates required columns, coerces numeric and date fields,
applies category translations, computes the agreed metrics, sorts output
deterministically, and writes `dashboard/data.js`.

The generated file exposes `window.DVD_DASHBOARD_DATA`, allowing the published
site to remain a static, dependency-free GitHub Pages application.

- [Issue #3](https://github.com/22f3002680/Dataviz-project-Group3/issues/3)
- [Pull request #13](https://github.com/22f3002680/Dataviz-project-Group3/pull/13)

### 4. Metric validation

`scripts/validate_dashboard_metrics.py` independently recalculates dashboard
outputs and checks summary counts, distributions, delivery metrics, product and
seller segmentation, and regional metrics. The current suite passes 35 checks.

- [Issue #4](https://github.com/22f3002680/Dataviz-project-Group3/issues/4)
- [Pull request #14](https://github.com/22f3002680/Dataviz-project-Group3/pull/14)

### 5. Baseline order journey

The baseline EDA covers order volume, status, weekday patterns, reviews, and
delivery outcomes. Current headline results are:

- 99,441 orders and 112,650 order items.
- 96,096 distinct customers, 3,095 sellers, and 32,951 products.
- Average review score of 4.09.
- 77.1% high reviews and 14.7% low reviews.
- 97.0% of orders have delivered status.

[Open the order journey report](https://22f3002680.github.io/Dataviz-project-Group3/reports/order-journey.html)

- [Issue #5](https://github.com/22f3002680/Dataviz-project-Group3/issues/5)
- [Pull request #21](https://github.com/22f3002680/Dataviz-project-Group3/pull/21)

### 6. Delivery delay impact

Delivery delay is strongly associated with customer dissatisfaction:

- Late deliveries have a 52.9% low-review rate versus 9.1% for on-time or early deliveries.
- The observed low-review rate is approximately 5.8 times higher for late orders.
- Orders delivered at least 22 days late average 1.77 stars and have a 73.6% low-review rate.
- Same-state orders average 7.93 delivery days versus 15.05 for cross-state orders.

[Open the delivery impact report](https://22f3002680.github.io/Dataviz-project-Group3/reports/delivery-impact.html)

- [Issue #6](https://github.com/22f3002680/Dataviz-project-Group3/issues/6)
- [Pull request #22](https://github.com/22f3002680/Dataviz-project-Group3/pull/22)

### 7. Product category analysis

The product analysis compares categories by item demand, revenue, growth,
delivery performance, and review risk. Review fixes corrected order/item
denominators so that category-level delivery KPIs are comparable.

[Open the product analysis report](https://22f3002680.github.io/Dataviz-project-Group3/reports/product-analysis.html)

- [Issue #7](https://github.com/22f3002680/Dataviz-project-Group3/issues/7)
- [Pull request #16](https://github.com/22f3002680/Dataviz-project-Group3/pull/16)
- [Analysis notebook](https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/issue7_eda.ipynb)

### 8. Seller performance analysis

Seller performance is segmented using delivered volume, late-delivery rate, and
low-review rate. After applying the corrected eligible seller population, the
analysis identifies 85 intervention candidates and 390 healthy benchmarks.

[Open the seller analysis report](https://22f3002680.github.io/Dataviz-project-Group3/reports/seller-analysis.html)

- [Issue #8](https://github.com/22f3002680/Dataviz-project-Group3/issues/8)
- [Pull request #17](https://github.com/22f3002680/Dataviz-project-Group3/pull/17)
- [Analysis notebook](https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/Issue_8_Seller_Analysis_Sourish.ipynb)

### 9. Regional demand and delivery risk

The regional analysis uses item-level revenue and delivered-item risk
denominators. It finds that Sao Paulo, Rio de Janeiro, and Minas Gerais account
for 63.4% of state-level revenue. Maranhao, Piaui, and Ceara are high-risk states
among states meeting the 500 delivered-item minimum. Rio de Janeiro and Bahia
combine high demand with elevated delivery risk and are priority candidates for
operational investigation.

[Open the regional analysis report](https://22f3002680.github.io/Dataviz-project-Group3/reports/regional-analysis.html)

- [Issue #9](https://github.com/22f3002680/Dataviz-project-Group3/issues/9)
- [Pull request #23](https://github.com/22f3002680/Dataviz-project-Group3/pull/23)

## Metric Rules

The most important rules used throughout the project are:

- A low review is a review score less than or equal to 2.
- A delivered order has `order_status == delivered` and a customer delivery timestamp.
- A late delivery has an actual delivery date after its estimated delivery date.
- Delivery averages and late rates exclude undelivered orders.
- Order counts, review rates, and delivery KPIs use order-level denominators.
- Revenue, freight, seller, category, and regional item metrics use item-level rows.
- Minimum-volume thresholds are applied before ranking seller and regional risk.

See the complete
[metric dictionary](https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/docs/metric_dictionary.md)
for exact definitions and validation rules.

## Reproduce the Project

Clone the repository and check out the implementation branch:

```bash
git clone https://github.com/22f3002680/Dataviz-project-Group3.git
cd Dataviz-project-Group3
git switch project-materials
```

Install the Python packages used by the scripts and notebooks in your preferred
environment. Then run the build in this order:

```bash
python3 scripts/build_dashboard_data.py
python3 scripts/build_order_journey_eda.py
python3 scripts/build_delivery_delay_analysis.py
python3 scripts/build_regional_analysis.py
python3 scripts/build_live_report_pages.py
python3 scripts/validate_dashboard_metrics.py
node --check dashboard/app.js
```

To build dashboard data from extracted CSV files instead of the workbook:

```bash
python3 scripts/build_dashboard_data.py --source-dir /path/to/raw_csvs
```

For a local preview, serve the repository root and open the dashboard directory:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000/dashboard/`.

## Deployment

The dashboard uses GitHub Pages and does not require a paid application server.
The deployment workflow is:

1. Work is completed on a feature branch.
2. A pull request is reviewed and merged into `project-materials`.
3. `.github/workflows/deploy-pages.yml` copies the static `dashboard/` directory
   to the `gh-pages` branch.
4. GitHub Pages publishes that branch at the live dashboard URL.

Only files inside `dashboard/` are published. The report builder converts the
analysis outputs into pages under `dashboard/reports/` before deployment.

- [Deployment workflow](https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/.github/workflows/deploy-pages.yml)
- [Deployment fix PR #19](https://github.com/22f3002680/Dataviz-project-Group3/pull/19)
- [Live reports PR #24](https://github.com/22f3002680/Dataviz-project-Group3/pull/24)

## Remaining Work

The core analyses through Issue #9 are implemented. The remaining tracked work is:

| Issue | Work item | Status |
| --- | --- | --- |
| [#10](https://github.com/22f3002680/Dataviz-project-Group3/issues/10) | Marketing funnel analysis | Open |
| [#11](https://github.com/22f3002680/Dataviz-project-Group3/issues/11) | Dashboard integration, polish, and QA | Open |
| [#12](https://github.com/22f3002680/Dataviz-project-Group3/issues/12) | Final report, presentation, and contribution log | Open |

Issues #7 and #8 may still appear open in GitHub even though their reviewed
implementations were merged. Their linked pull requests and current dashboard
outputs are the authoritative implementation record.

## Contribution Workflow

1. Choose or receive an assigned GitHub issue.
2. Create a feature branch from `project-materials`.
3. Keep analysis logic reproducible in a notebook or script.
4. Apply the metric dictionary and document any new cleaning decision.
5. Run metric validation and relevant syntax checks.
6. Open a pull request that links the issue and summarizes findings.
7. Resolve review comments before merging.

Do not commit credentials, personal access tokens, generated caches, or local
environment files. GitHub credentials should be managed through `gh auth login`
or an operating-system credential manager.
