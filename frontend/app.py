import streamlit as st
import requests
import uuid
from datetime import datetime
import time

# ─── Config ────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:3000/api"

st.set_page_config(
    page_title="NexPay Banking",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State Init ─────────────────────────────────────────────────────
for key in ["token", "user", "page"]:
    if key not in st.session_state:
        st.session_state[key] = None
if st.session_state.page is None:
    st.session_state.page = "login"

# ─── Multi-Currency Config ───────────────────────────────────────────────────
CURRENCIES = {
    "INR": {"symbol": "₹",    "name": "Indian Rupee",     "flag": "🇮🇳", "rate_to_inr": 1.0},
    "TWD": {"symbol": "NT$",  "name": "Taiwan Dollar",    "flag": "🇹🇼", "rate_to_inr": 2.70},
    "USD": {"symbol": "$",    "name": "US Dollar",        "flag": "🇺🇸", "rate_to_inr": 83.50},
    "EUR": {"symbol": "€",    "name": "Euro",             "flag": "🇪🇺", "rate_to_inr": 90.20},
    "GBP": {"symbol": "£",    "name": "British Pound",    "flag": "🇬🇧", "rate_to_inr": 105.80},
    "JPY": {"symbol": "¥",    "name": "Japanese Yen",     "flag": "🇯🇵", "rate_to_inr": 0.56},
    "SGD": {"symbol": "S$",   "name": "Singapore Dollar", "flag": "🇸🇬", "rate_to_inr": 62.30},
    "AED": {"symbol": "د.إ", "name": "UAE Dirham",        "flag": "🇦🇪", "rate_to_inr": 22.73},
}

def convert_currency(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return amount
    return (amount * CURRENCIES[from_currency]["rate_to_inr"]) / CURRENCIES[to_currency]["rate_to_inr"]

def fmt_currency(amount, currency="INR"):
    sym = CURRENCIES.get(currency, CURRENCIES["INR"])["symbol"]
    return f"{sym}{amount:,.0f}" if currency == "JPY" else f"{sym}{amount:,.2f}"

def fmt_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return iso_str

def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def api_post(endpoint, payload, auth=False):
    headers = auth_headers() if auth else {}
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=payload, headers=headers, timeout=10)
        return r.status_code, r.json()
    except requests.exceptions.ConnectionError:
        return 0, {"message": "Cannot connect to backend. Is the server running on port 3000?"}
    except Exception as e:
        return 0, {"message": str(e)}

def api_get(endpoint, auth=True):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", headers=auth_headers() if auth else {}, timeout=10)
        return r.status_code, r.json()
    except requests.exceptions.ConnectionError:
        return 0, {"message": "Cannot connect to backend. Is the server running on port 3000?"}
    except Exception as e:
        return 0, {"message": str(e)}

def logout():
    st.session_state.token = None
    st.session_state.user  = None
    st.session_state.page  = "login"

def _is_credit(txn, account_id):
    to = txn.get("toAccount")
    if isinstance(to, dict):
        to = to.get("_id", "")
    return str(to) == str(account_id)

# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Base ── */
html, body, .stApp,
[data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
}
* { box-sizing: border-box; }

/* ── Hide streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── Block container ── */
.block-container {
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1280px !important;
}

/* ═══════════════════════════
   SIDEBAR
═══════════════════════════ */
[data-testid="stSidebar"] {
    background-color: #090d18 !important;
    border-right: 1px solid #1e2433 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1rem 0.9rem !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label {
    color: #7d8da8 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #7d8da8 !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    text-align: left !important;
    padding: 0.5rem 0.85rem !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    margin-bottom: 1px !important;
    transition: all 0.15s ease !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #13192a !important;
    color: #c9d1e0 !important;
    border-color: #1e2a40 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1e2433 !important;
    margin: 0.5rem 0 !important;
}

/* ═══════════════════════════
   INPUT FIELDS — dark bg, white text
   Using aggressive selectors to beat Streamlit's specificity
═══════════════════════════ */

/* All text/password/number inputs */
input[type="text"],
input[type="password"],
input[type="number"],
input[type="email"],
input[type="search"] {
    background-color: #13192a !important;
    color: #e6edf3 !important;
    -webkit-text-fill-color: #e6edf3 !important;
    border: 1.5px solid #1e2a40 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    caret-color: #4d8ef0 !important;
}
input[type="text"]:focus,
input[type="password"]:focus,
input[type="number"]:focus,
input[type="email"]:focus {
    border-color: #4d8ef0 !important;
    box-shadow: 0 0 0 3px rgba(77, 142, 240, 0.18) !important;
    outline: none !important;
}
input::placeholder {
    color: #3d4f6a !important;
    -webkit-text-fill-color: #3d4f6a !important;
}
/* Autofill override */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {
    -webkit-text-fill-color: #e6edf3 !important;
    -webkit-box-shadow: 0 0 0px 1000px #13192a inset !important;
    transition: background-color 5000s ease-in-out 0s;
}

/* Wrapper divs that Streamlit wraps inputs in */
[data-baseweb="input"],
[data-baseweb="base-input"],
[data-baseweb="input"] > div,
[data-baseweb="base-input"] > div {
    background-color: #13192a !important;
    border-color: #1e2a40 !important;
    border-radius: 8px !important;
}

/* Number input container */
[data-testid="stNumberInput"] > div {
    background-color: #13192a !important;
}
[data-testid="stNumberInput"] button {
    background: #1a2236 !important;
    border-color: #1e2a40 !important;
    color: #7d8da8 !important;
}
[data-testid="stNumberInput"] button:hover {
    background: #1e2a40 !important;
    color: #c9d1e0 !important;
}

/* ── Labels (all pages) ── */
.stTextInput > label,
.stNumberInput > label,
.stSelectbox > label,
[data-testid="stTextInput"] > label,
[data-testid="stNumberInput"] > label,
[data-testid="stSelectbox"] > label {
    color: #5d7090 !important;
    font-size: 0.77rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.7px !important;
}

/* ── Selectbox ── */
[data-baseweb="select"] > div:first-child,
[data-baseweb="select"] [data-baseweb="select"] {
    background-color: #13192a !important;
    border: 1.5px solid #1e2a40 !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
}
[data-baseweb="select"] svg { fill: #5d7090 !important; }
[data-baseweb="select"] span { color: #e6edf3 !important; }

/* Dropdown menu */
[data-baseweb="menu"],
[data-baseweb="popover"] > div {
    background-color: #13192a !important;
    border: 1px solid #1e2a40 !important;
    border-radius: 8px !important;
}
[role="option"] {
    background-color: transparent !important;
    color: #c9d1e0 !important;
    font-size: 0.875rem !important;
}
[role="option"]:hover,
[aria-selected="true"][role="option"] {
    background-color: #1a2236 !important;
    color: #e6edf3 !important;
}

/* ═══════════════════════════
   TABS
═══════════════════════════ */
[data-baseweb="tab-list"] {
    background: #13192a !important;
    border-radius: 10px !important;
    padding: 3px !important;
    border: 1px solid #1e2a40 !important;
    gap: 2px !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 7px !important;
    color: #5d7090 !important;
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 0.45rem 1.2rem !important;
    font-family: 'Inter', sans-serif !important;
}
[data-baseweb="tab"][aria-selected="true"] {
    background: #1a2236 !important;
    color: #e6edf3 !important;
}
[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] { display: none !important; }

/* ═══════════════════════════
   BUTTONS
═══════════════════════════ */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    font-size: 0.875rem !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
    border: 1px solid #1e2a40 !important;
    background: #13192a !important;
    color: #c9d1e0 !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    background: #1a2236 !important;
    border-color: #2a3a58 !important;
    color: #e6edf3 !important;
}
.stButton > button[kind="primary"] {
    background: #1a56c4 !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(26, 86, 196, 0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #2363d4 !important;
    box-shadow: 0 4px 14px rgba(26, 86, 196, 0.5) !important;
    transform: translateY(-1px) !important;
}

/* ═══════════════════════════
   ALERTS
═══════════════════════════ */
[data-testid="stSuccess"] > div {
    background: #0b2218 !important;
    border: 1px solid #196030 !important;
    border-radius: 8px !important;
    color: #3fb950 !important;
}
[data-testid="stError"] > div {
    background: #220b0b !important;
    border: 1px solid #7a1a1a !important;
    border-radius: 8px !important;
    color: #f85149 !important;
}
[data-testid="stInfo"] > div {
    background: #0a1828 !important;
    border: 1px solid #1a4a7a !important;
    border-radius: 8px !important;
    color: #4d8ef0 !important;
}
[data-testid="stWarning"] > div {
    background: #221700 !important;
    border: 1px solid #7a4a00 !important;
    border-radius: 8px !important;
    color: #d29922 !important;
}

/* Caption */
[data-testid="stCaptionContainer"] p { color: #3d4f6a !important; font-size: 0.77rem !important; }

/* Spinner */
.stSpinner > div { color: #4d8ef0 !important; }

/* Divider */
hr { border-color: #1e2433 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #1e2a40; border-radius: 3px; }

/* ═══════════════════════════
   PAGE HEADERS
═══════════════════════════ */
.pg-title {
    font-size: 1.75rem; font-weight: 800;
    color: #e6edf3; letter-spacing: -0.5px;
    margin-bottom: 0.2rem; line-height: 1.2;
}
.pg-title .hi { color: #4d8ef0; }
.pg-sub { font-size: 0.85rem; color: #3d4f6a; margin-bottom: 1.6rem; }
.sec-label {
    font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    color: #3d4f6a; margin: 1.4rem 0 0.7rem;
}

/* ═══════════════════════════
   COMPONENTS
═══════════════════════════ */

/* Balance card */
.bal-card {
    background: linear-gradient(140deg, #0f1e3a 0%, #102454 50%, #163272 100%);
    border: 1px solid #1e3a6e;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    position: relative; overflow: hidden;
    margin-bottom: 0.8rem;
}
.bal-card::after {
    content: ''; position: absolute;
    top: -70px; right: -70px;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: rgba(77,142,240,0.06);
    pointer-events: none;
}
.bal-label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #5d8ad0; margin-bottom: 0.5rem; }
.bal-amount { font-size: 2.3rem; font-weight: 800; color: #e6edf3; letter-spacing: -1.5px; font-family: 'JetBrains Mono', monospace; line-height: 1.1; margin-bottom: 0.5rem; }
.bal-id { font-size: 0.67rem; color: #3d5a8a; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px; }
.bal-chips { display: flex; gap: 0.4rem; margin-top: 0.8rem; }
.bal-chip { background: rgba(77,142,240,0.1); border: 1px solid rgba(77,142,240,0.18); border-radius: 20px; padding: 2px 9px; font-size: 0.67rem; font-weight: 600; color: #6a9de0; }

/* Dark card */
.card {
    background: #111827;
    border: 1px solid #1e2a40;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 0.8rem;
}
.card-title { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #3d4f6a; margin-bottom: 1rem; }

/* Stat card */
.stat-card {
    background: #111827;
    border: 1px solid #1e2a40;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}
.stat-label { font-size: 0.7rem; color: #3d4f6a; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
.stat-val { font-size: 1.45rem; font-weight: 800; color: #e6edf3; margin-top: 0.3rem; font-family: 'JetBrains Mono', monospace; letter-spacing: -0.5px; }

/* Transaction card */
.txn-card {
    background: #111827;
    border: 1px solid #1e2a40;
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.4rem;
    display: flex; justify-content: space-between; align-items: center;
    transition: border-color 0.15s;
}
.txn-card:hover { border-color: #2a3a58; }
.txn-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700; margin-right: 0.9rem; flex-shrink: 0; }
.txn-icon-in  { background: #0b2218; color: #3fb950; }
.txn-icon-out { background: #220b0b; color: #f85149; }
.txn-amt-in  { color: #3fb950; font-weight: 700; font-size: 1rem; font-family: 'JetBrains Mono', monospace; }
.txn-amt-out { color: #f85149; font-weight: 700; font-size: 1rem; font-family: 'JetBrains Mono', monospace; }

/* Badges */
.badge { display: inline-block; padding: 1px 7px; border-radius: 20px; font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; }
.badge-completed { background: #0b2218; color: #3fb950; }
.badge-pending   { background: #221700; color: #d29922; }
.badge-failed    { background: #220b0b; color: #f85149; }
.badge-reversed  { background: #151530; color: #a5b4fc; }

/* Currency pill */
.cur-pill { display: inline-block; background: #0d1e35; color: #4d8ef0; border: 1px solid #1a3a5a; border-radius: 20px; padding: 1px 7px; font-size: 0.63rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

/* Rate row */
.rate-row { display: flex; justify-content: space-between; align-items: center; padding: 0.55rem 0; border-bottom: 1px solid #1a2236; }
.rate-row:last-child { border-bottom: none; }

/* Quick action card */
.qa-card { background: #111827; border: 1px solid #1e2a40; border-radius: 12px; padding: 1rem 0.8rem; text-align: center; transition: all 0.15s; }
.qa-card:hover { border-color: #1a56c4; }
.qa-icon  { font-size: 1.25rem; margin-bottom: 0.3rem; }
.qa-label { font-size: 0.73rem; font-weight: 600; color: #5d7090;  }

/* Login */
.login-logo { text-align: center; margin-bottom: 1.8rem; }
.login-logo-icon {
    width: 58px; height: 58px;
    background: #1a56c4;
    border-radius: 16px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 1.6rem; margin-bottom: 0.8rem;
    box-shadow: 0 8px 24px rgba(26,86,196,0.4);
}
.login-brand { font-size: 1.7rem; font-weight: 800; color: #e6edf3; letter-spacing: -0.5px; }
.login-brand span { color: #4d8ef0; }
.login-tagline { font-size: 0.82rem; color: #3d4f6a; margin-top: 0.3rem; }
.login-card { background: #111827; border: 1px solid #1e2a40; border-radius: 16px; padding: 1.8rem; }
.trust-bar { display: flex; justify-content: center; gap: 1.8rem; margin-top: 1.4rem; font-size: 0.73rem; color: #3d4f6a; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
def render_sidebar(active_page="dashboard"):
    user = st.session_state.user
    name = user["name"] if user else ""
    initials = "".join([p[0].upper() for p in name.split()[:2]]) if name else "?"

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:0.3rem 0.2rem 0.8rem;">
            <div style="display:flex;align-items:center;gap:0.55rem;margin-bottom:1.2rem;">
                <div style="width:30px;height:30px;background:#1a56c4;border-radius:7px;
                            display:flex;align-items:center;justify-content:center;
                            font-size:0.95rem;font-weight:800;color:#fff;flex-shrink:0;">N</div>
                <span style="font-size:1rem;font-weight:800;color:#e6edf3 !important;letter-spacing:-0.3px;">NexPay</span>
            </div>
            <div style="background:#13192a;border:1px solid #1e2a40;border-radius:10px;
                        padding:0.65rem 0.8rem;display:flex;align-items:center;gap:0.65rem;">
                <div style="width:34px;height:34px;background:#1a56c4;border-radius:8px;
                            display:flex;align-items:center;justify-content:center;
                            font-size:0.85rem;font-weight:700;color:#fff;flex-shrink:0;">{initials}</div>
                <div style="overflow:hidden;min-width:0;">
                    <div style="font-weight:600;color:#c9d1e0;font-size:0.83rem;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
                    <div style="font-size:0.7rem;color:#3d4f6a;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{user['email'] if user else ''}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        nav = [
            ("dashboard",    "🏠", "Dashboard"),
            ("send",         "↗️", "Send Money"),
            ("transactions", "📋", "Transactions"),
            ("converter",    "🔄", "Currency Converter"),
            ("new_account",  "➕", "Open New Account"),
            ("add_balance",  "💰", "Add Balance"),
        ]
        for pk, icon, lbl in nav:
            if st.button(f"{icon}  {lbl}", key=f"nav_{pk}"):
                st.session_state.page = pk; st.rerun()

        st.divider()
        if st.button("🚪  Sign Out", key="nav_logout"):
            logout(); st.rerun()

        st.markdown('<div style="margin-top:1rem;text-align:center;font-size:0.67rem;color:#1e2a40;">🔒 256-bit SSL</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════
def page_login():
    _, col, _ = st.columns([1, 1.05, 1])
    with col:
        st.markdown("""
        <div class="login-logo">
            <div class="login-logo-icon">💳</div>
            <div class="login-brand">Nex<span>Pay</span></div>
            <div class="login-tagline">Professional banking for the modern world</div>
        </div>
        """, unsafe_allow_html=True)

        
        tab_in, tab_reg = st.tabs(["Sign In", "Create Account"])

        with tab_in:
            st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
            email = st.text_input("Email address", key="li_email", placeholder="you@example.com")
            password = st.text_input("Password", key="li_pass", placeholder="Enter password", type="password")
            st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
            if st.button("Sign In →", key="btn_li", type="primary"):
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Signing in…"):
                        s, d = api_post("/auth/login", {"email": email, "password": password})
                    if s == 200:
                        st.session_state.token = d["token"]
                        st.session_state.user  = d["user"]
                        st.session_state.page  = "dashboard"
                        st.rerun()
                    else:
                        st.error(d.get("message", "Login failed."))

        with tab_reg:
            st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
            r_name  = st.text_input("Full name",        key="rg_name",  placeholder="John Doe")
            r_email = st.text_input("Email address",    key="rg_email", placeholder="you@example.com")
            r_pass  = st.text_input("Password",         key="rg_pass",  placeholder="Min 6 characters", type="password")
            r_pass2 = st.text_input("Confirm password", key="rg_pass2", placeholder="Repeat password",  type="password")
            st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
            if st.button("Create Account →", key="btn_rg", type="primary"):
                if not all([r_name, r_email, r_pass, r_pass2]):
                    st.error("Please fill in all fields.")
                elif r_pass != r_pass2:
                    st.error("Passwords do not match.")
                elif len(r_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    with st.spinner("Creating account…"):
                        s, d = api_post("/auth/register", {"name": r_name, "email": r_email, "password": r_pass})
                    if s == 201:
                        st.session_state.token = d["token"]
                        st.session_state.user  = d["user"]
                        st.session_state.page  = "dashboard"
                        st.rerun()
                    else:
                        st.error(d.get("message", "Registration failed."))

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="trust-bar"><span>🔒 256-bit SSL</span><span>🛡️ Bank-grade Security</span><span>⚡ Instant Transfers</span></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
def page_dashboard():
    render_sidebar("dashboard")
    user = st.session_state.user
    hour = datetime.now().hour
    g = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"

    st.markdown(f'<div class="pg-title">{g}, <span class="hi">{user["name"].split()[0]}</span> 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Here\'s your complete financial overview.</div>', unsafe_allow_html=True)

    with st.spinner("Loading accounts…"):
        status, data = api_get("/accounts")

    if status != 200:
        st.error(data.get("message", "Failed to load accounts.")); return

    accounts = data.get("accounts", [])
    if not accounts:
        st.info("No accounts yet.")
        if st.button("➕ Open Your First Account", type="primary"):
            s, d = api_post("/accounts", {}, auth=True)
            if s == 201: st.rerun()
            else: st.error(d.get("message", "Failed."))
        return

    st.markdown('<div class="sec-label">Your Accounts</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(accounts), 3))
    for i, acc in enumerate(accounts):
        with cols[i % 3]:
            cur = acc.get("currency", "INR")
            ci  = CURRENCIES.get(cur, CURRENCIES["INR"])
            st.markdown(f"""
            <div class="bal-card">
                <div class="bal-label">{ci['flag']}  {ci['name']}</div>
                <div class="bal-amount">{fmt_currency(acc.get('balance',0), cur)}</div>
                <div class="bal-id">···· {str(acc['_id'])[-6:].upper()}</div>
                <div class="bal-chips">
                    <span class="bal-chip">✓ {acc.get('status','active').upper()}</span>
                    <span class="bal-chip">{cur}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Quick Actions</div>', unsafe_allow_html=True)
    actions = [
        ("send","📤","Send Money"), ("transactions","📋","Transactions"),
        ("converter","🔄","Converter"), ("new_account","➕","New Account"), ("add_balance","💰","Add Balance"),
    ]
    acols = st.columns(5)
    for idx, (pk, icon, lbl) in enumerate(actions):
        with acols[idx]:
            st.markdown(f'<div class="qa-card"><div class="qa-icon">{icon}</div><div class="qa-label">{lbl}</div></div>', unsafe_allow_html=True)
            if st.button(lbl, key=f"dash_{pk}"):
                st.session_state.page = pk; st.rerun()

    st.markdown('<div class="sec-label">Recent Activity</div>', unsafe_allow_html=True)
    first = accounts[0]
    s2, d2 = api_get(f"/accounts/transactions/{first['_id']}")
    if s2 == 200:
        txns = d2.get("transactions", [])[:6]
        if txns:
            for txn in txns:
                ic = _is_credit(txn, first["_id"])
                st.markdown(f"""
                <div class="txn-card">
                    <div style="display:flex;align-items:center;">
                        <div class="txn-icon {'txn-icon-in' if ic else 'txn-icon-out'}">{'↙' if ic else '↗'}</div>
                        <div>
                            <div style="font-weight:600;color:#c9d1e0;font-size:0.875rem;">{'Received' if ic else 'Sent'}</div>
                            <span class="badge badge-{txn.get('status','pending')}">{txn.get('status','pending')}</span>
                            <div style="font-size:0.73rem;color:#3d4f6a;margin-top:2px;">{fmt_date(txn.get('createdAt',''))}</div>
                        </div>
                    </div>
                    <div class="{'txn-amt-in' if ic else 'txn-amt-out'}">{'+' if ic else '-'}{fmt_currency(txn.get('amount',0))}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#3d4f6a;font-size:0.85rem;padding:1rem 0;">No transactions yet — send or receive money to get started.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# SEND MONEY
# ═══════════════════════════════════════════════════════════════════════════
def page_send():
    if st.session_state.get("txn_success"):
        if time.time() - st.session_state.get("txn_time", 0) < 5:
            st.success(st.session_state["txn_success"])
            st.balloons()
        else:
            st.session_state["txn_success"] = None

    render_sidebar("send")
    st.markdown('<div class="pg-title">Send <span class="hi">Money</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Transfer funds to any account instantly.</div>', unsafe_allow_html=True)

    my_s, my_d = api_get("/accounts")
    if my_s != 200: st.error(my_d.get("message", "Failed.")); return
    my_accounts = [a for a in my_d.get("accounts", []) if a.get("status") == "active"]
    if not my_accounts: st.warning("No active accounts."); return

    all_s, all_d = api_get("/accounts/all")
    if all_s != 200: st.error(all_d.get("message", "Failed.")); return
    all_accounts = all_d.get("accounts", [])

    col1, col2 = st.columns([1.3, 1], gap="large")

    with col1:
        
        st.markdown('<div class="card-title">Transfer Details</div>', unsafe_allow_html=True)

        # ① Recipient search — TOP
        search = st.text_input("Search recipient", placeholder="Type a name to search…", key="send_search")

        recipient_accounts = [
            a for a in all_accounts
            if str(a.get("user", {}).get("_id")) != str(st.session_state.user.get("_id"))
        ]
        if search:
            recipient_accounts = [
                a for a in recipient_accounts
                if search.lower() in a.get("user", {}).get("name", "").lower()
            ]

        # ② From account
        acc_labels = [f"{a.get('user',{}).get('name','User')} — {fmt_currency(a.get('balance',0))}" for a in my_accounts]
        sel_idx = st.selectbox("From account", range(len(my_accounts)), format_func=lambda i: acc_labels[i])
        sel_acc = my_accounts[sel_idx]

        # ③ To account
        if not recipient_accounts:
            st.warning("No recipients found.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        rec_labels = [a.get("user", {}).get("name", "User") for a in recipient_accounts]
        rec_idx    = st.selectbox("To account", range(len(recipient_accounts)), format_func=lambda i: rec_labels[i])
        sel_rec    = recipient_accounts[rec_idx]
        to_id      = sel_rec["_id"]

        rname = sel_rec.get("user", {}).get("name", "Unknown")
        st.markdown(f"""
        <div style="background:#0d1e35;border:1px solid #1a3a5a;border-radius:8px;
                    padding:0.5rem 0.9rem;margin:0.4rem 0 0.6rem;font-size:0.82rem;color:#4d8ef0;">
            📨 Sending to: <strong style="color:#7ab4f8;">{rname}</strong>
        </div>
        """, unsafe_allow_html=True)

        # ④ Amount
        amount = st.number_input("Amount (₹)", min_value=0.01, step=100.0, format="%.2f", key="send_amount")
        st.caption("A unique idempotency key is auto-generated to prevent duplicates.")
        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

        if st.button("Send Money →", key="btn_send", type="primary"):
            if amount <= 0:
                st.error("Amount must be greater than ₹0.")
            elif to_id == sel_acc["_id"]:
                st.error("Cannot send to your own account.")
            else:
                with st.spinner("Processing…"):
                    s, d = api_post("/transactions", {
                        "toAccountId": to_id, "amount": amount,
                        "idempotencyKey": str(uuid.uuid4())
                    }, auth=True)
                if s == 201:
                    st.session_state["txn_success"] = f"✅ Transfer of {fmt_currency(amount)} successful!"
                    st.session_state["txn_time"]    = time.time()
                    st.rerun()
                elif s == 200:
                    st.info(d.get("message", "Duplicate transaction detected."))
                else:
                    st.error(d.get("message", "Transfer failed."))

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        cur = sel_acc.get("currency", "INR")
        ci  = CURRENCIES.get(cur, CURRENCIES["INR"])
        st.markdown(f"""
        <div class="bal-card">
            <div class="bal-label">{ci['flag']}  Available Balance</div>
            <div class="bal-amount">{fmt_currency(sel_acc.get('balance',0), cur)}</div>
            <div class="bal-id">···· {str(sel_acc['_id'])[-6:].upper()}</div>
            <div class="bal-chips">
                <span class="bal-chip">{cur}</span>
                <span class="bal-chip">✓ Active</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if amount > 0:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Equivalent Amounts</div>', unsafe_allow_html=True)
            for c in ["TWD", "USD", "EUR", "GBP", "JPY", "SGD"]:
                conv = convert_currency(amount, "INR", c)
                info = CURRENCIES[c]
                st.markdown(f"""
                <div class="rate-row">
                    <span style="font-size:0.875rem;color:#5d7090;">{info['flag']} {c}</span>
                    <span style="font-family:'JetBrains Mono',monospace;font-weight:600;color:#c9d1e0;font-size:0.875rem;">{fmt_currency(conv, c)}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════
def page_transactions():
    render_sidebar("transactions")
    st.markdown('<div class="pg-title">Transaction <span class="hi">History</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">All your account activity in one place.</div>', unsafe_allow_html=True)

    s, d = api_get("/accounts")
    if s != 200: st.error(d.get("message", "Failed.")); return
    accounts = d.get("accounts", [])
    if not accounts: st.info("No accounts found."); return

    acc_labels = [f"{a.get('user',{}).get('name','User')} — {fmt_currency(a.get('balance',0))}" for a in accounts]
    idx = st.selectbox("Select account", range(len(accounts)), format_func=lambda i: acc_labels[i])
    acc = accounts[idx]

    with st.spinner("Loading…"):
        ts, td = api_get(f"/accounts/transactions/{acc['_id']}")
    if ts != 200: st.error(td.get("message", "Failed.")); return

    txns = td.get("transactions", [])
    cur  = acc.get("currency", "INR")

    total_in  = sum(t["amount"] for t in txns if _is_credit(t, acc["_id"]) and t.get("status") == "completed")
    total_out = sum(t["amount"] for t in txns if not _is_credit(t, acc["_id"]) and t.get("status") == "completed")

    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f'<div class="stat-card"><div class="stat-label">Total Received</div><div class="stat-val" style="color:#3fb950;">{fmt_currency(total_in,cur)}</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="stat-card"><div class="stat-label">Total Sent</div><div class="stat-val" style="color:#f85149;">{fmt_currency(total_out,cur)}</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="stat-card"><div class="stat-label">Total Transactions</div><div class="stat-val">{len(txns)}</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    if not txns: st.info("No transactions yet."); return

    fc1, fc2 = st.columns(2)
    with fc1: direction = st.selectbox("Direction", ["All", "Credits (Received)", "Debits (Sent)"])
    with fc2: sf = st.selectbox("Status", ["All", "completed", "pending", "failed", "reversed"])

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
    for txn in txns:
        ic = _is_credit(txn, acc["_id"])
        if direction == "Credits (Received)" and not ic: continue
        if direction == "Debits (Sent)"      and ic:     continue
        if sf != "All" and txn.get("status") != sf:     continue

        cp = txn.get("fromAccount") if ic else txn.get("toAccount")
        if isinstance(cp, dict): cp = cp.get("_id", "")

        st.markdown(f"""
        <div class="txn-card">
            <div style="display:flex;align-items:center;">
                <div class="txn-icon {'txn-icon-in' if ic else 'txn-icon-out'}">{'↙' if ic else '↗'}</div>
                <div>
                    <div style="font-weight:600;color:#c9d1e0;font-size:0.875rem;">{'RECEIVED' if ic else 'SENT'}</div>
                    <span class="badge badge-{txn.get('status','pending')}">{txn.get('status','pending')}</span>
                    <div style="font-size:0.72rem;color:#3d4f6a;margin-top:2px;">{fmt_date(txn.get('createdAt',''))}</div>
                    <div style="font-size:0.67rem;color:#1e2a40;font-family:'JetBrains Mono',monospace;">
                        {'From' if ic else 'To'}: ···{str(cp)[-8:]}
                    </div>
                </div>
            </div>
            <div style="text-align:right;">
                <div class="{'txn-amt-in' if ic else 'txn-amt-out'}">{'+' if ic else '-'}{fmt_currency(txn.get('amount',0),cur)}</div>
                <div class="cur-pill">{cur}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# CURRENCY CONVERTER
# ═══════════════════════════════════════════════════════════════════════════
def page_converter():
    render_sidebar("converter")
    st.markdown('<div class="pg-title">Currency <span class="hi">Converter</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Multi-currency conversion across 8 major currencies.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1], gap="large")
    cur_opts   = list(CURRENCIES.keys())
    cur_labels = [f"{CURRENCIES[c]['flag']} {c} — {CURRENCIES[c]['name']}" for c in cur_opts]

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Convert Currency</div>', unsafe_allow_html=True)
        fi  = st.selectbox("From", range(len(cur_opts)), format_func=lambda i: cur_labels[i], key="cv_from")
        fc  = cur_opts[fi]
        amt = st.number_input("Amount", min_value=0.01, value=1000.0, step=100.0, format="%.2f", key="cv_amt")
        ti  = st.selectbox("To", range(len(cur_opts)), format_func=lambda i: cur_labels[i], key="cv_to", index=2)
        tc  = cur_opts[ti]
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

        if st.button("Convert →", key="btn_cv", type="primary"):
            res  = convert_currency(amt, fc, tc)
            rate = convert_currency(1, fc, tc)
            fi_  = CURRENCIES[fc]; ti_ = CURRENCIES[tc]
            st.markdown(f"""
            <div style="background:#0d1e35;border:1px solid #1a3a5a;border-radius:12px;padding:1.2rem 1.4rem;margin-top:0.8rem;">
                <div style="font-size:0.7rem;color:#4d8ef0;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.5rem;">Result</div>
                <div style="font-size:0.875rem;color:#5d7090;margin-bottom:0.3rem;">{fi_['flag']} {fmt_currency(amt, fc)} →</div>
                <div style="font-size:2.1rem;font-weight:800;color:#e6edf3;font-family:'JetBrains Mono',monospace;letter-spacing:-1px;margin-bottom:0.5rem;">
                    {ti_['flag']} {fmt_currency(res, tc)}
                </div>
                <span style="background:#111827;color:#4d8ef0;border:1px solid #1e2a40;border-radius:6px;
                             padding:3px 10px;font-size:0.72rem;font-family:'JetBrains Mono',monospace;font-weight:600;">
                    1 {fc} = {fmt_currency(rate, tc)} {tc}
                </span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Live Rates vs INR</div>', unsafe_allow_html=True)
        for code, info in CURRENCIES.items():
            st.markdown(f"""
            <div class="rate-row">
                <div style="display:flex;align-items:center;gap:0.55rem;">
                    <span style="font-size:1rem;">{info['flag']}</span>
                    <div>
                        <div style="font-weight:600;color:#c9d1e0;font-size:0.84rem;">{code}</div>
                        <div style="color:#3d4f6a;font-size:0.69rem;">{info['name']}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:700;color:#4d8ef0;font-size:0.875rem;font-family:'JetBrains Mono',monospace;">{fmt_currency(info['rate_to_inr'],'INR')}</div>
                    <div style="color:#3d4f6a;font-size:0.67rem;">per 1 {code}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("Rates are indicative only.")

    st.markdown('<div class="sec-label">1,000 INR equals</div>', unsafe_allow_html=True)
    rcols = st.columns(4)
    for i, cur in enumerate(cur_opts):
        with rcols[i % 4]:
            val  = convert_currency(1000, "INR", cur)
            info = CURRENCIES[cur]
            st.markdown(f'<div class="stat-card" style="margin-bottom:0.5rem;"><div class="stat-label">{info["flag"]} {cur}</div><div class="stat-val" style="font-size:0.95rem;">{fmt_currency(val,cur)}</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# NEW ACCOUNT
# ═══════════════════════════════════════════════════════════════════════════
def page_new_account():
    render_sidebar("new_account")
    st.markdown('<div class="pg-title">Open New <span class="hi">Account</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Create an additional bank account instantly.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown('<div class="card"><div class="card-title">Standard Account</div>', unsafe_allow_html=True)
        for f in ["INR base currency", "Instant transfers", "Full transaction history", "Multi-currency view", "Zero fees"]:
            st.markdown(f'<div style="font-size:0.875rem;color:#8b949e;padding:0.2rem 0;"><span style="color:#3fb950;font-weight:700;margin-right:8px;">✓</span>{f}</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div></div>", unsafe_allow_html=True)
        if st.button("Open Account →", key="btn_new", type="primary"):
            with st.spinner("Opening…"):
                s, d = api_post("/accounts", {}, auth=True)
            if s == 201: st.success("🎉 Account opened!"); st.json(d.get("account", {}))
            else: st.error(d.get("message", "Failed."))

    with col2:
        st.markdown("""
        <div class="card" style="border-color:#1a3a5a;background:#0d1e35;">
            <div class="card-title" style="color:#4d8ef0;">Did You Know?</div>
            <p style="color:#5d8ad0;font-size:0.875rem;line-height:1.75;margin:0;">
                NexPay supports <strong style="color:#7ab4f8;">8 currencies</strong> — INR, TWD, USD, EUR, GBP, JPY, SGD, and AED.
                Use the Currency Converter to check indicative exchange rates at any time.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# ADD BALANCE
# ═══════════════════════════════════════════════════════════════════════════
def page_add_balance():
    render_sidebar("add_balance")
    st.markdown('<div class="pg-title">Add <span class="hi">Balance</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Add funds to your account instantly.</div>', unsafe_allow_html=True)

    if "dep_val" not in st.session_state:
        st.session_state.dep_val = 100.0

    s, d = api_get("/accounts")
    if s != 200: st.error(d.get("message", "Failed.")); return
    accounts = d.get("accounts", [])
    if not accounts: st.warning("No accounts yet."); return
    active = [a for a in accounts if a.get("status") == "active"]
    if not active: st.warning("No active accounts."); return

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:

        acc = active[0]
        cur = acc.get("currency", "INR")

        st.markdown('<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#3d4f6a;margin-bottom:0.5rem;">Quick Add</div>', unsafe_allow_html=True)
        qa1, qa2, qa3, qa4 = st.columns(4)
        for qcol, qlabel, qval in [(qa1,"₹500",500.0),(qa2,"₹1,000",1000.0),(qa3,"₹2,000",2000.0),(qa4,"₹5,000",5000.0)]:
            with qcol:
                if st.button(qlabel, key=f"qa_{int(qval)}"):
                    st.session_state.dep_val = qval
                    st.rerun()

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

        # Fixed: value= from session state, separate key to avoid conflict
        amount = st.number_input(
            "Amount (₹)",
            min_value=1.0, step=100.0, format="%.2f",
            value=float(st.session_state.dep_val),
            key="dep_number_input"
        )
        st.session_state.dep_val = float(amount)

        if amount > 0:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            ec1, ec2, ec3, ec4 = st.columns(4)
            for ecol, c in zip([ec1, ec2, ec3, ec4], ["TWD", "USD", "EUR", "GBP"]):
                with ecol:
                    v  = convert_currency(amount, "INR", c)
                    ci = CURRENCIES[c]
                    st.markdown(f"""
                    <div style="background:#13192a;border:1px solid #1e2a40;border-radius:8px;
                                padding:0.5rem 0.4rem;text-align:center;">
                        <div style="color:#3d4f6a;font-size:0.67rem;font-weight:600;">{ci['flag']} {c}</div>
                        <div style="font-weight:700;color:#4d8ef0;font-size:0.8rem;font-family:'JetBrains Mono',monospace;">{fmt_currency(v,c)}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.caption("Funds credited to your account immediately.")
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

        if st.button("Add Balance →", key="btn_dep", type="primary"):
            if amount <= 0:
                st.error("Enter an amount greater than ₹0.")
            else:
                with st.spinner(f"Adding {fmt_currency(amount)}…"):
                    ds, dd = api_post("/accounts/deposit", {"amount": amount}, auth=True)
                if ds == 200:
                    st.success(f"✅ {fmt_currency(amount)} added! New balance: {fmt_currency(dd.get('balance',0))}")
                    st.balloons()
                    st.session_state.dep_val = 100.0
                    st.rerun()
                else:
                    st.error(dd.get("message", "Failed."))

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        ci   = CURRENCIES.get(cur, CURRENCIES["INR"])
        live = acc.get("balance", 0)
        bs, bd = api_get(f"/accounts/{acc['_id']}/balance")
        if bs == 200: live = bd.get("balance", live)

        st.markdown(f"""
        <div class="bal-card">
            <div class="bal-label">{ci['flag']}  Current Balance</div>
            <div class="bal-amount">{fmt_currency(live, cur)}</div>
            <div class="bal-id">···· {str(acc['_id'])[-6:].upper()}</div>
            <div class="bal-chips">
                <span class="bal-chip">✓ {acc.get('status','active').upper()}</span>
                <span class="bal-chip">{cur}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if amount > 0:
            projected = live + amount
            st.markdown(f"""
            <div class="card">
                <div class="card-title">After Deposit</div>
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #1e2a40;">
                    <span style="font-size:0.82rem;color:#5d7090;">Current</span>
                    <span style="font-family:'JetBrains Mono',monospace;font-weight:600;color:#c9d1e0;font-size:0.875rem;">{fmt_currency(live,cur)}</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #1e2a40;">
                    <span style="font-size:0.82rem;color:#3fb950;">Adding</span>
                    <span style="font-family:'JetBrains Mono',monospace;font-weight:600;color:#3fb950;font-size:0.875rem;">+{fmt_currency(amount,cur)}</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.5rem 0;">
                    <span style="font-size:0.875rem;font-weight:700;color:#e6edf3;">New Balance</span>
                    <span style="font-family:'JetBrains Mono',monospace;font-weight:800;color:#4d8ef0;font-size:1.05rem;">{fmt_currency(projected,cur)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════
if not st.session_state.token:
    page_login()
else:
    p = st.session_state.page
    if   p == "dashboard":    page_dashboard()
    elif p == "send":         page_send()
    elif p == "transactions": page_transactions()
    elif p == "converter":    page_converter()
    elif p == "new_account":  page_new_account()
    elif p == "add_balance":  page_add_balance()
    else:                     page_dashboard()