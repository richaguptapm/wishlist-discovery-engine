import json
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="Wishlist Discovery Engine",
    page_icon="◆",
    layout="wide",
)

# Colour-blind safe palette (blue / orange, never red / green).
# Meaning is always carried by labels and ordering as well as colour.
INK = "#12233B"
BLUE = "#1F5FA8"
BLUE_LT = "#7FA8D4"
ORANGE = "#E07A24"
MUTED = "#5A6B7D"
LINE = "#DCE2E8"

st.markdown(
    f"""
    <style>
      .stApp {{ background: #FAFAF8; }}
      body, .stApp, .block-container {{ color: {INK}; }}
      [data-testid="stDataFrame"] {{ background:#FFF; border:1px solid {LINE}; border-radius:8px; }}
      [data-testid="stDataFrame"] * {{ color: {INK} !important; }}
      [data-testid="stDataFrame"] thead th {{ background:#EEF3F9 !important; font-weight:600; }}
      .stTabs [data-baseweb="tab-list"] {{ gap: 1.5rem; }}
      .stTabs [data-baseweb="tab"] {{ color: {MUTED}; }}
      .stTabs [data-baseweb="tab"] p {{ font-size: 1.05rem !important; font-weight: 600; }}
      .stTabs [aria-selected="true"] p {{ color: {INK} !important; }}
      .bigtitle {{ font-size:2.1rem; font-weight:700; color:{INK}; line-height:1.15;
                   letter-spacing:-0.02em; margin:0.1rem 0 0.6rem 0; }}
      h1, h2, h3 {{ color: {INK}; letter-spacing: -0.01em; }}
      .eyebrow {{
        font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em;
        color: {MUTED}; font-weight: 600; margin-bottom: 0.15rem;
      }}
      .stat {{
        background: #FFFFFF; border: 1px solid {LINE}; border-radius: 10px;
        padding: 1rem 1.1rem; height: 100%;
      }}
      .stat .num {{ font-size: 1.9rem; font-weight: 700; color: {INK}; line-height: 1.1; }}
      .stat .lbl {{ font-size: 0.82rem; color: {MUTED}; margin-top: 0.3rem; }}
      .quote {{
        border-left: 3px solid {ORANGE}; padding: 0.5rem 0 0.5rem 0.9rem;
        margin: 0.5rem 0; color: {INK}; font-size: 0.92rem; background: #FFF;
      }}
      .tag {{
        display: inline-block; background: #EEF3F9; color: {BLUE};
        border-radius: 4px; padding: 0.1rem 0.45rem; font-size: 0.72rem;
        font-weight: 600; margin-right: 0.3rem;
      }}
      .note {{ font-size: 0.85rem; color: {MUTED}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# DATA
# ----------------------------------------------------------------------

CLUSTERS = {
    "Fit & size": ["fit_size_unsure", "fit_body_unsure", "fit_brand_inconsistent"],
    "Price": ["price_too_high", "price_cheaper_elsewhere", "price_waiting"],
    "Can't find the item": ["product_findability"],
    "Trust in the item": ["trust_quality", "trust_photos", "trust_reviews_thin"],
    "Stock & availability": ["stock_size_gone", "stock_unavailable"],
    "Returns uncertainty": ["return_hassle", "return_policy_unclear"],
    "Decision paralysis": ["choice_overload", "choice_undecided", "forgot"],
    "Styling & occasion": ["styling_unsure", "occasion_absent", "wardrobe_mismatch"],
    "Needs validation": ["validation_needed", "validation_self"],
    "Not real intent": ["never_intended", "bookmarking"],
}

SEVERITY_WEIGHT = {"abandoned": 3, "delayed": 2, "bought_eventually": 1, "unclear": 1}


@st.cache_data
def load():
    df = pd.read_csv("coded_clean.csv")
    df["relevant_bool"] = df["relevant"].astype(str).str.lower() == "true"
    with open("codebook.yaml") as f:
        cb = yaml.safe_load(f)
    solvable = {
        b["id"]: b.get("solvable_without_money") for b in cb["blockers"]
    }
    return df, cb, solvable


try:
    df, codebook, SOLVABLE = load()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

rel = df[df["relevant_bool"]].copy()


def cluster_of(blocker):
    for name, ids in CLUSTERS.items():
        if blocker in ids:
            return name
    return None


rel["cluster"] = rel["blocker"].apply(cluster_of)


# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------

st.markdown('<div class="eyebrow">AJIO · Growth · Discovery Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="bigtitle">Why wishlisted fashion items never get bought</div>', unsafe_allow_html=True)
st.markdown(
    f"<p class='note'>An AI pipeline that reads public conversation about online fashion shopping "
    f"in India and codes every item against a fixed taxonomy, so opportunity areas can be counted "
    f"and compared rather than summarised.</p>",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
stats = [
    (f"{len(df):,}", "items collected and read"),
    (f"{len(rel):,}", f"consideration-stage items ({100*len(rel)/len(df):.1f}%)"),
    (f"{len(codebook['blockers'])}", "blocker codes in taxonomy"),
    ("2", "sources: Play Store, YouTube"),
]
for col, (num, lbl) in zip([c1, c2, c3, c4], stats):
    col.markdown(
        f"<div class='stat'><div class='num'>{num}</div><div class='lbl'>{lbl}</div></div>",
        unsafe_allow_html=True,
    )

st.write("")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Findings", "Try it live", "Browse the evidence", "How it works"]
)


# ----------------------------------------------------------------------
# TAB 1 — FINDINGS
# ----------------------------------------------------------------------

with tab1:
    st.subheader("Wishlists hold delayed purchases, not idle browsing")

    a, b = st.columns(2)

    with a:
        intent = rel["intent_type"].value_counts()
        labels = {
            "conditional_intent": "Will buy if a condition is met",
            "genuine_intent": "Definitely intends to buy",
            "bookmark": "Bookmarking, little real intent",
            "unclear": "Cannot tell",
        }
        names = [labels.get(i, i) for i in intent.index]
        fig = go.Figure(
            go.Bar(
                x=intent.values,
                y=names,
                orientation="h",
                marker_color=[BLUE, BLUE, ORANGE, MUTED][: len(intent)],
                text=[f"{v} ({100*v/len(rel):.0f}%)" for v in intent.values],
                textposition="outside",
            )
        )
        fig.update_layout(
            title="Type of intent behind a saved item",
            height=280,
            margin=dict(l=0, r=20, t=40, b=0),
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor=LINE, title="Mentions",
                       range=[0, int(intent.values.max() * 1.35)]),
            yaxis=dict(autorange="reversed"),
            font=dict(color=INK, size=12),
        )
        st.plotly_chart(fig, use_container_width=True)

    with b:
        sev = rel["severity"].value_counts()
        slabels = {
            "delayed": "Still undecided / postponed",
            "abandoned": "Gave up on it",
            "bought_eventually": "Bought it in the end",
            "unclear": "Cannot tell",
        }
        fig = go.Figure(
            go.Bar(
                x=sev.values,
                y=[slabels.get(i, i) for i in sev.index],
                orientation="h",
                marker_color=[BLUE, ORANGE, BLUE_LT, MUTED][: len(sev)],
                text=[f"{v} ({100*v/len(rel):.0f}%)" for v in sev.values],
                textposition="outside",
            )
        )
        fig.update_layout(
            title="How the hesitation resolved",
            height=280,
            margin=dict(l=0, r=20, t=40, b=0),
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor=LINE, title="Mentions",
                       range=[0, int(sev.values.max() * 1.35)]),
            yaxis=dict(autorange="reversed"),
            font=dict(color=INK, size=12),
        )
        st.plotly_chart(fig, use_container_width=True)

    cond = (rel["intent_type"] == "conditional_intent").sum()
    book = (rel["intent_type"] == "bookmark").sum()
    delayed = (rel["severity"] == "delayed").sum()
    st.markdown(
        f"<p class='note'><b>{100*cond/len(rel):.0f}%</b> of saved items are conditional intent — "
        f"the person will buy once something is resolved. Only <b>{100*book/len(rel):.0f}%</b> is "
        f"pure bookmarking, and <b>{100*delayed/len(rel):.0f}%</b> of hesitations are postponed "
        f"rather than abandoned. The demand is real and still live.</p>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ---- blocker ranking ----
    st.subheader("Fit is the widest blocker; price and stock are the deadliest")

    rows = []
    for name, ids in CLUSTERS.items():
        sub = rel[rel["blocker"].isin(ids)]
        if len(sub) == 0:
            continue
        aband = (sub["severity"] == "abandoned").mean()
        solv = any(SOLVABLE.get(i) for i in ids)
        sev_w = sub["severity"].map(SEVERITY_WEIGHT).fillna(1).mean()
        score = (len(sub) / len(rel)) * sev_w * (1.0 if solv else 0.2)
        rows.append(
            {
                "Opportunity area": name,
                "Mentions": len(sub),
                "Share": len(sub) / len(rel),
                "Abandonment rate": aband,
                "Solvable without discounts": "Yes" if solv else "No",
                "Opportunity score": round(score * 100, 1),
            }
        )
    opp = pd.DataFrame(rows).sort_values("Mentions", ascending=False)

    fig = go.Figure()
    fig.add_bar(
        x=opp["Mentions"],
        y=opp["Opportunity area"],
        orientation="h",
        marker_color=[
            BLUE if s == "Yes" else ORANGE for s in opp["Solvable without discounts"]
        ],
        text=[
            f"{m}  ({s:.0%})  ·  {'solvable' if v == 'Yes' else 'needs discounts'}"
            for m, s, v in zip(
                opp["Mentions"], opp["Share"], opp["Solvable without discounts"]
            )
        ],
        textposition="outside",
    )
    fig.update_layout(
        height=430,
        margin=dict(l=0, r=40, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=LINE, title="Mentions",
                   range=[0, opp["Mentions"].max() * 1.75]),
        yaxis=dict(autorange="reversed"),
        font=dict(color=INK, size=12),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "<p class='note'>Bars are labelled as well as coloured. Blue = addressable without "
        "monetary incentives; orange = would require discounts, which the brief rules out.</p>",
        unsafe_allow_html=True,
    )

    st.dataframe(
        opp.style.format(
            {"Share": "{:.1%}", "Abandonment rate": "{:.1%}",
             "Opportunity score": "{:.1f}", "Mentions": "{:,.0f}"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        "<p class='note'>Frequency and lethality are different things. Fit questions are the most "
        "common but rarely kill the purchase outright — people stall. Price and stock have the "
        "highest abandonment rates. The opportunity score combines share, severity and whether the "
        "blocker can be solved without money.</p>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ---- discovery story ----
    st.subheader("The engine found a blocker the taxonomy did not have")
    find = rel[rel["blocker"] == "product_findability"]
    if len(find):
        d1, d2 = st.columns([1, 2])
        with d1:
            gi = (find["intent_type"] == "genuine_intent").sum()
            st.markdown(
                f"<div class='stat'><div class='num'>{len(find)}</div>"
                f"<div class='lbl'>mentions of wanting an item but being unable to locate it</div></div>",
                unsafe_allow_html=True,
            )
            st.write("")
            st.markdown(
                f"<div class='stat'><div class='num'>{100*gi/len(find):.0f}%</div>"
                f"<div class='lbl'>of them are coded definite purchase intent — the highest of any blocker</div></div>",
                unsafe_allow_html=True,
            )
        with d2:
            st.markdown(
                "Version 1 of the taxonomy had 24 blockers. The first run left 88 items "
                "unclassified. Sweeping that bucket revealed a single recurring theme that had not "
                "been anticipated: people with maximum intent who simply cannot reach the product. "
                "It was added as a code and the corpus re-run, which also pulled these items out of "
                "the buckets they had been misfiled into."
            )
            for q in find["text"].dropna().head(4):
                st.markdown(
                    f"<div class='quote'>{str(q)[:150]}</div>", unsafe_allow_html=True
                )

    st.divider()

    # ---- where the signal lives ----
    st.subheader("Consideration-stage talk does not happen in app store reviews")
    s1, s2 = st.columns([1, 1])
    with s1:
        src = rel["source"].value_counts()
        tot_src = df["source"].value_counts()
        comp = pd.DataFrame(
            {
                "Source": ["YouTube comments", "Play Store reviews"],
                "Collected": [tot_src.get("youtube", 0), tot_src.get("play_store", 0)],
                "Relevant": [src.get("youtube", 0), src.get("play_store", 0)],
            }
        )
        comp["Hit rate"] = comp["Relevant"] / comp["Collected"]
        st.dataframe(
            comp.style.format({"Hit rate": "{:.1%}", "Collected": "{:,}"}),
            use_container_width=True,
            hide_index=True,
        )
    with s2:
        st.markdown(
            "<p class='note'>App store reviews are dominated by delivery, refund and app-crash "
            "complaints written <i>after</i> a purchase. YouTube comments on haul and review videos "
            "capture people mid-decision — asking which size to order, whether quality holds up, "
            "where to buy something. Reddit was attempted but blocks cloud IP ranges, and is noted "
            "as a methodology limitation.</p>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ---- limitations ----
    st.subheader("What this data cannot tell you")
    l1, l2, l3 = st.columns(3)
    unk_g = (rel["gender"] == "unknown").mean()
    unk_p = (rel["price_band"] == "unknown").mean()
    none_w = (rel["workaround"] == "none_mentioned").mean()
    for col, (v, t) in zip(
        [l1, l2, l3],
        [
            (f"{unk_g:.0%}", "of items give no clue to the person's gender"),
            (f"{unk_p:.0%}", "give no clue to the price band involved"),
            (f"{none_w:.0%}", "mention no workaround outside the app"),
        ],
    ):
        col.markdown(
            f"<div class='stat'><div class='num'>{v}</div><div class='lbl'>{t}</div></div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<p class='note'>Public comments rarely reveal who wrote them or what they did offline. "
        "Segmentation and workaround discovery are therefore the explicit job of primary research, "
        "not this engine. Counts are shares of coded consideration-stage mentions and are not "
        "population estimates — the people who post are self-selected.</p>",
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# TAB 2 — LIVE CLASSIFIER
# ----------------------------------------------------------------------

with tab2:
    st.subheader("Paste any review or comment and watch the engine code it")
    st.markdown(
        "<p class='note'>This runs the same prompt and the same taxonomy used on all "
        f"{len(df):,} items. Try something ambiguous — the filter is deliberately strict about "
        "the difference between hesitating before a purchase and complaining after one.</p>",
        unsafe_allow_html=True,
    )

    api_key = None
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = os.environ.get("GEMINI_API_KEY")

    examples = {
        "Size uncertainty": "Bhai mere 6 no slippers aate hain, main India size 6 loon ya 7? Confused hoon, order karu ya nahi",
        "Post-purchase complaint": "I ordered a top and received a completely different kurti, raised return request and no response from customer care",
        "Cannot find the item": "That black sweatshirt looks amazing, can you please share the link? I searched everywhere and can't find it",
        "Waiting on price": "Nice jacket but 4000 is too much, will wait for the end of season sale",
    }
    pick = st.selectbox("Load an example, or write your own below", ["—"] + list(examples))
    default = examples.get(pick, "")

    text = st.text_area("Text to classify", value=default, height=110)

    if st.button("Classify", type="primary"):
        if not text.strip():
            st.warning("Enter some text first.")
        elif not api_key:
            st.error(
                "No API key configured. Add GEMINI_API_KEY in the app's Secrets settings."
            )
        else:
            with st.spinner("Reading…"):
                try:
                    from google import genai

                    def opts(key):
                        return "\n".join(
                            f"  {i['id']} = {i['label']}" for i in codebook[key]
                        )

                    prompt = f"""You are coding user feedback about online fashion shopping in India.

KEEP an item if: {codebook['relevance']['keep_if']}
DISCARD an item if: {codebook['relevance']['discard_if']}

Return ONE JSON object with these fields.
relevant: true or false. If false, set every other field to "na".

blocker:
{opts('blockers')}

save_motivation:
{opts('save_motivations')}

workaround:
{opts('workarounds')}

comparison:
{opts('comparison_behaviours')}

intent_type:
{opts('intent_types')}

severity:
{opts('severities')}

gender: woman, man, unknown
category: western_wear, ethnic_occasion_wear, footwear, accessories, personal_care, activewear, unknown
price_band: under_1000, 1000_2500, 2500_5000, above_5000, unknown
age_band: under_25, 25_34, 35_plus, unknown
evidence: a short direct quote (max 15 words), or "na".
reasoning: one short sentence explaining the relevance decision.

Return ONLY the JSON object.

ITEM:
{text}"""

                    client = genai.Client(api_key=api_key)
                    models_to_try = [
                        "gemini-3.5-flash-lite",
                        "gemini-3.5-flash",
                        "gemini-2.5-flash",
                        "gemini-2.0-flash",
                    ]
                    resp, used, errs = None, None, []
                    for m in models_to_try:
                        try:
                            resp = client.models.generate_content(
                                model=m,
                                contents=prompt,
                                config={"response_mime_type": "application/json"},
                            )
                            used = m
                            break
                        except Exception as me:
                            errs.append(f"{m}: {str(me)[:90]}")
                    if resp is None:
                        raise RuntimeError(" | ".join(errs))
                    out = json.loads(resp.text)
                    st.caption(f"Classified with {used}")

                    is_rel = str(out.get("relevant")).lower() == "true"
                    if is_rel:
                        st.success("Kept — this is consideration-stage feedback")
                    else:
                        st.info("Discarded — not about a decision that is still open")

                    if out.get("reasoning"):
                        st.markdown(
                            f"<p class='note'><b>Why:</b> {out['reasoning']}</p>",
                            unsafe_allow_html=True,
                        )

                    if is_rel:
                        label = {
                            b["id"]: b["label"] for b in codebook["blockers"]
                        }.get(out.get("blocker"), out.get("blocker"))
                        k1, k2, k3 = st.columns(3)
                        k1.markdown(
                            f"<div class='stat'><div class='lbl'>Blocker</div>"
                            f"<div style='font-weight:700;color:{INK};margin-top:.3rem'>{label}</div></div>",
                            unsafe_allow_html=True,
                        )
                        k2.markdown(
                            f"<div class='stat'><div class='lbl'>Intent</div>"
                            f"<div style='font-weight:700;color:{INK};margin-top:.3rem'>{out.get('intent_type')}</div></div>",
                            unsafe_allow_html=True,
                        )
                        k3.markdown(
                            f"<div class='stat'><div class='lbl'>Severity</div>"
                            f"<div style='font-weight:700;color:{INK};margin-top:.3rem'>{out.get('severity')}</div></div>",
                            unsafe_allow_html=True,
                        )

                    with st.expander("Full structured record"):
                        st.json(out)

                except Exception as e:
                    st.error(f"Classification failed: {e}")


# ----------------------------------------------------------------------
# TAB 3 — EVIDENCE
# ----------------------------------------------------------------------

with tab3:
    st.subheader("Every number above traces back to specific text")

    f1, f2, f3 = st.columns(3)
    pick_cluster = f1.selectbox(
        "Opportunity area", ["All"] + [c for c in CLUSTERS if rel["cluster"].eq(c).any()]
    )
    pick_intent = f2.selectbox(
        "Intent", ["All"] + sorted(rel["intent_type"].dropna().unique().tolist())
    )
    pick_source = f3.selectbox(
        "Source", ["All"] + sorted(rel["source"].dropna().unique().tolist())
    )

    view = rel.copy()
    if pick_cluster != "All":
        view = view[view["cluster"] == pick_cluster]
    if pick_intent != "All":
        view = view[view["intent_type"] == pick_intent]
    if pick_source != "All":
        view = view[view["source"] == pick_source]

    st.markdown(
        f"<p class='note'>{len(view)} items match.</p>", unsafe_allow_html=True
    )

    blabel = {b["id"]: b["label"] for b in codebook["blockers"]}
    for r in view.head(40).itertuples():
        st.markdown(
            f"<div class='quote'>{str(r.text)[:300]}<br>"
            f"<span class='tag'>{blabel.get(r.blocker, r.blocker)}</span>"
            f"<span class='tag'>{r.intent_type}</span>"
            f"<span class='tag'>{r.severity}</span>"
            f"<span class='tag'>{r.source}</span></div>",
            unsafe_allow_html=True,
        )
    if len(view) > 40:
        st.markdown(
            f"<p class='note'>Showing the first 40 of {len(view)}.</p>",
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------
# TAB 4 — HOW IT WORKS
# ----------------------------------------------------------------------

with tab4:
    st.subheader("A constrained pipeline, not an autonomous agent")

    st.markdown(
        """
**1 · Collect** — Scrapers pull public reviews and comments from the Google Play Store
(AJIO, Myntra) and from YouTube comment threads on haul, review and try-on videos.
No AI at this stage.

**2 · Read and code** — Every item goes to a model in batches with one prompt built from the
taxonomy file. Only about 8% are consideration-stage; the rest are delivery and refund complaints. The model answers the same fixed set of questions about each item: is this
someone hesitating before a purchase, and if so what is blocking them, what did they do about
it, was it real intent, how did it resolve, and who are they. Every answer comes from a closed
list, which is what makes the results countable.

**3 · Discover** — Items the model cannot classify are collected in an `other` bucket and
reviewed for themes the taxonomy missed. This is how the findability blocker was found. New
codes are added and the whole corpus is re-run so that misfiled items are recovered.

**4 · Count and rank** — Results are cross-cut by segment, source and severity, and opportunity
areas are scored on share, severity and whether they can be solved without monetary incentives.

**5 · Serve** — This app, including the live classifier on the second tab.
        """
    )

    st.divider()
    st.markdown("**Why the AI is deliberately constrained**")
    st.markdown(
        """
An agent left free to reason over the corpus would invent a fresh taxonomy on every run, which
makes it impossible to say that one opportunity area is larger than another, or to reproduce a
result. Fixing the codebook is what turns qualitative text into countable data. The judgment
work — understanding intent, working across Hindi, Malayalam and Tamil, telling *"I'm not sure
which size to order"* apart from *"they sent the wrong size"* — is all done by the model.
        """
    )

    st.divider()
    st.markdown("**Reusing this engine on a different problem**")
    st.markdown(
        f"""
The taxonomy lives in a single configuration file, currently
{len(codebook['blockers'])} blocker codes plus save motivations, workarounds, comparison
behaviours, intent types and segment signals. Replacing that one file points the same pipeline
at a different company, category or question. No code changes.
        """
    )

    with st.expander("View the current taxonomy"):
        st.code(yaml.safe_dump(codebook, sort_keys=False), language="yaml")
