"""
FINORA — Personal Finance Planner
Run:    streamlit run finora_app.py
Deploy: https://streamlit.io/cloud
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import date

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finora",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── THEMES ───────────────────────────────────────────────────────────────────
THEMES = {
    "Paper": {
        "bg":          "#f4efe8", "sidebar_bg":  "#ece6de",
        "text":        "#1c1713", "muted":       "#8a7f74",
        "card":        "#faf6f1", "border":      "#ddd5c8",
        "accent":      "#b84c2b", "accent_bg":   "#f5e8e3",
        "success":     "#3a6b4a", "warning":     "#8a6020", "danger": "#a02020",
        "font_h":      "'Playfair Display', Georgia, serif",
        "font_b":      "'Source Serif 4', Georgia, serif",
        "font_m":      "'IBM Plex Mono', monospace",
        "gfonts":      "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=Source+Serif+4:wght@300;400;500&family=IBM+Plex+Mono&display=swap",
    },
    "Slate": {
        "bg":          "#f7f8fa", "sidebar_bg":  "#eef0f4",
        "text":        "#111827", "muted":       "#6b7280",
        "card":        "#ffffff", "border":      "#e2e6ed",
        "accent":      "#1d4ed8", "accent_bg":   "#eff3ff",
        "success":     "#15803d", "warning":     "#b45309", "danger": "#b91c1c",
        "font_h":      "'DM Serif Text', Georgia, serif",
        "font_b":      "'Nunito Sans', sans-serif",
        "font_m":      "'JetBrains Mono', monospace",
        "gfonts":      "https://fonts.googleapis.com/css2?family=DM+Serif+Text&family=Nunito+Sans:wght@300;400;600&family=JetBrains+Mono&display=swap",
    },
    "Void": {
        "bg":          "#060606", "sidebar_bg":  "#0c0c0c",
        "text":        "#eeeeee", "muted":       "#4a4a4a",
        "card":        "#0f0f0f", "border":      "#1e1e1e",
        "accent":      "#c9a84c", "accent_bg":   "#13100a",
        "success":     "#16a34a", "warning":     "#d97706", "danger": "#dc2626",
        "font_h":      "'Bebas Neue', Impact, sans-serif",
        "font_b":      "'Fira Sans', sans-serif",
        "font_m":      "'Fira Code', monospace",
        "gfonts":      "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Fira+Sans:wght@300;400;500&family=Fira+Code&display=swap",
    },
}

# ── THEME PICK ───────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "Slate"

T = THEMES[st.session_state["theme"]]

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<link rel="stylesheet" href="{T['gfonts']}">
<style>
html, body, [class*="css"] {{
    font-family: {T['font_b']};
    background: {T['bg']};
    color: {T['text']};
}}
.main .block-container {{
    padding: 1.8rem 2rem 3rem 2rem;
    max-width: 1000px;
}}
/* hide default chrome */
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* TOP NAV BAR */
.topbar {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 1.6rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid {T['border']};
}}
.topbar-logo {{
    font-family: {T['font_h']};
    font-size: clamp(1.6rem, 4vw, 2.4rem);
    color: {T['text']};
    letter-spacing: -0.01em;
    line-height: 1;
}}
.topbar-sub {{
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {T['muted']};
    margin-top: 3px;
}}
.theme-btns {{
    display: flex;
    gap: 6px;
}}
.theme-btn {{
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border: 1px solid {T['border']};
    background: {T['card']};
    color: {T['muted']};
    padding: 5px 12px;
    border-radius: 4px;
    cursor: pointer;
    text-decoration: none;
}}
.theme-btn.active {{
    border-color: {T['accent']};
    color: {T['accent']};
    background: {T['accent_bg']};
}}

/* SECTION LABEL */
.slabel {{
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {T['muted']};
    padding-bottom: 0.5rem;
    border-bottom: 1px solid {T['border']};
    margin: 0 0 1rem 0;
}}

/* CARDS */
.card {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 8px;
    padding: 18px 20px;
}}
.card.left-accent {{ border-left: 3px solid {T['accent']}; }}
.card.left-success {{ border-left: 3px solid {T['success']}; }}
.card.left-warning {{ border-left: 3px solid {T['warning']}; }}
.card.left-danger  {{ border-left: 3px solid {T['danger']}; }}

/* METRIC GRID */
.metric-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
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
.mc-lbl {{ font-size: 0.6rem; letter-spacing:0.14em; text-transform:uppercase; color:{T['muted']}; margin-bottom:6px; }}
.mc-val {{
    font-family: {T['font_h']};
    font-size: clamp(1.4rem, 3.5vw, 2rem);
    color: {T['text']};
    line-height: 1;
}}
.mc-val .unit {{ font-size: 0.85rem; opacity: 0.4; }}
.mc-note {{ font-size: 0.68rem; color: {T['muted']}; margin-top: 5px; }}
.bar-track {{ height:3px; background:{T['border']}; border-radius:2px; margin:7px 0 3px; overflow:hidden; }}
.bar-fill  {{ height:100%; border-radius:2px; background:{T['accent']}; }}

/* INSIGHT BANNERS */
.banner {{
    border: 1px solid {T['border']};
    border-left: 3px solid {T['muted']};
    border-radius: 6px;
    padding: 11px 15px;
    font-size: 0.84rem;
    color: {T['text']};
    margin: 0.35rem 0;
    background: {T['card']};
    line-height: 1.6;
}}
.banner.success {{ border-left-color: {T['success']}; }}
.banner.warning {{ border-left-color: {T['warning']}; }}
.banner.danger  {{ border-left-color: {T['danger']}; }}
.banner.info    {{ border-left-color: {T['accent']}; }}

/* BUDGET BREAKDOWN */
.brow {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
    margin: 0.5rem 0 1.5rem 0;
}}
.bitem {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 6px;
    padding: 14px 16px;
}}
.bi-lbl {{ font-size: 0.6rem; letter-spacing:0.13em; text-transform:uppercase; color:{T['muted']}; margin-bottom:5px; }}
.bi-val {{ font-family:{T['font_m']}; font-size:1rem; color:{T['text']}; }}
.bi-desc {{ font-size:0.66rem; color:{T['muted']}; margin-top:3px; }}

/* GOAL ITEMS */
.goal-item {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 8px;
    padding: 16px 18px;
    margin-bottom: 10px;
}}
.goal-top {{ display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:6px; }}
.goal-name {{ font-family:{T['font_h']}; font-size:1.05rem; color:{T['text']}; }}
.goal-amt {{ font-family:{T['font_m']}; font-size:0.9rem; color:{T['muted']}; }}
.goal-bar-track {{ height:4px; background:{T['border']}; border-radius:2px; margin:10px 0 5px; overflow:hidden; }}
.goal-bar-fill  {{ height:100%; border-radius:2px; }}
.goal-meta {{ font-size:0.68rem; color:{T['muted']}; display:flex; justify-content:space-between; flex-wrap:wrap; gap:4px; }}

/* TRIP CARD */
.trip-summary {{
    background: {T['card']};
    border: 1px solid {T['border']};
    border-radius: 8px;
    padding: 20px 22px;
    margin: 1rem 0;
}}
.trip-title {{ font-family:{T['font_h']}; font-size:1.3rem; color:{T['text']}; margin-bottom:4px; }}
.trip-meta  {{ font-size:0.72rem; letter-spacing:0.1em; text-transform:uppercase; color:{T['muted']}; margin-bottom:14px; }}
.trip-row   {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(110px, 1fr)); gap:10px; }}
.trip-cell  {{ border-top: 1px solid {T['border']}; padding-top: 10px; }}
.tc-lbl     {{ font-size:0.6rem; letter-spacing:0.14em; text-transform:uppercase; color:{T['muted']}; margin-bottom:4px; }}
.tc-val     {{ font-family:{T['font_m']}; font-size:0.95rem; color:{T['text']}; }}

/* CATEGORY TABLE */
.cat-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid {T['border']};
    font-size: 0.84rem;
}}
.cat-name {{ flex: 1; color:{T['text']}; }}
.cat-bar  {{ flex: 2; height:4px; background:{T['border']}; border-radius:2px; overflow:hidden; }}
.cat-pct  {{ width:36px; text-align:right; color:{T['muted']}; font-family:{T['font_m']}; font-size:0.75rem; }}

/* TABS */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid {T['border']};
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: {T['font_b']};
    font-size: 0.75rem;
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
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 1.5rem;
}}

/* INPUTS */
.stNumberInput input, .stTextInput input, .stDateInput input {{
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
label, .stNumberInput label, .stTextInput label, .stSelectbox label {{
    font-size: 0.68rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: {T['muted']} !important;
}}
.stSlider label {{
    font-size: 0.68rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: {T['muted']} !important;
}}

/* PLOTLY TRANSPARENT */
.js-plotly-plot .plotly, .js-plotly-plot .plotly .svg-container {{
    background: transparent !important;
}}

hr {{ border: none; border-top: 1px solid {T['border']}; margin: 1.5rem 0; }}

/* MOBILE */
@media (max-width: 640px) {{
    .main .block-container {{ padding: 1rem 0.8rem 2rem; }}
    .topbar {{ flex-direction: column; gap: 8px; }}
    .metric-grid, .brow, .trip-row {{ grid-template-columns: 1fr 1fr; }}
}}
@media (max-width: 400px) {{
    .metric-grid, .brow, .trip-row {{ grid-template-columns: 1fr; }}
}}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ──────────────────────────────────────────────────────────────────
CURRENCY_SYM = {"AUD": "A$", "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}

def fmt(n, sym="$"):
    if n is None:
        return f"{sym}0"
    if abs(n) >= 1_000_000:
        return f"{sym}{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{sym}{n:,.0f}"
    return f"{sym}{n:.0f}"

def months_until(target_date):
    today = date.today()
    if target_date <= today:
        return 0
    return (target_date.year - today.year) * 12 + (target_date.month - today.month)

# ── TOP BAR ──────────────────────────────────────────────────────────────────
t_options = list(THEMES.keys())
cur_theme = st.session_state["theme"]

col_logo, col_theme = st.columns([3, 1])
with col_logo:
    st.markdown(f"""
    <div>
      <div class="topbar-logo">Finora</div>
      <div class="topbar-sub">Personal Finance Planner</div>
    </div>
    """, unsafe_allow_html=True)

with col_theme:
    chosen = st.selectbox(
        "UI Theme",
        t_options,
        index=t_options.index(cur_theme),
        label_visibility="collapsed",
        key="theme_select",
    )
    if chosen != cur_theme:
        st.session_state["theme"] = chosen
        st.rerun()

st.markdown("<hr style='margin:0 0 1.5rem 0'>", unsafe_allow_html=True)

# ── MAIN TABS ─────────────────────────────────────────────────────────────────
tab_overview, tab_budget, tab_goals, tab_trip = st.tabs([
    "Overview", "Budget", "Goals", "Trip Planner"
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW (read-only dashboard, inputs inline at top)
# ═════════════════════════════════════════════════════════════════════════════
with tab_overview:
    st.markdown('<p class="slabel">Your Financials</p>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        currency = st.selectbox("Currency", list(CURRENCY_SYM.keys()), index=0)
    sym = CURRENCY_SYM[currency]
    with c2:
        income = st.number_input("Monthly Income", min_value=0, value=0, step=100)
    with c3:
        expenses = st.number_input("Monthly Expenses", min_value=0, value=0, step=100)
    with c4:
        savings = st.number_input("Total Savings", min_value=0, value=0, step=500)
    with c5:
        debt = st.number_input("Total Debt", min_value=0, value=0, step=500)

    # Store in session for other tabs
    st.session_state.update({
        "income": income, "expenses": expenses,
        "savings": savings, "debt": debt,
        "currency": currency, "sym": sym,
    })

    st.markdown("<hr>", unsafe_allow_html=True)

    # — Calculations —
    surplus      = income - expenses
    savings_rate = (surplus / income * 100) if income > 0 else 0.0
    net_worth    = savings - debt
    annual_inc   = income * 12

    # Health score
    score = 50.0
    if income > 0:
        score += min(max(savings_rate, 0) * 0.5, 25)
        score -= min((debt / annual_inc) * 15, 30) if annual_inc > 0 else 0
    score = max(0.0, min(100.0, score))

    score_label = (
        "Strong"  if score >= 80 else
        "Stable"  if score >= 60 else
        "Caution" if score >= 40 else
        "At Risk"
    )

    st.markdown('<p class="slabel">Summary</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metric-grid">
      <div class="mcard hi">
        <div class="mc-lbl">Health Score</div>
        <div class="mc-val">{score:.0f}<span class="unit">/100</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:{score:.0f}%"></div></div>
        <div class="mc-note">{score_label}</div>
      </div>
      <div class="mcard">
        <div class="mc-lbl">Net Worth</div>
        <div class="mc-val">{fmt(net_worth, sym)}</div>
        <div class="mc-note">Savings minus debt</div>
      </div>
      <div class="mcard">
        <div class="mc-lbl">Monthly Surplus</div>
        <div class="mc-val">{fmt(surplus, sym)}</div>
        <div class="mc-note">{savings_rate:.1f}% savings rate</div>
      </div>
      <div class="mcard">
        <div class="mc-lbl">Annual Income</div>
        <div class="mc-val">{fmt(annual_inc, sym)}</div>
        <div class="mc-note">Gross estimate</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # — Insights —
    st.markdown('<p class="slabel">Insights</p>', unsafe_allow_html=True)

    if income == 0:
        st.markdown('<div class="banner info">Enter your income above to begin.</div>',
                    unsafe_allow_html=True)
    else:
        banners = []
        if savings_rate < 0:
            banners.append(("danger",
                f"Spending {fmt(abs(surplus), sym)} more than earned each month. "
                f"Reduce expenses immediately."))
        elif savings_rate < 10:
            banners.append(("warning",
                f"Savings rate is {savings_rate:.1f}%. The 50/30/20 rule targets 20% or more."))
        else:
            banners.append(("success",
                f"Saving {savings_rate:.1f}% of income monthly — solid foundation."))

        if debt > savings and debt > 0:
            banners.append(("danger",
                f"Debt ({fmt(debt, sym)}) exceeds savings ({fmt(savings, sym)}). "
                f"Focus on debt reduction before investing."))
        elif debt > 0:
            banners.append(("warning",
                f"Carrying {fmt(debt, sym)} in debt. Net worth is {fmt(net_worth, sym)}."))

        if income > 0 and expenses >= income:
            banners.append(("danger", "Expenses equal or exceed income. No room for savings or emergencies."))
        elif income > 0 and expenses > income * 0.85:
            banners.append(("warning", "Expenses exceed 85% of income — very limited financial buffer."))

        for cls, msg in banners:
            st.markdown(f'<div class="banner {cls}">{msg}</div>', unsafe_allow_html=True)

    # — Donut chart —
    if income > 0:
        st.markdown('<p class="slabel" style="margin-top:1.5rem">50/30/20 Allocation</p>',
                    unsafe_allow_html=True)

        needs_t  = income * 0.5
        wants_t  = income * 0.3
        invest_t = income * 0.2

        col_c, col_b = st.columns([1, 1])

        with col_c:
            fig = go.Figure(go.Pie(
                labels=["Needs", "Wants", "Save/Invest"],
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
                height=240,
                showlegend=False,
                font=dict(family=T["font_b"], color=T["text"]),
                annotations=[dict(
                    text=f"<b>{fmt(income, sym)}</b><br>monthly",
                    x=0.5, y=0.5,
                    font=dict(size=13, family=T["font_h"], color=T["text"]),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown(f"""
            <div style="padding-top:1rem">
            <div class="brow" style="grid-template-columns:1fr">
              <div class="bitem">
                <div class="bi-lbl">Needs — 50%</div>
                <div class="bi-val">{fmt(needs_t, sym)}</div>
                <div class="bi-desc">Housing, food, utilities, transport</div>
              </div>
              <div class="bitem">
                <div class="bi-lbl">Wants — 30%</div>
                <div class="bi-val">{fmt(wants_t, sym)}</div>
                <div class="bi-desc">Dining, entertainment, lifestyle</div>
              </div>
              <div class="bitem">
                <div class="bi-lbl">Save / Invest — 20%</div>
                <div class="bi-val">{fmt(invest_t, sym)}</div>
                <div class="bi-desc">Emergency fund, super, investments</div>
              </div>
            </div>
            </div>
            """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — BUDGET (category-level breakdown)
# ═════════════════════════════════════════════════════════════════════════════
with tab_budget:
    income_b = st.session_state.get("income", 0)
    sym_b    = st.session_state.get("sym", "$")

    st.markdown('<p class="slabel">Monthly Expense Categories</p>', unsafe_allow_html=True)
    st.caption("Break down your expenses by category to see where your money goes.")

    col_a, col_b2 = st.columns(2)

    with col_a:
        housing   = st.number_input("Housing (rent/mortgage)", min_value=0, value=0, step=50)
        groceries = st.number_input("Groceries & Food",        min_value=0, value=0, step=20)
        transport = st.number_input("Transport",               min_value=0, value=0, step=20)
        utilities = st.number_input("Utilities & Bills",       min_value=0, value=0, step=20)
        insurance = st.number_input("Insurance",               min_value=0, value=0, step=20)

    with col_b2:
        dining    = st.number_input("Dining Out",              min_value=0, value=0, step=20)
        entertain = st.number_input("Entertainment",           min_value=0, value=0, step=20)
        health    = st.number_input("Health & Fitness",        min_value=0, value=0, step=20)
        subscript = st.number_input("Subscriptions",           min_value=0, value=0, step=10)
        other     = st.number_input("Other",                   min_value=0, value=0, step=20)

    categories = {
        "Housing":       housing,
        "Groceries":     groceries,
        "Transport":     transport,
        "Utilities":     utilities,
        "Insurance":     insurance,
        "Dining Out":    dining,
        "Entertainment": entertain,
        "Health":        health,
        "Subscriptions": subscript,
        "Other":         other,
    }

    total_cat = sum(categories.values())

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p class="slabel">Breakdown</p>', unsafe_allow_html=True)

    if total_cat == 0:
        st.markdown('<div class="banner info">Enter expenses above to see the breakdown.</div>',
                    unsafe_allow_html=True)
    else:
        # Bar chart
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        names  = [c[0] for c in sorted_cats if c[1] > 0]
        values = [c[1] for c in sorted_cats if c[1] > 0]

        fig2 = go.Figure(go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker_color=T["accent"],
            hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=20),
            height=max(180, len(names) * 32),
            font=dict(family=T["font_b"], size=11, color=T["text"]),
            xaxis=dict(showgrid=False, zeroline=False, color=T["muted"]),
            yaxis=dict(showgrid=False, color=T["text"]),
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Category table with inline progress
        for name, val in sorted_cats:
            if val == 0:
                continue
            pct = (val / total_cat * 100)
            pct_inc = (val / income_b * 100) if income_b > 0 else 0
            st.markdown(f"""
            <div class="cat-row">
              <div class="cat-name">{name}</div>
              <div class="cat-bar">
                <div style="width:{pct:.0f}%;height:100%;background:{T['accent']};border-radius:2px"></div>
              </div>
              <div class="cat-pct">{pct:.0f}%</div>
              <div style="width:70px;text-align:right;font-family:{T['font_m']};font-size:0.78rem;color:{T['text']}">
                {fmt(val, sym_b)}
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="banner info" style="margin-top:1rem">
            Total categorised: <b>{fmt(total_cat, sym_b)}</b>
            {"&nbsp;&nbsp;|&nbsp;&nbsp; " + fmt(income_b - total_cat, sym_b) + " unaccounted" if income_b > 0 else ""}
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — SAVINGS GOALS
# ═════════════════════════════════════════════════════════════════════════════
with tab_goals:
    surplus_g = st.session_state.get("income", 0) - st.session_state.get("expenses", 0)
    sym_g     = st.session_state.get("sym", "$")

    st.markdown('<p class="slabel">Savings Goals</p>', unsafe_allow_html=True)
    st.caption("Track up to 4 goals. Progress is calculated against your monthly surplus.")

    goal_colors = [T["accent"], T["success"], T["warning"], "#8b5cf6"]

    goals = []
    for i in range(1, 5):
        with st.expander(f"Goal {i}", expanded=(i == 1)):
            gc1, gc2, gc3, gc4 = st.columns(4)
            g_name    = gc1.text_input("Goal Name",        value="", key=f"gn{i}")
            g_target  = gc2.number_input("Target Amount",  min_value=0, value=0, step=100, key=f"gt{i}")
            g_saved   = gc3.number_input("Already Saved",  min_value=0, value=0, step=100, key=f"gs{i}")
            g_monthly = gc4.number_input("Monthly Contrib", min_value=0, value=0, step=50, key=f"gm{i}")

            if g_name and g_target > 0:
                goals.append({
                    "name": g_name, "target": g_target,
                    "saved": g_saved, "monthly": g_monthly,
                    "color": goal_colors[i - 1],
                })

    if goals:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="slabel">Progress</p>', unsafe_allow_html=True)

        for g in goals:
            remaining = max(g["target"] - g["saved"], 0)
            pct       = min(g["saved"] / g["target"] * 100, 100) if g["target"] > 0 else 0
            months_to = (remaining / g["monthly"]) if g["monthly"] > 0 else None

            if months_to is not None:
                eta_str = f"{months_to:.0f} months to go"
            else:
                eta_str = "No monthly contribution set"

            st.markdown(f"""
            <div class="goal-item">
              <div class="goal-top">
                <div class="goal-name">{g['name']}</div>
                <div class="goal-amt">{fmt(g['saved'], sym_g)} / {fmt(g['target'], sym_g)}</div>
              </div>
              <div class="goal-bar-track">
                <div class="goal-bar-fill" style="width:{pct:.0f}%;background:{g['color']}"></div>
              </div>
              <div class="goal-meta">
                <span>{pct:.0f}% complete</span>
                <span>{fmt(remaining, sym_g)} remaining</span>
                <span>{eta_str}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Combined progress donut
        if len(goals) > 1:
            st.markdown('<p class="slabel" style="margin-top:1.5rem">Goals Overview</p>',
                        unsafe_allow_html=True)
            fig3 = go.Figure(go.Pie(
                labels=[g["name"] for g in goals],
                values=[g["target"] for g in goals],
                hole=0.65,
                marker=dict(
                    colors=[g["color"] for g in goals],
                    line=dict(color=T["bg"], width=3),
                ),
                textinfo="label+percent",
                textfont=dict(family=T["font_b"], size=11, color=T["text"]),
            ))
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10),
                height=240,
                showlegend=False,
                font=dict(family=T["font_b"], color=T["text"]),
                annotations=[dict(
                    text=f"<b>{len(goals)}</b><br>goals",
                    x=0.5, y=0.5,
                    font=dict(size=14, family=T["font_h"], color=T["text"]),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.markdown('<div class="banner info">Add at least one goal above to see progress.</div>',
                    unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — TRIP / VACATION PLANNER
# ═════════════════════════════════════════════════════════════════════════════
with tab_trip:
    sym_t    = st.session_state.get("sym", "$")
    surplus_t = st.session_state.get("income", 0) - st.session_state.get("expenses", 0)

    st.markdown('<p class="slabel">Trip Planner</p>', unsafe_allow_html=True)
    st.caption("Plan your next trip, estimate costs, and see how long until you can go.")

    tc1, tc2, tc3 = st.columns(3)
    trip_name       = tc1.text_input("Destination / Trip Name", value="", placeholder="e.g. Japan — 2 weeks")
    trip_date       = tc2.date_input("Travel Date", value=date.today(), min_value=date.today())
    trip_travellers = tc3.number_input("Travellers", min_value=1, value=1, step=1)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p class="slabel">Cost Estimate</p>', unsafe_allow_html=True)

    te1, te2 = st.columns(2)
    with te1:
        t_flights    = st.number_input("Flights (total)",         min_value=0, value=0, step=50)
        t_accomm     = st.number_input("Accommodation (total)",   min_value=0, value=0, step=50)
        t_food       = st.number_input("Food & Dining (total)",   min_value=0, value=0, step=50)
    with te2:
        t_activities = st.number_input("Activities & Tours",      min_value=0, value=0, step=50)
        t_transport  = st.number_input("Local Transport",         min_value=0, value=0, step=20)
        t_misc       = st.number_input("Misc / Emergency Buffer", min_value=0, value=0, step=50)

    trip_saved = st.number_input("Already saved for this trip", min_value=0, value=0, step=50)

    # — Calculations —
    total_trip   = t_flights + t_accomm + t_food + t_activities + t_transport + t_misc
    per_person   = total_trip / trip_travellers if trip_travellers > 0 else 0
    still_needed = max(total_trip - trip_saved, 0)
    months_left  = months_until(trip_date)

    needed_pm = (still_needed / months_left) if months_left > 0 else still_needed
    pct_saved = min(trip_saved / total_trip * 100, 100) if total_trip > 0 else 0

    can_afford = surplus_t >= needed_pm if (surplus_t > 0 and months_left > 0) else False

    # — Summary Card —
    if total_trip > 0 or trip_name:
        display_name = trip_name if trip_name else "Your Trip"
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="trip-summary">
          <div class="trip-title">{display_name}</div>
          <div class="trip-meta">{trip_date.strftime('%B %Y')} &nbsp;·&nbsp; {trip_travellers} traveller{'s' if trip_travellers > 1 else ''}</div>
          <div class="trip-row">
            <div class="trip-cell">
              <div class="tc-lbl">Total Cost</div>
              <div class="tc-val">{fmt(total_trip, sym_t)}</div>
            </div>
            <div class="trip-cell">
              <div class="tc-lbl">Per Person</div>
              <div class="tc-val">{fmt(per_person, sym_t)}</div>
            </div>
            <div class="trip-cell">
              <div class="tc-lbl">Still Needed</div>
              <div class="tc-val">{fmt(still_needed, sym_t)}</div>
            </div>
            <div class="trip-cell">
              <div class="tc-lbl">Months Away</div>
              <div class="tc-val">{months_left}</div>
            </div>
            <div class="trip-cell">
              <div class="tc-lbl">Save per Month</div>
              <div class="tc-val">{fmt(needed_pm, sym_t)}</div>
            </div>
          </div>

          <div class="goal-bar-track" style="margin-top:16px">
            <div class="goal-bar-fill" style="width:{pct_saved:.0f}%;background:{T['accent']}"></div>
          </div>
          <div class="goal-meta" style="margin-top:4px">
            <span>{pct_saved:.0f}% saved</span>
            <span>{fmt(trip_saved, sym_t)} of {fmt(total_trip, sym_t)}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Advice banners
        if months_left == 0:
            st.markdown('<div class="banner warning">Travel date has passed or is today. Update your travel date.</div>',
                        unsafe_allow_html=True)
        elif pct_saved >= 100:
            st.markdown('<div class="banner success">Fully funded — enjoy your trip.</div>',
                        unsafe_allow_html=True)
        elif can_afford:
            st.markdown(
                f'<div class="banner success">Your monthly surplus ({fmt(surplus_t, sym_t)}) '
                f'covers the required {fmt(needed_pm, sym_t)}/month. On track.</div>',
                unsafe_allow_html=True)
        elif surplus_t > 0:
            st.markdown(
                f'<div class="banner warning">You need {fmt(needed_pm, sym_t)}/month but '
                f'only have {fmt(surplus_t, sym_t)} surplus. Consider a later date or lower budget.</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="banner danger">No monthly surplus available. '
                'Reduce expenses before planning a trip.</div>',
                unsafe_allow_html=True)

        # Cost breakdown chart
        if total_trip > 0:
            cost_items = {
                "Flights":    t_flights,
                "Accomm.":    t_accomm,
                "Food":       t_food,
                "Activities": t_activities,
                "Transport":  t_transport,
                "Misc":       t_misc,
            }
            c_names  = [k for k, v in cost_items.items() if v > 0]
            c_values = [v for v in cost_items.values() if v > 0]

            if c_names:
                st.markdown('<p class="slabel" style="margin-top:1.5rem">Cost Breakdown</p>',
                            unsafe_allow_html=True)
                fig4 = go.Figure(go.Pie(
                    labels=c_names,
                    values=c_values,
                    hole=0.5,
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
                    height=240,
                    showlegend=False,
                    font=dict(family=T["font_b"], color=T["text"]),
                )
                st.plotly_chart(fig4, use_container_width=True)
    else:
        st.markdown('<div class="banner info">Enter a trip name and cost estimates above to begin planning.</div>',
                    unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<hr>
<div style="font-size:0.62rem;color:{T['muted']};letter-spacing:0.1em;
            text-align:center;padding-bottom:1rem;text-transform:uppercase;">
Finora — For informational purposes only. Not financial advice.
</div>
""", unsafe_allow_html=True)
