"""
FINORA — Personal Finance Planner
Run:    streamlit run finora_app.py
Deploy: https://streamlit.io/cloud
requirements: streamlit, plotly
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import date

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finora",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── SESSION STATE DEFAULTS ────────────────────────────────────────────────────
DEFAULTS = {
    "theme":        "Slate",
    "currency":     "AUD",
    "income":       0,
    "expenses":     0,
    "savings":      0,
    "debt":         0,
    "housing":      0,
    "groceries":    0,
    "transport":    0,
    "utilities":    0,
    "insurance":    0,
    "dining":       0,
    "entertain":    0,
    "health":       0,
    "subscript":    0,
    "other":        0,
    "g1_name":      "", "g1_target": 0, "g1_saved": 0, "g1_monthly": 0,
    "g2_name":      "", "g2_target": 0, "g2_saved": 0, "g2_monthly": 0,
    "g3_name":      "", "g3_target": 0, "g3_saved": 0, "g3_monthly": 0,
    "g4_name":      "", "g4_target": 0, "g4_saved": 0, "g4_monthly": 0,
    "trip_name":    "",
    "trip_date":    date.today(),
    "trip_pax":     1,
    "t_flights":    0,
    "t_accomm":     0,
    "t_food":       0,
    "t_activities": 0,
    "t_transport":  0,
    "t_misc":       0,
    "trip_saved":   0,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── THEMES ────────────────────────────────────────────────────────────────────
THEMES = {
    "Paper": {
        "bg":         "#f4efe8", "card":     "#faf6f1",
        "border":     "#ddd5c8", "text":     "#1c1713",
        "muted":      "#8a7f74", "accent":   "#b84c2b",
        "accent_bg":  "#f5e8e3", "success":  "#3a6b4a",
        "warning":    "#8a6020", "danger":   "#a02020",
        "font_h":     "'Playfair Display', Georgia, serif",
        "font_b":     "'Source Serif 4', Georgia, serif",
        "font_m":     "'IBM Plex Mono', monospace",
        "gfonts":     "Playfair+Display:wght@400;600&family=Source+Serif+4:wght@300;400;500&family=IBM+Plex+Mono",
    },
    "Slate": {
        "bg":         "#f7f8fa", "card":     "#ffffff",
        "border":     "#e2e6ed", "text":     "#111827",
        "muted":      "#6b7280", "accent":   "#1d4ed8",
        "accent_bg":  "#eff3ff", "success":  "#15803d",
        "warning":    "#b45309", "danger":   "#b91c1c",
        "font_h":     "'DM Serif Text', Georgia, serif",
        "font_b":     "'Nunito Sans', sans-serif",
        "font_m":     "'JetBrains Mono', monospace",
        "gfonts":     "DM+Serif+Text&family=Nunito+Sans:wght@300;400;600&family=JetBrains+Mono",
    },
    "Void": {
        "bg":         "#060606", "card":     "#0f0f0f",
        "border":     "#1e1e1e", "text":     "#eeeeee",
        "muted":      "#4a4a4a", "accent":   "#c9a84c",
        "accent_bg":  "#13100a", "success":  "#16a34a",
        "warning":    "#d97706", "danger":   "#dc2626",
        "font_h":     "'Bebas Neue', Impact, sans-serif",
        "font_b":     "'Fira Sans', sans-serif",
        "font_m":     "'Fira Code', monospace",
        "gfonts":     "Bebas+Neue&family=Fira+Sans:wght@300;400;500&family=Fira+Code",
    },
}

T = THEMES[st.session_state["theme"]]
GFONTS_URL = f"https://fonts.googleapis.com/css2?family={T['gfonts']}&display=swap"

# ── HELPERS ───────────────────────────────────────────────────────────────────
CURRENCY_SYM = {"AUD": "A$", "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}

def sym():
    return CURRENCY_SYM.get(st.session_state["currency"], "$")

def fmt(n):
    s = sym()
    if n is None:
        return f"{s}0"
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000:
        return f"{sign}{s}{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{sign}{s}{n:,.0f}"
    return f"{sign}{s}{n:.0f}"

def months_until(target):
    today = date.today()
    if target <= today:
        return 0
    return (target.year - today.year) * 12 + (target.month - today.month)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<link rel="stylesheet" href="{GFONTS_URL}">
<style>
html, body, [class*="css"] {{
    font-family: {T['font_b']};
    background: {T['bg']};
    color: {T['text']};
}}
.main .block-container {{
    padding: 1.6rem 2rem 3rem;
    max-width: 1040px;
}}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* TOP BAR */
.fin-logo {{
    font-family: {T['font_h']};
    font-size: clamp(1.8rem, 5vw, 2.6rem);
    color: {T['text']};
    line-height: 1;
    letter-spacing: -0.01em;
}}
.fin-sub {{
    font-size: 0.65rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {T['muted']};
    margin-top: 2px;
}}

/* SECTION LABEL */
.slabel {{
    font-size: 0.6rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {T['muted']};
    padding-bottom: 0.5rem;
    border-bottom: 1px solid {T['border']};
    margin: 1.6rem 0 1rem;
}}
.slabel:first-child {{ margin-top: 0; }}

/* METRIC GRID */
.metric-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
    gap: 10px;
    margin-bottom: 1.5rem;
}}
.mcard {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 8px;
    padding: 16px 18px;
}}
.mcard.hi {{ border-left: 3px solid {T['accent']}; }}
.mc-lbl {{
    font-size: 0.58rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: {T['muted']};
    margin-bottom: 7px;
}}
.mc-val {{
    font-family: {T['font_h']};
    font-size: clamp(1.4rem, 3.5vw, 2rem);
    color: {T['text']};
    line-height: 1;
}}
.mc-unit {{ font-size: 0.85rem; opacity: 0.38; }}
.mc-note {{ font-size: 0.67rem; color: {T['muted']}; margin-top: 5px; }}
.bar-track {{
    height: 3px;
    background: {T['border']};
    border-radius: 2px;
    margin: 8px 0 3px;
    overflow: hidden;
}}
.bar-fill {{
    height: 100%;
    border-radius: 2px;
    background: {T['accent']};
}}

/* BANNERS */
.banner {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-left: 3px solid {T['muted']};
    border-radius: 6px;
    padding: 11px 15px;
    font-size: 0.83rem;
    color: {T['text']};
    margin: 0.35rem 0;
    line-height: 1.65;
}}
.banner.success {{ border-left-color: {T['success']}; }}
.banner.warning {{ border-left-color: {T['warning']}; }}
.banner.danger  {{ border-left-color: {T['danger']};  }}
.banner.info    {{ border-left-color: {T['accent']};  }}

/* BUDGET GRID */
.brow {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
    margin: 0.5rem 0 1.5rem;
}}
.bitem {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 6px;
    padding: 13px 15px;
}}
.bi-lbl {{
    font-size: 0.58rem;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: {T['muted']};
    margin-bottom: 5px;
}}
.bi-val {{ font-family: {T['font_m']}; font-size: 1rem; color: {T['text']}; }}
.bi-desc {{ font-size: 0.65rem; color: {T['muted']}; margin-top: 3px; }}

/* GOALS */
.goal-item {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 8px;
    padding: 16px 18px;
    margin-bottom: 10px;
}}
.goal-top {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 6px;
}}
.goal-name {{
    font-family: {T['font_h']};
    font-size: 1.05rem;
    color: {T['text']};
}}
.goal-amt {{
    font-family: {T['font_m']};
    font-size: 0.88rem;
    color: {T['muted']};
}}
.goal-bar-track {{
    height: 4px;
    background: {T['border']};
    border-radius: 2px;
    margin: 10px 0 5px;
    overflow: hidden;
}}
.goal-bar-fill {{ height: 100%; border-radius: 2px; }}
.goal-meta {{
    font-size: 0.67rem;
    color: {T['muted']};
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 4px;
}}

/* TRIP */
.trip-card {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 8px;
    padding: 20px 22px;
    margin: 1rem 0;
}}
.trip-title {{
    font-family: {T['font_h']};
    font-size: 1.3rem;
    color: {T['text']};
    margin-bottom: 3px;
}}
.trip-meta {{
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {T['muted']};
    margin-bottom: 14px;
}}
.trip-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(105px, 1fr));
    gap: 10px;
}}
.trip-cell {{ border-top: 1px solid {T['border']}; padding-top: 10px; }}
.tc-lbl {{
    font-size: 0.58rem;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: {T['muted']};
    margin-bottom: 4px;
}}
.tc-val {{ font-family: {T['font_m']}; font-size: 0.95rem; color: {T['text']}; }}

/* CATEGORY ROWS */
.cat-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid {T['border']};
    font-size: 0.83rem;
}}
.cat-name {{ flex: 1; color: {T['text']}; }}
.cat-bar  {{ flex: 2; height: 4px; background: {T['border']}; border-radius: 2px; overflow: hidden; }}
.cat-pct  {{
    width: 36px;
    text-align: right;
    color: {T['muted']};
    font-family: {T['font_m']};
    font-size: 0.74rem;
}}
.cat-amt  {{
    width: 70px;
    text-align: right;
    font-family: {T['font_m']};
    font-size: 0.78rem;
    color: {T['text']};
}}

/* TABS */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid {T['border']};
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: {T['font_b']};
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {T['muted']};
    border: none;
    background: transparent;
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
}}
.stTabs [aria-selected="true"] {{
    color: {T['accent']} !important;
    border-bottom: 2px solid {T['accent']} !important;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 1.4rem; }}

/* INPUTS */
.stNumberInput input,
.stTextInput input,
.stDateInput input {{
    background: {T['card']} !important;
    border: 1px solid {T['border']} !important;
    color: {T['text']} !important;
    border-radius: 6px !important;
    font-family: {T['font_m']} !important;
    font-size: 0.88rem !important;
}}
.stSelectbox > div > div {{
    background: {T['card']} !important;
    border: 1px solid {T['border']} !important;
    color: {T['text']} !important;
    border-radius: 6px !important;
}}
div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stDateInput"] label {{
    font-size: 0.65rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: {T['muted']} !important;
}}

/* PLOTLY */
.js-plotly-plot .plotly,
.js-plotly-plot .plotly .svg-container {{
    background: transparent !important;
}}

hr {{
    border: none;
    border-top: 1px solid {T['border']};
    margin: 1.4rem 0;
}}

/* MOBILE */
@media (max-width: 640px) {{
    .main .block-container {{ padding: 1rem 0.8rem 2rem; }}
    .metric-grid, .brow, .trip-row {{ grid-template-columns: 1fr 1fr; }}
}}
@media (max-width: 400px) {{
    .metric-grid, .brow, .trip-row {{ grid-template-columns: 1fr; }}
}}
</style>
""", unsafe_allow_html=True)

# ── TOP BAR ───────────────────────────────────────────────────────────────────
col_logo, col_gap, col_theme = st.columns([4, 2, 2])

with col_logo:
    st.markdown(
        f'<div class="fin-logo">Finora</div>'
        f'<div class="fin-sub">Personal Finance Planner</div>',
        unsafe_allow_html=True,
    )

with col_theme:
    theme_options = list(THEMES.keys())
    # Use index to avoid re-render issues
    new_theme = st.selectbox(
        "Theme",
        theme_options,
        index=theme_options.index(st.session_state["theme"]),
        key="theme_select",
        label_visibility="collapsed",
    )
    # Only update + rerun if changed (compatible with all recent Streamlit versions)
    if new_theme != st.session_state["theme"]:
        st.session_state["theme"] = new_theme
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

st.markdown("<hr style='margin:0.8rem 0 0'>", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_ov, tab_bg, tab_gl, tab_tr = st.tabs(["Overview", "Budget", "Goals", "Trip Planner"])


# ═══════════════════════════════════════════════════════════════════
# TAB 1  OVERVIEW
# ═══════════════════════════════════════════════════════════════════
with tab_ov:
    st.markdown('<p class="slabel">Your Financials</p>', unsafe_allow_html=True)

    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns([1, 1, 1, 1, 1])

    with r1c1:
        st.selectbox(
            "Currency",
            list(CURRENCY_SYM.keys()),
            index=list(CURRENCY_SYM.keys()).index(st.session_state["currency"]),
            key="currency",
        )
    with r1c2:
        st.number_input("Monthly Income",   min_value=0, step=100, key="income")
    with r1c3:
        st.number_input("Monthly Expenses", min_value=0, step=100, key="expenses")
    with r1c4:
        st.number_input("Total Savings",    min_value=0, step=500, key="savings")
    with r1c5:
        st.number_input("Total Debt",       min_value=0, step=500, key="debt")

    # — Compute —
    income_v   = st.session_state["income"]
    expenses_v = st.session_state["expenses"]
    savings_v  = st.session_state["savings"]
    debt_v     = st.session_state["debt"]

    surplus      = income_v - expenses_v
    savings_rate = (surplus / income_v * 100) if income_v > 0 else 0.0
    net_worth    = savings_v - debt_v
    annual_inc   = income_v * 12

    score = 50.0
    if income_v > 0:
        score += min(max(savings_rate, 0) * 0.5, 25)
        score -= min((debt_v / (annual_inc if annual_inc > 0 else 1)) * 15, 30)
    score = max(0.0, min(100.0, score))

    score_label = (
        "Strong"  if score >= 80 else
        "Stable"  if score >= 60 else
        "Caution" if score >= 40 else
        "At Risk"
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p class="slabel">Summary</p>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-grid">
      <div class="mcard hi">
        <div class="mc-lbl">Health Score</div>
        <div class="mc-val">{score:.0f}<span class="mc-unit">/100</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:{score:.0f}%"></div></div>
        <div class="mc-note">{score_label}</div>
      </div>
      <div class="mcard">
        <div class="mc-lbl">Net Worth</div>
        <div class="mc-val">{fmt(net_worth)}</div>
        <div class="mc-note">Savings minus debt</div>
      </div>
      <div class="mcard">
        <div class="mc-lbl">Monthly Surplus</div>
        <div class="mc-val">{fmt(surplus)}</div>
        <div class="mc-note">{savings_rate:.1f}% savings rate</div>
      </div>
      <div class="mcard">
        <div class="mc-lbl">Annual Income</div>
        <div class="mc-val">{fmt(annual_inc)}</div>
        <div class="mc-note">Gross estimate</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # — Insights —
    st.markdown('<p class="slabel">Insights</p>', unsafe_allow_html=True)

    if income_v == 0:
        st.markdown('<div class="banner info">Enter your income above to begin.</div>',
                    unsafe_allow_html=True)
    else:
        if savings_rate < 0:
            st.markdown(
                f'<div class="banner danger">Spending {fmt(abs(surplus))} more than earned each month. '
                f'Reduce expenses immediately.</div>', unsafe_allow_html=True)
        elif savings_rate < 10:
            st.markdown(
                f'<div class="banner warning">Savings rate is {savings_rate:.1f}%. '
                f'The 50/30/20 rule targets 20%.</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="banner success">Saving {savings_rate:.1f}% of income monthly — '
                f'solid foundation.</div>', unsafe_allow_html=True)

        if debt_v > savings_v and debt_v > 0:
            st.markdown(
                f'<div class="banner danger">Debt ({fmt(debt_v)}) exceeds savings ({fmt(savings_v)}). '
                f'Prioritise debt reduction.</div>', unsafe_allow_html=True)
        elif debt_v > 0:
            st.markdown(
                f'<div class="banner warning">Carrying {fmt(debt_v)} in debt. '
                f'Net worth is {fmt(net_worth)}.</div>', unsafe_allow_html=True)

        if expenses_v >= income_v:
            st.markdown(
                '<div class="banner danger">Expenses equal or exceed income. '
                'No room for savings or emergencies.</div>', unsafe_allow_html=True)
        elif expenses_v > income_v * 0.85:
            st.markdown(
                '<div class="banner warning">Expenses exceed 85% of income — '
                'very limited financial buffer.</div>', unsafe_allow_html=True)

    # — 50/30/20 Chart —
    if income_v > 0:
        st.markdown('<p class="slabel">50/30/20 Allocation</p>', unsafe_allow_html=True)

        needs_t  = income_v * 0.5
        wants_t  = income_v * 0.3
        invest_t = income_v * 0.2

        ch_col, br_col = st.columns([1, 1])

        with ch_col:
            fig = go.Figure(go.Pie(
                labels=["Needs", "Wants", "Save / Invest"],
                values=[needs_t, wants_t, invest_t],
                hole=0.70,
                marker=dict(
                    colors=[T["muted"], T["accent"], T["success"]],
                    line=dict(color=T["bg"], width=3),
                ),
                textinfo="label+percent",
                textfont=dict(family=T["font_b"], size=11, color=T["text"]),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10),
                height=230,
                showlegend=False,
                font=dict(family=T["font_b"], color=T["text"]),
                annotations=[dict(
                    text=f"<b>{fmt(income_v)}</b><br>monthly",
                    x=0.5, y=0.5,
                    font=dict(size=13, family=T["font_h"], color=T["text"]),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True)

        with br_col:
            st.markdown(f"""
            <div style="padding-top:0.5rem">
              <div class="brow" style="grid-template-columns:1fr;gap:8px">
                <div class="bitem">
                  <div class="bi-lbl">Needs — 50%</div>
                  <div class="bi-val">{fmt(needs_t)}</div>
                  <div class="bi-desc">Housing, food, utilities, transport</div>
                </div>
                <div class="bitem">
                  <div class="bi-lbl">Wants — 30%</div>
                  <div class="bi-val">{fmt(wants_t)}</div>
                  <div class="bi-desc">Dining, entertainment, lifestyle</div>
                </div>
                <div class="bitem">
                  <div class="bi-lbl">Save / Invest — 20%</div>
                  <div class="bi-val">{fmt(invest_t)}</div>
                  <div class="bi-desc">Emergency fund, super, investments</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 2  BUDGET
# ═══════════════════════════════════════════════════════════════════
with tab_bg:
    income_b = st.session_state["income"]

    st.markdown('<p class="slabel">Monthly Expense Categories</p>', unsafe_allow_html=True)

    ba, bb = st.columns(2)
    with ba:
        st.number_input("Housing (rent / mortgage)", min_value=0, step=50,  key="housing")
        st.number_input("Groceries & Food",          min_value=0, step=20,  key="groceries")
        st.number_input("Transport",                 min_value=0, step=20,  key="transport")
        st.number_input("Utilities & Bills",         min_value=0, step=20,  key="utilities")
        st.number_input("Insurance",                 min_value=0, step=20,  key="insurance")
    with bb:
        st.number_input("Dining Out",                min_value=0, step=20,  key="dining")
        st.number_input("Entertainment",             min_value=0, step=20,  key="entertain")
        st.number_input("Health & Fitness",          min_value=0, step=20,  key="health")
        st.number_input("Subscriptions",             min_value=0, step=10,  key="subscript")
        st.number_input("Other",                     min_value=0, step=20,  key="other")

    cats = {
        "Housing":       st.session_state["housing"],
        "Groceries":     st.session_state["groceries"],
        "Transport":     st.session_state["transport"],
        "Utilities":     st.session_state["utilities"],
        "Insurance":     st.session_state["insurance"],
        "Dining Out":    st.session_state["dining"],
        "Entertainment": st.session_state["entertain"],
        "Health":        st.session_state["health"],
        "Subscriptions": st.session_state["subscript"],
        "Other":         st.session_state["other"],
    }
    total_cat = sum(cats.values())

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p class="slabel">Breakdown</p>', unsafe_allow_html=True)

    if total_cat == 0:
        st.markdown('<div class="banner info">Enter your expenses above to see the breakdown.</div>',
                    unsafe_allow_html=True)
    else:
        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
        active = [(n, v) for n, v in sorted_cats if v > 0]

        # Horizontal bar chart
        fig2 = go.Figure(go.Bar(
            x=[v for _, v in active],
            y=[n for n, _ in active],
            orientation="h",
            marker_color=T["accent"],
            hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=5, b=5, l=10, r=20),
            height=max(160, len(active) * 30),
            font=dict(family=T["font_b"], size=11, color=T["text"]),
            xaxis=dict(showgrid=False, zeroline=False, color=T["muted"], showticklabels=False),
            yaxis=dict(showgrid=False, color=T["text"]),
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Category table
        for name, val in active:
            pct = val / total_cat * 100
            st.markdown(f"""
            <div class="cat-row">
              <div class="cat-name">{name}</div>
              <div class="cat-bar">
                <div style="width:{pct:.0f}%;height:100%;background:{T['accent']};border-radius:2px"></div>
              </div>
              <div class="cat-pct">{pct:.0f}%</div>
              <div class="cat-amt">{fmt(val)}</div>
            </div>
            """, unsafe_allow_html=True)

        unaccounted = income_b - total_cat if income_b > 0 else None
        ua_str = f"&nbsp;&nbsp;·&nbsp;&nbsp; {fmt(unaccounted)} unaccounted for" if unaccounted is not None else ""
        st.markdown(
            f'<div class="banner info" style="margin-top:1rem">'
            f'Total categorised: <b>{fmt(total_cat)}</b>{ua_str}</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════
# TAB 3  GOALS
# ═══════════════════════════════════════════════════════════════════
with tab_gl:
    st.markdown('<p class="slabel">Savings Goals</p>', unsafe_allow_html=True)

    GOAL_COLORS = [T["accent"], T["success"], T["warning"], "#8b5cf6"]

    for i, color in enumerate(GOAL_COLORS, start=1):
        with st.expander(f"Goal {i}", expanded=(i == 1)):
            gc1, gc2, gc3, gc4 = st.columns(4)
            gc1.text_input(   "Goal Name",         key=f"g{i}_name")
            gc2.number_input( "Target Amount",      min_value=0, step=100, key=f"g{i}_target")
            gc3.number_input( "Already Saved",      min_value=0, step=100, key=f"g{i}_saved")
            gc4.number_input( "Monthly Contribution", min_value=0, step=50, key=f"g{i}_monthly")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p class="slabel">Progress</p>', unsafe_allow_html=True)

    active_goals = []
    for i, color in enumerate(GOAL_COLORS, start=1):
        name    = st.session_state.get(f"g{i}_name", "")
        target  = st.session_state.get(f"g{i}_target", 0)
        saved   = st.session_state.get(f"g{i}_saved", 0)
        monthly = st.session_state.get(f"g{i}_monthly", 0)

        if name and target > 0:
            active_goals.append({
                "name": name, "target": target,
                "saved": saved, "monthly": monthly, "color": color,
            })
            remaining = max(target - saved, 0)
            pct       = min(saved / target * 100, 100)
            eta       = f"{remaining / monthly:.0f} months" if monthly > 0 else "No contribution set"

            st.markdown(f"""
            <div class="goal-item">
              <div class="goal-top">
                <div class="goal-name">{name}</div>
                <div class="goal-amt">{fmt(saved)} / {fmt(target)}</div>
              </div>
              <div class="goal-bar-track">
                <div class="goal-bar-fill" style="width:{pct:.0f}%;background:{color}"></div>
              </div>
              <div class="goal-meta">
                <span>{pct:.0f}% complete</span>
                <span>{fmt(remaining)} remaining</span>
                <span>{eta}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    if not active_goals:
        st.markdown('<div class="banner info">Add at least one goal above to see progress.</div>',
                    unsafe_allow_html=True)
    elif len(active_goals) > 1:
        st.markdown('<p class="slabel">Overview</p>', unsafe_allow_html=True)
        fig3 = go.Figure(go.Pie(
            labels=[g["name"] for g in active_goals],
            values=[g["target"] for g in active_goals],
            hole=0.65,
            marker=dict(
                colors=[g["color"] for g in active_goals],
                line=dict(color=T["bg"], width=3),
            ),
            textinfo="label+percent",
            textfont=dict(family=T["font_b"], size=11, color=T["text"]),
        ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10),
            height=230,
            showlegend=False,
            font=dict(family=T["font_b"], color=T["text"]),
            annotations=[dict(
                text=f"<b>{len(active_goals)}</b><br>goals",
                x=0.5, y=0.5,
                font=dict(size=14, family=T["font_h"], color=T["text"]),
                showarrow=False,
            )],
        )
        st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 4  TRIP PLANNER
# ═══════════════════════════════════════════════════════════════════
with tab_tr:
    surplus_t = st.session_state["income"] - st.session_state["expenses"]

    st.markdown('<p class="slabel">Trip Details</p>', unsafe_allow_html=True)

    td1, td2, td3 = st.columns(3)
    td1.text_input(    "Destination / Trip Name", key="trip_name",  placeholder="e.g. Japan — 2 weeks")
    td2.date_input(    "Travel Date",             key="trip_date",  min_value=date.today())
    td3.number_input(  "Travellers",              key="trip_pax",   min_value=1, step=1)

    st.markdown('<p class="slabel">Cost Estimate</p>', unsafe_allow_html=True)

    te1, te2 = st.columns(2)
    with te1:
        st.number_input("Flights (total)",          min_value=0, step=50, key="t_flights")
        st.number_input("Accommodation (total)",    min_value=0, step=50, key="t_accomm")
        st.number_input("Food & Dining (total)",    min_value=0, step=50, key="t_food")
    with te2:
        st.number_input("Activities & Tours",       min_value=0, step=50, key="t_activities")
        st.number_input("Local Transport",          min_value=0, step=20, key="t_transport")
        st.number_input("Misc / Emergency Buffer",  min_value=0, step=50, key="t_misc")

    st.number_input("Already saved for this trip", min_value=0, step=50, key="trip_saved")

    # — Compute —
    trip_date_v  = st.session_state["trip_date"]
    trip_pax_v   = max(st.session_state["trip_pax"], 1)
    total_trip   = (
        st.session_state["t_flights"] + st.session_state["t_accomm"] +
        st.session_state["t_food"]    + st.session_state["t_activities"] +
        st.session_state["t_transport"] + st.session_state["t_misc"]
    )
    per_person   = total_trip / trip_pax_v
    trip_saved_v = st.session_state["trip_saved"]
    still_needed = max(total_trip - trip_saved_v, 0)
    months_left  = months_until(trip_date_v)
    needed_pm    = (still_needed / months_left) if months_left > 0 else still_needed
    pct_saved    = min(trip_saved_v / total_trip * 100, 100) if total_trip > 0 else 0
    can_afford   = (surplus_t >= needed_pm) if (surplus_t > 0 and months_left > 0) else False
    trip_name_v  = st.session_state["trip_name"] or "Your Trip"

    # — Summary Card —
    st.markdown("<hr>", unsafe_allow_html=True)

    if total_trip > 0 or st.session_state["trip_name"]:
        st.markdown(f"""
        <div class="trip-card">
          <div class="trip-title">{trip_name_v}</div>
          <div class="trip-meta">
            {trip_date_v.strftime('%B %Y')}
            &nbsp;·&nbsp;
            {trip_pax_v} traveller{'s' if trip_pax_v > 1 else ''}
          </div>
          <div class="trip-row">
            <div class="trip-cell">
              <div class="tc-lbl">Total Cost</div>
              <div class="tc-val">{fmt(total_trip)}</div>
            </div>
            <div class="trip-cell">
              <div class="tc-lbl">Per Person</div>
              <div class="tc-val">{fmt(per_person)}</div>
            </div>
            <div class="trip-cell">
              <div class="tc-lbl">Still Needed</div>
              <div class="tc-val">{fmt(still_needed)}</div>
            </div>
            <div class="trip-cell">
              <div class="tc-lbl">Months Away</div>
              <div class="tc-val">{months_left}</div>
            </div>
            <div class="trip-cell">
              <div class="tc-lbl">Save / Month</div>
              <div class="tc-val">{fmt(needed_pm)}</div>
            </div>
          </div>
          <div class="goal-bar-track" style="margin-top:16px">
            <div class="goal-bar-fill" style="width:{pct_saved:.0f}%;background:{T['accent']}"></div>
          </div>
          <div class="goal-meta" style="margin-top:4px">
            <span>{pct_saved:.0f}% saved</span>
            <span>{fmt(trip_saved_v)} of {fmt(total_trip)}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Advice
        if months_left == 0:
            st.markdown('<div class="banner warning">Travel date has passed or is today. Update your travel date.</div>',
                        unsafe_allow_html=True)
        elif pct_saved >= 100:
            st.markdown('<div class="banner success">Fully funded — enjoy your trip.</div>',
                        unsafe_allow_html=True)
        elif can_afford:
            st.markdown(
                f'<div class="banner success">Monthly surplus ({fmt(surplus_t)}) covers '
                f'the required {fmt(needed_pm)}/month. On track.</div>',
                unsafe_allow_html=True)
        elif surplus_t > 0:
            st.markdown(
                f'<div class="banner warning">Need {fmt(needed_pm)}/month but only '
                f'{fmt(surplus_t)} surplus available. Consider a later date or trimming costs.</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="banner danger">No monthly surplus. Reduce expenses before planning travel.</div>',
                unsafe_allow_html=True)

        # Cost breakdown donut
        cost_items = {
            "Flights":    st.session_state["t_flights"],
            "Accomm.":    st.session_state["t_accomm"],
            "Food":       st.session_state["t_food"],
            "Activities": st.session_state["t_activities"],
            "Transport":  st.session_state["t_transport"],
            "Misc":       st.session_state["t_misc"],
        }
        active_costs = {k: v for k, v in cost_items.items() if v > 0}

        if active_costs:
            st.markdown('<p class="slabel">Cost Breakdown</p>', unsafe_allow_html=True)
            fig4 = go.Figure(go.Pie(
                labels=list(active_costs.keys()),
                values=list(active_costs.values()),
                hole=0.55,
                marker=dict(
                    colors=[T["accent"], T["success"], T["warning"],
                            T["muted"], "#8b5cf6", T["danger"]],
                    line=dict(color=T["bg"], width=2),
                ),
                textinfo="label+percent",
                textfont=dict(family=T["font_b"], size=11, color=T["text"]),
            ))
            fig4.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10),
                height=230,
                showlegend=False,
                font=dict(family=T["font_b"], color=T["text"]),
            )
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.markdown(
            '<div class="banner info">Enter a trip name and cost estimates above to begin planning.</div>',
            unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<hr>
<div style="font-size:0.6rem;color:{T['muted']};letter-spacing:0.12em;
            text-transform:uppercase;text-align:center;padding-bottom:1rem">
Finora — For informational purposes only. Not financial advice.
</div>
""", unsafe_allow_html=True)
