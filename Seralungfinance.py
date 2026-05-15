"""
╔══════════════════════════════════════════════════════════╗
║          Seralung Finance Pro  —  requirements.txt       ║
║  streamlit>=1.32                                         ║
║  plotly>=5.18                                            ║
║  pandas>=2.0                                             ║
║  fpdf2>=2.7                                              ║
║                                                          ║
║  Run:  streamlit run seralung_finance_pro.py             ║
╚══════════════════════════════════════════════════════════╝
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math, io, json, csv, re, base64
from datetime import datetime, date, timedelta

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Seralung Finance Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# THEMES
# ═══════════════════════════════════════════════════════════════════════════════
THEMES = {
    "Obsidian ✦": {
        "bg":"#0A0A0F","surface":"#13131A","surface2":"#1C1C28","border":"#2A2A3E",
        "accent":"#C9A84C","accent2":"#E8C87A","text":"#F0EEE8","muted":"#7A7A9A",
        "green":"#4ADE80","red":"#F87171","amber":"#FBBF24","blue":"#60A5FA",
        "chart_colors":["#C9A84C","#4ADE80","#60A5FA","#F87171","#A78BFA","#34D399"],"dark":True,
    },
    "Arctic ❄": {
        "bg":"#F8FAFB","surface":"#FFFFFF","surface2":"#EEF2F5","border":"#CBD5E1",
        "accent":"#0EA5E9","accent2":"#38BDF8","text":"#0F172A","muted":"#64748B",
        "green":"#10B981","red":"#EF4444","amber":"#F59E0B","blue":"#3B82F6",
        "chart_colors":["#0EA5E9","#10B981","#F59E0B","#EF4444","#8B5CF6","#06B6D4"],"dark":False,
    },
    "Emerald ◆": {
        "bg":"#061510","surface":"#0C2118","surface2":"#122B20","border":"#1E4A32",
        "accent":"#34D399","accent2":"#6EE7B7","text":"#ECFDF5","muted":"#9CA3AF",
        "green":"#34D399","red":"#F87171","amber":"#FCD34D","blue":"#60A5FA",
        "chart_colors":["#34D399","#60A5FA","#FCD34D","#F87171","#A78BFA","#38BDF8"],"dark":True,
    },
    "Sunset 🌅": {
        "bg":"#FFF7ED","surface":"#FFFFFF","surface2":"#FEF3C7","border":"#FCD34D",
        "accent":"#EA580C","accent2":"#FB923C","text":"#1C0A00","muted":"#92400E",
        "green":"#16A34A","red":"#DC2626","amber":"#D97706","blue":"#2563EB",
        "chart_colors":["#EA580C","#F59E0B","#16A34A","#DC2626","#7C3AED","#0891B2"],"dark":False,
    },
    "Royal ♚": {
        "bg":"#07071A","surface":"#0D0D2B","surface2":"#141438","border":"#23234A",
        "accent":"#818CF8","accent2":"#A5B4FC","text":"#EEF2FF","muted":"#94A3B8",
        "green":"#34D399","red":"#F87171","amber":"#FCD34D","blue":"#60A5FA",
        "chart_colors":["#818CF8","#34D399","#FCD34D","#F87171","#38BDF8","#C084FC"],"dark":True,
    },
    "Slate Pro": {
        "bg":"#0F1117","surface":"#1A1D27","surface2":"#22263A","border":"#2E3350",
        "accent":"#6C8EF5","accent2":"#4ECDC4","text":"#E8EAF6","muted":"#8B90B0",
        "green":"#43D9A2","red":"#FF6B6B","amber":"#FFB347","blue":"#6C8EF5",
        "chart_colors":["#6C8EF5","#4ECDC4","#FF6B6B","#FFB347","#43D9A2","#C084FC"],"dark":True,
    },
}

CATEGORIES = ["Housing","Food","Transport","Health","Insurance","Tech","Entertainment","Personal","Education","Other"]
ASSET_TYPES = ["Cash","Savings","Investments","Super","Property","Vehicle","Business","Other"]
LIAB_TYPES  = ["Mortgage","Loan","Credit","HECS","Personal","Business","Other"]

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════
def _init(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

_init("expenses",[
    {"name":"Rent / Mortgage",   "amount":1800.0,"budget":2000.0,"category":"Housing"},
    {"name":"Groceries",         "amount":450.0, "budget":500.0, "category":"Food"},
    {"name":"Transport",         "amount":250.0, "budget":300.0, "category":"Transport"},
    {"name":"Dining & Takeaway", "amount":350.0, "budget":300.0, "category":"Food"},
    {"name":"Utilities",         "amount":180.0, "budget":220.0, "category":"Housing"},
    {"name":"Phone Plan",        "amount":85.0,  "budget":85.0,  "category":"Tech"},
    {"name":"Insurance",         "amount":150.0, "budget":200.0, "category":"Insurance"},
    {"name":"Entertainment",     "amount":120.0, "budget":150.0, "category":"Entertainment"},
    {"name":"Health & Fitness",  "amount":80.0,  "budget":100.0, "category":"Health"},
    {"name":"Clothing",          "amount":80.0,  "budget":100.0, "category":"Personal"},
])
_init("subscriptions",[
    {"name":"Netflix",       "amount":18.0, "cycle":"Monthly"},
    {"name":"Spotify",       "amount":12.0, "cycle":"Monthly"},
    {"name":"Amazon Prime",  "amount":9.99, "cycle":"Monthly"},
    {"name":"Gym",           "amount":45.0, "cycle":"Monthly"},
    {"name":"Cloud Storage", "amount":5.0,  "cycle":"Monthly"},
])
_init("bills",[
    {"name":"Rent",        "amount":1800.0,"due_day":1},
    {"name":"Electricity", "amount":180.0, "due_day":15},
    {"name":"Internet",    "amount":90.0,  "due_day":20},
    {"name":"Phone",       "amount":85.0,  "due_day":25},
])
_init("assets",[
    {"name":"Savings Account", "type":"Cash",       "value":12000.0},
    {"name":"Superannuation",  "type":"Super",      "value":35000.0},
    {"name":"Car",             "type":"Vehicle",    "value":18000.0},
    {"name":"ETF Portfolio",   "type":"Investments","value":8500.0},
])
_init("liabilities",[
    {"name":"Car Loan",   "type":"Loan",  "balance":14000.0,"rate":6.5, "min_payment":350.0},
    {"name":"Credit Card","type":"Credit","balance":2800.0, "rate":19.99,"min_payment":84.0},
    {"name":"HECS Debt",  "type":"HECS", "balance":18000.0,"rate":3.9, "min_payment":200.0},
])
_init("goals",[
    {"name":"Emergency Fund",             "amount":15000.0,"saved":12000.0,"priority":"High"},
    {"name":"Europe Holiday",             "amount":8000.0, "saved":2000.0, "priority":"Medium"},
    {"name":"Investment Property Deposit","amount":80000.0,"saved":25000.0,"priority":"High"},
])
_init("transactions",[])
_init("risk_profile","Moderate")
_init("needs_pct",50); _init("wants_pct",30); _init("invest_pct",20)
_init("em_pct",30);    _init("idx_pct",40);   _init("stk_pct",20); _init("cry_pct",10)

# ═══════════════════════════════════════════════════════════════════════════════
# T-INDEPENDENT HELPERS  (defined before sidebar)
# ═══════════════════════════════════════════════════════════════════════════════
def pct_slider(label, key, default):
    cur = st.session_state.get(key, default)
    c1, c2 = st.columns([3, 1])
    with c1:
        s = st.slider(label, 0, 100, int(cur), 1, key=f"{key}_s")
    with c2:
        n = st.number_input("%", 0, 100, s, key=f"{key}_n", label_visibility="visible")
    final = n if n != s else s
    st.session_state[key] = final
    return final

def calc_tax(income):
    if   income <= 18200:  return 0.0
    elif income <= 45000:  return (income-18200)*0.19
    elif income <= 135000: return 5092+(income-45000)*0.325
    elif income <= 190000: return 31288+(income-135000)*0.37
    else:                  return 51638+(income-190000)*0.45

def calc_lito(income):
    if   income <= 37500: return 700.0
    elif income <= 45000: return 700-(income-37500)*0.05
    elif income <= 66667: return 325-(income-45000)*0.015
    else:                 return 0.0

def fmt(n): return f"${n:,.0f}"

def auto_categorize(desc):
    d = str(desc).lower()
    rules = [
        (["rent","lease","real estate","landlord","property manager"],"Housing"),
        (["mortgage","home loan"],"Housing"),
        (["electricity","power","energy","agl","origin","simply"],"Housing"),
        (["internet","nbn","optus","telstra","vodafone","tpg","iinet"],"Tech"),
        (["coles","woolworths","aldi","iga","harris farm","costco","supermarket","grocer"],"Food"),
        (["uber eats","menulog","doordash","deliveroo","mcdonalds","kfc","subway","dominos",
           "pizza","cafe","coffee","restaurant","takeaway","bakery","sushi"],"Food"),
        (["netflix","stan","disney","binge","foxtel","spotify","apple music","youtube premium",
           "amazon prime","hbo","paramount"],"Entertainment"),
        (["gym","fitness","yoga","pilates","crossfit","anytime fitness","f45"],"Health"),
        (["pharmacy","chemist","doctor","medical","dental","hospital","medibank","bupa","ahm","hbf"],"Health"),
        (["fuel","petrol","shell","bp","caltex","ampol","7-eleven"],"Transport"),
        (["uber","ola","didi","taxi","parking","toll","myki","opal","go card","translink","bus","train","tram"],"Transport"),
        (["insurance","nrma","aami","racv","gio","allianz","qbe"],"Insurance"),
        (["clothing","h&m","zara","uniqlo","target","kmart","cotton on","country road","myer","david jones"],"Personal"),
        (["amazon","ebay","paypal","afterpay","zip","klarna"],"Personal"),
        (["school","university","tafe","course","udemy","coursera","textbook","tuition"],"Education"),
    ]
    for kws, cat in rules:
        if any(k in d for k in kws):
            return cat
    return "Other"

def parse_bank_csv(uploaded_file):
    try:
        content = uploaded_file.read().decode("utf-8", errors="replace")
        lines = content.strip().split("\n")
        header_idx = 0
        for i, line in enumerate(lines):
            low = line.lower()
            if any(k in low for k in ["date","amount","description","debit","credit","transaction"]):
                header_idx = i
                break
        df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])), on_bad_lines="skip", dtype=str)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        date_col  = next((c for c in df.columns if "date" in c), None)
        desc_col  = next((c for c in df.columns if any(k in c for k in ["description","details","narration","memo","narrative","transaction","reference"])), None)
        amt_col   = next((c for c in df.columns if c=="amount" or c=="net_amount"), None)
        debit_col = next((c for c in df.columns if "debit" in c), None)
        credit_col= next((c for c in df.columns if "credit" in c), None)
        if not date_col or not desc_col:
            return None, "Could not identify Date/Description columns. Check CSV format."
        res = pd.DataFrame()
        res["Date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        res["Description"] = df[desc_col].fillna("Unknown").str.strip()
        if amt_col:
            res["Amount"] = pd.to_numeric(df[amt_col].str.replace(r'[$,\s]','',regex=True), errors="coerce").fillna(0)
        elif debit_col and credit_col:
            d = pd.to_numeric(df[debit_col].str.replace(r'[$,\s]','',regex=True), errors="coerce").fillna(0)
            c = pd.to_numeric(df[credit_col].str.replace(r'[$,\s]','',regex=True), errors="coerce").fillna(0)
            res["Amount"] = c - d
        else:
            return None, "Could not find Amount/Debit/Credit columns."
        res["Category"] = res["Description"].apply(auto_categorize)
        res = res.dropna(subset=["Date"]).copy()
        res = res[res["Amount"] != 0].sort_values("Date", ascending=False)
        return res, None
    except Exception as e:
        return None, str(e)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 💎 Seralung Finance Pro")
    st.markdown("---")
    theme_name = st.selectbox("Theme", list(THEMES.keys()))
    T = THEMES[theme_name]
    st.markdown("---")
    st.markdown("<p style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;'>Monthly Income (AUD)</p>", unsafe_allow_html=True)
    primary_income = st.number_input("Primary (after tax)", min_value=0.0, value=6000.0, step=100.0, format="%.0f")
    other_income   = st.number_input("Other income",        min_value=0.0, value=500.0,  step=50.0,  format="%.0f")
    total_income   = primary_income + other_income
    st.markdown("---")
    st.markdown("<p style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;'>Budget Rule</p>", unsafe_allow_html=True)
    st.caption("Sliders must sum to 100%")
    needs_pct  = pct_slider("🏠 Needs %",    "needs_pct",  50)
    wants_pct  = pct_slider("🎉 Wants %",    "wants_pct",  30)
    invest_pct = pct_slider("📈 Invest %",   "invest_pct", 20)
    _sum = needs_pct + wants_pct + invest_pct
    if _sum != 100:
        st.warning(f"Sum = {_sum}% — adjust to 100%")
    st.markdown("---")
    if st.button("🔄 Reset Demo Data", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    st.caption("Educational only. Not financial advice.")

# ═══════════════════════════════════════════════════════════════════════════════
# T-DEPENDENT HELPERS  (T is now set from sidebar)
# ═══════════════════════════════════════════════════════════════════════════════
def hex_to_rgba(hx, a=0.15):
    h = hx.lstrip("#")
    r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
    return f"rgba({r},{g},{b},{a})"

def plot_layout(title="", height=280):
    d = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans,sans-serif",color=T["muted"],size=11),
        height=height, margin=dict(l=10,r=10,t=36 if title else 10,b=10),
        legend=dict(font=dict(color=T["muted"],size=11),bgcolor="rgba(0,0,0,0)",borderwidth=0),
        xaxis=dict(gridcolor=T["border"],linecolor=T["border"],showgrid=True,color=T["muted"]),
        yaxis=dict(gridcolor=T["border"],linecolor=T["border"],showgrid=True,color=T["muted"]),
    )
    if title: d["title"] = dict(text=title,font=dict(color=T["text"],size=13))
    return d

def calc_health_score():
    score, det = 0, {}
    tsub = sum(s["amount"] for s in st.session_state.subscriptions)
    mexp = sum(e["amount"] for e in st.session_state.expenses) + tsub
    sr = (total_income - mexp)/total_income*100 if total_income > 0 else 0
    s1 = min(25, sr/20*25); score += s1
    det["savings"]={"score":s1,"max":25,"label":"Savings rate","value":f"{sr:.1f}%","good":sr>=20}
    cash = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
    em = cash/mexp if mexp > 0 else 0
    s2 = min(20, em/6*20); score += s2
    det["emergency"]={"score":s2,"max":20,"label":"Emergency fund","value":f"{em:.1f} months","good":em>=6}
    nd = sum(l["balance"] for l in st.session_state.liabilities if l["type"]!="HECS")
    dti = nd/(total_income*12)*100 if total_income > 0 else 0
    s3 = max(0, 20-dti*0.5); score += s3
    det["debt"]={"score":s3,"max":20,"label":"Debt-to-income","value":f"{dti:.0f}%","good":dti<=36}
    nw = sum(a["value"] for a in st.session_state.assets)-sum(l["balance"] for l in st.session_state.liabilities)
    s4 = 15 if nw>0 else max(0,15+nw/10000); score += s4
    det["networth"]={"score":s4,"max":15,"label":"Net worth positive","value":fmt(nw),"good":nw>0}
    over = sum(max(0,e["amount"]-e.get("budget",e["amount"])) for e in st.session_state.expenses)
    s5 = max(0,10-over/100); score += s5
    det["budget"]={"score":s5,"max":10,"label":"Budget adherence","value":f"{fmt(over)} over","good":over==0}
    s6 = min(10,len(st.session_state.goals)*3.5); score += s6
    det["goals"]={"score":s6,"max":10,"label":"Goals set","value":f"{len(st.session_state.goals)} active","good":len(st.session_state.goals)>=2}
    return round(score), det

# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════
def generate_csv_report(period="Monthly"):
    tsub = sum(s["amount"] for s in st.session_state.subscriptions)
    texp = sum(e["amount"] for e in st.session_state.expenses) + tsub
    nw   = sum(a["value"] for a in st.session_state.assets) - sum(l["balance"] for l in st.session_state.liabilities)
    sr   = (total_income-texp)/total_income*100 if total_income>0 else 0
    hs,_ = calc_health_score()
    buf  = io.StringIO()
    w    = csv.writer(buf)
    now  = datetime.now().strftime("%B %Y")
    w.writerow([f"Seralung Finance Pro — {period} Report — {now}"])
    w.writerow([f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}"])
    w.writerow([])
    w.writerow(["SUMMARY"])
    w.writerow(["Metric","Value"])
    for lbl,val in [("Financial Health Score",f"{hs}/100"),("Monthly Income",fmt(total_income)),
                    ("Total Expenses",fmt(texp)),("Net Cash Flow",fmt(total_income-texp)),
                    ("Savings Rate",f"{sr:.1f}%"),("Net Worth",fmt(nw)),
                    ("Total Assets",fmt(sum(a['value'] for a in st.session_state.assets))),
                    ("Total Liabilities",fmt(sum(l['balance'] for l in st.session_state.liabilities)))]:
        w.writerow([lbl,val])
    w.writerow([])
    w.writerow(["EXPENSES"])
    w.writerow(["Name","Category","Spent ($)","Budget ($)","Over Budget ($)","Status"])
    for e in st.session_state.expenses:
        budget = e.get("budget",e["amount"]); over = max(0,e["amount"]-budget)
        w.writerow([e["name"],e.get("category","Other"),f"{e['amount']:.2f}",f"{budget:.2f}",f"{over:.2f}","OVER" if over>0 else "OK"])
    w.writerow([])
    w.writerow(["SUBSCRIPTIONS"])
    w.writerow(["Name","Amount ($)","Cycle"])
    for s in st.session_state.subscriptions:
        w.writerow([s["name"],f"{s['amount']:.2f}",s.get("cycle","Monthly")])
    w.writerow(["TOTAL",f"{tsub:.2f}",""])
    w.writerow([])
    w.writerow(["ASSETS"])
    w.writerow(["Name","Type","Value ($)"])
    for a in st.session_state.assets:
        w.writerow([a["name"],a["type"],f"{a['value']:.2f}"])
    w.writerow(["TOTAL","",f"{sum(a['value'] for a in st.session_state.assets):.2f}"])
    w.writerow([])
    w.writerow(["LIABILITIES"])
    w.writerow(["Name","Type","Balance ($)","Rate (%)","Min Payment ($)","Monthly Interest ($)"])
    for l in st.session_state.liabilities:
        mi = l["balance"]*l.get("rate",0)/100/12
        w.writerow([l["name"],l["type"],f"{l['balance']:.2f}",f"{l.get('rate',0):.2f}",f"{l.get('min_payment',0):.2f}",f"{mi:.2f}"])
    w.writerow([])
    w.writerow(["GOALS"])
    w.writerow(["Name","Priority","Target ($)","Saved ($)","Remaining ($)","Progress (%)","Months to Goal"])
    for g in st.session_state.goals:
        rem = max(0,g["amount"]-g["saved"]); pct = g["saved"]/g["amount"]*100 if g["amount"]>0 else 0
        inv = total_income*invest_pct/100
        mo  = math.ceil(rem/inv) if inv>0 else 9999
        w.writerow([g["name"],g.get("priority","Medium"),f"{g['amount']:.2f}",f"{g['saved']:.2f}",f"{rem:.2f}",f"{pct:.1f}%",mo])
    w.writerow([])
    if st.session_state.transactions:
        w.writerow(["IMPORTED TRANSACTIONS"])
        w.writerow(["Date","Description","Amount ($)","Category"])
        for tx in st.session_state.transactions:
            w.writerow([tx.get("Date",""),tx.get("Description",""),f"{tx.get('Amount',0):.2f}",tx.get("Category","Other")])
        w.writerow([])
    w.writerow(["Seralung Finance Pro — Educational only. Not financial advice."])
    return buf.getvalue().encode("utf-8")

def generate_pdf_report(period="Monthly"):
    if not PDF_AVAILABLE:
        return None
    tsub = sum(s["amount"] for s in st.session_state.subscriptions)
    texp = sum(e["amount"] for e in st.session_state.expenses) + tsub
    nw   = sum(a["value"] for a in st.session_state.assets) - sum(l["balance"] for l in st.session_state.liabilities)
    sr   = (total_income-texp)/total_income*100 if total_income>0 else 0
    hs,_ = calc_health_score()
    grade = "Excellent" if hs>=80 else "Good" if hs>=65 else "Fair" if hs>=50 else "Needs Work" if hs>=35 else "Critical"

    pdf = FPDF(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()

    # Header banner
    pdf.set_fill_color(10,10,15); pdf.rect(0,0,210,42,"F")
    pdf.set_font("Helvetica","B",22); pdf.set_text_color(201,168,76)
    pdf.cell(0,18,"",ln=True); pdf.cell(0,14,"  Seralung Finance Pro",ln=True)
    pdf.set_font("Helvetica","",11); pdf.set_text_color(200,200,200)
    pdf.cell(0,8,f"  {period} Financial Report  —  {datetime.now().strftime('%B %Y')}",ln=True)
    pdf.ln(10)

    # Health Score
    sc_rgb = (74,222,128) if hs>=70 else (251,191,36) if hs>=50 else (248,113,113)
    pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","B",13)
    pdf.cell(0,8,"Financial Health Score",ln=True)
    pdf.set_font("Helvetica","B",40); pdf.set_text_color(*sc_rgb)
    pdf.cell(0,16,f"{hs} / 100",ln=True)
    pdf.set_font("Helvetica","",12); pdf.set_text_color(80,80,80)
    pdf.cell(0,8,f"{grade}  |  Generated {datetime.now().strftime('%d %b %Y %H:%M')}",ln=True); pdf.ln(4)

    # Summary table
    def section(title):
        pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","B",13)
        pdf.cell(0,10,title,ln=True)

    def tbl_header(*cols_w):
        pdf.set_fill_color(20,30,20); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
        return cols_w

    def tbl_row(i, cells, widths, colors=None):
        fill = (245,250,246) if i%2==0 else (255,255,255)
        pdf.set_fill_color(*fill); pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","",9)
        for j,(cell,w) in enumerate(zip(cells,widths)):
            if colors and j==len(cells)-1:
                pdf.set_text_color(*colors)
            txt = str(cell)[:30]
            pdf.cell(w,7,f" {txt}",border=0,fill=True)
        pdf.set_text_color(30,30,30); pdf.ln()

    section("Monthly Summary")
    rows=[("Monthly Income",fmt(total_income)),("Total Expenses",fmt(texp)),
          ("Net Cash Flow",fmt(total_income-texp)),("Savings Rate",f"{sr:.1f}%"),
          ("Net Worth",fmt(nw)),("Total Assets",fmt(sum(a['value'] for a in st.session_state.assets))),
          ("Total Liabilities",fmt(sum(l['balance'] for l in st.session_state.liabilities)))]
    for i,(lbl,val) in enumerate(rows):
        pdf.set_fill_color(245,250,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","",10)
        pdf.cell(100,8,f"  {lbl}",fill=True)
        pdf.set_font("Helvetica","B",10); pdf.cell(80,8,f"  {val}",fill=True,ln=True)
    pdf.ln(5)

    # Expenses
    section("Expense Breakdown")
    ww=[62,28,25,25,22,18]
    pdf.set_fill_color(20,30,20); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
    for hdr,w in zip(["  Name","Category","Spent","Budget","Over","Status"],ww):
        pdf.cell(w,7,hdr,fill=True)
    pdf.ln()
    for i,e in enumerate(st.session_state.expenses):
        budget=e.get("budget",e["amount"]); over=max(0,e["amount"]-budget)
        pdf.set_fill_color(245,250,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","",9)
        pdf.cell(62,7,f"  {e['name'][:24]}",fill=True)
        pdf.cell(28,7,e.get("category","Other")[:12],fill=True)
        pdf.cell(25,7,f"${e['amount']:,.0f}",fill=True)
        pdf.cell(25,7,f"${budget:,.0f}",fill=True)
        pdf.set_text_color(220,38,38) if over>0 else pdf.set_text_color(16,185,129)
        pdf.cell(22,7,f"${over:,.0f}",fill=True)
        pdf.cell(18,7,"OVER" if over>0 else "OK",fill=True); pdf.ln()
    pdf.set_fill_color(220,235,225); pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","B",9)
    pdf.cell(62,7,"  Subscriptions total",fill=True); pdf.cell(28,7,"Various",fill=True)
    pdf.cell(25,7,f"${tsub:,.0f}",fill=True); pdf.cell(25+22+18,7,"",fill=True); pdf.ln(); pdf.ln(4)

    # Goals
    if st.session_state.goals:
        section("Financial Goals")
        gw=[60,22,22,22,22,22,10]
        pdf.set_fill_color(20,30,20); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
        for hdr,w in zip(["  Goal","Priority","Target","Saved","Remaining","Progress","Mo"],gw):
            pdf.cell(w,7,hdr,fill=True)
        pdf.ln()
        inv=total_income*invest_pct/100
        for i,g in enumerate(st.session_state.goals):
            rem=max(0,g["amount"]-g["saved"]); pct=g["saved"]/g["amount"]*100 if g["amount"]>0 else 0
            mo=math.ceil(rem/inv) if inv>0 else 9999
            pdf.set_fill_color(245,250,246) if i%2==0 else pdf.set_fill_color(255,255,255)
            pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","",9)
            pdf.cell(60,7,f"  {g['name'][:26]}",fill=True); pdf.cell(22,7,g.get("priority","Med"),fill=True)
            pdf.cell(22,7,f"${g['amount']:,.0f}",fill=True); pdf.cell(22,7,f"${g['saved']:,.0f}",fill=True)
            pdf.cell(22,7,f"${rem:,.0f}",fill=True); pdf.cell(22,7,f"{pct:.0f}%",fill=True)
            pdf.cell(10,7,str(mo) if mo<999 else "—",fill=True); pdf.ln()
        pdf.ln(4)

    # Assets & Liabilities
    section("Net Worth Breakdown")
    pdf.set_font("Helvetica","B",10); pdf.set_text_color(30,30,30); pdf.cell(0,7,"Assets",ln=True)
    for i,a in enumerate(st.session_state.assets):
        pdf.set_fill_color(240,253,244) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","",9)
        pdf.cell(100,7,f"  {a['name']} ({a['type']})",fill=True)
        pdf.set_text_color(16,185,129); pdf.set_font("Helvetica","B",9)
        pdf.cell(80,7,f"+{fmt(a['value'])}",fill=True); pdf.ln()
    pdf.ln(2)
    pdf.set_font("Helvetica","B",10); pdf.set_text_color(30,30,30); pdf.cell(0,7,"Liabilities",ln=True)
    for i,l in enumerate(st.session_state.liabilities):
        pdf.set_fill_color(255,241,241) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","",9)
        pdf.cell(100,7,f"  {l['name']} ({l.get('rate',0):.1f}% p.a.)",fill=True)
        pdf.set_text_color(220,38,38); pdf.set_font("Helvetica","B",9)
        pdf.cell(80,7,f"-{fmt(l['balance'])}",fill=True); pdf.ln()
    pdf.ln(2)
    pdf.set_fill_color(220,235,225); pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","B",10)
    pdf.cell(100,8,"  Net Worth",fill=True)
    c = (16,185,129) if nw>=0 else (220,38,38)
    pdf.set_text_color(*c); pdf.cell(80,8,fmt(nw),fill=True); pdf.ln(); pdf.ln(5)

    # Footer
    pdf.set_font("Helvetica","I",8); pdf.set_text_color(150,150,150)
    pdf.cell(0,5,f"Seralung Finance Pro  |  Educational purposes only. Not financial advice.",ln=True)
    pdf.cell(0,5,"Always consult a qualified financial adviser before making investment decisions.",ln=True)
    return bytes(pdf.output())

# ═══════════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════════
ti = "#111111" if not T["dark"] else T["text"]
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Mono:wght@400;500&display=swap');
html,body,.stApp{{background:{T['bg']} !important;color:{T['text']} !important;font-family:'DM Sans',sans-serif;}}
*,*::before,*::after{{box-sizing:border-box;}}
p,span,div,label,li,td,th,[data-testid="stMarkdownContainer"] p{{color:{T['text']};}}
h1,h2,h3,h4{{color:{T['text']} !important;font-weight:600;}}
[data-testid="stSidebar"]{{background:{T['surface']} !important;border-right:1px solid {T['border']};}}
[data-testid="stSidebar"] *,[data-testid="stSidebar"] label{{color:{T['text']} !important;}}
[data-testid="metric-container"]{{background:{T['surface']} !important;border:1px solid {T['border']} !important;border-radius:14px !important;padding:1rem 1.2rem !important;}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] *{{color:{T['muted']} !important;font-size:0.7rem !important;text-transform:uppercase;letter-spacing:0.06em;}}
[data-testid="metric-container"] [data-testid="stMetricValue"] *{{color:{T['text']} !important;font-weight:700 !important;}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] *{{font-size:0.73rem !important;}}
[data-testid="stTabs"] [role="tab"]{{background:{T['surface2']};border:1px solid {T['border']};border-radius:8px;color:{T['muted']} !important;font-size:0.77rem;font-weight:500;padding:0.3rem 0.65rem;margin-right:3px;}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{{background:{T['accent']} !important;color:#fff !important;border-color:{T['accent']} !important;}}
[data-testid="stTabs"] [role="tablist"]{{border-bottom:1px solid {T['border']};padding-bottom:0.5rem;flex-wrap:wrap;gap:3px;}}
label,[data-testid="stWidgetLabel"]{{color:{T['text']} !important;}}
[data-testid="stNumberInput"] input,[data-testid="stTextInput"] input,textarea{{background:{T['surface2']} !important;border:1px solid {T['border']} !important;border-radius:8px !important;color:{ti} !important;}}
[data-testid="stSelectbox"]>div>div,[data-testid="stSelectbox"] span{{background:{T['surface2']} !important;border:1px solid {T['border']} !important;color:{T['text']} !important;border-radius:8px !important;}}
[data-testid="stCheckbox"] span{{color:{T['text']} !important;}}
[data-baseweb="slider"] [role="slider"]{{background:{T['accent']} !important;border-color:{T['accent']} !important;}}
.stButton>button{{background:{T['accent']} !important;border:none !important;border-radius:8px !important;color:#fff !important;font-weight:500 !important;transition:opacity 0.15s,transform 0.12s;}}
.stButton>button:hover{{opacity:0.85 !important;transform:translateY(-1px);}}
[data-testid="stExpander"]{{background:{T['surface']} !important;border:1px solid {T['border']} !important;border-radius:10px !important;}}
[data-testid="stExpander"] summary *{{color:{T['text']} !important;}}
[data-testid="stAlert"] div{{color:{T['text']} !important;}}
[data-testid="stFileUploader"]{{background:{T['surface2']} !important;border:2px dashed {T['border']} !important;border-radius:12px !important;}}
hr{{border-color:{T['border']} !important;}}
.sf-card{{background:{T['surface']};border:1px solid {T['border']};border-radius:16px;padding:1.2rem 1.4rem;margin-bottom:1rem;}}
.sf-card-title{{font-size:0.63rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{T['muted']};margin-bottom:0.85rem;}}
.sf-badge-green{{background:{hex_to_rgba(T['green'],0.18)};color:{T['green']};font-size:0.63rem;font-weight:700;padding:2px 7px;border-radius:5px;display:inline-block;}}
.sf-badge-red{{background:{hex_to_rgba(T['red'],0.18)};color:{T['red']};font-size:0.63rem;font-weight:700;padding:2px 7px;border-radius:5px;display:inline-block;}}
.sf-badge-amber{{background:{hex_to_rgba(T['amber'],0.18)};color:{T['amber']};font-size:0.63rem;font-weight:700;padding:2px 7px;border-radius:5px;display:inline-block;}}
.sf-badge-blue{{background:{hex_to_rgba(T['blue'],0.18)};color:{T['blue']};font-size:0.63rem;font-weight:700;padding:2px 7px;border-radius:5px;display:inline-block;}}
.sf-tip{{background:{hex_to_rgba(T['accent'],0.1)};border-left:3px solid {T['accent']};border-radius:0 10px 10px 0;padding:0.7rem 1rem;font-size:0.83rem;color:{T['text']};margin-bottom:1rem;line-height:1.5;}}
.sf-tip strong{{color:{T['accent']};}}
.sf-row{{display:flex;justify-content:space-between;padding:0.48rem 0;border-bottom:1px solid {T['border']};font-size:0.82rem;color:{T['text']};}}
.sf-row:last-child{{border-bottom:none;font-weight:600;}}
.sf-insight{{background:{T['surface2']};border-radius:10px;padding:0.85rem 1rem;margin-bottom:0.6rem;border:1px solid {T['border']};}}
@media(max-width:768px){{.block-container{{padding:0.7rem 0.7rem 2rem !important;}}[data-testid="stTabs"] [role="tab"]{{font-size:0.68rem;padding:0.25rem 0.45rem;}}}}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DERIVED VALUES
# ═══════════════════════════════════════════════════════════════════════════════
total_sub_monthly = sum(s["amount"] for s in st.session_state.subscriptions)
total_expenses    = sum(e["amount"] for e in st.session_state.expenses) + total_sub_monthly
total_assets      = sum(a["value"]  for a in st.session_state.assets)
total_liabilities = sum(l["balance"] for l in st.session_state.liabilities)
net_worth         = total_assets - total_liabilities
investable        = total_income * invest_pct / 100
left_over         = total_income - total_expenses
savings_rate      = left_over / total_income * 100 if total_income > 0 else 0
cash_assets       = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
em_months         = cash_assets / total_expenses if total_expenses > 0 else 0
health_score, health_details = calc_health_score()
nw_color          = T["green"] if net_worth >= 0 else T["red"]

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
hc1, hc2 = st.columns([3,1])
with hc1:
    st.markdown(f"<h1 style='margin:0;font-size:1.8rem;letter-spacing:-0.02em;color:{T['text']};'>💎 Seralung Finance Pro</h1>"
                f"<p style='color:{T['muted']};font-size:0.8rem;margin:2px 0 1rem;'>Complete personal finance command centre — AUD</p>", unsafe_allow_html=True)
with hc2:
    st.markdown(f"<div style='text-align:right;padding-top:0.5rem;'>"
                f"<div style='font-size:0.7rem;color:{T['muted']};'>{datetime.now().strftime('%A')}</div>"
                f"<div style='font-size:1rem;font-weight:600;color:{T['text']};'>{datetime.now().strftime('%d %b %Y')}</div></div>", unsafe_allow_html=True)
st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs(["🏠 Dashboard","💰 Budget","📈 Investments","🏦 Net Worth",
                "💳 Debt","🎯 Goals","🧾 Tax & FIRE","💡 Insights","📊 Reports","📤 Import"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 ▸ DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[0]:
    if   health_score >= 80: sc,sg,st_ = T["green"],"Excellent","You're crushing it! 🎉"
    elif health_score >= 65: sc,sg,st_ = T["blue"],"Good","On the right track"
    elif health_score >= 50: sc,sg,st_ = T["amber"],"Fair","Room to improve"
    elif health_score >= 35: sc,sg,st_ = T["red"],"Needs Work","Take action now"
    else:                    sc,sg,st_ = T["red"],"Critical","Urgent attention needed"

    r1,r2,r3,r4,r5 = st.columns([1.3,1,1,1,1])
    with r1:
        st.markdown(f"<div class='sf-card' style='border-color:{sc};text-align:center;padding:1.3rem;'>"
                    f"<div class='sf-card-title'>Financial Health</div>"
                    f"<div style='font-size:3.2rem;font-weight:800;color:{sc};line-height:1;'>{health_score}</div>"
                    f"<div style='font-size:0.82rem;font-weight:600;color:{sc};margin:5px 0 2px;'>{sg}</div>"
                    f"<div style='font-size:0.7rem;color:{T['muted']};'>{st_}</div>"
                    f"<div style='margin-top:10px;background:{T['surface2']};border-radius:8px;height:8px;'>"
                    f"<div style='width:{health_score}%;height:100%;background:{sc};border-radius:8px;'></div></div>"
                    f"</div>", unsafe_allow_html=True)
    with r2: st.metric("Net Worth",      fmt(net_worth),    "Positive ✓" if net_worth>=0 else "Negative ✗", delta_color="normal" if net_worth>=0 else "inverse")
    with r3: st.metric("Cash Flow",      fmt(left_over),    "Surplus"    if left_over>=0 else "Deficit",    delta_color="normal" if left_over>=0 else "inverse")
    with r4: st.metric("Savings Rate",   f"{savings_rate:.1f}%", f"Target 20%", delta_color="normal" if savings_rate>=20 else "inverse")
    with r5: st.metric("Emergency Fund", f"{em_months:.1f} mo",  "Safe ✓"  if em_months>=6 else "Build up", delta_color="normal" if em_months>=6 else "inverse")

    st.markdown("<div style='margin:1rem 0'></div>", unsafe_allow_html=True)
    dc1, dc2 = st.columns(2, gap="large")

    with dc1:
        st.markdown(f"<div class='sf-card'><div class='sf-card-title'>This Month — Budget Overview</div>", unsafe_allow_html=True)
        for lbl, actual, budget, col in [
            ("🏠 Needs", total_expenses*0.60, total_income*needs_pct/100, T["blue"]),
            ("🎉 Wants", total_expenses*0.40, total_income*wants_pct/100, T["accent"]),
            ("📈 Invest", investable,          total_income*invest_pct/100, T["green"]),
        ]:
            p = min(100, actual/budget*100) if budget > 0 else 0
            bc = "green" if p<=85 else "amber" if p<=100 else "red"
            br = T["red"] if p>100 else col
            st.markdown(f"<div style='margin-bottom:12px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:0.79rem;margin-bottom:4px;'>"
                        f"<span style='color:{T['text']}'>{lbl}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:6px;'>{fmt(actual)} / {fmt(budget)}</span>"
                        f"<span class='sf-badge-{bc}'>{'On track' if p<=85 else 'Near limit' if p<=100 else 'Over!'}</span></div></div>"
                        f"<div style='background:{T['surface2']};border-radius:5px;height:7px;'>"
                        f"<div style='width:{p:.1f}%;height:100%;background:{br};border-radius:5px;'></div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        fig_nw = go.Figure()
        fig_nw.add_trace(go.Bar(name="Assets",x=["Net Worth"],y=[total_assets],marker_color=T["green"],text=[fmt(total_assets)],textposition="auto",textfont=dict(color=T["text"],size=11)))
        fig_nw.add_trace(go.Bar(name="Liabilities",x=["Net Worth"],y=[-total_liabilities],marker_color=T["red"],text=[fmt(total_liabilities)],textposition="auto",textfont=dict(color=T["text"],size=11)))
        fig_nw.update_layout(**plot_layout("Net Worth Overview",200)); fig_nw.update_layout(barmode="relative")
        st.plotly_chart(fig_nw, use_container_width=True)

    with dc2:
        df_e = pd.DataFrame(st.session_state.expenses); df_e = df_e[df_e["amount"]>0]
        if not df_e.empty:
            cat_df = df_e.groupby("category")["amount"].sum().reset_index()
            n = len(cat_df); cc = (T["chart_colors"]*math.ceil(n/max(1,len(T["chart_colors"]))))[:n]
            fig_d = go.Figure(go.Pie(labels=cat_df["category"],values=cat_df["amount"],hole=0.58,
                marker=dict(colors=cc,line=dict(color=T["bg"],width=2)),textfont=dict(size=11,color=T["muted"]),
                hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>"))
            fig_d.update_layout(**plot_layout("Spending by Category",250))
            st.plotly_chart(fig_d, use_container_width=True)

        st.markdown(f"<div class='sf-card'><div class='sf-card-title'>Upcoming Bills</div>", unsafe_allow_html=True)
        today = date.today()
        for bill in sorted(st.session_state.bills, key=lambda b: b["due_day"]):
            days = bill["due_day"]-today.day
            if days < 0: days += 30
            badge = "green" if days>7 else "amber" if days>2 else "red"
            btext = f"in {days}d" if days>0 else "Today!"
            st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;"
                        f"padding:0.42rem 0;border-bottom:1px solid {T['border']};font-size:0.81rem;'>"
                        f"<span style='color:{T['text']}'>{bill['name']}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:8px;'>{fmt(bill['amount'])}</span>"
                        f"<span class='sf-badge-{badge}'>{btext}</span></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 ▸ BUDGET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[1]:
    bc1, bc2 = st.columns([1.1,1], gap="large")
    with bc1:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Monthly Expenses — Name · Spent · Budget · Category</div>", unsafe_allow_html=True)
        to_del = None
        for i, exp in enumerate(st.session_state.expenses):
            c1,c2,c3,c4,c5 = st.columns([2.5,1.5,1.5,1.5,0.5])
            with c1:
                nn=st.text_input(f"n{i}",value=exp["name"],label_visibility="collapsed",key=f"en_{i}")
                st.session_state.expenses[i]["name"]=nn
            with c2:
                na=st.number_input(f"a{i}",value=float(exp["amount"]),min_value=0.0,step=10.0,label_visibility="collapsed",key=f"ea_{i}",format="%.0f")
                st.session_state.expenses[i]["amount"]=na
            with c3:
                nb=st.number_input(f"b{i}",value=float(exp.get("budget",exp["amount"])),min_value=0.0,step=10.0,label_visibility="collapsed",key=f"eb_{i}",format="%.0f")
                st.session_state.expenses[i]["budget"]=nb
            with c4:
                idx_c=CATEGORIES.index(exp.get("category","Other")) if exp.get("category","Other") in CATEGORIES else 0
                nc=st.selectbox(f"c{i}",CATEGORIES,index=idx_c,label_visibility="collapsed",key=f"ec_{i}")
                st.session_state.expenses[i]["category"]=nc
            with c5:
                if st.button("✕",key=f"ed_{i}"): to_del=i
        if to_del is not None:
            st.session_state.expenses.pop(to_del); st.rerun()
        st.markdown("---")
        r1,r2,r3,r4 = st.columns([2.5,1.5,1.5,1.5])
        with r1: nn2=st.text_input("Name",placeholder="New expense",key="ne_n")
        with r2: na2=st.number_input("Spent ($)",min_value=0.0,step=10.0,key="ne_a",format="%.0f")
        with r3: nb2=st.number_input("Budget ($)",min_value=0.0,step=10.0,key="ne_b",format="%.0f")
        with r4: nc2=st.selectbox("Category",CATEGORIES,key="ne_c")
        if st.button("+ Add Expense",use_container_width=True):
            if nn2:
                st.session_state.expenses.append({"name":nn2,"amount":float(na2),"budget":float(nb2) if nb2>0 else float(na2),"category":nc2})
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='sf-card'><div class='sf-card-title'>Subscriptions — {fmt(total_sub_monthly)}/mo · {fmt(total_sub_monthly*12)}/yr</div>", unsafe_allow_html=True)
        del_sub=None
        for i,sub in enumerate(st.session_state.subscriptions):
            s1,s2,s3=st.columns([3,1.5,0.5])
            with s1:
                sn=st.text_input(f"sn{i}",value=sub["name"],label_visibility="collapsed",key=f"sn_{i}")
                st.session_state.subscriptions[i]["name"]=sn
            with s2:
                sa=st.number_input(f"sa{i}",value=float(sub["amount"]),min_value=0.0,step=0.5,label_visibility="collapsed",key=f"sa_{i}",format="%.2f")
                st.session_state.subscriptions[i]["amount"]=sa
            with s3:
                if st.button("✕",key=f"sd_{i}"): del_sub=i
        if del_sub is not None:
            st.session_state.subscriptions.pop(del_sub); st.rerun()
        st.markdown("---")
        ss1,ss2=st.columns([3,1.5])
        with ss1: snn=st.text_input("Service",placeholder="e.g. Disney+",key="ns_n")
        with ss2: sna=st.number_input("$/mo",min_value=0.0,step=0.5,key="ns_a",format="%.2f")
        if st.button("+ Add Subscription",use_container_width=True):
            if snn:
                st.session_state.subscriptions.append({"name":snn,"amount":float(sna),"cycle":"Monthly"}); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with bc2:
        df_e2=pd.DataFrame(st.session_state.expenses); df_e2=df_e2[df_e2["amount"]>0]
        if not df_e2.empty:
            cat_df2=df_e2.groupby("category").agg({"amount":"sum","budget":"sum"}).reset_index()
            fig_cat=go.Figure()
            fig_cat.add_trace(go.Bar(name="Spent",x=cat_df2["category"],y=cat_df2["amount"],marker_color=T["accent"],
                text=[fmt(v) for v in cat_df2["amount"]],textposition="outside",textfont=dict(color=T["text"],size=10)))
            fig_cat.add_trace(go.Bar(name="Budget",x=cat_df2["category"],y=cat_df2["budget"],
                marker_color=hex_to_rgba(T["green"],0.4),marker_line=dict(color=T["green"],width=1.5)))
            fig_cat.update_layout(**plot_layout("Spent vs Budget by Category",260)); fig_cat.update_layout(barmode="overlay")
            st.plotly_chart(fig_cat, use_container_width=True)

        st.markdown("<div class='sf-card'><div class='sf-card-title'>Per-Item Budget Tracker</div>", unsafe_allow_html=True)
        for exp in sorted(st.session_state.expenses,key=lambda e: e["amount"]/max(e.get("budget",1),1),reverse=True):
            budget=exp.get("budget",exp["amount"]); p=min(100,exp["amount"]/budget*100) if budget>0 else 0
            bc="red" if p>100 else "amber" if p>85 else "green"
            br=T["red"] if p>100 else T["amber"] if p>85 else T["green"]
            st.markdown(f"<div style='margin-bottom:9px;'><div style='display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:3px;'>"
                        f"<span style='color:{T['text']}'>{exp['name']}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:5px;'>{fmt(exp['amount'])} / {fmt(budget)}</span>"
                        f"<span class='sf-badge-{bc}'>{p:.0f}%</span></div></div>"
                        f"<div style='background:{T['surface2']};border-radius:4px;height:5px;'>"
                        f"<div style='width:{p:.1f}%;height:100%;background:{br};border-radius:4px;'></div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 ▸ INVESTMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[2]:
    st.markdown(f"<div class='sf-tip'>You have <strong>{fmt(investable)}/month</strong> to invest ({invest_pct}% of income) — <strong>{fmt(investable*12)}/year</strong>.</div>", unsafe_allow_html=True)
    inv1, inv2 = st.columns(2, gap="large")
    with inv1:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Investment Allocation</div>", unsafe_allow_html=True)
        em_pct  = pct_slider("🛡 Emergency top-up",  "em_pct",  30)
        idx_pct = pct_slider("📊 Index funds (ETFs)", "idx_pct", 40)
        stk_pct = pct_slider("📱 Individual stocks",  "stk_pct", 20)
        cry_pct = pct_slider("₿  Crypto",             "cry_pct", 10)
        if em_pct+idx_pct+stk_pct+cry_pct != 100:
            st.warning(f"Sum = {em_pct+idx_pct+stk_pct+cry_pct}% — adjust to 100%")
        st.markdown("</div>", unsafe_allow_html=True)
        labels=["Emergency","Index Funds","Stocks","Crypto"]; values=[em_pct,idx_pct,stk_pct,cry_pct]
        amounts=[investable*v/100 for v in values]
        fig_inv=go.Figure(go.Pie(labels=[f"{l} {fmt(a)}/mo" for l,a in zip(labels,amounts)],values=values,hole=0.55,
            marker=dict(colors=[T["blue"],T["green"],T["amber"],T["red"]],line=dict(color=T["bg"],width=2)),textfont=dict(size=11,color=T["muted"])))
        fig_inv.update_layout(**plot_layout("Monthly Allocation",240))
        st.plotly_chart(fig_inv, use_container_width=True)

        st.markdown("<div class='sf-card'><div class='sf-card-title'>Dollar-Cost Averaging Calculator</div>", unsafe_allow_html=True)
        dca_a=st.number_input("Monthly DCA ($)",min_value=0.0,value=float(investable*idx_pct/100),step=50.0,format="%.0f",key="dca_a")
        dca_y=st.slider("Period (years)",1,30,10,key="dca_y")
        dca_r=st.slider("Expected return (% p.a.)",1.0,20.0,7.0,0.5,key="dca_r")
        dca_inv=dca_a*12*dca_y; dca_f=0.0
        for _ in range(dca_y): dca_f=(dca_f+dca_a*12)*(1+dca_r/100)
        st.markdown(f"<div class='sf-row'><span>Total contributed</span><span style='color:{T['muted']}'>{fmt(dca_inv)}</span></div>"
                    f"<div class='sf-row'><span>Investment gain</span><span style='color:{T['green']}'>{fmt(dca_f-dca_inv)}</span></div>"
                    f"<div class='sf-row'><span>Final value</span><span style='color:{T['accent']};font-size:1.05rem;'>{fmt(dca_f)}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with inv2:
        yrs=list(range(21))
        def compound(r):
            v,res=0,[]
            for _ in yrs: res.append(round(v)); v=(v+investable*12)*(1+r)
            return res
        c_p=compound(0.04); m_p=compound(0.07); a_p=compound(0.12)
        fig_proj=go.Figure()
        for proj,lbl,col,dash in [(c_p,"Conservative (4%)",T["blue"],"dot"),(m_p,"Moderate (7%)",T["green"],"solid"),(a_p,"Aggressive (12%)",T["amber"],"dash")]:
            fig_proj.add_trace(go.Scatter(x=yrs,y=proj,name=lbl,mode="lines",line=dict(color=col,width=2,dash=dash),hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
        fig_proj.update_layout(**plot_layout("20-Year Growth Projection",300)); fig_proj.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_proj.update_xaxes(title_text="Year")
        st.plotly_chart(fig_proj, use_container_width=True)

        st.markdown("<div class='sf-card'><div class='sf-card-title'>Milestones</div>", unsafe_allow_html=True)
        for yr in [1,3,5,10,15,20]:
            st.markdown(f"<div class='sf-row'><span>Year {yr}</span>"
                        f"<span style='color:{T[\"blue\"]}'>{fmt(c_p[yr])}</span>"
                        f"<span style='color:{T[\"green\"]}'>{fmt(m_p[yr])}</span>"
                        f"<span style='color:{T[\"amber\"]}'>{fmt(a_p[yr])}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:0.63rem;color:{T['muted']};padding-top:6px;'><span></span><span>Conservative</span><span>Moderate</span><span>Aggressive</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        risk_profiles={
            "Conservative":{"desc":"Capital preservation, low volatility","alloc":{"Gov Bonds":40,"Blue-chips":30,"REITs":20,"Cash":10},"ret":(3,5),"scen":(-5,3,8)},
            "Moderate":    {"desc":"Balanced growth, equities + bonds",   "alloc":{"Index funds":50,"Growth stocks":25,"Bonds":15,"Crypto":10},"ret":(6,9),"scen":(-15,7,18)},
            "Aggressive":  {"desc":"Maximum growth, high volatility",      "alloc":{"Growth stocks":40,"Crypto":25,"Emerging":20,"Alts":15},"ret":(10,20),"scen":(-35,12,45)},
        }
        rr1,rr2,rr3=st.columns(3)
        for col_r,rname in zip([rr1,rr2,rr3],risk_profiles.keys()):
            rp_=risk_profiles[rname]; sel=st.session_state.risk_profile==rname
            with col_r:
                st.markdown(f"<div style='background:{T['surface2'] if sel else T['surface']};border:{'2px solid '+T['accent'] if sel else '1px solid '+T['border']};border-radius:10px;padding:0.8rem;margin-bottom:6px;'>"
                            f"<div style='font-weight:600;font-size:0.85rem;color:{T['text']};'>{rname}</div>"
                            f"<div style='font-size:0.7rem;color:{T['muted']};margin:4px 0;'>{rp_['desc']}</div>"
                            f"<div style='font-size:0.72rem;color:{T['accent']};font-weight:600;'>{rp_['ret'][0]}–{rp_['ret'][1]}% p.a.</div></div>", unsafe_allow_html=True)
                if st.button("Select",key=f"risk_{rname}",use_container_width=True):
                    st.session_state.risk_profile=rname; st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 ▸ NET WORTH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[3]:
    st.markdown(f"<div style='text-align:center;padding:1.5rem 0 1.2rem;'>"
                f"<div style='font-size:0.63rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{T['muted']};margin-bottom:6px;'>Total Net Worth</div>"
                f"<div style='font-size:3.8rem;font-weight:800;color:{nw_color};letter-spacing:-0.03em;'>{fmt(net_worth)}</div>"
                f"<div style='font-size:0.8rem;color:{T['muted']};margin-top:6px;'>Assets {fmt(total_assets)} — Liabilities {fmt(total_liabilities)}</div></div>", unsafe_allow_html=True)
    nw1,nw2=st.columns(2, gap="large")
    with nw1:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Assets — Name · Value · Type</div>", unsafe_allow_html=True)
        del_a=None
        for i,a in enumerate(st.session_state.assets):
            a1,a2,a3,a4=st.columns([2.5,1.5,1.5,0.5])
            with a1:
                an=st.text_input(f"ann{i}",value=a["name"],label_visibility="collapsed",key=f"an_{i}")
                st.session_state.assets[i]["name"]=an
            with a2:
                av=st.number_input(f"avv{i}",value=float(a["value"]),min_value=0.0,step=100.0,label_visibility="collapsed",key=f"av_{i}",format="%.0f")
                st.session_state.assets[i]["value"]=av
            with a3:
                at_i=ASSET_TYPES.index(a["type"]) if a["type"] in ASSET_TYPES else 0
                at_=st.selectbox(f"att{i}",ASSET_TYPES,index=at_i,label_visibility="collapsed",key=f"at_{i}")
                st.session_state.assets[i]["type"]=at_
            with a4:
                if st.button("✕",key=f"ad_{i}"): del_a=i
        if del_a is not None: st.session_state.assets.pop(del_a); st.rerun()
        st.markdown("---")
        na1,na2,na3=st.columns([2.5,1.5,1.5])
        with na1: new_an=st.text_input("Asset",placeholder="e.g. Shares",key="naa_n")
        with na2: new_av=st.number_input("Value ($)",min_value=0.0,step=100.0,key="naa_v",format="%.0f")
        with na3: new_at=st.selectbox("Type",ASSET_TYPES,key="naa_t")
        if st.button("+ Add Asset",use_container_width=True):
            if new_an: st.session_state.assets.append({"name":new_an,"value":float(new_av),"type":new_at}); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        df_a=pd.DataFrame(st.session_state.assets); df_a=df_a[df_a["value"]>0]
        if not df_a.empty:
            at_df=df_a.groupby("type")["value"].sum().reset_index()
            n=len(at_df); cc=(T["chart_colors"]*math.ceil(n/max(1,len(T["chart_colors"]))))[:n]
            fig_a=go.Figure(go.Pie(labels=at_df["type"],values=at_df["value"],hole=0.55,marker=dict(colors=cc,line=dict(color=T["bg"],width=2)),textfont=dict(size=11,color=T["muted"]),hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>"))
            fig_a.update_layout(**plot_layout("Asset Allocation",240)); st.plotly_chart(fig_a, use_container_width=True)

    with nw2:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Liabilities — Name · Balance · Rate · Type</div>", unsafe_allow_html=True)
        del_l=None
        for i,l in enumerate(st.session_state.liabilities):
            l1,l2,l3,l4,l5=st.columns([2,1.5,1,1.5,0.5])
            with l1:
                ln=st.text_input(f"lnn{i}",value=l["name"],label_visibility="collapsed",key=f"ln_{i}")
                st.session_state.liabilities[i]["name"]=ln
            with l2:
                lb=st.number_input(f"lbb{i}",value=float(l["balance"]),min_value=0.0,step=100.0,label_visibility="collapsed",key=f"lb_{i}",format="%.0f")
                st.session_state.liabilities[i]["balance"]=lb
            with l3:
                lr=st.number_input(f"lrr{i}",value=float(l.get("rate",5.0)),min_value=0.0,max_value=99.0,step=0.1,label_visibility="collapsed",key=f"lr_{i}",format="%.1f")
                st.session_state.liabilities[i]["rate"]=lr
            with l4:
                lt_i=LIAB_TYPES.index(l["type"]) if l["type"] in LIAB_TYPES else 0
                lt_=st.selectbox(f"ltt{i}",LIAB_TYPES,index=lt_i,label_visibility="collapsed",key=f"lt_{i}")
                st.session_state.liabilities[i]["type"]=lt_
            with l5:
                if st.button("✕",key=f"ld_{i}"): del_l=i
        if del_l is not None: st.session_state.liabilities.pop(del_l); st.rerun()
        st.markdown("---")
        nl1,nl2,nl3,nl4=st.columns([2,1.5,1,1.5])
        with nl1: new_ln=st.text_input("Liability",placeholder="e.g. Home Loan",key="nll_n")
        with nl2: new_lb=st.number_input("Balance ($)",min_value=0.0,step=100.0,key="nll_b",format="%.0f")
        with nl3: new_lr=st.number_input("Rate (%)",min_value=0.0,max_value=99.0,step=0.1,key="nll_r",format="%.1f")
        with nl4: new_lt=st.selectbox("Type",LIAB_TYPES,key="nll_t")
        if st.button("+ Add Liability",use_container_width=True):
            if new_ln: st.session_state.liabilities.append({"name":new_ln,"balance":float(new_lb),"rate":float(new_lr),"type":new_lt,"min_payment":0.0}); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        if st.session_state.assets or st.session_state.liabilities:
            wf_x=[a["name"] for a in st.session_state.assets]+[l["name"] for l in st.session_state.liabilities]+["Net Worth"]
            wf_m=["relative"]*len(st.session_state.assets)+["relative"]*len(st.session_state.liabilities)+["total"]
            wf_y=[a["value"] for a in st.session_state.assets]+[-l["balance"] for l in st.session_state.liabilities]+[0]
            fig_wf=go.Figure(go.Waterfall(x=wf_x,measure=wf_m,y=wf_y,connector=dict(line=dict(color=T["border"],width=0.5)),
                increasing=dict(marker=dict(color=T["green"])),decreasing=dict(marker=dict(color=T["red"])),totals=dict(marker=dict(color=nw_color)),
                texttemplate="%{y:$,.0f}",textposition="outside",textfont=dict(color=T["text"],size=9)))
            fig_wf.update_layout(**plot_layout("Net Worth Waterfall",280)); st.plotly_chart(fig_wf, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5 ▸ DEBT TRACKER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[4]:
    if not st.session_state.liabilities:
        st.info("No liabilities yet. Add them in the Net Worth tab.")
    else:
        tdb=sum(l["balance"] for l in st.session_state.liabilities)
        tmp=sum(l.get("min_payment",0) for l in st.session_state.liabilities)
        avg_r=sum(l["rate"]*l["balance"] for l in st.session_state.liabilities)/tdb if tdb else 0
        ann_i=sum(l["balance"]*l.get("rate",0)/100 for l in st.session_state.liabilities)
        d1,d2,d3,d4=st.columns(4)
        d1.metric("Total Debt",fmt(tdb)); d2.metric("Avg Rate",f"{avg_r:.1f}%")
        d3.metric("Min Payments",fmt(tmp)+"/mo"); d4.metric("Annual Interest",fmt(ann_i),delta=f"{fmt(ann_i/12)}/mo",delta_color="inverse")
        st.markdown("<div style='margin:1rem 0'></div>", unsafe_allow_html=True)
        dc1,dc2=st.columns([1.2,1],gap="large")
        with dc1:
            extra=st.number_input("Extra monthly payment ($)",min_value=0.0,value=200.0,step=50.0,format="%.0f",key="extra_pay")
            strat=st.radio("Payoff strategy",["🏔 Avalanche — highest rate first (saves most interest)","⛄ Snowball — smallest balance first (best motivation)"],key="strat")
            use_av="Avalanche" in strat
            st.markdown("<div class='sf-card'><div class='sf-card-title'>Your Debts (sorted by strategy)</div>", unsafe_allow_html=True)
            debts_s=sorted([dict(l) for l in st.session_state.liabilities if l["balance"]>0],key=lambda d: -d["rate"] if use_av else d["balance"])
            for debt in debts_s:
                mi=debt["balance"]*debt.get("rate",0)/100/12
                rb="red" if debt.get("rate",0)>10 else "amber" if debt.get("rate",0)>5 else "green"
                st.markdown(f"<div class='sf-insight'><div style='display:flex;justify-content:space-between;align-items:center;'>"
                            f"<div><div style='font-weight:600;font-size:0.85rem;color:{T['text']};'>{debt['name']}</div>"
                            f"<div style='font-size:0.7rem;color:{T['muted']};margin-top:2px;'><span class='sf-badge-{rb}'>{debt.get('rate',0):.1f}% p.a.</span>"
                            f" &nbsp; Interest: {fmt(mi)}/mo</div></div>"
                            f"<div style='text-align:right;font-size:1rem;font-weight:700;color:{T['text']};'>{fmt(debt['balance'])}</div></div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            def simulate_payoff(debts, extra_pay, av=True):
                ds=[dict(d) for d in debts if d["balance"]>0]
                for d in ds:
                    if not d.get("min_payment"): d["min_payment"]=max(d["balance"]*0.03,50)
                mo,ti,hist=0,0,[]
                while any(d["balance"]>0 for d in ds) and mo<360:
                    mo+=1
                    for d in ds:
                        if d["balance"]>0:
                            i=d["balance"]*d.get("rate",0)/100/12; d["balance"]+=i; ti+=i
                    for d in ds:
                        if d["balance"]>0:
                            pay=min(d["balance"],d.get("min_payment",50)); d["balance"]=max(0,d["balance"]-pay)
                    active=[d for d in ds if d["balance"]>0]
                    if active:
                        focus=min(active,key=lambda x: -x["rate"] if av else x["balance"])
                        focus["balance"]=max(0,focus["balance"]-extra_pay)
                    hist.append({"month":mo,"total":sum(d["balance"] for d in ds)})
                    if all(d["balance"]<=0 for d in ds): break
                return mo,ti,hist

            av_mo,av_int,av_hist=simulate_payoff(st.session_state.liabilities,extra,True)
            sb_mo,sb_int,sb_hist=simulate_payoff(st.session_state.liabilities,extra,False)
            st.markdown("<div class='sf-card'><div class='sf-card-title'>Strategy Comparison</div>", unsafe_allow_html=True)
            for nm,mo,interest,col_ in [("🏔 Avalanche",av_mo,av_int,T["green"]),("⛄ Snowball",sb_mo,sb_int,T["blue"])]:
                st.markdown(f"<div class='sf-row'><span style='color:{col_};font-weight:600;'>{nm}</span>"
                            f"<span>{mo} months ({mo/12:.1f} yrs)</span><span style='color:{T[\"red\"]};'>Int: {fmt(interest)}</span></div>", unsafe_allow_html=True)
            diff=abs(sb_int-av_int)
            if diff>0: st.markdown(f"<div style='margin-top:8px;font-size:0.81rem;color:{T['green']};'>Avalanche saves <strong>{fmt(diff)}</strong> in interest</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with dc2:
            if av_hist and sb_hist:
                fig_p=go.Figure()
                fig_p.add_trace(go.Scatter(x=[h["month"] for h in av_hist],y=[h["total"] for h in av_hist],name="Avalanche",mode="lines",line=dict(color=T["green"],width=2),hovertemplate="Month %{x}<br>$%{y:,.0f}<extra></extra>"))
                fig_p.add_trace(go.Scatter(x=[h["month"] for h in sb_hist],y=[h["total"] for h in sb_hist],name="Snowball",mode="lines",line=dict(color=T["blue"],width=2,dash="dash"),hovertemplate="Month %{x}<br>$%{y:,.0f}<extra></extra>"))
                fig_p.update_layout(**plot_layout("Debt Payoff Timeline",280)); fig_p.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_p.update_xaxes(title_text="Month")
                st.plotly_chart(fig_p, use_container_width=True)
            fig_m=go.Figure()
            cc2=T["chart_colors"]
            for i,l in enumerate(st.session_state.liabilities):
                if l["balance"]>0:
                    fig_m.add_trace(go.Scatter(x=[l["balance"]],y=[l.get("rate",0)],mode="markers+text",name=l["name"],text=[l["name"]],textposition="top center",textfont=dict(size=10,color=T["muted"]),marker=dict(size=22,color=cc2[i%len(cc2)],opacity=0.85)))
            fig_m.update_layout(**plot_layout("Priority: Balance vs Interest Rate",240)); fig_m.update_xaxes(title_text="Balance ($)",tickprefix="$",tickformat=",.0f"); fig_m.update_yaxes(title_text="Rate (%)",ticksuffix="%")
            st.plotly_chart(fig_m, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 6 ▸ GOALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[5]:
    g1,g2,g3,g4=st.columns(4)
    g1.metric("Goals",len(st.session_state.goals)); g2.metric("Total Target",fmt(sum(g["amount"] for g in st.session_state.goals)))
    g3.metric("Total Saved",fmt(sum(g["saved"] for g in st.session_state.goals))); g4.metric("Investable",fmt(investable)+"/mo")
    st.markdown("<div style='margin:1rem 0'></div>", unsafe_allow_html=True)
    with st.expander("+ Add New Goal",expanded=not bool(st.session_state.goals)):
        gc1,gc2,gc3,gc4=st.columns([2,1,1,1])
        with gc1: gname=st.text_input("Goal",placeholder="e.g. First Home Deposit")
        with gc2: gtgt=st.number_input("Target ($)",min_value=0.0,step=1000.0,format="%.0f",key="g_tgt")
        with gc3: gsaved=st.number_input("Saved ($)",min_value=0.0,step=100.0,format="%.0f",key="g_sav")
        with gc4: gprio=st.selectbox("Priority",["High","Medium","Low"])
        if st.button("Add Goal",use_container_width=True):
            if gname and gtgt>0: st.session_state.goals.append({"name":gname,"amount":gtgt,"saved":gsaved,"priority":gprio}); st.rerun()
    for i,g in enumerate(st.session_state.goals):
        rem=max(0,g["amount"]-g["saved"]); pct_g=min(100,round(g["saved"]/g["amount"]*100)) if g["amount"]>0 else 0
        mo=math.ceil(rem/investable) if investable>0 else 9999; yr_g=mo/12
        pc=T["red"] if g["priority"]=="High" else T["amber"] if g["priority"]=="Medium" else T["blue"]
        pb="red" if g["priority"]=="High" else "amber" if g["priority"]=="Medium" else "blue"
        gc_,gd_=st.columns([11,1])
        with gc_:
            st.markdown(f"<div class='sf-card'><div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>"
                        f"<div><span style='font-weight:700;font-size:0.95rem;color:{T['text']};'>{g['name']}</span>"
                        f"<span class='sf-badge-{pb}' style='margin-left:8px;'>{g['priority']}</span></div>"
                        f"<span style='font-size:0.78rem;color:{T['muted']};'>Target: {fmt(g['amount'])}</span></div>"
                        f"<div style='font-size:0.78rem;color:{T['muted']};margin-bottom:10px;'>{fmt(g['saved'])} saved · {fmt(rem)} remaining · "
                        f"<span style='color:{T[\"accent\"]};'>{yr_g:.1f} yrs ({mo} mo) at current rate</span></div>"
                        f"<div style='background:{T['surface2']};border-radius:6px;height:9px;margin-bottom:4px;'>"
                        f"<div style='width:{pct_g}%;height:100%;background:{pc};border-radius:6px;'></div></div>"
                        f"<div style='font-size:0.7rem;color:{T['muted']};'>{pct_g}% complete</div></div>", unsafe_allow_html=True)
            new_s=st.number_input(f"Update saved ($) for goal {i}",value=float(g["saved"]),min_value=0.0,step=100.0,key=f"g_upd_{i}",format="%.0f",label_visibility="collapsed")
            if new_s!=g["saved"]: st.session_state.goals[i]["saved"]=new_s; st.rerun()
        with gd_:
            if st.button("✕",key=f"gd_{i}"): st.session_state.goals.pop(i); st.rerun()
    if st.session_state.goals and investable>0:
        gl=[g["name"] for g in st.session_state.goals]
        gm=[math.ceil(max(0,g["amount"]-g["saved"])/investable) for g in st.session_state.goals]
        gcc_=[T["red"] if g["priority"]=="High" else T["amber"] if g["priority"]=="Medium" else T["blue"] for g in st.session_state.goals]
        fig_g=go.Figure(go.Bar(x=gm,y=gl,orientation="h",marker_color=gcc_,text=[f"{m} months" for m in gm],textposition="outside",textfont=dict(color=T["text"],size=11)))
        fig_g.update_layout(**plot_layout("Months to Each Goal",max(180,len(gl)*65))); fig_g.update_xaxes(title_text="Months")
        st.plotly_chart(fig_g, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 7 ▸ TAX & FIRE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[6]:
    tc1,tc2=st.columns(2, gap="large")
    with tc1:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Australian Tax Estimator — FY2024-25</div>", unsafe_allow_html=True)
        gross=st.number_input("Annual gross income ($)",min_value=0.0,value=float(primary_income*12),step=1000.0,format="%.0f",key="tax_g")
        inc_med=st.checkbox("Medicare levy (2%)",value=True)
        inc_lito=st.checkbox("Apply LITO offset",value=True)
        priv_h=st.checkbox("Private health insurance (avoids MLS)",value=False)
        tax_r=calc_tax(gross); med=gross*0.02 if inc_med else 0
        mls=gross*0.01 if (not priv_h and gross>93000 and inc_med) else 0
        lito=calc_lito(gross) if inc_lito else 0
        ttax=max(0,tax_r+med+mls-lito); net_ann=gross-ttax
        eff_r=ttax/gross*100 if gross>0 else 0
        for lbl,val,col_,bold in [("Gross income",fmt(gross),T["text"],False),("Income tax (gross)",f"−{fmt(tax_r)}",T["red"],False),
                                   ("Medicare levy",f"−{fmt(med)}",T["amber"],False),("MLS surcharge",f"−{fmt(mls)}",T["red"],mls>0),
                                   ("LITO offset",f"+{fmt(lito)}",T["green"],False),("Total tax payable",f"−{fmt(ttax)}",T["red"],True),
                                   ("Net income (annual)",fmt(net_ann),T["accent"],True),("Net income (monthly)",fmt(net_ann/12),T["accent"],True),
                                   ("Effective tax rate",f"{eff_r:.1f}%",T["amber"],True)]:
            fw="font-weight:600;" if bold else ""
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid {T['border']};font-size:0.82rem;{fw}'>"
                        f"<span style='color:{T['muted']}'>{lbl}</span><span style='color:{col_}'>{val}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        brackets=[("$0–$18.2k",0,0),("$18k–$45k",18200,19),("$45k–$135k",45000,32.5),("$135k–$190k",135000,37),("$190k+",190000,45)]
        fig_br=go.Figure(go.Bar(x=[b[0] for b in brackets],y=[b[2] for b in brackets],
            marker_color=[T["accent"] if gross>b[1] else hex_to_rgba(T["border"],0.5) for b in brackets],
            text=[f"{b[2]}%" for b in brackets],textposition="outside",textfont=dict(color=T["text"],size=11)))
        fig_br.update_layout(**plot_layout("Marginal Tax Brackets",200)); fig_br.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig_br, use_container_width=True)

    with tc2:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>FIRE Calculator — Financial Independence</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.75rem;color:{T['muted']};margin-bottom:1rem;line-height:1.5;'>Save 25× annual expenses (4% rule). Lean FIRE = 20×, Fat FIRE = 33×.</div>", unsafe_allow_html=True)
        ann_exp=st.number_input("Annual living expenses ($)",min_value=0.0,value=float(total_expenses*12),step=500.0,format="%.0f",key="f_exp")
        cur_port=st.number_input("Current investable portfolio ($)",min_value=0.0,value=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings"])),step=1000.0,format="%.0f",key="f_port")
        fire_r=st.slider("Expected growth (% p.a.)",1.0,15.0,7.0,0.5,key="f_rate")
        lean_f=ann_exp*20; fire_t=ann_exp*25; fat_f=ann_exp*33
        for lbl_,tgt,col_ in [("🌿 Lean FIRE (5% withdrawal)",lean_f,T["blue"]),("🔥 FIRE (4% withdrawal)",fire_t,T["accent"]),("💎 Fat FIRE (3% withdrawal)",fat_f,T["amber"])]:
            p=min(100,cur_port/tgt*100) if tgt>0 else 0
            st.markdown(f"<div style='margin-bottom:12px;'><div style='display:flex;justify-content:space-between;font-size:0.79rem;margin-bottom:4px;'>"
                        f"<span style='color:{T['text']}'>{lbl_}</span><span style='color:{T['muted']}'>{fmt(cur_port)} / {fmt(tgt)}</span></div>"
                        f"<div style='background:{T['surface2']};border-radius:5px;height:7px;'>"
                        f"<div style='width:{p:.1f}%;height:100%;background:{col_};border-radius:5px;'></div></div>"
                        f"<div style='font-size:0.7rem;color:{T['muted']};margin-top:2px;'>{p:.0f}% there</div></div>", unsafe_allow_html=True)
        fi_r=cur_port/fire_t*100 if fire_t>0 else 0
        st.markdown(f"<div style='text-align:center;margin:0.5rem 0;'><span style='font-size:2.2rem;font-weight:800;color:{T['accent']};'>{fi_r:.0f}%</span><div style='font-size:0.7rem;color:{T['muted']};'>FI Ratio</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if investable>0 and fire_t>0:
            yrs_f,vals_f=[],[]; v,yr_hit=cur_port,None
            for yr in range(51):
                yrs_f.append(yr); vals_f.append(round(v))
                if v>=fire_t and yr_hit is None: yr_hit=yr
                v=(v+investable*12)*(1+fire_r/100)
            fig_fire=go.Figure()
            fig_fire.add_trace(go.Scatter(x=yrs_f,y=vals_f,name="Portfolio",mode="lines",line=dict(color=T["green"],width=2),fill="tozeroy",fillcolor=hex_to_rgba(T["green"],0.1),hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
            for lbl_,tgt,col_ in [("Lean",lean_f,T["blue"]),("FIRE",fire_t,T["amber"]),("Fat",fat_f,T["red"])]:
                fig_fire.add_hline(y=tgt,line_dash="dot",line_color=col_,annotation_text=lbl_,annotation_font_color=col_)
            fig_fire.update_layout(**plot_layout("Path to Financial Independence",270)); fig_fire.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_fire.update_xaxes(title_text="Years from now")
            st.plotly_chart(fig_fire, use_container_width=True)
            if yr_hit:
                st.markdown(f"<div class='sf-tip'>FIRE in approximately <strong>{yr_hit} years</strong>. Monthly withdrawal: <strong>{fmt(fire_t*0.04/12)}</strong> (4% rule).</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 8 ▸ INSIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[7]:
    grade=["Critical","Needs Work","Fair","Good","Excellent"][min(4,health_score//20)]
    st.markdown(f"<div class='sf-tip'>Health score <strong>{health_score}/100 — {grade}</strong>. Personalised insights and recommendations below.</div>", unsafe_allow_html=True)
    ins1,ins2=st.columns(2, gap="large")
    with ins1:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Health Score Breakdown</div>", unsafe_allow_html=True)
        for k,d in health_details.items():
            p=d["score"]/d["max"]*100; bc="green" if p>=70 else "amber" if p>=40 else "red"; br=T[bc]
            st.markdown(f"<div style='margin-bottom:12px;'><div style='display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:4px;'>"
                        f"<span style='color:{T['text']}'>{d['label']}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:5px;'>{d['value']}</span><span class='sf-badge-{bc}'>{d['score']:.0f}/{d['max']}pts</span></div></div>"
                        f"<div style='background:{T['surface2']};border-radius:5px;height:6px;'>"
                        f"<div style='width:{p:.1f}%;height:100%;background:{br};border-radius:5px;'></div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        nd_=sum(l["balance"] for l in st.session_state.liabilities if l["type"]!="HECS")
        dti_=nd_/(total_income*12)*100 if total_income>0 else 0
        hpct=sum(e["amount"] for e in st.session_state.expenses if e["category"]=="Housing")/total_income*100 if total_income>0 else 0
        spct=total_sub_monthly/total_income*100 if total_income>0 else 0
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Key Financial Ratios</div>", unsafe_allow_html=True)
        for name,val,good,bench in [("Savings rate",f"{savings_rate:.1f}%",savings_rate>=20,"Target ≥20%"),
                                     ("Debt-to-income",f"{dti_:.0f}%",dti_<=36,"Healthy ≤36%"),
                                     ("Housing % income",f"{hpct:.0f}%",hpct<=30,"Ideal ≤30%"),
                                     ("Emergency fund",f"{em_months:.1f} mo",em_months>=6,"Safe = 6+ months"),
                                     ("Subscription spend",f"{spct:.1f}%",spct<=5,"Ideal ≤5% income")]:
            col_r=T["green"] if good else T["red"]; badge="green" if good else "red"
            st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0;border-bottom:1px solid {T['border']};'>"
                        f"<div><div style='font-size:0.82rem;color:{T['text']};'>{name}</div><div style='font-size:0.68rem;color:{T['muted']};'>{bench}</div></div>"
                        f"<div style='text-align:right;'><div style='font-size:1rem;font-weight:700;color:{col_r};'>{val}</div>"
                        f"<span class='sf-badge-{badge}'>{'✓' if good else '⚠'}</span></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with ins2:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Smart Recommendations</div>", unsafe_allow_html=True)
        recs=[]
        if em_months<3: recs.append(("🚨","Critical","red",f"Build emergency fund urgently — you have {em_months:.1f} months. Pause investing until 3 months is reached."))
        elif em_months<6: recs.append(("⚠️","Build up","amber",f"Emergency fund is {em_months:.1f} months. Target 6 months ({fmt(total_expenses*6)})."))
        else: recs.append(("✅","Excellent","green",f"Emergency fund covers {em_months:.1f} months. You are protected."))
        if savings_rate<10: recs.append(("📉","Urgent","red",f"Savings rate of {savings_rate:.1f}% is very low. Target 20%. Find {fmt(total_income*0.1)}/mo in cuts."))
        elif savings_rate<20: recs.append(("💡","Improve","amber",f"Savings rate is {savings_rate:.1f}%. Target 20% — you need {fmt(total_income*0.2-left_over)}/mo more."))
        else: recs.append(("🌟","Great","green",f"Savings rate {savings_rate:.1f}% beats the 20% benchmark. Keep compounding!"))
        hi_debt=[l for l in st.session_state.liabilities if l.get("rate",0)>10]
        if hi_debt: recs.append(("💳","Action","red",f"{fmt(sum(d['balance'] for d in hi_debt))} in high-interest debt (>10%). Prioritise payoff — it costs more than investments earn."))
        if spct>5: recs.append(("📱","Review","amber",f"Subscriptions are {spct:.1f}% of income ({fmt(total_sub_monthly)}/mo, {fmt(total_sub_monthly*12)}/yr). Audit unused services."))
        if not st.session_state.goals: recs.append(("🎯","Setup","amber","No financial goals set. Goals 3× your savings consistency. Add your first goal now!"))
        over_exp=[e for e in st.session_state.expenses if e["amount"]>e.get("budget",e["amount"])]
        if over_exp: recs.append(("🔴","Over budget","red",f"{len(over_exp)} expense(s) over budget: {', '.join(e['name'] for e in over_exp[:3])}. Review spending."))
        for icon,lbl,badge,text in recs[:7]:
            st.markdown(f"<div class='sf-insight'><div style='display:flex;align-items:flex-start;gap:8px;'>"
                        f"<span style='font-size:1.1rem;'>{icon}</span>"
                        f"<div><span class='sf-badge-{badge}' style='margin-bottom:5px;display:inline-block;'>{lbl}</span>"
                        f"<div style='font-size:0.81rem;color:{T['text']};line-height:1.5;margin-top:4px;'>{text}</div></div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        cat_t={};
        for e in st.session_state.expenses: cat_t[e.get("category","Other")]=cat_t.get(e.get("category","Other"),0)+e["amount"]
        if cat_t:
            cats=list(cat_t.keys()); vals=[cat_t[c] for c in cats]
            fig_r=go.Figure(go.Scatterpolar(r=vals+[vals[0]],theta=cats+[cats[0]],fill="toself",
                fillcolor=hex_to_rgba(T["accent"],0.15),line=dict(color=T["accent"],width=2),name="Spending"))
            fig_r.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                polar=dict(bgcolor="rgba(0,0,0,0)",radialaxis=dict(visible=True,color=T["muted"],gridcolor=T["border"]),angularaxis=dict(color=T["muted"],gridcolor=T["border"])),
                font=dict(family="DM Sans,sans-serif",color=T["muted"],size=11),height=260,margin=dict(l=40,r=40,t=30,b=10),
                title=dict(text="Spending Radar",font=dict(color=T["text"],size=13)),legend=dict(bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig_r, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 9 ▸ REPORTS  (CSV + PDF export)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[8]:
    st.markdown(f"<div class='sf-tip'>Export your full financial data as <strong>CSV</strong> (Excel-compatible) or <strong>PDF</strong> report. All data stays local — nothing leaves your browser.</div>", unsafe_allow_html=True)
    rp1, rp2 = st.columns(2, gap="large")

    with rp1:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>📄 CSV Export</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.83rem;color:{T['muted']};margin-bottom:1rem;line-height:1.6;'>CSV exports open in Excel, Google Sheets, or Numbers. Includes expenses, subscriptions, assets, liabilities, goals, transactions, and summary metrics.</div>", unsafe_allow_html=True)
        period_csv = st.selectbox("Report period", ["Monthly","Weekly","Quarterly","Annual"], key="csv_period")
        now_str = datetime.now().strftime("%Y-%m-%d")
        csv_bytes = generate_csv_report(period_csv)
        st.download_button(
            label=f"⬇ Download {period_csv} CSV",
            data=csv_bytes,
            file_name=f"seralung_finance_{period_csv.lower()}_{now_str}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.markdown("---", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.78rem;color:{T['muted']};'>What's included:</div>", unsafe_allow_html=True)
        for item in ["Summary metrics & health score","All expenses with budget vs actual","Subscriptions & annual cost","Assets & liabilities","Goals with progress","Imported bank transactions (if any)"]:
            st.markdown(f"<div style='font-size:0.78rem;color:{T['text']};padding:3px 0;'>✓ &nbsp; {item}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with rp2:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>📑 PDF Report</div>", unsafe_allow_html=True)
        if PDF_AVAILABLE:
            st.markdown(f"<div style='font-size:0.83rem;color:{T['muted']};margin-bottom:1rem;line-height:1.6;'>Professional PDF report with colour-coded tables, health score, expenses, goals, net worth breakdown, and footer disclaimer.</div>", unsafe_allow_html=True)
            period_pdf = st.selectbox("Report period", ["Monthly","Weekly","Quarterly","Annual"], key="pdf_period")
            pdf_bytes = generate_pdf_report(period_pdf)
            if pdf_bytes:
                st.download_button(
                    label=f"⬇ Download {period_pdf} PDF",
                    data=pdf_bytes,
                    file_name=f"seralung_finance_{period_pdf.lower()}_{now_str}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            st.markdown("---")
            for item in ["Financial health score","Monthly summary table","Expense breakdown (colour-coded)","Goals progress","Net worth waterfall","Assets & liabilities detail"]:
                st.markdown(f"<div style='font-size:0.78rem;color:{T['text']};padding:3px 0;'>✓ &nbsp; {item}</div>", unsafe_allow_html=True)
        else:
            st.warning("PDF export requires **fpdf2**. Install it with:")
            st.code("pip install fpdf2", language="bash")
            st.markdown(f"<div style='font-size:0.83rem;color:{T['muted']};margin-top:0.5rem;'>After installing, restart Streamlit and PDF export will be available.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Report preview
    st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sf-card'><div class='sf-card-title'>Report Preview — Current Month Summary</div>", unsafe_allow_html=True)
    hs_,_=calc_health_score()
    tsub_=sum(s["amount"] for s in st.session_state.subscriptions)
    texp_=sum(e["amount"] for e in st.session_state.expenses)+tsub_
    sr_=(total_income-texp_)/total_income*100 if total_income>0 else 0
    nw_=sum(a["value"] for a in st.session_state.assets)-sum(l["balance"] for l in st.session_state.liabilities)
    p1,p2,p3,p4=st.columns(4)
    p1.metric("Health Score",  f"{hs_}/100"); p2.metric("Net Cash Flow", fmt(total_income-texp_))
    p3.metric("Savings Rate",  f"{sr_:.1f}%"); p4.metric("Net Worth",    fmt(nw_))
    if st.session_state.expenses:
        df_prev=pd.DataFrame(st.session_state.expenses)[["name","category","amount"]].copy()
        df_prev.columns=["Expense","Category","Amount ($)"]
        df_prev["Amount ($)"]=df_prev["Amount ($)"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(df_prev, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 10 ▸ IMPORT DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[9]:
    st.markdown(f"<div class='sf-tip'>Upload your bank statement CSV or a previously exported Seralung Finance JSON to auto-populate your data.</div>", unsafe_allow_html=True)
    imp1, imp2 = st.columns(2, gap="large")

    with imp1:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>🏦 Bank Statement Import (CSV)</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.82rem;color:{T['muted']};margin-bottom:0.8rem;line-height:1.6;'>Supports ANZ, CBA, Westpac, NAB, Macquarie, and most AUS bank CSV exports. Transactions are auto-categorised using keyword matching.</div>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Drop your bank statement CSV here", type=["csv"], key="bank_upload")
        if uploaded:
            df_tx, err = parse_bank_csv(uploaded)
            if err:
                st.error(f"Parse error: {err}")
                st.markdown(f"<div style='font-size:0.8rem;color:{T['muted']};margin-top:6px;'>Tip: Make sure your CSV has Date, Description, and Amount (or Debit/Credit) columns.</div>", unsafe_allow_html=True)
            else:
                st.success(f"✓ Parsed {len(df_tx)} transactions")
                # Category override
                st.markdown(f"<div style='font-size:0.8rem;color:{T['muted']};margin:0.5rem 0;'>Review auto-categorisation below. Edit categories if needed before importing.</div>", unsafe_allow_html=True)
                df_display=df_tx.copy()
                df_display["Date"]=df_display["Date"].dt.strftime("%d %b %Y")
                df_display["Amount ($)"]=df_display["Amount"].apply(lambda x: f"+${x:,.2f}" if x>0 else f"-${abs(x):,.2f}")
                st.dataframe(df_display[["Date","Description","Amount ($)","Category"]].head(30), use_container_width=True, hide_index=True)
                col_a,col_b=st.columns(2)
                with col_a:
                    if st.button("📥 Import as Transactions", use_container_width=True):
                        records=df_tx.to_dict("records")
                        for r in records:
                            r["Date"]=str(r["Date"])[:10]
                        st.session_state.transactions=records
                        st.success(f"Imported {len(records)} transactions!")
                        st.rerun()
                with col_b:
                    if st.button("➕ Add to Expenses", use_container_width=True):
                        debits=df_tx[df_tx["Amount"]<0].copy()
                        debits["amount"]=debits["Amount"].abs()
                        debits["budget"]=debits["Amount"].abs()
                        added=0
                        for _,row in debits.iterrows():
                            if row["amount"]>5:
                                st.session_state.expenses.append({"name":str(row["Description"])[:35],"amount":float(row["amount"]),"budget":float(row["amount"]),"category":str(row["Category"])})
                                added+=1
                        st.success(f"Added {added} debit transactions to expenses!"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Supported formats
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Supported Bank CSV Formats</div>", unsafe_allow_html=True)
        formats=[("ANZ","Date, Description, Debit, Credit, Balance"),
                 ("CBA","Date, Amount, Description, Balance"),
                 ("Westpac","Date, Amount, Description, Balance"),
                 ("NAB","Date, Amount, Description, Balance"),
                 ("Macquarie","Date, Transaction Type, Debit, Credit, Balance"),
                 ("Generic","Any CSV with Date + Amount/Debit/Credit + Description")]
        for bank,cols in formats:
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid {T['border']};font-size:0.79rem;'>"
                        f"<span style='color:{T['text']};font-weight:600;'>{bank}</span>"
                        f"<span style='color:{T['muted']};font-size:0.72rem;'>{cols}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with imp2:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>📦 JSON Data Import / Export</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.82rem;color:{T['muted']};margin-bottom:0.8rem;line-height:1.6;'>Export all your data as JSON to back it up or move it between devices. Import a previously saved JSON to restore your full financial profile.</div>", unsafe_allow_html=True)

        # Export JSON
        data_export={
            "expenses":      st.session_state.expenses,
            "subscriptions": st.session_state.subscriptions,
            "bills":         st.session_state.bills,
            "assets":        st.session_state.assets,
            "liabilities":   st.session_state.liabilities,
            "goals":         st.session_state.goals,
            "transactions":  st.session_state.transactions,
            "settings":      {"needs_pct":needs_pct,"wants_pct":wants_pct,"invest_pct":invest_pct,"risk_profile":st.session_state.risk_profile},
            "exported_at":   datetime.now().isoformat(),
        }
        json_bytes = json.dumps(data_export, indent=2, default=str).encode("utf-8")
        st.download_button(
            label="⬇ Export All Data (JSON)",
            data=json_bytes,
            file_name=f"seralung_data_{datetime.now().strftime('%Y-%m-%d')}.json",
            mime="application/json",
            use_container_width=True,
        )
        st.markdown("---")
        json_upload = st.file_uploader("Import JSON backup", type=["json"], key="json_upload")
        if json_upload:
            try:
                imported = json.loads(json_upload.read().decode("utf-8"))
                if st.button("✅ Restore from JSON", use_container_width=True):
                    for key in ["expenses","subscriptions","bills","assets","liabilities","goals","transactions"]:
                        if key in imported: st.session_state[key]=imported[key]
                    if "settings" in imported:
                        s=imported["settings"]
                        for k,v in s.items(): st.session_state[k]=v
                    st.success("Data restored successfully!"); st.rerun()
                st.markdown(f"<div style='font-size:0.78rem;color:{T['muted']};margin-top:0.5rem;'>Preview: {len(imported.get('expenses',[]))} expenses, {len(imported.get('goals',[]))} goals, {len(imported.get('assets',[]))} assets</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

        # Imported transactions viewer
        if st.session_state.transactions:
            st.markdown("<div class='sf-card'><div class='sf-card-title'>Imported Transactions</div>", unsafe_allow_html=True)
            df_tx2 = pd.DataFrame(st.session_state.transactions)
            total_in  = df_tx2[df_tx2["Amount"]>0]["Amount"].sum() if "Amount" in df_tx2.columns else 0
            total_out = df_tx2[df_tx2["Amount"]<0]["Amount"].abs().sum() if "Amount" in df_tx2.columns else 0
            tx1,tx2,tx3=st.columns(3)
            tx1.metric("Transactions", len(df_tx2)); tx2.metric("Total In", fmt(total_in)); tx3.metric("Total Out", fmt(total_out))
            if "Category" in df_tx2.columns and "Amount" in df_tx2.columns:
                cat_sum=df_tx2[df_tx2["Amount"]<0].groupby("Category")["Amount"].sum().abs().reset_index()
                if not cat_sum.empty:
                    n=len(cat_sum); cc=(T["chart_colors"]*math.ceil(n/max(1,len(T["chart_colors"]))))[:n]
                    fig_tx=go.Figure(go.Bar(x=cat_sum["Category"],y=cat_sum["Amount"],marker_color=cc,text=[fmt(v) for v in cat_sum["Amount"]],textposition="outside",textfont=dict(color=T["text"],size=10)))
                    fig_tx.update_layout(**plot_layout("Spending by Category (Imported)",220)); fig_tx.update_yaxes(tickprefix="$",tickformat=",.0f")
                    st.plotly_chart(fig_tx, use_container_width=True)
            if st.button("🗑 Clear Transactions",use_container_width=True):
                st.session_state.transactions=[]; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.markdown(f"<p style='text-align:center;color:{T['muted']};font-size:0.68rem;'>"
            "💎 Seralung Finance Pro &nbsp;·&nbsp; Educational purposes only. Not financial advice. "
            "Always consult a qualified financial adviser. &nbsp;·&nbsp; AUS Tax: FY2024-25</p>", unsafe_allow_html=True)
