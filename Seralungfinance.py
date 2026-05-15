"""
Seralung Finance
requirements.txt:
    streamlit>=1.32
    plotly>=5.18
    pandas>=2.0
    fpdf2>=2.7

Run:  streamlit run seralung_finance_pro.py
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math, io, json, csv
from datetime import datetime, date

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
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
    "Natural": {
        "bg":"#FAFAF8","surface":"#FFFFFF","surface2":"#F5F3F0","border":"#E5E1DB",
        "accent":"#2D6A4F","accent2":"#40916C","text":"#1C1917","muted":"#78716C",
        "green":"#16A34A","red":"#DC2626","amber":"#D97706","blue":"#2563EB",
        "chart":["#2D6A4F","#D97706","#2563EB","#DC2626","#7C3AED","#0891B2"],"dark":False,
    },
    "Dark": {
        "bg":"#0F1117","surface":"#1A1D27","surface2":"#22263A","border":"#2E3350",
        "accent":"#6C8EF5","accent2":"#4ECDC4","text":"#E8EAF6","muted":"#8B90B0",
        "green":"#43D9A2","red":"#FF6B6B","amber":"#FFB347","blue":"#6C8EF5",
        "chart":["#6C8EF5","#4ECDC4","#FF6B6B","#FFB347","#43D9A2","#C084FC"],"dark":True,
    },
    "Slate": {
        "bg":"#F1F5F9","surface":"#FFFFFF","surface2":"#E2E8F0","border":"#CBD5E1",
        "accent":"#1E40AF","accent2":"#3B82F6","text":"#0F172A","muted":"#64748B",
        "green":"#16A34A","red":"#DC2626","amber":"#D97706","blue":"#2563EB",
        "chart":["#1E40AF","#16A34A","#D97706","#DC2626","#7C3AED","#0891B2"],"dark":False,
    },
    "Midnight": {
        "bg":"#060B18","surface":"#0D1526","surface2":"#142035","border":"#1E3050",
        "accent":"#38BDF8","accent2":"#0EA5E9","text":"#E1F0FF","muted":"#6A8BAA",
        "green":"#34D399","red":"#F87171","amber":"#FCD34D","blue":"#38BDF8",
        "chart":["#38BDF8","#34D399","#FCD34D","#F87171","#A78BFA","#60A5FA"],"dark":True,
    },
}

CATEGORIES  = ["Housing","Food","Transport","Health","Insurance","Tech","Entertainment","Personal","Education","Other"]
ASSET_TYPES = ["Cash","Savings","Investments","Super","Property","Vehicle","Business","Other"]
LIAB_TYPES  = ["Mortgage","Loan","Credit","HECS","Personal","Business","Other"]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def _init(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

_init("expenses",[
    {"name":"Rent",        "amount":1800.0,"budget":2000.0,"category":"Housing"},
    {"name":"Groceries",   "amount":450.0, "budget":500.0, "category":"Food"},
    {"name":"Transport",   "amount":250.0, "budget":300.0, "category":"Transport"},
    {"name":"Dining",      "amount":350.0, "budget":300.0, "category":"Food"},
    {"name":"Utilities",   "amount":180.0, "budget":220.0, "category":"Housing"},
    {"name":"Phone",       "amount":85.0,  "budget":85.0,  "category":"Tech"},
    {"name":"Insurance",   "amount":150.0, "budget":200.0, "category":"Insurance"},
    {"name":"Entertainment","amount":120.0,"budget":150.0, "category":"Entertainment"},
    {"name":"Health",      "amount":80.0,  "budget":100.0, "category":"Health"},
    {"name":"Clothing",    "amount":80.0,  "budget":100.0, "category":"Personal"},
])
_init("subscriptions",[
    {"name":"Netflix","amount":18.0},{"name":"Spotify","amount":12.0},
    {"name":"Amazon Prime","amount":9.99},{"name":"Gym","amount":45.0},
    {"name":"Cloud Storage","amount":5.0},
])
_init("bills",[
    {"name":"Rent","amount":1800.0,"due_day":1},
    {"name":"Electricity","amount":180.0,"due_day":15},
    {"name":"Internet","amount":90.0,"due_day":20},
    {"name":"Phone","amount":85.0,"due_day":25},
])
_init("assets",[
    {"name":"Savings Account","type":"Cash","value":12000.0},
    {"name":"Superannuation","type":"Super","value":35000.0},
    {"name":"Car","type":"Vehicle","value":18000.0},
    {"name":"ETF Portfolio","type":"Investments","value":8500.0},
])
_init("liabilities",[
    {"name":"Car Loan","type":"Loan","balance":14000.0,"rate":6.5,"min_payment":350.0},
    {"name":"Credit Card","type":"Credit","balance":2800.0,"rate":19.99,"min_payment":84.0},
    {"name":"HECS Debt","type":"HECS","balance":18000.0,"rate":3.9,"min_payment":200.0},
])
_init("goals",[
    {"name":"Emergency Fund","amount":15000.0,"saved":12000.0,"priority":"High"},
    {"name":"Europe Holiday","amount":8000.0,"saved":2000.0,"priority":"Medium"},
    {"name":"Property Deposit","amount":80000.0,"saved":25000.0,"priority":"High"},
])
_init("transactions",[])
_init("risk_profile","Moderate")
_init("needs_pct",50); _init("wants_pct",30); _init("invest_pct",20)
_init("em_pct",30);    _init("idx_pct",40);   _init("stk_pct",20); _init("cry_pct",10)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt(n): return f"${n:,.0f}"

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

def _p(text):
    """Sanitise text for FPDF latin-1 — fixes FPDFUnicodeEncodingException."""
    text = str(text)
    for uni, asc in {
        '\u2014':' - ','\u2013':'-','\u2018':"'",'\u2019':"'",
        '\u201c':'"','\u201d':'"','\u00b7':'.','\u2022':'*',
        '\u00e9':'e','\u00e8':'e','\u00ea':'e','\u00e0':'a',
        '\u00e2':'a','\u00ee':'i','\u00f4':'o','\u00fb':'u',
        '\u00e7':'c','\u00fc':'u','\u00f6':'o','\u00e4':'a',
    }.items():
        text = text.replace(uni, asc)
    return text.encode('latin-1', errors='replace').decode('latin-1')

def auto_categorize(desc):
    d = str(desc).lower()
    rules = [
        (["rent","lease","landlord","property manager","mortgage"],"Housing"),
        (["electricity","power","energy","agl","origin","simply"],"Housing"),
        (["internet","nbn","optus","telstra","vodafone","tpg"],"Tech"),
        (["coles","woolworths","aldi","iga","supermarket","grocer","costco"],"Food"),
        (["uber eats","menulog","doordash","mcdonalds","kfc","subway","dominos",
          "pizza","cafe","coffee","restaurant","takeaway","bakery"],"Food"),
        (["netflix","stan","disney","binge","foxtel","spotify","apple music",
          "youtube","amazon prime"],"Entertainment"),
        (["gym","fitness","yoga","pilates","crossfit"],"Health"),
        (["pharmacy","chemist","doctor","medical","dental","hospital",
          "medibank","bupa","ahm"],"Health"),
        (["fuel","petrol","shell","bp","caltex","ampol"],"Transport"),
        (["uber","ola","taxi","parking","toll","myki","opal","train","bus"],"Transport"),
        (["insurance","nrma","aami","racv","gio","allianz"],"Insurance"),
        (["school","university","tafe","course","udemy","coursera"],"Education"),
    ]
    for kws, cat in rules:
        if any(k in d for k in kws): return cat
    return "Other"

def parse_bank_csv(uploaded_file):
    try:
        content = uploaded_file.read().decode("utf-8", errors="replace")
        lines   = content.strip().split("\n")
        hi = 0
        for i, ln in enumerate(lines):
            if any(k in ln.lower() for k in ["date","amount","description","debit","credit"]):
                hi = i; break
        df = pd.read_csv(io.StringIO("\n".join(lines[hi:])), on_bad_lines="skip", dtype=str)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        dcol = next((c for c in df.columns if "date" in c), None)
        ncol = next((c for c in df.columns if any(k in c for k in ["description","details","narration","memo","narrative"])), None)
        acol = next((c for c in df.columns if c in ["amount","net_amount"]), None)
        dbcol= next((c for c in df.columns if "debit"  in c), None)
        crcol= next((c for c in df.columns if "credit" in c), None)
        if not dcol or not ncol:
            return None, "Cannot find Date/Description columns."
        res = pd.DataFrame()
        res["Date"]        = pd.to_datetime(df[dcol], dayfirst=True, errors="coerce")
        res["Description"] = df[ncol].fillna("Unknown").str.strip()
        if acol:
            res["Amount"] = pd.to_numeric(df[acol].str.replace(r'[$,\s]','',regex=True), errors="coerce").fillna(0)
        elif dbcol and crcol:
            d2 = pd.to_numeric(df[dbcol].str.replace(r'[$,\s]','',regex=True), errors="coerce").fillna(0)
            c2 = pd.to_numeric(df[crcol].str.replace(r'[$,\s]','',regex=True), errors="coerce").fillna(0)
            res["Amount"] = c2 - d2
        else:
            return None, "Cannot find Amount/Debit/Credit columns."
        res["Category"] = res["Description"].apply(auto_categorize)
        res = res.dropna(subset=["Date"])
        res = res[res["Amount"] != 0].sort_values("Date", ascending=False)
        return res, None
    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  (theme only)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Seralung Finance")
    theme_name = st.selectbox("Theme", list(THEMES.keys()))
    T = THEMES[theme_name]
    st.divider()
    if st.button("Reset demo data", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    st.caption("Educational use only. Not financial advice.")

# ─────────────────────────────────────────────────────────────────────────────
# T-DEPENDENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def hex_to_rgba(hx, a=0.15):
    h = hx.lstrip("#")
    r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
    return f"rgba({r},{g},{b},{a})"

def plot_layout(title="", height=280):
    d = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter,sans-serif",color=T["muted"],size=11),
        height=height, margin=dict(l=8,r=8,t=36 if title else 8,b=8),
        legend=dict(font=dict(color=T["muted"],size=11),bgcolor="rgba(0,0,0,0)",borderwidth=0),
        xaxis=dict(gridcolor=T["border"],linecolor=T["border"],showgrid=True,color=T["muted"]),
        yaxis=dict(gridcolor=T["border"],linecolor=T["border"],showgrid=True,color=T["muted"]),
    )
    if title: d["title"] = dict(text=title, font=dict(color=T["text"],size=13))
    return d

def health_score():
    score, det = 0, {}
    tsub = sum(s["amount"] for s in st.session_state.subscriptions)
    mexp = sum(e["amount"] for e in st.session_state.expenses) + tsub
    sr   = max(0,(total_income-mexp)/total_income*100) if total_income>0 else 0
    s1   = min(25, sr/20*25); score += s1
    det["Savings rate"]     = {"score":s1,"max":25,"val":f"{sr:.1f}%","ok":sr>=20}
    cash = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
    em   = cash/mexp if mexp>0 else 0
    s2   = min(20, em/6*20); score += s2
    det["Emergency fund"]   = {"score":s2,"max":20,"val":f"{em:.1f} mo","ok":em>=6}
    nd   = sum(l["balance"] for l in st.session_state.liabilities if l["type"]!="HECS")
    dti  = nd/(total_income*12)*100 if total_income>0 else 0
    s3   = max(0, 20-dti*0.5); score += s3
    det["Debt-to-income"]   = {"score":s3,"max":20,"val":f"{dti:.0f}%","ok":dti<=36}
    nw   = sum(a["value"] for a in st.session_state.assets)-sum(l["balance"] for l in st.session_state.liabilities)
    s4   = 15 if nw>0 else max(0,15+nw/10000); score += s4
    det["Net worth"]        = {"score":s4,"max":15,"val":fmt(nw),"ok":nw>0}
    over = sum(max(0,e["amount"]-e.get("budget",e["amount"])) for e in st.session_state.expenses)
    s5   = max(0,10-over/100); score += s5
    det["Budget adherence"] = {"score":s5,"max":10,"val":f"{fmt(over)} over","ok":over==0}
    s6   = min(10, len(st.session_state.goals)*3.5); score += s6
    det["Goals set"]        = {"score":s6,"max":10,"val":f"{len(st.session_state.goals)} active","ok":len(st.session_state.goals)>=2}
    return round(score), det

# ─────────────────────────────────────────────────────────────────────────────
# REPORT GENERATORS
# ─────────────────────────────────────────────────────────────────────────────
def generate_csv(period="Monthly"):
    tsub = sum(s["amount"] for s in st.session_state.subscriptions)
    texp = sum(e["amount"] for e in st.session_state.expenses) + tsub
    nw   = sum(a["value"] for a in st.session_state.assets) - sum(l["balance"] for l in st.session_state.liabilities)
    sr   = (total_income-texp)/total_income*100 if total_income>0 else 0
    hs,_ = health_score()
    buf  = io.StringIO(); w = csv.writer(buf)
    w.writerow([f"Seralung Finance - {period} Report - {datetime.now().strftime('%B %Y')}"])
    w.writerow([f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}"])
    w.writerow([])
    w.writerow(["SUMMARY"])
    for lbl,val in [("Health Score",f"{hs}/100"),("Monthly Income",fmt(total_income)),
                    ("Total Expenses",fmt(texp)),("Net Cash Flow",fmt(total_income-texp)),
                    ("Savings Rate",f"{sr:.1f}%"),("Net Worth",fmt(nw))]:
        w.writerow([lbl,val])
    w.writerow([])
    w.writerow(["EXPENSES","","","",""])
    w.writerow(["Name","Category","Spent","Budget","Over Budget"])
    for e in st.session_state.expenses:
        bud=e.get("budget",e["amount"]); over=max(0,e["amount"]-bud)
        w.writerow([e["name"],e.get("category","Other"),f"{e['amount']:.2f}",f"{bud:.2f}",f"{over:.2f}"])
    w.writerow([])
    w.writerow(["SUBSCRIPTIONS"])
    w.writerow(["Name","Amount/mo"])
    for s in st.session_state.subscriptions:
        w.writerow([s["name"],f"{s['amount']:.2f}"])
    w.writerow(["TOTAL",f"{tsub:.2f}"])
    w.writerow([])
    w.writerow(["ASSETS"])
    w.writerow(["Name","Type","Value"])
    for a in st.session_state.assets:
        w.writerow([a["name"],a["type"],f"{a['value']:.2f}"])
    w.writerow([])
    w.writerow(["LIABILITIES"])
    w.writerow(["Name","Type","Balance","Rate %","Min Payment"])
    for l in st.session_state.liabilities:
        w.writerow([l["name"],l["type"],f"{l['balance']:.2f}",f"{l.get('rate',0):.2f}",f"{l.get('min_payment',0):.2f}"])
    w.writerow([])
    w.writerow(["GOALS"])
    w.writerow(["Name","Priority","Target","Saved","Remaining","Progress %"])
    for g in st.session_state.goals:
        rem=max(0,g["amount"]-g["saved"]); pct=g["saved"]/g["amount"]*100 if g["amount"]>0 else 0
        w.writerow([g["name"],g.get("priority","Medium"),f"{g['amount']:.2f}",f"{g['saved']:.2f}",f"{rem:.2f}",f"{pct:.1f}%"])
    w.writerow([])
    if st.session_state.transactions:
        w.writerow(["TRANSACTIONS"])
        w.writerow(["Date","Description","Amount","Category"])
        for tx in st.session_state.transactions:
            w.writerow([tx.get("Date",""),tx.get("Description",""),f"{tx.get('Amount',0):.2f}",tx.get("Category","")])
    w.writerow([])
    w.writerow(["Educational use only. Not financial advice."])
    return buf.getvalue().encode("utf-8")

def generate_pdf(period="Monthly"):
    if not PDF_AVAILABLE: return None
    tsub = sum(s["amount"] for s in st.session_state.subscriptions)
    texp = sum(e["amount"] for e in st.session_state.expenses) + tsub
    nw   = sum(a["value"] for a in st.session_state.assets) - sum(l["balance"] for l in st.session_state.liabilities)
    sr   = (total_income-texp)/total_income*100 if total_income>0 else 0
    hs,_ = health_score()
    grade= "Excellent" if hs>=80 else "Good" if hs>=65 else "Fair" if hs>=50 else "Needs Work" if hs>=35 else "Critical"

    pdf = FPDF(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()

    # Header
    pdf.set_fill_color(20,40,30); pdf.rect(0,0,210,35,"F")
    pdf.set_font("Helvetica","B",20); pdf.set_text_color(200,230,210)
    pdf.cell(0,15,"",ln=True)
    pdf.cell(0,12,_p("  Seralung Finance"),ln=True)
    pdf.set_font("Helvetica","",10); pdf.set_text_color(160,200,175)
    pdf.cell(0,6,_p(f"  {period} Report  |  {datetime.now().strftime('%B %Y')}"),ln=True)
    pdf.ln(8)

    # Health score
    sc = (74,222,128) if hs>=70 else (251,191,36) if hs>=50 else (248,113,113)
    pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","B",12)
    pdf.cell(0,8,_p("Financial Health Score"),ln=True)
    pdf.set_font("Helvetica","B",36); pdf.set_text_color(*sc)
    pdf.cell(0,14,_p(f"{hs}/100"),ln=True)
    pdf.set_font("Helvetica","",11); pdf.set_text_color(80,80,80)
    pdf.cell(0,7,_p(f"{grade}  |  Generated {datetime.now().strftime('%d %b %Y %H:%M')}"),ln=True); pdf.ln(4)

    # Summary
    pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","B",12)
    pdf.cell(0,9,_p("Monthly Summary"),ln=True)
    rows=[("Monthly Income",fmt(total_income)),("Total Expenses",fmt(texp)),
          ("Net Cash Flow",fmt(total_income-texp)),("Savings Rate",f"{sr:.1f}%"),
          ("Net Worth",fmt(nw)),
          ("Total Assets",fmt(sum(a['value'] for a in st.session_state.assets))),
          ("Total Liabilities",fmt(sum(l['balance'] for l in st.session_state.liabilities)))]
    for i,(lbl,val) in enumerate(rows):
        pdf.set_fill_color(245,250,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",10); pdf.set_text_color(60,60,60)
        pdf.cell(100,8,_p(f"  {lbl}"),fill=True)
        pdf.set_font("Helvetica","B",10); pdf.set_text_color(20,60,40)
        pdf.cell(80,8,_p(f"  {val}"),fill=True,ln=True)
    pdf.ln(5)

    # Expenses table
    pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","B",12)
    pdf.cell(0,9,_p("Expense Breakdown"),ln=True)
    pdf.set_fill_color(20,40,30); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
    for hdr,w_ in [("  Name",65),("Category",28),("Spent",25),("Budget",25),("Over",22),("Status",20)]:
        pdf.cell(w_,7,_p(hdr),fill=True)
    pdf.ln()
    for i,e in enumerate(st.session_state.expenses):
        bud=e.get("budget",e["amount"]); over=max(0,e["amount"]-bud)
        pdf.set_fill_color(245,250,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","",9)
        pdf.cell(65,7,_p(f"  {e['name'][:26]}"),fill=True)
        pdf.cell(28,7,_p(e.get("category","Other")[:12]),fill=True)
        pdf.cell(25,7,_p(f"${e['amount']:,.0f}"),fill=True)
        pdf.cell(25,7,_p(f"${bud:,.0f}"),fill=True)
        pdf.cell(22,7,_p(f"${over:,.0f}") if over>0 else _p(""),fill=True)
        pdf.set_text_color(180,20,20) if over>0 else pdf.set_text_color(16,120,60)
        pdf.cell(20,7,_p("OVER") if over>0 else _p("OK"),fill=True,ln=True)
        pdf.set_text_color(30,30,30)
    pdf.set_fill_color(220,235,225); pdf.set_font("Helvetica","B",9); pdf.set_text_color(30,30,30)
    pdf.cell(65,7,_p("  Subscriptions total"),fill=True)
    pdf.cell(28,7,_p("Various"),fill=True)
    pdf.cell(25,7,_p(f"${tsub:,.0f}"),fill=True)
    pdf.cell(25+22+20,7,"",fill=True,ln=True); pdf.ln(4)

    # Goals
    if st.session_state.goals:
        pdf.set_font("Helvetica","B",12); pdf.set_text_color(30,30,30)
        pdf.cell(0,9,_p("Financial Goals"),ln=True)
        pdf.set_fill_color(20,40,30); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
        for hdr,w_ in [("  Goal",60),("Priority",22),("Target",28),("Saved",28),("Progress",28),("Remaining",20)]:
            pdf.cell(w_,7,_p(hdr),fill=True)
        pdf.ln()
        for i,g in enumerate(st.session_state.goals):
            rem=max(0,g["amount"]-g["saved"]); pct=g["saved"]/g["amount"]*100 if g["amount"]>0 else 0
            pdf.set_fill_color(245,250,246) if i%2==0 else pdf.set_fill_color(255,255,255)
            pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","",9)
            pdf.cell(60,7,_p(f"  {g['name'][:24]}"),fill=True)
            pdf.cell(22,7,_p(g.get("priority","Med")),fill=True)
            pdf.cell(28,7,_p(f"${g['amount']:,.0f}"),fill=True)
            pdf.cell(28,7,_p(f"${g['saved']:,.0f}"),fill=True)
            pdf.cell(28,7,_p(f"{pct:.0f}%"),fill=True)
            pdf.cell(20,7,_p(f"${rem:,.0f}"),fill=True,ln=True)
        pdf.ln(4)

    # Net worth
    pdf.set_font("Helvetica","B",12); pdf.set_text_color(30,30,30)
    pdf.cell(0,9,_p("Net Worth Breakdown"),ln=True)
    pdf.set_font("Helvetica","B",10); pdf.cell(0,7,_p("Assets"),ln=True)
    for i,a in enumerate(st.session_state.assets):
        pdf.set_fill_color(240,253,244) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(30,30,30)
        pdf.cell(100,7,_p(f"  {a['name']} ({a['type']})"),fill=True)
        pdf.set_text_color(16,100,50); pdf.set_font("Helvetica","B",9)
        pdf.cell(80,7,_p(f"+{fmt(a['value'])}"),fill=True,ln=True)
    pdf.ln(2); pdf.set_font("Helvetica","B",10); pdf.set_text_color(30,30,30)
    pdf.cell(0,7,_p("Liabilities"),ln=True)
    for i,l in enumerate(st.session_state.liabilities):
        pdf.set_fill_color(255,241,241) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(30,30,30)
        pdf.cell(100,7,_p(f"  {l['name']} ({l.get('rate',0):.1f}% p.a.)"),fill=True)
        pdf.set_text_color(180,20,20); pdf.set_font("Helvetica","B",9)
        pdf.cell(80,7,_p(f"-{fmt(l['balance'])}"),fill=True,ln=True)
    pdf.ln(2)
    nwc = (16,100,50) if nw>=0 else (180,20,20)
    pdf.set_fill_color(220,235,225); pdf.set_text_color(30,30,30); pdf.set_font("Helvetica","B",10)
    pdf.cell(100,8,_p("  Net Worth"),fill=True)
    pdf.set_text_color(*nwc); pdf.cell(80,8,_p(fmt(nw)),fill=True,ln=True); pdf.ln(5)

    # Footer
    pdf.set_font("Helvetica","I",8); pdf.set_text_color(150,150,150)
    pdf.cell(0,5,_p("Seralung Finance  |  Educational use only. Not financial advice. Consult a qualified adviser."),ln=True)
    return bytes(pdf.output())

# ─────────────────────────────────────────────────────────────────────────────
# CSS  (clean, mobile-first)
# ─────────────────────────────────────────────────────────────────────────────
ti = "#111111" if not T["dark"] else T["text"]
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,.stApp{{background:{T['bg']} !important;color:{T['text']} !important;font-family:Inter,sans-serif;}}
*,*::before,*::after{{box-sizing:border-box;}}
p,span,div,label,li{{color:{T['text']};}}
h1,h2,h3,h4{{color:{T['text']} !important;font-weight:600;}}
[data-testid="stSidebar"]{{background:{T['surface']} !important;border-right:1px solid {T['border']};}}
[data-testid="stSidebar"] *{{color:{T['text']} !important;}}
[data-testid="metric-container"]{{background:{T['surface']} !important;border:1px solid {T['border']} !important;border-radius:12px !important;padding:0.85rem 1rem !important;}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] *{{color:{T['muted']} !important;font-size:0.68rem !important;text-transform:uppercase;letter-spacing:0.06em;}}
[data-testid="metric-container"] [data-testid="stMetricValue"] *{{color:{T['text']} !important;font-weight:700 !important;}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] *{{font-size:0.7rem !important;}}
[data-testid="stTabs"] [role="tab"]{{background:{T['surface2']};border:1px solid {T['border']};border-radius:8px;color:{T['muted']} !important;font-size:0.78rem;font-weight:500;padding:0.3rem 0.7rem;margin-right:3px;}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{{background:{T['accent']} !important;color:#fff !important;border-color:{T['accent']} !important;}}
[data-testid="stTabs"] [role="tablist"]{{border-bottom:1px solid {T['border']};padding-bottom:0.5rem;flex-wrap:wrap;gap:3px;}}
label,[data-testid="stWidgetLabel"]{{color:{T['text']} !important;}}
[data-testid="stNumberInput"] input,[data-testid="stTextInput"] input,textarea{{background:{T['surface2']} !important;border:1px solid {T['border']} !important;border-radius:8px !important;color:{ti} !important;}}
[data-testid="stSelectbox"]>div>div,[data-testid="stSelectbox"] span{{background:{T['surface2']} !important;border:1px solid {T['border']} !important;color:{T['text']} !important;border-radius:8px !important;}}
[data-testid="stCheckbox"] span{{color:{T['text']} !important;}}
[data-baseweb="slider"] [role="slider"]{{background:{T['accent']} !important;border-color:{T['accent']} !important;}}
.stButton>button{{background:{T['accent']} !important;border:none !important;border-radius:8px !important;color:#fff !important;font-weight:500 !important;font-family:Inter,sans-serif !important;transition:opacity 0.15s,transform 0.12s;}}
.stButton>button:hover{{opacity:0.85 !important;transform:translateY(-1px);}}
[data-testid="stExpander"]{{background:{T['surface']} !important;border:1px solid {T['border']} !important;border-radius:10px !important;}}
[data-testid="stExpander"] summary *{{color:{T['text']} !important;}}
[data-testid="stFileUploader"]{{background:{T['surface2']} !important;border:2px dashed {T['border']} !important;border-radius:10px !important;}}
[data-testid="stAlert"] div{{color:{T['text']} !important;}}
hr{{border-color:{T['border']} !important;}}
.card{{background:{T['surface']};border:1px solid {T['border']};border-radius:14px;padding:1.1rem 1.3rem;margin-bottom:0.9rem;}}
.card-label{{font-size:0.62rem;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;color:{T['muted']};margin-bottom:0.7rem;display:block;}}
.row{{display:flex;justify-content:space-between;padding:0.44rem 0;border-bottom:1px solid {T['border']};font-size:0.81rem;color:{T['text']};}}
.row:last-child{{border-bottom:none;font-weight:600;}}
.tip{{background:{hex_to_rgba(T['accent'],0.1)};border-left:3px solid {T['accent']};border-radius:0 10px 10px 0;padding:0.65rem 1rem;font-size:0.81rem;color:{T['text']};margin-bottom:0.9rem;line-height:1.5;}}
.tip strong{{color:{T['accent']};}}
.ok  {{background:{hex_to_rgba(T['green'],0.14)};color:{T['green']};font-size:0.61rem;font-weight:700;padding:2px 7px;border-radius:5px;display:inline-block;}}
.warn{{background:{hex_to_rgba(T['amber'],0.14)};color:{T['amber']};font-size:0.61rem;font-weight:700;padding:2px 7px;border-radius:5px;display:inline-block;}}
.bad {{background:{hex_to_rgba(T['red'],0.14)};color:{T['red']};font-size:0.61rem;font-weight:700;padding:2px 7px;border-radius:5px;display:inline-block;}}
.blu {{background:{hex_to_rgba(T['blue'],0.14)};color:{T['blue']};font-size:0.61rem;font-weight:700;padding:2px 7px;border-radius:5px;display:inline-block;}}
.income-bar{{background:{T['surface']};border:1px solid {T['border']};border-radius:14px;padding:0.9rem 1.2rem 0.6rem;margin-bottom:0.9rem;}}
@media(max-width:768px){{
  .block-container{{padding:0.5rem 0.5rem 2rem !important;}}
  [data-testid="stTabs"] [role="tab"]{{font-size:0.7rem;padding:0.25rem 0.5rem;}}
  .card{{padding:0.75rem 0.85rem;}}
  h1{{font-size:1.25rem !important;}}
}}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([3,1])
with hc1:
    st.markdown(f"<h1 style='margin:0;font-size:1.65rem;letter-spacing:-0.02em;color:{T['text']};'>Seralung Finance</h1>"
                f"<p style='color:{T['muted']};font-size:0.76rem;margin:2px 0 0.7rem;'>Your complete financial command centre</p>", unsafe_allow_html=True)
with hc2:
    st.markdown(f"<div style='text-align:right;padding-top:0.4rem;'>"
                f"<div style='font-size:0.68rem;color:{T['muted']};'>{datetime.now().strftime('%A')}</div>"
                f"<div style='font-size:0.92rem;font-weight:600;color:{T['text']};'>{datetime.now().strftime('%d %b %Y')}</div>"
                f"</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INCOME & BUDGET RULE  — always visible in main area, no sidebar required
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"<div class='income-bar'><span class='card-label'>Monthly Income & Budget Rule</span></div>", unsafe_allow_html=True)
i1, i2, i3, i4, i5 = st.columns([2, 2, 1, 1, 1])
with i1:
    primary_income = st.number_input("Primary take-home /mo", min_value=0.0, value=6000.0, step=100.0, format="%.0f", key="pi")
with i2:
    other_income   = st.number_input("Other income /mo",      min_value=0.0, value=500.0,  step=50.0,  format="%.0f", key="oi")
with i3:
    needs_pct  = st.number_input("Needs %",  0, 100, st.session_state.get("needs_pct",50),  1, key="np_n")
    st.session_state["needs_pct"]  = needs_pct
with i4:
    wants_pct  = st.number_input("Wants %",  0, 100, st.session_state.get("wants_pct",30),  1, key="wp_n")
    st.session_state["wants_pct"]  = wants_pct
with i5:
    invest_pct = st.number_input("Invest %", 0, 100, st.session_state.get("invest_pct",20), 1, key="ip_n")
    st.session_state["invest_pct"] = invest_pct

total_income = primary_income + other_income
_psum = needs_pct + wants_pct + invest_pct
if _psum != 100:
    st.warning(f"Budget percentages sum to {_psum}% — adjust to reach 100%.")
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# DERIVED VALUES
# ─────────────────────────────────────────────────────────────────────────────
total_sub    = sum(s["amount"] for s in st.session_state.subscriptions)
total_exp    = sum(e["amount"] for e in st.session_state.expenses) + total_sub
total_assets = sum(a["value"]  for a in st.session_state.assets)
total_liab   = sum(l["balance"] for l in st.session_state.liabilities)
net_worth    = total_assets - total_liab
investable   = total_income * invest_pct / 100
cash_flow    = total_income - total_exp
savings_rate = cash_flow / total_income * 100 if total_income > 0 else 0
cash_assets  = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
em_months    = cash_assets / total_exp if total_exp > 0 else 0
hs, hs_det   = health_score()
nw_col       = T["green"] if net_worth >= 0 else T["red"]

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5 = st.tabs(["Overview","Budget","Invest","Wealth","Reports & Import"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t1:
    if   hs>=80: sc,sg = T["green"],"Excellent"
    elif hs>=65: sc,sg = T["blue"],"Good"
    elif hs>=50: sc,sg = T["amber"],"Fair"
    elif hs>=35: sc,sg = T["red"],"Needs Work"
    else:        sc,sg = T["red"],"Critical"

    col_score, col_m1, col_m2, col_m3, col_m4 = st.columns([1.3,1,1,1,1])
    with col_score:
        st.markdown(f"<div class='card' style='border-color:{sc};text-align:center;'>"
                    f"<span class='card-label'>Financial Health</span>"
                    f"<div style='font-size:3rem;font-weight:800;color:{sc};line-height:1;'>{hs}</div>"
                    f"<div style='font-size:0.8rem;font-weight:600;color:{sc};margin:4px 0 2px;'>{sg}</div>"
                    f"<div style='background:{T['surface2']};border-radius:8px;height:7px;margin-top:8px;'>"
                    f"<div style='width:{hs}%;height:100%;background:{sc};border-radius:8px;'></div></div>"
                    f"</div>", unsafe_allow_html=True)
    with col_m1: st.metric("Net Worth",     fmt(net_worth),  "Positive" if net_worth>=0 else "Negative", delta_color="normal" if net_worth>=0 else "inverse")
    with col_m2: st.metric("Cash Flow",     fmt(cash_flow),  "Surplus"  if cash_flow>=0 else "Deficit",  delta_color="normal" if cash_flow>=0 else "inverse")
    with col_m3: st.metric("Savings Rate",  f"{savings_rate:.1f}%", "Target 20%", delta_color="normal" if savings_rate>=20 else "inverse")
    with col_m4: st.metric("Emergency Fund",f"{em_months:.1f} mo",  "Safe" if em_months>=6 else "Low",   delta_color="normal" if em_months>=6 else "inverse")

    st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)
    ov1, ov2 = st.columns(2, gap="large")

    with ov1:
        # Budget bars
        st.markdown(f"<div class='card'><span class='card-label'>Budget Overview</span>", unsafe_allow_html=True)
        for lbl, actual, budget, col in [
            ("Needs",  total_exp*0.60, total_income*needs_pct/100,  T["blue"]),
            ("Wants",  total_exp*0.40, total_income*wants_pct/100,  T["accent"]),
            ("Invest", investable,     total_income*invest_pct/100, T["green"]),
        ]:
            p = min(100, actual/budget*100) if budget>0 else 0
            bc = "ok" if p<=85 else "warn" if p<=100 else "bad"
            br = T["red"] if p>100 else col
            bt = "On track" if p<=85 else "Near limit" if p<=100 else "Over"
            st.markdown(f"<div style='margin-bottom:10px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:3px;'>"
                        f"<span style='color:{T['text']}'>{lbl}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:5px;'>{fmt(actual)} / {fmt(budget)}</span>"
                        f"<span class='{bc}'>{bt}</span></div></div>"
                        f"<div style='background:{T['surface2']};border-radius:5px;height:6px;'>"
                        f"<div style='width:{p:.1f}%;height:100%;background:{br};border-radius:5px;'></div>"
                        f"</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Health breakdown
        st.markdown(f"<div class='card'><span class='card-label'>Score Breakdown</span>", unsafe_allow_html=True)
        for name, d in hs_det.items():
            p = d["score"]/d["max"]*100
            bc = "ok" if p>=70 else "warn" if p>=40 else "bad"
            br = T["green"] if p>=70 else T["amber"] if p>=40 else T["red"]
            st.markdown(f"<div style='margin-bottom:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:0.77rem;margin-bottom:3px;'>"
                        f"<span style='color:{T['text']}'>{name}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:4px;'>{d['val']}</span>"
                        f"<span class='{bc}'>{d['score']:.0f}/{d['max']}</span></div></div>"
                        f"<div style='background:{T['surface2']};border-radius:4px;height:5px;'>"
                        f"<div style='width:{p:.1f}%;height:100%;background:{br};border-radius:4px;'></div>"
                        f"</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with ov2:
        # Spending donut
        df_e = pd.DataFrame(st.session_state.expenses); df_e=df_e[df_e["amount"]>0]
        if not df_e.empty:
            cat_df = df_e.groupby("category")["amount"].sum().reset_index()
            n=len(cat_df); cc=(T["chart"]*math.ceil(n/max(1,len(T["chart"]))))[:n]
            fig_d=go.Figure(go.Pie(labels=cat_df["category"],values=cat_df["amount"],hole=0.58,
                marker=dict(colors=cc,line=dict(color=T["bg"],width=2)),textfont=dict(size=11,color=T["muted"]),
                hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>"))
            fig_d.update_layout(**plot_layout("Spending by Category",240))
            st.plotly_chart(fig_d, use_container_width=True)

        # Upcoming bills
        st.markdown(f"<div class='card'><span class='card-label'>Upcoming Bills</span>", unsafe_allow_html=True)
        today = date.today()
        for bill in sorted(st.session_state.bills, key=lambda b: b["due_day"]):
            days = bill["due_day"]-today.day
            if days < 0: days += 30
            bc = "ok" if days>7 else "warn" if days>2 else "bad"
            bt = f"in {days}d" if days>0 else "Today"
            st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;"
                        f"padding:0.38rem 0;border-bottom:1px solid {T['border']};font-size:0.8rem;'>"
                        f"<span style='color:{T['text']}'>{bill['name']}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:6px;'>{fmt(bill['amount'])}</span>"
                        f"<span class='{bc}'>{bt}</span></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Action items
        tips = []
        if em_months<3:       tips.append(("bad","Emergency fund under 3 months. Build cash reserves before investing."))
        elif em_months<6:     tips.append(("warn",f"Emergency fund at {em_months:.1f} months. Target 6 months ({fmt(total_exp*6)})."))
        if savings_rate<10:   tips.append(("bad",f"Savings rate {savings_rate:.1f}% is very low. Target 20%."))
        elif savings_rate<20: tips.append(("warn",f"Savings rate {savings_rate:.1f}%. Target 20% — need {fmt(total_income*0.2-cash_flow)}/mo more."))
        hi = [l for l in st.session_state.liabilities if l.get("rate",0)>10]
        if hi: tips.append(("bad",f"High-interest debt {fmt(sum(l['balance'] for l in hi))} at >10%. Prioritise payoff."))
        ob = [e for e in st.session_state.expenses if e["amount"]>e.get("budget",e["amount"])]
        if ob: tips.append(("warn",f"{len(ob)} expense(s) over budget: {', '.join(e['name'] for e in ob[:3])}."))
        if not tips: tips.append(("ok","All key ratios look healthy. Keep it up."))
        st.markdown(f"<div class='card'><span class='card-label'>Action Items</span>", unsafe_allow_html=True)
        for bc, text in tips[:4]:
            lbl = "Good" if bc=="ok" else "Note" if bc=="warn" else "Action"
            st.markdown(f"<div style='padding:0.45rem 0;border-bottom:1px solid {T['border']};font-size:0.79rem;color:{T['text']};'>"
                        f"<span class='{bc}' style='margin-right:7px;'>{lbl}</span>{text}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUDGET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t2:
    bc1, bc2 = st.columns(2, gap="large")
    with bc1:
        st.markdown(f"<div class='card'><span class='card-label'>Monthly Expenses</span>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.61rem;color:{T['muted']};padding-bottom:4px;'>Name  /  Spent  /  Budget  /  Category</div>", unsafe_allow_html=True)
        to_del = None
        for i, e in enumerate(st.session_state.expenses):
            c1,c2,c3,c4,c5 = st.columns([2.5,1.5,1.5,1.5,0.5])
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
            if nn2:
                st.session_state.expenses.append({"name":nn2,"amount":float(na2),"budget":float(nb2) if nb2>0 else float(na2),"category":nc2}); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='card'><span class='card-label'>Subscriptions — {fmt(total_sub)}/mo  /  {fmt(total_sub*12)}/yr</span>", unsafe_allow_html=True)
        del_s=None
        for i, s in enumerate(st.session_state.subscriptions):
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
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='card'><span class='card-label'>Recurring Bills</span>", unsafe_allow_html=True)
        del_b=None
        for i, bill in enumerate(st.session_state.bills):
            b1,b2,b3,b4=st.columns([2.5,1.5,1,0.5])
            with b1:
                bn=st.text_input(f"bn{i}",value=bill["name"],label_visibility="collapsed",key=f"bn_{i}")
                st.session_state.bills[i]["name"]=bn
            with b2:
                ba=st.number_input(f"ba{i}",value=float(bill["amount"]),min_value=0.0,step=10.0,label_visibility="collapsed",key=f"ba_{i}",format="%.0f")
                st.session_state.bills[i]["amount"]=ba
            with b3:
                bd=st.number_input(f"bd{i}",value=int(bill["due_day"]),min_value=1,max_value=31,label_visibility="collapsed",key=f"bd_{i}")
                st.session_state.bills[i]["due_day"]=bd
            with b4:
                if st.button("X",key=f"bld_{i}"): del_b=i
        if del_b is not None: st.session_state.bills.pop(del_b); st.rerun()
        bb1,bb2,bb3=st.columns([2.5,1.5,1])
        with bb1: bnn=st.text_input("Bill name",placeholder="e.g. Water",key="nb_n")
        with bb2: bna=st.number_input("Amount",min_value=0.0,step=10.0,key="nb_a",format="%.0f")
        with bb3: bnd=st.number_input("Due day",min_value=1,max_value=31,value=1,key="nb_d")
        if st.button("Add bill",use_container_width=True):
            if bnn: st.session_state.bills.append({"name":bnn,"amount":float(bna),"due_day":int(bnd)}); st.rerun()
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

        st.markdown(f"<div class='card'><span class='card-label'>Per-Item Budget Tracker</span>", unsafe_allow_html=True)
        for exp in sorted(st.session_state.expenses,key=lambda e: e["amount"]/max(e.get("budget",1),1),reverse=True):
            bud=exp.get("budget",exp["amount"]); p=min(100,exp["amount"]/bud*100) if bud>0 else 0
            bc="ok" if p<=85 else "warn" if p<=100 else "bad"
            br=T["red"] if p>100 else T["amber"] if p>85 else T["green"]
            st.markdown(f"<div style='margin-bottom:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:0.77rem;margin-bottom:3px;'>"
                        f"<span style='color:{T['text']}'>{exp['name']}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:4px;'>{fmt(exp['amount'])} / {fmt(bud)}</span>"
                        f"<span class='{bc}'>{p:.0f}%</span></div></div>"
                        f"<div style='background:{T['surface2']};border-radius:4px;height:5px;'>"
                        f"<div style='width:{p:.1f}%;height:100%;background:{br};border-radius:4px;'></div>"
                        f"</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INVEST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t3:
    st.markdown(f"<div class='tip'>You have <strong>{fmt(investable)}/month</strong> to invest ({invest_pct}% of income) = <strong>{fmt(investable*12)}/year</strong>.</div>", unsafe_allow_html=True)
    inv1, inv2 = st.columns(2, gap="large")
    with inv1:
        st.markdown(f"<div class='card'><span class='card-label'>Allocation — must sum to 100%</span>", unsafe_allow_html=True)
        def _sl(label, key, default):
            cur = st.session_state.get(key, default)
            val = st.slider(label, 0, 100, int(cur), 1, key=f"{key}_sl")
            st.session_state[key] = val; return val
        em_pct  = _sl("Emergency top-up",  "em_pct",  30)
        idx_pct = _sl("Index funds (ETFs)", "idx_pct", 40)
        stk_pct = _sl("Individual stocks",  "stk_pct", 20)
        cry_pct = _sl("Crypto",             "cry_pct", 10)
        if em_pct+idx_pct+stk_pct+cry_pct != 100:
            st.warning(f"Sum = {em_pct+idx_pct+stk_pct+cry_pct}% — adjust to 100%")
        st.markdown("</div>", unsafe_allow_html=True)
        labels=["Emergency","Index Funds","Stocks","Crypto"]; values=[em_pct,idx_pct,stk_pct,cry_pct]
        amounts=[investable*v/100 for v in values]
        fig_inv=go.Figure(go.Pie(
            labels=[f"{l}  {fmt(a)}/mo" for l,a in zip(labels,amounts)],values=values,hole=0.55,
            marker=dict(colors=[T["blue"],T["green"],T["amber"],T["red"]],line=dict(color=T["bg"],width=2)),
            textfont=dict(size=11,color=T["muted"])))
        fig_inv.update_layout(**plot_layout("Monthly Split",230))
        st.plotly_chart(fig_inv, use_container_width=True)

        st.markdown(f"<div class='card'><span class='card-label'>Dollar-Cost Averaging Calculator</span>", unsafe_allow_html=True)
        dca_a=st.number_input("Monthly amount ($)",min_value=0.0,value=float(investable*idx_pct/100),step=50.0,format="%.0f",key="dca_a")
        dca_y=st.slider("Period (years)",1,30,10,key="dca_y")
        dca_r=st.slider("Expected return (% p.a.)",1.0,20.0,7.0,0.5,key="dca_r")
        dca_in=dca_a*12*dca_y; dca_f=0.0
        for _ in range(dca_y): dca_f=(dca_f+dca_a*12)*(1+dca_r/100)
        st.markdown(f"<div class='row'><span>Total contributed</span><span style='color:{T['muted']}'>{fmt(dca_in)}</span></div>"
                    f"<div class='row'><span>Investment gain</span><span style='color:{T['green']}'>{fmt(dca_f-dca_in)}</span></div>"
                    f"<div class='row'><span>Final value</span><span style='color:{T['accent']};font-size:1.05rem;'>{fmt(dca_f)}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with inv2:
        yrs=list(range(21))
        def compound(r):
            v,res=0,[]
            for _ in yrs: res.append(round(v)); v=(v+investable*12)*(1+r)
            return res
        cp,mp,ap=compound(0.04),compound(0.07),compound(0.12)
        fig_p=go.Figure()
        for proj,lbl,col,dash in [(cp,"Conservative 4%",T["blue"],"dot"),(mp,"Moderate 7%",T["green"],"solid"),(ap,"Aggressive 12%",T["amber"],"dash")]:
            fig_p.add_trace(go.Scatter(x=yrs,y=proj,name=lbl,mode="lines",line=dict(color=col,width=2,dash=dash),hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
        fig_p.update_layout(**plot_layout("20-Year Growth Projection",290))
        fig_p.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_p.update_xaxes(title_text="Year")
        st.plotly_chart(fig_p, use_container_width=True)

        st.markdown(f"<div class='card'><span class='card-label'>Milestones</span>", unsafe_allow_html=True)
        bc_=T["blue"]; gc_=T["green"]; ac_=T["amber"]
        for yr in [1,3,5,10,15,20]:
            st.markdown(f"<div class='row'><span>Year {yr}</span>"
                        f"<span style='color:{bc_}'>{fmt(cp[yr])}</span>"
                        f"<span style='color:{gc_}'>{fmt(mp[yr])}</span>"
                        f"<span style='color:{ac_}'>{fmt(ap[yr])}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:0.61rem;color:{T['muted']};padding-top:5px;'>"
                    f"<span></span><span>Conservative</span><span>Moderate</span><span>Aggressive</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Goals
        st.markdown(f"<div class='card'><span class='card-label'>Financial Goals</span>", unsafe_allow_html=True)
        for i, g in enumerate(st.session_state.goals):
            rem=max(0,g["amount"]-g["saved"]); pct_g=min(100,round(g["saved"]/g["amount"]*100)) if g["amount"]>0 else 0
            mo=math.ceil(rem/investable) if investable>0 else 9999
            pc=T["red"] if g["priority"]=="High" else T["amber"] if g["priority"]=="Medium" else T["blue"]
            pb="bad" if g["priority"]=="High" else "warn" if g["priority"]=="Medium" else "blu"
            gc_col, gd_col = st.columns([11,1])
            with gc_col:
                st.markdown(f"<div style='margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid {T['border']};'>"
                            f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
                            f"<span style='font-weight:600;font-size:0.87rem;color:{T['text']};'>{g['name']}</span>"
                            f"<span class='{pb}'>{g['priority']}</span></div>"
                            f"<div style='font-size:0.74rem;color:{T['muted']};margin-bottom:6px;'>"
                            f"{fmt(g['saved'])} saved / {fmt(g['amount'])} target  "
                            f"<span style='color:{T['accent']};'>{mo} months at current rate</span></div>"
                            f"<div style='background:{T['surface2']};border-radius:5px;height:6px;'>"
                            f"<div style='width:{pct_g}%;height:100%;background:{pc};border-radius:5px;'></div></div>"
                            f"<div style='font-size:0.67rem;color:{T['muted']};margin-top:3px;'>{pct_g}% complete</div></div>", unsafe_allow_html=True)
                new_s=st.number_input(f"Saved ({g['name']})",value=float(g["saved"]),min_value=0.0,step=100.0,key=f"g_upd_{i}",format="%.0f",label_visibility="collapsed")
                if new_s!=g["saved"]: st.session_state.goals[i]["saved"]=new_s; st.rerun()
            with gd_col:
                if st.button("X",key=f"gd_{i}"): st.session_state.goals.pop(i); st.rerun()
        st.markdown("---")
        with st.expander("Add a new goal"):
            gc1,gc2,gc3,gc4=st.columns([2,1,1,1])
            with gc1: gname=st.text_input("Goal name",placeholder="e.g. Property deposit")
            with gc2: gtgt =st.number_input("Target ($)",min_value=0.0,step=1000.0,format="%.0f",key="g_tgt")
            with gc3: gsav =st.number_input("Saved ($)", min_value=0.0,step=100.0, format="%.0f",key="g_sav")
            with gc4: gpri =st.selectbox("Priority",["High","Medium","Low"])
            if st.button("Add goal",use_container_width=True):
                if gname and gtgt>0:
                    st.session_state.goals.append({"name":gname,"amount":gtgt,"saved":gsav,"priority":gpri}); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEALTH  (Net Worth + Debt + Tax + FIRE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t4:
    st.markdown(f"<div style='text-align:center;padding:1rem 0 0.9rem;'>"
                f"<div style='font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{T['muted']};margin-bottom:5px;'>Net Worth</div>"
                f"<div style='font-size:3.4rem;font-weight:800;color:{nw_col};letter-spacing:-0.03em;'>{fmt(net_worth)}</div>"
                f"<div style='font-size:0.76rem;color:{T['muted']};margin-top:4px;'>Assets {fmt(total_assets)}  /  Liabilities {fmt(total_liab)}</div>"
                f"</div>", unsafe_allow_html=True)

    w1, w2 = st.columns(2, gap="large")
    with w1:
        st.markdown(f"<div class='card'><span class='card-label'>Assets — Name / Value / Type</span>", unsafe_allow_html=True)
        del_a=None
        for i, a in enumerate(st.session_state.assets):
            a1,a2,a3,a4=st.columns([2.5,1.5,1.5,0.5])
            with a1:
                an=st.text_input(f"an{i}",value=a["name"],label_visibility="collapsed",key=f"an_{i}")
                st.session_state.assets[i]["name"]=an
            with a2:
                av=st.number_input(f"av{i}",value=float(a["value"]),min_value=0.0,step=100.0,label_visibility="collapsed",key=f"av_{i}",format="%.0f")
                st.session_state.assets[i]["value"]=av
            with a3:
                ai=ASSET_TYPES.index(a["type"]) if a["type"] in ASSET_TYPES else 0
                at_=st.selectbox(f"at{i}",ASSET_TYPES,index=ai,label_visibility="collapsed",key=f"at_{i}")
                st.session_state.assets[i]["type"]=at_
            with a4:
                if st.button("X",key=f"ad_{i}"): del_a=i
        if del_a is not None: st.session_state.assets.pop(del_a); st.rerun()
        na1,na2,na3=st.columns([2.5,1.5,1.5])
        with na1: new_an=st.text_input("Asset name",placeholder="e.g. Shares",key="naa_n")
        with na2: new_av=st.number_input("Value ($)",min_value=0.0,step=100.0,key="naa_v",format="%.0f")
        with na3: new_at=st.selectbox("Type",ASSET_TYPES,key="naa_t")
        if st.button("Add asset",use_container_width=True):
            if new_an: st.session_state.assets.append({"name":new_an,"value":float(new_av),"type":new_at}); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        df_a=pd.DataFrame(st.session_state.assets); df_a=df_a[df_a["value"]>0]
        if not df_a.empty:
            at_df=df_a.groupby("type")["value"].sum().reset_index()
            n=len(at_df); cc=(T["chart"]*math.ceil(n/max(1,len(T["chart"]))))[:n]
            fig_a=go.Figure(go.Pie(labels=at_df["type"],values=at_df["value"],hole=0.55,
                marker=dict(colors=cc,line=dict(color=T["bg"],width=2)),textfont=dict(size=11,color=T["muted"]),
                hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>"))
            fig_a.update_layout(**plot_layout("Asset Allocation",230))
            st.plotly_chart(fig_a, use_container_width=True)

        # AUS Tax
        st.markdown(f"<div class='card'><span class='card-label'>Australian Tax Estimator — FY2024-25</span>", unsafe_allow_html=True)
        gross=st.number_input("Annual gross income ($)",min_value=0.0,value=float(primary_income*12),step=1000.0,format="%.0f",key="tax_g")
        inc_med =st.checkbox("Medicare levy (2%)",value=True)
        inc_lito=st.checkbox("Apply LITO offset",value=True)
        priv_h  =st.checkbox("Private health insurance (avoids MLS surcharge)",value=False)
        tax_r=calc_tax(gross); med=gross*0.02 if inc_med else 0
        mls=gross*0.01 if (not priv_h and gross>93000 and inc_med) else 0
        lito=calc_lito(gross) if inc_lito else 0
        ttax=max(0,tax_r+med+mls-lito); net_ann=gross-ttax; eff_r=ttax/gross*100 if gross>0 else 0
        for lbl,val,col_,bold in [
            ("Gross income",fmt(gross),T["text"],False),("Income tax",f"-{fmt(tax_r)}",T["red"],False),
            ("Medicare levy",f"-{fmt(med)}",T["amber"],False),("MLS surcharge",f"-{fmt(mls)}",T["red"],mls>0),
            ("LITO offset",f"+{fmt(lito)}",T["green"],False),("Total tax",f"-{fmt(ttax)}",T["red"],True),
            ("Net annual",fmt(net_ann),T["accent"],True),("Net monthly",fmt(net_ann/12),T["accent"],True),
            ("Effective rate",f"{eff_r:.1f}%",T["amber"],True)]:
            fw="font-weight:600;" if bold else ""
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid {T['border']};font-size:0.8rem;{fw}'>"
                        f"<span style='color:{T['muted']}'>{lbl}</span><span style='color:{col_}'>{val}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with w2:
        st.markdown(f"<div class='card'><span class='card-label'>Liabilities — Name / Balance / Rate% / Type</span>", unsafe_allow_html=True)
        del_l=None
        for i, l in enumerate(st.session_state.liabilities):
            l1,l2,l3,l4,l5=st.columns([2,1.5,1,1.5,0.5])
            with l1:
                ln=st.text_input(f"ln{i}",value=l["name"],label_visibility="collapsed",key=f"ln_{i}")
                st.session_state.liabilities[i]["name"]=ln
            with l2:
                lb=st.number_input(f"lb{i}",value=float(l["balance"]),min_value=0.0,step=100.0,label_visibility="collapsed",key=f"lb_{i}",format="%.0f")
                st.session_state.liabilities[i]["balance"]=lb
            with l3:
                lr=st.number_input(f"lr{i}",value=float(l.get("rate",5.0)),min_value=0.0,max_value=99.0,step=0.1,label_visibility="collapsed",key=f"lr_{i}",format="%.1f")
                st.session_state.liabilities[i]["rate"]=lr
            with l4:
                li=LIAB_TYPES.index(l["type"]) if l["type"] in LIAB_TYPES else 0
                lt_=st.selectbox(f"lt{i}",LIAB_TYPES,index=li,label_visibility="collapsed",key=f"lt_{i}")
                st.session_state.liabilities[i]["type"]=lt_
            with l5:
                if st.button("X",key=f"ld_{i}"): del_l=i
        if del_l is not None: st.session_state.liabilities.pop(del_l); st.rerun()
        nl1,nl2,nl3,nl4=st.columns([2,1.5,1,1.5])
        with nl1: new_ln=st.text_input("Liability name",placeholder="e.g. Home Loan",key="nll_n")
        with nl2: new_lb=st.number_input("Balance ($)",min_value=0.0,step=100.0,key="nll_b",format="%.0f")
        with nl3: new_lr=st.number_input("Rate %",min_value=0.0,max_value=99.0,step=0.1,key="nll_r",format="%.1f")
        with nl4: new_lt=st.selectbox("Type",LIAB_TYPES,key="nll_t")
        if st.button("Add liability",use_container_width=True):
            if new_ln: st.session_state.liabilities.append({"name":new_ln,"balance":float(new_lb),"rate":float(new_lr),"type":new_lt,"min_payment":0.0}); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Waterfall
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
            fig_wf.update_layout(**plot_layout("Net Worth Waterfall",250))
            st.plotly_chart(fig_wf, use_container_width=True)

        # Debt tracker
        if st.session_state.liabilities:
            tdb=sum(l["balance"] for l in st.session_state.liabilities)
            avg_r=sum(l["rate"]*l["balance"] for l in st.session_state.liabilities)/tdb if tdb else 0
            ann_i=sum(l["balance"]*l.get("rate",0)/100 for l in st.session_state.liabilities)
            dm1,dm2,dm3=st.columns(3)
            dm1.metric("Total Debt",fmt(tdb)); dm2.metric("Avg Rate",f"{avg_r:.1f}%"); dm3.metric("Annual Interest",fmt(ann_i))
            extra=st.number_input("Extra monthly payment ($)",min_value=0.0,value=200.0,step=50.0,format="%.0f",key="extra_pay")
            strat=st.selectbox("Payoff strategy",["Avalanche - highest rate first (saves most)","Snowball - smallest balance first (motivating)"],key="strat")
            use_av="Avalanche" in strat
            def sim(debts, ep, av=True):
                ds=[dict(d) for d in debts if d["balance"]>0]
                for d in ds:
                    if not d.get("min_payment"): d["min_payment"]=max(d["balance"]*0.03,50)
                mo,ti,hist=0,0,[]
                while any(d["balance"]>0 for d in ds) and mo<360:
                    mo+=1
                    for d in ds:
                        if d["balance"]>0: i=d["balance"]*d.get("rate",0)/100/12; d["balance"]+=i; ti+=i
                    for d in ds:
                        if d["balance"]>0: pay=min(d["balance"],d.get("min_payment",50)); d["balance"]=max(0,d["balance"]-pay)
                    active=[d for d in ds if d["balance"]>0]
                    if active:
                        focus=min(active,key=lambda x: -x["rate"] if av else x["balance"])
                        focus["balance"]=max(0,focus["balance"]-ep)
                    hist.append({"month":mo,"total":sum(d["balance"] for d in ds)})
                    if all(d["balance"]<=0 for d in ds): break
                return mo,ti,hist
            av_mo,av_int,av_hist=sim(st.session_state.liabilities,extra,True)
            sb_mo,sb_int,sb_hist=sim(st.session_state.liabilities,extra,False)
            st.markdown(f"<div class='card'><span class='card-label'>Payoff Comparison</span>", unsafe_allow_html=True)
            green_c=T["green"]; blue_c=T["blue"]; red_c=T["red"]
            for nm,mo,interest,col_ in [("Avalanche",av_mo,av_int,green_c),("Snowball",sb_mo,sb_int,blue_c)]:
                st.markdown(f"<div class='row'><span style='color:{col_};font-weight:600;'>{nm}</span>"
                            f"<span>{mo} mo ({mo/12:.1f} yrs)</span>"
                            f"<span style='color:{red_c};'>Interest: {fmt(interest)}</span></div>", unsafe_allow_html=True)
            diff=abs(sb_int-av_int)
            if diff>0: st.markdown(f"<div style='margin-top:5px;font-size:0.79rem;color:{green_c};'>Avalanche saves {fmt(diff)} in interest</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            if av_hist and sb_hist:
                fig_debt=go.Figure()
                fig_debt.add_trace(go.Scatter(x=[h["month"] for h in av_hist],y=[h["total"] for h in av_hist],name="Avalanche",mode="lines",line=dict(color=green_c,width=2),hovertemplate="Month %{x}<br>$%{y:,.0f}<extra></extra>"))
                fig_debt.add_trace(go.Scatter(x=[h["month"] for h in sb_hist],y=[h["total"] for h in sb_hist],name="Snowball",mode="lines",line=dict(color=blue_c,width=2,dash="dash"),hovertemplate="Month %{x}<br>$%{y:,.0f}<extra></extra>"))
                fig_debt.update_layout(**plot_layout("Debt Payoff Timeline",230))
                fig_debt.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_debt.update_xaxes(title_text="Month")
                st.plotly_chart(fig_debt, use_container_width=True)

        # FIRE
        st.markdown(f"<div class='card'><span class='card-label'>FIRE Calculator (Financial Independence)</span>", unsafe_allow_html=True)
        st.caption("Save 25x annual expenses. Withdraw 4% annually without depleting the portfolio.")
        ann_exp =st.number_input("Annual living expenses ($)",min_value=0.0,value=float(total_exp*12),step=500.0,format="%.0f",key="f_exp")
        cur_port=st.number_input("Current portfolio ($)",min_value=0.0,value=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings"])),step=1000.0,format="%.0f",key="f_port")
        fire_r  =st.slider("Expected growth (% p.a.)",1.0,15.0,7.0,0.5,key="f_rate")
        lean_f=ann_exp*20; fire_t=ann_exp*25; fat_f=ann_exp*33
        acc_c=T["accent"]; amb_c=T["amber"]
        for lbl_,tgt,col_ in [("Lean FIRE  (5% withdrawal)",lean_f,blue_c),("FIRE  (4% withdrawal)",fire_t,acc_c),("Fat FIRE  (3% withdrawal)",fat_f,amb_c)]:
            p=min(100,cur_port/tgt*100) if tgt>0 else 0
            st.markdown(f"<div style='margin-bottom:10px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:0.77rem;margin-bottom:3px;'>"
                        f"<span style='color:{T['text']}'>{lbl_}</span><span style='color:{T['muted']}'>{p:.0f}%  /  {fmt(tgt)}</span></div>"
                        f"<div style='background:{T['surface2']};border-radius:5px;height:6px;'>"
                        f"<div style='width:{p:.1f}%;height:100%;background:{col_};border-radius:5px;'></div></div>"
                        f"</div>", unsafe_allow_html=True)
        fi_r=cur_port/fire_t*100 if fire_t>0 else 0
        st.markdown(f"<div style='text-align:center;margin:0.4rem 0;'><span style='font-size:2rem;font-weight:800;color:{acc_c};'>{fi_r:.0f}%</span><span style='font-size:0.7rem;color:{T['muted']};margin-left:6px;'>FI Ratio</span></div>", unsafe_allow_html=True)
        if investable>0 and fire_t>0:
            yrs_f,vals_f=[],[]; v,yr_hit=cur_port,None
            for yr in range(51):
                yrs_f.append(yr); vals_f.append(round(v))
                if v>=fire_t and yr_hit is None: yr_hit=yr
                v=(v+investable*12)*(1+fire_r/100)
            green_c2=T["green"]
            fig_fire=go.Figure()
            fig_fire.add_trace(go.Scatter(x=yrs_f,y=vals_f,name="Portfolio",mode="lines",line=dict(color=green_c2,width=2),fill="tozeroy",fillcolor=hex_to_rgba(green_c2,0.1),hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
            for lbl_,tgt,col_ in [("Lean",lean_f,blue_c),("FIRE",fire_t,amb_c),("Fat",fat_f,red_c)]:
                fig_fire.add_hline(y=tgt,line_dash="dot",line_color=col_,annotation_text=lbl_,annotation_font_color=col_)
            fig_fire.update_layout(**plot_layout("Path to Financial Independence",245))
            fig_fire.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_fire.update_xaxes(title_text="Years")
            st.plotly_chart(fig_fire, use_container_width=True)
            if yr_hit:
                st.markdown(f"<div class='tip'>FIRE in approximately <strong>{yr_hit} years</strong>. Monthly withdrawal at 4% rule: <strong>{fmt(fire_t*0.04/12)}</strong>.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REPORTS & IMPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t5:
    r1, r2 = st.columns(2, gap="large")
    now_str = datetime.now().strftime("%Y-%m-%d")

    with r1:
        st.markdown(f"<div class='card'><span class='card-label'>Export as CSV</span>", unsafe_allow_html=True)
        st.caption("Opens in Excel, Google Sheets, or Numbers. Includes expenses, assets, liabilities, goals, and transactions.")
        period_c=st.selectbox("Period",["Monthly","Weekly","Quarterly","Annual"],key="csv_p")
        csv_bytes=generate_csv(period_c)
        st.download_button(f"Download {period_c} CSV",data=csv_bytes,
            file_name=f"seralung_{period_c.lower()}_{now_str}.csv",mime="text/csv",use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='card'><span class='card-label'>Export as PDF</span>", unsafe_allow_html=True)
        if PDF_AVAILABLE:
            st.caption("Professional report with health score, expense tables, goals, and net worth summary.")
            period_p=st.selectbox("Period",["Monthly","Weekly","Quarterly","Annual"],key="pdf_p")
            pdf_bytes=generate_pdf(period_p)
            if pdf_bytes:
                st.download_button(f"Download {period_p} PDF",data=pdf_bytes,
                    file_name=f"seralung_{period_p.lower()}_{now_str}.pdf",mime="application/pdf",use_container_width=True)
        else:
            st.warning("PDF export requires fpdf2:")
            st.code("pip install fpdf2")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='card'><span class='card-label'>JSON Backup / Restore</span>", unsafe_allow_html=True)
        data_exp={
            "expenses":st.session_state.expenses,"subscriptions":st.session_state.subscriptions,
            "bills":st.session_state.bills,"assets":st.session_state.assets,
            "liabilities":st.session_state.liabilities,"goals":st.session_state.goals,
            "transactions":st.session_state.transactions,
            "settings":{"needs_pct":needs_pct,"wants_pct":wants_pct,"invest_pct":invest_pct},
            "exported_at":datetime.now().isoformat(),
        }
        st.download_button("Download backup JSON",data=json.dumps(data_exp,indent=2,default=str).encode(),
            file_name=f"seralung_backup_{now_str}.json",mime="application/json",use_container_width=True)
        json_up=st.file_uploader("Restore from JSON",type=["json"],key="json_up")
        if json_up:
            try:
                imp=json.loads(json_up.read().decode())
                if st.button("Restore data",use_container_width=True):
                    for key in ["expenses","subscriptions","bills","assets","liabilities","goals","transactions"]:
                        if key in imp: st.session_state[key]=imp[key]
                    if "settings" in imp:
                        for k,v in imp["settings"].items(): st.session_state[k]=v
                    st.success("Restored!"); st.rerun()
                st.caption(f"Preview: {len(imp.get('expenses',[]))} expenses, {len(imp.get('goals',[]))} goals")
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with r2:
        st.markdown(f"<div class='card'><span class='card-label'>Import Bank Statement CSV</span>", unsafe_allow_html=True)
        st.caption("Supports ANZ, CBA, Westpac, NAB, Macquarie, and most AUS bank exports. Transactions are auto-categorised by keyword.")
        uploaded=st.file_uploader("Drop your bank CSV here",type=["csv"],key="bank_up")
        if uploaded:
            df_tx,err=parse_bank_csv(uploaded)
            if err:
                st.error(f"Parse error: {err}")
                st.caption("Ensure your CSV has Date, Description, and Amount (or Debit/Credit) columns.")
            else:
                st.success(f"Parsed {len(df_tx)} transactions")
                df_show=df_tx.copy()
                df_show["Date"]=df_show["Date"].dt.strftime("%d %b %Y")
                df_show["Amount ($)"]=df_show["Amount"].apply(lambda x: f"+${x:,.2f}" if x>0 else f"-${abs(x):,.2f}")
                st.dataframe(df_show[["Date","Description","Amount ($)","Category"]].head(25),use_container_width=True,hide_index=True)
                cb1,cb2=st.columns(2)
                with cb1:
                    if st.button("Import as transactions",use_container_width=True):
                        recs=df_tx.to_dict("records")
                        for r in recs: r["Date"]=str(r["Date"])[:10]
                        st.session_state.transactions=recs; st.success(f"Imported {len(recs)}"); st.rerun()
                with cb2:
                    if st.button("Add debits to expenses",use_container_width=True):
                        debits=df_tx[df_tx["Amount"]<0].copy(); added=0
                        for _,row in debits.iterrows():
                            if abs(row["Amount"])>5:
                                st.session_state.expenses.append({"name":str(row["Description"])[:32],"amount":float(abs(row["Amount"])),"budget":float(abs(row["Amount"])),"category":str(row["Category"])}); added+=1
                        st.success(f"Added {added} expenses"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='card'><span class='card-label'>Supported Bank CSV Formats</span>", unsafe_allow_html=True)
        for bank,cols in [("ANZ","Date, Description, Debit, Credit, Balance"),
                          ("CBA","Date, Amount, Description, Balance"),
                          ("Westpac","Date, Amount, Description, Balance"),
                          ("NAB","Date, Amount, Description, Balance"),
                          ("Macquarie","Date, Debit, Credit, Balance"),
                          ("Generic","Any CSV with Date + Amount + Description")]:
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:0.35rem 0;border-bottom:1px solid {T['border']};font-size:0.77rem;'>"
                        f"<span style='color:{T['text']};font-weight:600;'>{bank}</span>"
                        f"<span style='color:{T['muted']};font-size:0.7rem;'>{cols}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.transactions:
            st.markdown(f"<div class='card'><span class='card-label'>Imported Transactions ({len(st.session_state.transactions)})</span>", unsafe_allow_html=True)
            df_t2=pd.DataFrame(st.session_state.transactions)
            ti2=df_t2[df_t2["Amount"]>0]["Amount"].sum() if "Amount" in df_t2.columns else 0
            to2=df_t2[df_t2["Amount"]<0]["Amount"].abs().sum() if "Amount" in df_t2.columns else 0
            tt1,tt2,tt3=st.columns(3)
            tt1.metric("Count",len(df_t2)); tt2.metric("Total in",fmt(ti2)); tt3.metric("Total out",fmt(to2))
            if "Category" in df_t2.columns and "Amount" in df_t2.columns:
                cs=df_t2[df_t2["Amount"]<0].groupby("Category")["Amount"].sum().abs().reset_index()
                if not cs.empty:
                    n=len(cs); cc=(T["chart"]*math.ceil(n/max(1,len(T["chart"]))))[:n]
                    fig_t=go.Figure(go.Bar(x=cs["Category"],y=cs["Amount"],marker_color=cc,
                        text=[fmt(v) for v in cs["Amount"]],textposition="outside",textfont=dict(color=T["text"],size=10)))
                    fig_t.update_layout(**plot_layout("Spending by Category",200))
                    fig_t.update_yaxes(tickprefix="$",tickformat=",.0f")
                    st.plotly_chart(fig_t, use_container_width=True)
            if st.button("Clear transactions",use_container_width=True):
                st.session_state.transactions=[]; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"<p style='text-align:center;color:{T['muted']};font-size:0.66rem;'>"
            "Seralung Finance  |  Educational use only. Not financial advice. "
            "Always consult a qualified financial adviser.  |  AUS Tax FY2024-25</p>", unsafe_allow_html=True)
