const data = window.DVD_DASHBOARD_DATA;

const state = {
  view: "overview",
};

const formatNumber = (value) => new Intl.NumberFormat("en-US").format(Math.round(value));
const formatMoney = (value) => `R$${new Intl.NumberFormat("en-US").format(Math.round(value))}`;
const formatPercent = (value) => `${Number(value).toFixed(1)}%`;
const shortId = (value) => `${String(value).slice(0, 8)}...`;

const root = document.querySelector("#view-root");
const kpis = document.querySelector("#kpis");

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

function table(rows, columns) {
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            ${columns
              .map((column) => `<th class="${column.numeric ? "numeric" : ""}">${column.label}</th>`)
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
                      return `<td class="${column.numeric ? "numeric" : ""}">${raw}</td>`;
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
  const width = 720;
  const rowHeight = 28;
  const left = options.left ?? 180;
  const right = 30;
  const top = 8;
  const height = Math.max(220, rows.length * rowHeight + 24);
  const max = Math.max(...rows.map((row) => Number(row[valueKey]) || 0), 1);
  const color = options.color || "teal";

  const bars = rows
    .map((row, index) => {
      const y = top + index * rowHeight;
      const value = Number(row[valueKey]) || 0;
      const barWidth = ((width - left - right) * value) / max;
      const label = String(row[labelKey]).replaceAll("_", " ");
      const valueLabel = options.format ? options.format(value) : formatNumber(value);
      return `
        <text x="0" y="${y + 16}">${label}</text>
        <rect class="bar ${color}" x="${left}" y="${y}" width="${barWidth}" height="18" rx="3"></rect>
        <text x="${left + barWidth + 6}" y="${y + 14}">${valueLabel}</text>
      `;
    })
    .join("");

  return `<svg class="chart" viewBox="0 0 ${width} ${height}" role="img">${bars}</svg>`;
}

function lineChart(rows, labelKey, valueKey) {
  const width = 760;
  const height = 280;
  const pad = { top: 18, right: 24, bottom: 44, left: 46 };
  const values = rows.map((row) => Number(row[valueKey]) || 0);
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const xStep = (width - pad.left - pad.right) / Math.max(rows.length - 1, 1);
  const yScale = (value) =>
    height - pad.bottom - ((value - min) / Math.max(max - min, 1)) * (height - pad.top - pad.bottom);

  const points = rows.map((row, index) => [pad.left + index * xStep, yScale(Number(row[valueKey]) || 0)]);
  const path = points.map(([x, y], index) => `${index === 0 ? "M" : "L"} ${x} ${y}`).join(" ");
  const labels = rows
    .filter((_, index) => index % 3 === 0 || index === rows.length - 1)
    .map((row, index) => {
      const originalIndex = rows.indexOf(row);
      return `<text x="${pad.left + originalIndex * xStep}" y="${height - 18}" text-anchor="middle">${row[labelKey]}</text>`;
    })
    .join("");

  return `
    <svg class="chart" viewBox="0 0 ${width} ${height}" role="img">
      <line class="axis" x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}"></line>
      <line class="axis" x1="${pad.left}" y1="${pad.top}" x2="${pad.left}" y2="${height - pad.bottom}"></line>
      <path class="line" d="${path}"></path>
      ${points.map(([x, y]) => `<circle class="dot" cx="${x}" cy="${y}" r="4"></circle>`).join("")}
      <text x="${pad.left - 10}" y="${pad.top + 8}" text-anchor="end">${formatNumber(max)}</text>
      <text x="${pad.left - 10}" y="${height - pad.bottom}" text-anchor="end">${formatNumber(min)}</text>
      ${labels}
    </svg>
  `;
}

function groupedBars(rows) {
  const width = 720;
  const height = 280;
  const left = 70;
  const bottom = 48;
  const chartHeight = height - bottom - 20;
  const max = Math.max(...rows.flatMap((row) => [row.avg_delivery, row.late_rate]), 1);
  const band = (width - left - 30) / rows.length;

  return `
    <svg class="chart" viewBox="0 0 ${width} ${height}" role="img">
      <line class="axis" x1="${left}" y1="${height - bottom}" x2="${width - 20}" y2="${height - bottom}"></line>
      ${rows
        .map((row, index) => {
          const x = left + index * band + 8;
          const deliveryHeight = (row.avg_delivery / max) * chartHeight;
          const lateHeight = (row.late_rate / max) * chartHeight;
          return `
            <rect class="bar teal" x="${x}" y="${height - bottom - deliveryHeight}" width="22" height="${deliveryHeight}" rx="3"></rect>
            <rect class="bar rose" x="${x + 26}" y="${height - bottom - lateHeight}" width="22" height="${lateHeight}" rx="3"></rect>
            <text x="${x + 24}" y="${height - 18}" text-anchor="middle">${row.segment}</text>
          `;
        })
        .join("")}
      <text x="${left}" y="18">Delivery days and late rate</text>
      <text x="${width - 160}" y="18" fill="#087f8c">teal: days</text>
      <text x="${width - 80}" y="18" fill="#bf3f4a">red: late %</text>
    </svg>
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
      ${panel("Monthly order pattern", "Orders peak around late 2017 and remain strong through 2018.", lineChart(data.monthlyOrders, "month", "orders"), "wide")}
      ${panel("Review distribution", "5-star reviews dominate, but 1-star volume is large enough to affect trust.", barChart(data.reviewDistribution, "score", "count", { left: 90, color: "indigo" }))}
      ${panel("Main takeaways", "", insights)}
    </div>
  `;
}

function delivery() {
  root.innerHTML = `
    <div class="grid">
      ${panel("Delivery time vs review", "Ratings drop sharply after 22 days.", barChart(data.deliveryBins, "range", "avg_review", { left: 120, color: "teal", format: (v) => v.toFixed(2) }))}
      ${panel("Same-state advantage", "Local seller/customer matching reduces freight and delivery time.", groupedBars(data.sameState))}
      ${panel("Late review risk", "Low-review rate by delivery speed.", table(data.deliveryBins, [
        { label: "Delivery range", key: "range" },
        { label: "Orders", key: "orders", numeric: true, value: (row) => formatNumber(row.orders) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
        { label: "Low reviews", key: "low_review_rate", numeric: true, value: (row) => formatPercent(row.low_review_rate) },
      ]), "wide")}
    </div>
  `;
}

function categories() {
  root.innerHTML = `
    <div class="grid">
      ${panel("Top categories by items", "Demand concentration across marketplace categories.", barChart(data.topCategoriesByItems.slice(0, 10), "category", "items", { color: "teal" }))}
      ${panel("Top categories by revenue", "Revenue is led by health, watches, bed/bath, sports, and computers.", barChart(data.topCategoriesByRevenue.slice(0, 10), "category", "revenue", { color: "indigo", format: formatMoney }))}
      ${panel("Category risk table", "High low-review or late-delivery categories need operational checks before scaling.", table(data.riskCategories, [
        { label: "Category", key: "category" },
        { label: "Items", key: "items", numeric: true, value: (row) => formatNumber(row.items) },
        { label: "Revenue", key: "revenue", numeric: true, value: (row) => formatMoney(row.revenue) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
        { label: "Late", key: "late_rate", numeric: true, value: (row) => formatPercent(row.late_rate) },
        { label: "Low reviews", key: "low_review_rate", numeric: true, value: (row) => formatPercent(row.low_review_rate) },
      ]), "wide")}
    </div>
  `;
}

function regions() {
  root.innerHTML = `
    <div class="grid">
      ${panel("Top demand states", "SP, RJ, and MG dominate item volume.", barChart(data.topStates.slice(0, 10), "customer_state", "items", { left: 90, color: "teal" }))}
      ${panel("Risk states", "Late rate among states with meaningful item volume.", barChart(data.riskStates.slice(0, 10), "customer_state", "late_rate", { left: 90, color: "rose", format: formatPercent }))}
      ${panel("Regional operating view", "High demand is not always high experience.", table(data.riskStates, [
        { label: "State", key: "customer_state" },
        { label: "Items", key: "items", numeric: true, value: (row) => formatNumber(row.items) },
        { label: "Avg delivery", key: "avg_delivery", numeric: true, value: (row) => `${row.avg_delivery.toFixed(1)}d` },
        { label: "Late", key: "late_rate", numeric: true, value: (row) => formatPercent(row.late_rate) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
      ]), "wide")}
    </div>
  `;
}

function sellers() {
  root.innerHTML = `
    <div class="grid">
      ${panel("High contribution, weak experience", "Seller watchlist by revenue and customer experience.", table(data.riskSellers, [
        { label: "Seller", key: "seller_id", value: (row) => shortId(row.seller_id) },
        { label: "City", key: "seller_city" },
        { label: "Orders", key: "orders", numeric: true, value: (row) => formatNumber(row.orders) },
        { label: "Revenue", key: "revenue", numeric: true, value: (row) => formatMoney(row.revenue) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
        { label: "Late", key: "late_rate", numeric: true, value: (row) => formatPercent(row.late_rate) },
      ]), "wide")}
      ${panel("Healthy sellers", "High-volume sellers that preserve stronger review and delivery metrics.", table(data.healthySellers, [
        { label: "Seller", key: "seller_id", value: (row) => shortId(row.seller_id) },
        { label: "City", key: "seller_city" },
        { label: "Orders", key: "orders", numeric: true, value: (row) => formatNumber(row.orders) },
        { label: "Revenue", key: "revenue", numeric: true, value: (row) => formatMoney(row.revenue) },
        { label: "Avg review", key: "avg_review", numeric: true, value: (row) => row.avg_review.toFixed(2) },
        { label: "Late", key: "late_rate", numeric: true, value: (row) => formatPercent(row.late_rate) },
      ]), "wide")}
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
      ]), "wide")}
      ${panel("Marketing funnel", "Seller acquisition funnel from marketing qualified leads.", `
        <div class="kpis">
          <article class="card"><p class="metric-label">MQLs</p><p class="metric-value">${formatNumber(data.summary.mql)}</p></article>
          <article class="card"><p class="metric-label">Closed deals</p><p class="metric-value">${formatNumber(data.summary.closedDeals)}</p></article>
          <article class="card"><p class="metric-label">Win rate</p><p class="metric-value">${formatPercent(data.summary.winRate)}</p></article>
          <article class="card"><p class="metric-label">Marketplace rule</p><p class="metric-value">4.0+</p><p class="metric-note">review guardrail</p></article>
        </div>
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
  document.querySelectorAll(".tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === state.view);
  });
  views[state.view]();
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    state.view = button.dataset.view;
    render();
  });
});

renderKpis();
render();
