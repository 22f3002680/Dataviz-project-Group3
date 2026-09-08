const data = window.DVD_DASHBOARD_DATA;
const root = document.querySelector("#view-root");
const kpis = document.querySelector("#kpis");
const tabs = [...document.querySelectorAll(".tab")];
const viewNames = tabs.map((button) => button.dataset.view);

if (!data?.summary) {
  root.innerHTML = '<div class="load-error" role="alert"><strong>Dashboard data could not be loaded.</strong><span>Refresh the page or check that data.js is available.</span></div>';
  throw new Error("window.DVD_DASHBOARD_DATA is unavailable");
}

const state = {
  view: viewNames.includes(window.location.hash.slice(1))
    ? window.location.hash.slice(1)
    : "overview",
};

const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");
const formatNumber = (value) => new Intl.NumberFormat("en-US").format(Math.round(Number(value) || 0));
const formatMoney = (value) => `R$${new Intl.NumberFormat("en-US").format(Math.round(Number(value) || 0))}`;
const formatPercent = (value) => `${Number(value || 0).toFixed(1)}%`;
const shortId = (value) => `${String(value).slice(0, 8)}...`;
let chartSequence = 0;

function renderKpis() {
  const items = [
    ["Orders", formatNumber(data.summary.orders), `${formatPercent(data.summary.deliveredRate)} delivered`],
    ["Avg review", data.summary.avgReview.toFixed(2), `${formatPercent(data.summary.highReviewRate)} are 4-5 stars`],
    ["Late delivery", formatPercent(data.summary.lateRate), `${formatPercent(data.summary.lateLowReviewRate)} low reviews when late`],
    ["Avg delivery", `${data.summary.avgDeliveryDays} days`, `${data.summary.medianDeliveryDays} day median`],
  ];

  kpis.innerHTML = items
    .map(
      ([label, value, note]) => `
        <article class="card">
          <p class="metric-label">${label}</p>
          <p class="metric-value">${value}</p>
          <p class="metric-note">${note}</p>
        </article>
      `
    )
    .join("");
}

function panel(title, subtitle, body, className = "") {
  return `
    <article class="panel ${className}">
      <div class="panel-header">
        <div>
          <h3>${title}</h3>
          ${subtitle ? `<p>${subtitle}</p>` : ""}
        </div>
      </div>
      ${body}
    </article>
  `;
}

function table(rows, columns, caption) {
  if (!rows.length) {
    return '<p class="empty-state">No rows meet the current reporting rules.</p>';
  }

  return `
    <div class="table-wrap" role="region" aria-label="${escapeHtml(caption)}" tabindex="0">
      <table>
        <caption class="sr-only">${escapeHtml(caption)}</caption>
        <thead>
          <tr>
            ${columns
              .map((column) => `<th scope="col" class="${column.numeric ? "numeric" : ""}">${escapeHtml(column.label)}</th>`)
              .join("")}
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  ${columns
                    .map((column) => {
                      const raw = column.value ? column.value(row) : row[column.key];
                      const title = column.title ? ` title="${escapeHtml(column.title(row))}"` : "";
                      return `<td class="${column.numeric ? "numeric" : ""}"${title}>${escapeHtml(raw ?? "n/a")}</td>`;
                    })
                    .join("")}
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function barChart(rows, labelKey, valueKey, options = {}) {
  if (!rows.length) {
    return '<p class="empty-state">No chart data is available.</p>';
  }

  const width = 760;
  const rowHeight = 28;
  const left = options.left ?? 180;
  const right = 110;
  const top = 8;
  const height = Math.max(220, rows.length * rowHeight + 24);
  const max = Math.max(...rows.map((row) => Number(row[valueKey]) || 0), 1);
  const color = options.color || "teal";
  const chartId = `chart-${++chartSequence}`;
  const title = options.title || `${valueKey.replaceAll("_", " ")} by ${labelKey.replaceAll("_", " ")}`;
  const description = options.description || "Horizontal bar chart.";

  const bars = rows
    .map((row, index) => {
      const y = top + index * rowHeight;
      const value = Number(row[valueKey]) || 0;
      const barWidth = ((width - left - right) * value) / max;
      const label = String(row[labelKey]).replaceAll("_", " ");
      const valueLabel = options.format ? options.format(value) : formatNumber(value);
      return `
        <g>
          <title>${escapeHtml(label)}: ${escapeHtml(valueLabel)}</title>
          <text x="0" y="${y + 16}">${escapeHtml(label)}</text>
          <rect class="bar ${color}" x="${left}" y="${y}" width="${barWidth}" height="18" rx="3"></rect>
          <text x="${left + barWidth + 6}" y="${y + 14}">${escapeHtml(valueLabel)}</text>
        </g>
      `;
    })
    .join("");

  return `
    <div class="chart-wrap" role="region" aria-label="${escapeHtml(title)}" tabindex="0">
      <svg class="chart" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="${chartId}-title ${chartId}-desc">
        <title id="${chartId}-title">${escapeHtml(title)}</title>
        <desc id="${chartId}-desc">${escapeHtml(description)}</desc>
        ${bars}
      </svg>
    </div>
  `;
}

function lineChart(rows, labelKey, valueKey, options = {}) {
  if (!rows.length) {
    return '<p class="empty-state">No chart data is available.</p>';
  }

  const width = 760;
  const height = 280;
  const pad = { top: 18, right: 24, bottom: 44, left: 46 };
  const chartId = `chart-${++chartSequence}`;
  const title = options.title || `${valueKey.replaceAll("_", " ")} over time`;
  const description = options.description || "Line chart showing values in chronological order.";
  const values = rows.map((row) => Number(row[valueKey]) || 0);
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const xStep = (width - pad.left - pad.right) / Math.max(rows.length - 1, 1);
  const yScale = (value) =>
    height - pad.bottom - ((value - min) / Math.max(max - min, 1)) * (height - pad.top - pad.bottom);

  const points = rows.map((row, index) => [pad.left + index * xStep, yScale(Number(row[valueKey]) || 0)]);
  const path = points.map(([x, y], index) => `${index === 0 ? "M" : "L"} ${x} ${y}`).join(" ");
  const labels = rows
    .map((row, index) => ({ row, index }))
    .filter(({ index }) => index % 3 === 0 || index === rows.length - 1)
    .map(({ row, index }) => `<text x="${pad.left + index * xStep}" y="${height - 18}" text-anchor="middle">${escapeHtml(row[labelKey])}</text>`)
    .join("");

  return `
    <div class="chart-wrap" role="region" aria-label="${escapeHtml(title)}" tabindex="0">
      <svg class="chart" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="${chartId}-title ${chartId}-desc">
        <title id="${chartId}-title">${escapeHtml(title)}</title>
        <desc id="${chartId}-desc">${escapeHtml(description)}</desc>
        <line class="axis" x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}"></line>
        <line class="axis" x1="${pad.left}" y1="${pad.top}" x2="${pad.left}" y2="${height - pad.bottom}"></line>
        <path class="line" d="${path}"></path>
        ${points.map(([x, y], index) => `<circle class="dot" cx="${x}" cy="${y}" r="4"><title>${escapeHtml(rows[index][labelKey])}: ${formatNumber(values[index])}</title></circle>`).join("")}
        <text x="${pad.left - 10}" y="${pad.top + 8}" text-anchor="end">${formatNumber(max)}</text>
        <text x="${pad.left - 10}" y="${height - pad.bottom}" text-anchor="end">${formatNumber(min)}</text>
        ${labels}
      </svg>
    </div>
  `;
}

function groupedBars(rows, options = {}) {
  if (!rows.length) {
    return '<p class="empty-state">No chart data is available.</p>';
  }

  const width = 720;
  const height = 280;
  const left = 70;
  const bottom = 48;
  const chartHeight = height - bottom - 20;
  const max = Math.max(...rows.flatMap((row) => [row.avg_delivery, row.late_rate]), 1);
  const band = (width - left - 30) / rows.length;
  const chartId = `chart-${++chartSequence}`;
  const title = options.title || "Delivery performance by shipment geography";

  return `
    <div class="chart-wrap" role="region" aria-label="${escapeHtml(title)}" tabindex="0">
      <svg class="chart" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="${chartId}-title ${chartId}-desc">
        <title id="${chartId}-title">${escapeHtml(title)}</title>
        <desc id="${chartId}-desc">Average delivery days and late-delivery percentage for same-state and cross-state shipments.</desc>
        <line class="axis" x1="${left}" y1="${height - bottom}" x2="${width - 20}" y2="${height - bottom}"></line>
        ${rows
          .map((row, index) => {
            const x = left + index * band + 8;
            const deliveryHeight = (row.avg_delivery / max) * chartHeight;
            const lateHeight = (row.late_rate / max) * chartHeight;
            return `
              <g>
                <title>${escapeHtml(row.segment)}: ${row.avg_delivery.toFixed(1)} delivery days, ${formatPercent(row.late_rate)} late</title>
                <rect class="bar teal" x="${x}" y="${height - bottom - deliveryHeight}" width="22" height="${deliveryHeight}" rx="3"></rect>
                <rect class="bar rose" x="${x + 26}" y="${height - bottom - lateHeight}" width="22" height="${lateHeight}" rx="3"></rect>
                <text x="${x + 24}" y="${height - 18}" text-anchor="middle">${escapeHtml(row.segment)}</text>
              </g>
            `;
          })
          .join("")}
        <text x="${left}" y="18">Delivery days and late rate</text>
        <text x="${width - 172}" y="18" class="legend teal-text">days</text>
        <text x="${width - 96}" y="18" class="legend rose-text">late %</text>
      </svg>
    </div>
  `;
}

function overview() {
  const insights = `
    <ul class="insight-list">
      <li><strong>Customer experience is generally strong.</strong> Average review is ${data.summary.avgReview}; ${formatPercent(data.summary.highReviewRate)} of reviews are 4-5 stars.</li>
      <li><strong>Delivery lateness is the main failure mode.</strong> Late orders are only ${formatPercent(data.summary.lateRate)} of delivered orders, but they create ${formatPercent(data.summary.lateLowReviewRate)} low reviews.</li>
      <li><strong>Growth should use guardrails.</strong> Prioritize categories and sellers that combine volume growth with 4.0+ reviews and late rate below roughly 10%.</li>
    </ul>
  `;
  root.innerHTML = `
    <div class="grid">
      ${panel("Monthly order pattern", "Order volume rises through 2017; low boundary months reflect partial coverage.", lineChart(data.monthlyOrders, "month", "orders", {
        title: "Monthly marketplace orders",
        description: "Monthly order volume from September 2016 through October 2018. The first and final months are partial.",
      }), "wide")}
      ${panel("Review distribution", "5-star reviews dominate, but 1-star volume is large enough to affect trust.", barChart(data.reviewDistribution, "score", "count", {
        left: 90,
        color: "indigo",
        title: "Review score distribution",
        description: "Review counts for scores one through five.",
      }))}
      ${panel("Main takeaways", "", insights)}
    </div>
  `;
}

function delivery() {
  root.innerHTML = `
    <div class="grid">
      ${panel("Delivery time vs review", "Ratings drop sharply as delivery time extends beyond three weeks.", barChart(data.deliveryBins, "range", "avg_review", {
        left: 120,
        color: "teal",
        format: (v) => v.toFixed(2),
        title: "Average review by delivery-time range",
        description: "Average review score for delivered orders grouped by total delivery days.",
      }))}
      ${panel("Same-state advantage", "Local seller/customer matching reduces freight and delivery time.", groupedBars(data.sameState, { title: "Same-state and cross-state delivery comparison" }))}
      ${panel("Late review risk", "Low-review rate by delivery speed.", table(data.deliveryBins, [
        { label: "Delivery range", key: "range" },
        { label: "Orders", key: "orders", numeric: true, value: (row) => formatNumber(row.orders) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
        { label: "Low reviews", key: "low_review_rate", numeric: true, value: (row) => formatPercent(row.low_review_rate) },
      ], "Delivery ranges with order volume, average review, and low-review rate"), "wide")}
    </div>
  `;
}

function categories() {
  root.innerHTML = `
    <div class="grid">
      ${panel("Top categories by items", "Demand concentration across marketplace categories.", barChart(data.topCategoriesByItems.slice(0, 10), "category", "items", {
        color: "teal",
        title: "Top product categories by item volume",
        description: "The ten categories with the most order-item rows.",
      }))}
      ${panel("Top categories by revenue", "Revenue is led by health, watches, bed/bath, sports, and computers.", barChart(data.topCategoriesByRevenue.slice(0, 10), "category", "revenue", {
        color: "indigo",
        format: formatMoney,
        title: "Top product categories by product revenue",
        description: "The ten categories with the highest sum of item price, excluding freight.",
      }))}
      ${panel("Category risk table", "High low-review or late-delivery categories need operational checks before scaling.", table(data.riskCategories, [
        { label: "Category", key: "category" },
        { label: "Items", key: "items", numeric: true, value: (row) => formatNumber(row.items) },
        { label: "Revenue", key: "revenue", numeric: true, value: (row) => formatMoney(row.revenue) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
        { label: "Late", key: "late_rate", numeric: true, value: (row) => formatPercent(row.late_rate) },
        { label: "Low reviews", key: "low_review_rate", numeric: true, value: (row) => formatPercent(row.low_review_rate) },
      ], "Category risk metrics for categories meeting the minimum item threshold"), "wide")}
    </div>
  `;
}

function regions() {
  root.innerHTML = `
    <div class="grid">
      ${panel("Top demand states", "SP, RJ, and MG dominate item volume.", barChart(data.topStates.slice(0, 10), "customer_state", "items", {
        left: 90,
        color: "teal",
        title: "Top customer states by item volume",
        description: "The ten customer states with the most order-item rows.",
      }))}
      ${panel("Risk states", "Late rate among states with at least 500 delivered item rows.", barChart(data.riskStates.slice(0, 10), "customer_state", "late_rate", {
        left: 90,
        color: "rose",
        format: formatPercent,
        title: "Late-delivery rate by customer state",
        description: "Late-delivery percentage for states meeting the minimum delivered-item threshold.",
      }))}
      ${panel("Regional operating view", "High demand is not always high experience.", table(data.riskStates, [
        { label: "State", key: "customer_state" },
        { label: "Items", key: "items", numeric: true, value: (row) => formatNumber(row.items) },
        { label: "Avg delivery", key: "avg_delivery", numeric: true, value: (row) => `${row.avg_delivery.toFixed(1)}d` },
        { label: "Late", key: "late_rate", numeric: true, value: (row) => formatPercent(row.late_rate) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
      ], "Regional delivery and review metrics for states meeting the minimum volume threshold"), "wide")}
    </div>
  `;
}

function sellers() {
  root.innerHTML = `
    <div class="grid">
      ${panel("High contribution, weak experience", "Seller watchlist by revenue and customer experience.", table(data.riskSellers, [
        { label: "Seller", key: "seller_id", value: (row) => shortId(row.seller_id), title: (row) => `Full seller ID: ${row.seller_id}` },
        { label: "City", key: "seller_city" },
        { label: "Orders", key: "orders", numeric: true, value: (row) => formatNumber(row.orders) },
        { label: "Revenue", key: "revenue", numeric: true, value: (row) => formatMoney(row.revenue) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
        { label: "Late", key: "late_rate", numeric: true, value: (row) => formatPercent(row.late_rate) },
      ], "Seller intervention watchlist with volume, revenue, review, and delivery metrics"), "wide")}
      ${panel("Healthy sellers", "High-volume sellers that preserve stronger review and delivery metrics.", table(data.healthySellers, [
        { label: "Seller", key: "seller_id", value: (row) => shortId(row.seller_id), title: (row) => `Full seller ID: ${row.seller_id}` },
        { label: "City", key: "seller_city" },
        { label: "Orders", key: "orders", numeric: true, value: (row) => formatNumber(row.orders) },
        { label: "Revenue", key: "revenue", numeric: true, value: (row) => formatMoney(row.revenue) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
        { label: "Late", key: "late_rate", numeric: true, value: (row) => formatPercent(row.late_rate) },
      ], "Healthy seller benchmarks with volume, revenue, review, and delivery metrics"), "wide")}
    </div>
  `;
}

function growth() {
  root.innerHTML = `
    <div class="grid">
      ${panel("Healthy growth categories", "Jan-Aug 2017 vs Jan-Aug 2018: growth with good review and delivery guardrails.", table(data.growthCategories, [
        { label: "Category", key: "category" },
        { label: "2017 items", key: "items_2017", numeric: true, value: (row) => formatNumber(row.items_2017) },
        { label: "2018 items", key: "items_2018", numeric: true, value: (row) => formatNumber(row.items_2018) },
        { label: "Item growth", key: "item_growth", numeric: true, value: (row) => formatPercent(row.item_growth) },
        { label: "2018 revenue", key: "revenue_2018", numeric: true, value: (row) => formatMoney(row.revenue_2018) },
        { label: "Review", key: "avg_review_2018", numeric: true, value: (row) => row.avg_review_2018.toFixed(2) },
        { label: "Late", key: "late_rate_2018", numeric: true, value: (row) => formatPercent(row.late_rate_2018) },
      ], "Growth categories meeting item-volume, review, and delivery guardrails"), "wide")}
      ${panel("Marketing funnel", "Seller acquisition funnel from marketing qualified leads.", `
        <div class="funnel-metrics" aria-label="Marketing funnel summary">
          <div class="funnel-metric"><p class="metric-label">MQLs</p><p class="metric-value">${formatNumber(data.summary.mql)}</p></div>
          <div class="funnel-metric"><p class="metric-label">Closed deals</p><p class="metric-value">${formatNumber(data.summary.closedDeals)}</p></div>
          <div class="funnel-metric"><p class="metric-label">Observed conversion</p><p class="metric-value">${formatPercent(data.summary.winRate)}</p></div>
          <div class="funnel-metric"><p class="metric-label">Final-story role</p><p class="metric-value compact">Supporting</p></div>
        </div>
        <a class="button-link" href="./reports/marketing-funnel.html">Open funnel analysis</a>
      `, "wide")}
    </div>
  `;
}

const views = {
  overview,
  delivery,
  categories,
  regions,
  sellers,
  growth,
};

function render() {
  chartSequence = 0;
  tabs.forEach((button) => {
    const selected = button.dataset.view === state.view;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-selected", String(selected));
    button.tabIndex = selected ? 0 : -1;
  });
  root.setAttribute("aria-labelledby", `tab-${state.view}`);
  document.title = `${tabs.find((button) => button.dataset.view === state.view).textContent} | E-Commerce Satisfaction Dashboard`;
  views[state.view]();
}

function activateView(view, updateHistory = true) {
  if (!views[view] || view === state.view) {
    return;
  }
  state.view = view;
  if (updateHistory) {
    window.history.pushState(null, "", `#${view}`);
  }
  render();
}

tabs.forEach((button, index) => {
  button.addEventListener("click", () => {
    activateView(button.dataset.view);
  });
  button.addEventListener("keydown", (event) => {
    const keyOffsets = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
    let targetIndex = index;
    if (event.key in keyOffsets) {
      targetIndex = (index + keyOffsets[event.key] + tabs.length) % tabs.length;
    } else if (event.key === "Home") {
      targetIndex = 0;
    } else if (event.key === "End") {
      targetIndex = tabs.length - 1;
    } else {
      return;
    }
    event.preventDefault();
    tabs[targetIndex].focus();
    activateView(tabs[targetIndex].dataset.view);
  });
});

window.addEventListener("popstate", () => {
  const requestedView = window.location.hash.slice(1);
  const nextView = views[requestedView] ? requestedView : "overview";
  if (nextView !== state.view) {
    state.view = nextView;
    render();
  }
});

if (!viewNames.includes(window.location.hash.slice(1))) {
  window.history.replaceState(null, "", "#overview");
}
renderKpis();
render();
