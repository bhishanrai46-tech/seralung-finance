"""
FINORA — AI Financial Planner
Run:   streamlit run finora_app.py
Deploy: https://streamlit.io/cloud
"""

import streamlit as st
import plotly.graph_objects as go

# ── PAGE CONFIG ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finora",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── THEME DEFINITIONS ────────────────────────────────────────────────
THEMES = {
    "Paper": {
        # Warm editorial — off-white, ink, terracotta accent
        "bg":           "#f5f0eb",
        "sidebar_bg":   "#ede8e2",
        "sidebar_bdr":  "#d8d0c6",
        "text":         "#1a1612",
        "text_muted":   "#7a736a",
        "card_bg":      "#faf7f4",
        "card_bdr":     "#ddd6cd",
        "accent":       "#b84c2b",
        "accent_soft":  "#f0e6e1",
        "success":      "#3a6b4a",
        "warning":      "#8a6020",
        "danger":       "#a02020",
        "font_display": "'Playfair Display', Georgia, serif",
        "font_body":    "'Source Serif 4', Georgia, serif",
        "font_mono":    "'IBM Plex Mono', monospace",
        "input_bg":     "#f0ebe4",
        "input_bdr":    "#c8bfb4",
    },
    "Slate": {
        # Cool corporate minimal — true grays, electric blue accent
        "bg":           "#f8f9fb",
        "sidebar_bg":   "#f0f2f5",
        "sidebar_bdr":  "#dde1e8",
        "text":         "#141820",
        "text_muted":   "#6b7280",
        "card_bg":      "#ffffff",
        "card_bdr":     "#e4e8ef",
        "accent":       "#1a56db",
        "accent_soft":  "#eef2ff",
        "success":      "#166534",
        "warning":      "#92400e",
        "danger":       "#991b1b",
        "font_display": "'DM Serif Text', Georgia, serif",
        "font_body":    "'Nunito Sans', sans-serif",
        "font_mono":    "'JetBrains Mono', monospace",
        "input_bg":     "#f3f5f8",
        "input_bdr":    "#cbd2dc",
    },
    "Void": {
        # Pure black — high contrast, amber accent, brutalist clean
        "bg":           "#080808",
        "sidebar_bg":   "#0e0e0e",
        "sidebar_bdr":  "#1c1c1c",
        "text":         "#f0f0f0",
        "text_muted":   "#555555",
        "card_bg":      "#111111",
        "card_bdr":     "#222222",
        "accent":       "#d4a017",
        "accent_soft":  "#1a1500",
        "success":      "#22c55e",
        "warning":      "#f59e0b",
        "danger":       "#ef4444",
        "font_display": "'Bebas Neue', Impact, sans-serif",
        "font_body":    "'Fira Sans', sans-serif",
        "font_mono":    "'Fira Code', monospace",
        "input_bg":     "#161616",
        "input_bdr":    "#2a2a2a",
    },
}

# ── THEME SELECTOR ───────────────────────────────────────────────────
st.sidebar.markdown("#### Theme")
theme_name = st.sidebar.radio(
    label="theme_radio",
    options=list(THEMES.keys()),
    horizontal=True,
    label_visibility="collapsed",
)
T = THEMES[theme_name]

# ── GOOGLE FONTS PER THEME ───────────────────────────────────────────
google_fonts = {
    "Paper": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=Source+Serif+4:wght@300;400;500&family=IBM+Plex+Mono&display=swap",
    "Slate": "https://fonts.googleapis.com/css2?family=DM+Serif+Text&family=Nunito+Sans:wght@300;400;600&family=JetBrains+Mono&display=swap",
    "Void":  "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Fira+Sans:wght@300;400;500&family=Fira+Code&display=swap",
}

# ── INJECT CSS ───────────────────────────────────────────────────────
st.markdown(f"""
<link rel="stylesheet" href="{google_fonts[theme_name]}">
<style>

/* ROOT RESET */
html, body, [class*="css"] {{
    font-family: {T['font_body']};
    background-color: {T['bg']};
    color: {T['text']};
}}

/* SIDEBAR */
section[data-testid="stSidebar"] {{
    background: {T['sidebar_bg']};
    border-right: 1px solid {T['sidebar_bdr']};
}}
section[data-testid="stSidebar"] * {{
    font-family: {T['font_body']};
    color: {T['text']};
}}

/* MAIN CONTAINER */
.main .block-container {{
    padding: 2rem 1.5rem;
    max-width: 860px;
}}

/* PAGE TITLE */
.fin-title {{
    font-family: {T['font_display']};
    font-size: clamp(2rem, 6vw, 3.2rem);
    font-weight: 400;
    color: {T['text']};
    letter-spacing: -0.01em;
    margin: 0 0 0.2rem 0;
    line-height: 1.05;
}}
.fin-subtitle {{
    font-size: 0.75rem;
    color: {T['text_muted']};
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 2.5rem;
}}

/* SECTION LABEL */
.section-label {{
    font-size: 0.65rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {T['text_muted']};
    margin: 2rem 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid {T['card_bdr']};
}}

/* METRIC CARDS */
.metric-row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
}}
.metric-card {{
    flex: 1 1 150px;
    background: {T['card_bg']};
    border: 1px solid {T['card_bdr']};
    border-radius: 8px;
    padding: 18px 20px;
}}
.metric-card.accented {{
    border-left: 3px solid {T['accent']};
}}
.mc-label {{
    font-size: 0.62rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {T['text_muted']};
    margin-bottom: 8px;
}}
.mc-value {{
    font-family: {T['font_display']};
    font-size: clamp(1.5rem, 4vw, 2.1rem);
    color: {T['text']};
    line-height: 1;
}}
.mc-unit {{
    font-size: 0.9rem;
    opacity: 0.4;
}}
.mc-sub {{
    font-size: 0.7rem;
    color: {T['text_muted']};
    margin-top: 6px;
}}
.score-track {{
    height: 3px;
    background: {T['card_bdr']};
    border-radius: 2px;
    margin: 8px 0 4px 0;
    overflow: hidden;
}}
.score-fill {{
    height: 100%;
    border-radius: 2px;
    background: {T['accent']};
}}

/* INSIGHT BANNERS */
.insight-banner {{
    border: 1px solid {T['card_bdr']};
    border-left: 3px solid {T['accent']};
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 0.875rem;
    color: {T['text']};
    margin: 0.4rem 0;
    line-height: 1.6;
    background: {T['card_bg']};
}}
.insight-banner.warning  {{ border-left-color: {T['warning']}; }}
.insight-banner.danger   {{ border-left-color: {T['danger']}; }}
.insight-banner.success  {{ border-left-color: {T['success']}; }}

/* BUDGET BREAKDOWN */
.budget-row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 0.5rem 0;
}}
.budget-item {{
    flex: 1 1 110px;
    background: {T['card_bg']};
    border: 1px solid {T['card_bdr']};
    border-radius: 6px;
    padding: 14px 16px;
}}
.bi-label {{
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {T['text_muted']};
    margin-bottom: 6px;
}}
.bi-value {{
    font-family: {T['font_mono']};
    font-size: 1.05rem;
    color: {T['text']};
}}
.bi-desc {{
    font-size: 0.68rem;
    color: {T['text_muted']};
    margin-top: 4px;
}}

/* INPUTS */
.stNumberInput input, .stTextInput input {{
    background: {T['input_bg']} !important;
    border: 1px solid {T['input_bdr']} !important;
    color: {T['text']} !important;
    border-radius: 6px !important;
    font-family: {T['font_mono']} !important;
    font-size: 0.9rem !important;
}}

/* SIDEBAR LABELS */
section[data-testid="stSidebar"] label {{
    font-size: 0.68rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {T['text_muted']} !important;
}}

/* HIDE STREAMLIT CHROME */
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* DIVIDER */
hr {{
    border: none;
    border-top: 1px solid {T['card_bdr']};
    margin: 1.5rem 0;
}}

/* MOBILE */
@media (max-width: 640px) {{
    .main .block-container {{ padding: 1rem 0.75rem; }}
    .metric-row, .budget-row {{ flex-direction: column; }}
    .metric-card, .budget-item {{ flex: unset; width: 100%; }}
}}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR INPUTS ───────────────────────────────────────────────────
st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.markdown("#### Financials")

income   = st.sidebar.number_input("Monthly Income",   min_value=0, value=0, step=100)
expenses = st.sidebar.number_input("Monthly Expenses", min_value=0, value=0, step=100)
savings  = st.sidebar.number_input("Total Savings",    min_value=0, value=0, step=500)
debt     = st.sidebar.number_input("Total Debt",       min_value=0, value=0, step=500)

st.sidebar.markdown("<hr>", unsafe_allow_html=True)
currency = st.sidebar.selectbox("Currency", ["AUD", "USD", "EUR", "GBP", "INR"], index=0)

currency_symbols = {"AUD": "A$", "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}
sym = currency_symbols[currency]

def fmt(n):
    if abs(n) >= 1_000_000:
        return f"{sym}{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{sym}{n:,.0f}"
    return f"{sym}{n:.0f}"

# ── CALCULATIONS ─────────────────────────────────────────────────────
monthly_surplus = income - expenses

# Savings rate = monthly surplus / income (fixed from original)
savings_rate = (monthly_surplus / income * 100) if income > 0 else 0

net_worth = savings - debt

# 50/30/20 targets
needs  = income * 0.50
wants  = income * 0.30
invest = income * 0.20

# Health score 0–100
score = 50.0
if income > 0:
    sr_bonus     = min(max(savings_rate, 0) * 0.5, 25)
    annual_income = income * 12
    debt_ratio   = debt / annual_income if annual_income > 0 else 0
    debt_penalty = min(debt_ratio * 15, 30)
    score = 50 + sr_bonus - debt_penalty

score = max(0.0, min(100.0, score))

if score >= 80:
    health_label, health_class = "Strong",  "success"
elif score >= 60:
    health_label, health_class = "Stable",  ""
elif score >= 40:
    health_label, health_class = "Caution", "warning"
else:
    health_label, health_class = "At Risk", "danger"

# ── PAGE HEADER ───────────────────────────────────────────────────────
st.markdown('<p class="fin-title">Finora</p>', unsafe_allow_html=True)
st.markdown('<p class="fin-subtitle">Personal Finance Overview</p>', unsafe_allow_html=True)

# ── METRICS ───────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Summary</p>', unsafe_allow_html=True)

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card accented">
    <div class="mc-label">Health Score</div>
    <div class="mc-value">{score:.0f}<span class="mc-unit">/100</span></div>
    <div class="score-track"><div class="score-fill" style="width:{score:.0f}%"></div></div>
    <div class="mc-sub">{health_label}</div>
  </div>
  <div class="metric-card">
    <div class="mc-label">Net Worth</div>
    <div class="mc-value">{fmt(net_worth)}</div>
    <div class="mc-sub">Savings minus debt</div>
  </div>
  <div class="metric-card">
    <div class="mc-label">Monthly Surplus</div>
    <div class="mc-value">{fmt(monthly_surplus)}</div>
    <div class="mc-sub">{savings_rate:.1f}% savings rate</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── INSIGHTS ─────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Insight</p>', unsafe_allow_html=True)

if income == 0:
    st.markdown('<div class="insight-banner">Enter your income in the sidebar to begin.</div>',
                unsafe_allow_html=True)
else:
    if savings_rate < 0:
        st.markdown(
            f'<div class="insight-banner danger">You are spending {fmt(abs(monthly_surplus))} '
            f'more than you earn each month.</div>', unsafe_allow_html=True)
    elif savings_rate < 10:
        st.markdown(
            f'<div class="insight-banner warning">Savings rate is {savings_rate:.1f}%. '
            f'The 50/30/20 rule targets 20%.</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="insight-banner success">Saving {savings_rate:.1f}% of income monthly — '
            f'on track.</div>', unsafe_allow_html=True)

    if debt > savings:
        st.markdown(
            f'<div class="insight-banner danger">Debt ({fmt(debt)}) exceeds savings ({fmt(savings)}). '
            f'Prioritise debt reduction.</div>', unsafe_allow_html=True)
    elif debt > 0 and income > 0:
        st.markdown(
            f'<div class="insight-banner warning">Carrying {fmt(debt)} in debt. '
            f'Net worth stands at {fmt(net_worth)}.</div>', unsafe_allow_html=True)

    if income > 0 and expenses > income * 0.9:
        st.markdown(
            '<div class="insight-banner warning">Expenses exceed 90% of income — '
            'limited buffer for unexpected costs.</div>', unsafe_allow_html=True)

# ── 50/30/20 BREAKDOWN ───────────────────────────────────────────────
st.markdown('<p class="section-label">50/30/20 Guideline</p>', unsafe_allow_html=True)

st.markdown(f"""
<div class="budget-row">
  <div class="budget-item">
    <div class="bi-label">Needs — 50%</div>
    <div class="bi-value">{fmt(needs)}</div>
    <div class="bi-desc">Housing, food, bills</div>
  </div>
  <div class="budget-item">
    <div class="bi-label">Wants — 30%</div>
    <div class="bi-value">{fmt(wants)}</div>
    <div class="bi-desc">Lifestyle, leisure</div>
  </div>
  <div class="budget-item">
    <div class="bi-label">Save / Invest — 20%</div>
    <div class="bi-value">{fmt(invest)}</div>
    <div class="bi-desc">Emergency fund, growth</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── DONUT CHART ───────────────────────────────────────────────────────
if income > 0:
    st.markdown('<p class="section-label">Allocation</p>', unsafe_allow_html=True)

    pie_colors = {
        "Paper": [T["text_muted"], T["accent"], T["success"]],
        "Slate": [T["text_muted"], T["accent"], T["success"]],
        "Void":  [T["text_muted"], T["accent"], T["warning"]],
    }

    fig = go.Figure(go.Pie(
        labels=["Needs", "Wants", "Save / Invest"],
        values=[needs, wants, invest],
        hole=0.72,
        marker=dict(
            colors=pie_colors[theme_name],
            line=dict(color=T["bg"], width=3),
        ),
        textinfo="label+percent",
        textfont=dict(family=T["font_body"], size=11, color=T["text"]),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
        height=270,
        showlegend=False,
        font=dict(family=T["font_body"], color=T["text"]),
        annotations=[dict(
            text=f"<b>{fmt(income)}</b><br>monthly",
            x=0.5, y=0.5,
            font=dict(size=14, family=T["font_display"], color=T["text"]),
            showarrow=False,
        )],
    )

    st.plotly_chart(fig, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────────────
st.markdown(f"""
<hr>
<div style="font-size:0.65rem;color:{T['text_muted']};letter-spacing:0.1em;
            text-align:center;padding-bottom:1rem;text-transform:uppercase;">
Finora — For informational purposes only. Not financial advice.
</div>
""", unsafe_allow_html=True)
