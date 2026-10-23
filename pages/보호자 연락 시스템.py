
import streamlit as st
from datetime import datetime
from urllib.parse import quote
import re

st.set_page_config(
    page_title="안심지하철",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- 디자인 ----------
st.markdown("""
<style>
.stApp {
    background: #F4F8FF;
    color: #17345C;
}
.block-container {
    max-width: 1100px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}
h1, h2, h3 {
    color: #17345C !important;
}
.hero {
    background: linear-gradient(135deg, #E4F0FF, #FFFFFF);
    border: 1px solid #D4E5FF;
    border-radius: 24px;
    padding: 28px;
    text-align: center;
}
.hero-icon {
    font-size: 64px;
}
.card {
    background: white;
    border: 1px solid #D9E7FB;
    border-radius: 18px;
    padding: 20px;
    margin: 8px 0;
}
.station {
    background: white;
    border: 1px solid #D9E7FB;
    border-radius: 14px;
    padding: 13px;
    margin: 8px 0;
}
.small-muted {
    color: #60748E;
    font-size: 14px;
}
.success-panel {
    background: #E8FAF3;
    border: 1px solid #B9ECDD;
    border-radius: 20px;
    text-align: center;
    padding: 30px 15px;
}
.success-icon {
    font-size: 66px;
}
div.stButton > button,
div.stLinkButton > a {
    border-radius: 14px;
    min-height: 48px;
    font-size: 17px;
    font-weight: 650;
}
div[data-testid="stFormSubmitButton"] button {
    min-height: 48px;
    border-radius: 14px;
    font-size: 17px;
}
[data-testid="stProgressBar"] > div > div {
    background-color: #4387F5;
}
</style>
""", unsafe_allow_html=True)

# ---------- 초기 상태 ----------
if "page" not in st.session_state:
    st.session_state.page = 0
if "trip" not in st.session_state:
    st.session_state.trip = None
if "history" not in st.session_state:
    st.session_state.history = []
if "start_time" not in st.session_state:
    st.session_state.start_time = ""
if "arrival_time" not in st.session_state:
    st.session_state.arrival_time = ""
if "notice" not in st.session_state:
    st.session_state.notice = ""
if "selected_destination" not in st.session_state:
    st.session_state.selected_destination = "강남역"

pages = [
    "메인 화면",
    "목적지 설정",
    "탑승 중",
    "도착 완료",
    "보호자 알림",
]

destinations = [
    "강남역",
    "서울역",
    "잠실역",
    "홍대입구역",
    "종로3가역",
    "병원",
    "기타",
]


def record(text):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.session_state.history.insert(0, f"{now} · {text}")


def create_notice(kind):
    trip = st.session_state.trip
    if not trip:
        return ""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if kind == "도착":
        detail = f"목적지 {trip['destination']}에 도착했습니다."
        heading = "[안심지하철 도착 알림]"
    elif kind == "도움":
        detail = (
            f"{trip['destination']}으로 이동 중 도움이 필요합니다. "
            "전화로 확인해 주세요."
        )
        heading = "[안심지하철 도움 요청]"
    else:
        detail = f"{trip['destination']}으로 이동을 시작했습니다."
        heading = "[안심지하철 이동 알림]"

    return (
        f"{heading}\n"
        f"이용자: {trip['name']}\n"
        f"보호자: {trip['guardian'] or '미입력'}\n"
        f"내용: {detail}\n"
        f"이동 수단: 지하철\n"
        f"확인 시간: {now}\n"
        "※ 버튼을 누른 시각이며 GPS로 확인한 위치가 아닙니다."
    )


def change_page(number):
    st.session_state.page = number


# ---------- 상단 제목 ----------
st.markdown(
    "<div style='text-align:center;font-size:15px;color:#54739C'>"
    "어르신의 안전한 지하철 이용 도우미</div>",
    unsafe_allow_html=True,
)
st.title("🚇 안심지하철")
st.caption("목적지에 도착하면 보호자에게 알릴 수 있어요.")

# ---------- 5단계 메뉴 ----------
selected_page = st.radio(
    "앱 화면",
    pages,
    index=st.session_state.page,
    horizontal=True,
    label_visibility="collapsed",
    key="page_selector",
)
st.session_state.page = pages.index(selected_page)

st.progress((st.session_state.page + 1) / len(pages))
st.caption(f"{st.session_state.page + 1} / 5 단계")

st.divider()

# ---------- 1. 메인 화면 ----------
if st.session_state.page == 0:
    st.markdown("""
    <div class="hero">
        <div class="hero-icon">🚇</div>
        <h2>안심지하철</h2>
        <p>노약자의 안전한 지하철 이용,<br>
        가족과 함께 안심하고 이동하세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.subheader("어디로 이동하시나요?")

    if st.session_state.trip:
        st.markdown(
            f"""<div class="card">
            📍 최근 목적지<br><br>
            <strong>{st.session_state.trip['destination']}</strong>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<div class="card">
            👋 안녕하세요!<br><br>
            목적지를 선택하고 안전한 이동을 시작해 보세요.
            </div>""",
            unsafe_allow_html=True,
        )

    if st.button("🚇 지하철 타기  →", type="primary",
                 use_container_width=True):
        change_page(1)
        st.rerun()

    st.subheader("이용 안내")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📍")
        st.write("목적지 설정")
    with col2:
        st.markdown("### 🚇")
        st.write("이동 상태 확인")
    with col3:
        st.markdown("### 🔔")
        st.write("보호자 알림")

# ---------- 2. 목적지 설정 ----------
elif st.session_state.page == 1:
    st.header("📍 목적지 설정")
    st.write("도착할 역을 선택해 주세요.")

    with st.form("destination_form"):
        name = st.text_input(
            "어르신 성함",
            value=st.session_state.trip["name"]
            if st.session_state.trip else "",
            max_chars=40,
        )
        guardian = st.text_input(
            "보호자 성함",
            value=st.session_state.trip["guardian"]
            if st.session_state.trip else "",
            max_chars=40,
        )
        phone = st.text_input(
            "보호자 전화번호",
            value=st.session_state.trip["phone"]
            if st.session_state.trip else "",
            placeholder="01012345678",
            max_chars=20,
        )
        origin = st.text_input(
            "출발역",
            value=st.session_state.trip["origin"]
            if st.session_state.trip else "",
            placeholder="예: 서울역",
        )
        destination = st.selectbox(
            "도착역",
            destinations,
            index=destinations.index(
                st.session_state.selected_destination
            ),
        )
        if destination == "기타":
            custom_destination = st.text_input(
                "목적지 직접 입력",
                placeholder="역 또는 장소 이름",
            )
        else:
            custom_destination = ""

        submitted = st.form_submit_button(
            "선택 완료 →",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            final_destination = (
                custom_destination.strip()
                if destination == "기타"
                else destination
            )
            digits = re.sub(r"\D", "", phone)

            if not name.strip() or not final_destination:
                st.error("성함과 목적지를 입력해 주세요.")
            elif phone.strip() and not 8 <= len(digits) <= 15:
                st.error("보호자 전화번호를 확인해 주세요.")
            else:
                st.session_state.trip = {
                    "name": name.strip(),
                    "guardian": guardian.strip(),
                    "phone": phone.strip(),
                    "origin": origin.strip() or "출발역 미입력",
                    "destination": final_destination,
                }
                st.session_state.selected_destination = destination
                st.session_state.start_time = ""
                st.session_state.arrival_time = ""
                st.session_state.notice = ""
                record(f"목적지 설정: {final_destination}")
                change_page(2)
                st.rerun()

    st.info("보호자 전화번호는 문자 앱을 열 때 사용합니다.")

# ---------- 3. 탑승 중 ----------
elif st.session_state.page == 2:
    st.header("🚇 이동 중")

    if not st.session_state.trip:
        st.warning("먼저 목적지를 설정해 주세요.")
        if st.button("목적지 설정으로 이동"):
            change_page(1)
            st.rerun()
    else:
        trip = st.session_state.trip
        st.markdown(
            f"""<div class="card">
            <span style="color:#4387F5;font-weight:bold">● 이동 경로</span>
            <h3>🚉 {trip['origin']}</h3>
            <p style="color:#4387F5">│</p>
            <p>🔵 현재 상태: { 
                '이동 중' if st.session_state.start_time
                else '탑승 준비'
            }</p>
            <p style="color:#4387F5">│</p>
            <h3>○ {trip['destination']}</h3>
            </div>""",
            unsafe_allow_html=True,
        )

        if st.session_state.start_time:
            st.success(
                f"이동 시작 시간: {st.session_state.start_time}"
            )
            st.info(
                "안전하게 이동하세요. 실제 현재 위치와 "
                "열차 위치를 추적하는 기능은 포함되어 있지 않습니다."
            )
        else:
            st.write("이동을 시작하면 시작 시간이 기록됩니다.")
            if st.button("🚇 지금 이동 시작", type="primary",
                         use_container_width=True):
                st.session_state.start_time = datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
                st.session_state.notice = create_notice("이동")
                record("이동 시작")
                st.rerun()

        if st.button("✅ 목적지에 도착했어요",
                     type="primary", use_container_width=True):
            if not st.session_state.start_time:
                st.warning("먼저 이동 시작 버튼을 눌러 주세요.")
            else:
                st.session_state.arrival_time = datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
                st.session_state.notice = create_notice("도착")
                record(f"{trip['destination']} 도착 확인")
                change_page(3)
                st.rerun()

        if st.button("🆘 도움이 필요해요",
                     use_container_width=True):
            st.session_state.notice = create_notice("도움")
            record("도움 요청")
            change_page(4)
            st.rerun()

# ---------- 4. 도착 완료 ----------
elif st.session_state.page == 3:
    st.header("도착 확인")

    if not st.session_state.trip:
        st.warning("먼저 목적지를 설정해 주세요.")
        if st.button("목적지 설정"):
            change_page(1)
            st.rerun()
    elif not st.session_state.arrival_time:
        st.info("이동 중 화면에서 도착 버튼을 눌러 주세요.")
        if st.button("이동 중 화면으로"):
            change_page(2)
            st.rerun()
    else:
        trip = st.session_state.trip
        st.markdown(f"""
        <div class="success-panel">
            <div class="success-icon">✅</div>
            <h2>목적지에 도착했어요!</h2>
            <p><strong>{trip['destination']}</strong></p>
            <p>안전하게 이동하셨습니다.</p>
            <p>보호자에게 알림을 보낼 수 있어요.</p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.markdown(
            f"""<div class="card">
            👤 이용자: {trip['name']}<br><br>
            🕒 도착 확인: {st.session_state.arrival_time}<br><br>
            🔔 보호자: {trip['guardian'] or '미입력'}
            </div>""",
            unsafe_allow_html=True,
        )

        st.warning(
            "도착은 버튼을 누른 것으로 기록됩니다. "
            "GPS가 자동으로 도착을 확인한 것은 아닙니다."
        )

        if st.button("🔔 보호자에게 알리기 →",
                     type="primary", use_container_width=True):
            st.session_state.notice = create_notice("도착")
            change_page(4)
            st.rerun()

# ---------- 5. 보호자 알림 ----------
elif st.session_state.page == 4:
    st.header("🔔 보호자 알림")

    if not st.session_state.trip:
        st.warning("먼저 목적지를 설정해 주세요.")
        if st.button("목적지 설정으로"):
            change_page(1)
            st.rerun()
    else:
        trip = st.session_state.trip

        if not st.session_state.notice:
            st.session_state.notice = create_notice(
                "도움" if st.session_state.history
                and "도움 요청" in st.session_state.history[0]
                else "도착"
            )

        st.markdown(
            """<div class="card">
            <h3>📱 보호자에게 전달할 메시지</h3>
            내용을 확인한 뒤 문자 앱에서 전송해 주세요.
            </div>""",
            unsafe_allow_html=True,
        )

        st.text_area(
            "알림 내용",
            value=st.session_state.notice,
            height=220,
            key="notice_preview",
        )

        phone = re.sub(r"\s+", "", trip["phone"])
        if phone:
            sms_url = (
                f"sms:{quote(phone, safe='+')}"
                f"?body={quote(st.session_state.notice)}"
            )
            st.link_button(
                "📨 문자 앱 열기",
                sms_url,
                use_container_width=True,
            )
        else:
            st.warning(
                "보호자 전화번호가 등록되지 않았어요. "
                "문자 앱을 열려면 목적지 설정에서 번호를 입력해 주세요."
            )

        st.info(
            "문자 앱이 열려도 자동 전송되지는 않습니다. "
            "문자 내용을 확인하고 직접 보내 주세요."
        )

        st.subheader("최근 이동 기록")
        if st.session_state.history:
            for item in st.session_state.history[:10]:
                st.write("• " + item)
        else:
            st.write("기록이 없습니다.")

        if st.button("🏠 처음 화면으로",
                     type="primary", use_container_width=True):
            change_page(0)
            st.rerun()

st.divider()
st.caption(
    "안심지하철 | 이동을 돕는 시범 앱 · 실제 GPS 추적 및 자동 문자 발송 미지원"
)
