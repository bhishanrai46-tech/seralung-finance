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

        pdf.cell(20,7,_p("Good" if d["ok"] else "Low"),fill=True, 

