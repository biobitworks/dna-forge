"""Find the Right Patients: live demo (DNA Forge AI x Bio Hackathon, Biobase challenge).
Research demo on SYNTHETIC reports and de-identified slides. Not for medical decisions.
All results are precomputed into ./data by make_app_data.py, so the app loads instantly."""
import html, json, re
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

HERE = Path(__file__).parent
DATA = HERE / "data"
THUMBS = HERE / "thumbs"
OURS, BASE = "#2a78d6", "#eb6834"   # validated categorical pair (light surface)

st.set_page_config(page_title="Find the Right Patients", layout="wide")


@st.cache_data
def load():
    rep = json.load(open(DATA / "reports.json"))
    ce = json.load(open(DATA / "criteria_evidence.json"))
    slides = json.load(open(DATA / "slides.json"))
    bridge = json.load(open(DATA / "bridge.json"))
    scores = json.load(open(DATA / "scores.json"))
    return rep, ce, slides, bridge, scores


REP, CE, SLIDES, BRIDGE, SCORES = load()
CRIT = {c["id"]: c["text"] for c in CE["criteria"]}
SL = {s["id"]: s for s in SLIDES}


def short(sid):
    return sid.replace("-biobase_", "·")[:22]


def thumb(sid):
    p = THUMBS / f"{sid}.jpg"
    return str(p) if p.exists() else None


def highlight_text(text, evidence):
    """HTML-escape the report and wrap each matched 'Field: value' in <mark>."""
    out = html.escape(text)
    for k, v in evidence.items():
        if k == "header":
            out = re.sub(r"(Patient:[^\n]*)", r"<mark>\1</mark>", out, count=1)
            continue
        val = html.escape(v)
        pat = re.escape(html.escape(k)) + r":\s*" + re.escape(val) if k != "Diagnosis" else re.escape(val)
        out = re.sub("(" + pat + ")", r"<mark>\1</mark>", out, count=1)
    return "<div style='white-space:pre-wrap;font-family:monospace;font-size:0.8rem'>" + out + "</div>"


def fields_html(fields, evidence):
    rows = []
    for k, v in fields.items():
        hit = k in evidence
        rows.append(f"<li>{'<mark>' if hit else ''}<b>{html.escape(k)}</b>: {html.escape(str(v))}{'</mark>' if hit else ''}</li>")
    return "<ul style='font-size:0.85rem'>" + "".join(rows) + "</ul>"


# ---------------- custom criterion (structured filter builder) ----------------
def custom_filter(df, spec):
    m = pd.Series(True, index=df.index)
    if spec["organ"] != "any": m &= df.organ == spec["organ"]
    if spec["sex"] != "any": m &= df.sex == spec["sex"]
    for k in ("ER", "PR", "HER2"):
        if spec[k] != "any": m &= df[k] == spec[k]
    if spec["nodes"] == ">= 1 positive": m &= df.nodes_pos.fillna(0) >= 1
    if spec["nodes"] == "0 positive": m &= df.nodes_pos == 0
    for k in ("lvi", "pni"):
        if spec[k] == "present": m &= df[k] == True  # noqa: E712
        if spec[k] == "not identified": m &= df[k] == False  # noqa: E712
    if spec["size_min"] > 0: m &= df.size_mm.fillna(-1) >= spec["size_min"]
    if spec["age_min"] > 0: m &= df.age_lo >= spec["age_min"]
    if spec["hist"]: m &= df.histology.fillna("").str.contains(spec["hist"], case=False, regex=False)
    if spec["pT"]: m &= df.pT.fillna("").str.startswith(spec["pT"].lstrip("p"))
    return df[m]


@st.cache_data
def table(split):
    rows = [{"id": i, **{k: v for k, v in r.items() if k not in ("fields", "report_text")}} for i, r in REP.items() if r["split"] == split]
    df = pd.DataFrame(rows).set_index("id")
    df["age_lo"] = df.age_band.str.extract(r"(\d+)").astype(float)
    return df


def nearest_criterion(q):
    tok = lambda s: set(re.findall(r"[a-z0-9]+", s.lower())) - {"with", "the", "and", "or", "a", "that", "is", "of", "cancer"}
    qs = tok(q)
    best = sorted(CRIT, key=lambda c: -len(qs & tok(CRIT[c])) / (len(qs | tok(CRIT[c])) or 1))
    return best[:3]


st.title("Find the Right Patients")
st.caption("Biobase challenge · DNA Forge AI x Bio Hackathon · research demo on synthetic reports and de-identified slides; "
           "no medical claims, not for clinical decisions.")
t1, t2, t3 = st.tabs(["Find patients", "Find samples", "Evaluation"])

# ======================= TAB 1 =======================
with t1:
    c1, c2 = st.columns([3, 1])
    mode = c2.radio("Criterion", ["Pick one of the 30", "Type a criterion", "Build a custom filter"], label_visibility="collapsed")
    split = c2.radio("Cohort", ["test", "train"], format_func=lambda s: {"test": "Test (979, unlabelled)", "train": "Train (9,010)"}[s])
    df = table(split)
    if mode == "Type a criterion":
        q = c1.text_input("Describe the patients you need", "breast cancer HER2 negative with positive lymph nodes")
        opts = nearest_criterion(q)
        cid = c1.radio("Closest explicit criteria (the engine only runs validated filters)", opts, format_func=lambda c: f"{c}: {CRIT[c]}")
    elif mode == "Pick one of the 30":
        cid = c1.selectbox("Criterion", list(CRIT), format_func=lambda c: f"{c}: {CRIT[c]}")
    else:
        cid = None
        with c1:
            a, b, c, d = st.columns(4)
            spec = dict(organ=a.selectbox("Organ", ["any", "breast", "colon", "lung", "prostate", "stomach", "kidney", "skin"], index=1),
                        sex=b.selectbox("Sex", ["any", "F", "M"]), ER=c.selectbox("ER", ["any", "positive", "negative"]),
                        PR=d.selectbox("PR", ["any", "positive", "negative"]), HER2=a.selectbox("HER2", ["any", "positive", "negative", "equivocal"]),
                        nodes=b.selectbox("Lymph nodes", ["any", ">= 1 positive", "0 positive"]),
                        lvi=c.selectbox("Lymphovascular inv.", ["any", "present", "not identified"]),
                        pni=d.selectbox("Perineural inv.", ["any", "present", "not identified"]),
                        size_min=a.number_input("Tumor size ≥ (mm)", 0, 300, 0), age_min=b.number_input("Age band from ≥", 0, 90, 0, step=10),
                        hist=c.text_input("Histology contains", ""), pT=d.text_input("pT starts with (e.g. T4)", ""))
    if cid:
        ev = CE["evidence"][split][cid]; ids = list(ev)
        sc = SCORES["A"]["train_scores"][cid]
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Matching {split} reports (feasibility)", len(ids))
        m2.metric("Share of cohort", f"{100 * len(ids) / len(df):.1f}%")
        m3.metric("Filter F1 on train key", f"{sc['f1']:.3f}", help=f"P={sc['precision']:.3f}, R={sc['recall']:.3f}")
    else:
        sub = custom_filter(df, spec); ids = list(sub.index); ev = {i: {} for i in ids}
        st.metric(f"Matching {split} reports (feasibility)", len(ids))
        st.caption("Custom filters run on the parsed table; they have no answer key, so no F1 is shown.")
    if ids:
        view = df.loc[ids, ["organ", "sex", "age_band", "report_year", "histology", "pT", "pN", "nodes_pos", "size_mm", "ER", "PR", "HER2"]]
        st.dataframe(view, height=260, width="stretch")
        pick = st.selectbox("Open a report (matched fields highlighted)", ids[:500])
        r = REP[pick]
        if "report_text" in r:
            st.markdown(highlight_text(r["report_text"], ev.get(pick, {})), unsafe_allow_html=True)
        else:
            st.markdown(fields_html(r["fields"], ev.get(pick, {})), unsafe_allow_html=True)
    if cid and cid in BRIDGE:
        b = BRIDGE[cid]
        with st.expander(f"Bridge (proof of concept): slides for this criterion, organ = {b['organ']}", expanded=False):
            st.caption("The same engine runs on the 57 slide reports (free text). 'Organ-level candidate' = right organ, "
                       "but the report does not state the needed fields. Suggestions are C2 nearest neighbours in the same organ group.")
            seeds = b["seeds"]
            if not seeds:
                st.write("No slide report covers this organ.")
            for sid, v in list(seeds.items())[:8]:
                st.markdown(f"**{short(sid)}**: {v['status']} · {html.escape(json.dumps(v['evidence'])[:160])}")
            sug = list(b["suggestions"].items())[:10]
            if sug:
                cols = st.columns(5)
                for k, (sid, v) in enumerate(sug):
                    with cols[k % 5]:
                        if thumb(sid): st.image(thumb(sid), width="stretch")
                        st.caption(f"{short(sid)}\n{'held-out' if v['heldout'] else 'labelled'} · {v['group_source']} · sim {v['score']:.2f}")

# ======================= TAB 2 =======================
with t2:
    f1, f2 = st.columns(2)
    which = f1.radio("Slides", ["Held-out (67)", "Labelled", "All"], horizontal=True)
    pool = [s for s in SLIDES if (which == "All") or (which.startswith("Held") == s["heldout"])]
    grp = f2.selectbox("Filter by predicted group", ["any"] + sorted({s["c1"]["pred"] for s in pool}))
    pool = [s for s in pool if grp == "any" or s["c1"]["pred"] == grp]
    if "sel" not in st.session_state or st.session_state.sel not in SL:
        st.session_state.sel = pool[0]["id"] if pool else SLIDES[0]["id"]
    with st.expander(f"Pick a thumbnail ({len(pool)} slides)", expanded=True):
        page = st.number_input("Page", 1, max(1, (len(pool) + 23) // 24), 1)
        cols = st.columns(8)
        for k, s in enumerate(pool[(page - 1) * 24: page * 24]):
            with cols[k % 8]:
                if thumb(s["id"]): st.image(thumb(s["id"]), width="stretch")
                if st.button(short(s["id"]), key="b" + s["id"]): st.session_state.sel = s["id"]
    s = SL[st.session_state.sel]
    a, b = st.columns([1, 3])
    with a:
        if thumb(s["id"]): st.image(thumb(s["id"]), width="stretch")
        st.caption(f"{s['id']} · {s['supplierId']} · {s['stain']}")
    with b:
        p = s["c1"]; top = sorted(p["probs"].items(), key=lambda x: -x[1])[:5]
        st.metric("Predicted organ group", p["pred"])
        st.caption(f"Confidence {p['conf']:.0%} (logistic regression on GigaPath; {p['model']})")
        if s.get("organGroup"):
            st.write(f"Known label: **{s['organGroup']}** ({s.get('organ')}); probabilities are out-of-fold for labelled slides.")
        fig = go.Figure(go.Bar(x=[v for _, v in top][::-1], y=[g for g, _ in top][::-1], orientation="h", marker_color=OURS,
                               hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
        fig.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0), xaxis_tickformat=".0%", xaxis_range=[0, 1])
        st.plotly_chart(fig, width="stretch")
        if s.get("report"): st.caption("Slide report: " + s["report"][:300])
    st.subheader("10 most similar slides")
    if not s["neighbours"]:
        st.write("This slide has no GigaPath vector.")
    cols = st.columns(5)
    for k, n in enumerate(s["neighbours"]):
        t = SL[n["id"]]
        with cols[k % 5]:
            if thumb(n["id"]): st.image(thumb(n["id"]), width="stretch")
            lab = t.get("organGroup") or f"pred. {t['c1']['pred']}"
            st.caption(f"#{k + 1} {short(n['id'])}\n{lab} · cos {n['cos']:.2f}")

# ======================= TAB 3 =======================
with t3:
    A, B = SCORES["A"], SCORES["A_baseline"]
    c1g = pd.DataFrame(SCORES["C1_grid"]); c2g = pd.DataFrame(SCORES["C2_grid"])
    best_c2 = c2g[(c2g.emb == "centred") & (c2g.lam == 1.0)].iloc[0]; base_c2 = c2g[(c2g.emb == "raw") & (c2g.lam == 0)].iloc[0]
    rows = [("A: mean F1 over 30 criteria", f"{A['mean_train_f1']:.3f} (train)", f"{B['mean_f1']:.3f} (train) · 0.27 published"),
            ("C1: organ accuracy", "0.823 (5×5 CV) · 0.852 on SUPP-02", "0.762 (1-NN, same CV) · ~0.70 published"),
            ("C1: leave-one-supplier-out", "0.142", "0.174 (1-NN)"),
            ("C2: P@1 / P@5 / P@10", f"{best_c2['p@1']:.2f} / {best_c2['p@5']:.2f} / {best_c2['p@10']:.2f} (CV)",
             f"{base_c2['p@1']:.2f} / {base_c2['p@5']:.2f} / {base_c2['p@10']:.2f} (CV) · 0.8/0.7/0.6 published")]
    st.subheader("Our scores vs baselines")
    st.table(pd.DataFrame(rows, columns=["Task", "Ours", "Baseline"]))
    if SCORES.get("official"):
        st.success("Official scores (answer key, 4 PM): " + json.dumps(SCORES["official"]))
    else:
        st.info("Official scores: pending the 4:00 PM answer key. Put them in out/official_scores.json and rerun make_app_data.py.")
    st.subheader("Task A: F1 per criterion (train)")
    cids = list(CRIT)
    fig = go.Figure([go.Bar(name="Ours (explicit filters)", x=cids, y=[A["train_scores"][c]["f1"] for c in cids], marker_color=OURS,
                            customdata=[CRIT[c] for c in cids], hovertemplate="%{x}: F1 %{y:.3f}<br>%{customdata}<extra>Ours</extra>"),
                     go.Bar(name="Keyword baseline", x=cids, y=[B["scores"][c]["f1"] for c in cids], marker_color=BASE,
                            customdata=[CRIT[c] for c in cids], hovertemplate="%{x}: F1 %{y:.3f}<br>%{customdata}<extra>Baseline</extra>")])
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08, height=340, yaxis_range=[0, 1.05], yaxis_title="F1",
                      margin=dict(t=10), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, width="stretch")
    st.subheader("C1: model comparison (5×5 stratified CV vs leave-one-supplier-out)")
    best = c1g.loc[c1g.groupby("models").strat_cv.idxmax()].sort_values("strat_cv")
    fig = go.Figure([go.Bar(name="Stratified CV", y=best.models, x=best.strat_cv, orientation="h", marker_color=OURS,
                            customdata=best.clf, hovertemplate="%{y} (%{customdata}): %{x:.3f}<extra>Stratified</extra>"),
                     go.Bar(name="Leave-one-supplier-out", y=best.models, x=best.loso_cv, orientation="h", marker_color=BASE,
                            customdata=best.clf, hovertemplate="%{y} (%{customdata}): %{x:.3f}<extra>LOSO</extra>")])
    fig.update_layout(barmode="group", height=420, xaxis_range=[0, 1], xaxis_title="accuracy", margin=dict(t=10), legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fig, width="stretch")
    st.caption("Best classifier per model set (uncentred). Final model: GigaPath, per-supplier centring, logistic regression C=10.")
    st.subheader("Limitations")
    st.markdown("""
- **Synthetic reports.** Templates are code-generated, so explicit filters can reach F1 = 1.0 on train. Real reports vary far more.
- **Ambiguous criteria, resolved against the train key:** c08 'stage III' includes pN1c (deposits with 0 nodes); c29 'node-positive' left literal (no train case decides it; none in test); 'ER low positive' counts as neither ER+ nor ER−.
- **Slides: small n and supplier shift.** 190 labelled slides, 15 groups; leave-one-supplier-out accuracy is 5–23% for every model, so supplier style is a confounder. Held-out is 57/67 SUPP-02, so in-supplier CV is the relevant estimate.
- **Bridge is a proof of concept.** Slide reports are free text and mostly lack the fields criteria need; 'candidates' need pathologist review.
- Research demo; no medical claims; not for clinical decisions.
""")
