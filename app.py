"""
app.py - Breast Cancer ML Dashboard (Streamlit)

Run with:  streamlit run app.py
Needs the results saved by:  python run_all_experiments.py   (run once)

Pages: Overview, Dataset Explorer, Data Insights, Model Comparison,
Model Details, Predict, About.  The dashboard only READS saved results
(and the saved models) - it never retrains on startup.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.data_loader import load_dataset, available_datasets
from src.evaluation import metric_definitions
from src.preprocessing import split_data
from src.training import MODELS_DIR

ROOT = Path(__file__).resolve().parent
EXP = ROOT / "experiments"
PLOTS = EXP / "plots"

NAVY, DEEP, TEAL, PINK, BLUE, AMBER, GREY = "#0B1F3A", "#17375E", "#12A7A0", "#E0527F", "#2F80C0", "#E9B44C", "#6B7C93"
MODEL_COLORS = {"Logistic Regression": TEAL, "K-Nearest Neighbors": BLUE, "Decision Tree": AMBER,
                "Random Forest": DEEP, "SVM (RBF Kernel)": PINK}

st.set_page_config(page_title="Breast Cancer ML Dashboard", layout="wide", page_icon="🩺")

# ----------------------------------------------------------------- styling
st.markdown(f"""
<style>
  #MainMenu, footer, header [data-testid="stToolbar"] {{visibility: hidden;}}
  .stApp {{background:#F4F8FA;}}
  .block-container {{padding-top:1.6rem; padding-bottom:2rem; max-width:1250px;}}
  [data-testid="stSidebar"] {{background:{NAVY};}}
  [data-testid="stSidebar"] * {{color:#E8F1F5 !important;}}
  [data-testid="stSidebar"] .stRadio label {{padding:6px 4px; font-size:0.95rem;}}
  h1, h2, h3 {{color:{NAVY}; letter-spacing:-0.01em;}}
  h1 {{font-size:1.9rem !important; margin-bottom:0.1rem;}}
  h3 {{font-size:1.1rem !important; margin-top:0.6rem;}}
  .hint {{color:{GREY}; font-size:0.85rem; margin:-0.2rem 0 0.7rem 0;}}
  .page-sub {{color:{GREY}; font-size:0.95rem; margin-bottom:1.1rem;}}
  .card {{background:#fff; border:1px solid #E1ECF0; border-radius:12px; padding:14px 16px;
          box-shadow:0 1px 3px rgba(11,31,58,0.05);}}
  .kpi-label {{color:{GREY}; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.05em;}}
  .kpi-value {{color:{NAVY}; font-size:1.7rem; font-weight:700; line-height:1.25;}}
  .kpi-note {{color:{GREY}; font-size:0.78rem;}}
  .callout {{background:#fff; border-left:4px solid {TEAL}; border-radius:8px; padding:12px 16px;
             color:{NAVY}; font-size:0.93rem; box-shadow:0 1px 3px rgba(11,31,58,0.05);}}
  .callout.warn {{border-left-color:{PINK};}}
  .pill {{display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.75rem; font-weight:600;
          background:#E3F5F4; color:#0B7C77;}}
  .pill.prog {{background:#FCE6EE; color:#B33A60;}}
  div[data-testid="stMetric"] {{background:#fff; border:1px solid #E1ECF0; border-radius:12px; padding:10px 14px;}}
  .stTabs [data-baseweb="tab"] {{font-weight:600;}}
  .stTabs [aria-selected="true"] {{color:{TEAL} !important;}}
</style>
""", unsafe_allow_html=True)


def kpi(label, value, note=""):
    st.markdown(f'<div class="card"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>',
                unsafe_allow_html=True)


def hint(text):
    st.markdown(f'<div class="hint">{text}</div>', unsafe_allow_html=True)


def header(title, sub):
    st.markdown(f"# {title}")
    st.markdown(f'<div class="page-sub">{sub}</div>', unsafe_allow_html=True)


def style(fig, h=380):
    fig.update_layout(template="plotly_white", height=h, margin=dict(l=10, r=10, t=40, b=10),
                      font=dict(family="Inter, Segoe UI, sans-serif", color=NAVY, size=13),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.2))
    return fig


# ----------------------------------------------------------------- data
@st.cache_data
def load_results():
    if not (EXP / "results.csv").exists():
        return None, None
    return pd.read_csv(EXP / "results.csv"), json.load(open(EXP / "results_full.json"))


@st.cache_data
def get_dataset(short):
    return load_dataset(short)


@st.cache_resource
def get_model(filename):
    return joblib.load(MODELS_DIR / filename)


df, full = load_results()
if df is None:
    st.error("No results found. Run `python run_all_experiments.py` first.")
    st.stop()

DS = [d for d in available_datasets() if d in set(df["dataset"])]
META = {d: get_dataset(d) for d in DS}
NAMES = {d: META[d]["name"] for d in DS}
MODELS = list(df["model"].unique())


def best_row(ds, by="accuracy"):
    sub = df[df["dataset"] == ds]
    return sub.loc[sub[by].idxmax()]


def pick_dataset(key, label="Dataset"):
    return st.selectbox(label, DS, format_func=lambda d: NAMES[d], key=key)


# ----------------------------------------------------------------- sidebar
st.sidebar.markdown("## 🩺 Breast Cancer ML")
st.sidebar.caption("Comparing 5 algorithms on 5 breast-cancer datasets")
PAGES = ["Overview", "Dataset Explorer", "Data Insights", "Model Comparison", "Model Details", "Predict", "About"]
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption("Educational prototype. Not a medical diagnostic tool.")

# =================================================================== OVERVIEW
if page == "Overview":
    header("Overview", "5 datasets, 5 algorithms, one fair comparison. Start here for the big picture.")
    c = st.columns(4)
    with c[0]: kpi("Datasets", len(DS), "breast-cancer sources")
    with c[1]: kpi("Algorithms", len(MODELS), "scikit-learn models")
    with c[2]: kpi("Experiments", len(df), "tuned + tested")
    top = df.loc[df["accuracy"].idxmax()]
    with c[3]: kpi("Top accuracy", f"{top['accuracy']*100:.1f}%", f"{top['model']} on {META[top['dataset']]['short_name'].upper()}")

    st.markdown("### Best model per dataset")
    hint("Each row shows the highest-accuracy model on that dataset's held-out test set.")
    rows = []
    for d in DS:
        b = best_row(d)
        rows.append({"Dataset": NAMES[d], "Task": META[d]["task"], "Samples": META[d]["n_samples"],
                     "Features": META[d]["n_features"], "Best model": b["model"],
                     "Accuracy": b["accuracy"], "Recall": b["recall"], "ROC-AUC": b["roc_auc"]})
    tbl = pd.DataFrame(rows)
    st.dataframe(tbl, hide_index=True, use_container_width=True,
                 column_config={"Accuracy": st.column_config.ProgressColumn(format="%.3f", min_value=0, max_value=1),
                                "Recall": st.column_config.ProgressColumn(format="%.3f", min_value=0, max_value=1),
                                "ROC-AUC": st.column_config.NumberColumn(format="%.3f")})

    st.markdown("### Performance across all datasets")
    metric = st.radio("Metric", ["accuracy", "recall", "f1", "roc_auc"], horizontal=True,
                      format_func=lambda m: {"accuracy": "Accuracy", "recall": "Recall", "f1": "F1", "roc_auc": "ROC-AUC"}[m])
    hint("Darker teal = better. Compare columns to see which algorithm suits which dataset.")
    piv = df.pivot(index="dataset", columns="model", values=metric).loc[DS, MODELS]
    fig = go.Figure(go.Heatmap(z=piv.values, x=MODELS, y=[NAMES[d] for d in DS], zmin=0, zmax=1,
                               colorscale=[[0, "#F4F8FA"], [0.5, "#9FD9D5"], [1, TEAL]],
                               text=np.round(piv.values, 3), texttemplate="%{text}", showscale=False))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style(fig, 330), use_container_width=True)

    diag = [d for d in DS if META[d]["task"] == "Diagnosis"]
    prog = [d for d in DS if META[d]["task"] == "Prognosis"]
    if diag and prog:
        ad = np.mean([best_row(d)["accuracy"] for d in diag])
        ap = np.mean([best_row(d)["accuracy"] for d in prog])
        ar = np.mean([best_row(d)["recall"] for d in prog])
        st.markdown(
            f'<div class="callout"><b>Key takeaway.</b> Diagnosis datasets (is the tumor malignant?) are much easier: '
            f'best accuracy averages <b>{ad*100:.0f}%</b>. Prognosis datasets (what happens after treatment?) are harder: '
            f'best accuracy averages <b>{ap*100:.0f}%</b>, and the average recall for the adverse class is only '
            f'<b>{ar*100:.0f}%</b>. Which algorithm wins changes from dataset to dataset.</div>', unsafe_allow_html=True)

# =================================================================== DATASET EXPLORER
elif page == "Dataset Explorer":
    header("Dataset Explorer", "Pick a dataset to see what it contains, where it comes from and how balanced it is.")
    d = pick_dataset("ds_explorer")
    m = META[d]
    pill = "pill" if m["task"] == "Diagnosis" else "pill prog"
    st.markdown(f'<span class="{pill}">{m["task"]}</span> &nbsp; <span style="color:{GREY}">{m["source"]}</span>',
                unsafe_allow_html=True)
    st.markdown("")
    c = st.columns(5)
    adverse = (m["y"] == 0).mean()
    with c[0]: kpi("Samples", m["n_samples"])
    with c[1]: kpi("Features", m["n_features"], m["feature_types"])
    with c[2]: kpi("Missing values", m["missing_values"])
    with c[3]: kpi("Repeated rows", m["duplicates"], "identical feature + label")
    with c[4]: kpi("Adverse class", f"{adverse*100:.0f}%", m["target_names"][0])
    st.markdown("")
    st.markdown(f'<div class="callout">{m["description"]}'
                f'{"<br><b>Note:</b> " + m["note"] if m["note"] else ""}</div>', unsafe_allow_html=True)
    if m["duplicates"] > 20:
        st.markdown('<div class="callout warn" style="margin-top:8px"><b>Heads-up:</b> many repeated rows can sit in both '
                    'train and test sets, which makes scores look slightly better than they would on new patients.</div>',
                    unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["Class balance", "Data preview", "Feature summary"])
    with t1:
        hint("How many samples fall in each outcome. Strong imbalance makes accuracy misleading.")
        counts = m["y"].map(m["target_names"]).value_counts()
        fig = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color=[PINK if i == m["target_names"][0] else TEAL for i in counts.index],
                               text=counts.values, textposition="outside"))
        fig.update_yaxes(title="Samples")
        st.plotly_chart(style(fig, 330), use_container_width=True)
    with t2:
        hint("First 15 rows as the models see them (after encoding).")
        st.dataframe(pd.concat([m["X"], m["y"].map(m["target_names"]).rename("outcome")], axis=1).head(15),
                     use_container_width=True)
    with t3:
        hint("Spread of each feature: mean, min and max.")
        st.dataframe(m["X"].describe().T[["mean", "std", "min", "max"]].round(3), use_container_width=True)

# =================================================================== DATA INSIGHTS
elif page == "Data Insights":
    header("Data Insights", "Which features relate to the outcome, and can the classes be told apart?")
    d = pick_dataset("ds_insights")
    m = META[d]; X, y, tn = m["X"], m["y"], m["target_names"]
    t1, t2, t3 = st.tabs(["Feature strength", "Feature distribution", "2D view (PCA)"])
    with t1:
        hint("How strongly each feature moves with the adverse outcome (absolute correlation, 0 to 1). Association, not cause.")
        corr = X.apply(lambda col: abs(col.corr(1 - y))).dropna().sort_values().tail(12)
        fig = go.Figure(go.Bar(x=corr.values, y=corr.index, orientation="h", marker_color=TEAL,
                               text=np.round(corr.values, 2), textposition="outside"))
        fig.update_xaxes(range=[0, min(1, corr.max() * 1.2)], title="|correlation|")
        st.plotly_chart(style(fig, 420), use_container_width=True)
    with t2:
        hint("Pick a feature. If the two colors barely overlap, that feature separates the classes well.")
        top_feats = X.apply(lambda col: abs(col.corr(1 - y))).sort_values(ascending=False).index.tolist()
        f = st.selectbox("Feature", top_feats, key="insight_feat")
        plot_df = pd.DataFrame({f: X[f], "Outcome": y.map(tn)})
        fig = px.histogram(plot_df.dropna(), x=f, color="Outcome", barmode="overlay", opacity=0.65, nbins=30,
                           color_discrete_map={tn[0]: PINK, tn[1]: TEAL})
        st.plotly_chart(style(fig, 380), use_container_width=True)
    with t3:
        hint("All features squeezed into 2 axes. Separated colors mean the classes are fairly easy to split.")
        Z = StandardScaler().fit_transform(X.fillna(X.median()))
        p = PCA(n_components=2).fit(Z); P = p.transform(Z)
        fig = px.scatter(x=P[:, 0], y=P[:, 1], color=y.map(tn), opacity=0.7,
                         color_discrete_map={tn[0]: PINK, tn[1]: TEAL},
                         labels={"x": f"PC1 ({p.explained_variance_ratio_[0]*100:.0f}% of variance)",
                                 "y": f"PC2 ({p.explained_variance_ratio_[1]*100:.0f}% of variance)", "color": "Outcome"})
        st.plotly_chart(style(fig, 420), use_container_width=True)

# =================================================================== MODEL COMPARISON
elif page == "Model Comparison":
    header("Model Comparison", "How the 5 algorithms perform on the same held-out test set.")
    d = pick_dataset("ds_compare")
    sub = df[df["dataset"] == d].set_index("model").loc[MODELS]
    ba, br = best_row(d, "accuracy"), best_row(d, "recall")
    c = st.columns(3)
    with c[0]: kpi("Best accuracy", f"{ba['accuracy']*100:.1f}%", ba["model"])
    with c[1]: kpi("Best recall", f"{br['recall']*100:.1f}%", br["model"])
    with c[2]: kpi("Best ROC-AUC", f"{sub['roc_auc'].max():.3f}", sub["roc_auc"].idxmax())
    st.markdown("### Scores by model")
    hint("Recall = share of adverse cases caught. In medicine, missing a case is the costliest mistake.")
    mets = {"accuracy": "Accuracy", "precision": "Precision", "recall": "Recall", "f1": "F1", "roc_auc": "ROC-AUC"}
    chosen = st.multiselect("Metrics", list(mets), default=["accuracy", "recall", "f1", "roc_auc"], format_func=lambda k: mets[k])
    long = sub[chosen].reset_index().melt(id_vars="model", var_name="metric", value_name="score")
    long["metric"] = long["metric"].map(mets)
    fig = px.bar(long, x="model", y="score", color="metric", barmode="group",
                 color_discrete_sequence=[NAVY, TEAL, BLUE, PINK, AMBER])
    fig.update_yaxes(range=[0, 1.05], title="Score"); fig.update_xaxes(title="")
    st.plotly_chart(style(fig, 400), use_container_width=True)
    st.markdown("### Full table")
    st.dataframe(sub[["accuracy", "precision", "recall", "specificity", "f1", "roc_auc", "cv_mean_accuracy"]]
                 .rename(columns={"cv_mean_accuracy": "CV accuracy"}).round(3), use_container_width=True)
    hint("CV accuracy = average score during tuning on the training data. Compare with Accuracy (test) to spot overfitting.")

# =================================================================== MODEL DETAILS
elif page == "Model Details":
    header("Model Details", "Look inside one model: its mistakes, its ranking ability and what it relies on.")
    c = st.columns(2)
    with c[0]: d = pick_dataset("ds_detail")
    best_name = best_row(d)["model"]
    with c[1]:
        mdl = st.selectbox("Model", MODELS, index=MODELS.index(best_name), key=f"mdl_{d}",
                           format_func=lambda x: x + ("  (best)" if x == best_name else ""))
    r = full[d][mdl]; tn = META[d]["target_names"]
    c = st.columns(4)
    with c[0]: kpi("Accuracy", f"{r['accuracy']*100:.1f}%")
    with c[1]: kpi("Recall", f"{r['recall']*100:.1f}%", f"{tn[0]} cases caught")
    with c[2]: kpi("Precision", f"{r['precision']*100:.1f}%")
    with c[3]: kpi("ROC-AUC", f"{r['roc_auc']:.3f}")
    t1, t2, t3 = st.tabs(["Confusion matrix", "ROC curve", "Important features"])
    with t1:
        hint("Rows = what was true, columns = what the model said. Top-right = missed adverse cases (the costly error).")
        names = [tn[0], tn[1]]
        z = [[r["tp"], r["fn"]], [r["fp"], r["tn"]]]
        fig = go.Figure(go.Heatmap(z=z, x=[f"Predicted: {n}" for n in names], y=[f"Actual: {n}" for n in names],
                                   colorscale=[[0, "#F4F8FA"], [1, TEAL]], showscale=False,
                                   text=z, texttemplate="<b>%{text}</b>", textfont=dict(size=26)))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(style(fig, 360), use_container_width=True)
        st.caption(f"Missed adverse cases: {r['fn']}   |   False alarms: {r['fp']}")
    with t2:
        hint("Curve closer to the top-left corner = better at ranking adverse cases above others. Dotted line = guessing.")
        fig = go.Figure()
        for mm in MODELS:
            rr = full[d][mm]
            fig.add_trace(go.Scatter(x=rr["roc_fpr"], y=rr["roc_tpr"], mode="lines", name=mm,
                                     line=dict(color=MODEL_COLORS.get(mm, GREY), width=4 if mm == mdl else 1.4),
                                     opacity=1 if mm == mdl else 0.45))
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(dash="dot", color=GREY), showlegend=False))
        fig.update_xaxes(title="False positive rate"); fig.update_yaxes(title="True positive rate")
        st.plotly_chart(style(fig, 420), use_container_width=True)
    with t3:
        ex = json.load(open(PLOTS / d / "explainability.json"))
        hint(f"Computed for the best model ({ex['best_model']}). Shows how much accuracy drops when a feature is shuffled.")
        imp = pd.Series(ex["permutation_importance"]).sort_values().tail(10)
        fig = go.Figure(go.Bar(x=imp.values, y=imp.index, orientation="h", marker_color=BLUE))
        fig.update_xaxes(title="Accuracy drop when shuffled")
        st.plotly_chart(style(fig, 400), use_container_width=True)
        st.caption("These show what the model relied on, not clinical risk factors.")
        shap_png = PLOTS / d / "shap_summary.png"
        if shap_png.exists():
            with st.expander("Advanced: SHAP summary"):
                st.image(str(shap_png))

# =================================================================== PREDICT
elif page == "Predict":
    header("Predict", "Try a model on one patient record. A prediction is an estimate, not a diagnosis.")
    c = st.columns(2)
    with c[0]: d = pick_dataset("ds_predict")
    best_name = best_row(d)["model"]
    with c[1]:
        mdl = st.selectbox("Model", MODELS, index=MODELS.index(best_name), key=f"pm_{d}",
                           format_func=lambda x: x + ("  (best)" if x == best_name else ""))
    m = META[d]; X, y, tn = m["X"], m["y"], m["target_names"]
    pipe = get_model(full[d][mdl]["model_file"])
    _, X_test, _, y_test = split_data(X, y)

    st.markdown("### 1. Choose the input values")
    hint("Start from a real test-set patient (the model never saw these) or type your own values.")
    pick = st.selectbox("Load a real test patient", ["- keep current values -"] + [int(i) for i in X_test.index],
                        key=f"pick_{d}")
    keys = {f: f"{d}__{f}" for f in X.columns}
    if st.session_state.get(f"last_pick_{d}") != pick:
        st.session_state[f"last_pick_{d}"] = pick
        if pick != "- keep current values -":
            row = X.loc[pick]
            for f in X.columns:
                v = row[f]
                st.session_state[keys[f]] = float(X[f].median()) if pd.isna(v) else float(v)
            st.session_state[f"true_{d}"] = tn[int(y.loc[pick])]
        else:
            st.session_state.pop(f"true_{d}", None)
    cols = st.columns(3)
    vals = {}
    for i, f in enumerate(X.columns):
        lo, hi = float(X[f].min()), float(X[f].max())
        span = hi - lo if hi > lo else 1.0
        if keys[f] not in st.session_state:
            st.session_state[keys[f]] = float(X[f].median())
        vals[f] = cols[i % 3].number_input(f, min_value=lo - span, max_value=hi + span,
                                           step=span / 100, format="%.4g", key=keys[f])
    if m["short_name"] == "ljubljana":
        st.caption("Tip: groups like breast_left / breast_right are 0-or-1 flags. Load a real patient to start from a consistent record.")

    st.markdown("### 2. Prediction")
    if st.button("Predict", type="primary"):
        row = pd.DataFrame([vals])[X.columns]
        p_adv = float(pipe.predict_proba(row)[0][list(pipe.classes_).index(0)])
        label = tn[0] if p_adv >= 0.5 else tn[1]
        color = PINK if p_adv >= 0.5 else TEAL
        c = st.columns([1, 1])
        with c[0]:
            st.markdown(f'<div class="card"><div class="kpi-label">Model says</div>'
                        f'<div class="kpi-value" style="color:{color}">{label}</div>'
                        f'<div class="kpi-note">{mdl}</div></div>', unsafe_allow_html=True)
        with c[1]:
            kpi(f"Probability of '{tn[0]}'", f"{p_adv*100:.0f}%")
        st.progress(min(max(p_adv, 0.0), 1.0))
        if f"true_{d}" in st.session_state and pick != "- keep current values -":
            st.caption(f"Recorded outcome for the loaded patient: **{st.session_state[f'true_{d}']}** (edited values may differ).")
        st.markdown('<div class="callout warn">A model prediction is a statistical estimate, '
                    'not a confirmed medical diagnosis.</div>', unsafe_allow_html=True)

# =================================================================== ABOUT
else:
    header("About", "How the comparison was run, and what it can and cannot tell you.")
    st.markdown("### Method in 5 steps")
    steps = [("1. Load", "5 breast-cancer datasets, bundled with the project."),
             ("2. Split", "80% train / 20% test, keeping class ratios (stratified)."),
             ("3. Prepare", "Scale features only where needed, inside a pipeline (no leakage)."),
             ("4. Tune", "Grid search with 5-fold cross-validation on training data only."),
             ("5. Test once", "Each tuned model is scored once on the unseen test set.")]
    cols = st.columns(5)
    for col, (t, s) in zip(cols, steps):
        with col:
            st.markdown(f'<div class="card"><b style="color:{TEAL}">{t}</b><div class="kpi-note" style="font-size:0.85rem">{s}</div></div>',
                        unsafe_allow_html=True)
    st.markdown("### Algorithms")
    st.markdown("Logistic Regression, K-Nearest Neighbors, Decision Tree, Random Forest and SVM (RBF kernel), "
                "all from scikit-learn.")
    st.markdown("### Metrics")
    for k, v in metric_definitions().items():
        st.markdown(f"**{k}**: {v}")
    st.markdown("### Limits")
    st.markdown('<div class="callout warn">Small datasets, no external validation, and some datasets contain repeated rows or '
                'simplified labels (see each dataset\'s note). This is an educational prototype, not a substitute for '
                'professional medical diagnosis.</div>', unsafe_allow_html=True)
