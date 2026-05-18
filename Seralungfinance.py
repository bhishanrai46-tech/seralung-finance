"""
Seralung Finance — v3
requirements.txt:
    streamlit>=1.32  plotly>=5.18  pandas>=2.0
    fpdf2>=2.7  numpy>=1.24  requests>=2.28  supabase>=2.0
    pdfplumber>=0.9  openpyxl>=3.0
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
    import plotly.io as pio; KALEIDO_OK = True
except Exception:
    KALEIDO_OK = False

import tempfile, os as _os

def _fig_png(fig, w=1100, h=420):
    """Export plotly figure to PNG bytes for PDF embedding."""
    if not KALEIDO_OK: return None
    try:
        return pio.to_image(fig, format="png", width=w, height=h, scale=2)
    except Exception:
        return None

def _pdf_img(pdf, img_bytes, pw=185, margin_left=12):
    """Embed PNG bytes into FPDF page."""
    if not img_bytes: return
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(img_bytes); path=tmp.name
        pdf.image(path, x=margin_left, w=pw)
        _os.unlink(path)
    except Exception:
        pass

try:
    from db import init_supabase, get_user, restore_session, load_user_data, save_user_data, login_page, logout
    AUTH_ENABLED = True
except ImportError:
    AUTH_ENABLED = False

st.set_page_config(page_title="Seralung Finance", layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────────────────────────────
# THEMES  — all use a visible colored accent (never black/white as button bg)
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "Light": {
        "bg":"#F9FAFB","surface":"#FFFFFF","surface2":"#F3F4F6","surface3":"#E9EAEC",
        "border":"#E5E7EB","accent":"#059669","accent2":"#10B981","glow":"rgba(5,150,105,0.12)",
        "text":"#111827","muted":"#6B7280","green":"#059669","red":"#DC2626",
        "amber":"#D97706","blue":"#2563EB","purple":"#7C3AED",
        "chart":["#059669","#2563EB","#D97706","#DC2626","#7C3AED","#0891B2","#BE185D"],
        "dark":False,"shadow":"0 1px 3px rgba(0,0,0,0.08),0 4px 12px rgba(0,0,0,0.04)",
    },
    "Dark": {
        "bg":"#0F1117","surface":"#1A1D27","surface2":"#22263A","surface3":"#2A2F46",
        "border":"#2E3350","accent":"#10B981","accent2":"#34D399","glow":"rgba(16,185,129,0.15)",
        "text":"#F1F5F9","muted":"#94A3B8","green":"#34D399","red":"#F87171",
        "amber":"#FCD34D","blue":"#60A5FA","purple":"#A78BFA",
        "chart":["#10B981","#60A5FA","#FCD34D","#F87171","#A78BFA","#22D3EE","#F472B6"],
        "dark":True,"shadow":"0 1px 3px rgba(0,0,0,0.3),0 4px 12px rgba(0,0,0,0.2)",
    },
    "Navy": {
        "bg":"#EEF2FF","surface":"#FFFFFF","surface2":"#E0E7FF","surface3":"#C7D2FE",
        "border":"#C7D2FE","accent":"#4F46E5","accent2":"#6366F1","glow":"rgba(79,70,229,0.15)",
        "text":"#1E1B4B","muted":"#6366F1","green":"#059669","red":"#DC2626",
        "amber":"#D97706","blue":"#4F46E5","purple":"#7C3AED",
        "chart":["#4F46E5","#059669","#D97706","#DC2626","#7C3AED","#0891B2","#BE185D"],
        "dark":False,"shadow":"0 1px 3px rgba(79,70,229,0.08),0 4px 12px rgba(79,70,229,0.06)",
    },
}

CATEGORIES  = ["Housing","Food","Transport","Health","Insurance","Tech","Entertainment","Personal","Education","Other"]
ASSET_TYPES = ["Cash","Savings","Investments","Super","Property","Vehicle","Business","Other"]
LIAB_TYPES  = ["Mortgage","Loan","Credit","HECS","Personal","Business","Other"]
RISK_LABELS = ["Conservative","Moderate","Growth","Aggressive"]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE  — income saved here so Supabase can persist it
# ─────────────────────────────────────────────────────────────────────────────
def _i(k, v):
    if k not in st.session_state: st.session_state[k] = v

_i("primary_income", 6000.0)   # saved to Supabase
_i("other_income",   500.0)    # saved to Supabase
_i("needs_pct",50); _i("wants_pct",30); _i("invest_pct",20)
_i("expenses",[
    {"name":"Rent",         "amount":1800.0,"budget":2000.0,"category":"Housing",       "freq":"Monthly"},
    {"name":"Groceries",    "amount":450.0, "budget":500.0, "category":"Food",          "freq":"Monthly"},
    {"name":"Transport",    "amount":250.0, "budget":300.0, "category":"Transport",     "freq":"Monthly"},
    {"name":"Dining Out",   "amount":350.0, "budget":300.0, "category":"Food",          "freq":"Monthly"},
    {"name":"Utilities",    "amount":180.0, "budget":220.0, "category":"Housing",       "freq":"Monthly"},
    {"name":"Phone",        "amount":85.0,  "budget":85.0,  "category":"Tech",          "freq":"Monthly"},
    {"name":"Insurance",    "amount":150.0, "budget":200.0, "category":"Insurance",     "freq":"Monthly"},
    {"name":"Entertainment","amount":120.0, "budget":150.0, "category":"Entertainment", "freq":"Monthly"},
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
    {"name":"Superannuation",  "type":"Super","value":35000.0},
    {"name":"Car",             "type":"Vehicle","value":18000.0},
    {"name":"ETF Portfolio",   "type":"Investments","value":8500.0},
])
_i("liabilities",[
    {"name":"Car Loan",    "type":"Loan",  "balance":14000.0,"rate":6.5, "min_payment":350.0},
    {"name":"Credit Card", "type":"Credit","balance":2800.0, "rate":19.99,"min_payment":84.0},
    {"name":"HECS Debt",   "type":"HECS",  "balance":18000.0,"rate":3.9, "min_payment":200.0},
])
_i("goals",[
    {"name":"Emergency Fund",  "target":15000.0,"saved":12000.0,"priority":"High",  "color":"green"},
    {"name":"Europe Trip",     "target":8000.0, "saved":2000.0, "priority":"Medium","color":"blue"},
    {"name":"Property Deposit","target":80000.0,"saved":25000.0,"priority":"High",  "color":"purple"},
])
_i("transactions",[])
_i("chat_history",[])
_i("risk_profile","Moderate"); _i("age",32); _i("retirement_age",65)

# Migrate old goal format: "amount" → "target"
for _gi, _g in enumerate(st.session_state.get("goals", [])):
    if "amount" in _g and "target" not in _g:
        st.session_state.goals[_gi]["target"] = _g["amount"]
        del st.session_state.goals[_gi]["amount"]
    if "saved" not in _g: st.session_state.goals[_gi]["saved"] = 0.0

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt(n):   return f"${n:,.0f}"
def fmtk(n):  return f"${n/1000:.1f}k" if abs(n)>=1000 else fmt(n)
def pct(n):   return f"{n:.1f}%"
def to_mo(amount, freq="Monthly"):
    return amount * 52/12 if freq == "Weekly" else amount

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
    for u,a in {'\u2014':'-','\u2013':'-','\u2018':"'",'\u2019':"'",'\u201c':'"','\u201d':'"'}.items():
        t=t.replace(u,a)
    return t.encode('latin-1',errors='replace').decode('latin-1')

def auto_categorize(desc):
    d=str(desc).lower()
    for kws,cat in [
        (["rent","lease","mortgage","real estate"],"Housing"),
        (["electricity","power","energy","agl","origin","gas","water"],"Housing"),
        (["internet","nbn","optus","telstra","vodafone","tpg"],"Tech"),
        (["coles","woolworths","aldi","iga","costco","supermarket","grocer"],"Food"),
        (["uber eats","menulog","doordash","mcdonald","kfc","subway","domino",
          "pizza","cafe","coffee","restaurant","takeaway","bakery"],"Food"),
        (["netflix","stan","disney","binge","foxtel","spotify","apple music","amazon prime"],"Entertainment"),
        (["gym","fitness","yoga","pilates","anytime","f45"],"Health"),
        (["pharmacy","chemist","doctor","medical","dental","hospital","medibank","bupa"],"Health"),
        (["fuel","petrol","shell","bp","caltex","ampol"],"Transport"),
        (["uber","ola","taxi","parking","toll","myki","opal","train","bus"],"Transport"),
        (["insurance","nrma","aami","racv","gio","allianz"],"Insurance"),
        (["school","university","tafe","udemy","coursera"],"Education"),
    ]:
        if any(k in d for k in kws): return cat
    return "Other"



try:
    import pdfplumber; PDF_PARSE_OK=True
except ImportError:
    PDF_PARSE_OK=False

def parse_pdf_statement(f):
    """Extract transactions from a bank statement PDF using pdfplumber."""
    if not PDF_PARSE_OK:
        return None,"Install pdfplumber: pip install pdfplumber"
    try:
        all_rows=[]
        with pdfplumber.open(f) as pdf:
            for page in pdf.pages:
                tables=page.extract_tables()
                for tbl in tables:
                    if tbl: all_rows.extend(tbl)
        if not all_rows:
            # Fallback: extract raw text and try line-by-line
            lines=[]
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    txt=page.extract_text()
                    if txt: lines.extend(txt.split("\n"))
            return _parse_text_lines(lines)
        # Find header row
        hi=0
        for i,row in enumerate(all_rows):
            if row and any(k in str(row).lower() for k in ["date","description","debit","credit","amount"]):
                hi=i; break
        headers=[str(h).strip().lower().replace(" ","_") if h else f"col_{j}" for j,h in enumerate(all_rows[hi])]
        data=pd.DataFrame(all_rows[hi+1:],columns=headers)
        data=data.dropna(how="all")
        return _process_df(data)
    except Exception as e:
        return None,f"PDF parse error: {str(e)[:120]}"

def parse_excel_statement(f):
    """Extract transactions from a bank statement Excel file (.xlsx/.xls)."""
    try:
        df=pd.read_excel(f,dtype=str,engine="openpyxl" if str(getattr(f,"name","")).endswith("xlsx") else None)
        df.columns=[str(c).strip().lower().replace(" ","_") for c in df.columns]
        return _process_df(df)
    except Exception as e:
        return None,f"Excel parse error: {str(e)[:120]}"

def parse_ofx_statement(f):
    """Parse OFX/QFX bank statement files."""
    try:
        content=f.read().decode("utf-8",errors="replace")
        import re
        rows=[]
        txns=re.findall(r"<STMTTRN>(.*?)</STMTTRN>",content,re.DOTALL)
        for txn in txns:
            def _g(tag): m=re.search(f"<{tag}>(.*?)<",txn,re.DOTALL); return m.group(1).strip() if m else ""
            rows.append({"Date":_g("DTPOSTED")[:8],"Description":_g("MEMO") or _g("NAME"),"Amount":_g("TRNAMT")})
        if not rows: return None,"No transactions found in OFX file."
        df=pd.DataFrame(rows)
        df["Date"]=pd.to_datetime(df["Date"],format="%Y%m%d",errors="coerce")
        df["Amount"]=pd.to_numeric(df["Amount"],errors="coerce").fillna(0)
        df["Category"]=df["Description"].apply(auto_categorize)
        df=df.dropna(subset=["Date"]); df=df[df["Amount"]!=0].sort_values("Date",ascending=False)
        return df,None
    except Exception as e:
        return None,f"OFX parse error: {str(e)[:120]}"

def _parse_text_lines(lines):
    """Last-resort: parse raw text lines looking for date+amount patterns."""
    import re
    rows=[]
    date_pat=re.compile(r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})",re.I)
    amt_pat =re.compile(r"-?\$?([\d,]+\.\d{2})")
    for ln in lines:
        d=date_pat.search(ln); a=amt_pat.findall(ln)
        if d and a:
            desc=date_pat.sub("",ln); desc=amt_pat.sub("",desc).strip()
            amt=float(a[-1].replace(",",""))
            rows.append({"Date":d.group(1),"Description":desc or "Unknown","Amount":-amt})
    if not rows: return None,"Could not extract transactions from PDF text."
    df=pd.DataFrame(rows)
    df["Date"]=pd.to_datetime(df["Date"],dayfirst=True,errors="coerce")
    df["Category"]=df["Description"].apply(auto_categorize)
    df=df.dropna(subset=["Date"]); df=df[df["Amount"]!=0].sort_values("Date",ascending=False)
    return df,None

def _process_df(df):
    """Shared column detection and normalisation for CSV/Excel/PDF tables."""
    dcol=next((c for c in df.columns if "date" in c),None)
    ncol=next((c for c in df.columns if any(k in c for k in ["description","details","narration","memo","narrative","particulars"])),None)
    acol=next((c for c in df.columns if c in ["amount","net_amount","net","value"]),None)
    dbcol=next((c for c in df.columns if "debit"  in c),None)
    crcol=next((c for c in df.columns if "credit" in c),None)
    if not dcol or not ncol: return None,f"Cannot find Date/Description columns. Found: {list(df.columns)}"
    res=pd.DataFrame()
    res["Date"]=pd.to_datetime(df[dcol].astype(str),dayfirst=True,errors="coerce")
    res["Description"]=df[ncol].fillna("Unknown").astype(str).str.strip()
    if acol:
        res["Amount"]=pd.to_numeric(df[acol].astype(str).str.replace(r"[$,\s]","",regex=True),errors="coerce").fillna(0)
    elif dbcol and crcol:
        d2=pd.to_numeric(df[dbcol].astype(str).str.replace(r"[$,\s]","",regex=True),errors="coerce").fillna(0)
        c2=pd.to_numeric(df[crcol].astype(str).str.replace(r"[$,\s]","",regex=True),errors="coerce").fillna(0)
        res["Amount"]=c2-d2
    else: return None,"Cannot find Amount/Debit/Credit columns."
    res["Category"]=res["Description"].apply(auto_categorize)
    res=res.dropna(subset=["Date"]); res=res[res["Amount"]!=0].sort_values("Date",ascending=False)
    return res,None

def parse_bank_csv(f):
    try:
        content=f.read().decode("utf-8",errors="replace").strip().split("\n")
        hi=0
        for i,ln in enumerate(content):
            if any(k in ln.lower() for k in ["date","amount","description","debit","credit"]):
                hi=i; break
        df=pd.read_csv(io.StringIO("\n".join(content[hi:])),on_bad_lines="skip",dtype=str)
        df.columns=[x.strip().lower().replace(" ","_") for x in df.columns]
        return _process_df(df)
    except Exception as e: return None,str(e)

def monte_carlo(init,monthly,years=25,n=200,mu=0.07,sigma=0.15):
    months=years*12; res=np.zeros((n,months+1)); res[:,0]=init
    mm,ms=mu/12,sigma/math.sqrt(12)
    for t in range(1,months+1):
        ret=np.random.normal(mm,ms,n); res[:,t]=res[:,t-1]*(1+ret)+monthly
    return res

def goal_target(g): return g.get("target",g.get("amount",0))
def goal_saved(g):  return g.get("saved",0)

# ─────────────────────────────────────────────────────────────────────────────
# HEALTH SCORE
# ─────────────────────────────────────────────────────────────────────────────
def health_score_calc():
    score,det={},{}
    mexp=sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses)+sum(s["amount"] for s in st.session_state.subscriptions)
    sr=max(0,(total_income-mexp)/total_income*100) if total_income>0 else 0
    s1=min(25,sr/20*25)
    det["Savings Rate"]={"score":s1,"max":25,"val":pct(sr),"ok":sr>=20,"desc":f"{sr:.1f}% — target 20%"}
    cash=sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
    em=cash/mexp if mexp>0 else 0
    s2=min(20,em/6*20)
    det["Emergency Fund"]={"score":s2,"max":20,"val":f"{em:.1f} mo","ok":em>=6,"desc":f"{em:.1f} months — target 6"}
    nd=sum(l["balance"] for l in st.session_state.liabilities if l["type"]!="HECS")
    dti=nd/(total_income*12)*100 if total_income>0 else 0
    s3=max(0,20-dti*0.5)
    det["Debt Ratio"]={"score":s3,"max":20,"val":pct(dti),"ok":dti<=36,"desc":f"{dti:.0f}% — target <36%"}
    nw=sum(a["value"] for a in st.session_state.assets)-sum(l["balance"] for l in st.session_state.liabilities)
    s4=15 if nw>0 else max(0,15+nw/10000)
    det["Net Worth"]={"score":s4,"max":15,"val":fmt(nw),"ok":nw>0,"desc":"Positive net worth"}
    over=sum(max(0,to_mo(e["amount"],e.get("freq","Monthly"))-e.get("budget",e["amount"])) for e in st.session_state.expenses)
    s5=max(0,10-over/100)
    det["Budget Control"]={"score":s5,"max":10,"val":fmt(over)+" over","ok":over==0,"desc":"All within budget"}
    s6=min(10,len(st.session_state.goals)*3.5)
    det["Goal Progress"]={"score":s6,"max":10,"val":f"{len(st.session_state.goals)} goals","ok":len(st.session_state.goals)>=2,"desc":"Track 3+ goals"}
    total=round(s1+s2+s3+s4+s5+s6)
    return total, det

# ─────────────────────────────────────────────────────────────────────────────
# SVG GAUGE  — no overlap
# ─────────────────────────────────────────────────────────────────────────────
def gauge_svg(score, grade, bg_track, muted_color):
    r=76; cx,cy=100,100
    circ=2*math.pi*r; half=circ/2; sl=half*score/100
    col="#059669" if score>=80 else "#2563EB" if score>=65 else "#D97706" if score>=50 else "#DC2626"
    return (f'<svg viewBox="0 0 200 110" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:200px;display:block;margin:0 auto;">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{bg_track}" stroke-width="13"'
            f' stroke-dasharray="{half:.2f} {half:.2f}" transform="rotate(-180 {cx} {cy})" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="13"'
            f' stroke-dasharray="{sl:.2f} {circ-sl:.2f}" transform="rotate(-180 {cx} {cy})" stroke-linecap="round"/>'
            f'<text x="{cx}" y="78" text-anchor="middle" font-size="38" font-weight="700"'
            f' fill="{col}" font-family="Inter,sans-serif">{score}</text>'
            f'<text x="{cx}" y="98" text-anchor="middle" font-size="11" fill="{muted_color}"'
            f' font-family="Inter,sans-serif" letter-spacing="0.06em">{grade.upper()}</text>'
            f'</svg>')

# ─────────────────────────────────────────────────────────────────────────────
# REPORT GENERATORS
# ─────────────────────────────────────────────────────────────────────────────
def gen_csv(period="Monthly"):
    buf=io.StringIO(); w=csv.writer(buf)
    sr=(total_income-total_exp)/total_income*100 if total_income>0 else 0
    w.writerow([f"Seralung Finance — {period} Report — {datetime.now().strftime('%B %Y')}"])
    w.writerow([f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}"]);w.writerow([])
    w.writerow(["SUMMARY"])
    for l,v in [("Health Score",f"{hs}/100"),("Monthly Income",fmt(total_income)),
                ("Monthly Expenses",fmt(total_exp)),("Cash Flow",fmt(cash_flow)),
                ("Savings Rate",pct(sr)),("Net Worth",fmt(net_worth)),
                ("Emergency Fund",f"{em_months:.1f} months")]: w.writerow([l,v])
    w.writerow([]);w.writerow(["EXPENSES","","","","",""])
    w.writerow(["Name","Category","Frequency","Amount","Monthly equiv","Budget","Status"])
    for e in st.session_state.expenses:
        mo=to_mo(e["amount"],e.get("freq","Monthly")); bud=e.get("budget",e["amount"])
        w.writerow([e["name"],e.get("category",""),e.get("freq","Monthly"),
                    f"{e['amount']:.2f}",f"{mo:.2f}",f"{bud:.2f}","OVER" if mo>bud else "OK"])
    w.writerow(["Subscriptions total","","Monthly",f"{total_sub:.2f}",f"{total_sub:.2f}","",""])
    w.writerow([]);w.writerow(["GOALS","","","","",""])
    w.writerow(["Name","Priority","Target","Saved","Progress","Remaining"])
    for g in st.session_state.goals:
        tgt=goal_target(g); sav=goal_saved(g); pg=sav/tgt*100 if tgt>0 else 0
        w.writerow([g["name"],g.get("priority",""),f"{tgt:.2f}",f"{sav:.2f}",f"{pg:.0f}%",f"{max(0,tgt-sav):.2f}"])
    w.writerow([]);w.writerow(["ASSETS","",""])
    w.writerow(["Name","Type","Value"])
    for a in st.session_state.assets: w.writerow([a["name"],a["type"],f"{a['value']:.2f}"])
    w.writerow([]);w.writerow(["LIABILITIES","","","",""])
    w.writerow(["Name","Type","Balance","Rate%","Min Payment"])
    for l in st.session_state.liabilities:
        w.writerow([l["name"],l["type"],f"{l['balance']:.2f}",f"{l.get('rate',0):.2f}",f"{l.get('min_payment',0):.2f}"])
    if st.session_state.transactions:
        w.writerow([]);w.writerow(["TRANSACTIONS","","",""])
        w.writerow(["Date","Description","Amount","Category"])
        for tx in st.session_state.transactions:
            w.writerow([tx.get("Date",""),tx.get("Description",""),f"{tx.get('Amount',0):.2f}",tx.get("Category","")])
    w.writerow([]);w.writerow(["Educational use only. Not financial advice."])
    return buf.getvalue().encode("utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# INVESTMENT GUIDE  — Australian-specific recommendations by risk profile
# ─────────────────────────────────────────────────────────────────────────────
INVEST_GUIDE = {
    "Conservative": {
        "summary": "Capital preservation with modest growth. Best for short horizons or retirees.",
        "items": [
            ("High-Yield Savings / Term Deposit", 30, "Safe, liquid, government-backed",
             ["ING Savings Maximiser","UBank Save","Macquarie Savings","Term deposits via banks"],"gr"),
            ("Australian Bond ETF", 28, "Fixed income, low volatility, stable returns",
             ["VAF — Vanguard AUS Fixed Interest","VACF — iShares Core AUS Bond","IAF — iShares AUS Composite Bond"],"bl"),
            ("Australian Shares ETF", 22, "Broad ASX 200/300, franked dividends",
             ["VAS — Vanguard AUS Shares","IOZ — iShares ASX 200","STW — SPDR ASX 200"],"gr"),
            ("International Shares ETF", 15, "Global diversification, USD exposure",
             ["VGS — Vanguard MSCI World","IWLD — iShares MSCI World","BGBL — Betashares Global Shares"],"bl"),
            ("Listed Investment Companies (LICs)", 5, "Steady franked dividends, long track record",
             ["AFI — Australian Foundation Investment","ARG — Argo Investments","MLT — Milton Corporation"],"pu"),
        ],
        "avoid": ["Individual stocks","Crypto","Leveraged ETFs","Speculative assets","Micro-caps"],
        "super": "Salary sacrifice up to $30k/yr into super. Choose a Balanced or Conservative super option.",
    },
    "Moderate": {
        "summary": "Balanced growth and stability. Ideal for 5–10 year investors.",
        "items": [
            ("Australian Shares ETF", 30, "Core ASX holdings, franked dividends, tax-effective",
             ["VAS — Vanguard AUS Shares","IOZ — iShares ASX 200","A200 — Betashares AUS 200"],"gr"),
            ("International Shares ETF", 28, "US and global market exposure",
             ["VGS — Vanguard MSCI World","IVV — iShares S&P 500","NDQ — Betashares NASDAQ 100"],"bl"),
            ("Bonds / Fixed Interest", 18, "Portfolio stability, reduces volatility",
             ["VAF — Vanguard AUS Fixed Interest","VBND — Vanguard Global Bond (AUD hedged)"],"am"),
            ("Listed REITs / Property ETF", 10, "Property exposure without buying real estate",
             ["VAP — Vanguard AUS Property","SLF — SPDR Property","MGR — Mirvac","GMG — Goodman Group"],"pu"),
            ("High-Yield Savings", 10, "Liquid emergency buffer",
             ["ING Savings Maximiser","Macquarie Savings","UBank Save Account"],"gr"),
            ("Crypto (small allocation)", 4, "Small speculative position only",
             ["BTC — Bitcoin via CoinSpot","ETH — Ethereum via Swyftx"],"rd"),
        ],
        "avoid": ["Concentrated single-stock bets >10%","High-fee managed funds (>0.5% MER)","Crypto >5%"],
        "super": "Check your super's investment option. Switch to Balanced or High Growth if under 50.",
    },
    "Growth": {
        "summary": "Higher long-term returns. Accepts short-term volatility. Horizon 7+ years.",
        "items": [
            ("International Shares ETF", 35, "Core global growth — US tech drives long-term gains",
             ["IVV — iShares S&P 500","NDQ — Betashares NASDAQ 100","VGS — Vanguard MSCI World"],"bl"),
            ("Australian Shares ETF", 25, "Domestic equities, dividend income, franking credits",
             ["VAS — Vanguard AUS Shares","A200 — Betashares AUS 200","IOZ — iShares ASX 200"],"gr"),
            ("Sector / Thematic ETFs", 15, "Higher conviction sectors for extra growth",
             ["RBTZ — Betashares Global Robots & AI","HACK — Betashares Cyber Security","CLNE — VanEck Clean Energy"],"pu"),
            ("Individual Stocks (ASX)", 10, "High conviction positions in quality companies",
             ["Research ASX growth/quality stocks","CBA, CSL, WES, REA, XRO as examples"],"am"),
            ("REITs", 7, "Property diversification with liquidity",
             ["VAP — Vanguard AUS Property","GMG — Goodman Group","MGR — Mirvac Group"],"bl"),
            ("Crypto", 8, "Speculative high-growth allocation",
             ["BTC — Bitcoin","ETH — Ethereum","via CoinSpot, Swyftx, or Binance AU"],"rd"),
        ],
        "avoid": ["Term deposits as main investment","Bond-heavy portfolios (>20%)","Cash drag"],
        "super": "Salary sacrifice to super — High Growth option recommended. Consider SMSFs if portfolio >$250k.",
    },
    "Aggressive": {
        "summary": "Maximum growth. Long horizon 10+ years. High volatility fully accepted.",
        "items": [
            ("International ETF — Growth Heavy", 33, "US/global growth markets are the core engine",
             ["IVV — iShares S&P 500","NDQ — Betashares NASDAQ 100","QQQ (via Stake/eToro for US)"],"bl"),
            ("Individual Stocks (ASX + US)", 25, "High conviction picks for alpha generation",
             ["ASX: quality growth companies","US stocks via Stake, eToro, or moomoo"],"gr"),
            ("Sector ETFs — Disruptive Tech", 15, "High-growth, high-risk sector bets",
             ["RBTZ — Robots & AI","HACK — Cyber Security","ESPO — Video Gaming & Esports"],"pu"),
            ("Crypto", 15, "Significant speculative allocation — high risk/reward",
             ["BTC — Bitcoin (60% of crypto allocation)","ETH — Ethereum (30%)","Altcoins via CoinSpot (10%)"],"rd"),
            ("Small-Caps / Micro-Caps", 12, "Small companies with outsized growth potential",
             ["MVS — VanEck Small Companies Masters","IEM — iShares MSCI Emerging Markets"],"am"),
        ],
        "avoid": ["Bonds as primary holding","High cash allocation >10%","Defensive assets (if long-term)"],
        "super": "Max salary sacrifice to super. Choose High Growth or International Shares super option. Consider SMSF.",
    },
}

def gen_pdf(period="Monthly"):
    """Generate comprehensive PDF report with charts."""
    if not PDF_OK: return None

    def sec(pdf, title):
        pdf.set_fill_color(5,100,70); pdf.set_text_color(255,255,255)
        pdf.set_font("Helvetica","B",11)
        pdf.cell(0,8,_p(f"  {title}"),fill=True,ln=True)
        pdf.set_text_color(30,30,30); pdf.ln(2)

    def row2(pdf,label,value,alt=False,green=False,red=False):
        pdf.set_fill_color(242,252,246) if alt else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(80,80,80)
        pdf.cell(100,7,_p(f"  {label}"),fill=True)
        pdf.set_font("Helvetica","B",9)
        if green: pdf.set_text_color(5,100,70)
        elif red: pdf.set_text_color(180,30,30)
        else: pdf.set_text_color(30,30,30)
        pdf.cell(85,7,_p(f"  {value}"),fill=True,ln=True)
        pdf.set_text_color(30,30,30)

    sr=(total_income-total_exp)/total_income*100 if total_income>0 else 0
    grade_="Excellent" if hs>=80 else "Good" if hs>=65 else "Fair" if hs>=50 else "Needs Work" if hs>=35 else "Critical"
    sc=(5,168,90) if hs>=70 else (217,119,6) if hs>=50 else (185,28,28)
    risk_sel=st.session_state.get("risk_profile","Moderate")
    age_val=st.session_state.get("age",32)

    pdf=FPDF(); pdf.set_auto_page_break(auto=True,margin=18)

    # ── PAGE 1: Cover + Overview ──────────────────────────────────────────────
    pdf.add_page()
    # Header banner
    pdf.set_fill_color(10,62,44); pdf.rect(0,0,210,42,"F")
    pdf.set_font("Helvetica","B",22); pdf.set_text_color(200,255,225)
    pdf.cell(0,18,"",ln=True)
    pdf.cell(0,13,_p("  Seralung Finance"),ln=True)
    pdf.set_font("Helvetica","",10); pdf.set_text_color(120,210,170)
    pdf.cell(0,7,_p(f"  {period} Financial Report   |   {datetime.now().strftime('%d %B %Y')}"),ln=True)
    pdf.ln(7)

    # Health score + grade
    pdf.set_font("Helvetica","B",14); pdf.set_text_color(30,30,30)
    pdf.cell(0,9,_p("Financial Health Score"),ln=True)
    pdf.set_font("Helvetica","B",52); pdf.set_text_color(*sc)
    pdf.cell(50,18,_p(f"{hs}"),)
    pdf.set_font("Helvetica","",14); pdf.set_text_color(80,80,80)
    pdf.cell(0,18,_p(f"/ 100  -  {grade_}"),ln=True)
    pdf.set_text_color(30,30,30); pdf.ln(2)

    # Key metrics 2-col
    pdf.set_font("Helvetica","B",12); pdf.cell(0,8,_p("Monthly Snapshot"),ln=True)
    metrics=[("Monthly Income",fmt(total_income)),("Monthly Expenses",fmt(total_exp)),
             ("Cash Flow",fmt(cash_flow)),("Savings Rate",pct(sr)),
             ("Net Worth",fmt(net_worth)),("Emergency Fund",f"{em_months:.1f} months")]
    for i,(l,v) in enumerate(metrics): row2(pdf,l,v,i%2==0)
    pdf.ln(4)

    # Budget rule
    sec(pdf,"Budget Rule (Needs / Wants / Save & Invest)")
    needs_cats={"Housing","Transport","Health","Insurance","Education"}
    needs_actual=sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses if e.get("category") in needs_cats)
    wants_actual=sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses if e.get("category") not in needs_cats)+total_sub
    for lbl,actual,budget in [("Needs",needs_actual,total_income*needs_pct/100),
                               ("Wants",wants_actual,total_income*wants_pct/100),
                               ("Save & Invest",investable,investable)]:
        p=min(200,actual/budget*100) if budget>0 else 0
        status="OVER BUDGET" if p>100 else "On track"
        row2(pdf,f"{lbl}  ({fmt(actual)} / {fmt(budget)})",f"{p:.0f}%  {status}",green=p<=100,red=p>100)
    pdf.ln(3)

    # Score breakdown
    sec(pdf,"Health Score Breakdown")
    pdf.set_fill_color(5,100,70); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
    for h_,w_ in [("  Pillar",85),("Score",25),("Max",20),("Value",40),("Status",20)]:
        pdf.cell(w_,7,_p(h_),fill=True)
    pdf.ln()
    for i,(name,d) in enumerate(hs_det.items()):
        pdf.set_fill_color(242,252,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(60,60,60)
        pdf.cell(85,7,_p(f"  {name}"),fill=True)
        pdf.set_text_color(5,100,70) if d["ok"] else pdf.set_text_color(185,28,28)
        pdf.set_font("Helvetica","B",9)
        pdf.cell(25,7,_p(f"{d['score']:.0f}"),fill=True)
        pdf.set_text_color(60,60,60); pdf.set_font("Helvetica","",9)
        pdf.cell(20,7,_p(f"{d['max']}"),fill=True)
        pdf.cell(40,7,_p(d["val"]),fill=True)
        pdf.set_text_color(5,100,70) if d["ok"] else pdf.set_text_color(185,28,28)
        pdf.cell(20,7,_p("Good" if d["ok"] else "Low"),fill=True,ln=True)
    pdf.set_text_color(30,30,30)

    # ── PAGE 2: Spending Charts ───────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(10,62,44); pdf.rect(0,0,210,12,"F")
    pdf.set_font("Helvetica","B",11); pdf.set_text_color(200,255,225)
    pdf.cell(0,12,_p("  Seralung Finance   |   Spending Analysis"),ln=True)
    pdf.set_text_color(30,30,30); pdf.ln(4)

    # Spending donut chart
    sec(pdf,"Spending by Category")
    if st.session_state.expenses:
        df_e2=pd.DataFrame(st.session_state.expenses)
        df_e2["mo"]=df_e2.apply(lambda r:to_mo(r["amount"],r.get("freq","Monthly")),axis=1)
        df_e2=df_e2[df_e2["mo"]>0]
        if not df_e2.empty:
            cat_df=df_e2.groupby("category")["mo"].sum().reset_index()
            cc=["#059669","#2563EB","#D97706","#DC2626","#7C3AED","#0891B2","#BE185D","#0284C7","#16A34A","#9333EA"]
            n=len(cat_df); colors=(cc*3)[:n]
            fig_d=go.Figure(go.Pie(labels=cat_df["category"],values=cat_df["mo"],hole=0.55,
                marker=dict(colors=colors,line=dict(color="#ffffff",width=2)),
                textfont=dict(size=13),textposition="outside"))
            fig_d.update_layout(paper_bgcolor="#ffffff",plot_bgcolor="#ffffff",
                height=420,margin=dict(l=20,r=20,t=20,b=20),showlegend=True,
                legend=dict(font=dict(size=12)),
                font=dict(family="Inter,sans-serif",color="#374151"))
            _pdf_img(pdf,_fig_png(fig_d,1000,430))

    # Spent vs budget bar
    pdf.ln(3); sec(pdf,"Expenses — Spent vs Budget")
    if st.session_state.expenses:
        df3=pd.DataFrame(st.session_state.expenses)
        df3["mo"]=df3.apply(lambda r:to_mo(r["amount"],r.get("freq","Monthly")),axis=1)
        cat_s=df3.groupby("category").agg({"mo":"sum","budget":"sum"}).reset_index()
        fig_b=go.Figure()
        fig_b.add_trace(go.Bar(name="Budget",x=cat_s["category"],y=cat_s["budget"],
            marker_color="rgba(5,150,105,0.3)",marker_line=dict(color="#059669",width=1.5)))
        fig_b.add_trace(go.Bar(name="Spent",x=cat_s["category"],y=cat_s["mo"],
            marker_color="#059669",
            text=[f"${v:,.0f}" for v in cat_s["mo"]],textposition="outside"))
        fig_b.update_layout(barmode="overlay",paper_bgcolor="#ffffff",plot_bgcolor="#ffffff",
            height=360,margin=dict(l=20,r=20,t=20,b=20),
            font=dict(family="Inter,sans-serif",color="#374151",size=12),
            legend=dict(orientation="h"),yaxis=dict(tickprefix="$"))
        _pdf_img(pdf,_fig_png(fig_b,1100,380))

    # Expense table
    pdf.ln(2); sec(pdf,"Expense Detail")
    pdf.set_fill_color(5,100,70); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
    for h_,w_ in [("  Name",60),("Category",28),("Freq",18),("Spent",24),("Budget",24),("Monthly",24),("Status",17)]:
        pdf.cell(w_,7,_p(h_),fill=True)
    pdf.ln()
    for i,e in enumerate(st.session_state.expenses):
        mo=to_mo(e["amount"],e.get("freq","Monthly")); bud=e.get("budget",e["amount"]); over=mo>bud
        pdf.set_fill_color(242,252,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",8.5); pdf.set_text_color(50,50,50)
        pdf.cell(60,7,_p(f"  {e['name'][:22]}"),fill=True)
        pdf.cell(28,7,_p(e.get("category","")[:11]),fill=True)
        pdf.cell(18,7,_p(e.get("freq","Mo")[:2]),fill=True)
        pdf.cell(24,7,_p(f"${e['amount']:,.0f}"),fill=True)
        pdf.cell(24,7,_p(f"${bud:,.0f}"),fill=True)
        pdf.cell(24,7,_p(f"${mo:,.0f}"),fill=True)
        pdf.set_text_color(180,30,30) if over else pdf.set_text_color(5,120,60)
        pdf.set_font("Helvetica","B",8.5)
        pdf.cell(17,7,_p("OVER" if over else "OK"),fill=True,ln=True)
    pdf.set_text_color(30,30,30)

    # ── PAGE 3: Net Worth + Goals ─────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(10,62,44); pdf.rect(0,0,210,12,"F")
    pdf.set_font("Helvetica","B",11); pdf.set_text_color(200,255,225)
    pdf.cell(0,12,_p("  Seralung Finance   |   Net Worth & Goals"),ln=True)
    pdf.set_text_color(30,30,30); pdf.ln(4)

    # Net worth headline
    nw_c=(5,168,90) if net_worth>=0 else (185,28,28)
    pdf.set_font("Helvetica","B",11); pdf.cell(0,8,_p("Net Worth"),ln=True)
    pdf.set_font("Helvetica","B",36); pdf.set_text_color(*nw_c)
    pdf.cell(0,14,_p(fmt(net_worth)),ln=True); pdf.set_text_color(30,30,30)

    # Waterfall chart
    if st.session_state.assets or st.session_state.liabilities:
        wf_x=[a["name"] for a in st.session_state.assets]+[l["name"] for l in st.session_state.liabilities]+["Net Worth"]
        wf_m=["relative"]*len(st.session_state.assets)+["relative"]*len(st.session_state.liabilities)+["total"]
        wf_y=[a["value"] for a in st.session_state.assets]+[-l["balance"] for l in st.session_state.liabilities]+[0]
        fig_wf=go.Figure(go.Waterfall(x=wf_x,measure=wf_m,y=wf_y,
            connector=dict(line=dict(color="#E5E7EB",width=0.5)),
            increasing=dict(marker=dict(color="#059669")),
            decreasing=dict(marker=dict(color="#DC2626")),
            totals=dict(marker=dict(color="#059669" if net_worth>=0 else "#DC2626")),
            texttemplate="%{y:$,.0f}",textposition="outside",textfont=dict(size=11)))
        fig_wf.update_layout(paper_bgcolor="#ffffff",plot_bgcolor="#ffffff",
            height=360,margin=dict(l=20,r=20,t=20,b=20),
            font=dict(family="Inter,sans-serif",color="#374151",size=12),
            yaxis=dict(tickprefix="$"))
        _pdf_img(pdf,_fig_png(fig_wf,1100,380)); pdf.ln(2)

    # Assets
    sec(pdf,"Assets")
    pdf.set_fill_color(5,100,70); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
    for h_,w_ in [("  Name",100),("Type",45),("Value",45)]: pdf.cell(w_,7,_p(h_),fill=True)
    pdf.ln()
    for i,a in enumerate(st.session_state.assets):
        pdf.set_fill_color(242,252,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(50,50,50)
        pdf.cell(100,7,_p(f"  {a['name']}"),fill=True); pdf.cell(45,7,_p(a["type"]),fill=True)
        pdf.set_font("Helvetica","B",9); pdf.set_text_color(5,100,70)
        pdf.cell(45,7,_p(f"+{fmt(a['value'])}"),fill=True,ln=True)
    pdf.set_text_color(30,30,30); pdf.ln(2)

    # Liabilities
    sec(pdf,"Liabilities")
    pdf.set_fill_color(5,100,70); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
    for h_,w_ in [("  Name",80),("Type",35),("Balance",35),("Rate",20),("Annual Int.",20)]: pdf.cell(w_,7,_p(h_),fill=True)
    pdf.ln()
    for i,l in enumerate(st.session_state.liabilities):
        ann_i=l["balance"]*l.get("rate",0)/100
        pdf.set_fill_color(255,242,242) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(50,50,50)
        pdf.cell(80,7,_p(f"  {l['name']}"),fill=True); pdf.cell(35,7,_p(l["type"]),fill=True)
        pdf.set_font("Helvetica","B",9); pdf.set_text_color(185,28,28)
        pdf.cell(35,7,_p(f"-{fmt(l['balance'])}"),fill=True)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(50,50,50)
        pdf.cell(20,7,_p(f"{l.get('rate',0):.1f}%"),fill=True)
        pdf.cell(20,7,_p(fmt(ann_i)),fill=True,ln=True)
    pdf.set_text_color(30,30,30); pdf.ln(4)

    # Goals with visual bar
    sec(pdf,"Financial Goals")
    pdf.set_fill_color(5,100,70); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
    for h_,w_ in [("  Goal",70),("Priority",24),("Target",28),("Saved",28),("Progress",22),("ETA"),]:
        pdf.cell(w_ if h_!="ETA" else 18,7,_p(h_),fill=True)
    pdf.ln()
    investable_=investable if investable>0 else 1
    for i,g in enumerate(st.session_state.goals):
        tgt=goal_target(g); sav=goal_saved(g); pg=min(100,sav/tgt*100) if tgt>0 else 0
        rem=max(0,tgt-sav); mo_g=math.ceil(rem/investable_)
        eta=f"{mo_g}mo" if rem>0 else "Done"
        pdf.set_fill_color(242,252,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(50,50,50)
        pdf.cell(70,7,_p(f"  {g['name'][:25]}"),fill=True)
        pdf.cell(24,7,_p(g.get("priority","Med")),fill=True)
        pdf.cell(28,7,_p(fmt(tgt)),fill=True); pdf.cell(28,7,_p(fmt(sav)),fill=True)
        pdf.set_font("Helvetica","B",9); pdf.set_text_color(5,100,70)
        pdf.cell(22,7,_p(f"{pg:.0f}%"),fill=True)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(50,50,50)
        pdf.cell(18,7,_p(eta),fill=True,ln=True)
    pdf.set_text_color(30,30,30)

    # Goals chart
    if st.session_state.goals:
        names=[g["name"][:18] for g in st.session_state.goals]
        saved_=[goal_saved(g) for g in st.session_state.goals]
        remain=[max(0,goal_target(g)-goal_saved(g)) for g in st.session_state.goals]
        fig_g=go.Figure()
        fig_g.add_trace(go.Bar(name="Saved",y=names,x=saved_,orientation="h",marker_color="#059669"))
        fig_g.add_trace(go.Bar(name="Remaining",y=names,x=remain,orientation="h",marker_color="#E5E7EB"))
        fig_g.update_layout(barmode="stack",paper_bgcolor="#ffffff",plot_bgcolor="#ffffff",
            height=max(220,len(names)*55),margin=dict(l=10,r=20,t=20,b=20),
            font=dict(family="Inter,sans-serif",color="#374151",size=12),
            legend=dict(orientation="h"),xaxis=dict(tickprefix="$"))
        _pdf_img(pdf,_fig_png(fig_g,1100,max(280,len(names)*65)))

    # ── PAGE 4: Investment Projection ─────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(10,62,44); pdf.rect(0,0,210,12,"F")
    pdf.set_font("Helvetica","B",11); pdf.set_text_color(200,255,225)
    pdf.cell(0,12,_p("  Seralung Finance   |   Investment Projection & Risk"),ln=True)
    pdf.set_text_color(30,30,30); pdf.ln(4)

    # Investment summary
    sec(pdf,"Investment Profile")
    ret_age_=st.session_state.get("retirement_age",65); yrs_left_=max(1,ret_age_-age_val)
    exp_mu_={"Conservative":0.055,"Moderate":0.07,"Growth":0.09,"Aggressive":0.12}.get(risk_sel,0.07)
    row2(pdf,"Risk Profile",risk_sel,alt=True)
    row2(pdf,"Age / Retirement Age",f"{age_val} / {ret_age_}")
    row2(pdf,"Years to Retirement",f"{yrs_left_} years",alt=True)
    row2(pdf,"Monthly Investable",fmt(investable))
    row2(pdf,"Expected Return (assumed)",f"{exp_mu_*100:.1f}% p.a.",alt=True)
    row2(pdf,"Annual Investable",fmt(investable*12))

    # 25-year projection
    pdf.ln(3); sec(pdf,"25-Year Growth Projection")
    yrs=list(range(26))
    def cmpd(r):
        v,res=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings","Super"])),[]
        for _ in yrs: res.append(round(v)); v=(v+investable*12)*(1+r)
        return res
    c4_=cmpd(0.04); c7_=cmpd(0.07); c10_=cmpd(0.10); c_r=cmpd(exp_mu_)
    fig_p=go.Figure()
    fig_p.add_trace(go.Scatter(x=yrs,y=c4_,name="Conservative 4%",mode="lines",line=dict(color="#6B7280",width=1.5,dash="dot")))
    fig_p.add_trace(go.Scatter(x=yrs,y=c7_,name="Moderate 7%",mode="lines",line=dict(color="#2563EB",width=2,dash="dash")))
    fig_p.add_trace(go.Scatter(x=yrs,y=c10_,name="Growth 10%",mode="lines",line=dict(color="#D97706",width=2)))
    fig_p.add_trace(go.Scatter(x=yrs,y=c_r,name=f"Your profile ({exp_mu_*100:.1f}%)",mode="lines",
        line=dict(color="#059669",width=3),fill="tozeroy",fillcolor="rgba(5,150,105,0.07)"))
    fig_p.update_layout(paper_bgcolor="#ffffff",plot_bgcolor="#ffffff",
        height=380,margin=dict(l=20,r=20,t=20,b=30),
        font=dict(family="Inter,sans-serif",color="#374151",size=12),
        legend=dict(orientation="h",y=-0.18),
        xaxis=dict(title="Years",tickvals=[0,5,10,15,20,25]),
        yaxis=dict(tickprefix="$",tickformat=",.0f"))
    _pdf_img(pdf,_fig_png(fig_p,1100,410)); pdf.ln(3)

    # Milestone table
    sec(pdf,"Portfolio Milestones")
    pdf.set_fill_color(5,100,70); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
    for h_,w_ in [("Year",18),("Conservative 4%",43),("Moderate 7%",43),("Growth 10%",43),("Your Profile",43)]:
        pdf.cell(w_,7,_p(h_),fill=True)
    pdf.ln()
    for i,yr in enumerate([1,3,5,10,15,20,25]):
        pdf.set_fill_color(242,252,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",9); pdf.set_text_color(50,50,50)
        pdf.cell(18,7,_p(f"  {yr}"),fill=True)
        pdf.cell(43,7,_p(fmt(c4_[yr])),fill=True); pdf.cell(43,7,_p(fmt(c7_[yr])),fill=True)
        pdf.cell(43,7,_p(fmt(c10_[yr])),fill=True)
        pdf.set_font("Helvetica","B",9); pdf.set_text_color(5,100,70)
        pdf.cell(43,7,_p(fmt(c_r[yr])),fill=True,ln=True)
    pdf.set_text_color(30,30,30); pdf.ln(3)

    # Investment recommendations
    sec(pdf,f"Investment Recommendations  -  {risk_sel} Profile")
    guide=INVEST_GUIDE.get(risk_sel,INVEST_GUIDE["Moderate"])
    pdf.set_font("Helvetica","I",9); pdf.set_text_color(80,80,80)
    pdf.multi_cell(0,5,_p(guide["summary"])); pdf.ln(2)
    pdf.set_fill_color(5,100,70); pdf.set_text_color(255,255,255); pdf.set_font("Helvetica","B",9)
    for h_,w_ in [("  Asset Class",60),("Alloc",18),("Why",62),("Products",50)]: pdf.cell(w_,7,_p(h_),fill=True)
    pdf.ln()
    for i,(name,alloc_pct,why,products,_) in enumerate(guide["items"]):
        mo_=investable*alloc_pct/100
        pdf.set_fill_color(242,252,246) if i%2==0 else pdf.set_fill_color(255,255,255)
        pdf.set_font("Helvetica","",8.5); pdf.set_text_color(50,50,50)
        pdf.cell(60,7,_p(name[:28]),fill=True)
        pdf.set_font("Helvetica","B",8.5); pdf.set_text_color(5,100,70)
        pdf.cell(18,7,_p(f"{alloc_pct}%"),fill=True)
        pdf.set_font("Helvetica","",8.5); pdf.set_text_color(50,50,50)
        pdf.cell(62,7,_p(why[:38]),fill=True)
        pdf.cell(50,7,_p(products[0][:24]),fill=True,ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica","B",9); pdf.set_text_color(5,100,70)
    pdf.cell(0,7,_p("Superannuation Tip:"),ln=True)
    pdf.set_font("Helvetica","",8.5); pdf.set_text_color(60,60,60)
    pdf.multi_cell(0,5,_p(guide["super"])); pdf.ln(2)
    avoid_txt="Avoid: " + ", ".join(guide["avoid"])
    pdf.set_font("Helvetica","I",8.5); pdf.set_text_color(185,28,28)
    pdf.multi_cell(0,5,_p(avoid_txt))

    # FIRE
    pdf.ln(3); sec(pdf,"FIRE Calculator (Financial Independence)")
    ann_exp_=total_exp*12; fire_t_=ann_exp_*25; fi_r_=cur_p_/fire_t_*100 if fire_t_>0 else 0
    cur_p_=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings"]))
    for i,(l,v) in enumerate([("Annual Expenses",fmt(ann_exp_)),("FIRE Number (25x)",fmt(fire_t_)),
            ("Current Portfolio",fmt(cur_p_)),("FI Ratio",f"{fi_r_:.1f}%"),
            ("Years to FIRE (at 7%)",f"{next((yr for yr in range(51) if (lambda v2:v2)(cur_p_*(1.07**yr)+investable*12*((1.07**yr-1)/0.07))>=fire_t_), 'N/A')} yrs")]):
        row2(pdf,l,v,i%2==0,green=("FIRE" in l or "FI" in l))

    # Footer
    pdf.ln(6); pdf.set_font("Helvetica","I",8); pdf.set_text_color(150,150,150)
    pdf.cell(0,5,_p("Seralung Finance  |  Educational use only. Not financial advice. Always consult a qualified financial adviser.  |  AUS Tax FY2024-25"),ln=True)
    return bytes(pdf.output())

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### Seralung Finance")
    theme_name = st.selectbox("Theme", list(THEMES.keys()), index=0)
    T = THEMES[theme_name]
    st.divider()
    if AUTH_ENABLED:
        try:
            sb=init_supabase()
            if not get_user(): restore_session(sb)
            if get_user():
                st.markdown(f"<div style='font-size:.8rem;font-weight:600;margin-bottom:.5rem;'>{get_user().email}</div>",unsafe_allow_html=True)
                sc1,sc2=st.columns(2)
                with sc1:
                    if st.button("💾 Save",use_container_width=True):
                        if save_user_data(sb): st.success("Saved!")
                with sc2:
                    if st.button("Sign out",use_container_width=True): logout(sb)
                st.divider()
        except Exception: pass
    if st.button("Reset to demo",use_container_width=True):
        keep={"sb_user","sb_access_token","sb_refresh_token","sb_client","data_loaded"}
        for k in [k for k in list(st.session_state) if k not in keep]: del st.session_state[k]
        st.rerun()
    st.caption("Educational only · Not financial advice")

# ─────────────────────────────────────────────────────────────────────────────
# AUTH GATE
# ─────────────────────────────────────────────────────────────────────────────
if AUTH_ENABLED:
    try:
        if not get_user(): login_page(sb,T); st.stop()
        if not st.session_state.get("data_loaded"):
            load_user_data(sb); st.session_state["data_loaded"]=True
    except Exception: pass

# ─────────────────────────────────────────────────────────────────────────────
# PLOT HELPER
# ─────────────────────────────────────────────────────────────────────────────
def plo(title="",h=280,mg=None):
    mg=mg or dict(l=8,r=8,t=36 if title else 10,b=10)
    d=dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
           font=dict(family="Inter,sans-serif",color=T["muted"],size=11),
           height=h,margin=mg,
           legend=dict(font=dict(color=T["muted"],size=11),bgcolor="rgba(0,0,0,0)",borderwidth=0),
           xaxis=dict(gridcolor=h2r(T["border"],0.6),linecolor=T["border"],color=T["muted"],showgrid=True),
           yaxis=dict(gridcolor=h2r(T["border"],0.6),linecolor=T["border"],color=T["muted"],showgrid=True))
    if title: d["title"]=dict(text=title,font=dict(color=T["text"],size=13,family="Inter,sans-serif"))
    return d

# ─────────────────────────────────────────────────────────────────────────────
# CSS  — clean, high contrast, professional
# ─────────────────────────────────────────────────────────────────────────────
A  = T["accent"]
A2 = T["accent2"]
TX = T["text"]
MU = T["muted"]
BG = T["bg"]
SU = T["surface"]
S2 = T["surface2"]
S3 = T["surface3"]
BO = T["border"]
SH = T["shadow"]
GR = T["green"]; RD = T["red"]; AM = T["amber"]; BL = T["blue"]; PU = T["purple"]
DK = T["dark"]
GL = T["glow"]
INPUT_BG = S2
INPUT_TX = TX

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html,body,.stApp{{background:{BG}!important;color:{TX}!important;font-family:Inter,sans-serif;-webkit-font-smoothing:antialiased;}}
*{{box-sizing:border-box;}}
p,span,div,label,li{{color:{TX};}}
h1,h2,h3,h4{{color:{TX}!important;font-weight:700;font-family:Inter,sans-serif;}}
::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-thumb{{background:{BO};border-radius:99px;}}
.block-container{{padding:.8rem 1.2rem 2rem!important;max-width:none!important;}}

/* Sidebar */
[data-testid="stSidebar"]{{background:{SU}!important;border-right:1px solid {BO}!important;}}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,[data-testid="stSidebar"] label{{color:{TX}!important;}}

/* Compact spacing */
[data-testid="stVerticalBlock"]>[data-testid="element-container"]{{margin-bottom:0!important;}}
[data-testid="stVerticalBlock"]>[data-testid="stHorizontalBlock"]{{margin-bottom:2px!important;}}
[data-testid="stNumberInput"],[data-testid="stTextInput"],[data-testid="stSelectbox"]{{margin-bottom:0!important;}}

/* Metrics */
[data-testid="metric-container"]{{
  background:{SU}!important;border:1px solid {BO}!important;
  border-radius:12px!important;padding:.75rem 1rem!important;
  box-shadow:{SH};transition:transform .18s;
}}
[data-testid="metric-container"]:hover{{transform:translateY(-2px);}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] *{{
  color:{MU}!important;font-size:.62rem!important;text-transform:uppercase;letter-spacing:.08em;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] *{{
  color:{TX}!important;font-weight:700!important;font-size:1.2rem!important;
}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] *{{font-size:.66rem!important;}}

/* Tabs */
[data-testid="stTabs"] [role="tab"]{{
  background:transparent;border:1.5px solid {BO};border-radius:8px;
  color:{MU}!important;font-size:.73rem;font-weight:500;
  padding:.26rem .65rem;margin-right:4px;transition:all .15s;
}}
[data-testid="stTabs"] [role="tab"]:hover{{color:{TX}!important;border-color:{A}!important;}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{{
  background:{A}!important;color:#ffffff!important;
  border-color:{A}!important;font-weight:600;
}}
[data-testid="stTabs"] [role="tablist"]{{
  border-bottom:1.5px solid {BO};padding-bottom:.5rem;flex-wrap:wrap;gap:3px;
}}

/* Inputs */
label,[data-testid="stWidgetLabel"]{{color:{TX}!important;font-size:.75rem!important;font-weight:500;}}
[data-testid="stNumberInput"] input,[data-testid="stTextInput"] input,textarea{{
  background:{S2}!important;border:1.5px solid {BO}!important;
  border-radius:8px!important;color:{TX}!important;font-size:.83rem!important;
}}
[data-testid="stNumberInput"] input:focus,[data-testid="stTextInput"] input:focus{{
  border-color:{A}!important;outline:none!important;
  box-shadow:0 0 0 3px {h2r(A,0.15)}!important;
}}
[data-testid="stSelectbox"]>div>div{{
  background:{S2}!important;border:1.5px solid {BO}!important;
  color:{TX}!important;border-radius:8px!important;font-size:.83rem!important;
}}
[data-testid="stSelectbox"] span{{color:{TX}!important;}}
[data-baseweb="slider"] [role="slider"]{{background:{A}!important;border-color:{A}!important;}}
[data-testid="stCheckbox"] span{{color:{TX}!important;}}
[data-testid="stRadio"] label span{{color:{TX}!important;}}

/* Buttons — always accent color, always readable */
.stButton>button{{
  background:{A}!important;border:none!important;border-radius:8px!important;
  color:#ffffff!important;font-weight:600!important;font-family:Inter,sans-serif!important;
  font-size:.79rem!important;transition:all .15s;
}}
.stButton>button:hover{{filter:brightness(1.08);transform:translateY(-1px);box-shadow:0 4px 12px {h2r(A,0.3)};}}
.stDownloadButton>button{{
  background:transparent!important;color:{A}!important;
  border:1.5px solid {A}!important;font-weight:600!important;
}}
.stDownloadButton>button:hover{{background:{h2r(A,0.08)}!important;}}

/* Sidebar buttons — MUST come after general button rules to win */
[data-testid="stSidebar"] .stButton>button{{
  background:{S2}!important;border:1.5px solid {BO}!important;
  color:{TX}!important;font-weight:500!important;border-radius:8px!important;
  font-size:.78rem!important;box-shadow:none!important;filter:none!important;transform:none!important;
}}
[data-testid="stSidebar"] .stButton>button:hover{{
  background:{A}!important;border-color:{A}!important;
  color:#ffffff!important;transform:none!important;box-shadow:none!important;
}}

/* Expander */
[data-testid="stExpander"]{{background:{SU}!important;border:1px solid {BO}!important;border-radius:12px!important;}}
[data-testid="stExpander"] summary *{{color:{TX}!important;}}
[data-testid="stFileUploader"]{{background:{S2}!important;border:2px dashed {BO}!important;border-radius:12px!important;}}
[data-testid="stAlert"] div{{color:{TX}!important;}}
hr{{border-color:{BO}!important;margin:.5rem 0!important;}}

/* Cards */
.card{{
  background:{SU};border:1px solid {BO};border-radius:14px;
  padding:1rem 1.2rem;margin-bottom:.75rem;box-shadow:{SH};
}}
.card-flat{{background:{S2};border-radius:10px;padding:.65rem .9rem;margin-bottom:.4rem;}}
.clabel{{font-size:.58rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:{MU};margin-bottom:.55rem;display:block;}}
.crow{{display:flex;justify-content:space-between;align-items:center;padding:.36rem 0;border-bottom:1px solid {BO};font-size:.79rem;color:{TX};}}
.crow:last-child{{border-bottom:none;font-weight:600;}}
.tip{{background:{h2r(A,0.08)};border-left:3px solid {A};border-radius:0 8px 8px 0;padding:.5rem .85rem;font-size:.79rem;line-height:1.55;margin-bottom:.65rem;color:{TX};}}
.tip b,.tip strong{{color:{A};}}
.pbar{{background:{S2};border-radius:99px;height:5px;overflow:hidden;margin:.2rem 0;}}
.pfill{{height:100%;border-radius:99px;}}
.bd{{display:inline-block;padding:2px 8px;border-radius:5px;font-size:.58rem;font-weight:700;letter-spacing:.04em;}}
.ok  {{background:{h2r(GR,.12)};color:{GR};border:1px solid {h2r(GR,.25)};}}
.warn{{background:{h2r(AM,.12)};color:{AM};border:1px solid {h2r(AM,.25)};}}
.bad {{background:{h2r(RD,.12)};color:{RD};border:1px solid {h2r(RD,.25)};}}
.blu {{background:{h2r(BL,.12)};color:{BL};border:1px solid {h2r(BL,.25)};}}
.pur {{background:{h2r(PU,.12)};color:{PU};border:1px solid {h2r(PU,.25)};}}
.grn {{background:{h2r(GR,.12)};color:{GR};border:1px solid {h2r(GR,.25)};}}
.acc-text{{color:{A};font-weight:700;}}
.divider-line{{height:1px;background:{BO};margin:.6rem 0;}}
/* Chat */
.chat-user{{background:{A};color:#fff;border-radius:14px 14px 4px 14px;padding:.55rem .85rem;font-size:.79rem;margin:.3rem 0;display:inline-block;max-width:88%;float:right;clear:both;line-height:1.5;}}
.chat-ai{{background:{S2};color:{TX};border-radius:14px 14px 14px 4px;padding:.55rem .85rem;font-size:.79rem;margin:.3rem 0;display:inline-block;max-width:92%;float:left;clear:both;line-height:1.55;border:1px solid {BO};}}
.chat-wrap::after{{content:'';display:table;clear:both;}}
/* Mobile */
@media(max-width:768px){{
  .block-container{{padding:.4rem .4rem 2rem!important;}}
  [data-testid="stTabs"] [role="tab"]{{font-size:.65rem;padding:.2rem .4rem;}}
  .card{{padding:.7rem .85rem;}}
}}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
hA,hB=st.columns([4,1])
with hA:
    st.markdown(f"<div style='margin-bottom:.1rem;'>"
                f"<span style='font-size:1.55rem;font-weight:800;color:{TX};letter-spacing:-.02em;'>Seralung Finance</span>"
                f"</div>"
                f"<div style='font-size:.72rem;color:{MU};margin-bottom:.6rem;letter-spacing:.01em;'>"
                f"Track. Spend. Build.</div>",unsafe_allow_html=True)
with hB:
    st.markdown(f"<div style='text-align:right;padding-top:.2rem;'>"
                f"<div style='font-size:.65rem;color:{MU};'>{datetime.now().strftime('%a, %d %b %Y')}</div>"
                f"<div style='font-size:.72rem;font-weight:700;color:{A};letter-spacing:.05em;margin-top:2px;'>AUD</div>"
                f"</div>",unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# INCOME — always visible, saved to Supabase
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"<span class='clabel'>Income & Budget Allocation</span>",unsafe_allow_html=True)
ic1,ic2,ic3,ic4,ic5=st.columns([2.2,2.2,1,1,1])
with ic1:
    primary_income=st.number_input("Take home income /mo ($)",min_value=0.0,
        value=float(st.session_state.get("primary_income",6000.0)),step=100.0,format="%.0f",key="pi")
    st.session_state["primary_income"]=primary_income
with ic2:
    other_income=st.number_input("Other income /mo ($)",min_value=0.0,
        value=float(st.session_state.get("other_income",500.0)),step=50.0,format="%.0f",key="oi")
    st.session_state["other_income"]=other_income
with ic3:
    needs_pct=st.number_input("Needs %",0,100,int(st.session_state.get("needs_pct",50)),1,key="np_n")
    st.session_state["needs_pct"]=needs_pct
with ic4:
    wants_pct=st.number_input("Wants %",0,100,int(st.session_state.get("wants_pct",30)),1,key="wp_n")
    st.session_state["wants_pct"]=wants_pct
with ic5:
    invest_pct=st.number_input("Save %",0,100,int(st.session_state.get("invest_pct",20)),1,key="ip_n")
    st.session_state["invest_pct"]=invest_pct

total_income=primary_income+other_income
psum=needs_pct+wants_pct+invest_pct
if psum!=100:
    st.warning(f"Budget percentages sum to {psum}% — must equal 100%.")
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# DERIVED VALUES
# ─────────────────────────────────────────────────────────────────────────────
total_sub   =sum(s["amount"] for s in st.session_state.subscriptions)
total_exp   =sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses)+total_sub
total_assets=sum(a["value"] for a in st.session_state.assets)
total_liab  =sum(l["balance"] for l in st.session_state.liabilities)
net_worth   =total_assets-total_liab
investable  =total_income*invest_pct/100
needs_budget=total_income*needs_pct/100
wants_budget=total_income*wants_pct/100
cash_flow   =total_income-total_exp
savings_rate=cash_flow/total_income*100 if total_income>0 else 0
cash_assets =sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash","Savings"])
em_months   =cash_assets/total_exp if total_exp>0 else 0
hs,hs_det   =health_score_calc()
nw_col      =GR if net_worth>=0 else RD
if   hs>=80: grade="Excellent"
elif hs>=65: grade="Good"
elif hs>=50: grade="Fair"
elif hs>=35: grade="Needs Work"
else:        grade="Critical"

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tabs=st.tabs(["Overview","Budget","Goals","Invest & Risk","Reports","Insights","AI Chat"])
t1,t2,t3,t4,t5,t6,t7=tabs

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t1:
    ga,gb,gc,gd,ge,gf=st.columns([1.4,1,1,1,1,1])
    with ga:
        st.markdown(f"<div class='card' style='text-align:center;padding:.75rem;border-color:{A};'>"
                    f"<span class='clabel' style='text-align:center;display:block;'>Financial Health</span>"
                    f"{gauge_svg(hs,grade,S2,MU)}</div>",unsafe_allow_html=True)
    with gb: st.metric("Net Worth",    fmtk(net_worth),  "Positive" if net_worth>=0 else "Negative",   delta_color="normal" if net_worth>=0 else "inverse")
    with gc: st.metric("Cash Flow",    fmt(cash_flow),   "Surplus"  if cash_flow>=0 else "Deficit",    delta_color="normal" if cash_flow>=0 else "inverse")
    with gd: st.metric("Savings Rate", pct(savings_rate),"Target 20%",                                 delta_color="normal" if savings_rate>=20 else "inverse")
    with ge: st.metric("Emergency",    f"{em_months:.1f} mo","Safe 6+ mo" if em_months>=6 else "Low",  delta_color="normal" if em_months>=6 else "inverse")
    with gf: st.metric("Monthly Total",fmt(total_income),"Take home",                                  delta_color="off")

    st.markdown("<div style='height:.6rem'></div>",unsafe_allow_html=True)
    ov1,ov2=st.columns(2,gap="large")
    with ov1:
        # Budget overview
        st.markdown(f"<div class='card'><span class='clabel'>Budget — {needs_pct}/{wants_pct}/{invest_pct} rule</span>",unsafe_allow_html=True)
        needs_cats={"Housing","Transport","Health","Insurance","Education"}
        needs_actual=sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses if e.get("category") in needs_cats)
        wants_actual=sum(to_mo(e["amount"],e.get("freq","Monthly")) for e in st.session_state.expenses if e.get("category") not in needs_cats)+total_sub
        for lbl,actual,budget,col in [("Needs",needs_actual,needs_budget,BL),
                                       ("Wants",wants_actual,wants_budget,AM),
                                       ("Save & Invest",investable,investable,GR)]:
            p=min(100,actual/budget*100) if budget>0 else 0
            bc="ok" if p<=85 else "warn" if p<=100 else "bad"
            br=RD if p>100 else col
            st.markdown(f"<div style='margin-bottom:10px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.77rem;margin-bottom:3px;color:{TX};'>"
                        f"<span style='font-weight:500;'>{lbl}</span>"
                        f"<div><span style='color:{MU};margin-right:5px;'>{fmt(actual)}/{fmt(budget)}</span>"
                        f"<span class='bd {bc}'>{p:.0f}%</span></div></div>"
                        f"<div class='pbar'><div class='pfill' style='width:{p:.1f}%;background:{br};'></div></div>"
                        f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Score breakdown
        st.markdown(f"<div class='card'><span class='clabel'>Score Breakdown</span>",unsafe_allow_html=True)
        for name,d in hs_det.items():
            p=d["score"]/d["max"]*100
            bc="ok" if p>=70 else "warn" if p>=40 else "bad"
            br=GR if p>=70 else AM if p>=40 else RD
            st.markdown(f"<div style='margin-bottom:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:2px;color:{TX};'>"
                        f"<span style='font-weight:500;'>{name}</span>"
                        f"<div><span style='color:{MU};margin-right:4px;font-size:.7rem;'>{d['desc']}</span>"
                        f"<span class='bd {bc}'>{d['score']:.0f}/{d['max']}</span></div></div>"
                        f"<div class='pbar'><div class='pfill' style='width:{p:.1f}%;background:{br};'></div></div>"
                        f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    with ov2:
        # Donut
        df_e=pd.DataFrame(st.session_state.expenses)
        df_e["mo"]=df_e.apply(lambda r:to_mo(r["amount"],r.get("freq","Monthly")),axis=1)
        df_e=df_e[df_e["mo"]>0]
        if not df_e.empty:
            cat_df=df_e.groupby("category")["mo"].sum().reset_index()
            n=len(cat_df); cc=(T["chart"]*math.ceil(n/max(1,len(T["chart"]))))[:n]
            fig=go.Figure(go.Pie(labels=cat_df["category"],values=cat_df["mo"],hole=0.62,
                marker=dict(colors=cc,line=dict(color=BG,width=2)),
                textfont=dict(size=11,color=MU),
                hovertemplate="%{label}<br>$%{value:,.0f}/mo<br>%{percent}<extra></extra>"))
            fig.add_annotation(text=f"<b>{fmt(total_exp)}</b><br>/mo",
                x=0.5,y=0.5,showarrow=False,font=dict(color=TX,size=14,family="Inter"))
            fig.update_layout(**plo("Spending by Category",230))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

        # Bills
        today=date.today()
        st.markdown(f"<div class='card'><span class='clabel'>Upcoming Bills</span>",unsafe_allow_html=True)
        for bill in sorted(st.session_state.bills,key=lambda b:b["due_day"]):
            days=bill["due_day"]-today.day
            if days<0: days+=30
            bc="ok" if days>7 else "warn" if days>2 else "bad"
            bt="Today" if days==0 else f"in {days}d"
            st.markdown(f"<div class='crow'><span style='font-weight:500;'>{bill['name']}</span>"
                        f"<div><span style='color:{MU};margin-right:7px;'>{fmt(bill['amount'])}</span>"
                        f"<span class='bd {bc}'>{bt}</span></div></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Action items
        tips=[]
        if em_months<3:        tips.append(("bad","Emergency fund critical — under 3 months. Priority #1."))
        elif em_months<6:      tips.append(("warn",f"Emergency fund at {em_months:.1f} months. Target: {fmt(total_exp*6)}."))
        if savings_rate<10:    tips.append(("bad",f"Savings rate {savings_rate:.1f}% is very low. Target 20%."))
        elif savings_rate<20:  tips.append(("warn",f"Savings rate {savings_rate:.1f}%. Need {fmt(total_income*0.2-cash_flow)}/mo more."))
        hi=[l for l in st.session_state.liabilities if l.get("rate",0)>15]
        if hi: tips.append(("bad",f"High-interest debt {fmt(sum(l['balance'] for l in hi))} at >15%. Prioritise."))
        ob=[e for e in st.session_state.expenses if to_mo(e["amount"],e.get("freq","Monthly"))>e.get("budget",e["amount"])]
        if ob: tips.append(("warn",f"{len(ob)} expense(s) over budget: {', '.join(e['name'] for e in ob[:3])}."))
        if total_sub>150: tips.append(("warn",f"Subscriptions {fmt(total_sub)}/mo = {fmt(total_sub*12)}/yr."))
        if not tips: tips.append(("ok","All key ratios look healthy. Great work."))
        st.markdown(f"<div class='card'><span class='clabel'>Action Items</span>",unsafe_allow_html=True)
        for bc,text in tips[:5]:
            lbl="Good" if bc=="ok" else "Note" if bc=="warn" else "Action"
            st.markdown(f"<div style='padding:.38rem 0;border-bottom:1px solid {BO};font-size:.78rem;color:{TX};'>"
                        f"<span class='bd {bc}' style='margin-right:7px;'>{lbl}</span>{text}</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUDGET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t2:
    bc1,bc2=st.columns(2,gap="large")
    with bc1:
        st.markdown(f"<div class='card'><span class='clabel'>Monthly Expenses — Name · Amount · Budget · Freq · Category</span>",unsafe_allow_html=True)
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
        st.markdown(f"<div style='font-size:.6rem;color:{MU};padding:3px 0 5px;'>Name · Spent · Budget · Freq · Category</div>",unsafe_allow_html=True)
        r1,r2,r3,r4,r5=st.columns([2.2,1.3,1.3,0.9,1.5])
        with r1: nn2=st.text_input("New expense name",placeholder="e.g. Groceries",key="ne_n",label_visibility="collapsed")
        with r2: na2=st.number_input("Amount",min_value=0.0,step=10.0,key="ne_a",format="%.0f",label_visibility="collapsed")
        with r3: nb2=st.number_input("Budget",min_value=0.0,step=10.0,key="ne_b",format="%.0f",label_visibility="collapsed")
        with r4: nf2=st.selectbox("Freq",["Monthly","Weekly"],key="ne_f",label_visibility="collapsed")
        with r5: nc2=st.selectbox("Cat",CATEGORIES,key="ne_c",label_visibility="collapsed")
        if st.button("Add expense",use_container_width=True):
            if nn2: st.session_state.expenses.append({"name":nn2,"amount":float(na2),"budget":float(nb2) if nb2>0 else float(na2),"category":nc2,"freq":nf2}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

        st.markdown(f"<div class='card'><span class='clabel'>Subscriptions — {fmt(total_sub)}/mo · {fmt(total_sub*12)}/yr</span>",unsafe_allow_html=True)
        ds=None
        for i,s in enumerate(st.session_state.subscriptions):
            s1,s2,s3=st.columns([3.5,1.5,0.4])
            with s1:
                sn=st.text_input(f"sn{i}",value=s["name"],label_visibility="collapsed",key=f"sn_{i}")
                st.session_state.subscriptions[i]["name"]=sn
            with s2:
                sa=st.number_input(f"sa{i}",value=float(s["amount"]),min_value=0.0,step=.5,label_visibility="collapsed",key=f"sa_{i}",format="%.2f")
                st.session_state.subscriptions[i]["amount"]=sa
            with s3:
                if st.button("✕",key=f"sd_{i}"): ds=i
        if ds is not None: st.session_state.subscriptions.pop(ds); st.rerun()
        ss1,ss2=st.columns([3.5,1.5])
        with ss1: snn=st.text_input("Service",placeholder="e.g. Netflix",key="ns_n",label_visibility="collapsed")
        with ss2: sna=st.number_input("$/mo",min_value=0.0,step=.5,key="ns_a",format="%.2f",label_visibility="collapsed")
        if st.button("Add subscription",use_container_width=True):
            if snn: st.session_state.subscriptions.append({"name":snn,"amount":float(sna)}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

    with bc2:
        if st.session_state.expenses:
            df2=pd.DataFrame(st.session_state.expenses)
            df2["mo"]=df2.apply(lambda r:to_mo(r["amount"],r.get("freq","Monthly")),axis=1)
            cat_s=df2.groupby("category").agg({"mo":"sum","budget":"sum"}).reset_index()
            fig=go.Figure()
            fig.add_trace(go.Bar(name="Budget",x=cat_s["category"],y=cat_s["budget"],
                marker_color=h2r(GR,.3),marker_line=dict(color=GR,width=1.5)))
            fig.add_trace(go.Bar(name="Spent",x=cat_s["category"],y=cat_s["mo"],
                marker_color=A,text=[fmt(v) for v in cat_s["mo"]],textposition="outside",textfont=dict(color=TX,size=9)))
            fig.update_layout(**plo("Spent vs Budget",245)); fig.update_layout(barmode="overlay")
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

        st.markdown(f"<div class='card'><span class='clabel'>Per-Item Tracker</span>",unsafe_allow_html=True)
        for exp in sorted(st.session_state.expenses,key=lambda e:to_mo(e["amount"],e.get("freq","Monthly"))/max(e.get("budget",1),1),reverse=True):
            mo=to_mo(exp["amount"],exp.get("freq","Monthly"))
            bud=exp.get("budget",exp["amount"]); p=min(100,mo/bud*100) if bud>0 else 0
            bc="ok" if p<=85 else "warn" if p<=100 else "bad"
            br=RD if p>100 else AM if p>85 else GR
            fr=" (Wk)" if exp.get("freq")=="Weekly" else ""
            st.markdown(f"<div style='margin-bottom:7px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:2px;color:{TX};'>"
                        f"<span style='font-weight:500;'>{exp['name']}<span style='color:{MU};font-size:.65rem;'>{fr}</span></span>"
                        f"<div><span style='color:{MU};margin-right:4px;'>{fmt(mo)}/{fmt(bud)}</span>"
                        f"<span class='bd {bc}'>{p:.0f}%</span></div></div>"
                        f"<div class='pbar'><div class='pfill' style='width:{p:.1f}%;background:{br};'></div></div>"
                        f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        st.markdown(f"<div class='card'><span class='clabel'>Recurring Bills</span>",unsafe_allow_html=True)
        db_=None
        for i,bill in enumerate(st.session_state.bills):
            b1,b2,b3,b4=st.columns([2.8,1.5,0.9,0.4])
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
                if st.button("✕",key=f"bld_{i}"): db_=i
        if db_ is not None: st.session_state.bills.pop(db_); st.rerun()
        bb1,bb2,bb3=st.columns([2.8,1.5,0.9])
        with bb1: bnn=st.text_input("Bill",placeholder="e.g. Water",key="nb_n",label_visibility="collapsed")
        with bb2: bna=st.number_input("Amount",min_value=0.0,step=10.0,key="nb_a",format="%.0f",label_visibility="collapsed")
        with bb3: bnd=st.number_input("Day",min_value=1,max_value=31,value=1,key="nb_d",label_visibility="collapsed")
        if st.button("Add bill",use_container_width=True):
            if bnn: st.session_state.bills.append({"name":bnn,"amount":float(bna),"due_day":int(bnd)}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t3:
    total_target =sum(goal_target(g) for g in st.session_state.goals)
    total_saved_g=sum(goal_saved(g)  for g in st.session_state.goals)
    gm1,gm2,gm3,gm4=st.columns(4)
    gm1.metric("Total Target",fmt(total_target))
    gm2.metric("Total Saved",fmt(total_saved_g))
    gm3.metric("Remaining",fmt(max(0,total_target-total_saved_g)))
    gm4.metric("Overall",pct(total_saved_g/total_target*100) if total_target>0 else "0.0%")
    st.markdown("<div style='height:.4rem'></div>",unsafe_allow_html=True)
    g1,g2=st.columns([1.7,1],gap="large")
    with g1:
        del_g=None
        GOAL_COLORS={"red":RD,"blue":BL,"green":GR,"purple":PU,"amber":AM}
        for i,g in enumerate(st.session_state.goals):
            tgt=goal_target(g); sav=goal_saved(g)
            rem=max(0,tgt-sav); pg=min(100,sav/tgt*100) if tgt>0 else 0
            eta=f"{math.ceil(rem/investable)} mo" if investable>0 and rem>0 else ("Done!" if rem<=0 else "—")
            col_h=GOAL_COLORS.get(g.get("color","blue"),BL)
            pb_cls={"High":"bad","Medium":"warn","Low":"blu"}.get(g.get("priority","Medium"),"blu")
            gh,gd=st.columns([11,1])
            with gh:
                st.markdown(f"<div style='background:{SU};border:1px solid {BO};border-left:4px solid {col_h};"
                            f"border-radius:0 12px 12px 0;padding:.85rem 1rem;margin-bottom:.5rem;box-shadow:{SH};'>"
                            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem;'>"
                            f"<span style='font-weight:600;font-size:.9rem;color:{TX};'>{g['name']}</span>"
                            f"<div><span class='bd {pb_cls}' style='margin-right:6px;'>{g.get('priority','Med')}</span>"
                            f"<span style='font-size:.7rem;color:{MU};'>ETA: {eta}</span></div></div>"
                            f"<div style='font-size:.74rem;color:{MU};margin-bottom:5px;'>"
                            f"{fmt(sav)} saved of {fmt(tgt)} "
                            f"<span style='color:{col_h};font-weight:600;'>· {pg:.0f}% done</span></div>"
                            f"<div class='pbar' style='height:7px;'><div class='pfill' style='width:{pg:.1f}%;background:{col_h};'></div></div>"
                            f"<div style='font-size:.68rem;color:{MU};margin-top:3px;'>{fmt(rem)} remaining</div></div>",
                            unsafe_allow_html=True)
                ns=st.number_input(f"Saved ({g['name']})",value=float(sav),min_value=0.0,
                    max_value=float(max(tgt,sav)),step=100.0,key=f"gupd_{i}",format="%.0f",label_visibility="collapsed")
                if ns!=sav: st.session_state.goals[i]["saved"]=ns; st.rerun()
            with gd:
                st.markdown("<div style='margin-top:.5rem'></div>",unsafe_allow_html=True)
                if st.button("✕",key=f"gd_{i}"): del_g=i
        if del_g is not None: st.session_state.goals.pop(del_g); st.rerun()
    with g2:
        st.markdown(f"<div class='card'><span class='clabel'>Add Goal</span>",unsafe_allow_html=True)
        gname=st.text_input("Goal name",placeholder="e.g. House deposit")
        gtgt =st.number_input("Target ($)",min_value=0.0,step=1000.0,format="%.0f",key="g_tgt")
        gsav =st.number_input("Already saved ($)",min_value=0.0,step=100.0,format="%.0f",key="g_sav")
        gcol_=st.columns(2)
        with gcol_[0]: gpri=st.selectbox("Priority",["High","Medium","Low"])
        with gcol_[1]: gcol=st.selectbox("Colour",["blue","green","red","purple","amber"])
        if st.button("Add goal",use_container_width=True):
            if gname and gtgt>0:
                st.session_state.goals.append({"name":gname,"target":float(gtgt),"saved":float(gsav),"priority":gpri,"color":gcol}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)
        if st.session_state.goals and investable>0:
            st.markdown(f"<div class='card'><span class='clabel'>Smart Allocation of {fmt(investable)}/mo</span>",unsafe_allow_html=True)
            for pri,ap,cls in [("High",0.6,"bad"),("Medium",0.3,"warn"),("Low",0.1,"blu")]:
                gl=[g for g in st.session_state.goals if g.get("priority")==pri and goal_saved(g)<goal_target(g)]
                if gl:
                    pool=investable*ap; per=pool/len(gl)
                    st.markdown(f"<div style='font-size:.72rem;font-weight:600;color:{TX};margin:.4rem 0 .2rem;'>{pri} priority</div>",unsafe_allow_html=True)
                    for g in gl:
                        rem=max(0,goal_target(g)-goal_saved(g))
                        mo_g=math.ceil(rem/per) if per>0 else 9999
                        st.markdown(f"<div class='crow'><span style='font-size:.74rem;'>{g['name']}</span>"
                                    f"<div><span class='acc-text' style='font-size:.74rem;'>{fmt(per)}/mo</span>"
                                    f"<span style='color:{MU};font-size:.68rem;margin-left:4px;'>→ {mo_g} mo</span></div></div>",unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)
        # Net worth quick view
        st.markdown(f"<div class='card'><span class='clabel'>Net Worth</span>",unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:1.8rem;font-weight:800;color:{nw_col};text-align:center;padding:.2rem 0 .5rem;'>{fmt(net_worth)}</div>",unsafe_allow_html=True)
        for a in st.session_state.assets[:4]:
            st.markdown(f"<div class='crow'><span style='color:{MU};font-size:.74rem;'>{a['name']}</span><span style='color:{GR};font-size:.74rem;'>+{fmt(a['value'])}</span></div>",unsafe_allow_html=True)
        for l in st.session_state.liabilities[:3]:
            st.markdown(f"<div class='crow'><span style='color:{MU};font-size:.74rem;'>{l['name']}</span><span style='color:{RD};font-size:.74rem;'>-{fmt(l['balance'])}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INVEST & RISK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t4:
    st.markdown(f"<div class='tip'><b>{fmt(investable)}/month</b> available to save & invest ({invest_pct}% of income).</div>",unsafe_allow_html=True)
    ir1,ir2=st.columns(2,gap="large")
    with ir1:
        st.markdown(f"<div class='card'><span class='clabel'>Risk Profile & Projection</span>",unsafe_allow_html=True)
        rp_idx=RISK_LABELS.index(st.session_state.risk_profile) if st.session_state.risk_profile in RISK_LABELS else 1
        risk_sel=st.selectbox("Risk tolerance",RISK_LABELS,index=rp_idx)
        st.session_state.risk_profile=risk_sel
        age_val=st.slider("Your age",18,75,int(st.session_state.get("age",32)),1)
        st.session_state["age"]=age_val
        ret_age=st.slider("Target retirement age",50,75,int(st.session_state.get("retirement_age",65)),1)
        st.session_state["retirement_age"]=ret_age
        yrs_left=max(1,ret_age-age_val)
        exp_mu={"Conservative":0.055,"Moderate":0.07,"Growth":0.09,"Aggressive":0.12}.get(risk_sel,0.07)
        exp_sig={"Conservative":0.08,"Moderate":0.13,"Growth":0.17,"Aggressive":0.22}.get(risk_sel,0.13)
        st.caption(f"Assumed {exp_mu*100:.1f}% return · {exp_sig*100:.0f}% volatility · {yrs_left} years to retire")
        st.markdown("</div>",unsafe_allow_html=True)
        if st.button("Run Monte Carlo (200 paths)",use_container_width=True):
            init_p=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings","Super"]))
            with st.spinner("Simulating..."):
                np.random.seed(42)
                sims=monte_carlo(init_p,investable,yrs_left,200,exp_mu,exp_sig)
                mo=np.arange(sims.shape[1])
                p10=np.percentile(sims,10,axis=0); p50=np.percentile(sims,50,axis=0); p90=np.percentile(sims,90,axis=0)
                fig=go.Figure()
                fig.add_trace(go.Scatter(x=mo,y=p90,fill=None,mode="lines",line=dict(color="rgba(0,0,0,0)"),showlegend=False,hoverinfo="skip"))
                fig.add_trace(go.Scatter(x=mo,y=p10,fill="tonexty",mode="lines",fillcolor=h2r(GR,.1),line=dict(color="rgba(0,0,0,0)"),name="80% range",hoverinfo="skip"))
                fig.add_trace(go.Scatter(x=mo,y=p50,mode="lines",name="Median",line=dict(color=GR,width=2.5),hovertemplate="Month %{x}<br>$%{y:,.0f}<extra></extra>"))
                fig.update_yaxes(tickprefix="$",tickformat=",.0f"); fig.update_xaxes(title_text="Month")
                fig.update_layout(**plo("Monte Carlo Portfolio Projection",280))
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                rc=st.columns(3)
                rc[0].metric("Worst 10%",fmtk(p10[-1])); rc[1].metric("Median",fmtk(p50[-1])); rc[2].metric("Best 90%",fmtk(p90[-1]))

        # FIRE
        st.markdown(f"<div class='card'><span class='clabel'>FIRE Calculator</span>",unsafe_allow_html=True)
        ann_exp=st.number_input("Annual expenses ($)",min_value=0.0,value=float(total_exp*12),step=500.0,format="%.0f",key="f_exp")
        cur_p=st.number_input("Current portfolio ($)",min_value=0.0,
            value=float(sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings"])),step=1000.0,format="%.0f",key="f_p")
        fire_r=st.slider("Return % p.a.",1.0,15.0,float(exp_mu*100),0.5,key="f_rate",format="%.1f%%")
        fire_t=ann_exp*25; lean_t=ann_exp*20; fat_t=ann_exp*33
        fi_r=cur_p/fire_t*100 if fire_t>0 else 0
        st.markdown(f"<div style='text-align:center;margin:.3rem 0;'>"
                    f"<span style='font-size:2rem;font-weight:800;color:{A};'>{fi_r:.0f}%</span>"
                    f"<span style='font-size:.7rem;color:{MU};margin-left:6px;'>FI Ratio</span></div>",unsafe_allow_html=True)
        for lbl,tgt,col in [("Lean FIRE",lean_t,BL),("FIRE (4% rule)",fire_t,A),("Fat FIRE",fat_t,AM)]:
            p=min(100,cur_p/tgt*100) if tgt>0 else 0
            st.markdown(f"<div style='margin-bottom:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:2px;color:{TX};'>"
                        f"<span>{lbl}</span><span style='color:{MU};'>{p:.0f}% of {fmtk(tgt)}</span></div>"
                        f"<div class='pbar'><div class='pfill' style='width:{p:.1f}%;background:{col};'></div></div>"
                        f"</div>",unsafe_allow_html=True)
        if investable>0 and fire_t>0:
            yf=[]; vf=[]; v=cur_p; yr_hit=None
            for yr in range(51):
                yf.append(yr); vf.append(round(v))
                if v>=fire_t and yr_hit is None: yr_hit=yr
                v=(v+investable*12)*(1+fire_r/100)
            fig=go.Figure(go.Scatter(x=yf,y=vf,mode="lines",line=dict(color=GR,width=2),fill="tozeroy",fillcolor=h2r(GR,.08),hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
            for lbl,tgt,col in [("Lean",lean_t,BL),("FIRE",fire_t,AM),("Fat",fat_t,RD)]:
                fig.add_hline(y=tgt,line_dash="dot",line_color=col,annotation_text=lbl,annotation_font_color=col,annotation_font_size=10)
            fig.update_yaxes(tickprefix="$",tickformat=",.0f"); fig.update_xaxes(title_text="Years")
            fig.update_layout(**plo("Path to Financial Independence",240))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            if yr_hit: st.markdown(f"<div class='tip'>FIRE in <b>{yr_hit} years</b> at age <b>{age_val+yr_hit}</b>. Monthly withdrawal: <b>{fmt(fire_t*0.04/12)}</b>.</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    with ir2:
        # AUS Tax
        st.markdown(f"<div class='card'><span class='clabel'>AUS Tax Estimator — FY2024-25</span>",unsafe_allow_html=True)
        gross=st.number_input("Annual gross income ($)",min_value=0.0,value=float(primary_income*12),step=1000.0,format="%.0f",key="tax_g")
        tc1,tc2,tc3=st.columns(3)
        with tc1: im=st.checkbox("Medicare 2%",value=True)
        with tc2: il=st.checkbox("LITO",value=True)
        with tc3: ph=st.checkbox("Private health",value=False)
        tr=calc_tax(gross); med=gross*0.02 if im else 0
        mls=gross*0.01 if (not ph and gross>93000 and im) else 0
        lito=calc_lito(gross) if il else 0
        ttax=max(0,tr+med+mls-lito); net_ann=gross-ttax; eff=ttax/gross*100 if gross>0 else 0
        for lbl,val,col_,bld in [
            ("Gross income",fmt(gross),TX,False),("Income tax",f"-{fmt(tr)}",RD,False),
            ("Medicare levy",f"-{fmt(med)}",AM,False),("MLS surcharge",f"-{fmt(mls)}",RD,mls>0),
            ("LITO offset",f"+{fmt(lito)}",GR,False),
            ("Net annual",fmt(net_ann),A,True),("Net monthly",fmt(net_ann/12),A,True),
            ("Effective rate",pct(eff),AM,True)]:
            fw="font-weight:600;" if bld else ""
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid {BO};font-size:.79rem;{fw}color:{TX};'>"
                        f"<span style='color:{MU}'>{lbl}</span><span style='color:{col_}'>{val}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Assets & liabilities
        st.markdown(f"<div class='card'><span class='clabel'>Assets — Name / Value / Type</span>",unsafe_allow_html=True)
        da=None
        for i,a in enumerate(st.session_state.assets):
            a1,a2,a3,a4=st.columns([2.5,1.5,1.5,0.4])
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
                if st.button("✕",key=f"ad_{i}"): da=i
        if da is not None: st.session_state.assets.pop(da); st.rerun()
        na1,na2,na3=st.columns([2.5,1.5,1.5])
        with na1: new_an=st.text_input("Asset",placeholder="e.g. Shares",key="naa_n",label_visibility="collapsed")
        with na2: new_av=st.number_input("Value",min_value=0.0,step=100.0,key="naa_v",format="%.0f",label_visibility="collapsed")
        with na3: new_at=st.selectbox("Type",ASSET_TYPES,key="naa_t",label_visibility="collapsed")
        if st.button("Add asset",use_container_width=True):
            if new_an: st.session_state.assets.append({"name":new_an,"value":float(new_av),"type":new_at}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

        st.markdown(f"<div class='card'><span class='clabel'>Liabilities — Name / Balance / Rate% / Type</span>",unsafe_allow_html=True)
        dl=None
        for i,l in enumerate(st.session_state.liabilities):
            l1,l2,l3,l4,l5=st.columns([2.2,1.5,1,1.5,0.4])
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
                if st.button("✕",key=f"ld_{i}"): dl=i
        if dl is not None: st.session_state.liabilities.pop(dl); st.rerun()
        nl1,nl2,nl3,nl4=st.columns([2.2,1.5,1,1.5])
        with nl1: new_ln=st.text_input("Liability",placeholder="e.g. Car loan",key="nll_n",label_visibility="collapsed")
        with nl2: new_lb=st.number_input("Balance",min_value=0.0,step=100.0,key="nll_b",format="%.0f",label_visibility="collapsed")
        with nl3: new_lr=st.number_input("Rate",min_value=0.0,max_value=99.0,step=0.1,key="nll_r",format="%.1f",label_visibility="collapsed")
        with nl4: new_lt=st.selectbox("Type",LIAB_TYPES,key="nll_t",label_visibility="collapsed")
        if st.button("Add liability",use_container_width=True):
            if new_ln: st.session_state.liabilities.append({"name":new_ln,"balance":float(new_lb),"rate":float(new_lr),"type":new_lt,"min_payment":0.0}); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

    # ── Investment Recommendations (full width, below the two columns) ──────────
    st.markdown("<div style='height:.5rem'></div>",unsafe_allow_html=True)
    st.markdown(f"<div class='card'><span class='clabel'>Investment Recommendations — {risk_sel} Profile · Age {age_val} · {fmt(investable)}/month available</span>",unsafe_allow_html=True)
    guide=INVEST_GUIDE.get(risk_sel,INVEST_GUIDE["Moderate"])
    # Emergency fund warning
    if em_months<3:
        st.markdown(f"<div class='tip' style='border-color:{RD};background:{h2r(RD,0.06)};'>"
                    f"<b>Important:</b> Your emergency fund is only {em_months:.1f} months. "
                    f"Put <b>100% of investable funds into a high-yield savings account</b> until you have 3+ months covered. "
                    f"Target: <b>{fmt(total_exp*3)}</b> minimum.</div>",unsafe_allow_html=True)
    elif em_months<6:
        st.markdown(f"<div class='tip'><b>Tip:</b> Allocate ~20% to savings until emergency fund reaches 6 months ({fmt(total_exp*6)}).</div>",unsafe_allow_html=True)
    # High debt warning
    hi_debt=[l for l in st.session_state.liabilities if l.get("rate",0)>10]
    if hi_debt:
        st.markdown(f"<div class='tip' style='border-color:{AM};background:{h2r(AM,0.06)};'>"
                    f"<b>High-interest debt detected:</b> {fmt(sum(l['balance'] for l in hi_debt))} at >10% APR. "
                    f"Paying this off = guaranteed {max(l['rate'] for l in hi_debt):.0f}% return. "
                    f"Consider allocating 50%+ of investable to debt payoff first.</div>",unsafe_allow_html=True)
    # Summary
    st.markdown(f"<div style='font-size:.81rem;color:{MU};margin-bottom:.8rem;line-height:1.6;'>{guide['summary']}</div>",unsafe_allow_html=True)
    # Allocation cards
    rcols=st.columns(len(guide["items"]) if len(guide["items"])<=5 else 5)
    COLOR_MAP={"gr":GR,"bl":BL,"am":AM,"rd":RD,"pu":PU}
    for idx,(name,alloc_pct,why,products,clr) in enumerate(guide["items"]):
        col=COLOR_MAP.get(clr,BL); mo_=investable*alloc_pct/100
        with rcols[idx % len(rcols)]:
            st.markdown(
                f"<div style='background:{SU};border:1px solid {BO};border-top:3px solid {col};"
                f"border-radius:10px;padding:.8rem .9rem;margin-bottom:.5rem;height:100%;'>"
                f"<div style='font-size:.62rem;font-weight:700;color:{col};text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;'>{alloc_pct}% allocation</div>"
                f"<div style='font-size:.83rem;font-weight:700;color:{TX};margin-bottom:4px;'>{name}</div>"
                f"<div style='font-size:.7rem;color:{MU};margin-bottom:6px;line-height:1.5;'>{why}</div>"
                f"<div style='font-size:.62rem;font-weight:700;color:{col};margin-bottom:4px;'>{fmt(mo_)}/mo</div>"
                f"<div style='font-size:.66rem;color:{MU};line-height:1.6;'>"
                + "".join(f"· {p}<br>" for p in products[:3]) +
                f"</div></div>",unsafe_allow_html=True)
    # Super tip
    st.markdown(f"<div style='margin-top:.6rem;background:{h2r(GR,0.07)};border:1px solid {h2r(GR,0.2)};"
                f"border-radius:9px;padding:.6rem .9rem;font-size:.79rem;color:{TX};'>"
                f"<span style='color:{GR};font-weight:700;'>Super tip: </span>{guide['super']}</div>",unsafe_allow_html=True)
    # Avoid list
    st.markdown(f"<div style='margin-top:.5rem;font-size:.73rem;color:{RD};'>"
                f"<b>Avoid for this profile:</b> {' · '.join(guide['avoid'])}</div>",unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REPORTS  — dedicated, easy to find
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t5:
    st.markdown(f"<div class='tip'>Download your financial report here or import your bank statement to auto-categorise transactions.</div>",unsafe_allow_html=True)
    rp1,rp2=st.columns(2,gap="large")

    with rp1:
        st.markdown(f"<div class='card'><span class='clabel'>Export Report</span>",unsafe_allow_html=True)
        period=st.selectbox("Report period",["Monthly","Weekly","Quarterly","Annual"],key="rp_period")
        now_str=datetime.now().strftime("%Y-%m-%d")

        # CSV
        st.download_button(
            f"Download {period} Report (CSV)",
            data=gen_csv(period),
            file_name=f"seralung_{period.lower()}_{now_str}.csv",
            mime="text/csv",use_container_width=True
        )
        # PDF
        if PDF_OK:
            pdf_b=gen_pdf(period)
            if pdf_b:
                st.download_button(
                    f"Download {period} Report (PDF)",
                    data=pdf_b,
                    file_name=f"seralung_{period.lower()}_{now_str}.pdf",
                    mime="application/pdf",use_container_width=True
                )
        else:
            st.caption("Install fpdf2 for PDF export: `pip install fpdf2`")

        st.markdown(f"<div style='height:.3rem'></div>",unsafe_allow_html=True)
        st.markdown(f"<span class='clabel'>What's included in the report</span>",unsafe_allow_html=True)
        for item in ["Financial health score","All expenses with categories",
                     "Budget vs actual comparison","Goals & progress",
                     "Assets & liabilities","Net worth","Imported transactions"]:
            st.markdown(f"<div style='font-size:.78rem;color:{TX};padding:.25rem 0;border-bottom:1px solid {BO};'>"
                        f"<span style='color:{GR};margin-right:6px;font-weight:700;'>+</span>{item}</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # JSON backup
        st.markdown(f"<div class='card'><span class='clabel'>JSON Backup / Restore</span>",unsafe_allow_html=True)
        backup={
            "expenses":st.session_state.expenses,"subscriptions":st.session_state.subscriptions,
            "bills":st.session_state.bills,"assets":st.session_state.assets,
            "liabilities":st.session_state.liabilities,"goals":st.session_state.goals,
            "settings":{"primary_income":primary_income,"other_income":other_income,
                        "needs_pct":needs_pct,"wants_pct":wants_pct,"invest_pct":invest_pct},
            "exported_at":datetime.now().isoformat()
        }
        st.download_button("Download backup JSON",data=json.dumps(backup,indent=2,default=str).encode(),
            file_name=f"seralung_backup_{now_str}.json",mime="application/json",use_container_width=True)
        json_up=st.file_uploader("Restore from JSON",type=["json"],key="json_up")
        if json_up:
            try:
                imp=json.loads(json_up.read().decode())
                if st.button("Restore data",use_container_width=True):
                    for key in ["expenses","subscriptions","bills","assets","liabilities","goals"]:
                        if key in imp: st.session_state[key]=imp[key]
                    if "settings" in imp:
                        for k,v in imp["settings"].items(): st.session_state[k]=v
                    st.success("Restored!"); st.rerun()
                st.caption(f"Preview: {len(imp.get('expenses',[]))} expenses · {len(imp.get('goals',[]))} goals")
            except Exception as e: st.error(f"Invalid JSON: {e}")
        st.markdown("</div>",unsafe_allow_html=True)

    with rp2:
        st.markdown(f"<div class='card'><span class='clabel'>Import Bank Statement</span>",unsafe_allow_html=True)
        st.caption("Supports ANZ, CBA, Westpac, NAB, Macquarie, and most AUS bank CSV exports. Transactions are auto-categorised by keyword matching.")
        st.markdown(f"<div style='font-size:.75rem;color:{MU};margin-bottom:.4rem;'>"
                    f"Supported: <b>PDF</b>, <b>CSV</b>, <b>Excel (.xlsx)</b>, <b>OFX/QFX</b> — "
                    f"works with ANZ, CBA, Westpac, NAB, Macquarie, ING and most AUS banks.</div>",unsafe_allow_html=True)
        bank_file=st.file_uploader("Drop bank statement here",
            type=["csv","pdf","xlsx","xls","ofx","qfx"],key="bank_up")
        if bank_file:
            fname=bank_file.name.lower()
            if fname.endswith(".pdf"):
                df_tx,err=parse_pdf_statement(bank_file)
            elif fname.endswith((".xlsx",".xls")):
                df_tx,err=parse_excel_statement(bank_file)
            elif fname.endswith((".ofx",".qfx")):
                df_tx,err=parse_ofx_statement(bank_file)
            else:
                df_tx,err=parse_bank_csv(bank_file)
            if err:
                st.error(f"Could not parse: {err}")
                st.caption("Ensure your CSV has Date, Description, and Amount (or Debit/Credit) columns.")
            else:
                st.success(f"Parsed {len(df_tx)} transactions")
                df_show=df_tx.copy()
                df_show["Date"]=df_show["Date"].dt.strftime("%d %b %Y")
                df_show["Amt"]=df_show["Amount"].apply(lambda x: f"+${x:,.2f}" if x>=0 else f"-${abs(x):,.2f}")
                st.dataframe(df_show[["Date","Description","Amt","Category"]].head(30),use_container_width=True,hide_index=True)
                ic1,ic2=st.columns(2)
                with ic1:
                    if st.button("Save as transactions",use_container_width=True,key="imp_tx"):
                        recs=df_tx.to_dict("records")
                        for r in recs: r["Date"]=str(r["Date"])[:10]
                        st.session_state.transactions=recs; st.success(f"Saved {len(recs)}"); st.rerun()
                with ic2:
                    if st.button("Add debits to expenses",use_container_width=True,key="imp_exp"):
                        debits=df_tx[df_tx["Amount"]<0].copy(); added=0
                        for _,row in debits.iterrows():
                            if abs(row["Amount"])>5:
                                st.session_state.expenses.append({"name":str(row["Description"])[:32],"amount":float(abs(row["Amount"])),"budget":float(abs(row["Amount"])),"category":str(row["Category"]),"freq":"Monthly"}); added+=1
                        st.success(f"Added {added} expenses"); st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

        # Supported banks
        st.markdown(f"<div class='card'><span class='clabel'>Supported Bank CSV Formats</span>",unsafe_allow_html=True)
        for bank,cols in [("ANZ","PDF, CSV, OFX — Debit/Credit columns"),
                          ("CBA","PDF, CSV, OFX — Amount column"),
                          ("Westpac","PDF, CSV, OFX, QIF — Amount column"),
                          ("NAB","PDF, CSV, OFX — Amount column"),
                          ("Macquarie","PDF, CSV — Debit/Credit columns"),
                          ("ING","PDF, CSV — Amount column"),
                          ("Bendigo","PDF, CSV — Debit/Credit columns"),
                          ("Generic CSV","Any CSV with Date + Amount + Description"),
                          ("Generic Excel","Any .xlsx with Date + Amount + Description"),
                          ("OFX/QFX","Standard open banking format")]:
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:.3rem 0;border-bottom:1px solid {BO};font-size:.76rem;'>"
                        f"<span style='font-weight:600;color:{TX};'>{bank}</span>"
                        f"<span style='color:{MU};font-size:.68rem;'>{cols}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Transaction viewer
        if st.session_state.transactions:
            df_t=pd.DataFrame(st.session_state.transactions)
            ti=df_t[df_t["Amount"]>0]["Amount"].sum() if "Amount" in df_t.columns else 0
            to_=df_t[df_t["Amount"]<0]["Amount"].abs().sum() if "Amount" in df_t.columns else 0
            tt1,tt2,tt3=st.columns(3)
            tt1.metric("Transactions",len(df_t)); tt2.metric("Total in",fmt(ti)); tt3.metric("Total out",fmt(to_))
            if "Category" in df_t.columns and "Amount" in df_t.columns:
                cs=df_t[df_t["Amount"]<0].groupby("Category")["Amount"].sum().abs().reset_index()
                if not cs.empty:
                    n=len(cs); cc=(T["chart"]*math.ceil(n/max(1,len(T["chart"]))))[:n]
                    fig=go.Figure(go.Bar(x=cs["Category"],y=cs["Amount"],marker_color=cc,
                        text=[fmt(v) for v in cs["Amount"]],textposition="outside",textfont=dict(color=TX,size=9)))
                    fig.update_yaxes(tickprefix="$",tickformat=",.0f")
                    fig.update_layout(**plo("Spending by Category (imported)",200))
                    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            if st.button("Clear transactions",use_container_width=True,key="clr_tx"):
                st.session_state.transactions=[]; st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INSIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t6:
    ins1,ins2=st.columns(2,gap="large")
    with ins1:
        st.markdown(f"<div class='card'><span class='clabel'>Financial Intelligence Report</span>",unsafe_allow_html=True)
        def insight(headline,detail,badge):
            st.markdown(f"<div style='padding:.5rem 0;border-bottom:1px solid {BO};'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;'>"
                        f"<span style='font-weight:600;font-size:.82rem;color:{TX};'>{headline}</span>"
                        f"<span class='bd {badge[0]}'>{badge[1]}</span></div>"
                        f"<div style='font-size:.73rem;color:{MU};line-height:1.5;'>{detail}</div>"
                        f"</div>",unsafe_allow_html=True)
        if savings_rate>=20: insight("Savings target met",f"Saving {savings_rate:.1f}% — above the 20% benchmark.",("ok","Healthy"))
        else: insight("Savings below target",f"Rate {savings_rate:.1f}%. Need {fmt(total_income*0.2-cash_flow)}/mo more.",("bad","Act"))
        if em_months>=6: insight("Emergency fund secure",f"{em_months:.1f} months covered — above target.",("ok","Secure"))
        elif em_months>=3: insight("Emergency fund building",f"{em_months:.1f} months. Target: {fmt(total_exp*6)}.",("warn","Build"))
        else: insight("Emergency fund critical",f"Only {em_months:.1f} months. Priority #1.",("bad","Urgent"))
        ob=[e for e in st.session_state.expenses if to_mo(e["amount"],e.get("freq","Monthly"))>e.get("budget",e["amount"])]
        if ob: insight("Budget breaches",f"{len(ob)} over budget: {', '.join(e['name'] for e in ob[:4])}.",("warn","Review"))
        else: insight("Budget on track","All categories within budget.",("ok","On Track"))
        if total_sub>150: insight("Subscription audit",f"{fmt(total_sub)}/mo = {fmt(total_sub*12)}/yr. Review cancellations.",("warn","Audit"))
        hi=[l for l in st.session_state.liabilities if l.get("rate",0)>15]
        if hi: insight("High-interest debt",f"{fmt(sum(l['balance'] for l in hi))} at >15% APR. Priority payoff.",("bad","Urgent"))
        yrl=max(1,st.session_state.get("retirement_age",65)-st.session_state.get("age",32))
        proj=sum(a["value"] for a in st.session_state.assets if a["type"] in ["Investments","Savings","Super"])
        for _ in range(yrl): proj=(proj+investable*12)*1.07
        insight("Retirement estimate",f"At 7% growth: {fmt(proj)} by age {st.session_state.get('retirement_age',65)}. Draw: {fmt(proj*0.04/12)}/mo.",("blu","Estimate"))
        st.markdown("</div>",unsafe_allow_html=True)
        # Cashflow waterfall
        fig=go.Figure(go.Waterfall(
            x=["Income","Needs","Wants","Save & Invest","Remaining"],
            measure=["absolute","relative","relative","relative","total"],
            y=[total_income,-needs_actual,-wants_actual,-investable,0],
            connector=dict(line=dict(color=BO,width=.5)),
            increasing=dict(marker=dict(color=GR)),decreasing=dict(marker=dict(color=RD)),
            totals=dict(marker=dict(color=GR if cash_flow>=0 else RD)),
            texttemplate="%{y:$,.0f}",textposition="outside",textfont=dict(color=TX,size=9)))
        fig.update_layout(**plo("Monthly Cash Flow",210))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with ins2:
        st.markdown(f"<div class='card'><span class='clabel'>Key Numbers & Predictions</span>",unsafe_allow_html=True)
        preds=[
            ("Savings in 12 months",fmt(cash_flow*12+cash_assets),"at current rate",GR),
            ("Net worth in 5 years",fmt(net_worth+(cash_flow+investable)*12*5),"7% growth estimate",BL),
            ("Subscriptions per year",fmt(total_sub*12),"review regularly",AM),
            ("Annual interest on debt",fmt(sum(l["balance"]*l.get("rate",0)/100 for l in st.session_state.liabilities)),"cost of debt",RD),
            ("FIRE number needed",fmt(total_exp*12*25),"4% withdrawal rule",PU),
            ("Monthly tax estimate",fmt(calc_tax(primary_income*12)/12),"income tax only",MU),
        ]
        for lbl,val,note,col in preds:
            st.markdown(f"<div style='padding:.42rem 0;border-bottom:1px solid {BO};'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.79rem;color:{TX};'>"
                        f"<span style='color:{MU};'>{lbl}</span><span style='color:{col};font-weight:600;'>{val}</span></div>"
                        f"<div style='font-size:.65rem;color:{MU};'>{note}</div></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
        # 10-year net worth
        nw_y=[]; nw_v=[]; v=net_worth
        for yr in range(11):
            nw_y.append(yr); nw_v.append(round(v)); v=v+(cash_flow+investable)*12*0.07
        fig=go.Figure(go.Scatter(x=nw_y,y=nw_v,mode="lines+markers",
            line=dict(color=A,width=2.5),fill="tozeroy",fillcolor=h2r(A,.08),
            marker=dict(size=5,color=A),hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>"))
        fig.update_yaxes(tickprefix="$",tickformat=",.0f"); fig.update_xaxes(title_text="Years from now")
        fig.update_layout(**plo("10-Year Net Worth Projection",230))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI CHAT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with t7:
    ai1,ai2=st.columns([2.5,1.5],gap="large")
    with ai1:
        st.markdown(f"<div class='card'><span class='clabel'>AI Financial Advisor — Powered by Claude</span>",unsafe_allow_html=True)
        api_key=st.text_input("Anthropic API key",type="password",placeholder="sk-ant-...",key="api_key",help="Get at console.anthropic.com")
        if api_key:
            prompts=["Can I afford a $40k car?","How do I reach 20% savings rate?",
                     "Pay off debt or invest?","How to grow my emergency fund faster?",
                     "When can I retire?","How to reduce my expenses?"]
            pc=st.columns(2)
            for i,p in enumerate(prompts):
                with pc[i%2]:
                    if st.button(p,key=f"sp_{i}",use_container_width=True):
                        st.session_state.chat_history.append({"role":"user","content":p})
                        sys_p=(f"Premium AUS financial advisor. User: income {fmt(total_income)}/mo, "
                               f"expenses {fmt(total_exp)}/mo, savings {savings_rate:.1f}%, "
                               f"net worth {fmt(net_worth)}, emergency {em_months:.1f} mo, "
                               f"investable {fmt(investable)}/mo, health {hs}/100, debt {fmt(total_liab)}. "
                               f"Concise specific AUD advice, under 180 words.")
                        try:
                            r=requests.post("https://api.anthropic.com/v1/messages",
                                headers={"x-api-key":api_key,"anthropic-version":"2023-06-01","content-type":"application/json"},
                                json={"model":"claude-sonnet-4-20250514","max_tokens":500,"system":sys_p,"messages":st.session_state.chat_history},timeout=30)
                            reply=r.json()["content"][0]["text"] if r.status_code==200 else f"Error {r.status_code}"
                        except Exception as e: reply=f"Error: {str(e)[:80]}"
                        st.session_state.chat_history.append({"role":"assistant","content":reply}); st.rerun()
            if st.session_state.chat_history:
                st.markdown("<div class='chat-wrap'>",unsafe_allow_html=True)
                for msg in st.session_state.chat_history[-14:]:
                    c=msg["content"].replace("\n","<br>")
                    if msg["role"]=="user": st.markdown(f"<div class='chat-user'>{c}</div>",unsafe_allow_html=True)
                    else: st.markdown(f"<div class='chat-ai'>{c}</div>",unsafe_allow_html=True)
                st.markdown("</div><div style='clear:both;margin:.5rem 0;'></div>",unsafe_allow_html=True)
            user_in=st.chat_input("Ask anything about your finances...")
            if user_in:
                st.session_state.chat_history.append({"role":"user","content":user_in})
                sys_p=f"AUS financial advisor. {fmt(total_income)}/mo income, {savings_rate:.1f}% savings, {fmt(net_worth)} net worth. Concise AUD advice."
                try:
                    r=requests.post("https://api.anthropic.com/v1/messages",
                        headers={"x-api-key":api_key,"anthropic-version":"2023-06-01","content-type":"application/json"},
                        json={"model":"claude-sonnet-4-20250514","max_tokens":500,"system":sys_p,"messages":st.session_state.chat_history},timeout=30)
                    reply=r.json()["content"][0]["text"] if r.status_code==200 else "Error"
                except Exception as e: reply=f"Error: {str(e)[:80]}"
                st.session_state.chat_history.append({"role":"assistant","content":reply}); st.rerun()
            if st.button("Clear chat",key="clr_chat"): st.session_state.chat_history=[]; st.rerun()
        else:
            st.markdown(f"<div style='text-align:center;padding:2.5rem 1rem;'>"
                        f"<div style='font-size:1.2rem;font-weight:700;color:{TX};margin-bottom:.5rem;'>AI Financial Advisor</div>"
                        f"<div style='font-size:.82rem;color:{MU};line-height:1.7;max-width:380px;margin:0 auto;'>"
                        f"Enter your Anthropic API key above to chat with a personalised AI advisor. "
                        f"Your financial profile is sent automatically for context-aware advice.</div>"
                        f"<div style='margin-top:1rem;font-size:.72rem;color:{MU};'>Get your key: <b>console.anthropic.com</b></div></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with ai2:
        st.markdown(f"<div class='card'><span class='clabel'>Your Profile (AI context)</span>",unsafe_allow_html=True)
        for lbl,val in [("Income",fmt(total_income)),("Expenses",fmt(total_exp)),("Cash flow",fmt(cash_flow)),
                        ("Savings rate",pct(savings_rate)),("Emergency",f"{em_months:.1f} mo"),
                        ("Net worth",fmt(net_worth)),("Total debt",fmt(total_liab)),
                        ("Investable",fmt(investable)),("Health score",f"{hs}/100"),
                        ("Risk profile",st.session_state.get("risk_profile","Moderate")),
                        ("Age/Retire",f"{st.session_state.get('age',32)} / {st.session_state.get('retirement_age',65)}")]:
            st.markdown(f"<div class='crow'><span style='color:{MU};font-size:.74rem;'>{lbl}</span>"
                        f"<span style='font-weight:600;color:{TX};font-size:.74rem;'>{val}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='tip'>Your full financial context is sent to the AI automatically. No need to repeat your situation.</div>",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"<p style='text-align:center;color:{MU};font-size:.62rem;'>Seralung Finance · Educational use only · Not financial advice · AUS Tax FY2024-25</p>",unsafe_allow_html=True)
