"""
markets.py
==========
Live Australian market data for Seralung Finance (Step 4 — Markets).

Data source: Yahoo Finance via the free ``yfinance`` library (no API key).
ASX quotes on Yahoo are typically delayed up to ~20 minutes — near real-time,
not tick-by-tick. All fetches are cached and wrapped so a network failure
degrades to a friendly message instead of crashing the app.

The "Top 5" lists are curated by market capitalisation / trading popularity.
They are EXAMPLES TO EXPLORE, not buy recommendations.
"""
import base64
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st

try:
    import yfinance as yf
    YF_OK = True
except Exception:                                    # pragma: no cover
    YF_OK = False

# ── Curated lists (by market cap / popularity — examples, not advice) ──
CURATED = {
    "Australian Stocks": [
        ("CBA.AX", "Commonwealth Bank"),
        ("BHP.AX", "BHP Group"),
        ("CSL.AX", "CSL Limited"),
        ("NAB.AX", "National Australia Bank"),
        ("WBC.AX", "Westpac Banking"),
    ],
    "ETFs": [
        ("VAS.AX", "Vanguard Australian Shares"),
        ("VGS.AX", "Vanguard MSCI Intl Shares"),
        ("IVV.AX", "iShares S&P 500"),
        ("A200.AX", "Betashares Australia 200"),
        ("NDQ.AX", "Betashares Nasdaq 100"),
    ],
    "Real Estate (A-REITs)": [
        ("GMG.AX", "Goodman Group"),
        ("SCG.AX", "Scentre Group"),
        ("DXS.AX", "Dexus"),
        ("SGP.AX", "Stockland"),
        ("MGR.AX", "Mirvac Group"),
    ],
}
SEG_NOTE = {
    "Australian Stocks": "the five largest ASX-listed companies by market capitalisation",
    "ETFs": "five of the most widely held ASX-listed index ETFs",
    "Real Estate (A-REITs)": "the five largest ASX-listed property trusts — the practical way to track Australian real estate on an exchange",
}


# ════════════════════════════ DATA ════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def load_history(symbol: str, period: str = "1y") -> Optional[pd.Series]:
    """Daily adjusted close history for *symbol*; None on any failure."""
    if not YF_OK:
        return None
    try:
        df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
        if df is None or df.empty or "Close" not in df:
            return None
        s = df["Close"].dropna()
        return s if len(s) >= 2 else None
    except Exception:
        return None


def stats_from_history(s: pd.Series) -> dict:
    """Derive quote-style stats purely from a daily close series."""
    v = np.asarray(s.values, dtype=float)
    last, prev = float(v[-1]), float(v[-2])
    day = last / prev - 1.0 if prev > 0 else 0.0
    yr = last / float(v[0]) - 1.0 if v[0] > 0 else 0.0
    lr = np.diff(np.log(np.clip(v, 1e-9, None)))
    vol = float(lr.std() * np.sqrt(252)) if lr.size > 1 else 0.0
    mu = float(lr.mean() * 252) if lr.size > 1 else 0.0
    # Illustrative 1-yr range: ±1σ (lognormal) around a CLAMPED drift. Drift is the
    # least reliable statistic, so it is bounded to ±σ/2 — uncertainty then strictly
    # dominates and the range always brackets the current price on BOTH sides
    # (an uncertainty illustration, never a momentum extrapolation).
    mu_c = float(np.clip(mu, -vol / 2.0, vol / 2.0))
    return {
        "last": last, "day": day, "yr": yr,
        "hi52": float(v.max()), "lo52": float(v.min()),
        "vol": vol, "mu": mu,
        "rng_lo": last * float(np.exp(mu_c - vol)),
        "rng_hi": last * float(np.exp(mu_c + vol)),
    }


# ════════════════════════════ SVG ════════════════════════════
def _img(svg: str, mw: int) -> str:
    b64 = base64.b64encode(svg.encode()).decode()
    return (f'<img src="data:image/svg+xml;base64,{b64}" '
            f'style="display:block;width:100%;max-width:{mw}px"/>')


def sparkline(vals, w: int = 130, h: int = 36) -> str:
    v = np.asarray([x for x in vals if np.isfinite(x)], dtype=float)
    if v.size < 2:
        return ""
    rng = (v.max() - v.min()) or 1.0
    xs = np.linspace(2, w - 2, v.size)
    ys = h - 4 - (v - v.min()) / rng * (h - 8)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    clr = "#16794D" if v[-1] >= v[0] else "#C53929"
    svg = (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
           f'<polyline points="{pts}" fill="none" stroke="{clr}" stroke-width="2" '
           f'stroke-linejoin="round" stroke-linecap="round"/></svg>')
    return _img(svg, w)


def big_chart(s: pd.Series, w: int = 640, h: int = 220) -> str:
    v = np.asarray(s.values, dtype=float)
    rng = (v.max() - v.min()) or 1.0
    xs = np.linspace(46, w - 10, v.size)
    ys = h - 26 - (v - v.min()) / rng * (h - 50)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    clr = "#16794D" if v[-1] >= v[0] else "#C53929"
    area = f"46,{h-26} {pts} {w-10:.1f},{h-26}"
    grid, labels = "", ""
    for frac in (0.0, 0.5, 1.0):
        val = v.min() + frac * rng
        y = h - 26 - frac * (h - 50)
        grid += f'<line x1="46" y1="{y:.0f}" x2="{w-10}" y2="{y:.0f}" stroke="#EEF1F5"/>'
        labels += (f'<text x="42" y="{y+3:.0f}" text-anchor="end" font-size="10" '
                   f'fill="#94A3B8" font-family="JetBrains Mono">{val:,.0f}</text>')
    d0 = s.index[0]; d1 = s.index[-1]
    try:
        t0, t1 = d0.strftime("%b %y"), d1.strftime("%b %y")
    except Exception:
        t0, t1 = "", ""
    svg = (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">{grid}'
           f'<polygon points="{area}" fill="{clr}" opacity="0.08"/>'
           f'<polyline points="{pts}" fill="none" stroke="{clr}" stroke-width="2.2" '
           f'stroke-linejoin="round" stroke-linecap="round"/>'
           f'{labels}'
           f'<text x="46" y="{h-8}" font-size="10" fill="#94A3B8" font-family="Plus Jakarta Sans">{t0}</text>'
           f'<text x="{w-10}" y="{h-8}" text-anchor="end" font-size="10" fill="#94A3B8" '
           f'font-family="Plus Jakarta Sans">{t1}</text></svg>')
    return _img(svg, w)


# ════════════════════════════ UI ════════════════════════════
def _sec(label):
    st.markdown(f'<div class="sec"><span>{label}</span><div class="ln"></div></div>',
                unsafe_allow_html=True)


def _note(t, k="info"):
    st.markdown(f'<div class="note {k}">{t}</div>', unsafe_allow_html=True)


def _mcard(l, v, s, clr="#16794D", bg="#fff"):
    return (f'<div class="metric" style="border-top-color:{clr};background:{bg}">'
            f'<div class="ml">{l}</div><div class="mv" style="color:{clr}">{v}</div>'
            f'<div class="ms">{s}</div></div>')


def _pricefmt(x: float) -> str:
    return f"A${x:,.2f}"


def _row(sym: str, name: str, s: Optional[pd.Series]) -> str:
    if s is None:
        return (f'<div class="mktrow"><div class="mi"><b>{name}</b>'
                f'<span class="msym">{sym}</span></div>'
                f'<div style="color:#94A3B8;font-size:.8rem">data unavailable</div></div>')
    q = stats_from_history(s)
    dc = "#16794D" if q["day"] >= 0 else "#C53929"
    yc = "#16794D" if q["yr"] >= 0 else "#C53929"
    return (f'<div class="mktrow"><div class="mi"><b>{name}</b>'
            f'<span class="msym">{sym}</span></div>'
            f'<div class="mq"><span class="mp">{_pricefmt(q["last"])}</span>'
            f'<span style="color:{dc}">{q["day"]*100:+.2f}% day</span>'
            f'<span style="color:{yc}">{q["yr"]*100:+.1f}% 1y</span></div>'
            f'<div class="mspark">{sparkline(s.values[-90:])}</div></div>')


def page_markets():
    ss = st.session_state
    st.markdown("""<style>
.mktrow{background:#fff;border:1px solid #E3E8EF;border-radius:12px;padding:11px 16px;margin-bottom:7px;
  display:flex;align-items:center;gap:14px;box-shadow:0 1px 3px rgba(0,0,0,.03)}
.mktrow .mi{flex:1.4;display:flex;flex-direction:column}.mktrow .mi b{font-size:.92rem}
.mktrow .msym{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#94A3B8}
.mktrow .mq{flex:1.6;display:flex;gap:16px;align-items:baseline;font-family:'JetBrains Mono',monospace;font-size:.8rem;flex-wrap:wrap}
.mktrow .mp{font-size:1.05rem;font-weight:700}
.mktrow .mspark{flex:0 0 130px}
@media(max-width:700px){.mktrow{flex-wrap:wrap}.mktrow .mspark{flex:1 1 100%}}
</style>""", unsafe_allow_html=True)

    _note("Live Australian market data from Yahoo Finance (free — ASX quotes are typically "
          "delayed up to ~20 minutes). Educational reference only, <b>not</b> a recommendation "
          "to buy or sell anything.")
    if not YF_OK:
        _note("The <b>yfinance</b> package is not installed — run "
              "<code>pip install yfinance</code> and restart.", "alert")
        return

    _sec("Choose a market")
    seg = st.radio("Market segment", list(CURATED), horizontal=True,
                   key="mkt_seg", label_visibility="collapsed")

    _sec(f"Top 5 — {seg}")
    st.markdown(f'<div class="diag">Curated by size &amp; popularity ({SEG_NOTE[seg]}) — '
                f'examples to explore, <b>not</b> buy recommendations.</div>',
                unsafe_allow_html=True)
    data = {}
    with st.spinner("Fetching live prices…"):
        for sym, name in CURATED[seg]:
            data[sym] = load_history(sym)
    rows = "".join(_row(sym, name, data[sym]) for sym, name in CURATED[seg])
    st.markdown(rows, unsafe_allow_html=True)
    if all(v is None for v in data.values()):
        _note("Couldn't reach Yahoo Finance just now (it sometimes rate-limits shared servers). "
              "Wait a minute and press <b>Refresh data</b> below — or run the app locally.", "warn")

    _sec("Explore a ticker")
    c1, c2, c3 = st.columns([2, 2, 1])
    pick = c1.selectbox("From the list", [f"{n} ({s})" for s, n in CURATED[seg]],
                        key=f"mkt_pick_{seg}")
    custom = c2.text_input("…or any Yahoo symbol", key="mkt_custom",
                           placeholder="e.g. WES.AX, VAP.AX, AAPL")
    if c3.button("⟳ Refresh data", key="mkt_refresh", type="secondary"):
        if hasattr(load_history, "clear"):
            load_history.clear()
        st.rerun()
    sym = custom.strip().upper() if custom.strip() else pick.split("(")[-1].rstrip(")")
    s = load_history(sym)
    if s is None:
        _note(f"No data for <b>{sym}</b> — check the symbol (ASX tickers end in "
              f"<b>.AX</b>) or try again shortly.", "warn")
        return

    q = stats_from_history(s)
    dc = "#16794D" if q["day"] >= 0 else "#C53929"
    st.markdown(f'<div class="card" style="padding:16px 18px">'
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
                f'<div><b style="font-size:1.05rem">{sym}</b> '
                f'<span style="font-family:JetBrains Mono;font-size:1.3rem;font-weight:800;margin-left:10px">{_pricefmt(q["last"])}</span> '
                f'<span style="font-family:JetBrains Mono;color:{dc};margin-left:6px">{q["day"]*100:+.2f}% today</span></div>'
                f'<span style="font-size:.72rem;color:#94A3B8">1-year daily closes · Yahoo Finance</span></div>'
                f'{big_chart(s)}</div>', unsafe_allow_html=True)
    g = st.columns(4)
    yc = "#16794D" if q["yr"] >= 0 else "#C53929"
    g[0].markdown(_mcard("1-Year Return", f"{q['yr']*100:+.1f}%", "Price change over the period",
                         yc, "#E7F5EC" if q["yr"] >= 0 else "#FBEAE7"), unsafe_allow_html=True)
    g[1].markdown(_mcard("52-Week Range", f"{q['lo52']:,.2f}–{q['hi52']:,.2f}", "Low – high (A$)",
                         "#0E7C7B", "#DFF2F1"), unsafe_allow_html=True)
    g[2].markdown(_mcard("Volatility", f"{q['vol']*100:.1f}%", "Annualised, from daily moves",
                         "#B7791F", "#FBF3E2"), unsafe_allow_html=True)
    g[3].markdown(_mcard("Illustrative 1-Yr Range", f"{q['rng_lo']:,.0f}–{q['rng_hi']:,.0f}",
                         "±1σ, drift clamped — NOT a forecast", "#7C3AED", "#ECE6FB"),
                  unsafe_allow_html=True)
    _note("The illustrative range projects this asset's past volatility one year forward (±1σ), with the "
          "historical drift clamped so momentum never dominates. Markets do not follow the "
          "past — treat it as a width-of-uncertainty illustration, never a prediction. "
          "Past performance does not guarantee future results.", "warn")
