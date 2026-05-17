"""
Seralung Finance — Premium v2
requirements.txt:
    streamlit>=1.32  plotly>=5.18  pandas>=2.0
    fpdf2>=2.7  numpy>=1.24  requests>=2.28  supabase>=2.0
Run: streamlit run seralung_premium.py
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math, io, json, csv, requests
from datetime import datetime, date

try:
    from fpdf import FPDF; PDF_OK = True
except ImportError:
    PDF_OK = False

try:
    from db import init_supabase, get_user, restore_session, load_user_data, save_user_data, login_page, logout
    AUTH_ENABLED = True
except ImportError:
    AUTH_ENABLED = False

st.set_page_config(page_title="Seralung Finance", layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────────────────────────────
# THEMES  — Pearl · Noir · Aurora
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "Pearl": {
        "bg":"#F7F6F3","surface":"#FFFFFF","surface2":"#F2F1EE","surface3":"#ECEAE6",
        "border":"#E4E2DC","accent":"#18181B","accent2":"#3F3F46","glow":"rgba(24,24,27,0.06)",
        "text":"#18181B","muted":"#71717A","green":"#16A34A","red":"#DC2626",
        "amber":"#B45309","blue":"#1D4ED8","purple":"#6D28D9",
        "chart":["#18181B","#1D4ED8","#16A34A","#DC2626","#6D28D9","#0369A1","#BE185D"],
        "dark":False,"grad":"linear-gradient(135deg,#18181B,#52525B)",
    },
    "Noir": {
        "bg":"#09090B","surface":"#18181B","surface2":"#27272A","surface3":"#3F3F46",
        "border":"#3F3F46","accent":"#F4F4F5","accent2":"#E4E4E7","glow":"rgba(244,244,245,0.07)",
        "text":"#F4F4F5","muted":"#A1A1AA","green":"#22C55E","red":"#EF4444",
        "amber":"#F59E0B","blue":"#60A5FA","purple":"#A78BFA",
        "chart":["#F4F4F5","#60A5FA","#22C55E","#EF4444","#A78BFA","#22D3EE","#F472B6"],
        "dark":True,"grad":"linear-gradient(135deg,#F4F4F5,#A1A1AA)",
    },
    "Aurora": {
        "bg":"#080714","surface":"#0F0B24","surface2":"#17113A","surface3":"#1E164D",
        "border":"#2D2060","accent":"#8B5CF6","accent2":"#06B6D4","glow":"rgba(139,92,246,0.18)",
        "text":"#EDE9FE","muted":"#8B7EC8","green":"#10B981","red":"#F43F5E",
        "amber":"#FBBF24","blue":"#60A5FA","purple":"#C084FC",
        "chart":["#8B5CF6","#06B6D4","#10B981","#F43F5E","#FBBF24","#60A5FA","#F472B6"],
        "dark":True,"grad":"linear-gradient(135deg,#8B5CF6,#06B6D4)",
    },
}

CATEGORIES  = ["Housing","Food","Transport","Health","Insurance","Tech","Entertainment","Personal","Education","Other"]
ASSET_TYPES = ["Cash","Savings","Investments","Super","Property","Vehicle","Business","Other"]
LIAB_TYPES  = ["Mortgage","Loan","Credit","HECS","Personal","Business","Other"]
RISK_LABELS = ["Very Conservative","Conservative","Moderate","Growth","Aggressive"]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def _i(k, v):
    if k not in st.session_state: st.session_state[k] = v

_i("expenses",[
    {"name":"Rent","amount":1800.0,"budget":2000.0,"category":"Housing","freq":"Monthly"},
    {"name":"Groceries","amount":450.0,"budget":500.0,"category":"Food","freq":"Monthly"},
    {"name":"Transport","amount":250.0,"budget":300.0,"category":"Transport","freq":"Monthly"},
    {"name":"Dining","amount":350.0,"budget":300.0,"category":"Food","freq":"Monthly"},
    {"name":"Utilities","amount":180.0,"budget":220.0,"category":"Housing","freq":"Monthly"},
    {"name":"Phone","amount":85.0,"budget":85.0,"category":"Tech","freq":"Monthly"},
    {"name":"Insurance","amount":150.0,"budget":200.0,"category":"Insurance","freq":"Monthly"},
    {"name":"Entertainment","amount":120.0,"budget":150.0,"category":"Entertainment","freq":"Monthly"},
])
_i("subscriptions",[
    {"name":"Netflix","amount":18.0},{"name":"Spotify","amount":12.0},
    {"name":"Amazon Prime","amount":9.99},{"name":"Gym","amount":45.0},
])
_i("bills",[
    {"name":"Rent","amount":1800.0,"due_day":1},
    {"name":"Electricity","amount":180.0,"due_day":15},
    {"name":"Internet","amount":90.0,"due_day":20},
    {"name":"Phone","amount":85.0,"due_day":25},
])
_i("assets",[
    {"name":"Savings Account","type":"Cash","value":12000.0},
    {"name":"Super","type":"Super","value":35000.0},
    {"name":"Car","type":"Vehicle","value":18000.0},
    {"name":"ETF Portfolio","type":"Investments","value":8500.0},
])
_i("liabilities",[
    {"name":"Car Loan","type":"Loan","balance":14000.0,"rate":6.5,"min_payment":350.0},
    {"name":"Credit Card","type":"Credit","balance":2800.0,"rate":19.99,"min_payment":84.0},
    {"name":"HECS","type":"HECS","balance":18000.0,"rate":3.9,"min_payment":200.0},
])
_i("goals",[
    {"name":"Emergency Fund","target":15000.0,"saved":12000.0,"priority":"High","color":"red"},
    {"name":"Europe Trip","target":8000.0,"saved":2000.0,"priority":"Medium","color":"blue"},
    {"name":"Property Deposit","target":80000.0,"saved":25000.0,"priority":"High","color":"purple"},
])
_i("transactions",[])
_i("chat_history",[])
_i("needs_pct",50); _i("wants_pct",30); _i("invest_pct",20)
_i("em_pct",30); _i("idx_pct",40); _i("stk_pct",20); _i("cry_pct",10)
_i("risk_profile","Moderate"); _i("age",32); _i("retirement_age",65)

# Migrate old goal format: "amount" key → "target" (backward compat with saved data)
for _gi, _g in enumerate(st.session_state.get("goals", [])):
    if "amount" in _g and "target" not in _g:
        st.session_state.goals[_gi]["target"] = _g["amount"]
        del st.session_state.goals[_gi]["amount"]
    if "saved" not in _g:
        st.session_state.goals[_gi]["saved"] = 0.0

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt(n):   return f"${n:,.0f}"
def fmtk(n):  return f"${n/1000:.1f}k" if abs(n)>=1000 else fmt(n)
def pct(n):   return f"{n:.1f}%"
def to_mo(amount, freq="Monthly"):
    """Convert weekly amount to monthly equivalent."""
    return amount * 52 / 12 if freq == "Weekly" else amount

def h2r(hx, a=0.15):
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

def _p(t):
    t=str(t)
    for u,a in {'\u2014':'-','\u2013':'-','\u2018':"'",'\u2019':"'",'\u201c':'"','\u201d':'"'}.items(): t=t.replace(u,a)
    return t.encode('latin-1',errors='replace').decode('latin-1')

def auto_categorize(desc):
    d = str(desc).lower()
    rules = [
        (["rent","lease","mortgage","real estate","strata"],"Housing"),
        (["electricity","power","energy","agl","origin","simply","gas","water","council"],"Housing"),
        (["internet","nbn","optus","telstra","vodafone","tpg"],"Tech"),
        (["coles","woolworths","aldi","iga","harris farm","costco","supermarket","grocer"],"Food"),
        (["uber eats","menulog","doordash","mcdonald","kfc","subway","domino","pizza",
          "cafe","coffee","restaurant","takeaway","bakery","dining","hungry jacks"],"Food"),
        (["netflix","stan","disney","binge","foxtel","spotify","apple music","youtube","amazon prime"],"Entertainment"),
        (["gym","fitness","yoga","pilates","crossfit","anytime fitness","f45"],"Health"),
        (["pharmacy","chemist","doctor","medical","dental","hospital","medibank","bupa","ahm","nib"],"Health"),
        (["fuel","petrol","shell","bp","caltex","ampol","7-eleven"],"Transport"),
        (["uber","ola","taxi","parking","toll","myki","opal","train","bus","tram"],"Transport"),
        (["insurance","nrma","aami","racv","gio","allianz","suncorp"],"Insurance"),
        (["school","university","tafe","udemy","coursera","education","tuition"],"Education"),
        (["amazon","ebay","kmart","target","big w","myer","david jones","clothing","cotton on","h&m"],"Personal"),
    ]
    for kws, cat in rules:
        if any(k in d for k in kws): return cat
    return "Other"

def parse_bank_csv(uploaded_file):
    try:
        content = uploaded_file.read().decode("utf-8", errors="replace")
        lines = content.strip().split("\n"); hi = 0
        for i, ln in enumerate(lines):
            if any(k in ln.lower() for k in ["date","amount","description","debit","credit"]):
                hi = i; break
        df = pd.read_csv(io.StringIO("\n".join(lines[hi:])), on_bad_lines="skip", dtype=str)
        df.columns = [x.strip().lower().replace(" ","_") for x in df.columns]
        dcol = next((c for c in df.columns if "date" in c), None)
        ncol = next((c for c in df.columns if any(k in c for k in ["description","details","narration","memo","narrative"])), None)
        acol = next((c for c in df.columns if c in ["amount","net_amount"]), None)
        dbcol= next((c for c in df.columns if "debit"  in c), None)
        crcol= next((c for c in df.columns if "credit" in c), None)
        if not dcol or not ncol: return None, "Cannot find Date/Description columns."
        res = pd.DataFrame()
        res["Date"]        = pd.to_datetime(df[dcol], dayfirst=True, errors="coerce")
        res["Description"] = df[ncol].fillna("Unknown").str.strip()
        if acol:
            res["Amount"] = pd.to_numeric(df[acol].str.replace(r"[$,\s]","",regex=True), errors="coerce").fillna(0)
        elif dbcol and crcol:
            d2 = pd.to_numeric(df[dbcol].str.replace(r"[$,\s]","",regex=True), errors="coerce").fillna(0)
            c2 = pd.to_numeric(df[crcol].str.replace(r"[$,\s]","",regex=True), errors="coerce").fillna(0)
            res["Amount"] = c2 - d2
        else:
            return None, "Cannot find Amount/Debit/Credit columns."
        res["Category"] = res["Description"].apply(auto_categorize)
        res = res.dropna(subset=["Date"]); res = res[res["Amount"]!=0].sort_values("Date", ascending=False)
        return res, None
    except Exception as e:
        return None, str(e)

def generate_report_csv(period="Monthly"):
    """Generate full financial report as CSV."""
    buf = io.StringIO(); w = csv.writer(buf)
    sr = (total_income-total_exp)/total_income*100 if total_income>0 else 0
    label = f"Seralung Finance — {period} Report — {datetime.now().strftime('%B %Y')}"
    w.writerow([label]); w.writerow([f"Generated {datetime.now().strftime('%d %b %Y %H:%M')})"])
    w.writerow([])
    w.writerow(["SUMMARY"])
    for l,v in [("Health Score",f"{hs}/100"),("Income",fmt(total_income)),("Expenses",fmt(total_exp)),
                ("Savings Rate",pct(sr)),("Net Worth",fmt(net_worth)),("Cash Flow",fmt(cash_flow)),
                ("Emergency Fund",f"{em_months:.1f} months")]:
        w.writerow([l,v])
    w.writerow([])
    w.writerow(["EXPENSES","","","",""])
    w.writerow(["Name","Category","Frequency","Spent","Monthly equiv","Budget","Status"])
    for e in st.session_state.expenses:
        mo = to_mo(e["amount"],e.get("freq","Monthly"))
        bud = e.get("budget",e["amount"]); over = "OVER" if mo>bud else "OK"
        w.writerow([e["name"],e.get("category",""),e.get("freq","Monthly"),f"{e['amount']:.2f}",f"{mo:.2f}",f"{bud:.2f}",over])
    w.writerow(["Subscriptions (total)","Various","Monthly",f"{total_sub:.2f}",f"{total_sub:.2f}","",""])
    w.writerow([])
    w.writerow(["GOALS","","","","",""])
    w.writerow(["Name","Priority","Target","Saved","Progress","Remaining"])
    for g in st.session_state.goals:
        tgt = g.get("target",g.get("amount",0)); sav = g.get("saved",0)
        pg = sav/tgt*100 if tgt>0 else 0
        w.writerow([g["name"],g.get("priority",""),f"{tgt:.2f}",f"{sav:.2f}",f"{pg:.0f}%",f"{max(0,tgt-sav):.2f}"])
    w.writerow([])
    w.writerow(["ASSETS","",""]); w.writerow(["Name","Type","Value"])
    for a in st.session_state.assets: w.writerow([a["name"],a["type"],f"{a['value']:.2f}"])
    w.writerow([])
    w.writerow(["LIABILITIES","","","",""]); w.writerow(["Name","Type","Balance","Rate%","Min Payment"])
    for l in st.session_state.liabilities:
        w.writerow([l["name"],l["type"],f"{l['balance']:.2f}",f"{l.get('rate',0):.2f}",f"{l.get('min_payment',0):.2f}"])
    if st.session_state.transactions:
        w.writerow([]); w.writerow(["TRANSACTIONS","","",""])
        w.writerow(["Date","Description","Amount","Category"])
        for tx in st.session_state.transactions:
            w.writerow([tx.get("Date",""),tx.get("Description",""),f"{tx.get('Amount',0):.2f}",tx.get("Category","")])
    w.writerow([]); w.writerow(["Educational use only. Not financial advice."])
    return buf.getvalue().encode("utf-8")

def monte_carlo(init, monthly, years=25, n=200, mu=0.07, sigma=0.15):
    months=years*12; res=np.zeros((n,months+1)); res[:,0]=init
    mm,ms=mu/12,sigma/math.sqrt(12)
    for t in range(1,months+1):
        ret=np.random.normal(mm,ms,n); res[:,t]=res[:,t-1]*(1+ret)+monthly
    return res

# ─────────────────────────────────────────────────────────────────────────────
# SVG HEALTH GAUGE — no overlap, clean arc
# ─────────────────────────────────────────────────────────────────────────────
def health_gauge_svg(score, grade, surface2, muted):
    r=78; cx,cy=100,100
    circ=2*math.pi*r; half=circ/2; sl=half*score/100
    if   score>=80: col="#22C55E"
    elif score>=65: col="#3B82F6"
    elif score>=50: col="#F59E0B"
    else:           col="#EF4444"
    return f"""<div style="text-align:center;margin:0 auto;">
<svg viewBox="0 0 200 108" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:210px;display:block;margin:0 auto;">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{surface2}"
    stroke-width="13" stroke-dasharray="{half:.2f} {half:.2f}"
    transform="rotate(-180 {cx} {cy})" stroke-linecap="round"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}"
    stroke-width="13" stroke-dasharray="{sl:.2f} {circ-sl:.2f}"
    transform="rotate(-180 {cx} {cy})" stroke-linecap="round"/>
  <text x="{cx}" y="80" text-anchor="middle" font-size="38" font-weight="700"
    fill="{col}" font-family="DM Sans,Inter,sans-serif">{score}</text>
  <text x="{cx}" y="100" text-anchor="middle" font-size="11.5"
    fill="{muted}" font-family="DM Sans,Inter,sans-serif"
    letter-spacing="0.04em">{grade.upper()}</text>
</svg></div>"""

# ─────────────────────────────────────────────────────────────────────────────
# HEALTH SCORE
# ─────────────────────────────────────────────────────────────────────────────
def health_score_calc():
    score, det = 0, {}
    mexp=sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses)+sum(s["amount"] for s in st.session_state.subscriptions)
    sr=max(0,(total_income-mexp)/total_income*100) if total_income>0 else 0
    s1=min(25,sr/20*25); score+=s1
    det["Savings Rate"]={"score":s1,"max":25,"val":pct(sr),"ok":sr>=20,"desc":f"{sr:.1f}% — target 20%"}
    cash=sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
    em=cash/mexp if mexp>0 else 0
    s2=min(20,em/6*20); score+=s2
    det["Emergency Fund"]={"score":s2,"max":20,"val":f"{em:.1f} mo","ok":em>=6,"desc":f"{em:.1f} months — target 6"}
    nd=sum(l["balance"] for l in st.session_state.liabilities if l["type"]!="HECS")
    dti=nd/(total_income*12)*100 if total_income>0 else 0
    s3=max(0,20-dti*0.5); score+=s3
    det["Debt Ratio"]={"score":s3,"max":20,"val":pct(dti),"ok":dti<=36,"desc":f"{dti:.0f}% — target <36%"}
    nw=sum(a["value"] for a in st.session_state.assets)-sum(l["balance"] for l in st.session_state.liabilities)
    s4=15 if nw>0 else max(0,15+nw/10000); score+=s4
    det["Net Worth"]={"score":s4,"max":15,"val":fmt(nw),"ok":nw>0,"desc":"Positive net worth"}
    over=sum(max(0,to_mo(e["amount"],e.get("freq","Monthly"))-e.get("budget",e["amount"])) for e in st.session_state.expenses)
    s5=max(0,10-over/100); score+=s5
    det["Budget Control"]={"score":s5,"max":10,"val":fmt(over)+" over","ok":over==0,"desc":"Within all budgets"}
    s6=min(10,len(st.session_state.goals)*3.5); score+=s6
    det["Goal Progress"]={"score":s6,"max":10,"val":f"{len(st.session_state.goals)} goals","ok":len(st.session_state.goals)>=2,"desc":"Track 3+ goals"}
    return round(score), det

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  — theme + auth
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Seralung Finance")
    theme_name = st.selectbox("Theme", list(THEMES.keys()), index=0)
    T = THEMES[theme_name]
    st.divider()
    if AUTH_ENABLED:
        try:
            sb = init_supabase()
            if not get_user(): restore_session(sb)
            if get_user():
                st.markdown(f"**{get_user().email}**")
                c1,c2 = st.columns(2)
                with c1:
                    if st.button("Save", use_container_width=True):
                        if save_user_data(sb): st.success("Saved!")
                with c2:
                    if st.button("Sign out", use_container_width=True): logout(sb)
                st.divider()
        except Exception: pass
    if st.button("Reset demo data", use_container_width=True):
        keep=["sb_user","sb_access_token","sb_refresh_token","sb_client","data_loaded"]
        for k in [k for k in st.session_state if k not in keep]: del st.session_state[k]
        st.rerun()
    st.caption("Educational only. Not financial advice.")

# ─────────────────────────────────────────────────────────────────────────────
# AUTH GATE
# ─────────────────────────────────────────────────────────────────────────────
if AUTH_ENABLED:
    try:
        if not get_user():
            login_page(sb, T); st.stop()
        if not st.session_state.get("data_loaded"):
            load_user_data(sb); st.session_state["data_loaded"]=True
    except Exception: pass

# ─────────────────────────────────────────────────────────────────────────────
# T-HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def plo(title="", h=280, mg=None):
    mg=mg or dict(l=8,r=8,t=36 if title else 10,b=10)
    d=dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
           font=dict(family="DM Sans,Inter,sans-serif",color=T["muted"],size=11),
           height=h,margin=mg,
           legend=dict(font=dict(color=T["muted"],size=11),bgcolor="rgba(0,0,0,0)",borderwidth=0),
           xaxis=dict(gridcolor=h2r(T["border"],0.5),linecolor=T["border"],color=T["muted"],showgrid=True),
           yaxis=dict(gridcolor=h2r(T["border"],0.5),linecolor=T["border"],color=T["muted"],showgrid=True))
    if title: d["title"]=dict(text=title,font=dict(color=T["text"],size=13,family="DM Sans,Inter,sans-serif"))
    return d

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
is_dark = T["dark"]
btn_text = "#ffffff" if is_dark or T["accent"]!="#18181B" else "#ffffff"
input_text = T["text"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&display=swap');
:root{{
  --bg:{T['bg']};--sur:{T['surface']};--sur2:{T['surface2']};--sur3:{T['surface3']};
  --bor:{T['border']};--acc:{T['accent']};--acc2:{T['accent2']};--glow:{T['glow']};
  --tx:{T['text']};--mu:{T['muted']};
  --gr:{T['green']};--rd:{T['red']};--am:{T['amber']};--bl:{T['blue']};--pu:{T['purple']};
  --grad:{T['grad']};--rad:14px;--rads:9px;
}}
html,body,.stApp{{background:var(--bg)!important;color:var(--tx)!important;font-family:'DM Sans',sans-serif;}}
*{{box-sizing:border-box;}}
p,span,div,label,li{{color:var(--tx);}}
h1,h2,h3,h4{{color:var(--tx)!important;font-weight:600;font-family:'DM Sans',sans-serif;}}
::-webkit-scrollbar{{width:3px;height:3px;}}
::-webkit-scrollbar-thumb{{background:var(--bor);border-radius:99px;}}
[data-testid="stSidebar"]{{background:var(--sur)!important;border-right:1px solid var(--bor);}}
[data-testid="stSidebar"] *{{color:var(--tx)!important;}}
.block-container{{padding:0.9rem 1.4rem 2rem!important;max-width:none!important;}}

/* Compact vertical spacing */
[data-testid="stVerticalBlock"]>[data-testid="element-container"]{{margin-bottom:0!important;}}
[data-testid="stVerticalBlock"]>[data-testid="stHorizontalBlock"]{{margin-bottom:3px!important;}}
[data-testid="stNumberInput"]{{margin-bottom:0!important;}}
[data-testid="stTextInput"]{{margin-bottom:0!important;}}
[data-testid="stSelectbox"]{{margin-bottom:0!important;}}
div[data-testid="column"]>div[data-testid="stVerticalBlock"]>div{{margin-bottom:0!important;}}

/* Metrics */
[data-testid="metric-container"]{{background:var(--sur)!important;border:1px solid var(--bor)!important;border-radius:var(--rad)!important;padding:0.8rem 1rem!important;transition:transform .18s,box-shadow .18s;}}
[data-testid="metric-container"]:hover{{transform:translateY(-2px);box-shadow:0 6px 24px {h2r(T['accent'],0.08)};}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] *{{color:var(--mu)!important;font-size:0.65rem!important;text-transform:uppercase;letter-spacing:.08em;}}
[data-testid="metric-container"] [data-testid="stMetricValue"] *{{color:var(--tx)!important;font-weight:700!important;font-size:1.25rem!important;}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] *{{font-size:0.68rem!important;}}

/* Tabs */
[data-testid="stTabs"] [role="tab"]{{background:var(--sur2);border:1px solid var(--bor);border-radius:var(--rads);color:var(--mu)!important;font-size:0.74rem;font-weight:500;padding:0.28rem 0.7rem;margin-right:3px;transition:all .15s;}}
[data-testid="stTabs"] [role="tab"]:hover{{color:var(--tx)!important;background:var(--sur3);}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{{background:var(--acc)!important;color:#fff!important;border-color:var(--acc)!important;font-weight:600;}}
[data-testid="stTabs"] [role="tablist"]{{border-bottom:1px solid var(--bor);padding-bottom:.5rem;flex-wrap:wrap;gap:3px;}}

/* Inputs */
label,[data-testid="stWidgetLabel"]{{color:var(--tx)!important;font-size:0.76rem!important;}}
[data-testid="stNumberInput"] input,[data-testid="stTextInput"] input,textarea{{
  background:var(--sur2)!important;border:1px solid var(--bor)!important;
  border-radius:var(--rads)!important;color:var(--tx)!important;font-size:0.83rem!important;
  padding:0.3rem 0.6rem!important;
}}
[data-testid="stNumberInput"] input:focus,[data-testid="stTextInput"] input:focus{{border-color:var(--acc)!important;outline:none!important;box-shadow:0 0 0 2px var(--glow)!important;}}
[data-testid="stSelectbox"]>div>div{{background:var(--sur2)!important;border:1px solid var(--bor)!important;color:var(--tx)!important;border-radius:var(--rads)!important;font-size:0.83rem!important;}}
[data-testid="stSelectbox"] span{{color:var(--tx)!important;}}
[data-baseweb="slider"] [role="slider"]{{background:var(--acc)!important;border-color:var(--acc)!important;}}
[data-testid="stCheckbox"] span{{color:var(--tx)!important;}}

/* Buttons */
.stButton>button{{background:var(--acc)!important;border:none!important;border-radius:var(--rads)!important;color:#fff!important;font-weight:600!important;font-family:'DM Sans',sans-serif!important;font-size:0.8rem!important;transition:all .16s;letter-spacing:.01em;}}
.stButton>button:hover{{opacity:.85!important;transform:translateY(-1px);box-shadow:0 4px 16px var(--glow);}}
.stDownloadButton>button{{background:var(--sur2)!important;color:var(--tx)!important;border:1px solid var(--bor)!important;box-shadow:none!important;}}
.stDownloadButton>button:hover{{border-color:var(--acc)!important;}}

/* Expander / file uploader */
[data-testid="stExpander"]{{background:var(--sur)!important;border:1px solid var(--bor)!important;border-radius:var(--rad)!important;}}
[data-testid="stExpander"] summary *{{color:var(--tx)!important;}}
[data-testid="stFileUploader"]{{background:var(--sur2)!important;border:2px dashed var(--bor)!important;border-radius:var(--rad)!important;}}
[data-testid="stAlert"] div{{color:var(--tx)!important;}}
hr{{border-color:var(--bor)!important;margin:.6rem 0!important;}}
[data-testid="stRadio"] label span{{color:var(--tx)!important;}}

/* Custom classes */
.card{{background:var(--sur);border:1px solid var(--bor);border-radius:var(--rad);padding:1rem 1.2rem;margin-bottom:.8rem;}}
.card-sm{{background:var(--sur);border:1px solid var(--bor);border-radius:var(--rad);padding:.7rem 1rem;margin-bottom:.5rem;}}
.clabel{{font-size:.59rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--mu);margin-bottom:.6rem;display:block;}}
.crow{{display:flex;justify-content:space-between;align-items:center;padding:.38rem 0;border-bottom:1px solid var(--bor);font-size:.8rem;}}
.crow:last-child{{border-bottom:none;font-weight:600;}}
.tip{{background:{h2r(T['accent'],0.07)};border-left:3px solid var(--acc);border-radius:0 var(--rads) var(--rads) 0;padding:.55rem .9rem;font-size:.79rem;line-height:1.55;margin-bottom:.7rem;}}
.tip b,.tip strong{{color:var(--acc);}}
.pbar{{background:var(--sur2);border-radius:99px;height:6px;overflow:hidden;margin:.25rem 0;}}
.pfill{{height:100%;border-radius:99px;transition:width .4s ease;}}
.bd{{display:inline-block;padding:2px 7px;border-radius:5px;font-size:.59rem;font-weight:700;letter-spacing:.04em;}}
.ok {{background:{h2r(T['green'],.14)};color:{T['green']};border:1px solid {h2r(T['green'],.3)};}}
.warn{{background:{h2r(T['amber'],.14)};color:{T['amber']};border:1px solid {h2r(T['amber'],.3)};}}
.bad {{background:{h2r(T['red'],.14)};color:{T['red']};border:1px solid {h2r(T['red'],.3)};}}
.blu {{background:{h2r(T['blue'],.14)};color:{T['blue']};border:1px solid {h2r(T['blue'],.3)};}}
.pur {{background:{h2r(T['purple'],.14)};color:{T['purple']};border:1px solid {h2r(T['purple'],.3)};}}
.grd{{color:var(--acc);font-weight:800;}}
.income-bar{{background:var(--sur);border:1px solid var(--bor);border-radius:var(--rad);padding:.75rem 1.1rem .5rem;margin-bottom:.75rem;}}
.chat-user{{background:var(--acc);color:#fff;border-radius:14px 14px 4px 14px;padding:.6rem .9rem;font-size:.8rem;margin:.35rem 0;display:inline-block;max-width:88%;float:right;clear:both;line-height:1.5;}}
.chat-ai{{background:var(--sur2);color:var(--tx);border-radius:14px 14px 14px 4px;padding:.6rem .9rem;font-size:.8rem;margin:.35rem 0;display:inline-block;max-width:92%;float:left;clear:both;line-height:1.55;border:1px solid var(--bor);}}
.chat-wrap::after{{content:'';display:table;clear:both;}}
@media(max-width:768px){{
  .block-container{{padding:.5rem .5rem 2rem!important;}}
  [data-testid="stTabs"] [role="tab"]{{font-size:.67rem;padding:.22rem .42rem;}}
  .card{{padding:.7rem .8rem;}}
  h1{{font-size:1.15rem!important;}}
}}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
hc1,hc2=st.columns([3,1])
with hc1:
    st.markdown(f"<h1 style='margin:0;font-size:1.6rem;letter-spacing:-.03em;'>"
                f"<span class='grd'>Seralung Finance</span></h1>"
                f"<p style='color:{T['muted']};font-size:.72rem;margin:1px 0 .6rem;'>Track. Spend. Build. · AUD</p>",
                unsafe_allow_html=True)
with hc2:
    st.markdown(f"<div style='text-align:right;padding-top:.3rem;'>"
                f"<div style='font-size:.64rem;color:{T['muted']};'>{datetime.now().strftime('%A')}</div>"
                f"<div style='font-size:.85rem;font-weight:600;color:{T['text']};'>{datetime.now().strftime('%d %b %Y')}</div>"
                f"</div>",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INCOME — always visible
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"<div class='income-bar'><span class='clabel'>Income & Budget Rule</span></div>",unsafe_allow_html=True)
c1,c2,c3,c4,c5=st.columns([2,2,1,1,1])
with c1: primary_income=st.number_input("Take home income /mo",min_value=0.0,value=6000.0,step=100.0,format="%.0f",key="pi")
with c2: other_income  =st.number_input("Other income /mo",min_value=0.0,value=500.0,step=50.0,format="%.0f",key="oi")
with c3:
    needs_pct=st.number_input("Needs %",0,100,st.session_state.get("needs_pct",50),1,key="np_n")
    st.session_state["needs_pct"]=needs_pct
with c4:
    wants_pct=st.number_input("Wants %",0,100,st.session_state.get("wants_pct",30),1,key="wp_n")
    st.session_state["wants_pct"]=wants_pct
with c5:
    invest_pct=st.number_input("Save & Invest %",0,100,st.session_state.get("invest_pct",20),1,key="ip_n")
    st.session_state["invest_pct"]=invest_pct

total_income=primary_income+other_income
psum=needs_pct+wants_pct+invest_pct
if psum!=100:
    st.warning(f"Percentages sum to {psum}% — adjust to reach 100%.")
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# DERIVED VALUES (real calculations)
# ─────────────────────────────────────────────────────────────────────────────
total_sub   = sum(s["amount"] for s in st.session_state.subscriptions)
total_exp   = sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses)+total_sub
total_assets= sum(a["value"] for a in st.session_state.assets)
total_liab  = sum(l["balance"] for l in st.session_state.liabilities)
net_worth   = total_assets-total_liab
investable  = total_income*invest_pct/100
needs_budget= total_income*needs_pct/100
wants_budget= total_income*wants_pct/100
cash_flow   = total_income-total_exp
savings_rate= cash_flow/total_income*100 if total_income>0 else 0
cash_assets = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
em_months   = cash_assets/total_exp if total_exp>0 else 0
nw_col      = T["green"] if net_worth>=0 else T["red"]
hs, hs_det  = health_score_calc()
if   hs>=80: sc_col,grade=T["green"],"Excellent"
elif hs>=65: sc_col,grade=T["blue"],"Good"
elif hs>=50: sc_col,grade=T["amber"],"Fair"
elif hs>=35: sc_col,grade=T["red"],"Needs Work"
else:        sc_col,grade=T["red"],"Critical"

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
t_tabs=st.tabs(["Overview","Budget","Goals","Invest & Risk","Insights","AI Assistant","Pro"])
t1,t2,t3,t4,t5,t6,t7=t_tabs

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t1:
    g1,m1,m2,m3,m4,m5=st.columns([1.3,1,1,1,1,1])
    with g1:
        st.markdown(f"<div class='card' style='border-color:{sc_col};padding:.7rem .9rem;'>"
                    f"<span class='clabel' style='text-align:center;display:block;'>Financial Health</span>"
                    f"{health_gauge_svg(hs,grade,T['surface2'],T['muted'])}"
                    f"</div>",unsafe_allow_html=True)
    with m1: st.metric("Net Worth",    fmtk(net_worth),  "Positive" if net_worth>=0 else "Negative", delta_color="normal" if net_worth>=0 else "inverse")
    with m2: st.metric("Cash Flow",    fmt(cash_flow),   "Surplus"  if cash_flow>=0 else "Deficit",  delta_color="normal" if cash_flow>=0 else "inverse")
    with m3: st.metric("Savings Rate", pct(savings_rate),"Target 20%", delta_color="normal" if savings_rate>=20 else "inverse")
    with m4: st.metric("Emergency",    f"{em_months:.1f} mo","Safe" if em_months>=6 else "Low",       delta_color="normal" if em_months>=6 else "inverse")
    with m5: st.metric("Investable",   fmt(investable),  f"{invest_pct}% of income",                  delta_color="off")

    st.markdown("<div style='margin:.5rem 0;'></div>",unsafe_allow_html=True)
    ov1,ov2=st.columns(2,gap="large")
    with ov1:
        # 50/30/20 bars
        st.markdown(f"<div class='card'><span class='clabel'>Budget Rule — {needs_pct}/{wants_pct}/{invest_pct}</span>",unsafe_allow_html=True)
        # Categorise expenses into needs/wants by category
        needs_cats={"Housing","Transport","Health","Insurance","Education"}
        needs_actual=sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses if e.get("category","Other") in needs_cats)
        wants_actual=sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses if e.get("category","Other") not in needs_cats)+total_sub
        for lbl,actual,budget,col in [("Needs",needs_actual,needs_budget,T["blue"]),
                                       ("Wants",wants_actual,wants_budget,T["amber"]),
                                       ("Save & Invest",investable,investable,T["green"])]:
            p=min(100,actual/budget*100) if budget>0 else 0
            bc="ok" if p<=85 else "warn" if p<=100 else "bad"
            br=T["red"] if p>100 else col
            st.markdown(f"<div style='margin-bottom:10px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.77rem;margin-bottom:3px;'>"
                        f"<span>{lbl}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:5px;'>{fmt(actual)}/{fmt(budget)}</span>"
                        f"<span class='bd {bc}'>{p:.0f}%</span></div></div>"
                        f"<div class='pbar'><div class='pfill' style='width:{p:.1f}%;background:{br};'></div></div>"
                        f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Health pillars
        st.markdown(f"<div class='card'><span class='clabel'>Score Breakdown</span>",unsafe_allow_html=True)
        for name,d in hs_det.items():
            p=d["score"]/d["max"]*100
            bc="ok" if p>=70 else "warn" if p>=40 else "bad"
            br=T["green"] if p>=70 else T["amber"] if p>=40 else T["red"]
            st.markdown(f"<div style='margin-bottom:7px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.76rem;margin-bottom:2px;'>"
                        f"<span>{name}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:4px;font-size:.7rem;'>{d['desc']}</span>"
                        f"<span class='bd {bc}'>{d['score']:.0f}/{d['max']}</span></div></div>"
                        f"<div class='pbar'><div class='pfill' style='width:{p:.1f}%;background:{br};'></div></div>"
                        f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    with ov2:
        # Spending donut
        df_e=pd.DataFrame(st.session_state.expenses)
        df_e["mo_amount"]=df_e.apply(lambda r:to_mo(r["amount"],r.get("freq","Monthly")),axis=1)
        df_e=df_e[df_e["mo_amount"]>0]
        if not df_e.empty:
            cat_df=df_e.groupby("category")["mo_amount"].sum().reset_index()
            n=len(cat_df); cc=(T["chart"]*math.ceil(n/max(1,len(T["chart"]))))[:n]
            fig_d=go.Figure(go.Pie(labels=cat_df["category"],values=cat_df["mo_amount"],hole=0.6,
                marker=dict(colors=cc,line=dict(color=T["bg"],width=2)),
                textfont=dict(size=11,color=T["muted"]),
                hovertemplate="%{label}<br>$%{value:,.0f}/mo<br>%{percent}<extra></extra>"))
            fig_d.add_annotation(text=f"<b>{fmt(total_exp)}</b><br><span style='font-size:10px'>/ mo</span>",
                x=0.5,y=0.5,showarrow=False,font=dict(color=T["text"],size=14,family="DM Sans"))
            fig_d.update_layout(**plo("Spending by Category",230))
            st.plotly_chart(fig_d,use_container_width=True,config={"displayModeBar":False})

        # Upcoming bills
        today=date.today()
        st.markdown(f"<div class='card'><span class='clabel'>Upcoming Bills</span>",unsafe_allow_html=True)
        for bill in sorted(st.session_state.bills,key=lambda b:b["due_day"]):
            days=bill["due_day"]-today.day
            if days<0: days+=30
            bc="ok" if days>7 else "warn" if days>2 else "bad"
            bt="Today" if days==0 else f"in {days}d"
            st.markdown(f"<div class='crow'><span>{bill['name']}</span>"
                        f"<div><span style='color:{T['muted']};margin-right:7px;'>{fmt(bill['amount'])}</span>"
                        f"<span class='bd {bc}'>{bt}</span></div></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Smart insights
        tips=[]
        if em_months<3:       tips.append(("bad","Emergency fund critical — under 3 months. Build cash before everything else."))
        elif em_months<6:     tips.append(("warn",f"Emergency fund at {em_months:.1f} months. Target {fmt(total_exp*6)}."))
        if savings_rate<10:   tips.append(("bad",f"Savings rate {savings_rate:.1f}% is dangerously low. Target 20%."))
        elif savings_rate<20: tips.append(("warn",f"Savings rate {savings_rate:.1f}%. Need {fmt(total_income*0.2-cash_flow)}/mo more."))
        hi=[l for l in st.session_state.liabilities if l.get("rate",0)>15]
        if hi: tips.append(("bad",f"High-interest debt {fmt(sum(l['balance'] for l in hi))} at >15% APR. Prioritise payoff."))
        ob=[e for e in st.session_state.expenses if to_mo(e["amount"],e.get("freq","Monthly"))>e.get("budget",e["amount"])]
        if ob: tips.append(("warn",f"{len(ob)} expense(s) over budget: {', '.join(e['name'] for e in ob[:3])}."))
        if total_sub>150: tips.append(("warn",f"Subscriptions {fmt(total_sub)}/mo = {fmt(total_sub*12)}/yr. Review them."))
        if not tips: tips.append(("ok","All key ratios are healthy. Great financial discipline."))
        st.markdown(f"<div class='card'><span class='clabel'>Action Items</span>",unsafe_allow_html=True)
        for bc,text in tips[:5]:
            lbl="Good" if bc=="ok" else "Note" if bc=="warn" else "Act Now"
            st.markdown(f"<div style='padding:.4rem 0;border-bottom:1px solid {T['border']};font-size:.78rem;'>"
                        f"<span class='bd {bc}' style='margin-right:7px;'>{lbl}</span>{text}</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUDGET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t2:
    bc1,bc2=st.columns(2,gap="large")
    with bc1:
        st.markdown(f"<div class='card'><span class='clabel'>Expenses — Name / Amount / Budget / Freq / Category</span>",unsafe_allow_html=True)
        to_del=None
        for i,e in enumerate(st.session_state.expenses):
            c1,c2,c3,c4,c5,c6=st.columns([2.2,1.3,1.3,0.9,1.5,0.4])
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
                fi=["Monthly","Weekly"].index(e.get("freq","Monthly"))
                nf=st.selectbox(f"f{i}",["Monthly","Weekly"],index=fi,label_visibility="collapsed",key=f"ef_{i}")
                st.session_state.expenses[i]["freq"]=nf
            with c5:
                ic=CATEGORIES.index(e.get("category","Other")) if e.get("category","Other") in CATEGORIES else 0
                nc=st.selectbox(f"c{i}",CATEGORIES,index=ic,label_visibility="collapsed",key=f"ec_{i}")
                st.session_state.expenses[i]["category"]=nc
            with c6:
                if st.button("✕",key=f"ed_{i}",help="Delete"): to_del=i
        if to_del is not None: st.session_state.expenses.pop(to_del); st.rerun()
        st.markdown(f"<div style='font-size:.6rem;color:{T['muted']};padding:2px 0 5px;'>Name · Amount · Budget · Freq · Category</div>",unsafe_allow_html=True)
        r1,r2,r3,r4,r5=st.columns([2.2,1.3,1.3,0.9,1.5])
        with r1: nn2=st.text_input("Name",placeholder="e.g. Groceries",key="ne_n")
        with r2: na2=st.number_input("Amount",min_value=0.0,step=10.0,key="ne_a",format="%.0f")
        with r3: nb2=st.number_input("Budget",min_value=0.0,step=10.0,key="ne_b",format="%.0f")
        with r4: nf2=st.selectbox("Freq",["Monthly","Weekly"],key="ne_f",label_visibility="collapsed")
        with r5: nc2=st.selectbox("Cat",CATEGORIES,key="ne_c",label_visibility="collapsed")
        if st.button("Add expense",use_container_width=True):
            if nn2: st.session_state.expenses.append({"name":nn2,"amount":float(na2),"budget":float(nb2) if nb2>0 else float(na2),"category":nc2,"freq":nf2}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

        # Subscriptions
        st.markdown(f"<div class='card'><span class='clabel'>Subscriptions — {fmt(total_sub)}/mo · {fmt(total_sub*12)}/yr</span>",unsafe_allow_html=True)
        ds=None
        for i,s in enumerate(st.session_state.subscriptions):
            s1,s2,s3=st.columns([3,1.5,0.4])
            with s1:
                sn=st.text_input(f"sn{i}",value=s["name"],label_visibility="collapsed",key=f"sn_{i}")
                st.session_state.subscriptions[i]["name"]=sn
            with s2:
                sa=st.number_input(f"sa{i}",value=float(s["amount"]),min_value=0.0,step=.5,label_visibility="collapsed",key=f"sa_{i}",format="%.2f")
                st.session_state.subscriptions[i]["amount"]=sa
            with s3:
                if st.button("✕",key=f"sd_{i}"): ds=i
        if ds is not None: st.session_state.subscriptions.pop(ds); st.rerun()
        ss1,ss2=st.columns([3,1.5])
        with ss1: snn=st.text_input("Service",placeholder="e.g. Netflix",key="ns_n")
        with ss2: sna=st.number_input("$/mo",min_value=0.0,step=.5,key="ns_a",format="%.2f")
        if st.button("Add subscription",use_container_width=True):
            if snn: st.session_state.subscriptions.append({"name":snn,"amount":float(sna)}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

    with bc2:
        # Spent vs budget chart
        if st.session_state.expenses:
            df2=pd.DataFrame(st.session_state.expenses)
            df2["mo_amt"]=df2.apply(lambda r:to_mo(r["amount"],r.get("freq","Monthly")),axis=1)
            cat_s=df2.groupby("category").agg({"mo_amt":"sum","budget":"sum"}).reset_index()
            fig_c=go.Figure()
            fig_c.add_trace(go.Bar(name="Budget",x=cat_s["category"],y=cat_s["budget"],
                marker_color=h2r(T["green"],.3),marker_line=dict(color=T["green"],width=1.5)))
            fig_c.add_trace(go.Bar(name="Spent",x=cat_s["category"],y=cat_s["mo_amt"],
                marker_color=T["accent"],
                text=[fmt(v) for v in cat_s["mo_amt"]],textposition="outside",textfont=dict(color=T["text"],size=9)))
            fig_c.update_layout(**plo("Spent vs Budget (monthly)",250)); fig_c.update_layout(barmode="overlay")
            st.plotly_chart(fig_c,use_container_width=True,config={"displayModeBar":False})

        # Per-item tracker
        st.markdown(f"<div class='card'><span class='clabel'>Per-Item Budget Tracker</span>",unsafe_allow_html=True)
        for exp in sorted(st.session_state.expenses,key=lambda e:to_mo(e["amount"],e.get("freq","Monthly"))/max(e.get("budget",1),1),reverse=True):
            mo_amt=to_mo(exp["amount"],exp.get("freq","Monthly"))
            bud=exp.get("budget",exp["amount"]); p=min(100,mo_amt/bud*100) if bud>0 else 0
            bc="ok" if p<=85 else "warn" if p<=100 else "bad"
            br=T["red"] if p>100 else T["amber"] if p>85 else T["green"]
            freq_label=f" ({exp.get('freq','Mo')[0:2]})" if exp.get("freq","Monthly")=="Weekly" else ""
            st.markdown(f"<div style='margin-bottom:7px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.76rem;margin-bottom:2px;'>"
                        f"<span>{exp['name']}<span style='color:{T['muted']};font-size:.65rem;'>{freq_label}</span></span>"
                        f"<div><span style='color:{T['muted']};margin-right:4px;'>{fmt(mo_amt)}/{fmt(bud)}</span>"
                        f"<span class='bd {bc}'>{p:.0f}%</span></div></div>"
                        f"<div class='pbar'><div class='pfill' style='width:{p:.1f}%;background:{br};'></div></div>"
                        f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Bills
        st.markdown(f"<div class='card'><span class='clabel'>Recurring Bills</span>",unsafe_allow_html=True)
        db=None
        for i,bill in enumerate(st.session_state.bills):
            b1,b2,b3,b4=st.columns([2.5,1.5,0.9,0.4])
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
                if st.button("✕",key=f"bld_{i}"): db=i
        if db is not None: st.session_state.bills.pop(db); st.rerun()
        bb1,bb2,bb3=st.columns([2.5,1.5,0.9])
        with bb1: bnn=st.text_input("Bill name",placeholder="e.g. Water",key="nb_n")
        with bb2: bna=st.number_input("Amount",min_value=0.0,step=10.0,key="nb_a",format="%.0f")
        with bb3: bnd=st.number_input("Day",min_value=1,max_value=31,value=1,key="nb_d")
        if st.button("Add bill",use_container_width=True):
            if bnn: st.session_state.bills.append({"name":bnn,"amount":float(bna),"due_day":int(bnd)}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

    # ── Import & Export (bottom of Budget tab, full width) ──────────────────────
    with st.expander("Import Bank Statement  /  Export Report", expanded=False):
        imp_col, exp_col = st.columns(2, gap="large")
        with imp_col:
            st.markdown(f"<span class='clabel'>Import bank statement CSV</span>", unsafe_allow_html=True)
            st.caption("Supports ANZ, CBA, Westpac, NAB, Macquarie, and most AUS banks. Transactions are auto-categorised.")
            bank_file = st.file_uploader("Drop CSV here", type=["csv"], key="bank_up")
            if bank_file:
                df_tx, err = parse_bank_csv(bank_file)
                if err:
                    st.error(f"Parse error: {err}")
                else:
                    st.success(f"Found {len(df_tx)} transactions")
                    df_show = df_tx.copy()
                    df_show["Date"] = df_show["Date"].dt.strftime("%d %b %Y")
                    df_show["Amt"] = df_show["Amount"].apply(lambda x: f"+${x:,.2f}" if x>=0 else f"-${abs(x):,.2f}")
                    st.dataframe(df_show[["Date","Description","Amt","Category"]].head(30), use_container_width=True, hide_index=True)
                    ic1, ic2 = st.columns(2)
                    with ic1:
                        if st.button("Save as transactions", use_container_width=True, key="imp_tx"):
                            recs = df_tx.to_dict("records")
                            for r in recs: r["Date"] = str(r["Date"])[:10]
                            st.session_state.transactions = recs
                            st.success(f"Saved {len(recs)} transactions"); st.rerun()
                    with ic2:
                        if st.button("Add debits to expenses", use_container_width=True, key="imp_exp"):
                            debits = df_tx[df_tx["Amount"] < 0].copy(); added = 0
                            for _, row in debits.iterrows():
                                if abs(row["Amount"]) > 5:
                                    st.session_state.expenses.append({
                                        "name": str(row["Description"])[:32], "amount": float(abs(row["Amount"])),
                                        "budget": float(abs(row["Amount"])), "category": str(row["Category"]), "freq": "Monthly"
                                    }); added += 1
                            st.success(f"Added {added} expenses"); st.rerun()

        with exp_col:
            st.markdown(f"<span class='clabel'>Export financial report</span>", unsafe_allow_html=True)
            rp = st.selectbox("Report period", ["Monthly","Weekly","Quarterly","Annual"], key="rp_period")
            now_str = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                f"Download {rp} CSV Report",
                data=generate_report_csv(rp),
                file_name=f"seralung_{rp.lower()}_{now_str}.csv",
                mime="text/csv", use_container_width=True
            )
            st.markdown(f"<div style='font-size:.72rem;color:{T['muted']};margin-top:.3rem;line-height:1.6;'>"
                        f"Includes: expenses, goals, assets, liabilities, net worth, and imported transactions.</div>",
                        unsafe_allow_html=True)
            if st.session_state.transactions:
                st.markdown(f"<div style='margin-top:.5rem;font-size:.75rem;'>"
                            f"<span class='bd ok'>{len(st.session_state.transactions)} transactions loaded</span></div>",
                            unsafe_allow_html=True)
                if st.button("Clear transactions", key="clr_tx", use_container_width=True):
                    st.session_state.transactions = []; st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOALS  — dedicated tab
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t3:
    # Summary metrics
    total_target=sum(g.get("target",g.get("amount",0)) for g in st.session_state.goals)
    total_saved_g=sum(g.get("saved",0) for g in st.session_state.goals)
    total_remaining=max(0,total_target-total_saved_g)
    overall_pct=total_saved_g/total_target*100 if total_target>0 else 0
    gm1,gm2,gm3,gm4=st.columns(4)
    gm1.metric("Total Targets",fmt(total_target))
    gm2.metric("Total Saved",fmt(total_saved_g))
    gm3.metric("Remaining",fmt(total_remaining))
    gm4.metric("Overall Progress",pct(overall_pct))
    st.markdown("<div style='margin:.5rem 0;'></div>",unsafe_allow_html=True)

    gc1,gc2=st.columns([1.6,1],gap="large")
    with gc1:
        del_g=None
        GOAL_COLORS={"red":T["red"],"blue":T["blue"],"green":T["green"],"purple":T["purple"],"amber":T["amber"]}
        for i,g in enumerate(st.session_state.goals):
            rem=max(0,g.get("target",g.get("amount",0))-g.get("saved",0))
            pg=min(100,g.get("saved",0)/g.get("target",g.get("amount",1))*100) if g.get("target",g.get("amount",0))>0 else 0
            # Real time-to-goal: how many months at current save rate
            if investable>0 and rem>0:
                mo_to_goal=math.ceil(rem/investable)
                eta=f"{mo_to_goal} mo" if mo_to_goal<24 else f"{mo_to_goal//12} yr {mo_to_goal%12} mo"
            else: eta="Set invest amount"
            col_key=g.get("color","blue"); col_hex=GOAL_COLORS.get(col_key,T["blue"])
            pb_dict={"High":"bad","Medium":"warn","Low":"blu"}
            pb=pb_dict.get(g.get("priority","Medium"),"blu")
            gh,gd=st.columns([12,1])
            with gh:
                st.markdown(f"<div class='card' style='border-left:3px solid {col_hex};border-radius:0 {14}px {14}px 0;padding:.9rem 1.1rem;margin-bottom:.5rem;'>"
                            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;'>"
                            f"<span style='font-weight:600;font-size:.92rem;'>{g['name']}</span>"
                            f"<div><span class='bd {pb}' style='margin-right:6px;'>{g.get('priority','Medium')}</span>"
                            f"<span style='font-size:.72rem;color:{T['muted']};'>ETA: {eta}</span></div></div>"
                            f"<div style='display:flex;justify-content:space-between;font-size:.75rem;color:{T['muted']};margin-bottom:6px;'>"
                            f"<span>{fmt(g['saved'])} saved of {fmt(g.get("target",g.get("amount",0)))} target</span>"
                            f"<span style='color:{col_hex};font-weight:600;'>{pg:.0f}% done</span></div>"
                            f"<div class='pbar' style='height:8px;'><div class='pfill' style='width:{pg:.1f}%;background:{col_hex};'></div></div>"
                            f"<div style='font-size:.7rem;color:{T['muted']};margin-top:4px;'>{fmt(rem)} remaining · at {fmt(investable)}/mo investable</div>"
                            f"</div>",unsafe_allow_html=True)
                # Update saved amount
                new_s=st.number_input(f"Update saved ({g['name']})",value=float(g["saved"]),min_value=0.0,max_value=float(g.get("target",g.get("amount",0))),step=100.0,key=f"gupd_{i}",format="%.0f",label_visibility="collapsed")
                if new_s!=g["saved"]: st.session_state.goals[i]["saved"]=new_s; st.rerun()
            with gd:
                st.markdown("<div style='margin-top:.6rem;'></div>",unsafe_allow_html=True)
                if st.button("✕",key=f"gd_{i}"): del_g=i
        if del_g is not None: st.session_state.goals.pop(del_g); st.rerun()

    with gc2:
        # Add goal
        st.markdown(f"<div class='card'><span class='clabel'>Add New Goal</span>",unsafe_allow_html=True)
        gname =st.text_input("Goal name",placeholder="e.g. House deposit",key="g_name")
        gtgt  =st.number_input("Target amount ($)",min_value=0.0,step=1000.0,format="%.0f",key="g_tgt")
        gsaved=st.number_input("Already saved ($)",min_value=0.0,step=100.0,format="%.0f",key="g_sav")
        gpri  =st.selectbox("Priority",["High","Medium","Low"],key="g_pri")
        gcol  =st.selectbox("Colour",["blue","green","red","purple","amber"],key="g_col")
        if st.button("Add goal",use_container_width=True,key="add_goal"):
            if gname and gtgt>0:
                st.session_state.goals.append({"name":gname,"target":float(gtgt),"saved":float(gsaved),"priority":gpri,"color":gcol})
                st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

        # Goal allocation
        if st.session_state.goals and investable>0:
            st.markdown(f"<div class='card'><span class='clabel'>Smart Allocation ({fmt(investable)}/mo available)</span>",unsafe_allow_html=True)
            high_goals=[g for g in st.session_state.goals if g.get("priority")=="High" and g.get("saved",0)<g.get("target",g.get("amount",0))]
            med_goals =[g for g in st.session_state.goals if g.get("priority")=="Medium" and g.get("saved",0)<g.get("target",g.get("amount",0))]
            low_goals =[g for g in st.session_state.goals if g.get("priority")=="Low" and g.get("saved",0)<g.get("target",g.get("amount",0))]
            total_g=len([g for g in st.session_state.goals if g.get("saved",0)<g.get("target",g.get("amount",0))])
            alloc_pcts={"High":.6,"Medium":.3,"Low":.1}
            rem_invest=investable
            for label,goals,ap in [("High priority",high_goals,0.6),("Medium priority",med_goals,0.3),("Low priority",low_goals,0.1)]:
                if goals:
                    pool=investable*ap
                    per=pool/len(goals)
                    st.markdown(f"<div style='font-size:.73rem;font-weight:600;color:{T['text']};margin:.4rem 0 .2rem;'>{label}</div>",unsafe_allow_html=True)
                    for g in goals:
                        rem_g=max(0,g.get("target",g.get("amount",0))-g.get("saved",0))
                        mo_g=math.ceil(rem_g/per) if per>0 else 9999
                        st.markdown(f"<div class='crow'><span style='font-size:.74rem;'>{g['name']}</span>"
                                    f"<div><span style='color:{T['accent']};font-weight:600;font-size:.74rem;'>{fmt(per)}/mo</span>"
                                    f"<span style='color:{T['muted']};font-size:.68rem;margin-left:5px;'>→ {mo_g} mo</span></div></div>",unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

        # Net worth
        st.markdown(f"<div class='card'><span class='clabel'>Net Worth Snapshot</span>",unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:2rem;font-weight:800;color:{nw_col};text-align:center;padding:.3rem 0;'>{fmt(net_worth)}</div>",unsafe_allow_html=True)
        for a in st.session_state.assets:
            st.markdown(f"<div class='crow'><span style='color:{T['muted']};font-size:.76rem;'>{a['name']}</span>"
                        f"<span style='color:{T['green']};font-size:.76rem;'>+{fmt(a['value'])}</span></div>",unsafe_allow_html=True)
        for l in st.session_state.liabilities:
            st.markdown(f"<div class='crow'><span style='color:{T['muted']};font-size:.76rem;'>{l['name']}</span>"
                        f"<span style='color:{T['red']};font-size:.76rem;'>-{fmt(l['balance'])}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # CSV
        buf=io.StringIO(); w=csv.writer(buf)
        w.writerow(["Goal","Target","Saved","Progress","Remaining","Priority"])
        for g in st.session_state.goals:
            pg=g.get("saved",0)/g.get("target",g.get("amount",1))*100 if g.get("target",g.get("amount",0))>0 else 0
            w.writerow([g["name"],f"{g.get("target",g.get("amount",0)):.2f}",f"{g['saved']:.2f}",f"{pg:.0f}%",f"{max(0,g.get("target",g.get("amount",0))-g['saved']):.2f}",g.get("priority","")])
        st.download_button("Export goals CSV",data=buf.getvalue().encode(),
            file_name=f"goals_{datetime.now().strftime('%Y-%m-%d')}.csv",mime="text/csv",use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INVEST & RISK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t4:
    st.markdown(f"<div class='tip'>You have <b>{fmt(investable)}/month</b> to save & invest ({invest_pct}% of income) = <b>{fmt(investable*12)}/year</b>.</div>",unsafe_allow_html=True)
    ir1,ir2=st.columns(2,gap="large")
    with ir1:
        st.markdown(f"<div class='card'><span class='clabel'>Risk Profile</span>",unsafe_allow_html=True)
        rp_idx=RISK_LABELS.index(st.session_state.risk_profile) if st.session_state.risk_profile in RISK_LABELS else 2
        risk_sel=st.selectbox("Risk tolerance",RISK_LABELS,index=rp_idx,key="rp_sel")
        st.session_state.risk_profile=risk_sel
        age_val=st.slider("Your age",18,75,st.session_state.get("age",32),1,key="age_sl")
        st.session_state["age"]=age_val
        ret_age=st.slider("Retirement age target",50,75,st.session_state.get("retirement_age",65),1,key="ret_sl")
        st.session_state["retirement_age"]=ret_age
        yrs_left=max(1,ret_age-age_val)
        st.markdown("</div>",unsafe_allow_html=True)

        # Risk gauge
        RISK_SCORES={"Very Conservative":15,"Conservative":30,"Moderate":50,"Growth":70,"Aggressive":90}
        risk_num=RISK_SCORES.get(risk_sel,50)
        age_adj=max(5,min(95,risk_num-(age_val-30)*0.7))
        risk_c=T["green"] if age_adj<40 else T["amber"] if age_adj<70 else T["red"]
        fig_risk=go.Figure(go.Indicator(
            mode="gauge+number",value=round(age_adj),
            number=dict(font=dict(size=28,color=risk_c,family="DM Sans")),
            gauge=dict(
                axis=dict(range=[0,100],tickwidth=0,tickcolor="rgba(0,0,0,0)",tickvals=[],showticklabels=False),
                bar=dict(color=risk_c,thickness=0.28),
                bgcolor="rgba(0,0,0,0)",borderwidth=0,
                steps=[dict(range=[0,33],color=h2r(T["green"],.18)),
                       dict(range=[33,67],color=h2r(T["amber"],.15)),
                       dict(range=[67,100],color=h2r(T["red"],.18))],
            )
        ))
        fig_risk.add_annotation(text=f"{risk_sel}",x=0.5,y=0.1,showarrow=False,
            font=dict(color=T["muted"],size=11,family="DM Sans"),align="center",xref="paper",yref="paper")
        fig_risk.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            height=180,margin=dict(l=10,r=10,t=10,b=5),font=dict(color=T["text"],family="DM Sans"))
        st.plotly_chart(fig_risk,use_container_width=True,config={"displayModeBar":False})
        if risk_num>60 and age_val>55:
            st.markdown(f"<div class='tip'>At age {age_val}, consider reducing risk. Score adjusted to {age_adj:.0f}.</div>",unsafe_allow_html=True)

        # Suggested allocation
        rr=age_adj/100
        sug_eq=max(5,int(rr*85)); sug_bond=max(5,int((1-rr)*55)); sug_crypto=int(rr*8) if risk_num>=50 else 0
        sug_cash=max(5,100-sug_eq-sug_bond-sug_crypto)
        st.markdown(f"<div class='card'><span class='clabel'>Suggested Allocation</span>",unsafe_allow_html=True)
        for lbl,pv,col in [("Equities/ETFs",sug_eq,T["green"]),("Bonds/Fixed",sug_bond,T["blue"]),
                            ("Cash/Stable",sug_cash,T["muted"]),("Crypto",sug_crypto,T["purple"])]:
            if pv>0:
                mo=investable*pv/100
                st.markdown(f"<div style='margin-bottom:7px;'>"
                            f"<div style='display:flex;justify-content:space-between;font-size:.76rem;margin-bottom:2px;'>"
                            f"<span>{lbl}</span><span style='color:{T['muted']};'>{pv}% · {fmt(mo)}/mo</span></div>"
                            f"<div class='pbar'><div class='pfill' style='width:{pv}%;background:{col};'></div></div>"
                            f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # AUS Tax
        st.markdown(f"<div class='card'><span class='clabel'>AUS Tax Estimator — FY2024-25</span>",unsafe_allow_html=True)
        gross=st.number_input("Annual gross income ($)",min_value=0.0,value=float(primary_income*12),step=1000.0,format="%.0f",key="tax_g")
        tc1,tc2,tc3=st.columns(3)
        with tc1: im=st.checkbox("Medicare 2%",value=True)
        with tc2: il=st.checkbox("LITO offset",value=True)
        with tc3: ph=st.checkbox("Private health",value=False)
        tr=calc_tax(gross); med=gross*0.02 if im else 0
        mls=gross*0.01 if (not ph and gross>93000 and im) else 0
        lito=calc_lito(gross) if il else 0
        ttax=max(0,tr+med+mls-lito); net_ann=gross-ttax; eff=ttax/gross*100 if gross>0 else 0
        for lbl,val,col,bld in [("Gross",fmt(gross),T["text"],False),("Income tax",f"-{fmt(tr)}",T["red"],False),
            ("Medicare",f"-{fmt(med)}",T["amber"],False),("MLS",f"-{fmt(mls)}",T["red"],mls>0),
            ("LITO",f"+{fmt(lito)}",T["green"],False),("Net annual",fmt(net_ann),T["accent"],True),
            ("Net monthly",fmt(net_ann/12),T["accent"],True),("Effective rate",pct(eff),T["amber"],True)]:
            fw="font-weight:600;" if bld else ""
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid {T['border']};font-size:.79rem;{fw}'>"
                        f"<span style='color:{T['muted']}'>{lbl}</span><span style='color:{col}'>{val}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    with ir2:
        # Monte Carlo
        st.markdown(f"<div class='card'><span class='clabel'>Monte Carlo — {yrs_left} years to retirement</span>",unsafe_allow_html=True)
        init_p=st.number_input("Current portfolio ($)",min_value=0.0,
            value=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings","Super"])),
            step=1000.0,format="%.0f",key="mc_init")
        mc_c=st.number_input("Monthly contribution ($)",min_value=0.0,value=float(investable),step=100.0,format="%.0f",key="mc_c")
        exp_mu={"Very Conservative":0.04,"Conservative":0.055,"Moderate":0.07,"Growth":0.09,"Aggressive":0.12}.get(risk_sel,0.07)
        exp_sig={"Very Conservative":0.05,"Conservative":0.08,"Moderate":0.13,"Growth":0.17,"Aggressive":0.22}.get(risk_sel,0.13)
        st.caption(f"{exp_mu*100:.1f}% return · {exp_sig*100:.0f}% volatility for {risk_sel}")
        if st.button("Run Simulation (200 paths)",use_container_width=True,key="mc_run"):
            with st.spinner("Simulating..."):
                np.random.seed(42)
                sims=monte_carlo(init_p,mc_c,yrs_left,200,exp_mu,exp_sig)
                mo=np.arange(sims.shape[1])
                p10=np.percentile(sims,10,axis=0); p25=np.percentile(sims,25,axis=0)
                p50=np.percentile(sims,50,axis=0); p75=np.percentile(sims,75,axis=0)
                p90=np.percentile(sims,90,axis=0)
                fig_mc=go.Figure()
                fig_mc.add_trace(go.Scatter(x=mo,y=p90,fill=None,mode="lines",line=dict(color="rgba(0,0,0,0)"),showlegend=False,hoverinfo="skip"))
                fig_mc.add_trace(go.Scatter(x=mo,y=p10,fill="tonexty",mode="lines",fillcolor=h2r(T["green"],.1),line=dict(color="rgba(0,0,0,0)"),name="80% range",hoverinfo="skip"))
                fig_mc.add_trace(go.Scatter(x=mo,y=p75,fill=None,mode="lines",line=dict(color="rgba(0,0,0,0)"),showlegend=False,hoverinfo="skip"))
                fig_mc.add_trace(go.Scatter(x=mo,y=p25,fill="tonexty",mode="lines",fillcolor=h2r(T["accent"],.18),line=dict(color="rgba(0,0,0,0)"),name="50% range",hoverinfo="skip"))
                fig_mc.add_trace(go.Scatter(x=mo,y=p50,mode="lines",name="Median",line=dict(color=T["green"],width=2.5),hovertemplate="Month %{x}<br>$%{y:,.0f}<extra></extra>"))
                fig_mc.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_mc.update_xaxes(title_text="Month")
                fig_mc.update_layout(**plo("Monte Carlo Portfolio Projection",280))
                st.plotly_chart(fig_mc,use_container_width=True,config={"displayModeBar":False})
                rc=st.columns(4)
                rc[0].metric("10th pct",fmtk(p10[-1]),"Worst case")
                rc[1].metric("Median",fmtk(p50[-1]),"Most likely")
                rc[2].metric("90th pct",fmtk(p90[-1]),"Best case")
                rc[3].metric("Contributed",fmtk(init_p+mc_c*12*yrs_left),"Total in")
        else:
            st.markdown(f"<div style='text-align:center;padding:1.5rem;color:{T['muted']};font-size:.8rem;'>Click to simulate 200 portfolio paths over {yrs_left} years.</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # FIRE
        st.markdown(f"<div class='card'><span class='clabel'>FIRE Calculator</span>",unsafe_allow_html=True)
        ann_exp=st.number_input("Annual expenses ($)",min_value=0.0,value=float(total_exp*12),step=500.0,format="%.0f",key="f_exp")
        cur_p=st.number_input("Current portfolio ($)",min_value=0.0,
            value=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings"])),step=1000.0,format="%.0f",key="f_p")
        fire_r=st.slider("Expected return % p.a.",1.0,15.0,exp_mu*100,0.5,key="f_rate",format="%.1f%%")
        lean_t=ann_exp*20; fire_t=ann_exp*25; fat_t=ann_exp*33
        fi_r=cur_p/fire_t*100 if fire_t>0 else 0
        st.markdown(f"<div style='text-align:center;margin:.3rem 0;'>"
                    f"<span style='font-size:2.2rem;font-weight:800;color:{T['accent']};'>{fi_r:.0f}%</span>"
                    f"<span style='font-size:.7rem;color:{T['muted']};margin-left:7px;'>FI Ratio</span></div>",unsafe_allow_html=True)
        for lbl,tgt,col in [("Lean FIRE (5% rule)",lean_t,T["blue"]),("FIRE (4% rule)",fire_t,T["accent"]),("Fat FIRE (3% rule)",fat_t,T["amber"])]:
            p=min(100,cur_p/tgt*100) if tgt>0 else 0
            st.markdown(f"<div style='margin-bottom:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:2px;'>"
                        f"<span>{lbl}</span><span style='color:{T['muted']};'>{p:.0f}% of {fmtk(tgt)}</span></div>"
                        f"<div class='pbar'><div class='pfill' style='width:{p:.1f}%;background:{col};'></div></div>"
                        f"</div>",unsafe_allow_html=True)
        if investable>0 and fire_t>0:
            yf=[]; vf=[]; v=cur_p; yr_hit=None
            for yr in range(51):
                yf.append(yr); vf.append(round(v))
                if v>=fire_t and yr_hit is None: yr_hit=yr
                v=(v+investable*12)*(1+fire_r/100)
            fig_fire=go.Figure()
            fig_fire.add_trace(go.Scatter(x=yf,y=vf,mode="lines",line=dict(color=T["green"],width=2),fill="tozeroy",fillcolor=h2r(T["green"],.08),hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
            for lbl,tgt,col in [("Lean",lean_t,T["blue"]),("FIRE",fire_t,T["amber"]),("Fat",fat_t,T["red"])]:
                fig_fire.add_hline(y=tgt,line_dash="dot",line_color=col,annotation_text=lbl,annotation_font_color=col,annotation_font_size=10)
            fig_fire.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_fire.update_xaxes(title_text="Years")
            fig_fire.update_layout(**plo("Path to FIRE",230))
            st.plotly_chart(fig_fire,use_container_width=True,config={"displayModeBar":False})
            if yr_hit:
                st.markdown(f"<div class='tip'>FIRE in <b>{yr_hit} years</b> at age <b>{age_val+yr_hit}</b>. Monthly drawdown at 4%: <b>{fmt(fire_t*0.04/12)}</b>.</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INSIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t5:
    ins1,ins2=st.columns(2,gap="large")
    with ins1:
        st.markdown(f"<div class='card'><span class='clabel'>Financial Intelligence Report</span>",unsafe_allow_html=True)
        def insight(headline, detail, badge):
            st.markdown(f"<div style='padding:.55rem 0;border-bottom:1px solid {T['border']};'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;'>"
                        f"<span style='font-weight:600;font-size:.82rem;'>{headline}</span>"
                        f"<span class='bd {badge[0]}'>{badge[1]}</span></div>"
                        f"<div style='font-size:.73rem;color:{T['muted']};line-height:1.5;'>{detail}</div>"
                        f"</div>",unsafe_allow_html=True)
        if savings_rate>=20: insight("Savings target met",f"Saving {savings_rate:.1f}% — above the 20% benchmark.",("ok","Healthy"))
        else: insight("Savings below target",f"Rate is {savings_rate:.1f}%. Need {fmt(total_income*0.2-cash_flow)}/mo more.",("bad","Act"))
        if em_months>=6: insight("Emergency fund secure",f"{em_months:.1f} months covered — above the 6-month target.",("ok","Secure"))
        elif em_months>=3: insight("Emergency fund building",f"{em_months:.1f} months. Target {fmt(total_exp*6)}.",("warn","Build"))
        else: insight("Emergency fund critical",f"Only {em_months:.1f} months. This is your #1 priority.",("bad","Urgent"))
        ob=[e for e in st.session_state.expenses if to_mo(e["amount"],e.get("freq","Monthly"))>e.get("budget",e["amount"])]
        if ob: insight("Budget overruns",f"{len(ob)} categories overspent: {', '.join(e['name'] for e in ob[:4])}.",("warn","Review"))
        else: insight("Budget on track","All categories within budget.",("ok","On track"))
        if total_sub>150: insight("Subscription overload",f"{fmt(total_sub)}/mo = {fmt(total_sub*12)}/yr on subscriptions.",("warn","Audit"))
        hi=[l for l in st.session_state.liabilities if l.get("rate",0)>15]
        if hi: insight("Predatory debt",f"{fmt(sum(l['balance'] for l in hi))} at >15% APR — costs {fmt(sum(l['balance']*l['rate']/100 for l in hi))}/yr.",("bad","Priority"))
        # Retirement projection
        proj=sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings","Super"])
        yrl=max(1,st.session_state.get("retirement_age",65)-st.session_state.get("age",32))
        for _ in range(yrl): proj=(proj+investable*12)*1.07
        insight("Retirement projection",f"At 7% growth: {fmt(proj)} at age {st.session_state.get('retirement_age',65)}. Monthly drawdown: {fmt(proj*0.04/12)}.",("blu","Estimate"))
        st.markdown("</div>",unsafe_allow_html=True)

        # Cash flow waterfall
        cf_items=[("Income",total_income,"absolute"),("Needs",-needs_actual,"relative"),
                  ("Wants",-wants_actual,"relative"),("Save & Invest",-investable,"relative")]
        remaining=total_income-needs_actual-wants_actual-investable
        fig_cf=go.Figure(go.Waterfall(
            x=[c[0] for c in cf_items]+["Remaining"],
            measure=[c[2] for c in cf_items]+["total"],
            y=[c[1] for c in cf_items]+[0],
            connector=dict(line=dict(color=T["border"],width=.5)),
            increasing=dict(marker=dict(color=T["green"])),
            decreasing=dict(marker=dict(color=T["red"])),
            totals=dict(marker=dict(color=T["green"] if remaining>=0 else T["red"])),
            texttemplate="%{y:$,.0f}",textposition="outside",textfont=dict(color=T["text"],size=9)))
        fig_cf.update_layout(**plo("Monthly Cash Flow",210))
        st.plotly_chart(fig_cf,use_container_width=True,config={"displayModeBar":False})

    with ins2:
        # Predictions
        st.markdown(f"<div class='card'><span class='clabel'>Predictions & Numbers</span>",unsafe_allow_html=True)
        preds=[
            ("Savings in 12 months",fmt(cash_flow*12+cash_assets),"at current rate",T["green"]),
            ("Net worth in 5 years",fmt(net_worth+(cash_flow+investable)*12*5),"7% growth estimate",T["blue"]),
            ("Subscriptions per year",fmt(total_sub*12),"review regularly",T["amber"]),
            ("Debt interest per year",fmt(sum(l["balance"]*l.get("rate",0)/100 for l in st.session_state.liabilities)),"cost of carrying debt",T["red"]),
            ("FIRE number needed",fmt(total_exp*12*25),"at 4% withdrawal rule",T["purple"]),
            ("Monthly tax (estimate)",fmt(calc_tax(primary_income*12)/12),"approx. income tax only",T["muted"]),
        ]
        for lbl,val,note,col in preds:
            st.markdown(f"<div style='padding:.45rem 0;border-bottom:1px solid {T['border']};'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.79rem;'>"
                        f"<span style='color:{T['muted']}'>{lbl}</span>"
                        f"<span style='color:{col};font-weight:600;'>{val}</span></div>"
                        f"<div style='font-size:.65rem;color:{T['muted']};'>{note}</div>"
                        f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # 10-year net worth
        nw_y=[]; nw_v=[]; v=net_worth
        for yr in range(11):
            nw_y.append(yr); nw_v.append(round(v))
            v=v+(cash_flow+investable)*12*0.07
        fig_nw=go.Figure(go.Scatter(x=nw_y,y=nw_v,mode="lines+markers",
            line=dict(color=T["accent"],width=2.5),fill="tozeroy",fillcolor=h2r(T["accent"],.09),
            marker=dict(size=5,color=T["accent"]),hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
        fig_nw.update_yaxes(tickprefix="$",tickformat=",.0f"); fig_nw.update_xaxes(title_text="Years from now")
        fig_nw.update_layout(**plo("10-Year Net Worth Projection",230))
        st.plotly_chart(fig_nw,use_container_width=True,config={"displayModeBar":False})

        # Spending anomalies
        if st.session_state.expenses:
            df_a=pd.DataFrame(st.session_state.expenses)
            df_a["mo"]=df_a.apply(lambda r:to_mo(r["amount"],r.get("freq","Monthly")),axis=1)
            avg=df_a["mo"].mean(); std=df_a["mo"].std()
            anomalies=df_a[df_a["mo"]>avg+std].sort_values("mo",ascending=False)
            if not anomalies.empty:
                st.markdown(f"<div class='card'><span class='clabel'>Spending Anomalies (above average)</span>",unsafe_allow_html=True)
                for _,row in anomalies.head(4).iterrows():
                    bud=row.get("budget",row["mo"]); pa=row["mo"]/bud*100 if bud>0 else 100
                    st.markdown(f"<div class='crow'>"
                                f"<div><span style='font-weight:600;font-size:.79rem;'>{row['name']}</span>"
                                f"<span style='color:{T['muted']};font-size:.68rem;margin-left:7px;'>{row.get('category','')}</span></div>"
                                f"<div><span style='color:{T['red']};font-weight:600;font-size:.79rem;'>{fmt(row['mo'])}/mo</span>"
                                f"<span style='color:{T['muted']};font-size:.65rem;margin-left:4px;'>{pa:.0f}% of budget</span></div>"
                                f"</div>",unsafe_allow_html=True)
                st.markdown("</div>",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI ASSISTANT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t6:
    ai1,ai2=st.columns([2.5,1.5],gap="large")
    with ai1:
        st.markdown(f"<div class='card'><span class='clabel'>AI Financial Advisor — powered by Claude</span>",unsafe_allow_html=True)
        api_key=st.text_input("Anthropic API Key",type="password",placeholder="sk-ant-...",key="api_key",
            help="Get at console.anthropic.com. Never stored.")
        if api_key:
            sp_cols=st.columns(2)
            prompts=["Can I afford a $40k car?","How do I hit a 20% savings rate?",
                     "Should I pay off debt or invest?","How do I reach my goals faster?",
                     "What's my projected retirement age?","How can I reduce expenses?"]
            for i,p in enumerate(prompts):
                with sp_cols[i%2]:
                    if st.button(p,key=f"sp_{i}",use_container_width=True):
                        st.session_state.chat_history.append({"role":"user","content":p})
                        with st.spinner("Thinking..."):
                            sys=f"""You are a premium AI financial advisor for Seralung Finance (Australia).
User context: income {fmt(total_income)}/mo, expenses {fmt(total_exp)}/mo, savings rate {savings_rate:.1f}%,
net worth {fmt(net_worth)}, emergency fund {em_months:.1f} months, investable {fmt(investable)}/mo,
health score {hs}/100, debt {fmt(total_liab)}, goals: {', '.join(g['name'] for g in st.session_state.goals)}.
Give concise, specific, actionable AUD advice under 180 words."""
                            try:
                                r=requests.post("https://api.anthropic.com/v1/messages",
                                    headers={"x-api-key":api_key,"anthropic-version":"2023-06-01","content-type":"application/json"},
                                    json={"model":"claude-sonnet-4-20250514","max_tokens":500,"system":sys,"messages":st.session_state.chat_history},timeout=30)
                                reply=r.json()["content"][0]["text"] if r.status_code==200 else f"Error {r.status_code}"
                            except Exception as e: reply=f"Error: {str(e)[:100]}"
                        st.session_state.chat_history.append({"role":"assistant","content":reply}); st.rerun()
            if st.session_state.chat_history:
                st.markdown("<div class='chat-wrap'>",unsafe_allow_html=True)
                for msg in st.session_state.chat_history[-14:]:
                    c=msg["content"].replace("\n","<br>")
                    if msg["role"]=="user": st.markdown(f"<div class='chat-user'>{c}</div>",unsafe_allow_html=True)
                    else: st.markdown(f"<div class='chat-ai'>{c}</div>",unsafe_allow_html=True)
                st.markdown("</div><div style='clear:both;margin:.5rem 0;'></div>",unsafe_allow_html=True)
            user_in=st.chat_input("Ask your AI financial advisor anything...")
            if user_in:
                st.session_state.chat_history.append({"role":"user","content":user_in})
                sys=f"Financial advisor for {fmt(total_income)}/mo income, {savings_rate:.1f}% savings rate, {fmt(net_worth)} net worth. Concise AUD advice."
                try:
                    r=requests.post("https://api.anthropic.com/v1/messages",
                        headers={"x-api-key":api_key,"anthropic-version":"2023-06-01","content-type":"application/json"},
                        json={"model":"claude-sonnet-4-20250514","max_tokens":500,"system":sys,"messages":st.session_state.chat_history},timeout=30)
                    reply=r.json()["content"][0]["text"] if r.status_code==200 else "Error"
                except Exception as e: reply=f"Error: {str(e)[:80]}"
                st.session_state.chat_history.append({"role":"assistant","content":reply}); st.rerun()
            if st.button("Clear chat",key="clear_chat"): st.session_state.chat_history=[]; st.rerun()
        else:
            st.markdown(f"<div style='text-align:center;padding:2rem 1rem;color:{T['muted']};font-size:.82rem;line-height:1.7;'>"
                        f"<div style='font-size:1.4rem;font-weight:700;color:{T['text']};margin-bottom:.4rem;'>AI Financial Advisor</div>"
                        f"Enter your Anthropic API key above to chat with a personalised advisor.<br>"
                        f"Your full financial profile is sent as context automatically.<br><br>"
                        f"<span style='font-size:.72rem;'>Get your key at <b>console.anthropic.com</b></span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with ai2:
        st.markdown(f"<div class='card'><span class='clabel'>Your Context (sent to AI)</span>",unsafe_allow_html=True)
        for lbl,val in [("Income",fmt(total_income)),("Expenses",fmt(total_exp)),("Savings rate",pct(savings_rate)),
                        ("Emergency",f"{em_months:.1f} mo"),("Net worth",fmt(net_worth)),("Debt",fmt(total_liab)),
                        ("Investable",fmt(investable)),("Health",f"{hs}/100"),("Risk",st.session_state.get("risk_profile","Moderate")),
                        ("Age/Retire",f"{st.session_state.get('age',32)}/{st.session_state.get('retirement_age',65)}"),
                        ("Goals",str(len(st.session_state.goals)))]:
            st.markdown(f"<div class='crow'><span style='color:{T['muted']};font-size:.75rem;'>{lbl}</span>"
                        f"<span style='font-weight:600;font-size:.75rem;'>{val}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t7:
    st.markdown(f"<div style='text-align:center;padding:1rem 0 .8rem;'>"
                f"<div style='font-size:2rem;font-weight:800;color:{T['accent']};letter-spacing:-.03em;'>Seralung Finance Pro</div>"
                f"<div style='color:{T['muted']};font-size:.82rem;margin-top:.3rem;'>Your complete financial operating system</div>"
                f"</div>",unsafe_allow_html=True)
    pc1,pc2,pc3=st.columns(3,gap="large")
    def price_card(title,price,period,features,featured=False):
        brd=f"border:2px solid {T['accent']};" if featured else f"border:1px solid {T['border']};"
        glo=f"box-shadow:0 0 24px {T['glow']};" if featured else ""
        tag=f"<div style='text-align:center;margin-bottom:.4rem;'><span class='bd ok'>Most Popular</span></div>" if featured else ""
        fs="".join(f"<div style='padding:.3rem 0;border-bottom:1px solid {T['border']};font-size:.76rem;display:flex;gap:7px;align-items:center;'>"
                   f"<span style='color:{T['green']};font-weight:700;'>+</span>{f}</div>" for f in features)
        return (f"<div style='background:{T['surface']};{brd}{glo}border-radius:18px;padding:1.4rem;'>"
                f"{tag}<div style='font-size:.95rem;font-weight:600;text-align:center;margin-bottom:.4rem;'>{title}</div>"
                f"<div style='font-size:2.2rem;font-weight:800;color:{T['accent']};text-align:center;letter-spacing:-.03em;'>{price}</div>"
                f"<div style='font-size:.68rem;color:{T['muted']};text-align:center;margin-bottom:.9rem;'>{period}</div>"
                f"<div style='margin-bottom:.8rem;'>{fs}</div></div>")
    with pc1:
        st.markdown(price_card("Free","$0","Forever",["Dashboard overview","Basic budgeting","3 financial goals","CSV export","Manual entry"]),unsafe_allow_html=True)
        st.button("Get started free",use_container_width=True,key="btn_free")
    with pc2:
        st.markdown(price_card("Pro","$9","/month",["Everything in Free","Unlimited goals","AI insights","Monte Carlo simulation","Debt payoff planner","FIRE calculator","AUS tax estimator","Bank CSV import","PDF reports","Cloud save"],featured=True),unsafe_allow_html=True)
        st.button("Start free trial",use_container_width=True,key="btn_pro")
    with pc3:
        st.markdown(price_card("Premium","$19","/month",["Everything in Pro","AI Financial Advisor (Claude)","Investment risk profiler","Family budgeting","Multi-account support","Advanced analytics","Tax optimisation","Advisor mode","Priority support","Custom categories"]),unsafe_allow_html=True)
        st.button("Start Premium trial",use_container_width=True,key="btn_prem")
    st.markdown(f"<p style='text-align:center;font-size:.68rem;color:{T['muted']};margin-top:.5rem;'>Cancel anytime · 30-day money-back guarantee · No credit card for free trial</p>",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"<p style='text-align:center;color:{T['muted']};font-size:.63rem;letter-spacing:.03em;'>"
            "SERALUNG FINANCE · Educational use only · Not financial advice · Consult a qualified adviser · AUS Tax FY2024-25</p>",
            unsafe_allow_html=True)
