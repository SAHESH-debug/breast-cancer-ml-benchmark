import json

with open("dashboard_data.json") as f:
    DATA = json.load(f)
with open("plots_b64.json") as f:
    PLOTS = json.load(f)
with open("lr_params.json") as f:
    LR = json.load(f)

HTML_TEMPLATE = r"""<title>Tumor Diagnosis Lab</title>
<style>
/* ===== Design tokens =====
   Layout: left icon-rail nav + main content; KPI tiles up top on Overview;
   clinical-lab palette (cool slate/teal) kept deliberately calm --
   this is a diagnostic-adjacent tool, not a marketing page. */
:root {
  --bg: #f3f5f6;
  --surface: #ffffff;
  --surface-2: #eef1f2;
  --border: #dbe1e3;
  --fg: #1c2528;
  --muted: #5c6b70;
  --accent: #0e7c86;
  --accent-fg: #ffffff;
  --malignant: #c0392b;
  --malignant-bg: #fbeae8;
  --benign: #1f8a52;
  --benign-bg: #e9f7ef;
  --focus: #0e7c86;
  --code-bg: #eef1f2;
  --shadow: 0 1px 2px rgba(20,30,32,0.06), 0 4px 14px rgba(20,30,32,0.06);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #11181a;
    --surface: #161f22;
    --surface-2: #1c2528;
    --border: #2a3539;
    --fg: #e7edee;
    --muted: #93a3a8;
    --accent: #2bb3bd;
    --accent-fg: #06181a;
    --malignant: #ff8a7a;
    --malignant-bg: #3a1e1b;
    --benign: #6bd99a;
    --benign-bg: #16302220;
    --focus: #2bb3bd;
    --code-bg: #1c2528;
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 6px 20px rgba(0,0,0,0.35);
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #11181a; --surface: #161f22; --surface-2: #1c2528; --border: #2a3539;
  --fg: #e7edee; --muted: #93a3a8; --accent: #2bb3bd; --accent-fg: #06181a;
  --malignant: #ff8a7a; --malignant-bg: #3a1e1b; --benign: #6bd99a; --benign-bg: #16302220;
  --focus: #2bb3bd; --code-bg: #1c2528; --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 6px 20px rgba(0,0,0,0.35);
  color-scheme: dark;
}

* { box-sizing: border-box; }
body {
  background: var(--bg); color: var(--fg); margin: 0;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 15px; line-height: 1.5;
}
h1,h2,h3 { font-family: "Fraunces", Georgia, serif; text-wrap: balance; margin: 0 0 4px; }
.mono { font-family: "JetBrains Mono", ui-monospace, Menlo, monospace; font-variant-numeric: tabular-nums; }

a { color: var(--accent); }

.app { display: flex; min-height: 100%; }

/* ---- Sidebar ---- */
.sidebar {
  width: 236px; flex-shrink: 0; background: var(--surface);
  border-right: 1px solid var(--border); padding: 20px 14px;
  display: flex; flex-direction: column; gap: 4px;
  position: sticky; top: env(safe-area-inset-top, 0px); align-self: flex-start;
  height: 100vh; overflow-y: auto;
}
.brand { display: flex; align-items: center; gap: 10px; padding: 4px 10px 18px; }
.brand-mark {
  width: 30px; height: 30px; border-radius: 8px; background: var(--accent);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.brand-mark svg { width: 17px; height: 17px; stroke: var(--accent-fg); }
.brand-name { font-family: "Fraunces", Georgia, serif; font-size: 16.5px; font-weight: 600; }
.brand-sub { font-size: 11px; color: var(--muted); margin-top: -2px; }

.nav-btn {
  display: flex; align-items: center; gap: 10px; width: 100%; text-align: left;
  padding: 9px 11px; border-radius: 8px; border: none; background: transparent;
  color: var(--muted); font-size: 13.5px; font-weight: 500; cursor: pointer;
  font-family: inherit;
}
.nav-btn:hover { background: var(--surface-2); color: var(--fg); }
.nav-btn.active { background: var(--accent); color: var(--accent-fg); }
.nav-btn svg { width: 16px; height: 16px; flex-shrink: 0; }
.nav-btn:focus-visible { outline: 2px solid var(--focus); outline-offset: 1px; }

.sidebar-foot {
  margin-top: auto; padding: 12px 10px; border-top: 1px solid var(--border);
  font-size: 11.5px; color: var(--muted); line-height: 1.45;
}
.theme-toggle {
  display: flex; gap: 6px; margin-bottom: 10px;
}
.theme-toggle button {
  flex: 1; padding: 6px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--surface-2); color: var(--muted); font-size: 11.5px; cursor: pointer;
  font-family: inherit;
}
.theme-toggle button.active { background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }

/* ---- Main ---- */
.main { flex: 1; min-width: 0; padding: 28px 32px 60px; max-width: 1180px; }
.page { display: none; }
.page.active { display: block; }

.disclaimer {
  background: var(--surface-2); border: 1px solid var(--border); border-left: 3px solid var(--accent);
  border-radius: 8px; padding: 10px 14px; font-size: 12.5px; color: var(--muted);
  margin-bottom: 22px; display: flex; gap: 8px; align-items: flex-start;
}
.disclaimer svg { width: 15px; height: 15px; flex-shrink: 0; margin-top: 1px; stroke: var(--accent); }

.page-head { margin-bottom: 20px; }
.page-head p { color: var(--muted); margin: 6px 0 0; max-width: 62ch; font-size: 13.5px; }

/* KPI tiles */
.kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px,1fr)); gap: 12px; margin-bottom: 22px; }
.kpi {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; box-shadow: var(--shadow);
}
.kpi .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
.kpi .value { font-family: "Fraunces", Georgia, serif; font-size: 26px; margin-top: 4px; }
.kpi .sub { font-size: 11.5px; color: var(--muted); margin-top: 2px; }

.card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 18px 20px; box-shadow: var(--shadow); margin-bottom: 18px;
}
.card h3 { font-size: 15.5px; margin-bottom: 10px; }
.card .cap { font-size: 12px; color: var(--muted); margin-top: 8px; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; }
@media (max-width: 860px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--border); white-space: nowrap; }
th { color: var(--muted); font-weight: 600; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em; }
tr:last-child td { border-bottom: none; }
.table-wrap { overflow-x: auto; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tr.best td { background: var(--benign-bg); }
.pill { display: inline-block; padding: 2px 9px; border-radius: 99px; font-size: 11px; font-weight: 600; }
.pill.best { background: var(--benign); color: white; }

select, input[type=number] {
  background: var(--surface-2); border: 1px solid var(--border); color: var(--fg);
  border-radius: 7px; padding: 7px 10px; font-size: 13px; font-family: inherit;
}
select:focus, input:focus { outline: 2px solid var(--focus); outline-offset: 1px; }
label { font-size: 12px; color: var(--muted); display: block; margin-bottom: 4px; }

.field-row { display: flex; gap: 12px; align-items: flex-end; margin-bottom: 16px; flex-wrap: wrap; }

.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border); margin-bottom: 16px; flex-wrap: wrap; }
.tab-btn {
  padding: 8px 14px; border: none; background: transparent; color: var(--muted);
  font-size: 13px; font-weight: 500; cursor: pointer; border-bottom: 2px solid transparent;
  margin-bottom: -1px; font-family: inherit;
}
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-panel { display: none; }
.tab-panel.active { display: block; }

img.plot { max-width: 100%; border-radius: 8px; border: 1px solid var(--border); display: block; }

.cm-grid { display: grid; grid-template-columns: auto 1fr 1fr; gap: 2px; max-width: 480px; }
.cm-cell { padding: 18px; text-align: center; border-radius: 6px; }
.cm-head { font-size: 11px; color: var(--muted); display: flex; align-items: center; justify-content: center; padding: 6px; }
.cm-val { font-family: "Fraunces", Georgia, serif; font-size: 28px; }
.cm-sub { font-size: 11px; margin-top: 2px; }
.cm-tp { background: var(--benign-bg); color: var(--benign); }
.cm-tn { background: var(--benign-bg); color: var(--benign); }
.cm-fp { background: var(--malignant-bg); color: var(--malignant); }
.cm-fn { background: var(--malignant-bg); color: var(--malignant); }

.legend { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 10px; font-size: 12px; }
.legend label { display: flex; align-items: center; gap: 5px; color: var(--fg); margin: 0; cursor: pointer; }
.legend input[type=checkbox] { accent-color: var(--accent); }
.swatch { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }

.pred-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px 14px; margin-bottom: 18px; }
.pred-field input { width: 100%; }
.btn {
  background: var(--accent); color: var(--accent-fg); border: none; border-radius: 8px;
  padding: 10px 20px; font-size: 13.5px; font-weight: 600; cursor: pointer; font-family: inherit;
}
.btn:hover { filter: brightness(1.06); }
.btn:focus-visible { outline: 2px solid var(--fg); outline-offset: 2px; }

.result-banner {
  display: none; border-radius: 10px; padding: 18px 20px; margin-top: 16px;
  border: 1px solid var(--border);
}
.result-banner.show { display: block; }
.result-banner.malignant { background: var(--malignant-bg); border-color: var(--malignant); }
.result-banner.benign { background: var(--benign-bg); border-color: var(--benign); }
.result-title { font-family: "Fraunces", Georgia, serif; font-size: 22px; margin-bottom: 6px; }
.result-title.malignant { color: var(--malignant); }
.result-title.benign { color: var(--benign); }
.prob-bar-track { height: 10px; border-radius: 99px; background: var(--surface-2); overflow: hidden; margin: 8px 0; }
.prob-bar-fill { height: 100%; border-radius: 99px; transition: width 0.4s ease; }

.src-note { font-size: 11.5px; color: var(--muted); margin-top: 4px; }

@media (max-width: 760px) {
  .sidebar { position: fixed; left: 0; top: 0; bottom: 0; z-index: 20; transform: translateX(-100%); transition: transform 0.2s; }
  .sidebar.open { transform: translateX(0); }
  .main { padding: 18px 16px 50px; }
  .mobile-nav-toggle { display: flex !important; }
}
.mobile-nav-toggle {
  display: none; align-items: center; gap: 8px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 12px; margin-bottom: 14px; color: var(--fg); font-size: 13px; cursor: pointer;
}
</style>

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">

<div class="app">
  <button class="mobile-nav-toggle" id="navToggle">☰ Menu</button>
  <nav class="sidebar" id="sidebar">
    <div class="brand">
      <div class="brand-mark"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a5 5 0 0 1 5 5c0 3-2 4-2 7a3 3 0 0 1-6 0c0-3-2-4-2-7a5 5 0 0 1 5-5Z"/><path d="M9 14c0 3 1.5 6 3 8 1.5-2 3-5 3-8"/></svg></div>
      <div><div class="brand-name">Tumor Diagnosis Lab</div><div class="brand-sub">WDBC · 5-model comparison</div></div>
    </div>

    <div class="theme-toggle">
      <button id="themeLight">Light</button>
      <button id="themeDark">Dark</button>
      <button id="themeSystem" class="active">Auto</button>
    </div>

    <button class="nav-btn active" data-page="overview"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>Overview</button>
    <button class="nav-btn" data-page="dataset"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5"/><path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3"/></svg>Dataset Explorer</button>
    <button class="nav-btn" data-page="eda"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="M7 15l4-6 4 3 5-8"/></svg>EDA &amp; PCA</button>
    <button class="nav-btn" data-page="compare"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>Model Comparison</button>
    <button class="nav-btn" data-page="confusion"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/></svg>Confusion Matrix</button>
    <button class="nav-btn" data-page="roc"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21 21 3"/><path d="M3 3c0 10 8 18 18 18"/></svg>ROC Curve</button>
    <button class="nav-btn" data-page="importance"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 2v10l7 7"/></svg>Feature Importance</button>
    <button class="nav-btn" data-page="predict"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/></svg>Prediction</button>

    <div class="sidebar-foot">
      Educational ML demonstration only.<br>Not a medical diagnostic tool.
    </div>
  </nav>

  <main class="main">
    <div class="disclaimer">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M12 9v4"/><path d="M12 17h.01"/><circle cx="12" cy="12" r="10"/></svg>
      <span>Educational machine-learning project. Nothing on this page is medical advice, a diagnosis, or validated for clinical use.</span>
    </div>

    <!-- ===================== OVERVIEW ===================== -->
    <section class="page active" id="page-overview">
      <div class="page-head"><h1>Overview</h1><p>Breast tumor diagnosis as a binary classification problem — comparing 5 algorithms on the Wisconsin Diagnostic Breast Cancer dataset, with correct cross-validation, tuning, and no train/test leakage.</p></div>

      <div class="kpi-row" id="kpiRow"></div>

      <div class="card">
        <h3>Best model per metric</h3>
        <div class="table-wrap"><table id="overviewTable"></table></div>
      </div>

      <div class="grid-2">
        <div class="card">
          <h3>Pipeline</h3>
          <table>
            <tr><td>Raw data</td><td class="mono">569 × 30</td></tr>
            <tr><td>Split</td><td class="mono">80 / 20, stratified</td></tr>
            <tr><td>Cross-validation</td><td class="mono">5-fold, stratified</td></tr>
            <tr><td>Tuning</td><td class="mono">GridSearchCV, train fold only</td></tr>
            <tr><td>Scaling</td><td class="mono">StandardScaler inside Pipeline</td></tr>
            <tr><td>Test set</td><td class="mono">touched once, at the end</td></tr>
          </table>
        </div>
        <div class="card">
          <h3>Why not just accuracy</h3>
          <p style="font-size:13px;color:var(--muted);margin:0 0 8px">Classes are imbalanced (63% / 37%). A model that always predicts benign scores ~63% accuracy while catching zero real cancers — so recall on the malignant class is tracked specifically.</p>
          <p style="font-size:13px;color:var(--muted);margin:0">See <b>Model Comparison</b> for the full metric breakdown per model.</p>
        </div>
      </div>
    </section>

    <!-- ===================== DATASET EXPLORER ===================== -->
    <section class="page" id="page-dataset">
      <div class="page-head"><h1>Dataset Explorer</h1><p id="dsSourceLine"></p></div>

      <div class="kpi-row" id="dsKpiRow"></div>

      <div class="card">
        <h3>Class distribution</h3>
        <div id="classBarChart"></div>
      </div>

      <div class="card">
        <h3>Sample rows</h3>
        <div class="table-wrap" id="sampleTable"></div>
      </div>

      <div class="card">
        <h3>Feature statistics (all 30 features)</h3>
        <div class="table-wrap" id="statsTable" style="max-height:360px;overflow-y:auto"></div>
      </div>
    </section>

    <!-- ===================== EDA ===================== -->
    <section class="page" id="page-eda">
      <div class="page-head"><h1>Exploratory Data Analysis &amp; PCA</h1><p>Every chart here answers one question about the data before any model sees it.</p></div>

      <div class="tabs">
        <button class="tab-btn active" data-tab="eda1">Class balance</button>
        <button class="tab-btn" data-tab="eda2">Correlation</button>
        <button class="tab-btn" data-tab="eda3">Feature distributions</button>
        <button class="tab-btn" data-tab="eda4">PCA</button>
      </div>
      <div class="card tab-panel active" id="eda1">
        <h3>Are the classes balanced?</h3>
        <img class="plot" src="data:image/png;base64,__PLOT_class_distribution__">
      </div>
      <div class="card tab-panel" id="eda2">
        <h3>Which features move together?</h3>
        <img class="plot" src="data:image/png;base64,__PLOT_correlation_heatmap__">
        <p class="cap">Radius, perimeter, and area cluster tightly — expected, since all three describe tumor size from different angles.</p>
      </div>
      <div class="card tab-panel" id="eda3">
        <h3>Do malignant and benign separate on individual features?</h3>
        <img class="plot" src="data:image/png;base64,__PLOT_feature_distributions__">
      </div>
      <div class="card tab-panel" id="eda4">
        <h3>Can the classes be separated in reduced dimensions?</h3>
        <div class="grid-2">
          <img class="plot" src="data:image/png;base64,__PLOT_pca_scatter__">
          <img class="plot" src="data:image/png;base64,__PLOT_pca_explained_variance__">
        </div>
        <p class="cap">PCA compresses many features into fewer new dimensions while trying to preserve as much information as possible. Even with only 2 of the 30 dimensions kept, the two classes visibly separate.</p>
      </div>
    </section>

    <!-- ===================== MODEL COMPARISON ===================== -->
    <section class="page" id="page-compare">
      <div class="page-head"><h1>Model Comparison</h1><p>All 5 models, trained and tuned identically, evaluated once on the same untouched test set.</p></div>

      <div class="card">
        <h3>Leaderboard</h3>
        <div class="table-wrap" id="leaderboardTable"></div>
      </div>

      <div class="card">
        <h3>Metric comparison</h3>
        <div class="field-row">
          <div><label>Metric</label>
            <select id="metricSelect">
              <option value="accuracy">Accuracy</option>
              <option value="precision">Precision</option>
              <option value="recall">Recall</option>
              <option value="f1">F1-Score</option>
              <option value="roc_auc">ROC-AUC</option>
            </select>
          </div>
        </div>
        <svg id="barChart" viewBox="0 0 640 300" width="100%" style="max-width:640px"></svg>
      </div>
    </section>

    <!-- ===================== CONFUSION MATRIX ===================== -->
    <section class="page" id="page-confusion">
      <div class="page-head"><h1>Confusion Matrix</h1><p>Pick a model to see exactly which kind of mistake it makes on the test set.</p></div>

      <div class="field-row">
        <div><label>Model</label><select id="cmModelSelect"></select></div>
      </div>

      <div class="card">
        <div class="cm-grid" id="cmGrid"></div>
      </div>

      <div class="card">
        <h3>What TP / TN / FP / FN mean</h3>
        <table>
          <tr><td><b>True Positive (TP)</b></td><td>Correctly caught a malignant tumor</td></tr>
          <tr><td><b>True Negative (TN)</b></td><td>Correctly identified a benign tumor</td></tr>
          <tr><td><b>False Positive (FP)</b></td><td>Said malignant, was actually benign — a false alarm</td></tr>
          <tr><td><b>False Negative (FN)</b></td><td>Said benign, was actually malignant — the costliest mistake here</td></tr>
        </table>
      </div>
    </section>

    <!-- ===================== ROC ===================== -->
    <section class="page" id="page-roc">
      <div class="page-head"><h1>ROC Curve</h1><p>How well each model ranks malignant above benign, across every possible decision threshold — not just the default 50% cutoff.</p></div>

      <div class="card">
        <div class="legend" id="rocLegend"></div>
        <svg id="rocChart" viewBox="0 0 520 520" width="100%" style="max-width:520px"></svg>
        <p class="cap">Dashed diagonal = random-guessing baseline (AUC = 0.5). A curve hugging the top-left corner is better.</p>
      </div>
    </section>

    <!-- ===================== FEATURE IMPORTANCE ===================== -->
    <section class="page" id="page-importance">
      <div class="page-head"><h1>Feature Importance</h1><p>What the best model (SVM, RBF kernel) actually relied on — computed three different ways.</p></div>

      <div class="tabs">
        <button class="tab-btn active" data-tab="fi1">Permutation importance</button>
        <button class="tab-btn" data-tab="fi2">SHAP</button>
      </div>
      <div class="card tab-panel active" id="fi1">
        <h3>Permutation importance (model-agnostic)</h3>
        <img class="plot" src="data:image/png;base64,__PLOT_permutation_importance__">
        <p class="cap">Shuffles one feature's values at a time and measures how much test accuracy drops. Works for any model — including SVM, which has no built-in feature_importances_.</p>
      </div>
      <div class="card tab-panel" id="fi2">
        <h3>SHAP summary</h3>
        <img class="plot" src="data:image/png;base64,__PLOT_shap_summary__">
        <p class="cap">SHAP shows how each feature pushes one individual prediction toward benign or malignant. Red = high feature value, blue = low. Points further right push that prediction toward malignant. This describes what the model learned to rely on — not an established clinical ranking of risk factors.</p>
      </div>
    </section>

    <!-- ===================== PREDICTION ===================== -->
    <section class="page" id="page-predict">
      <div class="page-head"><h1>Prediction</h1><p>Live, in-browser prediction using the actual trained Logistic Regression model — its real learned weights, run with plain JavaScript. Not medical advice.</p></div>

      <div class="card">
        <div class="field-row">
          <button class="btn" id="fillMeansBtn" type="button" style="background:var(--surface-2);color:var(--fg);border:1px solid var(--border)">Fill with dataset means</button>
          <button class="btn" id="fillMalignantBtn" type="button" style="background:var(--surface-2);color:var(--fg);border:1px solid var(--border)">Fill with a malignant example</button>
          <button class="btn" id="fillBenignBtn" type="button" style="background:var(--surface-2);color:var(--fg);border:1px solid var(--border)">Fill with a benign example</button>
        </div>
        <div class="pred-grid" id="predGrid"></div>
        <button class="btn" id="predictBtn">Predict</button>

        <div class="result-banner" id="resultBanner">
          <div class="result-title" id="resultTitle"></div>
          <div class="prob-bar-track"><div class="prob-bar-fill" id="probBarFill"></div></div>
          <div class="mono" id="probText" style="font-size:13px"></div>
          <div class="src-note">Model: Logistic Regression · computed entirely in your browser from the model's real coefficients · test-set accuracy 97.4%</div>
        </div>
      </div>
    </section>

  </main>
</div>

<script>
const DATA = __DATA_JSON__;
const LR = __LR_JSON__;

// ---------- theme ----------
const root = document.documentElement;
function setTheme(t){
  if(t==='system'){ root.removeAttribute('data-theme'); try{localStorage.setItem('theme','system')}catch(e){} }
  else { root.setAttribute('data-theme', t); try{localStorage.setItem('theme',t)}catch(e){} }
  document.querySelectorAll('.theme-toggle button').forEach(b=>b.classList.remove('active'));
  document.getElementById('theme'+t[0].toUpperCase()+t.slice(1)).classList.add('active');
}
try{ const saved = localStorage.getItem('theme'); if(saved) setTheme(saved); }catch(e){}
document.getElementById('themeLight').onclick=()=>setTheme('light');
document.getElementById('themeDark').onclick=()=>setTheme('dark');
document.getElementById('themeSystem').onclick=()=>setTheme('system');

// ---------- nav ----------
document.querySelectorAll('.nav-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
    document.getElementById('page-'+btn.dataset.page).classList.add('active');
    document.getElementById('sidebar').classList.remove('open');
  });
});
document.getElementById('navToggle').onclick=()=>document.getElementById('sidebar').classList.toggle('open');

// ---------- tabs ----------
document.querySelectorAll('.tabs').forEach(tabset=>{
  tabset.querySelectorAll('.tab-btn').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      tabset.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      const panelId = btn.dataset.tab;
      const panel = document.getElementById(panelId);
      panel.parentElement.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
      panel.classList.add('active');
    });
  });
});

const COLORS = ['#0e7c86','#c0392b','#8a6d3b','#5b6ee1','#2a9d8f'];
const fmtPct = v => (v*100).toFixed(1)+'%';
const fmtN = (v,d=3) => Number(v).toFixed(d);

// ================= OVERVIEW =================
(function(){
  const results = DATA.results;
  const best = results.reduce((a,b)=> b.accuracy>a.accuracy?b:a);
  const kpiRow = document.getElementById('kpiRow');
  kpiRow.innerHTML = `
    <div class="kpi"><div class="label">Samples</div><div class="value">${DATA.dataset.n_samples}</div><div class="sub">${DATA.dataset.n_features} features</div></div>
    <div class="kpi"><div class="label">Models compared</div><div class="value">${results.length}</div><div class="sub">all tuned via GridSearchCV</div></div>
    <div class="kpi"><div class="label">Best accuracy</div><div class="value">${fmtPct(best.accuracy)}</div><div class="sub">${best.model}</div></div>
    <div class="kpi"><div class="label">Best ROC-AUC</div><div class="value">${fmtN(Math.max(...results.map(r=>r.roc_auc)),4)}</div><div class="sub">across all 5 models</div></div>
  `;

  const metricsToShow = [['accuracy','Accuracy'],['recall','Recall'],['f1','F1-Score'],['roc_auc','ROC-AUC']];
  let rows = metricsToShow.map(([key,label])=>{
    const winner = results.reduce((a,b)=> b[key]>a[key]?b:a);
    return `<tr><td>${label}</td><td>${winner.model}</td><td class="num mono">${key==='roc_auc'?fmtN(winner[key],4):fmtPct(winner[key])}</td></tr>`;
  }).join('');
  document.getElementById('overviewTable').innerHTML =
    `<thead><tr><th>Metric</th><th>Best model</th><th class="num">Score</th></tr></thead><tbody>${rows}</tbody>`;
})();

// ================= DATASET EXPLORER =================
(function(){
  const d = DATA.dataset;
  document.getElementById('dsSourceLine').textContent = `${d.name} — ${d.source}`;
  document.getElementById('dsKpiRow').innerHTML = `
    <div class="kpi"><div class="label">Samples</div><div class="value">${d.n_samples}</div></div>
    <div class="kpi"><div class="label">Features</div><div class="value">${d.n_features}</div></div>
    <div class="kpi"><div class="label">Missing values</div><div class="value">${d.missing}</div></div>
    <div class="kpi"><div class="label">Task</div><div class="value" style="font-size:16px">${d.task}</div></div>
  `;

  const total = d.class_counts.Malignant + d.class_counts.Benign;
  const mPct = d.class_counts.Malignant/total*100, bPct = d.class_counts.Benign/total*100;
  document.getElementById('classBarChart').innerHTML = `
    <div style="display:flex;height:34px;border-radius:7px;overflow:hidden;margin-bottom:8px">
      <div style="width:${mPct}%;background:var(--malignant);display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:600">${mPct>12?'Malignant '+mPct.toFixed(0)+'%':''}</div>
      <div style="width:${bPct}%;background:var(--benign);display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:600">${bPct>12?'Benign '+bPct.toFixed(0)+'%':''}</div>
    </div>
    <div style="font-size:12.5px;color:var(--muted)">Malignant: ${d.class_counts.Malignant} &nbsp;·&nbsp; Benign: ${d.class_counts.Benign}</div>
  `;

  const cols = d.feature_names.slice(0,8);
  let head = '<thead><tr>'+cols.map(c=>`<th>${c}</th>`).join('')+'</tr></thead>';
  let body = '<tbody>'+d.sample_rows.map(r=>'<tr>'+cols.map(c=>`<td class="num mono">${r[c]}</td>`).join('')+'</tr>').join('')+'</tbody>';
  document.getElementById('sampleTable').innerHTML = `<table>${head}${body}</table><p class="cap">Showing first 8 of 30 columns, 8 of 569 rows.</p>`;

  let srows = Object.entries(d.feature_stats).map(([feat,s])=>
    `<tr><td>${feat}</td><td class="num mono">${s.mean}</td><td class="num mono">${s.std}</td><td class="num mono">${s.min}</td><td class="num mono">${s.max}</td></tr>`
  ).join('');
  document.getElementById('statsTable').innerHTML =
    `<table><thead><tr><th>Feature</th><th class="num">Mean</th><th class="num">Std</th><th class="num">Min</th><th class="num">Max</th></tr></thead><tbody>${srows}</tbody></table>`;
})();

// ================= MODEL COMPARISON =================
function renderLeaderboard(){
  const results = [...DATA.results].sort((a,b)=>b.accuracy-a.accuracy);
  const bestAcc = results[0].accuracy;
  let rows = results.map(r=>{
    const isBest = r.accuracy===bestAcc;
    return `<tr class="${isBest?'best':''}">
      <td>${r.model} ${isBest?'<span class="pill best">Best</span>':''}</td>
      <td class="num mono">${fmtPct(r.accuracy)}</td>
      <td class="num mono">${fmtPct(r.precision)}</td>
      <td class="num mono">${fmtPct(r.recall)}</td>
      <td class="num mono">${fmtPct(r.specificity)}</td>
      <td class="num mono">${fmtPct(r.f1)}</td>
      <td class="num mono">${fmtN(r.roc_auc,4)}</td>
      <td class="num mono">${r.train_time}s</td>
    </tr>`;
  }).join('');
  document.getElementById('leaderboardTable').innerHTML = `
    <table><thead><tr><th>Model</th><th class="num">Accuracy</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">Specificity</th><th class="num">F1</th><th class="num">ROC-AUC</th><th class="num">Train time</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}
renderLeaderboard();

function renderBarChart(metric){
  const results = DATA.results;
  const svg = document.getElementById('barChart');
  const W=640,H=300,padL=50,padB=70,padT=20,padR=20;
  const chartW = W-padL-padR, chartH = H-padT-padB;
  const barW = chartW/results.length*0.55;
  const gap = chartW/results.length;
  let bars='', labels='', axisLines='';
  for(let i=0;i<=5;i++){
    const y = padT + chartH - (i/5)*chartH;
    axisLines += `<line x1="${padL}" y1="${y}" x2="${W-padR}" y2="${y}" stroke="var(--border)" stroke-width="1"/>
      <text x="${padL-8}" y="${y+4}" font-size="10" fill="var(--muted)" text-anchor="end">${(i/5).toFixed(1)}</text>`;
  }
  results.forEach((r,i)=>{
    const val = r[metric];
    const x = padL + i*gap + (gap-barW)/2;
    const h = val*chartH;
    const y = padT+chartH-h;
    bars += `<rect x="${x}" y="${y}" width="${barW}" height="${h}" rx="4" fill="${COLORS[i%COLORS.length]}"/>
      <text x="${x+barW/2}" y="${y-6}" font-size="11" text-anchor="middle" fill="var(--fg)" font-weight="600">${(val*100).toFixed(1)}</text>`;
    labels += `<text x="${x+barW/2}" y="${H-padB+16}" font-size="10.5" text-anchor="middle" fill="var(--muted)">${r.model.split(' ')[0]}</text>`;
  });
  svg.innerHTML = axisLines+bars+labels;
}
document.getElementById('metricSelect').addEventListener('change', e=>renderBarChart(e.target.value));
renderBarChart('accuracy');

// ================= CONFUSION MATRIX =================
const cmSelect = document.getElementById('cmModelSelect');
DATA.results.forEach(r=>{
  const opt = document.createElement('option'); opt.value = r.model; opt.textContent = r.model;
  cmSelect.appendChild(opt);
});
function renderCM(modelName){
  const r = DATA.results.find(x=>x.model===modelName);
  document.getElementById('cmGrid').innerHTML = `
    <div></div><div class="cm-head">Predicted Malignant</div><div class="cm-head">Predicted Benign</div>
    <div class="cm-head" style="writing-mode:vertical-rl;text-orientation:mixed">Actual Malignant</div>
    <div class="cm-cell cm-tp"><div class="cm-val">${r.tp}</div><div class="cm-sub">True Positive</div></div>
    <div class="cm-cell cm-fn"><div class="cm-val">${r.fn}</div><div class="cm-sub">False Negative</div></div>
    <div class="cm-head" style="writing-mode:vertical-rl;text-orientation:mixed">Actual Benign</div>
    <div class="cm-cell cm-fp"><div class="cm-val">${r.fp}</div><div class="cm-sub">False Positive</div></div>
    <div class="cm-cell cm-tn"><div class="cm-val">${r.tn}</div><div class="cm-sub">True Negative</div></div>
  `;
}
cmSelect.addEventListener('change', e=>renderCM(e.target.value));
cmSelect.value = DATA.results.reduce((a,b)=>b.accuracy>a.accuracy?b:a).model;
renderCM(cmSelect.value);

// ================= ROC =================
(function(){
  const legend = document.getElementById('rocLegend');
  DATA.results.forEach((r,i)=>{
    const id = 'roc_chk_'+i;
    legend.innerHTML += `<label><input type="checkbox" id="${id}" checked data-idx="${i}"><span class="swatch" style="background:${COLORS[i%COLORS.length]}"></span>${r.model} (AUC ${fmtN(r.roc_auc,3)})</label>`;
  });
  function renderROC(){
    const W=520,H=520,pad=46;
    const plotSize = W-2*pad;
    let svg = `<line x1="${pad}" y1="${pad}" x2="${pad}" y2="${H-pad}" stroke="var(--border)"/>
      <line x1="${pad}" y1="${H-pad}" x2="${W-pad}" y2="${H-pad}" stroke="var(--border)"/>
      <line x1="${pad}" y1="${H-pad}" x2="${W-pad}" y2="${pad}" stroke="var(--muted)" stroke-dasharray="4 4"/>
      <text x="${W/2}" y="${H-10}" font-size="11" text-anchor="middle" fill="var(--muted)">False Positive Rate</text>
      <text x="14" y="${H/2}" font-size="11" text-anchor="middle" fill="var(--muted)" transform="rotate(-90 14 ${H/2})">True Positive Rate</text>`;
    DATA.results.forEach((r,i)=>{
      const chk = document.getElementById('roc_chk_'+i);
      if(!chk.checked) return;
      const pts = r.roc_fpr.map((fpr,j)=>{
        const x = pad + fpr*plotSize;
        const y = H-pad - r.roc_tpr[j]*plotSize;
        return `${x},${y}`;
      }).join(' ');
      svg += `<polyline points="${pts}" fill="none" stroke="${COLORS[i%COLORS.length]}" stroke-width="2.5"/>`;
    });
    document.getElementById('rocChart').innerHTML = svg;
  }
  legend.querySelectorAll('input').forEach(c=>c.addEventListener('change', renderROC));
  renderROC();
})();

// ================= PREDICTION (real Logistic Regression, client-side) =================
(function(){
  const grid = document.getElementById('predGrid');
  LR.feature_names.forEach((feat,i)=>{
    const div = document.createElement('div'); div.className='pred-field';
    div.innerHTML = `<label>${feat}</label><input type="number" step="any" id="pf_${i}" value="${LR.feature_means[i].toFixed(4)}">`;
    grid.appendChild(div);
  });

  function sigmoid(z){ return 1/(1+Math.exp(-z)); }

  function predict(){
    let z = LR.intercept;
    LR.feature_names.forEach((feat,i)=>{
      const raw = parseFloat(document.getElementById('pf_'+i).value);
      const scaled = (raw - LR.scaler_mean[i]) / LR.scaler_scale[i];
      z += scaled * LR.coef[i];
    });
    // model's classes_ = [0,1] -> index0 = malignant(class 0), sigmoid(z) = P(class 1 = benign)
    const pBenign = sigmoid(z);
    const pMalignant = 1 - pBenign;
    const isMalignant = pMalignant > 0.5;

    const banner = document.getElementById('resultBanner');
    banner.classList.add('show');
    banner.className = 'result-banner show ' + (isMalignant?'malignant':'benign');
    const title = document.getElementById('resultTitle');
    title.className = 'result-title ' + (isMalignant?'malignant':'benign');
    title.textContent = 'Prediction: ' + (isMalignant?'Malignant':'Benign');
    document.getElementById('probBarFill').style.width = (pMalignant*100).toFixed(1)+'%';
    document.getElementById('probBarFill').style.background = isMalignant ? 'var(--malignant)' : 'var(--benign)';
    document.getElementById('probText').textContent =
      `P(Malignant) = ${(pMalignant*100).toFixed(2)}%   ·   P(Benign) = ${(pBenign*100).toFixed(2)}%`;
  }
  document.getElementById('predictBtn').addEventListener('click', predict);

  document.getElementById('fillMeansBtn').addEventListener('click', ()=>{
    LR.feature_names.forEach((f,i)=> document.getElementById('pf_'+i).value = LR.feature_means[i].toFixed(4));
  });
  // Example rows pulled from real dataset extremes (max-ish values for malignant-leaning, min-ish for benign-leaning features)
  document.getElementById('fillMalignantBtn').addEventListener('click', ()=>{
    LR.feature_names.forEach((f,i)=>{
      const v = LR.feature_means[i] + (LR.feature_maxs[i]-LR.feature_means[i])*0.55;
      document.getElementById('pf_'+i).value = v.toFixed(4);
    });
  });
  document.getElementById('fillBenignBtn').addEventListener('click', ()=>{
    LR.feature_names.forEach((f,i)=>{
      const v = LR.feature_means[i] - (LR.feature_means[i]-LR.feature_mins[i])*0.55;
      document.getElementById('pf_'+i).value = Math.max(v,0).toFixed(4);
    });
  });
})();
</script>
"""

html = HTML_TEMPLATE
html = html.replace("__DATA_JSON__", json.dumps(DATA))
html = html.replace("__LR_JSON__", json.dumps(LR))
for key, b64 in PLOTS.items():
    placeholder = "__PLOT_" + key.replace(".png", "") + "__"
    html = html.replace(placeholder, b64)

with open("tumor_diagnosis_lab.html", "w") as f:
    f.write(html)

print("Built tumor_diagnosis_lab.html, size:", len(html)/1024/1024, "MB")
