"""
FINORA — AI Financial Planner Web App
Run: streamlit run finora_app.py
Share: Deploy to https://streamlit.io/cloud (free)
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime
import math
import pandas as pd

# ── PAGE CONFIG ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finora — Financial Planner",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS — Premium dark theme ─────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
}

section[data-testid="stSidebar"] {
    background: #0f0f1a;
    border-right: 1px solid #1e1e2e;
}

.fin-card {
    background: linear-gradient(135deg, #13131f 0%, #1a1a2e 100%);
    border: 1px solid #2a2a42;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
}

.metric-card {
    background: linear-gradient(135deg, #13131f 0%, #1a1a2e 100%);
    border: 1px solid #2a2a42;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.metric-label {
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6b6b8a;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 28px;
    color: #e8e8f0;
}

.insight-card {
    background: #0f1629;
    border: 1px solid #1e3a5f;
    border-left: 3px solid #4f46e5;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 14px;
}
.insight-card.warning { border-left-color: #f59e0b; }
.insight-card.danger  { border-left-color: #f87171; }
.insight-card.success { border-left-color: #34d399; }
</style>
""", unsafe_allow_html=True)

st.title("💰 AI Financial Planner")

# ── INPUTS ──────────────────────────────────────────────────────────
st.sidebar.header("Your Financial Data")

income = st.sidebar.number_input("Monthly Income", 0)
expenses = st.sidebar.number_input("Monthly Expenses", 0)
savings = st.sidebar.number_input("Total Savings", 0)
debt = st.sidebar.number_input("Total Debt", 0)

# ── CALCULATIONS ────────────────────────────────────────────────────
needs = income * 0.5
wants = income * 0.3
invest = income * 0.2

net_worth = savings - debt
savings_rate = (savings / income * 100) if income > 0 else 0

# 💡 Financial Health Score
score = 50
if income > 0:
    score += min(savings_rate * 0.5, 25)
    score -= min((debt / income) * 20, 30)

score = max(0, min(100, score))

# 📊 Insight
if score >= 80:
    insight = "Excellent financial health."
elif score >= 60:
    insight = "Good financial position."
elif score >= 40:
    insight = "Moderate financial risk."
else:
    insight = "High financial risk."

# ⚠️ Warning
warning = ""
if debt > savings:
    warning = "⚠️ Your debt is higher than your savings!"

# ── DASHBOARD ───────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metric-card"><div class="metric-label">Score</div>'
                f'<div class="metric-value">{score:.0f}/100</div></div>',
                unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card"><div class="metric-label">Net Worth</div>'
                f'<div class="metric-value">{net_worth:,.0f}</div></div>',
                unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card"><div class="metric-label">Savings Rate</div>'
                f'<div class="metric-value">{savings_rate:.1f}%</div></div>',
                unsafe_allow_html=True)

st.markdown("### 📊 Monthly Insight")
st.info(insight)

if warning:
    st.error(warning)

# ── 50/30/20 ─────────────────────────────────────────────────────────
st.subheader("50/30/20 Breakdown")
st.write("Needs:", needs)
st.write("Wants:", wants)
st.write("Invest:", invest)
