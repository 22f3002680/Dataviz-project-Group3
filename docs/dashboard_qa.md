# Dashboard QA Record

Issue #11 covers final usability, accessibility, responsive-layout, and GitHub
Pages checks for the interactive dashboard.

## Surfaces Reviewed

- Overview
- Delivery
- Categories
- Regions
- Sellers
- Growth and marketing funnel
- Reports and methods index

## Viewports

| Profile | Viewport | Result |
| --- | ---: | --- |
| Desktop | 1440 x 1000 | Passed |
| Tablet | 768 x 1024 | Passed |
| Mobile | 390 x 844 | Passed |

All six tabs were opened at each viewport. The page had no document-level
horizontal overflow. Wide charts and tables use labelled, keyboard-focusable
scroll regions on narrow screens; mobile tables keep the first column visible.

## Interaction and Accessibility Checks

- Exactly one tab exposes `aria-selected="true"` after every navigation action.
- Arrow keys, Home, and End move between tabs and update the visible panel.
- URL fragments such as `#delivery` and `#sellers` open a specific view directly.
- Browser Back restores the preceding selected tab.
- The tab panel is labelled by the selected tab.
- Every SVG chart has a title and description, plus native value tooltips.
- Every data table has a descriptive caption and labelled scroll region.
- Truncated seller IDs expose the full identifier through a native tooltip.
- Focus indicators remain visible for tabs, links, charts, tables, and the skip link.
- Empty-data and missing-dashboard-data states have explicit messages.

## Technical Checks

The browser run completed without console errors, uncaught page errors, or failed
requests. Dashboard scripts, styles, data, report pages, and local assets returned
successful responses. The favicon uses an empty data URL to avoid an unnecessary
missing-file request.

Run the static and data checks with:

```bash
node --check dashboard/app.js
python3 scripts/validate_dashboard_metrics.py
python3 scripts/validate_marketing_funnel_analysis.py
git diff --check
```

Preview the same paths served by GitHub Pages with:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000/dashboard/#overview` and repeat the viewport and
keyboard checks above.

## Deployment Acceptance

After merge, verify the workflow run succeeds and check these routes:

- <https://22f3002680.github.io/Dataviz-project-Group3/>
- <https://22f3002680.github.io/Dataviz-project-Group3/#delivery>
- <https://22f3002680.github.io/Dataviz-project-Group3/#growth>
- <https://22f3002680.github.io/Dataviz-project-Group3/reports/index.html>
- <https://22f3002680.github.io/Dataviz-project-Group3/reports/marketing-funnel.html>
