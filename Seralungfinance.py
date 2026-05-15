"""
Seralung Finance — Premium Edition
Inspired by YNAB, Monarch Money, Copilot, Wealthfront

requirements.txt:
    streamlit>=1.32
    plotly>=5.18
    pandas>=2.0
    fpdf2>=2.7
    numpy>=1.24
    requests>=2.28

Run:  streamlit run seralung_premium.py
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math, io, json, csv, requests
from datetime import datetime, date

try:
    from fpdf import FPDF
    PDF_OK = True
except ImportError:
    PDF_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Seralung Finance",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# THEMES
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "Obsidian": {
        "bg":"#090E1A","surface":"#111827","surface2":"#1C2639","surface3":"#243047",
        "border":"#1F2D45","accent":"#10B981","accent2":"#059669","accent_glow":"rgba(16,185,129,0.15)",
        "text":"#F0F6FF","muted":"#6B7A99","green":"#10B981","red":"#EF4444",
        "amber":"#F59E0B","blue":"#3B82F6","purple":"#8B5CF6",
        "chart":["#10B981","#3B82F6","#F59E0B","#EF4444","#8B5CF6","#06B6D4","#EC4899"],"dark":True,
        "grad":"linear-gradient(135deg,#10B981 0%,#3B82F6 100%)",
    },
    "Arctic": {
        "bg":"#F0F5FF","surface":"#FFFFFF","surface2":"#EBF2FF","surface3":"#DCEEFF",
        "border":"#C8DEFF","accent":"#1D4ED8","accent2":"#1E40AF","accent_glow":"rgba(29,78,216,0.1)",
        "text":"#0F1C3F","muted":"#5A6E8A","green":"#059669","red":"#DC2626",
        "amber":"#D97706","blue":"#1D4ED8","purple":"#7C3AED",
        "chart":["#1D4ED8","#059669","#D97706","#DC2626","#7C3AED","#0891B2","#BE185D"],"dark":False,
        "grad":"linear-gradient(135deg,#1D4ED8 0%,#7C3AED 100%)",
    },
    "Midnight": {
        "bg":"#060914","surface":"#0D1224","surface2":"#141B33","surface3":"#1B2444",
        "border":"#1E2D50","accent":"#818CF8","accent2":"#6366F1","accent_glow":"rgba(129,140,248,0.15)",
        "text":"#E2E8FF","muted":"#5C6B9A","green":"#34D399","red":"#F87171",
        "amber":"#FCD34D","blue":"#818CF8","purple":"#A78BFA",
        "chart":["#818CF8","#34D399","#FCD34D","#F87171","#A78BFA","#38BDF8","#F472B6"],"dark":True,
        "grad":"linear-gradient(135deg,#818CF8 0%,#38BDF8 100%)",
    },
    "Emerald": {
        "bg":"#F0FBF7","surface":"#FFFFFF","surface2":"#E8F8F1","surface3":"#D1F0E2",
        "border":"#A7DFCC","accent":"#059669","accent2":"#047857","accent_glow":"rgba(5,150,105,0.1)",
        "text":"#052E1C","muted":"#3D7060","green":"#059669","red":"#DC2626",
        "amber":"#D97706","blue":"#2563EB","purple":"#7C3AED",
        "chart":["#059669","#2563EB","#D97706","#DC2626","#7C3AED","#0891B2","#DB2777"],"dark":False,
        "grad":"linear-gradient(135deg,#059669 0%,#2563EB 100%)",
    },
}

CATEGORIES  = ["Housing","Food","Transport","Health","Insurance","Tech","Entertainment","Personal","Education","Other"]
ASSET_TYPES = ["Cash","Savings","Investments","Super","Property","Vehicle","Business","Other"]
LIAB_TYPES  = ["Mortgage","Loan","Credit","HECS","Personal","Business","Other"]
RISK_LABELS = ["Very Conservative","Conservative","Moderate","Growth","Aggressive"]
RISK_SCORES = [15, 30, 50, 70, 90]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def _i(k, v):
    if k not in st.session_state: st.session_state[k] = v

_i("expenses",[
    {"name":"Rent","amount":1800.0,"budget":2000.0,"category":"Housing"},
    {"name":"Groceries","amount":450.0,"budget":500.0,"category":"Food"},
    {"name":"Transport","amount":250.0,"budget":300.0,"category":"Transport"},
    {"name":"Dining","amount":350.0,"budget":300.0,"category":"Food"},
    {"name":"Utilities","amount":180.0,"budget":220.0,"category":"Housing"},
    {"name":"Phone","amount":85.0,"budget":85.0,"category":"Tech"},
    {"name":"Insurance","amount":150.0,"budget":200.0,"category":"Insurance"},
    {"name":"Entertainment","amount":120.0,"budget":150.0,"category":"Entertainment"},
    {"name":"Health","amount":80.0,"budget":100.0,"category":"Health"},
    {"name":"Clothing","amount":80.0,"budget":100.0,"category":"Personal"},
])
_i("subscriptions",[
    {"name":"Netflix","amount":18.0},{"name":"Spotify","amount":12.0},
    {"name":"Amazon Prime","amount":9.99},{"name":"Gym","amount":45.0},
    {"name":"Cloud Storage","amount":5.0},
])
_i("bills",[
    {"name":"Rent","amount":1800.0,"due_day":1},{"name":"Electricity","amount":180.0,"due_day":15},
    {"name":"Internet","amount":90.0,"due_day":20},{"name":"Phone","amount":85.0,"due_day":25},
])
_i("assets",[
    {"name":"Savings Account","type":"Cash","value":12000.0},
    {"name":"Superannuation","type":"Super","value":35000.0},
    {"name":"Car","type":"Vehicle","value":18000.0},
    {"name":"ETF Portfolio","type":"Investments","value":8500.0},
])
_i("liabilities",[
    {"name":"Car Loan","type":"Loan","balance":14000.0,"rate":6.5,"min_payment":350.0},
    {"name":"Credit Card","type":"Credit","balance":2800.0,"rate":19.99,"min_payment":84.0},
    {"name":"HECS Debt","type":"HECS","balance":18000.0,"rate":3.9,"min_payment":200.0},
])
_i("goals",[
    {"name":"Emergency Fund","amount":15000.0,"saved":12000.0,"priority":"High"},
    {"name":"Europe Holiday","amount":8000.0,"saved":2000.0,"priority":"Medium"},
    {"name":"Property Deposit","amount":80000.0,"saved":25000.0,"priority":"High"},
])
_i("transactions",[])
_i("chat_history",[])
_i("needs_pct",50); _i("wants_pct",30); _i("invest_pct",20)
_i("em_pct",30); _i("idx_pct",40); _i("stk_pct",20); _i("cry_pct",10)
_i("risk_profile","Moderate"); _i("age",32); _i("retirement_age",65)
_i("streak_days",14); _i("total_saved_this_year",8400.0)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt(n):    return f"${n:,.0f}"
def fmtk(n):   return f"${n/1000:.0f}k" if abs(n)>=1000 else fmt(n)
def pct(n):    return f"{n:.1f}%"

def h2rgba(hx, a=0.15):
    h=hx.lstrip("#"); r,g,b=int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
    return f"rgba({r},{g},{b},{a})"

def calc_tax(income):
    if   income<=18200:  return 0.0
    elif income<=45000:  return (income-18200)*0.19
    elif income<=135000: return 5092+(income-45000)*0.325
    elif income<=190000: return 31288+(income-135000)*0.37
    else:                return 51638+(income-190000)*0.45

def calc_lito(income):
    if   income<=37500: return 700.0
    elif income<=45000: return 700-(income-37500)*0.05
    elif income<=66667: return 325-(income-45000)*0.015
    else:               return 0.0

def _p(text):
    """Latin-1-safe text for FPDF (fixes FPDFUnicodeEncodingException)."""
    text=str(text)
    for u,a in {'\u2014':' - ','\u2013':'-','\u2018':"'",'\u2019':"'",'\u201c':'"','\u201d':'"','\u00b7':'.', '\u2022':'*'}.items():
        text=text.replace(u,a)
    return text.encode('latin-1',errors='replace').decode('latin-1')

def monte_carlo(initial, monthly, years=25, n=200, mu=0.07, sigma=0.15):
    months = years*12
    res = np.zeros((n, months+1)); res[:,0]=initial
    mm, ms = mu/12, sigma/math.sqrt(12)
    for t in range(1, months+1):
        ret = np.random.normal(mm, ms, n)
        res[:,t] = res[:,t-1]*(1+ret)+monthly
    return res

def health_score_calc():
    score, det = 0, {}
    mexp = sum(e["amount"] for e in st.session_state.expenses) + sum(s["amount"] for s in st.session_state.subscriptions)
    sr = max(0,(total_income-mexp)/total_income*100) if total_income>0 else 0
    s1 = min(25,sr/20*25); score+=s1
    det["Savings Rate"]     = {"score":s1,"max":25,"val":pct(sr),"ok":sr>=20,"desc":f"Target 20%. You're at {sr:.1f}%."}
    cash = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
    em = cash/mexp if mexp>0 else 0
    s2 = min(20,em/6*20); score+=s2
    det["Emergency Fund"]   = {"score":s2,"max":20,"val":f"{em:.1f} mo","ok":em>=6,"desc":f"Target 6 months. You have {em:.1f}."}
    nd = sum(l["balance"] for l in st.session_state.liabilities if l["type"]!="HECS")
    dti = nd/(total_income*12)*100 if total_income>0 else 0
    s3 = max(0,20-dti*0.5); score+=s3
    det["Debt-to-Income"]   = {"score":s3,"max":20,"val":pct(dti),"ok":dti<=36,"desc":f"Target under 36%. Yours is {dti:.0f}%."}
    nw = sum(a["value"] for a in st.session_state.assets)-sum(l["balance"] for l in st.session_state.liabilities)
    s4 = 15 if nw>0 else max(0,15+nw/10000); score+=s4
    det["Net Worth"]        = {"score":s4,"max":15,"val":fmt(nw),"ok":nw>0,"desc":"Positive net worth is the foundation."}
    over = sum(max(0,e["amount"]-e.get("budget",e["amount"])) for e in st.session_state.expenses)
    s5 = max(0,10-over/100); score+=s5
    det["Budget Control"]   = {"score":s5,"max":10,"val":f"{fmt(over)} over","ok":over==0,"desc":"No over-budget items is ideal."}
    s6 = min(10,len(st.session_state.goals)*3.5); score+=s6
    det["Goal Progress"]    = {"score":s6,"max":10,"val":f"{len(st.session_state.goals)} goals","ok":len(st.session_state.goals)>=2,"desc":"Track 3+ goals for full points."}
    return round(score), det

def get_badges():
    blist=[]
    if em_months>=6:    blist.append(("Emergency Pro","6+ months saved","green"))
    if savings_rate>=20: blist.append(("20% Achiever","Saving 20%+ monthly","green"))
    if savings_rate>=10 and savings_rate<20: blist.append(("Building Momentum","10%+ savings","blue"))
    if len(st.session_state.goals)>=3: blist.append(("Goal Crusher","3+ active goals","purple"))
    if net_worth>50000:  blist.append(("50k Club","Net worth over 50k","gold"))
    if net_worth>0:      blist.append(("Positive Territory","Net worth is positive","green"))
    if total_liab==0:    blist.append(("Debt Free","Zero liabilities","green"))
    if st.session_state.streak_days>=7: blist.append((f"{st.session_state.streak_days}-Day Streak","Consistent budgeting","amber"))
    if not blist:       blist.append(("Getting Started","First steps to financial health","blue"))
    return blist

def ask_claude(messages_hist, api_key, ctx):
    sys_prompt = f"""You are a premium AI financial advisor for Seralung Finance (Australian).
Financial context:
- Monthly income: {fmt(total_income)} | Annual: {fmt(total_income*12)}
- Monthly expenses: {fmt(total_exp)} | Savings rate: {savings_rate:.1f}%
- Net worth: {fmt(net_worth)} | Cash flow: {fmt(cash_flow)}
- Emergency fund: {em_months:.1f} months (target 6)
- Financial health score: {hs}/100
- Total debt: {fmt(total_liab)} | Assets: {fmt(total_assets)}
- Investment amount available: {fmt(investable)}/month
- Goals: {', '.join(g['name'] for g in st.session_state.goals)}

Give concise, actionable, personalised Australian financial advice. Use AUD. Be specific with numbers. Keep responses under 200 words unless a complex question requires more."""
    try:
        resp=requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key":api_key,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":600,"system":sys_prompt,"messages":messages_hist},
            timeout=30
        )
        if resp.status_code==200:
            return resp.json()["content"][0]["text"]
        else:
            return f"API error {resp.status_code}. Check your API key."
    except requests.Timeout:
        return "Request timed out. Please try again."
    except Exception as e:
        return f"Error: {str(e)[:120]}"

def generate_csv_report(period="Monthly"):
    sr=(total_income-total_exp)/total_income*100 if total_income>0 else 0
    buf=io.StringIO(); w=csv.writer(buf)
    w.writerow([f"Seralung Finance Premium - {period} Report - {datetime.now().strftime('%B %Y')}"])
    w.writerow([])
    w.writerow(["SUMMARY"])
    for l,v in [("Health Score",f"{hs}/100"),("Income",fmt(total_income)),("Expenses",fmt(total_exp)),
                ("Savings Rate",pct(sr)),("Net Worth",fmt(net_worth)),("Cash Flow",fmt(total_income-total_exp))]:
        w.writerow([l,v])
    w.writerow([]); w.writerow(["EXPENSES"])
    w.writerow(["Name","Category","Spent","Budget","Status"])
    for e in st.session_state.expenses:
        bud=e.get("budget",e["amount"]); over=max(0,e["amount"]-bud)
        w.writerow([e["name"],e.get("category",""),f"{e['amount']:.2f}",f"{bud:.2f}","OVER" if over>0 else "OK"])
    w.writerow([]); w.writerow(["ASSETS"])
    w.writerow(["Name","Type","Value"])
    for a in st.session_state.assets: w.writerow([a["name"],a["type"],f"{a['value']:.2f}"])
    w.writerow([]); w.writerow(["LIABILITIES"])
    w.writerow(["Name","Type","Balance","Rate"])
    for l in st.session_state.liabilities: w.writerow([l["name"],l["type"],f"{l['balance']:.2f}",f"{l.get('rate',0):.2f}%"])
    w.writerow([]); w.writerow(["GOALS"])
    w.writerow(["Name","Target","Saved","Progress"])
    for g in st.session_state.goals:
        pct_g=g['saved']/g['amount']*100 if g['amount']>0 else 0
        w.writerow([g["name"],f"{g['amount']:.2f}",f"{g['saved']:.2f}",f"{pct_g:.0f}%"])
    return buf.getvalue().encode("utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Seralung Finance")
    theme_name = st.selectbox("Theme", list(THEMES.keys()), index=0)
    T = THEMES[theme_name]
    st.divider()
    st.caption("Version Premium")
    if st.button("Reset data", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    st.caption("Educational use only. Not financial advice.")

# ─────────────────────────────────────────────────────────────────────────────
# T-DEPENDENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def plo(title="", h=280, mg=None):
    mg = mg or dict(l=8,r=8,t=36 if title else 10,b=10)
    d = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'DM Sans','Inter',sans-serif",color=T["muted"],size=11),
        height=h, margin=mg,
        legend=dict(font=dict(color=T["muted"],size=11),bgcolor="rgba(0,0,0,0)",borderwidth=0),
        xaxis=dict(gridcolor=h2rgba(T["border"],0.5),linecolor=T["border"],color=T["muted"],showgrid=True),
        yaxis=dict(gridcolor=h2rgba(T["border"],0.5),linecolor=T["border"],color=T["muted"],showgrid=True),
    )
    if title: d["title"]=dict(text=title,font=dict(color=T["text"],size=13,family="'DM Sans','Inter',sans-serif"))
    return d

# ─────────────────────────────────────────────────────────────────────────────
# PREMIUM CSS
# ─────────────────────────────────────────────────────────────────────────────
is_dark = T["dark"]
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap');

:root{{
  --bg:{T['bg']}; --surface:{T['surface']}; --surface2:{T['surface2']}; --surface3:{T['surface3']};
  --border:{T['border']}; --accent:{T['accent']}; --accent2:{T['accent2']};
  --text:{T['text']}; --muted:{T['muted']}; --glow:{T['accent_glow']};
  --green:{T['green']}; --red:{T['red']}; --amber:{T['amber']}; --blue:{T['blue']}; --purple:{T['purple']};
  --grad:{T['grad']};
  --radius:16px; --radius-sm:10px; --radius-lg:24px;
  --shadow: 0 4px 24px rgba(0,0,0,{0.35 if is_dark else 0.08});
  --shadow-accent: 0 0 32px {T['accent_glow']};
}}
html,body,.stApp{{background:var(--bg) !important;color:var(--text) !important;font-family:'DM Sans',sans-serif;}}
*,*::before,*::after{{box-sizing:border-box;}}
::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-track{{background:var(--surface);}}
::-webkit-scrollbar-thumb{{background:var(--border);border-radius:99px;}}
p,span,div,label,li{{color:var(--text);}}
h1,h2,h3,h4,h5{{color:var(--text) !important;font-family:'DM Sans',sans-serif;font-weight:700;}}

/* Sidebar */
[data-testid="stSidebar"]{{background:var(--surface) !important;border-right:1px solid var(--border);}}
[data-testid="stSidebar"] *{{color:var(--text) !important;}}
.block-container{{padding:1rem 1.5rem 2rem !important;max-width:none !important;}}

/* Metrics */
[data-testid="metric-container"]{{
  background:var(--surface) !important;border:1px solid var(--border) !important;
  border-radius:var(--radius) !important;padding:1rem 1.1rem !important;
  transition:transform 0.2s,box-shadow 0.2s;
}}
[data-testid="metric-container"]:hover{{transform:translateY(-2px);box-shadow:var(--shadow);}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] *{{
  color:var(--muted) !important;font-size:0.65rem !important;text-transform:uppercase;letter-spacing:0.08em;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] *{{
  color:var(--text) !important;font-weight:700 !important;font-size:1.3rem !important;
}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] *{{font-size:0.7rem !important;}}

/* Tabs */
[data-testid="stTabs"] [role="tab"]{{
  background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius-sm);
  color:var(--muted) !important;font-size:0.76rem;font-weight:500;padding:0.3rem 0.75rem;margin-right:3px;
  transition:all 0.18s;
}}
[data-testid="stTabs"] [role="tab"]:hover{{background:var(--surface3);color:var(--text) !important;}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{{
  background:var(--accent) !important;color:#fff !important;border-color:var(--accent) !important;
  box-shadow:var(--shadow-accent);
}}
[data-testid="stTabs"] [role="tablist"]{{border-bottom:1px solid var(--border);padding-bottom:0.6rem;flex-wrap:wrap;gap:3px;}}

/* Inputs */
label,[data-testid="stWidgetLabel"]{{color:var(--text) !important;font-size:0.8rem !important;}}
[data-testid="stNumberInput"] input,[data-testid="stTextInput"] input,textarea{{
  background:var(--surface2) !important;border:1px solid var(--border) !important;
  border-radius:var(--radius-sm) !important;color:var(--text) !important;
}}
[data-testid="stSelectbox"]>div>div,[data-testid="stSelectbox"] span{{
  background:var(--surface2) !important;border:1px solid var(--border) !important;
  color:var(--text) !important;border-radius:var(--radius-sm) !important;
}}
[data-testid="stCheckbox"] span{{color:var(--text) !important;}}
[data-baseweb="slider"] [role="slider"]{{background:var(--accent) !important;border-color:var(--accent) !important;}}
[data-testid="stSlider"] [data-testid="stThumbValue"]{{color:var(--text) !important;}}

/* Buttons */
.stButton>button{{
  background:var(--grad) !important;border:none !important;border-radius:var(--radius-sm) !important;
  color:#fff !important;font-weight:600 !important;font-family:'DM Sans',sans-serif !important;
  font-size:0.82rem !important;transition:all 0.18s;letter-spacing:0.01em;
}}
.stButton>button:hover{{opacity:0.88 !important;transform:translateY(-1px);box-shadow:var(--shadow-accent);}}
.stDownloadButton>button{{background:var(--surface2) !important;color:var(--text) !important;border:1px solid var(--border) !important;}}
.stDownloadButton>button:hover{{border-color:var(--accent) !important;}}

/* Expander */
[data-testid="stExpander"]{{background:var(--surface) !important;border:1px solid var(--border) !important;border-radius:var(--radius) !important;}}
[data-testid="stExpander"] summary *{{color:var(--text) !important;}}
[data-testid="stFileUploader"]{{background:var(--surface2) !important;border:2px dashed var(--border) !important;border-radius:var(--radius) !important;}}
[data-testid="stAlert"] div{{color:var(--text) !important;}}
hr{{border-color:var(--border) !important;margin:0.8rem 0 !important;}}

/* Custom components */
.g-card{{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.2rem 1.4rem;margin-bottom:1rem;box-shadow:var(--shadow);
  transition:transform 0.2s,box-shadow 0.2s;
}}
.g-card:hover{{transform:translateY(-1px);box-shadow:0 8px 32px rgba(0,0,0,{0.4 if is_dark else 0.1});}}
.g-label{{
  font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
  color:var(--muted);margin-bottom:0.75rem;display:block;
}}
.g-row{{
  display:flex;justify-content:space-between;align-items:center;
  padding:0.45rem 0;border-bottom:1px solid var(--border);font-size:0.81rem;color:var(--text);
}}
.g-row:last-child{{border-bottom:none;font-weight:600;}}
.g-tip{{
  background:{h2rgba(T['accent'],0.08)};border-left:3px solid var(--accent);
  border-radius:0 var(--radius-sm) var(--radius-sm) 0;
  padding:0.7rem 1rem;font-size:0.8rem;color:var(--text);margin-bottom:0.9rem;line-height:1.6;
}}
.g-tip strong{{color:var(--accent);}}
.g-tip b{{color:var(--accent);}}

/* Badges */
.badge{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:0.6rem;font-weight:700;letter-spacing:0.04em;}}
.b-ok  {{background:{h2rgba(T['green'],0.15)};color:{T['green']};border:1px solid {h2rgba(T['green'],0.3)};}}
.b-warn{{background:{h2rgba(T['amber'],0.15)};color:{T['amber']};border:1px solid {h2rgba(T['amber'],0.3)};}}
.b-bad {{background:{h2rgba(T['red'],0.15)};color:{T['red']};border:1px solid {h2rgba(T['red'],0.3)};}}
.b-blue{{background:{h2rgba(T['blue'],0.15)};color:{T['blue']};border:1px solid {h2rgba(T['blue'],0.3)};}}
.b-pur {{background:{h2rgba(T['purple'],0.15)};color:{T['purple']};border:1px solid {h2rgba(T['purple'],0.3)};}}
.b-gold{{background:rgba(251,191,36,0.15);color:#F59E0B;border:1px solid rgba(251,191,36,0.3);}}
.b-amb {{background:{h2rgba(T['amber'],0.15)};color:{T['amber']};border:1px solid {h2rgba(T['amber'],0.3)};}}

/* Income bar */
.income-stripe{{
  background:{'linear-gradient(135deg,'+h2rgba(T['accent'],0.12)+','+h2rgba(T['blue'],0.08)+')'};
  border:1px solid var(--border);border-radius:var(--radius);
  padding:0.9rem 1.3rem 0.6rem;margin-bottom:1rem;
}}
/* Gradient heading */
.grad-text{{
  background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;font-weight:800;
}}

/* Chat bubbles */
.chat-user{{
  background:var(--accent);color:#fff;border-radius:16px 16px 4px 16px;
  padding:0.7rem 1rem;font-size:0.82rem;margin:0.5rem 0;display:inline-block;
  max-width:85%;float:right;clear:both;line-height:1.5;
}}
.chat-ai{{
  background:var(--surface2);color:var(--text);border-radius:16px 16px 16px 4px;
  padding:0.7rem 1rem;font-size:0.82rem;margin:0.5rem 0;display:inline-block;
  max-width:90%;float:left;clear:both;line-height:1.6;border:1px solid var(--border);
}}
.chat-wrap{{min-height:120px;overflow-x:hidden;}}
.chat-wrap::after{{content:'';display:table;clear:both;}}

/* Achievement card */
.achieve-card{{
  background:var(--surface2);border:1px solid var(--border);border-radius:12px;
  padding:0.75rem 1rem;text-align:center;transition:all 0.2s;
}}
.achieve-card:hover{{border-color:var(--accent);box-shadow:var(--shadow-accent);transform:translateY(-2px);}}

/* Progress bars */
.pbar-wrap{{background:var(--surface2);border-radius:6px;height:7px;overflow:hidden;}}
.pbar{{height:100%;border-radius:6px;transition:width 0.5s ease;}}

/* Premium card */
.pro-card{{
  background:var(--grad);border-radius:var(--radius-lg);padding:1.8rem;
  color:#fff;text-align:center;box-shadow:var(--shadow-accent);
}}

/* Mobile */
@media(max-width:768px){{
  .block-container{{padding:0.5rem 0.5rem 2rem !important;}}
  [data-testid="stTabs"] [role="tab"]{{font-size:0.68rem;padding:0.22rem 0.45rem;}}
  .g-card{{padding:0.8rem 0.9rem;}}
  h1{{font-size:1.2rem !important;}}
  [data-testid="metric-container"] [data-testid="stMetricValue"] *{{font-size:1rem !important;}}
}}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([3,1])
with hc1:
    st.markdown(f"<h1 style='margin:0;font-size:1.8rem;letter-spacing:-0.03em;'>"
                f"<span class='grad-text'>Seralung Finance</span></h1>"
                f"<p style='color:{T['muted']};font-size:0.74rem;margin:2px 0 0.7rem;'>Premium Financial Intelligence</p>", unsafe_allow_html=True)
with hc2:
    st.markdown(f"<div style='text-align:right;padding-top:0.3rem;'>"
                f"<div style='font-size:0.65rem;color:{T['muted']};'>{datetime.now().strftime('%A, %d %B %Y')}</div>"
                f"<div style='font-size:0.78rem;color:{T['accent']};font-weight:600;margin-top:2px;'>AUD</div>"
                f"</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INCOME — always visible
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"<div class='income-stripe'><span class='g-label'>Monthly Income & Budget Rule</span></div>", unsafe_allow_html=True)
i1,i2,i3,i4,i5 = st.columns([2,2,1,1,1])
with i1: primary_income=st.number_input("Primary take-home /mo",min_value=0.0,value=6000.0,step=100.0,format="%.0f",key="pi")
with i2: other_income  =st.number_input("Other income /mo",min_value=0.0,value=500.0,step=50.0,format="%.0f",key="oi")
with i3:
    needs_pct=st.number_input("Needs %",0,100,st.session_state.get("needs_pct",50),1,key="np_n")
    st.session_state["needs_pct"]=needs_pct
with i4:
    wants_pct=st.number_input("Wants %",0,100,st.session_state.get("wants_pct",30),1,key="wp_n")
    st.session_state["wants_pct"]=wants_pct
with i5:
    invest_pct=st.number_input("Invest %",0,100,st.session_state.get("invest_pct",20),1,key="ip_n")
    st.session_state["invest_pct"]=invest_pct

total_income=primary_income+other_income
if needs_pct+wants_pct+invest_pct!=100:
    st.warning(f"Budget percentages sum to {needs_pct+wants_pct+invest_pct}% — adjust to 100%.")
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# DERIVED VALUES
# ─────────────────────────────────────────────────────────────────────────────
total_sub    = sum(s["amount"] for s in st.session_state.subscriptions)
total_exp    = sum(e["amount"] for e in st.session_state.expenses)+total_sub
total_assets = sum(a["value"] for a in st.session_state.assets)
total_liab   = sum(l["balance"] for l in st.session_state.liabilities)
net_worth    = total_assets-total_liab
investable   = total_income*invest_pct/100
cash_flow    = total_income-total_exp
savings_rate = cash_flow/total_income*100 if total_income>0 else 0
cash_assets  = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
em_months    = cash_assets/total_exp if total_exp>0 else 0
hs, hs_det   = health_score_calc()
nw_col       = T["green"] if net_worth>=0 else T["red"]

if   hs>=80: sc,sg="var(--green)","Excellent"
elif hs>=65: sc,sg="var(--blue)","Good"
elif hs>=50: sc,sg="var(--amber)","Fair"
elif hs>=35: sc,sg="var(--red)","Needs Work"
else:        sc,sg="var(--red)","Critical"

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tabs = st.tabs(["Dashboard","Budget & Goals","Invest & Risk","AI Insights","AI Assistant","Pro"])
t1,t2,t3,t4,t5,t6 = tabs

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t1:
    # Health gauge + 5 metrics
    hg, m1, m2, m3, m4, m5 = st.columns([1.4,1,1,1,1,1])
    with hg:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",value=hs,
            number=dict(font=dict(size=36,color=T["accent"],family="DM Sans"),suffix="/100"),
            gauge=dict(
                axis=dict(range=[0,100],tickwidth=0,tickcolor="rgba(0,0,0,0)",tickvals=[],showticklabels=False),
                bar=dict(color=T["accent"],thickness=0.25),
                bgcolor="rgba(0,0,0,0)",borderwidth=0,
                steps=[
                    dict(range=[0,35],  color=h2rgba(T["red"],0.18)),
                    dict(range=[35,50], color=h2rgba(T["amber"],0.15)),
                    dict(range=[50,65], color=h2rgba(T["amber"],0.10)),
                    dict(range=[65,80], color=h2rgba(T["blue"],0.12)),
                    dict(range=[80,100],color=h2rgba(T["green"],0.18)),
                ],
                threshold=dict(line=dict(color=T["accent"],width=3),thickness=0.8,value=hs)
            )
        ))
        fig_gauge.add_annotation(text=sg,x=0.5,y=0.18,showarrow=False,font=dict(color=T["accent"],size=14,family="DM Sans"),xref="paper",yref="paper")
        fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=180,
            margin=dict(l=10,r=10,t=10,b=10),font=dict(color=T["text"],family="DM Sans"))
        st.markdown(f"<div class='g-card' style='text-align:center;padding:0.6rem 0.8rem;'>", unsafe_allow_html=True)
        st.markdown(f"<span class='g-label' style='display:block;text-align:center;'>Financial Health</span>", unsafe_allow_html=True)
        st.plotly_chart(fig_gauge,use_container_width=True,config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)
    with m1: st.metric("Net Worth",     fmtk(net_worth),  "Positive" if net_worth>=0 else "Negative",   delta_color="normal" if net_worth>=0 else "inverse")
    with m2: st.metric("Cash Flow",     fmt(cash_flow),   "Surplus"  if cash_flow>=0 else "Deficit",    delta_color="normal" if cash_flow>=0 else "inverse")
    with m3: st.metric("Savings Rate",  pct(savings_rate),"Target 20%",                                 delta_color="normal" if savings_rate>=20 else "inverse")
    with m4: st.metric("Emergency Fund",f"{em_months:.1f} mo","Safe" if em_months>=6 else "Low",        delta_color="normal" if em_months>=6 else "inverse")
    with m5: st.metric("Invest /mo",    fmt(investable),  f"{invest_pct}% of income",                   delta_color="normal" if investable>0 else "off")

    st.markdown("<div style='margin:0.6rem 0;'></div>", unsafe_allow_html=True)
    da, db = st.columns(2,gap="large")

    with da:
        # 50/30/20 visual
        st.markdown(f"<div class='g-card'><span class='g-label'>50 / 30 / 20 Budget Rule</span>", unsafe_allow_html=True)
        rule_data = [
            ("Needs (Housing, Food, Bills)",  total_income*needs_pct/100,  total_exp*0.60,  T["blue"]),
            ("Wants (Dining, Entertainment)", total_income*wants_pct/100,  total_exp*0.40,  T["amber"]),
            ("Invest & Save",                 total_income*invest_pct/100, investable,      T["green"]),
        ]
        for lbl, budget, actual, col in rule_data:
            p = min(100, actual/budget*100) if budget>0 else 0
            bc = "b-ok" if p<=85 else "b-warn" if p<=100 else "b-bad"
            br = T["red"] if p>100 else col
            st.markdown(
                f"<div style='margin-bottom:12px;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:4px;'>"
                f"<span style='color:{T['text']}'>{lbl}</span>"
                f"<div><span style='color:{T['muted']};margin-right:6px;'>{fmt(actual)}/{fmt(budget)}</span>"
                f"<span class='badge {bc}'>{p:.0f}%</span></div></div>"
                f"<div class='pbar-wrap'><div class='pbar' style='width:{p:.1f}%;background:{br};'></div></div>"
                f"</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Spending donut
        df_e = pd.DataFrame(st.session_state.expenses)
        df_e = df_e[df_e["amount"]>0]
        if not df_e.empty:
            cat_df = df_e.groupby("category")["amount"].sum().reset_index()
            n=len(cat_df); cc=(T["chart"]*math.ceil(n/max(1,len(T["chart"]))))[:n]
            fig_d = go.Figure(go.Pie(labels=cat_df["category"],values=cat_df["amount"],hole=0.6,
                marker=dict(colors=cc,line=dict(color=T["bg"],width=2)),
                textfont=dict(size=11,color=T["muted"]),
                hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>"))
            fig_d.add_annotation(text=f"<b>{fmt(total_exp)}</b><br><span style='font-size:10px'>total</span>",
                x=0.5,y=0.5,showarrow=False,font=dict(color=T["text"],size=14,family="DM Sans"),align="center")
            fig_d.update_layout(**plo("Spending by Category",240))
            st.plotly_chart(fig_d,use_container_width=True,config={"displayModeBar":False})

        # Health pillars
        st.markdown(f"<div class='g-card'><span class='g-label'>Score Breakdown</span>", unsafe_allow_html=True)
        for name, d in hs_det.items():
            p=d["score"]/d["max"]*100
            bc="b-ok" if p>=70 else "b-warn" if p>=40 else "b-bad"
            br=T["green"] if p>=70 else T["amber"] if p>=40 else T["red"]
            st.markdown(
                f"<div style='margin-bottom:9px;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:0.76rem;margin-bottom:3px;'>"
                f"<span style='color:{T['text']}'>{name}</span>"
                f"<div><span style='color:{T['muted']};margin-right:5px;font-size:0.7rem;'>{d['desc']}</span>"
                f"<span class='badge {bc}'>{d['score']:.0f}/{d['max']}</span></div></div>"
                f"<div class='pbar-wrap'><div class='pbar' style='width:{p:.1f}%;background:{br};'></div></div>"
                f"</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with db:
        # Upcoming bills
        today=date.today()
        st.markdown(f"<div class='g-card'><span class='g-label'>Upcoming Bills</span>", unsafe_allow_html=True)
        for bill in sorted(st.session_state.bills,key=lambda b: b["due_day"]):
            days=bill["due_day"]-today.day
            if days<0: days+=30
            bc="b-ok" if days>7 else "b-warn" if days>2 else "b-bad"
            bt="Today" if days==0 else f"in {days}d"
            st.markdown(
                f"<div class='g-row'><span>{bill['name']}</span>"
                f"<div><span style='color:{T['muted']};margin-right:8px;'>{fmt(bill['amount'])}</span>"
                f"<span class='badge {bc}'>{bt}</span></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Smart action items
        tips=[]
        if em_months<3:        tips.append(("b-bad","Build emergency fund urgently. Under 3 months cash is high risk."))
        elif em_months<6:      tips.append(("b-warn",f"Emergency fund at {em_months:.1f} months. Target {fmt(total_exp*6)} total."))
        if savings_rate<10:    tips.append(("b-bad",f"Savings rate {savings_rate:.1f}% is dangerously low. Find cuts now."))
        elif savings_rate<20:  tips.append(("b-warn",f"Savings rate {savings_rate:.1f}%. Need {fmt(total_income*0.2-cash_flow)}/mo more to hit 20%."))
        hi=[l for l in st.session_state.liabilities if l.get("rate",0)>15]
        if hi: tips.append(("b-bad",f"Predatory debt {fmt(sum(l['balance'] for l in hi))} at >15% APR — prioritise payoff immediately."))
        ob=[e for e in st.session_state.expenses if e["amount"]>e.get("budget",e["amount"])]
        if ob: tips.append(("b-warn",f"{len(ob)} category(s) over budget: {', '.join(e['name'] for e in ob[:3])}."))
        if total_sub>200: tips.append(("b-warn",f"Subscriptions at {fmt(total_sub)}/mo = {fmt(total_sub*12)}/yr. Review cancellations."))
        if savings_rate>=20 and em_months>=6: tips.append(("b-ok","All key ratios healthy. Consider increasing investment allocation."))
        if not tips: tips.append(("b-ok","Financial health looks solid. Keep the momentum going."))
        st.markdown(f"<div class='g-card'><span class='g-label'>Smart Insights</span>", unsafe_allow_html=True)
        for bc,text in tips[:5]:
            lbl="Good" if "ok" in bc else "Note" if "warn" in bc else "Action"
            st.markdown(f"<div style='padding:0.45rem 0;border-bottom:1px solid {T['border']};font-size:0.79rem;'>"
                        f"<span class='badge {bc}' style='margin-right:8px;'>{lbl}</span>{text}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Streak + badges preview
        badges=get_badges()
        st.markdown(f"<div class='g-card'><span class='g-label'>Achievements ({len(badges)} earned)</span>", unsafe_allow_html=True)
        bcols=st.columns(min(3,len(badges)))
        for i,(name,desc,col) in enumerate(badges[:3]):
            bcm={"green":"b-ok","blue":"b-blue","purple":"b-pur","gold":"b-gold","amber":"b-amb"}.get(col,"b-ok")
            with bcols[i]:
                st.markdown(f"<div class='achieve-card'>"
                            f"<div class='badge {bcm}' style='margin-bottom:5px;'>{name}</div>"
                            f"<div style='font-size:0.64rem;color:{T['muted']};'>{desc}</div>"
                            f"</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUDGET & GOALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t2:
    bg1, bg2 = st.columns(2, gap="large")
    with bg1:
        st.markdown(f"<div class='g-card'><span class='g-label'>Monthly Expenses — Name / Spent / Budget / Category</span>", unsafe_allow_html=True)
        to_del=None
        for i,e in enumerate(st.session_state.expenses):
            c1,c2,c3,c4,c5=st.columns([2.5,1.5,1.5,1.5,0.5])
            with c1:
                nn=st.text_input(f"n{i}",value=e["name"],label_visibility="collapsed",key=f"en_{i}")
                st.session_state.expenses[i]["name"]=nn
            with c2:
                na=st.number_input(f"a{i}",value=float(e["amount"]),min_value=0.0,step=10.0,label_visibility="collapsed",key=f"ea_{i}",format="%.0f")
                st.session_state.expenses[i]["amount"]=na
            with c3:
                nb=st.number_input(f"b{i}",value=float(e.get("budget",e["amount"])),min_value=0.0,step=10.0,label_visibility="collapsed",key=f"eb_{i}",format="%.0f")
                st.session_state.expenses[i]["budget"]=nb
            with c4:
                ic=CATEGORIES.index(e.get("category","Other")) if e.get("category","Other") in CATEGORIES else 0
                nc=st.selectbox(f"c{i}",CATEGORIES,index=ic,label_visibility="collapsed",key=f"ec_{i}")
                st.session_state.expenses[i]["category"]=nc
            with c5:
                if st.button("X",key=f"ed_{i}"): to_del=i
        if to_del is not None: st.session_state.expenses.pop(to_del); st.rerun()
        st.markdown("---")
        r1,r2,r3,r4=st.columns([2.5,1.5,1.5,1.5])
        with r1: nn2=st.text_input("Name",placeholder="New expense",key="ne_n")
        with r2: na2=st.number_input("Spent",min_value=0.0,step=10.0,key="ne_a",format="%.0f")
        with r3: nb2=st.number_input("Budget",min_value=0.0,step=10.0,key="ne_b",format="%.0f")
        with r4: nc2=st.selectbox("Category",CATEGORIES,key="ne_c",label_visibility="collapsed")
        if st.button("Add expense",use_container_width=True):
            if nn2: st.session_state.expenses.append({"name":nn2,"amount":float(na2),"budget":float(nb2) if nb2>0 else float(na2),"category":nc2}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

        # Subscriptions
        st.markdown(f"<div class='g-card'><span class='g-label'>Subscriptions — {fmt(total_sub)}/mo  =  {fmt(total_sub*12)}/yr</span>",unsafe_allow_html=True)
        del_s=None
        for i,s in enumerate(st.session_state.subscriptions):
            s1,s2,s3=st.columns([3,1.5,0.5])
            with s1:
                sn=st.text_input(f"sn{i}",value=s["name"],label_visibility="collapsed",key=f"sn_{i}")
                st.session_state.subscriptions[i]["name"]=sn
            with s2:
                sa=st.number_input(f"sa{i}",value=float(s["amount"]),min_value=0.0,step=0.5,label_visibility="collapsed",key=f"sa_{i}",format="%.2f")
                st.session_state.subscriptions[i]["amount"]=sa
            with s3:
                if st.button("X",key=f"sd_{i}"): del_s=i
        if del_s is not None: st.session_state.subscriptions.pop(del_s); st.rerun()
        ss1,ss2=st.columns([3,1.5])
        with ss1: snn=st.text_input("Service",placeholder="e.g. Disney+",key="ns_n")
        with ss2: sna=st.number_input("$/mo",min_value=0.0,step=0.5,key="ns_a",format="%.2f")
        if st.button("Add subscription",use_container_width=True):
            if snn: st.session_state.subscriptions.append({"name":snn,"amount":float(sna)}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

    with bg2:
        # Spent vs Budget chart
        df_e2=pd.DataFrame(st.session_state.expenses)
        df_e2=df_e2[df_e2["amount"]>0]
        if not df_e2.empty:
            cat_s=df_e2.groupby("category").agg({"amount":"sum","budget":"sum"}).reset_index()
            fig_c=go.Figure()
            fig_c.add_trace(go.Bar(name="Budget",x=cat_s["category"],y=cat_s["budget"],
                marker_color=h2rgba(T["green"],0.3),marker_line=dict(color=T["green"],width=1.5)))
            fig_c.add_trace(go.Bar(name="Spent",x=cat_s["category"],y=cat_s["amount"],
                marker_color=T["accent"],text=[fmt(v) for v in cat_s["amount"]],textposition="outside",
                textfont=dict(color=T["text"],size=9)))
            fig_c.update_layout(**plo("Spent vs Budget",250)); fig_c.update_layout(barmode="overlay")
            st.plotly_chart(fig_c,use_container_width=True,config={"displayModeBar":False})

        # Per-item tracker
        st.markdown(f"<div class='g-card'><span class='g-label'>Per-Item Budget Tracker</span>",unsafe_allow_html=True)
        for exp in sorted(st.session_state.expenses,key=lambda e: e["amount"]/max(e.get("budget",1),1),reverse=True):
            bud=exp.get("budget",exp["amount"]); p=min(100,exp["amount"]/bud*100) if bud>0 else 0
            bc="b-ok" if p<=85 else "b-warn" if p<=100 else "b-bad"
            br=T["red"] if p>100 else T["amber"] if p>85 else T["green"]
            st.markdown(
                f"<div style='margin-bottom:9px;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:0.76rem;margin-bottom:3px;'>"
                f"<span>{exp['name']}</span>"
                f"<div><span style='color:{T['muted']};margin-right:5px;'>{fmt(exp['amount'])}/{fmt(bud)}</span>"
                f"<span class='badge {bc}'>{p:.0f}%</span></div></div>"
                f"<div class='pbar-wrap'><div class='pbar' style='width:{p:.1f}%;background:{br};'></div></div>"
                f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Goals
        st.markdown(f"<div class='g-card'><span class='g-label'>Financial Goals</span>",unsafe_allow_html=True)
        del_g=None
        for i,g in enumerate(st.session_state.goals):
            rem=max(0,g["amount"]-g["saved"]); pct_g=min(100,round(g["saved"]/g["amount"]*100)) if g["amount"]>0 else 0
            mo=math.ceil(rem/investable) if investable>0 else 9999
            pc={"High":T["red"],"Medium":T["amber"],"Low":T["blue"]}.get(g["priority"],T["blue"])
            pb={"High":"b-bad","Medium":"b-warn","Low":"b-blue"}.get(g["priority"],"b-blue")
            gc_,gd_=st.columns([11,1])
            with gc_:
                st.markdown(
                    f"<div style='margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid {T['border']};'>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
                    f"<span style='font-weight:600;font-size:0.88rem;'>{g['name']}</span>"
                    f"<span class='badge {pb}'>{g['priority']}</span></div>"
                    f"<div style='font-size:0.73rem;color:{T['muted']};margin-bottom:5px;'>"
                    f"{fmt(g['saved'])} saved / {fmt(g['amount'])} target  "
                    f"<span style='color:{T['accent']};'>{mo} months at current rate</span></div>"
                    f"<div class='pbar-wrap'><div class='pbar' style='width:{pct_g}%;background:{pc};'></div></div>"
                    f"<div style='font-size:0.65rem;color:{T['muted']};margin-top:2px;'>{pct_g}% complete</div></div>",
                    unsafe_allow_html=True)
                ns=st.number_input(f"Saved ({g['name']})",value=float(g["saved"]),min_value=0.0,step=100.0,key=f"gupd_{i}",format="%.0f",label_visibility="collapsed")
                if ns!=g["saved"]: st.session_state.goals[i]["saved"]=ns; st.rerun()
            with gd_:
                if st.button("X",key=f"gd_{i}"): del_g=i
        if del_g is not None: st.session_state.goals.pop(del_g); st.rerun()
        with st.expander("Add new goal"):
            gc1,gc2,gc3,gc4=st.columns([2,1,1,1])
            with gc1: gname=st.text_input("Goal name",placeholder="e.g. House deposit")
            with gc2: gtgt=st.number_input("Target ($)",min_value=0.0,step=1000.0,format="%.0f",key="g_tgt")
            with gc3: gsav=st.number_input("Saved ($)",min_value=0.0,step=100.0,format="%.0f",key="g_sav")
            with gc4: gpri=st.selectbox("Priority",["High","Medium","Low"])
            if st.button("Add goal",use_container_width=True):
                if gname and gtgt>0: st.session_state.goals.append({"name":gname,"amount":gtgt,"saved":gsav,"priority":gpri}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

        # CSV export
        st.download_button("Download CSV Report",data=generate_csv_report(),
            file_name=f"seralung_{datetime.now().strftime('%Y-%m-%d')}.csv",mime="text/csv",use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INVEST & RISK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t3:
    ir1, ir2 = st.columns(2, gap="large")
    with ir1:
        # Risk profiler
        st.markdown(f"<div class='g-card'><span class='g-label'>Risk Profile</span>",unsafe_allow_html=True)
        rp_idx = RISK_LABELS.index(st.session_state.risk_profile) if st.session_state.risk_profile in RISK_LABELS else 2
        risk_sel = st.selectbox("Risk tolerance",RISK_LABELS,index=rp_idx,key="rp_sel")
        st.session_state.risk_profile=risk_sel
        age_val = st.slider("Your age",18,75,st.session_state.get("age",32),1,key="age_sl")
        st.session_state["age"]=age_val
        ret_age = st.slider("Target retirement age",50,75,st.session_state.get("retirement_age",65),1,key="ret_sl")
        st.session_state["retirement_age"]=ret_age
        yrs_to_retire = max(1,ret_age-age_val)
        risk_num = RISK_SCORES[RISK_LABELS.index(risk_sel)]
        # Age-adjust: older should be less aggressive
        age_adj = max(0,risk_num-(age_val-30)*0.8)
        risk_final = max(5,min(95,age_adj))
        if risk_num>60 and age_val>55:
            st.markdown(f"<div class='g-tip'>At age {age_val}, a <b>{risk_sel}</b> profile may be too aggressive. Consider reducing equity exposure.</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Risk gauge
        risk_c = T["green"] if risk_final<40 else T["amber"] if risk_final<70 else T["red"]
        fig_risk=go.Figure(go.Indicator(
            mode="gauge+number+delta",value=risk_final,
            number=dict(font=dict(size=30,color=risk_c,family="DM Sans"),suffix=""),
            delta=dict(reference=50,relative=False,font=dict(size=13)),
            gauge=dict(
                axis=dict(range=[0,100],tickwidth=0,tickvals=[],showticklabels=False),
                bar=dict(color=risk_c,thickness=0.28),
                bgcolor="rgba(0,0,0,0)",borderwidth=0,
                steps=[
                    dict(range=[0,33],color=h2rgba(T["green"],0.2)),
                    dict(range=[33,67],color=h2rgba(T["amber"],0.15)),
                    dict(range=[67,100],color=h2rgba(T["red"],0.2)),
                ],
            )
        ))
        fig_risk.add_annotation(text=f"<b>Risk Score</b><br>{risk_sel}",x=0.5,y=0.12,showarrow=False,
            font=dict(color=T["muted"],size=11,family="DM Sans"),align="center",xref="paper",yref="paper")
        fig_risk.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            height=190,margin=dict(l=10,r=10,t=10,b=5),font=dict(color=T["text"],family="DM Sans"))
        st.plotly_chart(fig_risk,use_container_width=True,config={"displayModeBar":False})

        # Allocation suggestion based on risk
        risk_ratio=risk_final/100
        sug_eq = min(90,int(risk_ratio*90))
        sug_bond= max(5,int((1-risk_ratio)*60))
        sug_cash= max(5,100-sug_eq-sug_bond)
        sug_crypto=max(0,int(risk_ratio*10)) if risk_num>=50 else 0
        sug_eq=max(5,sug_eq-sug_crypto)

        st.markdown(f"<div class='g-card'><span class='g-label'>Suggested Allocation (age {age_val}, {risk_sel})</span>",unsafe_allow_html=True)
        for lbl,pct_v,col in [("Equities/ETFs",sug_eq,T["green"]),("Bonds/Fixed",sug_bond,T["blue"]),
                               ("Cash/Stable",sug_cash,T["muted"]),("Crypto",sug_crypto,T["purple"])]:
            if pct_v>0:
                mo_v=investable*pct_v/100
                st.markdown(
                    f"<div style='margin-bottom:9px;'>"
                    f"<div style='display:flex;justify-content:space-between;font-size:0.77rem;margin-bottom:3px;'>"
                    f"<span>{lbl}</span><span style='color:{T['muted']};'>{pct_v}%  —  {fmt(mo_v)}/mo</span></div>"
                    f"<div class='pbar-wrap'><div class='pbar' style='width:{pct_v}%;background:{col};'></div></div>"
                    f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # AUS Tax
        st.markdown(f"<div class='g-card'><span class='g-label'>Australian Tax Estimator — FY2024-25</span>",unsafe_allow_html=True)
        gross=st.number_input("Annual gross income ($)",min_value=0.0,value=float(primary_income*12),step=1000.0,format="%.0f",key="tax_g")
        c_m,c_l,c_p=st.columns(3)
        with c_m: inc_med=st.checkbox("Medicare 2%",value=True)
        with c_l: inc_lito=st.checkbox("LITO offset",value=True)
        with c_p: priv_h=st.checkbox("Private health",value=False)
        tax_r=calc_tax(gross); med=gross*0.02 if inc_med else 0
        mls=gross*0.01 if (not priv_h and gross>93000 and inc_med) else 0
        lito=calc_lito(gross) if inc_lito else 0
        ttax=max(0,tax_r+med+mls-lito); net_ann=gross-ttax; eff_r=ttax/gross*100 if gross>0 else 0
        for lbl,val,col_,bld in [("Gross",fmt(gross),T["text"],False),("Income tax",f"-{fmt(tax_r)}",T["red"],False),
            ("Medicare",f"-{fmt(med)}",T["amber"],False),("MLS",f"-{fmt(mls)}",T["red"],mls>0),
            ("LITO",f"+{fmt(lito)}",T["green"],False),("Net annual",fmt(net_ann),T["accent"],True),
            ("Net monthly",fmt(net_ann/12),T["accent"],True),("Effective rate",pct(eff_r),T["amber"],True)]:
            fw="font-weight:600;" if bld else ""
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid {T['border']};font-size:0.8rem;{fw}'>"
                        f"<span style='color:{T['muted']}'>{lbl}</span><span style='color:{col_}'>{val}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    with ir2:
        # Monte Carlo projection
        st.markdown(f"<div class='g-card'><span class='g-label'>Monte Carlo Portfolio Projection ({yrs_to_retire} years to retirement)</span>",unsafe_allow_html=True)
        init_port=st.number_input("Current portfolio ($)",min_value=0.0,
            value=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings","Super"])),
            step=1000.0,format="%.0f",key="mc_init")
        mc_contrib=st.number_input("Monthly contribution ($)",min_value=0.0,value=float(investable),step=100.0,format="%.0f",key="mc_c")
        exp_mu={"Very Conservative":0.04,"Conservative":0.055,"Moderate":0.07,"Growth":0.09,"Aggressive":0.12}.get(risk_sel,0.07)
        exp_sig={"Very Conservative":0.05,"Conservative":0.08,"Moderate":0.13,"Growth":0.17,"Aggressive":0.22}.get(risk_sel,0.13)
        st.caption(f"Assumed: {exp_mu*100:.1f}% annual return, {exp_sig*100:.0f}% volatility for {risk_sel} profile")

        if st.button("Run Monte Carlo Simulation",use_container_width=True,key="mc_run"):
            with st.spinner("Simulating 200 portfolio paths..."):
                np.random.seed(42)
                sims=monte_carlo(init_port,mc_contrib,yrs_to_retire,200,exp_mu,exp_sig)
                months=np.arange(sims.shape[1])
                p10=np.percentile(sims,10,axis=0); p25=np.percentile(sims,25,axis=0)
                p50=np.percentile(sims,50,axis=0); p75=np.percentile(sims,75,axis=0)
                p90=np.percentile(sims,90,axis=0)
                fig_mc=go.Figure()
                # Confidence bands
                fig_mc.add_trace(go.Scatter(x=months,y=p90,fill=None,mode="lines",
                    line=dict(color=h2rgba(T["green"],0.0)),showlegend=False,hoverinfo="skip"))
                fig_mc.add_trace(go.Scatter(x=months,y=p10,fill="tonexty",mode="lines",
                    fillcolor=h2rgba(T["green"],0.12),line=dict(color=h2rgba(T["green"],0.0)),
                    name="80% confidence",hoverinfo="skip"))
                fig_mc.add_trace(go.Scatter(x=months,y=p75,fill=None,mode="lines",
                    line=dict(color=h2rgba(T["accent"],0.0)),showlegend=False,hoverinfo="skip"))
                fig_mc.add_trace(go.Scatter(x=months,y=p25,fill="tonexty",mode="lines",
                    fillcolor=h2rgba(T["accent"],0.2),line=dict(color=h2rgba(T["accent"],0.0)),
                    name="50% confidence",hoverinfo="skip"))
                fig_mc.add_trace(go.Scatter(x=months,y=p50,mode="lines",name="Median",
                    line=dict(color=T["green"],width=2.5),hovertemplate="Month %{x}<br>$%{y:,.0f}<extra></extra>"))
                # Add some individual paths for visual effect
                for path in sims[::20]:
                    fig_mc.add_trace(go.Scatter(x=months,y=path,mode="lines",
                        line=dict(color=h2rgba(T["accent"],0.06),width=0.8),showlegend=False,hoverinfo="skip"))
                fig_mc.update_yaxes(tickprefix="$",tickformat=",.0f")
                fig_mc.update_xaxes(title_text="Month")
                fig_mc.update_layout(**plo("Monte Carlo Portfolio Simulation",300))
                st.plotly_chart(fig_mc,use_container_width=True,config={"displayModeBar":False})
                # Results summary
                res_cols=st.columns(4)
                res_cols[0].metric("10th pct",fmtk(p10[-1]),"Worst case")
                res_cols[1].metric("Median",fmtk(p50[-1]),"Most likely")
                res_cols[2].metric("90th pct",fmtk(p90[-1]),"Best case")
                res_cols[3].metric("Contributed",fmtk(init_port+mc_contrib*12*yrs_to_retire),"Total in")
        else:
            st.markdown(f"<div style='text-align:center;padding:2rem;color:{T['muted']};font-size:0.82rem;'>"
                        f"Click 'Run Monte Carlo Simulation' to project 200 portfolio scenarios<br>over {yrs_to_retire} years to retirement.</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # FIRE calculator
        st.markdown(f"<div class='g-card'><span class='g-label'>FIRE Calculator (Financial Independence)</span>",unsafe_allow_html=True)
        st.caption("Rule of thumb: 25x annual expenses at 4% withdrawal rate.")
        ann_exp=st.number_input("Annual expenses ($)",min_value=0.0,value=float(total_exp*12),step=500.0,format="%.0f",key="f_exp")
        cur_port2=st.number_input("Portfolio ($)",min_value=0.0,value=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings"])),step=1000.0,format="%.0f",key="f_p")
        fire_r=st.slider("Return (% p.a.)",1.0,15.0,exp_mu*100,0.5,key="f_rate",format="%.1f%%")
        lean_t=ann_exp*20; fire_t=ann_exp*25; fat_t=ann_exp*33
        fi_ratio=cur_port2/fire_t*100 if fire_t>0 else 0
        bc_fi="b-ok" if fi_ratio>=100 else "b-warn" if fi_ratio>=50 else "b-bad"
        st.markdown(f"<div style='text-align:center;margin:0.5rem 0;'>"
                    f"<span style='font-size:2.5rem;font-weight:800;color:{T['accent']};'>{fi_ratio:.0f}%</span>"
                    f"<span style='font-size:0.75rem;color:{T['muted']};margin-left:8px;'>FI Ratio</span></div>",unsafe_allow_html=True)
        for lbl,tgt,col in [("Lean FIRE  (5%)",lean_t,T["blue"]),("FIRE  (4%)",fire_t,T["accent"]),("Fat FIRE  (3%)",fat_t,T["amber"])]:
            p=min(100,cur_port2/tgt*100) if tgt>0 else 0
            st.markdown(f"<div style='margin-bottom:10px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:0.76rem;margin-bottom:3px;'>"
                        f"<span>{lbl}</span><span style='color:{T['muted']};'>{p:.0f}% of {fmtk(tgt)}</span></div>"
                        f"<div class='pbar-wrap'><div class='pbar' style='width:{p:.1f}%;background:{col};'></div></div>"
                        f"</div>",unsafe_allow_html=True)
        # FIRE projection chart
        if investable>0 and fire_t>0:
            yrs_f=[]; vals_f=[]; v=cur_port2; yr_hit=None
            for yr in range(51):
                yrs_f.append(yr); vals_f.append(round(v))
                if v>=fire_t and yr_hit is None: yr_hit=yr
                v=(v+investable*12)*(1+fire_r/100)
            fig_fire=go.Figure()
            fig_fire.add_trace(go.Scatter(x=yrs_f,y=vals_f,mode="lines",name="Portfolio",
                line=dict(color=T["green"],width=2.5),fill="tozeroy",fillcolor=h2rgba(T["green"],0.1),
                hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
            for lbl,tgt,col in [("Lean",lean_t,T["blue"]),("FIRE",fire_t,T["amber"]),("Fat",fat_t,T["red"])]:
                fig_fire.add_hline(y=tgt,line_dash="dot",line_color=col,annotation_text=lbl,annotation_font_color=col,annotation_font_size=10)
            fig_fire.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_fire.update_xaxes(title_text="Years")
            fig_fire.update_layout(**plo("Path to Financial Independence",230))
            st.plotly_chart(fig_fire,use_container_width=True,config={"displayModeBar":False})
            if yr_hit:
                withdrawal=fire_t*0.04/12
                st.markdown(f"<div class='g-tip'>At current savings rate, FIRE in <b>{yr_hit} years</b> at age <b>{age_val+yr_hit}</b>. Monthly withdrawal: <b>{fmt(withdrawal)}</b>. Retirement at {ret_age} is {'achievable' if yr_hit<=yrs_to_retire else f'{yr_hit-yrs_to_retire} years later than target'}.</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Net worth + debt tracker
        total_debt=sum(l["balance"] for l in st.session_state.liabilities)
        ann_interest=sum(l["balance"]*l.get("rate",0)/100 for l in st.session_state.liabilities)
        wc1,wc2,wc3=st.columns(3)
        wc1.metric("Net Worth",fmt(net_worth)); wc2.metric("Total Debt",fmt(total_debt)); wc3.metric("Annual Interest",fmt(ann_interest))
        if st.session_state.assets or st.session_state.liabilities:
            wf_x=[a["name"] for a in st.session_state.assets]+[l["name"] for l in st.session_state.liabilities]+["Net Worth"]
            wf_m=["relative"]*len(st.session_state.assets)+["relative"]*len(st.session_state.liabilities)+["total"]
            wf_y=[a["value"] for a in st.session_state.assets]+[-l["balance"] for l in st.session_state.liabilities]+[0]
            fig_wf=go.Figure(go.Waterfall(x=wf_x,measure=wf_m,y=wf_y,
                connector=dict(line=dict(color=T["border"],width=0.5)),
                increasing=dict(marker=dict(color=T["green"])),
                decreasing=dict(marker=dict(color=T["red"])),
                totals=dict(marker=dict(color=nw_col)),
                texttemplate="%{y:$,.0f}",textposition="outside",textfont=dict(color=T["text"],size=9)))
            fig_wf.update_layout(**plo("Net Worth Waterfall",240))
            st.plotly_chart(fig_wf,use_container_width=True,config={"displayModeBar":False})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI INSIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t4:
    ins1, ins2 = st.columns(2, gap="large")
    with ins1:
        # Smart report cards
        st.markdown(f"<div class='g-card'><span class='g-label'>Financial Intelligence Report</span>",unsafe_allow_html=True)
        def insight(icon_lbl, headline, detail, badge):
            st.markdown(f"<div style='padding:0.7rem 0;border-bottom:1px solid {T['border']};'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;'>"
                        f"<span style='font-weight:600;font-size:0.82rem;'>{headline}</span>"
                        f"<span class='badge {badge[0]}'>{badge[1]}</span></div>"
                        f"<div style='font-size:0.74rem;color:{T['muted']};line-height:1.5;'>{detail}</div>"
                        f"</div>",unsafe_allow_html=True)
        ann_need=total_exp*0.6*12; ann_want=total_exp*0.4*12; ann_inv=investable*12
        over_cat=[e for e in st.session_state.expenses if e["amount"]>e.get("budget",e["amount"])]
        sub_count=len(st.session_state.subscriptions)

        if savings_rate>=20: insight("","Savings target met",f"You're saving {savings_rate:.1f}% — above the 20% target. {fmt(cash_flow)}/mo going to savings.",("b-ok","Healthy"))
        else: insight("","Savings below target",f"Savings rate is {savings_rate:.1f}%. Need {fmt(total_income*0.2-cash_flow)}/mo more to hit 20%.",("b-bad","Action"))

        if em_months>=6: insight("","Emergency fund secure",f"{em_months:.1f} months of expenses covered — you're in a strong position.",("b-ok","Secure"))
        elif em_months>=3: insight("","Emergency fund needs work",f"Only {em_months:.1f} months covered. Target: {fmt(total_exp*6)} total.",("b-warn","Build"))
        else: insight("","Emergency fund critical",f"Under 3 months ({em_months:.1f} mo). Prioritise this above everything.",("b-bad","Urgent"))

        if over_cat: insight("","Budget breaches detected",f"{len(over_cat)} category(s) overspent: {', '.join(e['name'] for e in over_cat[:4])}. Total overrun: {fmt(sum(max(0,e['amount']-e.get('budget',e['amount'])) for e in st.session_state.expenses))}.",("b-warn","Review"))
        else: insight("","Budget control excellent","All expense categories within budget. Well done.",("b-ok","On Track"))

        if total_sub>150: insight("","Subscription audit suggested",f"{sub_count} subscriptions at {fmt(total_sub)}/mo = {fmt(total_sub*12)}/yr. That's {fmt(total_sub/total_income*100) if total_income>0 else '?'}% of income.",("b-warn","Audit"))

        hi_rate=[l for l in st.session_state.liabilities if l.get("rate",0)>15]
        if hi_rate: insight("","High-interest debt alert",f"{fmt(sum(l['balance'] for l in hi_rate))} at over 15% APR. This costs {fmt(sum(l['balance']*l['rate']/100 for l in hi_rate))}/yr in interest.",("b-bad","Priority"))
        elif st.session_state.liabilities: insight("","Debt manageable",f"Total debt {fmt(total_liab)}. Annual interest approx {fmt(sum(l['balance']*l.get('rate',0)/100 for l in st.session_state.liabilities))}.",("b-ok","Managed"))

        # Retirement projection
        yrs_left=max(1,st.session_state.get("retirement_age",65)-st.session_state.get("age",32))
        projected=sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings","Super"])
        for yr in range(yrs_left): projected=(projected+investable*12)*1.07
        insight("","Retirement projection",f"At 7% growth: {fmt(projected)} at retirement age {st.session_state.get('retirement_age',65)}. Monthly draw: {fmt(projected*0.04/12)}.",("b-blue","Estimate"))
        st.markdown("</div>",unsafe_allow_html=True)

        # Spending anomalies
        st.markdown(f"<div class='g-card'><span class='g-label'>Spending Analysis</span>",unsafe_allow_html=True)
        df_ea=pd.DataFrame(st.session_state.expenses); df_ea=df_ea[df_ea["amount"]>0]
        if not df_ea.empty:
            avg=df_ea["amount"].mean(); std=df_ea["amount"].std()
            anomalies=df_ea[df_ea["amount"]>avg+std].sort_values("amount",ascending=False)
            if not anomalies.empty:
                for _,row in anomalies.head(3).iterrows():
                    bud=row.get("budget",row["amount"]); pct_a=row["amount"]/bud*100 if bud>0 else 100
                    st.markdown(f"<div class='g-row'>"
                                f"<div><span style='font-weight:600;'>{row['name']}</span>"
                                f"<span style='font-size:0.68rem;color:{T['muted']};margin-left:8px;'>{row.get('category','')}</span></div>"
                                f"<div><span style='color:{T['red']};font-weight:600;'>{fmt(row['amount'])}</span>"
                                f"<span style='font-size:0.65rem;color:{T['muted']};margin-left:5px;'>{pct_a:.0f}% of budget</span></div>"
                                f"</div>",unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color:{T['muted']};font-size:0.8rem;padding:0.5rem 0;'>No anomalous spending detected. Spending is consistent across categories.</div>",unsafe_allow_html=True)

            # Bar chart: income vs expenses trend (illustrative)
            cats=df_ea.groupby("category")["amount"].sum().reset_index().sort_values("amount",ascending=True)
            fig_h=go.Figure(go.Bar(y=cats["category"],x=cats["amount"],orientation="h",
                marker_color=[T["red"] if v>1500 else T["amber"] if v>700 else T["green"] for v in cats["amount"]],
                text=[fmt(v) for v in cats["amount"]],textposition="outside",textfont=dict(color=T["text"],size=10)))
            fig_h.update_layout(**plo("Spending by Category",230)); fig_h.update_xaxes(tickprefix="$")
            st.plotly_chart(fig_h,use_container_width=True,config={"displayModeBar":False})
        st.markdown("</div>",unsafe_allow_html=True)

    with ins2:
        # Achievements & gamification
        badges=get_badges()
        st.markdown(f"<div class='g-card'><span class='g-label'>Achievements — {len(badges)} Unlocked</span>",unsafe_allow_html=True)
        badge_cols=st.columns(2)
        badge_map={"green":"b-ok","blue":"b-blue","purple":"b-pur","gold":"b-gold","amber":"b-amb","red":"b-bad"}
        for i,(name,desc,col) in enumerate(badges):
            bcm=badge_map.get(col,"b-ok")
            with badge_cols[i%2]:
                st.markdown(f"<div class='achieve-card' style='margin-bottom:8px;'>"
                            f"<div class='badge {bcm}' style='margin-bottom:5px;display:block;'>{name}</div>"
                            f"<div style='font-size:0.68rem;color:{T['muted']};'>{desc}</div>"
                            f"</div>",unsafe_allow_html=True)
        # Streak
        streak=st.session_state.get("streak_days",14)
        st.markdown(f"<div style='text-align:center;padding:0.7rem 0;background:{h2rgba(T['accent'],0.08)};border-radius:{10}px;margin-top:6px;'>"
                    f"<div style='font-size:2rem;font-weight:800;color:{T['accent']};'>{streak}</div>"
                    f"<div style='font-size:0.68rem;color:{T['muted']};text-transform:uppercase;letter-spacing:0.08em;'>Day Budget Streak</div>"
                    f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Financial predictions
        st.markdown(f"<div class='g-card'><span class='g-label'>Predictions & Projections</span>",unsafe_allow_html=True)
        predictions=[
            ("Savings in 12 months",fmt(cash_flow*12+cash_assets),"at current rate",T["green"]),
            ("Net worth in 5 years",fmt(net_worth+(cash_flow+investable)*12*5),"estimated",T["blue"]),
            ("Subscription cost per year",fmt(total_sub*12),"review annually",T["amber"]),
            ("Interest paid on debt /yr",fmt(sum(l["balance"]*l.get("rate",0)/100 for l in st.session_state.liabilities)),"cost of carrying debt",T["red"]),
            ("FIRE number needed",fmt(total_exp*12*25),"at 4% withdrawal rule",T["purple"]),
        ]
        for lbl,val,note,col in predictions:
            st.markdown(f"<div style='padding:0.5rem 0;border-bottom:1px solid {T['border']};'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:0.8rem;'>"
                        f"<span style='color:{T['muted']}'>{lbl}</span>"
                        f"<span style='color:{col};font-weight:600;'>{val}</span></div>"
                        f"<div style='font-size:0.65rem;color:{T['muted']};'>{note}</div>"
                        f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Net worth timeline
        nw_years=[]; nw_vals=[]; nw_v=net_worth
        for yr in range(11):
            nw_years.append(yr); nw_vals.append(round(nw_v))
            nw_v=nw_v+cash_flow*12+investable*12*0.07
        fig_nw=go.Figure(go.Scatter(x=nw_years,y=nw_vals,mode="lines+markers",
            line=dict(color=T["accent"],width=2.5),fill="tozeroy",fillcolor=h2rgba(T["accent"],0.1),
            marker=dict(size=5,color=T["accent"]),hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
        fig_nw.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_nw.update_xaxes(title_text="Years from now")
        fig_nw.update_layout(**plo("10-Year Net Worth Projection",230))
        st.plotly_chart(fig_nw,use_container_width=True,config={"displayModeBar":False})

        # Monthly cashflow breakdown
        cf_labels=["Income","Needs","Wants","Invest","Remaining"]
        cf_vals=[total_income,-total_exp*0.6,-total_exp*0.4,-investable,cash_flow]
        cf_colors=[T["green"],T["blue"],T["amber"],T["purple"],T["green"] if cash_flow>=0 else T["red"]]
        fig_cf=go.Figure(go.Waterfall(x=cf_labels,measure=["absolute","relative","relative","relative","total"],y=[total_income,-total_exp*0.6,-total_exp*0.4,-investable,0],
            connector=dict(line=dict(color=T["border"],width=0.5)),
            increasing=dict(marker=dict(color=T["green"])),decreasing=dict(marker=dict(color=T["red"])),
            totals=dict(marker=dict(color=T["green"] if cash_flow>=0 else T["red"])),
            texttemplate="%{y:$,.0f}",textposition="outside",textfont=dict(color=T["text"],size=9)))
        fig_cf.update_layout(**plo("Monthly Cash Flow Breakdown",210))
        st.plotly_chart(fig_cf,use_container_width=True,config={"displayModeBar":False})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI ASSISTANT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t5:
    ai1, ai2 = st.columns([2.5,1.5], gap="large")
    with ai1:
        st.markdown(f"<div class='g-card'><span class='g-label'>AI Financial Advisor — Powered by Claude</span>",unsafe_allow_html=True)
        api_key=st.text_input("Anthropic API Key (starts with sk-ant-...)",type="password",placeholder="sk-ant-...",key="api_key",
            help="Get your key at console.anthropic.com. Never shared or stored.")

        if api_key:
            # Suggested prompts
            st.markdown(f"<div style='font-size:0.68rem;color:{T['muted']};margin-bottom:6px;'>Suggested questions:</div>",unsafe_allow_html=True)
            sp_cols=st.columns(2)
            prompts=[f"Can I afford a $40k car?",f"How do I reduce expenses by {fmt(total_exp*0.1)}/mo?",
                     f"Should I pay off debt or invest?","How do I reach my property deposit goal faster?",
                     f"What's my projected retirement age?","How can I boost my savings rate to 20%?"]
            for i,p in enumerate(prompts):
                with sp_cols[i%2]:
                    if st.button(p,key=f"sp_{i}",use_container_width=True):
                        st.session_state.chat_history.append({"role":"user","content":p})
                        with st.spinner("Thinking..."):
                            reply=ask_claude(st.session_state.chat_history,api_key,"")
                        st.session_state.chat_history.append({"role":"assistant","content":reply})
                        st.rerun()

            # Chat display
            if st.session_state.chat_history:
                st.markdown("<div class='chat-wrap'>",unsafe_allow_html=True)
                for msg in st.session_state.chat_history[-12:]:
                    if msg["role"]=="user":
                        st.markdown(f"<div class='chat-user'>{msg['content']}</div>",unsafe_allow_html=True)
                    else:
                        content=msg["content"].replace("\n","<br>")
                        st.markdown(f"<div class='chat-ai'>{content}</div>",unsafe_allow_html=True)
                st.markdown("</div>",unsafe_allow_html=True)
                st.markdown("<div style='clear:both;margin:0.5rem 0;'></div>",unsafe_allow_html=True)

            # Input
            user_input=st.chat_input("Ask your AI financial advisor anything...")
            if user_input:
                st.session_state.chat_history.append({"role":"user","content":user_input})
                with st.spinner("Your advisor is thinking..."):
                    reply=ask_claude(st.session_state.chat_history,api_key,"")
                st.session_state.chat_history.append({"role":"assistant","content":reply})
                st.rerun()

            if st.button("Clear conversation",key="clear_chat"):
                st.session_state.chat_history=[]; st.rerun()
        else:
            st.markdown(f"<div style='text-align:center;padding:2rem;'>"
                        f"<div style='font-size:2.5rem;margin-bottom:0.8rem;color:{T['accent']};'>AI</div>"
                        f"<div style='font-size:1rem;font-weight:600;color:{T['text']};margin-bottom:0.5rem;'>AI Financial Advisor</div>"
                        f"<div style='font-size:0.8rem;color:{T['muted']};max-width:380px;margin:0 auto;line-height:1.6;'>"
                        f"Enter your Anthropic API key above to chat with a personalised AI financial advisor. "
                        f"The assistant knows your financial profile and will give you specific, actionable advice.</div>"
                        f"<div style='margin-top:1rem;font-size:0.72rem;color:{T['muted']};'>Get your key at <b>console.anthropic.com</b></div>"
                        f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    with ai2:
        st.markdown(f"<div class='g-card'><span class='g-label'>Your Financial Profile (AI Context)</span>",unsafe_allow_html=True)
        ctx_items=[
            ("Monthly Income",fmt(total_income)),("Monthly Expenses",fmt(total_exp)),
            ("Savings Rate",pct(savings_rate)),("Emergency Fund",f"{em_months:.1f} months"),
            ("Net Worth",fmt(net_worth)),("Total Debt",fmt(total_liab)),
            ("Invest /mo",fmt(investable)),("Health Score",f"{hs}/100"),
            ("Risk Profile",st.session_state.get("risk_profile","Moderate")),
            ("Age / Retire",f"{st.session_state.get('age',32)} / {st.session_state.get('retirement_age',65)}"),
            ("Goals",str(len(st.session_state.goals))),
        ]
        for lbl,val in ctx_items:
            st.markdown(f"<div class='g-row'><span style='color:{T['muted']};'>{lbl}</span>"
                        f"<span style='font-weight:600;color:{T['text']};'>{val}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='g-tip'>Your financial context is automatically provided to the AI advisor so you get personalised, specific answers without repeating yourself.</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='g-card'><span class='g-label'>Example Questions</span>",unsafe_allow_html=True)
        qs=["Can I afford to quit my job?","Should I rent or buy property?","How do I optimise my tax?",
            "What investment strategy suits my risk?","How much life insurance do I need?","Should I get income protection?"]
        for q in qs:
            st.markdown(f"<div class='g-row'><span style='font-size:0.78rem;color:{T['muted']};'>{q}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRO / PREMIUM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t6:
    st.markdown(f"<div style='text-align:center;padding:1.5rem 0 1rem;'>"
                f"<div class='grad-text' style='font-size:2.2rem;font-weight:800;letter-spacing:-0.03em;'>Seralung Finance Pro</div>"
                f"<div style='color:{T['muted']};font-size:0.88rem;margin-top:0.4rem;'>Your complete financial operating system</div>"
                f"</div>",unsafe_allow_html=True)

    # Pricing cards
    pc1,pc2,pc3=st.columns(3,gap="large")
    def pro_card(title,price,period,features,is_featured=False):
        border=f"border: 2px solid {T['accent']};" if is_featured else f"border: 1px solid {T['border']};"
        glow=f"box-shadow: var(--shadow-accent);" if is_featured else ""
        badge=f"<span class='badge b-ok' style='display:block;margin:0 auto 0.5rem;width:fit-content;'>Most Popular</span>" if is_featured else ""
        feats="".join(f"<div style='padding:0.3rem 0;font-size:0.78rem;color:{T['text']};border-bottom:1px solid {T['border']};display:flex;align-items:center;gap:8px;'>"
                      f"<span style='color:{T['green']};font-weight:700;'>+</span>{f}</div>" for f in features)
        return (f"<div style='background:{T['surface']};{border}{glow}border-radius:20px;padding:1.5rem;text-align:center;'>"
                f"{badge}"
                f"<div style='font-size:1rem;font-weight:700;color:{T['text']};margin-bottom:0.5rem;'>{title}</div>"
                f"<div style='font-size:2.4rem;font-weight:800;color:{T['accent']};letter-spacing:-0.03em;'>{price}</div>"
                f"<div style='font-size:0.7rem;color:{T['muted']};margin-bottom:1rem;'>{period}</div>"
                f"<div style='text-align:left;margin-bottom:1rem;'>{feats}</div>"
                f"</div>")

    with pc1:
        st.markdown(pro_card("Free",
            "$0","Forever",
            ["Dashboard overview","Basic budgeting","Manual expense entry","3 financial goals","CSV export"]),unsafe_allow_html=True)
        st.button("Get started free",use_container_width=True,key="free_btn")

    with pc2:
        st.markdown(pro_card("Pro",
            "$9","per month",
            ["Everything in Free","Unlimited goals","AI-powered insights","Monte Carlo simulation","Bank import (CSV)","PDF reports","Debt payoff planner","FIRE calculator","AUS tax estimator"],
            is_featured=True),unsafe_allow_html=True)
        st.button("Start Pro free trial",use_container_width=True,key="pro_btn")

    with pc3:
        st.markdown(pro_card("Premium",
            "$19","per month",
            ["Everything in Pro","AI Financial Advisor (Claude)","Investment risk profiler","Family/partner budgeting","Multi-account support","Advanced analytics","Priority support","Tax optimisation","Advisor mode","Custom categories"]),unsafe_allow_html=True)
        st.button("Start Premium trial",use_container_width=True,key="prem_btn")

    st.divider()
    # Feature comparison
    st.markdown(f"<div class='g-card'><span class='g-label'>Why users upgrade</span>",unsafe_allow_html=True)
    testimonials=[
        ('"The Monte Carlo simulation showed me I could retire 8 years earlier with a small strategy change."','- David K., Melbourne'),
        ('"AI advisor answered questions my bank charge $500/hr to explain."','- Sarah L., Sydney'),
        ('"Finally understand where my money goes. Paid for itself in the first month."','- James W., Brisbane'),
    ]
    tc=st.columns(3)
    for i,(quote,author) in enumerate(testimonials):
        with tc[i]:
            st.markdown(f"<div style='background:{T['surface2']};border:1px solid {T['border']};border-radius:{14}px;padding:1rem;'>"
                        f"<div style='font-size:0.8rem;color:{T['text']};line-height:1.6;font-style:italic;margin-bottom:0.6rem;'>{quote}</div>"
                        f"<div style='font-size:0.68rem;color:{T['muted']};font-weight:600;'>{author}</div>"
                        f"</div>",unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;font-size:0.67rem;color:{T['muted']};margin-top:0.5rem;'>Cancel anytime. No contracts. 30-day money-back guarantee.</p>",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"<p style='text-align:center;color:{T['muted']};font-size:0.64rem;letter-spacing:0.03em;'>"
            "SERALUNG FINANCE PREMIUM  |  Educational use only. Not financial advice. "
            "Always consult a qualified financial adviser.  |  AUS Tax FY2024-25</p>",unsafe_allow_html=True)
