"""
db.py — Supabase auth + data persistence for Seralung Finance
Place this file in the SAME FOLDER as seralung_premium.py

Streamlit Cloud secrets (App Settings → Secrets):
    SUPABASE_URL = "https://abcdefgh.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

Common mistakes that cause "Invalid path" error:
  ✗  https://abcdefgh.supabase.co/    ← trailing slash
  ✗  abcdefgh.supabase.co             ← missing https://
  ✓  https://abcdefgh.supabase.co     ← correct
"""

import streamlit as st
from supabase import create_client, Client

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DATA_KEYS = [
    "expenses", "subscriptions", "bills",
    "assets", "liabilities", "goals", "transactions",
]
SETTING_DEFAULTS = {
    "needs_pct": 50, "wants_pct": 30, "invest_pct": 20,
    "risk_profile": "Moderate", "age": 32, "retirement_age": 65,
    "em_pct": 30, "idx_pct": 40, "stk_pct": 20, "cry_pct": 10,
    "streak_days": 0, "total_saved_this_year": 0.0,
}

# ─────────────────────────────────────────────────────────────────────────────
# CLIENT  (cached in session_state)
# ─────────────────────────────────────────────────────────────────────────────
def _clean_url(raw: str) -> str:
    """Strip whitespace, trailing slashes and ensure https://"""
    url = raw.strip().rstrip("/")
    if not url.startswith("http"):
        url = "https://" + url
    return url

def init_supabase() -> Client:
    if "sb_client" in st.session_state:
        return st.session_state["sb_client"]

    # ── Read secrets ──────────────────────────────────────────────────────────
    missing = []
    if "SUPABASE_URL" not in st.secrets: missing.append("SUPABASE_URL")
    if "SUPABASE_KEY" not in st.secrets: missing.append("SUPABASE_KEY")
    if missing:
        st.error(f"Missing secret(s): {', '.join(missing)}\n\n"
                 "Go to Streamlit Cloud → App Settings → Secrets and add:\n\n"
                 "SUPABASE_URL = \"https://your-project.supabase.co\"\n"
                 "SUPABASE_KEY = \"eyJ...\"")
        st.stop()

    url = _clean_url(st.secrets["SUPABASE_URL"])
    key = st.secrets["SUPABASE_KEY"].strip()

    # ── Basic validation ──────────────────────────────────────────────────────
    if "supabase.co" not in url:
        st.error(f"SUPABASE_URL looks wrong: `{url}`\n\n"
                 "It should look like: `https://abcdefgh.supabase.co`\n"
                 "Check Streamlit Cloud → App Settings → Secrets.")
        st.stop()
    if not key.startswith("eyJ"):
        st.error("SUPABASE_KEY looks wrong — it should start with `eyJ`.\n\n"
                 "Make sure you copied the **anon / public** key from:\n"
                 "Supabase → Project Settings → API → Project API keys")
        st.stop()

    try:
        client = create_client(url, key)
        st.session_state["sb_client"] = client
        return client
    except Exception as e:
        st.error(f"Could not connect to Supabase.\n\nURL used: `{url}`\n\nError: {e}")
        st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_user():
    return st.session_state.get("sb_user", None)

def _store_session(session):
    st.session_state["sb_user"]          = session.user
    st.session_state["sb_access_token"]  = session.access_token
    st.session_state["sb_refresh_token"] = session.refresh_token

def _clear_session():
    for k in ["sb_user", "sb_access_token", "sb_refresh_token",
              "sb_client", "data_loaded", "chat_history"]:
        st.session_state.pop(k, None)

def restore_session(sb: Client) -> bool:
    """Re-hydrate session from stored tokens — survives page refresh."""
    tok = st.session_state.get("sb_access_token")
    ref = st.session_state.get("sb_refresh_token")
    if not tok or not ref:
        return False
    try:
        res = sb.auth.set_session(tok, ref)
        if res and res.user:
            _store_session(res.session)
            return True
    except Exception:
        _clear_session()
    return False

def logout(sb: Client):
    try:
        sb.auth.sign_out()
    except Exception:
        pass
    _clear_session()
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DATA SYNC
# ─────────────────────────────────────────────────────────────────────────────
def load_user_data(sb: Client) -> bool:
    user = get_user()
    if not user:
        return False
    try:
        res = sb.table("user_data").select("*").eq("user_id", user.id).execute()
        if res.data:
            row = res.data[0]
            for k in DATA_KEYS:
                if row.get(k) is not None:
                    st.session_state[k] = row[k]
            settings = row.get("settings") or {}
            for k, default in SETTING_DEFAULTS.items():
                st.session_state[k] = settings.get(k, default)
            return True
        return False          # first login — keep demo defaults
    except Exception as e:
        st.warning(f"Could not load saved data: {e}")
        return False

def save_user_data(sb: Client) -> bool:
    user = get_user()
    if not user:
        return False
    try:
        payload = {
            "user_id": user.id,
            **{k: st.session_state.get(k, []) for k in DATA_KEYS},
            "settings": {k: st.session_state.get(k, d) for k, d in SETTING_DEFAULTS.items()},
        }
        sb.table("user_data").upsert(payload, on_conflict="user_id").execute()
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN / SIGNUP PAGE
# ─────────────────────────────────────────────────────────────────────────────
def _friendly_error(raw: str) -> str:
    """Turn raw Supabase error strings into readable messages."""
    r = raw.lower()
    if "invalid path" in r or "invalid url" in r:
        return ("Configuration error: the Supabase URL is wrong.\n"
                "Fix it in Streamlit Cloud → App Settings → Secrets.\n"
                "It must look like: https://abcdefgh.supabase.co  (no trailing slash)")
    if "email not confirmed" in r:
        return "Please confirm your email first — check your inbox for a link from Supabase."
    if "invalid login" in r or "invalid_credentials" in r or "invalid email or password" in r:
        return "Wrong email or password. Please try again."
    if "already registered" in r or "user already registered" in r:
        return "That email is already registered. Switch to Sign in."
    if "password should be" in r or "password must be" in r:
        return "Password must be at least 6 characters."
    if "rate limit" in r or "too many requests" in r:
        return "Too many attempts. Please wait a minute then try again."
    if "network" in r or "connection" in r or "timeout" in r:
        return "Network error — check your internet connection and try again."
    # Return the raw message but trimmed
    return raw[:200]

def login_page(sb: Client, T: dict):
    accent  = T.get("accent",  "#10B981")
    surface = T.get("surface", "#111827")
    surface2= T.get("surface2","#1C2639")
    border  = T.get("border",  "#1F2D45")
    text    = T.get("text",    "#F0F6FF")
    muted   = T.get("muted",   "#6B7A99")
    grad    = T.get("grad",    "linear-gradient(135deg,#10B981,#3B82F6)")
    bg      = T.get("bg",      "#090E1A")

    st.markdown(f"""
<style>
html,body,.stApp{{background:{bg} !important;}}
.lw{{
  max-width:420px;margin:3rem auto 0;
  background:{surface};border:1px solid {border};
  border-radius:20px;padding:2.2rem 1.8rem 1.8rem;
  box-shadow:0 8px 48px rgba(0,0,0,0.5);
}}
.lt{{background:{grad};-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;font-size:1.65rem;font-weight:800;text-align:center;
  letter-spacing:-0.03em;margin-bottom:.25rem;font-family:sans-serif;}}
.ls{{color:{muted};font-size:0.78rem;text-align:center;margin-bottom:1.4rem;}}
.le{{background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.35);
  border-radius:8px;padding:.65rem .9rem;color:#F87171;font-size:0.78rem;
  margin:.5rem 0;line-height:1.5;white-space:pre-wrap;}}
.lo{{background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.35);
  border-radius:8px;padding:.65rem .9rem;color:{accent};font-size:0.78rem;margin:.5rem 0;}}
[data-testid="stTextInput"] input{{
  background:{surface2} !important;border:1px solid {border} !important;
  border-radius:10px !important;color:{text} !important;font-size:0.88rem !important;}}
label,[data-testid="stWidgetLabel"] *{{color:{text} !important;font-size:0.8rem !important;}}
.stButton>button{{
  background:{grad} !important;border:none !important;border-radius:10px !important;
  color:#fff !important;font-weight:700 !important;font-size:0.88rem !important;
  padding:.55rem 1rem !important;width:100%;transition:opacity .15s;}}
.stButton>button:hover{{opacity:.86 !important;}}
.stRadio [role="radiogroup"]{{justify-content:center;gap:1.5rem;}}
.stRadio label span{{color:{text} !important;font-size:.85rem !important;}}
.stSpinner>div{{border-top-color:{accent} !important;}}
</style>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<div class='lw'>", unsafe_allow_html=True)
        st.markdown("<div class='lt'>Seralung Finance</div>", unsafe_allow_html=True)
        st.markdown("<div class='ls'>Your premium financial companion</div>", unsafe_allow_html=True)

        mode = st.radio("", ["Sign in", "Create account"],
                        horizontal=True, label_visibility="collapsed")

        email    = st.text_input("Email",    placeholder="you@example.com",   key="login_email")
        password = st.text_input("Password", placeholder="At least 6 characters",
                                 type="password", key="login_pass")

        confirm = None
        if mode == "Create account":
            confirm = st.text_input("Confirm password", placeholder="Repeat password",
                                    type="password", key="login_confirm")

        btn_label = "Create account" if mode == "Create account" else "Sign in"
        clicked   = st.button(btn_label, use_container_width=True, key="login_btn")

        if clicked:
            # ── Client-side validation ────────────────────────────────────────
            error_msg = None
            if not email or "@" not in email:
                error_msg = "Please enter a valid email address."
            elif not password:
                error_msg = "Please enter your password."
            elif mode == "Create account" and len(password) < 6:
                error_msg = "Password must be at least 6 characters."
            elif mode == "Create account" and confirm is not None and password != confirm:
                error_msg = "Passwords do not match."

            if error_msg:
                st.markdown(f"<div class='le'>{error_msg}</div>", unsafe_allow_html=True)
            else:
                with st.spinner("Please wait..."):
                    try:
                        if mode == "Create account":
                            res = sb.auth.sign_up({
                                "email":    email.strip(),
                                "password": password,
                            })
                            if res.user and res.session:
                                # Email confirmation OFF — logged in immediately
                                _store_session(res.session)
                                st.session_state["just_registered"] = True
                                st.rerun()
                            elif res.user:
                                # Email confirmation ON — need to confirm first
                                st.markdown(
                                    "<div class='lo'>Account created! Check your inbox "
                                    "for a confirmation email, then come back and sign in.</div>",
                                    unsafe_allow_html=True)
                            else:
                                st.markdown(
                                    "<div class='le'>Sign-up failed. "
                                    "Try a different email address.</div>",
                                    unsafe_allow_html=True)

                        else:  # Sign in
                            res = sb.auth.sign_in_with_password({
                                "email":    email.strip(),
                                "password": password,
                            })
                            if res.session:
                                _store_session(res.session)
                                st.rerun()
                            else:
                                st.markdown(
                                    "<div class='le'>Sign-in failed. "
                                    "Check your email and password.</div>",
                                    unsafe_allow_html=True)

                    except Exception as e:
                        friendly = _friendly_error(str(e))
                        st.markdown(f"<div class='le'>{friendly}</div>",
                                    unsafe_allow_html=True)

        st.markdown(
            f"<div style='text-align:center;margin-top:1.2rem;"
            f"font-size:0.66rem;color:{muted};line-height:1.6;'>"
            "Your data is encrypted and stored securely.<br>"
            "We never share or sell your financial data.</div>",
            unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
