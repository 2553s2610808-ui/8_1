import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

st.set_page_config(page_title="안심지하철", page_icon="🚇", layout="centered")

# 색상 및 화면 디자인
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700;800&display=swap');
html, body, [class*="css"] {font-family: 'Noto Sans KR', sans-serif;}
.stApp {background-color: #FBFAFF;}
[data-testid="stSidebar"] {background-color: #F0EBFF;}
.hero {
    background: linear-gradient(135deg, #7654D6, #A58BEF);
    padding: 28px; border-radius: 22px; color: white; margin-bottom: 18px;
}
.hero h1 {color: white; font-size: 30px;}
.hero p {color: white; font-size: 16px;}
div.stButton > button {
    background: #7654D6; color: white; border: none;
    border-radius: 13px; min-height: 50px; font-size: 17px;
    font-weight: 700; width: 100%;
}
div.stButton > button:hover {background: #6240C4; color: white;}
</style>
""", unsafe_allow_html=True)

STATIONS = [
    "서울역", "시청역", "종각역", "종로3가역", "동대문역",
    "왕십리역", "건대입구역", "잠실역", "강남역", "교대역",
    "고속터미널역", "홍대입구역", "신촌역", "여의도역", "영등포역"
]

# 화면 전환 및 입력값 저장
if "page" not in st.session_state:
    st.session_state.page = "메인 화면"
if "start_station" not in st.session_state:
    st.session_state.start_station = "서울역"
if "destination" not in st.session_state:
    st.session_state.destination = "강남역"
if "guardian_phone" not in st.session_state:
    st.session_state.guardian_phone = ""
if "travelling" not in st.session_state:
    st.session_state.travelling = False
if "arrived" not in st.session_state:
    st.session_state.arrived = False
if "sms_status" not in st.session_state:
    st.session_state.sms_status = ""

def move_to(page_name):
    st.session_state.page = page_name
    st.rerun()

def send_arrival_sms(phone_number, message):
    """Twilio Secrets가 설정되어 있으면 보호자에게 실제 문자를 보냅니다."""
    try:
        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        sender_number = st.secrets["TWILIO_PHONE_NUMBER"]
    except Exception:
        return False, "문자 발송 설정이 없습니다. 알림 내용을 복사해 보호자에게 직접 전달해 주세요."

    if not phone_number:
        return False, "보호자 전화번호를 입력해 주세요."

    try:
        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            + account_sid
            + "/Messages.json"
        )
        response = requests.post(
            url,
            data={
                "To": phone_number,
                "From": sender_number,
                "Body": message
            },
            auth=HTTPBasicAuth(account_sid, auth_token),
            timeout=15
        )
        if response.status_code in (200, 201):
            return True, "보호자에게 도착 문자를 보냈습니다."
        return False, "문자 발송에 실패했습니다. Twilio 설정과 전화번호를 확인해 주세요."
    except requests.RequestException:
        return False, "네트워크 오류로 문자를 보내지 못했습니다. 잠시 후 다시 시도해 주세요."
    except Exception:
        return False, "문자 발송 중 문제가 발생했습니다. 설정을 확인해 주세요."

# 사이드바 메뉴
with st.sidebar:
    st.markdown("## 🚇 안심지하철")
    st.write("안전한 지하철 이동을 도와드려요.")
    st.divider()
    menu_items = ["메인 화면", "목적지 설정", "탑승 중", "도착 완료", "보호자 알림"]
    selected_page = st.radio(
        "화면 선택",
        menu_items,
        index=menu_items.index(st.session_state.page),
        label_visibility="collapsed"
    )
    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.rerun()

page = st.session_state.page

# 1. 메인 화면
if page == "메인 화면":
    st.markdown("""
    <div class="hero">
        <h1>안심지하철 🚇</h1>
        <p>목적지까지 편안하게 이동하고<br>도착 소식을 보호자에게 알려드려요.</p>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("오늘도 안전하게 이동해요")
    st.info("출발역과 도착역, 보호자 연락처를 설정한 뒤 이용해 주세요.")
    st.markdown("### 이용 방법")
    st.write("① 목적지 설정")
    st.write("② 지하철 이동")
    st.write("③ 도착 확인")
    st.write("④ 보호자에게 알림 보내기")
    if st.button("🚆 지하철 타기 시작하기"):
        move_to("목적지 설정")

# 2. 목적지 설정
elif page == "목적지 설정":
    st.subheader("📍 목적지를 설정해 주세요")
    start = st.selectbox(
        "출발역",
        STATIONS,
        index=STATIONS.index(st.session_state.start_station)
    )
    destination = st.selectbox(
        "도착역",
        STATIONS,
        index=STATIONS.index(st.session_state.destination)
    )
    phone = st.text_input(
        "보호자 전화번호",
        value=st.session_state.guardian_phone,
        placeholder="+821012345678"
    )

    if st.button("선택 완료하고 이동하기"):
        if start == destination:
            st.error("출발역과 도착역을 다르게 선택해 주세요.")
        else:
            st.session_state.start_station = start
            st.session_state.destination = destination
            st.session_state.guardian_phone = phone.strip()
            st.session_state.travelling = True
            st.session_state.arrived = False
            st.session_state.sms_status = ""
            move_to("탑승 중")

# 3. 탑승 중
elif page == "탑승 중":
    st.subheader("🚉 안전하게 이동하세요")
    if not st.session_state.travelling:
        st.info("먼저 목적지를 설정해 주세요.")
        if st.button("목적지 설정하기"):
            move_to("목적지 설정")
    else:
        st.markdown("### 현재 이동 경로")
        st.success("출발역: " + st.session_state.start_station)
        st.markdown("⬇️")
        st.info("도착역: " + st.session_state.destination)
        st.progress(0.6, text="이동 상태 예시")
        st.warning("실제 열차 위치를 자동 추적하는 기능은 아닙니다. 도착한 뒤 버튼을 눌러 주세요.")
        if st.button("✅ 목적지에 도착했어요"):
            st.session_state.travelling = False
            st.session_state.arrived = True
            move_to("도착 완료")

# 4. 도착 완료
elif page == "도착 완료":
    st.subheader("🎉 목적지에 도착하셨나요?")
    if st.session_state.arrived:
        st.markdown("""
        <div class="hero" style="text-align:center;">
            <h1>도착을 확인했어요!</h1>
            <p>안전하게 이동을 마쳤습니다.</p>
        </div>
        """, unsafe_allow_html=True)
        st.success(
            st.session_state.destination
            + " 도착 확인 · "
            + datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        if st.button("보호자 알림 화면으로 이동"):
            move_to("보호자 알림")
    else:
        st.info("먼저 탑승 중 화면에서 도착 확인을 해 주세요.")
        if st.button("탑승 중 화면으로 이동"):
            move_to("탑승 중")

# 5. 보호자 알림
elif page == "보호자 알림":
    st.subheader("💌 보호자에게 도착 알림")
    if not st.session_state.arrived:
        st.info("도착 확인을 먼저 해 주세요.")
    else:
        phone = st.text_input(
            "보호자 전화번호",
            value=st.session_state.guardian_phone,
            placeholder="+821012345678",
            key="guardian_phone_alert"
        )
        message = (
            "[안심지하철] 탑승자가 목적지에 도착했습니다. "
            + "출발역: " + st.session_state.start_station
            + ", 도착역: " + st.session_state.destination
            + ", 확인 시각: " + datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        st.markdown("### 전송할 알림 내용")
        st.code(message)

        if st.button("📩 보호자에게 문자 보내기"):
            st.session_state.guardian_phone = phone.strip()
            success, result_message = send_arrival_sms(phone.strip(), message)
            st.session_state.sms_status = result_message
            if success:
                st.success(result_message)
            else:
                st.warning(result_message)

        if st.session_state.sms_status:
            st.caption(st.session_state.sms_status)

        st.caption("실제 문자 발송을 위해서는 Twilio 계정과 Secrets 설정이 필요합니다.")

st.divider()
st.caption("안심지하철 | 안전한 이동을 위한 도우미")
