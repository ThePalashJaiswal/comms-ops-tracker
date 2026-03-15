import streamlit as st
import pandas as pd
import json
import os
import base64
import requests
from datetime import datetime, date
from streamlit_autorefresh import st_autorefresh
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Comms Ops Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Auto-refresh every 30 seconds ────────────────────────────────────────────
st_autorefresh(interval=60000, key="autorefresh")

# ── GitHub config (set in Streamlit secrets) ─────────────────────────────────
GITHUB_TOKEN  = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO   = st.secrets.get("GITHUB_REPO", "")   # e.g. "palash/comms-ops-tracker"
GITHUB_BRANCH = st.secrets.get("GITHUB_BRANCH", "main")
DATA_FILE     = "data/events.json"

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:ital,wght@0,300;0,600;1,300&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }

.main-title {
    font-family: 'Fraunces', serif;
    font-size: 28px;
    font-weight: 300;
    color: #1a1a18;
    margin-bottom: 0px;
}
.main-title span { font-style: italic; font-weight: 600; color: #BA7517; }

.stat-card {
    background: #f7f5f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 4px;
}
.stat-label { font-size: 11px; color: #8a8a84; text-transform: uppercase; letter-spacing: 0.07em; }
.stat-num { font-family: 'Fraunces', serif; font-size: 28px; font-weight: 600; line-height: 1.1; }
.num-red { color: #A32D2D; }
.num-orange { color: #854F0B; }
.num-green { color: #3B6D11; }
.num-ink { color: #1a1a18; }

.brand-le5  { background:#EEEDFE; color:#3B2F8A; border:1px solid #AFA9EC; border-radius:10px; padding:2px 9px; font-size:11px; font-weight:500; }
.brand-le3  { background:#E1F5EE; color:#085041; border:1px solid #5DCAA5; border-radius:10px; padding:2px 9px; font-size:11px; font-weight:500; }
.brand-leac { background:#FAECE7; color:#712B13; border:1px solid #F0997B; border-radius:10px; padding:2px 9px; font-size:11px; font-weight:500; }
.brand-jg   { background:#FAEEDA; color:#633806; border:1px solid #EF9F27; border-radius:10px; padding:2px 9px; font-size:11px; font-weight:500; }

.status-done     { background:#EAF3DE; color:#3B6D11; border-radius:8px; padding:2px 8px; font-size:11px; }
.status-progress { background:#FAEEDA; color:#854F0B; border-radius:8px; padding:2px 8px; font-size:11px; }
.status-blocked  { background:#FCEBEB; color:#A32D2D; border-radius:8px; padding:2px 8px; font-size:11px; }
.status-pending  { background:#F1EFE8; color:#5F5E5A; border-radius:8px; padding:2px 8px; font-size:11px; }

.day-header {
    font-family: 'Fraunces', serif;
    font-size: 16px;
    font-weight: 400;
    color: #1a1a18;
    border-bottom: 1px solid #e2dfd8;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 4px;
}
.day-today   { color: #854F0B; font-weight: 600; }
.day-urgent  { color: #A32D2D; }
.day-past    { color: #8a8a84; }

.today-badge  { background:#FAEEDA; color:#633806; font-size:10px; padding:2px 8px; border-radius:8px; margin-left:10px; }
.urgent-badge { background:#FCEBEB; color:#A32D2D; font-size:10px; padding:2px 8px; border-radius:8px; margin-left:10px; }
.flagged-badge { background:#FCEBEB; color:#A32D2D; font-size:10px; padding:2px 8px; border-radius:8px; }

[data-testid="stDataFrame"] { border: 1px solid #e2dfd8; border-radius: 8px; }
div[data-testid="stHorizontalBlock"] { gap: 8px; }

.stSelectbox > div > div { border-radius: 6px !important; font-size: 13px !important; }
.stTextInput > div > div > input { border-radius: 6px !important; font-size: 13px !important; }

.save-msg { font-size: 12px; color: #3B6D11; }
</style>
""", unsafe_allow_html=True)

# ── Seed data ─────────────────────────────────────────────────────────────────
SEED_EVENTS = [
    {"id":1,"date":"2026-03-01","brand":"LE5","event":"AISAT","detail":"Scholarship Test","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":2,"date":"2026-03-02","brand":"LE5","event":"Sale","detail":"Holi Sale 2027","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":3,"date":"2026-03-03","brand":"LE5","event":"Sale","detail":"Holi Sale 2027","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":4,"date":"2026-03-05","brand":"LE5","event":"Batch Launch","detail":"2028 Achievers Plat+Gold (Eng)","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":5,"date":"2026-03-06","brand":"LE5","event":"Emailer","detail":"Your NLU dream begins today","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":6,"date":"2026-03-06","brand":"LE5","event":"Batch Launch","detail":"2027 Fighters + Warriors Plat+Gold","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":7,"date":"2026-03-07","brand":"LE5","event":"Webinar","detail":"Early Start for Law Career","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":8,"date":"2026-03-08","brand":"LE5","event":"AISAT","detail":"Scholarship Test","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":9,"date":"2026-03-09","brand":"LE5","event":"Emailer","detail":"A Small Check-In for CLAT Prep","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":10,"date":"2026-03-09","brand":"LE5","event":"Batch Launch","detail":"2027 Fighters+Warriors Hinglish+Eng","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":11,"date":"2026-03-11","brand":"LE5","event":"Emailer","detail":"Someone else is studying right now","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":12,"date":"2026-03-13","brand":"LE5","event":"Emailer","detail":"TBD","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":13,"date":"2026-03-14","brand":"LE5","event":"WA Message","detail":"Conversational Awareness – Fighters/Warriors/Achievers","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":14,"date":"2026-03-14","brand":"LE5","event":"Webinar","detail":"Smart CLAT Strategy for Future Aspirants","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":15,"date":"2026-03-15","brand":"LE5","event":"AISAT","detail":"Scholarship Test","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":16,"date":"2026-03-16","brand":"LE5","event":"Emailer","detail":"Scored low in your mock? Read this.","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":17,"date":"2026-03-16","brand":"LE5","event":"Batch Launch","detail":"2027 Fighters+Warriors Plat+Gold Hinglish","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":18,"date":"2026-03-17","brand":"LE5","event":"WA Message","detail":"Awareness for GSAT","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":19,"date":"2026-03-18","brand":"LE5","event":"Emailer","detail":"TBD","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":20,"date":"2026-03-21","brand":"LE5","event":"Webinar","detail":"CLAT Journey to law career","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":21,"date":"2026-03-21","brand":"LE5","event":"WA Message","detail":"Offline Reminder for GSAT","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":22,"date":"2026-03-22","brand":"LE5","event":"GSAT","detail":"Scholarship Test","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":23,"date":"2026-03-23","brand":"LE5","event":"Batch Launch","detail":"2027 Fighter+Warriors+2028 Achievers","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":24,"date":"2026-03-27","brand":"LE5","event":"Webinar","detail":"CLAT Rank Strategy for Successful Law Career","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":25,"date":"2026-03-29","brand":"LE5","event":"AISAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":26,"date":"2026-03-31","brand":"LE5","event":"Emailer","detail":"What CLAT toppers do every day","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":27,"date":"2026-03-01","brand":"LE3","event":"AILSAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":28,"date":"2026-03-02","brand":"LE3","event":"Sale","detail":"Holi Offer","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":29,"date":"2026-03-06","brand":"LE3","event":"Rapid Revision","detail":"Batch Demo – 2026 Batch","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":30,"date":"2026-03-08","brand":"LE3","event":"AILSAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":31,"date":"2026-03-10","brand":"LE3","event":"WA Message","detail":"GSAT Awareness – 2027 Batch","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":32,"date":"2026-03-11","brand":"LE3","event":"Mail","detail":"Life at DU vs BHU vs GLC","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":33,"date":"2026-03-13","brand":"LE3","event":"Webinar","detail":"45 Days Strategy for NLSAT 2026","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":34,"date":"2026-03-14","brand":"LE3","event":"WA Message","detail":"GSAT Offline Reminder","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":35,"date":"2026-03-14","brand":"LE3","event":"WA Message","detail":"MH-CET AIOM Offline Reminder","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":36,"date":"2026-03-15","brand":"LE3","event":"GSAT","detail":"Scholarship Test","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":37,"date":"2026-03-15","brand":"LE3","event":"MHCET AIOM","detail":"All India Open Mock (Offline)","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":38,"date":"2026-03-17","brand":"LE3","event":"Batch Launch","detail":"NLSAT Pro 2027 + Super Course 2027","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":39,"date":"2026-03-21","brand":"LE3","event":"WA Message","detail":"NLSAT AIOM Offline Reminder","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":40,"date":"2026-03-22","brand":"LE3","event":"AILSAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":41,"date":"2026-03-22","brand":"LE3","event":"NLSAT AIOM","detail":"All India Open Mock (Offline)","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":42,"date":"2026-03-27","brand":"LE3","event":"Webinar","detail":"One Month Strategy for NLSAT 2026","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":43,"date":"2026-03-29","brand":"LE3","event":"AILSAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":44,"date":"2026-03-31","brand":"LE3","event":"Mail","detail":"DU or BHU – Which is better?","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":45,"date":"2026-03-01","brand":"LEAC","event":"AISAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":46,"date":"2026-03-05","brand":"LEAC","event":"WA Message","detail":"Nurturing Messages","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":47,"date":"2026-03-06","brand":"LEAC","event":"Mail","detail":"Salary, Power & Growth: Govt Legal Jobs","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":48,"date":"2026-03-08","brand":"LEAC","event":"AISAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":49,"date":"2026-03-12","brand":"LEAC","event":"WA Message","detail":"Nurturing Messages","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":50,"date":"2026-03-13","brand":"LEAC","event":"WA Conv.","detail":"LLM One & LLM One Plus Awareness","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":51,"date":"2026-03-14","brand":"LEAC","event":"Webinar","detail":"UGC NET: 90 Days to Clear with Confidence","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":52,"date":"2026-03-15","brand":"LEAC","event":"AISAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":53,"date":"2026-03-16","brand":"LEAC","event":"Batch Launch","detail":"LLM One Batch","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":54,"date":"2026-03-16","brand":"LEAC","event":"Batch Launch","detail":"LLM One Plus Batch","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":55,"date":"2026-03-16","brand":"LEAC","event":"Batch Launch","detail":"Govt Law Officer Comprehensive Batch","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":56,"date":"2026-03-19","brand":"LEAC","event":"WA Message","detail":"Nurturing Messages","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":57,"date":"2026-03-22","brand":"LEAC","event":"AISAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":58,"date":"2026-03-26","brand":"LEAC","event":"WA Message","detail":"Nurturing Messages","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":59,"date":"2026-03-28","brand":"LEAC","event":"Webinar","detail":"CLAT & AILET PG: Strategic Judgment Workshop","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":60,"date":"2026-03-29","brand":"LEAC","event":"AISAT","detail":"Scholarship Test","wa":False,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":61,"date":"2026-03-31","brand":"LEAC","event":"Mail","detail":"CLAT PG 2027: Where Most Aspirants Go Wrong","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":62,"date":"2026-03-05","brand":"JG","event":"WA Message","detail":"Conversational Awareness – Working Professionals","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":63,"date":"2026-03-05","brand":"JG","event":"WA Message","detail":"Nurturing – College Students","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":64,"date":"2026-03-12","brand":"JG","event":"WA Message","detail":"Conversational Awareness – College Students","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":65,"date":"2026-03-14","brand":"JG","event":"WA Message","detail":"Nurturing (12th, 19th, 26th March)","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":66,"date":"2026-03-14","brand":"JG","event":"Webinar","detail":"Bihar APO: Preparation Strategy","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":67,"date":"2026-03-26","brand":"JG","event":"WA Message","detail":"Conversational Awareness – College Students","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":68,"date":"2026-03-28","brand":"JG","event":"WA Message","detail":"Reminder Messages for Webinar","wa":True,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":69,"date":"2026-03-28","brand":"JG","event":"Webinar","detail":"MP ADPO: Prep Strategy","wa":True,"sm":True,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":70,"date":"2026-03-04","brand":"JG","event":"Emailer","detail":"Nurturing Emailer 1","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":71,"date":"2026-03-11","brand":"JG","event":"Emailer","detail":"Nurturing Emailer 2","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":72,"date":"2026-03-18","brand":"JG","event":"Emailer","detail":"Nurturing Emailer 3","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
    {"id":73,"date":"2026-03-25","brand":"JG","event":"Emailer","detail":"Nurturing Emailer 4","wa":False,"sm":False,"status":"Pending","owner":"","flagged":False,"notes":""},
]

# ── GitHub I/O ────────────────────────────────────────────────────────────────
def gh_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def load_data():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return SEED_EVENTS[:]
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}?ref={GITHUB_BRANCH}"
    try:
        r = requests.get(url, headers=gh_headers(), timeout=10)
        if r.status_code == 200:
            content = base64.b64decode(r.json()["content"]).decode("utf-8")
            return json.loads(content)
        return SEED_EVENTS[:]
    except Exception:
        return SEED_EVENTS[:]

def save_data(events):
    st.session_state.last_save_time = time.time()  # guard against immediate re-fetch
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False, "No GitHub config — running in local mode."
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"
    content = base64.b64encode(json.dumps(events, indent=2).encode()).decode()
    # Get current SHA
    sha = None
    try:
        r = requests.get(url + f"?ref={GITHUB_BRANCH}", headers=gh_headers(), timeout=10)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception:
        pass
    payload = {
        "message": f"update: comms ops data {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": content,
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    try:
        r = requests.put(url, headers=gh_headers(), json=payload, timeout=15)
        if r.status_code in (200, 201):
            return True, "Saved & synced to GitHub ✓"
        return False, f"GitHub error: {r.status_code}"
    except Exception as e:
        return False, str(e)

# ── Helpers ───────────────────────────────────────────────────────────────────
TODAY = date.today()

def day_diff(d_str):
    d = date.fromisoformat(d_str)
    return (d - TODAY).days

def brand_label(b):
    return {"LE5":"LE-5","LE3":"LE-3","LEAC":"LEAC","JG":"JG"}.get(b, b)

def fmt_date(d_str):
    d = date.fromisoformat(d_str)
    return d.strftime("%A, %-d %B")

STATUS_OPTIONS = ["Pending", "In Progress", "Done", "Blocked"]
BRAND_OPTIONS  = ["LE5", "LE3", "LEAC", "JG"]
EVENT_OPTIONS  = ["Webinar","Batch Launch","Emailer","WA Message","AISAT","AILSAT","GSAT","Sale/Offer","Mail","Rapid Revision","WA Conv.","Other"]

# ── Load state ────────────────────────────────────────────────────────────────
if "save_msg" not in st.session_state:
    st.session_state.save_msg = ""
if "show_add" not in st.session_state:
    st.session_state.show_add = False
if "last_save_time" not in st.session_state:
    st.session_state.last_save_time = 0
if "events" not in st.session_state:
    st.session_state.events = []

# Only fetch from GitHub if it's been >10 seconds since our last save
# This prevents the auto-refresh from overwriting a save that just happened
seconds_since_save = time.time() - st.session_state.last_save_time
if seconds_since_save > 10:
    fresh = load_data()
    if fresh:
        st.session_state.events = fresh

events = st.session_state.events

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_btn = st.columns([6,1])
with col_title:
    st.markdown('<p class="main-title">Comms <span>Ops</span> Tracker</p>', unsafe_allow_html=True)
with col_btn:
    st.write("")
    if st.button("＋ Add event", use_container_width=True):
        st.session_state.show_add = not st.session_state.show_add

if st.session_state.save_msg:
    st.markdown(f'<p class="save-msg">{st.session_state.save_msg}</p>', unsafe_allow_html=True)

# ── Stats ─────────────────────────────────────────────────────────────────────
total    = len(events)
today_c  = sum(1 for e in events if day_diff(e["date"]) == 0)
urgent_c = sum(1 for e in events if 0 < day_diff(e["date"]) <= 3)
done_c   = sum(1 for e in events if e["status"] == "Done")
blocked_c= sum(1 for e in events if e["status"] == "Blocked")
flagged_c= sum(1 for e in events if e.get("flagged"))
unowned_c= sum(1 for e in events if not e.get("owner","").strip())

sc = st.columns(7)
cards = [
    ("Total", str(total), "num-ink"),
    ("Today", str(today_c), "num-orange"),
    ("Next 3 days", str(urgent_c), "num-red"),
    ("Done", str(done_c), "num-green"),
    ("Blocked", str(blocked_c), "num-red"),
    ("Flagged", str(flagged_c), "num-red"),
    ("Unassigned", str(unowned_c), "num-orange"),
]
for col, (label, val, cls) in zip(sc, cards):
    with col:
        st.markdown(f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-num {cls}">{val}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ── Add event form ────────────────────────────────────────────────────────────
if st.session_state.show_add:
    with st.expander("New event", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            nb = st.selectbox("Brand", BRAND_OPTIONS, key="nb")
            nd = st.date_input("Date", value=TODAY, key="nd")
        with fc2:
            ne = st.selectbox("Event type", EVENT_OPTIONS, key="ne")
            nst = st.selectbox("Status", STATUS_OPTIONS, key="nst")
        with fc3:
            ndt = st.text_input("Detail / Description", key="ndt")
            no  = st.text_input("Owner", key="no")
        fc4, fc5 = st.columns(2)
        with fc4:
            nwa = st.checkbox("WhatsApp", key="nwa")
            nsm = st.checkbox("Social Media", key="nsm")
        with fc5:
            nn = st.text_input("Notes", key="nn")
        if st.button("Save event", type="primary"):
            if not ndt.strip():
                st.error("Detail is required.")
            else:
                new_id = max((e["id"] for e in events), default=0) + 1
                events.append({
                    "id": new_id, "date": nd.isoformat(), "brand": nb,
                    "event": ne, "detail": ndt.strip(), "wa": nwa, "sm": nsm,
                    "status": nst, "owner": no.strip(), "flagged": False, "notes": nn.strip()
                })
                events.sort(key=lambda e: e["date"])
                ok, msg = save_data(events)
                st.session_state.save_msg = msg
                st.session_state.show_add = False
                st.rerun()

# ── Filters ───────────────────────────────────────────────────────────────────
f1, f2, f3, f4, f5 = st.columns([2,2,2,2,3])
with f1:
    brand_f = st.selectbox("Brand", ["All brands","LE-5","LE-3","LEAC","JG"], label_visibility="collapsed")
with f2:
    date_f = st.selectbox("Date range", ["All dates","Today","Next 3 days","This week","Upcoming","Past"], label_visibility="collapsed")
with f3:
    status_f = st.selectbox("Status", ["All statuses","Pending","In Progress","Done","Blocked"], label_visibility="collapsed")
with f4:
    flag_f = st.selectbox("Show", ["All rows","Flagged only","Unassigned only"], label_visibility="collapsed")
with f5:
    search_q = st.text_input("Search", placeholder="Search events…", label_visibility="collapsed")

# ── Filter logic ──────────────────────────────────────────────────────────────
brand_map = {"LE-5":"LE5","LE-3":"LE3","LEAC":"LEAC","JG":"JG"}

def passes(e):
    diff = day_diff(e["date"])
    if brand_f != "All brands" and e["brand"] != brand_map.get(brand_f, brand_f): return False
    if date_f == "Today" and diff != 0: return False
    if date_f == "Next 3 days" and not (0 <= diff <= 3): return False
    if date_f == "This week"   and not (0 <= diff <= 7): return False
    if date_f == "Upcoming"    and diff < 0: return False
    if date_f == "Past"        and diff >= 0: return False
    if status_f != "All statuses" and e["status"] != status_f: return False
    if flag_f == "Flagged only"   and not e.get("flagged"): return False
    if flag_f == "Unassigned only" and e.get("owner","").strip(): return False
    if search_q:
        q = search_q.lower()
        if not any(q in str(e.get(k,"")).lower() for k in ["detail","event","brand","owner","notes"]):
            return False
    return True

filtered = [e for e in events if passes(e)]

if not filtered:
    st.info("No events match the current filters.")
else:
    # Group by date
    from itertools import groupby
    filtered_sorted = sorted(filtered, key=lambda e: e["date"])
    groups = {k: list(v) for k, v in groupby(filtered_sorted, key=lambda e: e["date"])}

    for date_str, group in groups.items():
        diff = day_diff(date_str)
        is_today  = diff == 0
        is_urgent = 0 < diff <= 2
        is_past   = diff < 0

        label_cls = "day-today" if is_today else ("day-urgent" if is_urgent else ("day-past" if is_past else ""))
        badge = ""
        if is_today:  badge = '<span class="today-badge">today</span>'
        elif is_urgent: badge = '<span class="urgent-badge">soon</span>'

        st.markdown(
            f'<div class="day-header"><span class="{label_cls}">{fmt_date(date_str)}</span>{badge} '
            f'<span style="font-size:12px;color:#8a8a84;font-family:\'DM Mono\',monospace;margin-left:8px">{len(group)} event{"s" if len(group)>1 else ""}</span></div>',
            unsafe_allow_html=True
        )

        for ev in group:
            idx = next(i for i,e in enumerate(events) if e["id"] == ev["id"])
            bcls = f"brand-{ev['brand'].lower()}"
            brand_html = f'<span class="{bcls}">{brand_label(ev["brand"])}</span>'

            left_border = ""
            if is_today:  left_border = "border-left:3px solid #854F0B;padding-left:8px;"
            elif is_urgent: left_border = "border-left:3px solid #A32D2D;padding-left:8px;"

            with st.container():
                c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([1,1.2,2.5,1.8,1.5,0.7,0.7,1])
                with c1:
                    st.markdown(f'<div style="{left_border}margin-top:6px">{brand_html}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div style="font-size:12px;color:#4a4a46;margin-top:6px">{ev["event"]}</div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div style="font-size:12px;margin-top:6px">{ev["detail"]}</div>', unsafe_allow_html=True)
                with c4:
                    new_status = st.selectbox(
                        "status", STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(ev["status"]),
                        key=f"status_{ev['id']}",
                        label_visibility="collapsed"
                    )
                    if new_status != ev["status"]:
                        events[idx]["status"] = new_status
                        ok, msg = save_data(events)
                        st.session_state.save_msg = msg
                        st.rerun()
                with c5:
                    new_owner = st.text_input(
                        "owner", value=ev.get("owner",""),
                        placeholder="Assign…",
                        key=f"owner_{ev['id']}",
                        label_visibility="collapsed"
                    )
                    if new_owner != ev.get("owner",""):
                        events[idx]["owner"] = new_owner
                        ok, msg = save_data(events)
                        st.session_state.save_msg = msg
                        st.rerun()
                with c6:
                    st.markdown(f'<div style="font-size:12px;color:{"#3B6D11" if ev["wa"] else "#c8c4bc"};margin-top:6px;text-align:center">{"WA ✓" if ev["wa"] else "WA –"}</div>', unsafe_allow_html=True)
                with c7:
                    st.markdown(f'<div style="font-size:12px;color:{"#3B6D11" if ev["sm"] else "#c8c4bc"};margin-top:6px;text-align:center">{"SM ✓" if ev["sm"] else "SM –"}</div>', unsafe_allow_html=True)
                with c8:
                    flag_label = "🚩 Flagged" if ev.get("flagged") else "Flag"
                    if st.button(flag_label, key=f"flag_{ev['id']}", use_container_width=True):
                        events[idx]["flagged"] = not ev.get("flagged", False)
                        ok, msg = save_data(events)
                        st.session_state.save_msg = msg
                        st.rerun()

            with st.expander(f"Notes for: {ev['detail'][:40]}…" if len(ev['detail'])>40 else f"Notes: {ev['detail']}", expanded=False):
                new_notes = st.text_area("Notes", value=ev.get("notes",""), key=f"notes_{ev['id']}", label_visibility="collapsed", height=80)
                if st.button("Save notes", key=f"savenotes_{ev['id']}"):
                    events[idx]["notes"] = new_notes
                    ok, msg = save_data(events)
                    st.session_state.save_msg = msg
                    st.rerun()

        st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
fc1, fc2 = st.columns([4,1])
with fc1:
    st.markdown(f'<span style="font-size:11px;color:#8a8a84">Showing {len(filtered)} of {total} events · Today: {TODAY.strftime("%-d %B %Y")}</span>', unsafe_allow_html=True)
with fc2:
    if st.button("↻ Refresh data", use_container_width=True):
        st.session_state.events = load_data()
        st.rerun()
