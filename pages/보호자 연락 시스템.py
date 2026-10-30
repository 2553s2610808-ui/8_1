import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

# -------------------------------------------------
# 기본 설정
# -------------------------------------------------
st.set_page_config(
    page_title="안심지하철",
    page_icon="🚇",
    layout="centered",
    initial_sidebar_state="expanded",
)

PURPLE = "#7654D6"
LIGHT_PURPLE = "#F2EEFF"
DARK = "#29213D"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Noto Sans KR', sans-serif;
    }}
    .stApp {{ background: #FBFAFF; color: {DARK}; }}
    [data-testid="stSidebar"] {{ background: #F1ECFF; }}
    [data-testid="stSidebar"] * {{ color: {DARK}; }}
    .hero {{
        background: linear-gradient(135deg, #7654D6, #A58BEF);
        padding: 28px 24px; border-radius: 22px; color: white;
        margin-bottom: 18px;
    }}
    .hero h1 {{ color: white; font-size: 30px; margin: 0 0 8px 0; }}
    .hero p {{ color: white; font-size: 16px; margin: 0; }}
    .panel {{
        background: white; border: 1px solid #E6DFFF; border-radius: 18px;
        padding: 20px; margin: 12px 0;
    }}
    .step {{
        display: inline-block; background: #EDE6FF; color: #6342C4;
        padding: 6px 12px; border-radius: 30px; font-size: 13px;
        font-weight: 700; margin-bottom: 8px;
    }}
    .big-text {{ font-size: 22px; font-weight: 800; }}
    div.stButton > button {{
        background: {PURPLE}; color: white; border: 0; border-radius: 13px;
        min-height: 52px; font-size: 17px; font-weight: 700; width: 100%;
    }}
    div.stButton > button:hover {{ background: #6240C4; color: white; border: 0; }}
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] div,
    div[data-testid="stTextArea"] textarea {{
        border-radius: 10px;
    }}
    .muted {{ color: #6E687A; font-size: 14px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# 세션 상태
# -------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "메인 화면"
if "destination" not in st.session_state:
    st.session_state.destination = "강남역"
if "start_station" not in st.session_state:
    st.session_state.start_station = "서울역"
if "guardian_phone" not in st.session_state:
    st.session_state.guardian_phone = ""
if "travelling" not in st.session_state:
    st.session_state.travelling = False
if "arrived" not in st.session_state:
    st.session_state.arrived = False
if "last_message" not in st.session_state:
    st.session_state.last_message = ""
if "sms_result" not in st.session_state:
    st.session_state.sms_result = ""

STATIONS = [
    "서울역", "시청역", "종각역", "종로3가역", "동대문역",
    "왕십리역", "건대입구역", "잠실역", "강남역", "교대역",
    "고속터미널역", "홍대입구역", "신촌역", "여의도역", "영등포역",
]

def go(page):
    st.session_state.page = page
    st.rerun()

def send_sms(phone, message):
    """Twilio 설정이 있을 때 실제 문자 발송. 설정이 없으면 안내 메시지를 반환."""
    try:
        sid = st.secrets.get("TWILIO_ACCOUNT_SID", "")
