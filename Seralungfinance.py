"""
Seralung Finance — Simplified Edition
Features: Budget tracking, expenses, goals, net worth, insights
No auth, no complex parsing, no errors. Just works.

Run: streamlit run seralung_simple.py

Requirements:
    pip install streamlit plotly pandas numpy
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math
from datetime import datetime, date
import json

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Seralung Finance", layout="wide", initial_sidebar_state="collapsed")

THEMES = {
    "Light": {
        "bg":"#F9FAFB","surface":"#FFFFFF","surface2":"#F3F4F6","border":"#E5E7EB",
        "accent":"#059669","text":"#111827","muted":"#6B7280",
        "green":"#059669","red":"#DC2626","amber":"#D97706","blue":"#2563EB",
        "dark":False,"shadow":"0 1px 3px rgba(0,0,0,0.08),0 4px 12px rgba(0,0,0,0.04)",
    },
    "Dark": {
        "bg":"#0F1117","surface":"#1A1D27","surface2":"#22263A","border":"#2E3350",
        "accent":"#10B981","text":"#F1F5F9","muted":"#94A3B8",
        "green":"#34D399","red":"#F87171","amber":"#FCD34D","blue":"#60A5FA",
        "dark":True,"shadow":"0 1px 3px rgba(0,0,0,0.3),0 4px 12px rgba(0,0,0,0.2)",
    },
}

CATEGORIES = ["Housing","Food","Transport","Health","Insurance","Tech","Entertainment","Personal","Education","Other"]
ASSET_TYPES = ["Cash","Savings","Investments","Super","Property","Vehicle","Business"]
LIABILITY_TYPES = ["Mortgage","Loan","Credit Card","HECS","Personal","Business"]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def init_session():
    if "primary_income" not in st.session_state:
        st.session_state.primary_income = 6000.0
    if "other_income" not in st.session_state:
        st.session_state.other_income = 500.0
    if "needs_pct" not in st.session_state:
        st.session_state.needs_pct = 50
        st.session_state.wants_pct = 30
        st.session_state.invest_pct = 20
    if "expenses" not in st.session_state:
        st.session_state.expenses = [
            {"name":"Rent","amount":1800.0,"budget":2000.0,"category":"Housing"},
            {"name":"Groceries","amount":450.0,"budget":500.0,"category":"Food"},
            {"name":"Transport","amount":250.0,"budget":300.0,"category":"Transport"},
            {"name":"Dining Out","amount":350.0,"budget":300.0,"category":"Food"},
            {"name":"Utilities","amount":180.0,"budget":220.0,"category":"Housing"},
            {"name":"Phone","amount":85.0,"budget":85.0,"category":"Tech"},
            {"name":"Insurance","amount":150.0,"budget":200.0,"category":"Insurance"},
            {"name":"Entertainment","amount":120.0,"budget":150.0,"category":"Entertainment"},
        ]
    if "subscriptions" not in st.session_state:
        st.session_state.subscriptions = [
            {"name":"Netflix","amount":18.0},
            {"name":"Spotify","amount":12.0},
            {"name":"Gym","amount":45.0},
        ]
    if "assets" not in st.session_state:
        st.session_state.assets = [
            {"name":"Savings Account","type":"Savings","value":12000.0},
            {"name":"Superannuation","type":"Super","value":35000.0},
            {"name":"Car","type":"Vehicle","value":18000.0},
            {"name":"ETF Portfolio","type":"Investments","value":8500.0},
        ]
    if "liabilities" not in st.session_state:
        st.session_state.liabilities = [
            {"name":"Car Loan","type":"Loan","balance":14000.0,"rate":6.5},
            {"name":"Credit Card","type":"Credit Card","balance":2800.0,"rate":19.99},
            {"name":"HECS Debt","type":"HECS","balance":18000.0,"rate":3.9},
        ]
    if "goals" not in st.session_state:
        st.session_state.goals = [
            {"name":"Emergency Fund","target":15000.0,"saved":12000.0,"priority":"High"},
            {"name":"Europe Trip","target":8000.0,"saved":2000.0,"priority":"Medium"},
            {"name":"House Deposit","target":80000.0,"saved":25000.0,"priority":"High"},
        ]

init_session()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt(n):
    return f"${n:,.0f}"

def pct(n):
    return f"{n:.1f}%"

def h2r(hx, a=0.15):
    h = hx.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"

def health_score():
    """Calculate financial health score (0-100)."""
    score = 0
    
    # Savings rate (0-25)
    sr = max(0, (total_income - total_exp) / total_income * 100) if total_income > 0 else 0
    score += min(25, sr / 20 * 25)
    
    # Emergency fund (0-20)
    cash = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash", "Savings"])
    em = cash / total_exp if total_exp > 0 else 0
    score += min(20, em / 6 * 20)
    
    # Debt ratio (0-20)
    debt = sum(l["balance"] for l in st.session_state.liabilities if l["type"] != "HECS")
    dti = debt / (total_income * 12) * 100 if total_income > 0 else 0
    score += max(0, 20 - dti * 0.5)
    
    # Net worth (0-15)
    nw = total_assets - total_liab
    score += 15 if nw > 0 else max(0, 15 + nw / 10000)
    
    # Budget control (0-10)
    over = sum(max(0, e["amount"] - e.get("budget", e["amount"])) for e in st.session_state.expenses)
    score += max(0, 10 - over / 100)
    
    # Goals (0-10)
    score += min(10, len(st.session_state.goals) * 3)
    
    return round(score)

# ─────────────────────────────────────────────────────────────────────────────
# THEME & STYLING
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### Seralung Finance")
    theme_name = st.selectbox("Theme", list(THEMES.keys()), index=0)
    T = THEMES[theme_name]

A = T["accent"]
TX = T["text"]
MU = T["muted"]
BG = T["bg"]
SU = T["surface"]
S2 = T["surface2"]
BO = T["border"]
SH = T["shadow"]
GR = T["green"]
RD = T["red"]
AM = T["amber"]
BL = T["blue"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, .stApp {{
    background: {BG} !important;
    color: {TX} !important;
    font-family: Inter, sans-serif;
}}
p, span, div, label {{ color: {TX}; }}
h1, h2, h3 {{ color: {TX} !important; font-weight: 700; }}

[data-testid="stSidebar"] {{ background: {SU} !important; border-right: 1px solid {BO} !important; }}
[data-testid="stMetricContainer"] {{
    background: {SU} !important;
    border: 1px solid {BO} !important;
    border-radius: 12px !important;
    box-shadow: {SH};
}}

[data-testid="stTabs"] [role="tab"] {{
    background: transparent;
    border: 1.5px solid {BO};
    border-radius: 8px;
    color: {MU} !important;
    padding: 0.5rem 1rem;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: {A} !important;
    color: white !important;
    border-color: {A} !important;
}}

[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {{
    background: {S2} !important;
    border: 1.5px solid {BO} !important;
    border-radius: 8px !important;
    color: {TX} !important;
}}

.stButton > button {{
    background: {A} !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
}}
.stButton > button:hover {{
    filter: brightness(1.08);
}}

.card {{
    background: {SU};
    border: 1px solid {BO};
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: {SH};
}}

.metric {{
    background: {S2};
    padding: 0.75rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
}}

.tip {{
    background: {h2r(A, 0.1)};
    border-left: 3px solid {A};
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    margin: 1rem 0;
    font-size: 0.85rem;
}}

hr {{ border-color: {BO} !important; }}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER & INCOME
# ─────────────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f"<h1 style='margin: 0; font-size: 2rem;'>Seralung Finance</h1>", unsafe_allow_html=True)
    st.caption("Track • Spend • Build")
with col2:
    st.markdown(f"<p style='text-align: right; margin: 0; color: {MU};'>{datetime.now().strftime('%a, %d %b')}</p>", unsafe_allow_html=True)

st.divider()

# Income section
st.markdown("**Income & Budget Allocation**")
ic1, ic2, ic3, ic4, ic5 = st.columns(5)
with ic1:
    pi = st.number_input("Take home /mo ($)", value=float(st.session_state.primary_income), step=100.0, key="pi")
    st.session_state.primary_income = pi
with ic2:
    oi = st.number_input("Other income /mo ($)", value=float(st.session_state.other_income), step=50.0, key="oi")
    st.session_state.other_income = oi
with ic3:
    np = st.slider("Needs %", 0, 100, st.session_state.needs_pct, key="np")
    st.session_state.needs_pct = np
with ic4:
    wp = st.slider("Wants %", 0, 100, st.session_state.wants_pct, key="wp")
    st.session_state.wants_pct = wp
with ic5:
    ip = st.slider("Save %", 0, 100, st.session_state.invest_pct, key="ip")
    st.session_state.invest_pct = ip

total_income = pi + oi
total_sub = sum(s["amount"] for s in st.session_state.subscriptions)
total_exp = sum(e["amount"] for e in st.session_state.expenses) + total_sub
total_assets = sum(a["value"] for a in st.session_state.assets)
total_liab = sum(l["balance"] for l in st.session_state.liabilities)
net_worth = total_assets - total_liab
cash_flow = total_income - total_exp
investable = total_income * st.session_state.invest_pct / 100
cash_assets = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash", "Savings"])
em_months = cash_assets / total_exp if total_exp > 0 else 0
hs = health_score()

# Check percentages sum to 100
psum = st.session_state.needs_pct + st.session_state.wants_pct + st.session_state.invest_pct
if psum != 100:
    st.warning(f"⚠️ Budget percentages sum to {psum}% — must equal 100%")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD METRICS
# ─────────────────────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Health Score", f"{hs}/100", f"{'✓ Great' if hs >= 70 else '⚠ Good' if hs >= 50 else '✗ Low'}")
m2.metric("Net Worth", fmt(net_worth), f"+{fmt(net_worth-total_assets+total_liab)}" if net_worth > 0 else "")
m3.metric("Monthly Flow", fmt(cash_flow), "Surplus" if cash_flow >= 0 else "Deficit")
m4.metric("Savings Rate", pct((cash_flow/total_income*100) if total_income > 0 else 0), "Target: 20%")
m5.metric("Emergency Fund", f"{em_months:.1f}mo", f"Target: 6mo" if em_months < 6 else "✓ Secure")
m6.metric("Investable", fmt(investable), f"{st.session_state.invest_pct}% of income")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Budget", "Goals", "Investments", "Reports"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OVERVIEW TAB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    ov1, ov2 = st.columns(2, gap="large")
    
    with ov1:
        st.markdown("### Budget Allocation (50/30/20 Rule)")
        needs_actual = sum(e["amount"] for e in st.session_state.expenses if e.get("category") in ["Housing", "Transport", "Health"])
        wants_actual = sum(e["amount"] for e in st.session_state.expenses if e.get("category") not in ["Housing", "Transport", "Health"]) + total_sub
        
        for lbl, actual, budget, color in [
            ("Needs", needs_actual, total_income * np / 100, GR),
            ("Wants", wants_actual, total_income * wp / 100, AM),
            ("Save & Invest", investable, investable, BL),
        ]:
            pct_val = min(100, actual / budget * 100) if budget > 0 else 0
            st.markdown(f"<div class='metric'><strong>{lbl}</strong> {fmt(actual)} / {fmt(budget)} ({pct_val:.0f}%)</div>", unsafe_allow_html=True)
            st.progress(pct_val / 100, text=f"{pct_val:.0f}%")
        
        # Expense chart
        st.markdown("### Spending by Category")
        if st.session_state.expenses:
            df_exp = pd.DataFrame(st.session_state.expenses)
            cat_summary = df_exp.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)
            
            fig = go.Figure(go.Pie(
                labels=cat_summary["category"],
                values=cat_summary["amount"],
                marker=dict(colors=[GR, BL, AM, RD, "#7C3AED", "#0891B2"] * 2),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>"
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color=MU, size=11),
                height=320,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    with ov2:
        st.markdown("### Key Insights")
        
        # Action items
        issues = []
        if em_months < 3:
            issues.append(("🔴", "Emergency fund critical", f"Only {em_months:.1f}mo. Target: {fmt(total_exp * 6)}"))
        elif em_months < 6:
            issues.append(("🟡", "Build emergency fund", f"Need {fmt(total_exp * 6 - cash_assets)} more"))
        
        sr = (cash_flow / total_income * 100) if total_income > 0 else 0
        if sr < 10:
            issues.append(("🔴", "Savings rate too low", f"Only {sr:.1f}%. Need 20%."))
        elif sr < 20:
            issues.append(("🟡", "Below savings target", f"Need {fmt(total_income * 0.2 - cash_flow)}/mo more"))
        
        hi_debt = [l for l in st.session_state.liabilities if l.get("rate", 0) > 15]
        if hi_debt:
            total_hi = sum(l["balance"] for l in hi_debt)
            issues.append(("🔴", "High-interest debt", f"{fmt(total_hi)} at >15%. Pay down ASAP."))
        
        over_budget = [e for e in st.session_state.expenses if e["amount"] > e.get("budget", e["amount"])]
        if over_budget:
            issues.append(("🟡", "Over budget", f"{len(over_budget)} categories over limit"))
        
        if total_sub > 100:
            issues.append(("🟡", "Subscriptions high", f"{fmt(total_sub)}/mo = {fmt(total_sub * 12)}/yr"))
        
        if not issues:
            issues = [("✅", "All systems healthy", "Keep this up!")]
        
        for emoji, title, detail in issues[:5]:
            st.markdown(f"<div class='card'><strong>{emoji} {title}</strong><br><small style='color: {MU};'>{detail}</small></div>", unsafe_allow_html=True)
        
        # Net worth breakdown
        st.markdown("### Net Worth")
        st.markdown(f"<h2 style='color: {GR if net_worth > 0 else RD}; text-align: center; margin: 1rem 0;'>{fmt(net_worth)}</h2>", unsafe_allow_html=True)
        
        assets_col, liab_col = st.columns(2)
        with assets_col:
            st.markdown(f"<strong style='color: {GR};'>Assets: {fmt(total_assets)}</strong>")
            for asset in sorted(st.session_state.assets, key=lambda x: x["value"], reverse=True)[:4]:
                st.caption(f"{asset['name']}: {fmt(asset['value'])}")
        
        with liab_col:
            st.markdown(f"<strong style='color: {RD};'>Liabilities: {fmt(total_liab)}</strong>")
            for liab in sorted(st.session_state.liabilities, key=lambda x: x["balance"], reverse=True)[:4]:
                st.caption(f"{liab['name']}: {fmt(liab['balance'])} @ {liab['rate']:.1f}%")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUDGET TAB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    b1, b2 = st.columns([2, 1.5], gap="large")
    
    with b1:
        st.markdown("### Expenses")
        to_delete = None
        for i, exp in enumerate(st.session_state.expenses):
            cols = st.columns([2.5, 1, 1, 1, 1.5, 0.4])
            with cols[0]:
                st.session_state.expenses[i]["name"] = st.text_input(
                    f"Name {i}", value=exp["name"], label_visibility="collapsed", key=f"e_name_{i}"
                )
            with cols[1]:
                st.session_state.expenses[i]["amount"] = st.number_input(
                    f"Amt {i}", value=float(exp["amount"]), min_value=0.0, step=10.0,
                    label_visibility="collapsed", key=f"e_amt_{i}", format="%.0f"
                )
            with cols[2]:
                st.session_state.expenses[i]["budget"] = st.number_input(
                    f"Budget {i}", value=float(exp.get("budget", exp["amount"])), min_value=0.0, step=10.0,
                    label_visibility="collapsed", key=f"e_bud_{i}", format="%.0f"
                )
            with cols[3]:
                cat_idx = CATEGORIES.index(exp.get("category", "Other"))
                st.session_state.expenses[i]["category"] = st.selectbox(
                    f"Cat {i}", CATEGORIES, index=cat_idx, label_visibility="collapsed", key=f"e_cat_{i}"
                )
            with cols[4]:
                spent = exp["amount"]
                budget = exp.get("budget", exp["amount"])
                pct_val = min(100, spent / budget * 100) if budget > 0 else 0
                color = "🟢" if pct_val <= 85 else "🟡" if pct_val <= 100 else "🔴"
                st.caption(f"{color} {pct_val:.0f}%")
            with cols[5]:
                if st.button("✕", key=f"e_del_{i}"):
                    to_delete = i
        
        if to_delete is not None:
            st.session_state.expenses.pop(to_delete)
            st.rerun()
        
        # Add new
        st.markdown("**Add Expense**")
        ac1, ac2, ac3, ac4, ac5 = st.columns([2.5, 1, 1, 1, 1.5])
        with ac1:
            new_name = st.text_input("Name", placeholder="e.g., Coffee", key="new_exp_name", label_visibility="collapsed")
        with ac2:
            new_amt = st.number_input("Amount", min_value=0.0, step=10.0, key="new_exp_amt", label_visibility="collapsed", format="%.0f")
        with ac3:
            new_bud = st.number_input("Budget", min_value=0.0, step=10.0, key="new_exp_bud", label_visibility="collapsed", format="%.0f")
        with ac4:
            new_cat = st.selectbox("Category", CATEGORIES, key="new_exp_cat", label_visibility="collapsed")
        with ac5:
            if st.button("+ Add", use_container_width=True):
                if new_name:
                    st.session_state.expenses.append({
                        "name": new_name,
                        "amount": float(new_amt),
                        "budget": float(new_bud) if new_bud > 0 else float(new_amt),
                        "category": new_cat
                    })
                    st.rerun()
    
    with b2:
        st.markdown("### Subscriptions")
        st.markdown(f"**Total: {fmt(total_sub)}/mo = {fmt(total_sub * 12)}/yr**")
        
        to_del_sub = None
        for i, sub in enumerate(st.session_state.subscriptions):
            sc1, sc2, sc3 = st.columns([2.5, 1, 0.4])
            with sc1:
                st.session_state.subscriptions[i]["name"] = st.text_input(
                    f"Sub {i}", value=sub["name"], label_visibility="collapsed", key=f"s_name_{i}"
                )
            with sc2:
                st.session_state.subscriptions[i]["amount"] = st.number_input(
                    f"Sub amt {i}", value=float(sub["amount"]), min_value=0.0, step=0.5,
                    label_visibility="collapsed", key=f"s_amt_{i}", format="%.2f"
                )
            with sc3:
                if st.button("✕", key=f"s_del_{i}"):
                    to_del_sub = i
        
        if to_del_sub is not None:
            st.session_state.subscriptions.pop(to_del_sub)
            st.rerun()
        
        st.markdown("**Add**")
        ss1, ss2 = st.columns([2.5, 1])
        with ss1:
            new_sub_name = st.text_input("Service", placeholder="e.g., Netflix", key="new_sub_name", label_visibility="collapsed")
        with ss2:
            new_sub_amt = st.number_input("$/mo", min_value=0.0, step=0.5, key="new_sub_amt", label_visibility="collapsed", format="%.2f")
        
        if st.button("+ Add Subscription", use_container_width=True):
            if new_sub_name:
                st.session_state.subscriptions.append({"name": new_sub_name, "amount": float(new_sub_amt)})
                st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOALS TAB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    g1, g2 = st.columns([2, 1.2], gap="large")
    
    with g1:
        st.markdown("### Your Goals")
        
        total_target = sum(g["target"] for g in st.session_state.goals)
        total_saved = sum(g["saved"] for g in st.session_state.goals)
        
        gm1, gm2, gm3, gm4 = st.columns(4)
        gm1.metric("Total Target", fmt(total_target))
        gm2.metric("Total Saved", fmt(total_saved))
        gm3.metric("Remaining", fmt(max(0, total_target - total_saved)))
        gm4.metric("Progress", pct(total_saved / total_target * 100) if total_target > 0 else "0%")
        
        st.divider()
        
        to_del_goal = None
        for i, goal in enumerate(st.session_state.goals):
            target = goal["target"]
            saved = goal["saved"]
            remaining = max(0, target - saved)
            progress = min(100, saved / target * 100) if target > 0 else 0
            months_left = math.ceil(remaining / investable) if investable > 0 and remaining > 0 else 0
            
            with st.container(border=True):
                gc1, gc2 = st.columns([3, 0.4])
                with gc1:
                    st.markdown(f"**{goal['name']}** — {goal.get('priority', 'Medium')} priority")
                    st.progress(progress / 100, text=f"{progress:.0f}% complete")
                    st.caption(f"Saved: {fmt(saved)} / {fmt(target)} | Remaining: {fmt(remaining)}")
                    if months_left > 0:
                        st.caption(f"⏱️ {months_left} months at {fmt(investable)}/mo")
                with gc2:
                    if st.button("✕", key=f"g_del_{i}"):
                        to_del_goal = i
                
                # Update saved amount
                new_saved = st.number_input(
                    f"Update {goal['name']}", min_value=0.0, value=float(saved),
                    max_value=float(target * 1.5), step=100.0, key=f"g_saved_{i}", format="%.0f", label_visibility="collapsed"
                )
                st.session_state.goals[i]["saved"] = new_saved
        
        if to_del_goal is not None:
            st.session_state.goals.pop(to_del_goal)
            st.rerun()
    
    with g2:
        st.markdown("### Add Goal")
        new_goal_name = st.text_input("Goal name", placeholder="e.g., House")
        new_goal_target = st.number_input("Target ($)", min_value=0.0, step=1000.0, format="%.0f")
        new_goal_saved = st.number_input("Already saved ($)", min_value=0.0, step=100.0, format="%.0f")
        new_goal_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        
        if st.button("+ Add Goal", use_container_width=True):
            if new_goal_name and new_goal_target > 0:
                st.session_state.goals.append({
                    "name": new_goal_name,
                    "target": float(new_goal_target),
                    "saved": float(new_goal_saved),
                    "priority": new_goal_priority
                })
                st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INVESTMENTS TAB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.markdown(f"<div class='tip'><strong>{fmt(investable)}/month</strong> available for investing ({st.session_state.invest_pct}% of income)</div>", unsafe_allow_html=True)
    
    i1, i2 = st.columns(2, gap="large")
    
    with i1:
        st.markdown("### Assets")
        to_del_asset = None
        for i, asset in enumerate(st.session_state.assets):
            ac1, ac2, ac3, ac4 = st.columns([2, 1.5, 1.2, 0.4])
            with ac1:
                st.session_state.assets[i]["name"] = st.text_input(
                    f"Asset {i}", value=asset["name"], label_visibility="collapsed", key=f"a_name_{i}"
                )
            with ac2:
                type_idx = ASSET_TYPES.index(asset.get("type", "Savings"))
                st.session_state.assets[i]["type"] = st.selectbox(
                    f"Type {i}", ASSET_TYPES, index=type_idx, label_visibility="collapsed", key=f"a_type_{i}"
                )
            with ac3:
                st.session_state.assets[i]["value"] = st.number_input(
                    f"Val {i}", value=float(asset["value"]), min_value=0.0, step=1000.0,
                    label_visibility="collapsed", key=f"a_val_{i}", format="%.0f"
                )
            with ac4:
                if st.button("✕", key=f"a_del_{i}"):
                    to_del_asset = i
        
        if to_del_asset is not None:
            st.session_state.assets.pop(to_del_asset)
            st.rerun()
        
        st.markdown("**Add Asset**")
        ana1, ana2, ana3 = st.columns([2, 1.5, 1.2])
        with ana1:
            new_asset_name = st.text_input("Name", placeholder="e.g., Shares", key="new_asset_name", label_visibility="collapsed")
        with ana2:
            new_asset_type = st.selectbox("Type", ASSET_TYPES, key="new_asset_type", label_visibility="collapsed")
        with ana3:
            new_asset_val = st.number_input("Value", min_value=0.0, step=1000.0, key="new_asset_val", label_visibility="collapsed", format="%.0f")
        
        if st.button("+ Add Asset", use_container_width=True):
            if new_asset_name:
                st.session_state.assets.append({
                    "name": new_asset_name,
                    "type": new_asset_type,
                    "value": float(new_asset_val)
                })
                st.rerun()
    
    with i2:
        st.markdown("### Liabilities")
        to_del_liab = None
        for i, liab in enumerate(st.session_state.liabilities):
            lc1, lc2, lc3, lc4, lc5 = st.columns([1.8, 1, 0.8, 0.8, 0.4])
            with lc1:
                st.session_state.liabilities[i]["name"] = st.text_input(
                    f"Liab {i}", value=liab["name"], label_visibility="collapsed", key=f"l_name_{i}"
                )
            with lc2:
                type_idx = LIABILITY_TYPES.index(liab.get("type", "Loan"))
                st.session_state.liabilities[i]["type"] = st.selectbox(
                    f"Ltype {i}", LIABILITY_TYPES, index=type_idx, label_visibility="collapsed", key=f"l_type_{i}"
                )
            with lc3:
                st.session_state.liabilities[i]["balance"] = st.number_input(
                    f"Bal {i}", value=float(liab["balance"]), min_value=0.0, step=1000.0,
                    label_visibility="collapsed", key=f"l_bal_{i}", format="%.0f"
                )
            with lc4:
                st.session_state.liabilities[i]["rate"] = st.number_input(
                    f"Rate {i}", value=float(liab.get("rate", 5.0)), min_value=0.0, max_value=30.0, step=0.1,
                    label_visibility="collapsed", key=f"l_rate_{i}", format="%.1f"
                )
            with lc5:
                if st.button("✕", key=f"l_del_{i}"):
                    to_del_liab = i
        
        if to_del_liab is not None:
            st.session_state.liabilities.pop(to_del_liab)
            st.rerun()
        
        st.markdown("**Add Liability**")
        lna1, lna2, lna3, lna4 = st.columns([1.8, 1, 0.8, 0.8])
        with lna1:
            new_liab_name = st.text_input("Name", placeholder="e.g., Car loan", key="new_liab_name", label_visibility="collapsed")
        with lna2:
            new_liab_type = st.selectbox("Type", LIABILITY_TYPES, key="new_liab_type", label_visibility="collapsed")
        with lna3:
            new_liab_bal = st.number_input("Balance", min_value=0.0, step=1000.0, key="new_liab_bal", label_visibility="collapsed", format="%.0f")
        with lna4:
            new_liab_rate = st.number_input("Rate %", min_value=0.0, max_value=30.0, step=0.1, key="new_liab_rate", label_visibility="collapsed", format="%.1f")
        
        if st.button("+ Add Liability", use_container_width=True):
            if new_liab_name:
                st.session_state.liabilities.append({
                    "name": new_liab_name,
                    "type": new_liab_type,
                    "balance": float(new_liab_bal),
                    "rate": float(new_liab_rate)
                })
                st.rerun()
    
    st.divider()
    
    # FIRE Calculator
    st.markdown("### FIRE Calculator (Financial Independence)")
    fire_col1, fire_col2 = st.columns(2)
    
    with fire_col1:
        annual_exp = st.number_input("Annual expenses ($)", value=float(total_exp * 12), step=1000.0, format="%.0f")
        current_inv = st.number_input("Current investments ($)", value=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments", "Savings"])), step=1000.0, format="%.0f")
        return_rate = st.slider("Expected return % p.a.", 1.0, 12.0, 7.0, 0.5)
    
    with fire_col2:
        fire_number = annual_exp * 25
        fire_ratio = (current_inv / fire_number * 100) if fire_number > 0 else 0
        years_to_fire = 0
        test_val = current_inv
        for yr in range(60):
            if test_val >= fire_number:
                years_to_fire = yr
                break
            test_val = (test_val + investable * 12) * (1 + return_rate / 100)
        
        st.markdown(f"<div class='metric'><strong>FIRE Number (25x rule)</strong><br>{fmt(fire_number)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric'><strong>FI Ratio</strong><br>{fire_ratio:.1f}%</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric'><strong>Years to FIRE</strong><br>{years_to_fire} years (age {st.session_state.get('age', 32) + years_to_fire})</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REPORTS TAB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab5:
    st.markdown("### Export Data")
    
    # CSV Export
    def gen_csv():
        lines = []
        lines.append(f"Seralung Finance Report - {datetime.now().strftime('%B %Y')}")
        lines.append(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}\n")
        
        lines.append("SUMMARY")
        sr = (cash_flow / total_income * 100) if total_income > 0 else 0
        lines.append(f"Health Score,{hs}/100")
        lines.append(f"Monthly Income,{total_income:.2f}")
        lines.append(f"Monthly Expenses,{total_exp:.2f}")
        lines.append(f"Cash Flow,{cash_flow:.2f}")
        lines.append(f"Savings Rate,{sr:.1f}%")
        lines.append(f"Net Worth,{net_worth:.2f}")
        lines.append(f"Emergency Fund,{em_months:.1f} months\n")
        
        lines.append("EXPENSES")
        lines.append("Name,Category,Amount,Budget,Over")
        for e in st.session_state.expenses:
            over = "YES" if e["amount"] > e.get("budget", e["amount"]) else "NO"
            lines.append(f"{e['name']},{e.get('category', '')},{e['amount']:.2f},{e.get('budget', e['amount']):.2f},{over}")
        
        lines.append("\nGOALS")
        lines.append("Name,Target,Saved,Remaining,Progress")
        for g in st.session_state.goals:
            remaining = max(0, g["target"] - g["saved"])
            progress = (g["saved"] / g["target"] * 100) if g["target"] > 0 else 0
            lines.append(f"{g['name']},{g['target']:.2f},{g['saved']:.2f},{remaining:.2f},{progress:.1f}%")
        
        lines.append("\nASSETS")
        lines.append("Name,Type,Value")
        for a in st.session_state.assets:
            lines.append(f"{a['name']},{a['type']},{a['value']:.2f}")
        
        lines.append("\nLIABILITIES")
        lines.append("Name,Type,Balance,Rate")
        for l in st.session_state.liabilities:
            lines.append(f"{l['name']},{l['type']},{l['balance']:.2f},{l['rate']:.2f}")
        
        return "\n".join(lines)
    
    csv_data = gen_csv()
    st.download_button(
        "📥 Download CSV Report",
        data=csv_data.encode(),
        file_name=f"seralung_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.divider()
    
    # JSON Backup
    st.markdown("### Backup & Restore")
    backup_data = {
        "expenses": st.session_state.expenses,
        "subscriptions": st.session_state.subscriptions,
        "assets": st.session_state.assets,
        "liabilities": st.session_state.liabilities,
        "goals": st.session_state.goals,
        "income": {
            "primary": st.session_state.primary_income,
            "other": st.session_state.other_income,
            "needs_pct": st.session_state.needs_pct,
            "wants_pct": st.session_state.wants_pct,
            "invest_pct": st.session_state.invest_pct,
        },
        "exported_at": datetime.now().isoformat()
    }
    
    st.download_button(
        "💾 Download Backup",
        data=json.dumps(backup_data, indent=2, default=str).encode(),
        file_name=f"seralung_backup_{datetime.now().strftime('%Y-%m-%d')}.json",
        mime="application/json",
        use_container_width=True
    )
    
    st.markdown("**Restore from backup:**")
    uploaded = st.file_uploader("Upload JSON backup", type=["json"])
    if uploaded:
        try:
            data = json.loads(uploaded.read().decode())
            if st.button("✓ Restore", use_container_width=True):
                if "expenses" in data:
                    st.session_state.expenses = data["expenses"]
                if "subscriptions" in data:
                    st.session_state.subscriptions = data["subscriptions"]
                if "assets" in data:
                    st.session_state.assets = data["assets"]
                if "liabilities" in data:
                    st.session_state.liabilities = data["liabilities"]
                if "goals" in data:
                    st.session_state.goals = data["goals"]
                if "income" in data:
                    inc = data["income"]
                    st.session_state.primary_income = inc.get("primary", 6000)
                    st.session_state.other_income = inc.get("other", 500)
                    st.session_state.needs_pct = inc.get("needs_pct", 50)
                    st.session_state.wants_pct = inc.get("wants_pct", 30)
                    st.session_state.invest_pct = inc.get("invest_pct", 20)
                st.success("✓ Restored!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Invalid backup: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Seralung Finance · Educational use only · Not financial advice · Always consult a professional")
