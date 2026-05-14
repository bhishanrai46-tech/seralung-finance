import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

st.set_page_config(
    page_title="Seralung Finance",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

THEMES = {
    "Slate (Default)": {
        "bg": "#0F1117", "surface": "#1A1D27", "surface2": "#22263A",
        "border": "#2E3350", "accent": "#6C8EF5", "accent2": "#4ECDC4",
        "text": "#E8EAF6", "muted": "#8B90B0", "green": "#43D9A2",
        "red": "#FF6B6B", "amber": "#FFB347",
        "chart_colors": ["#6C8EF5","#4ECDC4","#FF6B6B","#FFB347","#43D9A2","#C084FC"],
        "dark": True,
    },
    "Ivory (Light)": {
        "bg": "#FAFAF8", "surface": "#FFFFFF", "surface2": "#F0EEEA",
        "border": "#C8C4BC", "accent": "#3D5A80", "accent2": "#5B8AB8",
        "text": "#111111", "muted": "#4A4A4A", "green": "#1E5C3A",
        "red": "#B01010", "amber": "#8B4A00",
        "chart_colors": ["#3D5A80","#5B8AB8","#B01010","#1E5C3A","#8B4A00","#6B28A0"],
        "dark": False,
    },
    "Forest (Earthy)": {
        "bg": "#1A2018", "surface": "#232C20", "surface2": "#2C3828",
        "border": "#3D5C36", "accent": "#7EC850", "accent2": "#A8D878",
        "text": "#E6F0E0", "muted": "#8AA880", "green": "#7EC850",
        "red": "#E8685A", "amber": "#F0B840",
        "chart_colors": ["#7EC850","#A8D878","#F0B840","#E8685A","#5BC8AF","#C4A0DC"],
        "dark": True,
    },
    "Sand (Minimal)": {
        "bg": "#F5F0E8", "surface": "#FFFFFF", "surface2": "#EDE8DC",
        "border": "#BEB4A4", "accent": "#5C4020", "accent2": "#8C6840",
        "text": "#1A1008", "muted": "#4A3C28", "green": "#2A5C32",
        "red": "#8C1C10", "amber": "#7A4400",
        "chart_colors": ["#5C4020","#8C6840","#2A5C32","#7A4400","#204A6C","#5C2080"],
        "dark": False,
    },
    "Midnight (Deep Blue)": {
        "bg": "#060B18", "surface": "#0D1526", "surface2": "#142035",
        "border": "#1E3050", "accent": "#4FC3F7", "accent2": "#29B6F6",
        "text": "#E1F0FF", "muted": "#6A8BAA", "green": "#26C6DA",
        "red": "#EF5350", "amber": "#FFA726",
        "chart_colors": ["#4FC3F7","#26C6DA","#EF5350","#FFA726","#AB47BC","#66BB6A"],
        "dark": True,
    },
    "Rose (Warm Pink)": {
        "bg": "#FDF6F0", "surface": "#FFFFFF", "surface2": "#F5EAE4",
        "border": "#D0A898", "accent": "#822030", "accent2": "#B04050",
        "text": "#1A0808", "muted": "#5A2828", "green": "#1E5A30",
        "red": "#8C1010", "amber": "#7A3800",
        "chart_colors": ["#822030","#B04050","#1E5A30","#7A3800","#1A4A8A","#5A1A8A"],
        "dark": False,
    },
}

# ── Sidebar theme selector ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Seralung Finance")
    st.markdown("---")
    theme_name = st.selectbox("Theme", list(THEMES.keys()))
    T = THEMES[theme_name]
    st.markdown("---")


# ── Helpers ───────────────────────────────────────────────────────────────────
def hex_to_rgba(hex_color, alpha=0.13):
    """Convert #RRGGBB to rgba() string — avoids the Plotly fillcolor validation error."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def plot_layout(title="", height=280):
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=T["muted"], size=11),
        height=height,
        margin=dict(l=10, r=10, t=36 if title else 10, b=10),
        legend=dict(font=dict(color=T["muted"], size=11),
                    bgcolor="rgba(0,0,0,0)", borderwidth=0),
        xaxis=dict(gridcolor=T["border"], linecolor=T["border"],
                   showgrid=True, color=T["muted"]),
        yaxis=dict(gridcolor=T["border"], linecolor=T["border"],
                   showgrid=True, color=T["muted"]),
    )
    if title:
        layout["title"] = dict(text=title,
                               font=dict(color=T["text"], size=13))
    return layout


def pct_slider_input(label, key, default):
    """Renders a slider + number input side by side for percentage entry."""
    cur = st.session_state.get(key, default)
    col_s, col_n = st.columns([3, 1])
    with col_s:
        s_val = st.slider(label, 0, 100, cur, 1, key=f"{key}_slider")
    with col_n:
        n_val = st.number_input(
            "%", 0, 100, s_val, key=f"{key}_num",
            label_visibility="visible"
        )
    # number input wins if user typed a different value
    final = n_val if n_val != s_val else s_val
    st.session_state[key] = final
    return final


# ── CSS ───────────────────────────────────────────────────────────────────────
# For light themes we need very dark text everywhere; compute once.
text_on_input = "#111111" if not T["dark"] else T["text"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
html, body {{ background-color:{T['bg']} !important; color:{T['text']} !important; }}
.stApp    {{ background-color:{T['bg']} !important; }}
*, *::before, *::after {{ box-sizing:border-box; }}

/* ── Typography ── */
p, span, div, label, li, td, th,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span {{
    color: {T['text']};
}}
h1, h2, h3, h4 {{ color:{T['text']} !important; font-weight:600; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background-color:{T['surface']} !important;
    border-right:1px solid {T['border']};
}}
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {{
    color:{T['text']} !important;
}}

/* ── Metrics ── */
[data-testid="metric-container"] {{
    background:{T['surface']} !important;
    border:1px solid {T['border']} !important;
    border-radius:12px !important;
    padding:0.9rem 1.1rem !important;
}}
[data-testid="metric-container"] [data-testid="stMetricLabel"],
[data-testid="metric-container"] [data-testid="stMetricLabel"] * {{
    color:{T['muted']} !important;
    font-size:0.74rem !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"],
[data-testid="metric-container"] [data-testid="stMetricValue"] * {{
    color:{T['text']} !important;
    font-weight:600 !important;
}}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {{
    background:{T['surface2']};
    border:1px solid {T['border']};
    border-radius:8px;
    color:{T['muted']} !important;
    font-size:0.8rem; font-weight:500;
    padding:0.32rem 0.75rem;
    margin-right:4px;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background:{T['accent']} !important;
    color:#ffffff !important;
    border-color:{T['accent']} !important;
}}
[data-testid="stTabs"] [role="tablist"] {{
    border-bottom:1px solid {T['border']};
    padding-bottom:0.5rem;
    flex-wrap:wrap; gap:4px;
}}

/* ── All form labels ── */
label, [data-testid="stWidgetLabel"], .stSlider label {{
    color:{T['text']} !important;
}}

/* ── Number & text inputs ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
textarea {{
    background:{T['surface2']} !important;
    border:1px solid {T['border']} !important;
    border-radius:8px !important;
    color:{text_on_input} !important;
    font-family:'DM Sans',sans-serif !important;
}}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stSelectbox"] span {{
    background:{T['surface2']} !important;
    border:1px solid {T['border']} !important;
    color:{T['text']} !important;
    border-radius:8px !important;
}}

/* ── Checkboxes ── */
[data-testid="stCheckbox"] span {{
    color:{T['text']} !important;
}}

/* ── Slider track & thumb ── */
[data-baseweb="slider"] [role="slider"] {{
    background:{T['accent']} !important;
    border-color:{T['accent']} !important;
}}

/* ── Buttons ── */
.stButton > button {{
    background:{T['accent']} !important;
    border:none !important;
    border-radius:8px !important;
    color:#ffffff !important;
    font-weight:500 !important;
    font-family:'DM Sans',sans-serif !important;
    transition:opacity 0.15s, transform 0.15s;
}}
.stButton > button:hover {{
    opacity:0.85 !important;
    transform:translateY(-1px);
}}

/* ── Expander ── */
[data-testid="stExpander"] {{
    background:{T['surface']} !important;
    border:1px solid {T['border']} !important;
    border-radius:10px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * {{
    color:{T['text']} !important;
}}

/* ── Warning / info ── */
[data-testid="stAlert"] div {{
    color:{T['text']} !important;
}}

/* ── Divider ── */
hr {{ border-color:{T['border']} !important; }}

/* ── Custom components ── */
.sf-card {{
    background:{T['surface']};
    border:1px solid {T['border']};
    border-radius:14px;
    padding:1.1rem 1.3rem;
    margin-bottom:1rem;
}}
.sf-card-title {{
    font-size:0.67rem; font-weight:600;
    letter-spacing:0.08em; text-transform:uppercase;
    color:{T['muted']}; margin-bottom:0.9rem;
}}
.sf-badge-green {{
    background:{hex_to_rgba(T['green'],0.18)};
    color:{T['green']};
    font-size:0.67rem; font-weight:600;
    padding:2px 7px; border-radius:6px; display:inline-block;
}}
.sf-badge-red {{
    background:{hex_to_rgba(T['red'],0.18)};
    color:{T['red']};
    font-size:0.67rem; font-weight:600;
    padding:2px 7px; border-radius:6px; display:inline-block;
}}
.sf-badge-amber {{
    background:{hex_to_rgba(T['amber'],0.18)};
    color:{T['amber']};
    font-size:0.67rem; font-weight:600;
    padding:2px 7px; border-radius:6px; display:inline-block;
}}
.sf-tip {{
    background:{hex_to_rgba(T['accent'],0.1)};
    border-left:3px solid {T['accent']};
    border-radius:0 8px 8px 0;
    padding:0.7rem 1rem;
    font-size:0.84rem; color:{T['text']};
    margin-bottom:1rem; line-height:1.5;
}}
.sf-tip strong {{ color:{T['accent']}; }}
.sf-proj-row {{
    display:flex; justify-content:space-between;
    padding:0.44rem 0;
    border-bottom:1px solid {T['border']};
    font-size:0.84rem; color:{T['text']};
}}
.sf-proj-row:last-child {{ border-bottom:none; font-weight:600; }}

/* ── Mobile ── */
@media (max-width:768px) {{
    .block-container {{ padding:0.7rem 0.7rem 2rem !important; }}
    [data-testid="stTabs"] [role="tab"] {{
        font-size:0.7rem; padding:0.28rem 0.5rem;
    }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{
        font-size:1rem !important;
    }}
    .sf-card {{ padding:0.75rem 0.85rem; }}
    h1 {{ font-size:1.25rem !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
def _init(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

_init("expenses", [
    {"name": "Rent / Mortgage",        "amount": 1500.0},
    {"name": "Groceries",              "amount": 400.0},
    {"name": "Transport",              "amount": 200.0},
    {"name": "Dining & Entertainment", "amount": 300.0},
    {"name": "Subscriptions",          "amount": 80.0},
])
_init("goals",        [])
_init("risk_profile", "Moderate")
_init("needs_pct",  50)
_init("wants_pct",  30)
_init("invest_pct", 20)
_init("em_pct",  30)
_init("idx_pct", 40)
_init("stk_pct", 20)
_init("cry_pct", 10)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h1 style='margin:0;font-size:1.7rem;letter-spacing:-0.02em;"
    f"color:{T['text']};'>Seralung Finance</h1>"
    f"<p style='color:{T['muted']};font-size:0.82rem;"
    f"margin-top:2px;margin-bottom:1.2rem;'>"
    "Your personal financial command centre</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ── Sidebar: income + budget sliders ─────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<p style='color:{T['muted']};font-size:0.72rem;font-weight:600;"
        "letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;'>"
        "Monthly Income</p>",
        unsafe_allow_html=True,
    )
    primary_income = st.number_input("Primary salary (after tax)",
                                     min_value=0.0, value=5000.0,
                                     step=100.0, format="%.0f")
    other_income   = st.number_input("Other income",
                                     min_value=0.0, value=0.0,
                                     step=50.0, format="%.0f")
    total_income   = primary_income + other_income

    st.markdown("---")
    st.markdown(
        f"<p style='color:{T['muted']};font-size:0.72rem;font-weight:600;"
        "letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;'>"
        "Budget Rule</p>",
        unsafe_allow_html=True,
    )
    st.caption("Slide or type a percentage directly")
    needs_pct  = pct_slider_input("Needs %",       "needs_pct",  50)
    wants_pct  = pct_slider_input("Wants %",        "wants_pct",  30)
    invest_pct = pct_slider_input("Invest/Save %",  "invest_pct", 20)

    total_pct = needs_pct + wants_pct + invest_pct
    if total_pct != 100:
        st.warning(f"Sum = {total_pct}% — must equal 100%")

    st.markdown("---")
    st.markdown(
        f"<p style='color:{T['muted']};font-size:0.72rem;line-height:1.5;'>"
        "Educational purposes only. Not financial advice.</p>",
        unsafe_allow_html=True,
    )

# ── Derived values ────────────────────────────────────────────────────────────
total_expenses = sum(e["amount"] for e in st.session_state.expenses)
investable     = total_income * invest_pct / 100
left_over      = total_income - total_expenses
needs_budget   = total_income * needs_pct  / 100
wants_budget   = total_income * wants_pct  / 100

# ── Summary metrics ───────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Monthly Income",      f"${total_income:,.0f}")
m2.metric("Total Expenses",      f"${total_expenses:,.0f}",
          delta=(f"${total_expenses - total_income:,.0f}"
                 if total_expenses > total_income else None),
          delta_color="inverse")
m3.metric("Investable (target)", f"${investable:,.0f}",
          f"{invest_pct}% of income")
m4.metric("Left Over",           f"${left_over:,.0f}",
          delta="Surplus" if left_over >= 0 else "Deficit",
          delta_color="normal" if left_over >= 0 else "inverse")

st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_budget, tab_invest, tab_risk, tab_goals, tab_tax = st.tabs(
    ["Budget", "Invest", "Risk", "Goals", "Tax & FIRE"]
)

# =============================================================================
# TAB 1 — BUDGET
# =============================================================================
with tab_budget:
    col_exp, col_charts = st.columns([1, 1], gap="large")

    with col_exp:
        st.markdown(
            "<div class='sf-card'><div class='sf-card-title'>Monthly Expenses</div>",
            unsafe_allow_html=True,
        )
        to_delete = None
        for i, exp in enumerate(st.session_state.expenses):
            c1, c2, c3 = st.columns([3, 2, 0.6])
            with c1:
                nn = st.text_input(f"n{i}", value=exp["name"],
                                   label_visibility="collapsed", key=f"ename_{i}")
                st.session_state.expenses[i]["name"] = nn
            with c2:
                na = st.number_input(f"a{i}", value=float(exp["amount"]),
                                     min_value=0.0, step=10.0,
                                     label_visibility="collapsed",
                                     key=f"eamt_{i}", format="%.0f")
                st.session_state.expenses[i]["amount"] = na
            with c3:
                if st.button("X", key=f"del_{i}", help="Remove"):
                    to_delete = i

        if to_delete is not None:
            st.session_state.expenses.pop(to_delete)
            st.rerun()

        ca, cb = st.columns(2)
        with ca:
            new_exp_name = st.text_input("Category", placeholder="e.g. Gym",
                                         key="new_exp_name")
        with cb:
            new_exp_amt = st.number_input("Amount ($)", min_value=0.0, step=10.0,
                                          key="new_exp_amt", format="%.0f")
        if st.button("+ Add expense", use_container_width=True):
            if new_exp_name:
                st.session_state.expenses.append(
                    {"name": new_exp_name, "amount": float(new_exp_amt)}
                )
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_charts:
        if st.session_state.expenses:
            df_e = pd.DataFrame(st.session_state.expenses)
            df_e = df_e[df_e["amount"] > 0].sort_values("amount", ascending=True)
            n = len(df_e)
            cc = (T["chart_colors"] * math.ceil(n / len(T["chart_colors"])))[:n]
            fig_e = go.Figure(go.Bar(
                x=df_e["amount"], y=df_e["name"], orientation="h",
                marker_color=cc,
                text=[f"${v:,.0f}" for v in df_e["amount"]],
                textposition="outside",
                textfont=dict(color=T["text"], size=11),
            ))
            fig_e.update_layout(**plot_layout("Spending by category", height=260))
            st.plotly_chart(fig_e, use_container_width=True)

        st.markdown(
            f"<div class='sf-card'><div class='sf-card-title'>"
            f"{needs_pct}/{wants_pct}/{invest_pct} Rule</div>",
            unsafe_allow_html=True,
        )
        for lbl, budget, color in [
            ("Needs",         needs_budget, T["accent"]),
            ("Wants",         wants_budget, T["accent2"]),
            ("Invest / Save", investable,   T["green"]),
        ]:
            actual = (total_expenses * 0.6 if lbl == "Needs"
                      else total_expenses * 0.4 if lbl == "Wants"
                      else investable)
            pct_b  = min(100, round(actual / budget * 100)) if budget > 0 else 0
            bc     = "green" if pct_b <= 80 else "amber" if pct_b <= 100 else "red"
            bt     = "On track" if pct_b <= 80 else "Near limit" if pct_b <= 100 else "Over"
            bar    = T["red"] if pct_b > 100 else color
            st.markdown(f"""
            <div style='margin-bottom:10px;'>
              <div style='display:flex;justify-content:space-between;margin-bottom:4px;
                          font-size:0.8rem;color:{T["muted"]};'>
                <span style='color:{T["text"]};'>{lbl} — ${actual:,.0f} / ${budget:,.0f}</span>
                <span class='sf-badge-{bc}'>{bt}</span>
              </div>
              <div style='background:{T["surface2"]};border-radius:6px;
                          height:7px;overflow:hidden;'>
                <div style='width:{pct_b}%;height:100%;background:{bar};
                            border-radius:6px;'></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.expenses:
            df_d = pd.DataFrame(st.session_state.expenses)
            df_d = df_d[df_d["amount"] > 0]
            nd = len(df_d)
            dc = (T["chart_colors"] * math.ceil(nd / len(T["chart_colors"])))[:nd]
            fig_dn = go.Figure(go.Pie(
                labels=df_d["name"], values=df_d["amount"], hole=0.55,
                marker=dict(colors=dc, line=dict(color=T["bg"], width=2)),
                textfont=dict(size=11, color=T["muted"]),
                hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig_dn.update_layout(**plot_layout("Expense distribution", height=260))
            st.plotly_chart(fig_dn, use_container_width=True)

# =============================================================================
# TAB 2 — INVEST
# =============================================================================
with tab_invest:
    st.markdown(
        f"<div class='sf-tip'>Based on your {invest_pct}% savings rate, you have "
        f"<strong>${investable:,.0f}/month</strong> to invest.</div>",
        unsafe_allow_html=True,
    )
    col_split, col_proj = st.columns([1, 1], gap="large")

    with col_split:
        st.markdown(
            "<div class='sf-card'><div class='sf-card-title'>Investment split</div>",
            unsafe_allow_html=True,
        )
        st.caption("Slide or type a percentage directly")
        em_pct  = pct_slider_input("Emergency fund",     "em_pct",  30)
        idx_pct = pct_slider_input("Index funds (ETFs)", "idx_pct", 40)
        stk_pct = pct_slider_input("Individual stocks",  "stk_pct", 20)
        cry_pct = pct_slider_input("Crypto",             "cry_pct", 10)
        isum = em_pct + idx_pct + stk_pct + cry_pct
        if isum != 100:
            st.warning(f"Sum = {isum}% — must equal 100%")
        st.markdown("</div>", unsafe_allow_html=True)

        labels  = ["Emergency", "Index funds", "Stocks", "Crypto"]
        values  = [em_pct, idx_pct, stk_pct, cry_pct]
        amounts = [investable * v / 100 for v in values]
        fig_inv = go.Figure(go.Pie(
            labels=[f"{l} ${a:,.0f}/mo" for l, a in zip(labels, amounts)],
            values=values, hole=0.55,
            marker=dict(colors=[T["accent"], T["green"], T["amber"], T["red"]],
                        line=dict(color=T["bg"], width=2)),
            textfont=dict(size=11, color=T["muted"]),
        ))
        fig_inv.update_layout(**plot_layout("Monthly allocation", height=260))
        st.plotly_chart(fig_inv, use_container_width=True)

    with col_proj:
        yrs = list(range(0, 11))

        def compound(rate):
            v, res = 0, []
            for _ in yrs:
                res.append(round(v))
                v = (v + investable * 12) * (1 + rate)
            return res

        c_p = compound(0.04)
        m_p = compound(0.07)
        a_p = compound(0.12)

        fig_proj = go.Figure()
        for proj, lbl, col, dash in [
            (c_p, "Conservative (4%)", T["accent"], "dot"),
            (m_p, "Moderate (7%)",     T["green"],  "solid"),
            (a_p, "Aggressive (12%)",  T["amber"],  "dash"),
        ]:
            fig_proj.add_trace(go.Scatter(
                x=yrs, y=proj, name=lbl, mode="lines",
                line=dict(color=col, width=2, dash=dash),
                hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>",
            ))
        fig_proj.update_layout(**plot_layout("10-year growth projection", height=300))
        fig_proj.update_yaxes(tickprefix="$", tickformat=",.0f")
        fig_proj.update_xaxes(title_text="Year", tickvals=yrs)
        st.plotly_chart(fig_proj, use_container_width=True)

        st.markdown(
            "<div class='sf-card'><div class='sf-card-title'>Year-by-year summary</div>",
            unsafe_allow_html=True,
        )
        for yr in [1, 3, 5, 10]:
            st.markdown(f"""
            <div class='sf-proj-row'>
              <span>Year {yr}</span>
              <span style='color:{T["accent"]}'>${c_p[yr]:,}</span>
              <span style='color:{T["green"]}'>${m_p[yr]:,}</span>
              <span style='color:{T["amber"]}'>${a_p[yr]:,}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;"
            f"font-size:0.67rem;color:{T['muted']};padding-top:6px;'>"
            "<span></span><span>Conservative</span>"
            "<span>Moderate</span><span>Aggressive</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# TAB 3 — RISK
# =============================================================================
with tab_risk:
    risk_profiles = {
        "Conservative": {
            "desc": "Capital preservation. Low volatility, stable returns. "
                    "Suited to short time horizons or risk-averse investors.",
            "alloc": {"Government bonds": 40, "Blue-chip stocks": 30,
                      "REITs": 20, "Cash": 10},
            "ret": (3, 5), "scenarios": (-5, 3, 8),
            "colors": [T["accent"], T["green"], T["accent2"], T["muted"]],
        },
        "Moderate": {
            "desc": "Balanced growth. Mix of equities and fixed income. "
                    "Suited to medium-term goals (5-15 years).",
            "alloc": {"Index funds": 50, "Growth stocks": 25,
                      "Bonds": 15, "Crypto": 10},
            "ret": (6, 9), "scenarios": (-15, 7, 18),
            "colors": [T["green"], T["amber"], T["accent"], T["red"]],
        },
        "Aggressive": {
            "desc": "Maximum growth. High volatility. "
                    "Suited to long time horizons (15+ years) with risk tolerance.",
            "alloc": {"Growth stocks": 40, "Crypto": 25,
                      "Emerging markets": 20, "Options/Alts": 15},
            "ret": (10, 20), "scenarios": (-35, 12, 45),
            "colors": [T["amber"], T["red"], T["accent2"], T["muted"]],
        },
    }

    r1, r2, r3 = st.columns(3)
    for col, rname in zip([r1, r2, r3], risk_profiles.keys()):
        with col:
            rp  = risk_profiles[rname]
            sel = st.session_state.risk_profile == rname
            border = f"2px solid {T['accent']}" if sel else f"1px solid {T['border']}"
            bg_s   = T["surface2"] if sel else T["surface"]
            st.markdown(f"""
            <div style='background:{bg_s};border:{border};border-radius:12px;
                        padding:1rem;margin-bottom:8px;'>
              <div style='font-weight:600;font-size:0.9rem;color:{T["text"]};
                          margin-bottom:6px;'>{rname}</div>
              <div style='font-size:0.75rem;color:{T["muted"]};line-height:1.5;'>
                {rp["desc"]}
              </div>
              <div style='margin-top:8px;font-size:0.75rem;color:{T["accent"]};
                          font-weight:600;'>
                Expected: {rp["ret"][0]}-{rp["ret"][1]}% p.a.
              </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Select {rname}", key=f"risk_{rname}",
                         use_container_width=True):
                st.session_state.risk_profile = rname
                st.rerun()

    st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
    rp = risk_profiles[st.session_state.risk_profile]

    col_alloc, col_scen = st.columns([1, 1], gap="large")

    with col_alloc:
        st.markdown(
            f"<div class='sf-card'><div class='sf-card-title'>"
            f"Portfolio: {st.session_state.risk_profile}</div>",
            unsafe_allow_html=True,
        )
        for idx_a, (asset, pct) in enumerate(rp["alloc"].items()):
            amt = investable * pct / 100
            bc  = rp["colors"][idx_a]
            st.markdown(f"""
            <div style='margin-bottom:10px;'>
              <div style='display:flex;justify-content:space-between;font-size:0.8rem;
                          color:{T["muted"]};margin-bottom:4px;'>
                <span style='color:{T["text"]};'>{asset}</span>
                <span>{pct}% — ${amt:,.0f}/mo</span>
              </div>
              <div style='background:{T["surface2"]};border-radius:5px;height:6px;'>
                <div style='width:{pct}%;height:100%;background:{bc};border-radius:5px;'></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        fig_rd = go.Figure(go.Pie(
            labels=list(rp["alloc"].keys()),
            values=list(rp["alloc"].values()),
            hole=0.55,
            marker=dict(colors=rp["colors"], line=dict(color=T["bg"], width=2)),
            textfont=dict(size=11, color=T["muted"]),
        ))
        fig_rd.update_layout(**plot_layout("Allocation breakdown", height=240))
        st.plotly_chart(fig_rd, use_container_width=True)

    with col_scen:
        st.markdown(
            "<div class='sf-card'><div class='sf-card-title'>"
            "Scenario analysis (10-year)</div>",
            unsafe_allow_html=True,
        )
        base = investable * 12 * 10
        for lbl, ret, col, bt in [
            ("Bear market", rp["scenarios"][0], T["red"],   "red"),
            ("Average",     rp["scenarios"][1], T["amber"], "amber"),
            ("Bull market", rp["scenarios"][2], T["green"], "green"),
        ]:
            est = base * (1 + ret / 100)
            st.markdown(f"""
            <div class='sf-proj-row'>
              <span style='color:{T["text"]};'>{lbl}</span>
              <span class='sf-badge-{bt}'>{ret:+}%</span>
              <span style='color:{col};font-weight:600;'>${est:,.0f}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        bubble_data = [
            {"asset": "Cash/Bonds",    "risk": 5,  "return": 2.5, "size": 16},
            {"asset": "Index funds",   "risk": 28, "return": 7,   "size": 24},
            {"asset": "Growth stocks", "risk": 52, "return": 12,  "size": 20},
            {"asset": "Crypto",        "risk": 80, "return": 22,  "size": 14},
            {"asset": "REITs",         "risk": 35, "return": 8,   "size": 18},
        ]
        fig_bub = go.Figure()
        for i, d in enumerate(bubble_data):
            fig_bub.add_trace(go.Scatter(
                x=[d["risk"]], y=[d["return"]],
                mode="markers+text", name=d["asset"],
                text=[d["asset"]], textposition="top center",
                textfont=dict(size=10, color=T["muted"]),
                marker=dict(size=d["size"] * 2,
                            color=T["chart_colors"][i % len(T["chart_colors"])],
                            opacity=0.8),
            ))
        fig_bub.update_layout(**plot_layout("Risk vs. expected return", height=300))
        fig_bub.update_xaxes(title_text="Risk (volatility %)", range=[-5, 100])
        fig_bub.update_yaxes(title_text="Expected return %", ticksuffix="%",
                             range=[-2, 30])
        st.plotly_chart(fig_bub, use_container_width=True)

# =============================================================================
# TAB 4 — GOALS
# =============================================================================
with tab_goals:
    g1, g2, g3 = st.columns(3)
    g1.metric("Monthly investable", f"${investable:,.0f}")
    g2.metric("1-year savings",     f"${investable * 12:,.0f}")
    five_yr = (investable * 12 * ((pow(1 + 0.07 / 12, 60) - 1) / (0.07 / 12))
               if investable > 0 else 0.0)
    g3.metric("5-year (7% growth)", f"${five_yr:,.0f}")

    st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)

    with st.expander("+ Add a financial goal",
                     expanded=not bool(st.session_state.goals)):
        gc1, gc2, gc3 = st.columns([2, 1, 1])
        with gc1:
            goal_name   = st.text_input("Goal name",
                                        placeholder="House deposit, Car, Holiday...")
        with gc2:
            goal_amount = st.number_input("Target ($)",
                                          min_value=0.0, step=1000.0, format="%.0f")
        with gc3:
            goal_saved  = st.number_input("Already saved ($)",
                                          min_value=0.0, step=100.0, format="%.0f")
        if st.button("Add goal", use_container_width=True):
            if goal_name and goal_amount > 0:
                st.session_state.goals.append(
                    {"name": goal_name, "amount": goal_amount, "saved": goal_saved}
                )
                st.rerun()

    if st.session_state.goals:
        for i, g in enumerate(st.session_state.goals):
            remaining = max(0, g["amount"] - g["saved"])
            months    = math.ceil(remaining / investable) if investable > 0 else 9999
            years_g   = months / 12
            pct_g     = (min(100, round(g["saved"] / g["amount"] * 100))
                         if g["amount"] > 0 else 0)
            cg, cd = st.columns([10, 1])
            with cg:
                st.markdown(f"""
                <div class='sf-card'>
                  <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                    <span style='font-weight:600;font-size:0.9rem;color:{T["text"]};'>
                      {g["name"]}
                    </span>
                    <span style='font-size:0.77rem;color:{T["muted"]};'>
                      ${g["amount"]:,.0f} target
                    </span>
                  </div>
                  <div style='font-size:0.77rem;color:{T["muted"]};margin-bottom:8px;'>
                    ${g["saved"]:,.0f} saved &middot; ${remaining:,.0f} remaining &middot;
                    <span style='color:{T["accent"]};'>
                      {years_g:.1f} yrs ({months} mo) at current rate
                    </span>
                  </div>
                  <div style='background:{T["surface2"]};border-radius:6px;height:8px;'>
                    <div style='width:{pct_g}%;height:100%;background:{T["green"]};
                                border-radius:6px;'></div>
                  </div>
                  <div style='font-size:0.72rem;color:{T["muted"]};margin-top:4px;'>
                    {pct_g}% complete
                  </div>
                </div>""", unsafe_allow_html=True)
            with cd:
                if st.button("X", key=f"goal_del_{i}"):
                    st.session_state.goals.pop(i)
                    st.rerun()
    else:
        st.markdown(
            f"<div style='text-align:center;padding:3rem;"
            f"color:{T['muted']};font-size:0.87rem;'>"
            "No goals yet — add one above.</div>",
            unsafe_allow_html=True,
        )

    if st.session_state.goals and investable > 0:
        gl  = [g["name"] for g in st.session_state.goals]
        gm  = [math.ceil(max(0, g["amount"] - g["saved"]) / investable)
               for g in st.session_state.goals]
        gcc = (T["chart_colors"] * math.ceil(len(gl) / len(T["chart_colors"])))[:len(gl)]
        fig_g = go.Figure(go.Bar(
            x=gm, y=gl, orientation="h", marker_color=gcc,
            text=[f"{m} months" for m in gm], textposition="outside",
            textfont=dict(color=T["text"], size=11),
        ))
        fig_g.update_layout(**plot_layout("Time to reach each goal",
                                          height=max(200, len(gl) * 60)))
        fig_g.update_xaxes(title_text="Months", showgrid=True)
        st.plotly_chart(fig_g, use_container_width=True)

# =============================================================================
# TAB 5 — TAX & FIRE
# =============================================================================
with tab_tax:
    col_tax, col_fire = st.columns([1, 1], gap="large")

    with col_tax:
        st.markdown(
            "<div class='sf-card'><div class='sf-card-title'>"
            "Australian Tax Estimator (FY2024-25)</div>",
            unsafe_allow_html=True,
        )
        gross_income     = st.number_input("Annual gross income ($)",
                                           min_value=0.0,
                                           value=float(primary_income * 12),
                                           step=1000.0, format="%.0f")
        include_medicare = st.checkbox("Include Medicare levy (2%)", value=True)

        def calc_tax(income):
            if   income <= 18200:  return 0.0
            elif income <= 45000:  return (income - 18200) * 0.19
            elif income <= 120000: return 5092  + (income - 45000)  * 0.325
            elif income <= 180000: return 29467 + (income - 120000) * 0.37
            else:                  return 51667 + (income - 180000) * 0.45

        def calc_lito(income):
            if   income <= 37500:  return 700.0
            elif income <= 45000:  return 700 - (income - 37500) * 0.05
            elif income <= 66667:  return 325 - (income - 45000) * 0.015
            else:                  return 0.0

        tax       = calc_tax(gross_income)
        medicare  = gross_income * 0.02 if include_medicare else 0.0
        lito      = calc_lito(gross_income)
        total_tax = max(0.0, tax + medicare - lito)
        net       = gross_income - total_tax
        eff_rate  = (total_tax / gross_income * 100) if gross_income > 0 else 0.0

        for lbl, val, col, bold in [
            ("Gross income",         f"${gross_income:,.0f}",  T["text"],   False),
            ("Income tax (gross)",   f"-${tax:,.0f}",          T["red"],    False),
            ("Medicare levy",        f"-${medicare:,.0f}",     T["amber"],  False),
            ("LITO offset",          f"+${lito:,.0f}",         T["green"],  False),
            ("Total tax payable",    f"-${total_tax:,.0f}",    T["red"],    True),
            ("Net income (annual)",  f"${net:,.0f}",           T["accent"], True),
            ("Net income (monthly)", f"${net/12:,.0f}",        T["accent"], True),
            ("Effective tax rate",   f"{eff_rate:.1f}%",       T["amber"],  True),
        ]:
            fw = "font-weight:600;" if bold else ""
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;padding:6px 0;
                        border-bottom:1px solid {T["border"]};font-size:0.83rem;{fw}'>
              <span style='color:{T["muted"]}'>{lbl}</span>
              <span style='color:{col}'>{val}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_fire:
        st.markdown(
            "<div class='sf-card'><div class='sf-card-title'>FIRE Calculator</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-size:0.75rem;color:{T['muted']};"
            "margin-bottom:1rem;line-height:1.5;'>"
            "Save 25x your annual expenses. The 4% rule lets you withdraw 4% "
            "annually without depleting your portfolio.</div>",
            unsafe_allow_html=True,
        )
        annual_expenses   = st.number_input("Annual living expenses ($)",
                                            min_value=0.0,
                                            value=float(total_expenses * 12),
                                            step=500.0, format="%.0f",
                                            key="fire_exp")
        current_portfolio = st.number_input("Current portfolio value ($)",
                                            min_value=0.0, value=0.0,
                                            step=1000.0, format="%.0f")
        fire_target = annual_expenses * 25
        gap         = max(0, fire_target - current_portfolio)

        for lbl, val in [
            ("Annual expenses",   f"${annual_expenses:,.0f}"),
            ("FIRE number (25x)", f"${fire_target:,.0f}"),
            ("Current portfolio", f"${current_portfolio:,.0f}"),
            ("Gap remaining",     f"${gap:,.0f}"),
        ]:
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;padding:6px 0;
                        border-bottom:1px solid {T["border"]};font-size:0.83rem;'>
              <span style='color:{T["muted"]}'>{lbl}</span>
              <span style='color:{T["text"]};font-weight:500;'>{val}</span>
            </div>""", unsafe_allow_html=True)

        fire_pct = (min(100, round(current_portfolio / fire_target * 100))
                    if fire_target > 0 else 0)
        st.markdown(f"""
        <div style='margin:1rem 0 0.4rem;font-size:0.8rem;color:{T["muted"]};'>
          FIRE progress: {fire_pct}%
        </div>
        <div style='background:{T["surface2"]};border-radius:6px;height:10px;'>
          <div style='width:{fire_pct}%;height:100%;background:{T["green"]};
                      border-radius:6px;'></div>
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if investable > 0 and fire_target > 0:
            yrs_fire, vals_fire = [], []
            v, yr_hit = current_portfolio, None
            for yr in range(41):
                yrs_fire.append(yr)
                vals_fire.append(round(v))
                if v >= fire_target and yr_hit is None:
                    yr_hit = yr
                v = (v + investable * 12) * 1.07

            fig_fire = go.Figure()
            fig_fire.add_trace(go.Scatter(
                x=yrs_fire,
                y=vals_fire,
                name="Portfolio (7% growth)",
                mode="lines",
                line=dict(color=T["green"], width=2),
                fill="tozeroy",
                # hex+"22" causes a validation error in Plotly 6 — use rgba() instead
                fillcolor=hex_to_rgba(T["green"], 0.13),
                hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>",
            ))
            fig_fire.add_hline(
                y=fire_target,
                line_dash="dot",
                line_color=T["amber"],
                annotation_text=f"FIRE ${fire_target:,.0f}",
                annotation_font_color=T["amber"],
            )
            fig_fire.update_layout(**plot_layout("Path to FIRE", height=280))
            fig_fire.update_yaxes(tickprefix="$", tickformat=",.0f")
            fig_fire.update_xaxes(title_text="Years from now")
            st.plotly_chart(fig_fire, use_container_width=True)

            if yr_hit is not None:
                st.markdown(
                    f"<div class='sf-tip'>At your current savings rate you could "
                    f"reach FIRE in approximately "
                    f"<strong>{yr_hit} years</strong>.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='sf-tip'>At your current rate you may not reach "
                    "FIRE within 40 years. Try increasing your savings rate.</div>",
                    unsafe_allow_html=True,
                )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<p style='text-align:center;color:{T['muted']};font-size:0.7rem;'>"
    "Seralung Finance — Educational purposes only. Not financial advice. "
    "Always consult a qualified financial adviser.</p>",
    unsafe_allow_html=True,
)
