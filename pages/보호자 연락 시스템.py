
import streamlit as st
from urllib.parse import quote

st.set_page_config(
    page_title="안심지하철",
    page_icon="🚇",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 상태 저장
defaults = {
    "page": "home",
    "start": "서울역",
    "destination": "",
    "transport": "지하철",
    "guardian": "",
    "phone": "",
    "status": "이동 준비",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 디자인
st.markdown("""
<style>
.stApp {
    background: #F5F8FE;
}
.block-container {
    max-width: 650px;
    padding: 1.5rem 1rem 3rem;
}
h1, h2, h3 {
    color: #173B70;
}
.hero {
    background: linear-gradient(135deg, #E4F0FF, #FFFFFF);
    border: 1px solid #D8E7FF;
    border-radius: 22px;
    padding: 24px 20px;
    text-align: center;
    margin-bottom: 18px;
}
.hero-icon {
    font-size: 54px;
}
.hero-title {
    font-size: 27px;
    font-weight: 800;
    color: #174A91;
}
.hero-desc {
    font-size: 17px;
    line-height: 1.7;
    color: #344B68;
}
.info-card {
    background: white;
    border: 1px solid #DCE7F6;
    border-radius: 16px;
    padding: 18px;
    margin: 10px 0;
}
.step {
    background: #E0ECFF;
    color: #194D98;
    border-radius: 30px;
    padding: 9px;
    text-align: center;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 16px;
}
.big-success {
    background: #E5FAF2;
    border: 1px solid #B8EBD8;
    border-radius: 22px;
    text-align: center;
    padding: 28px 15px;
}
.success-icon {
    font-size: 65px;
}
div.stButton > button,
div.stLinkButton > a {
    min-height: 52px;
    border-radius: 14px;
    font-size: 17px;
    font-weight: 700;
}
div.stButton > button[kind="primary"] {
    background: #367CF5;
    border-color: #367CF5;
}
label, .stMarkdown, .stCaption {
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)


def go(page):
    st.session_state.page = page


def header(step, title):
    st.markdown(
        f'<div class="step">{step}</div>',
        unsafe_allow_html=True
    )
    st.title(title)


# 1. 메인 화면
if st.session_state.page == "home":
    st.markdown("""
    <div class="hero">
        <div class="hero-icon">🚇</div>
        <div class="hero-title">안심지하철</div>
        <div class="hero-desc">
            대중교통 이용이 어려운 어르신도<br>
            목적지까지 안심하고 이동하세요.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <b>👣 간편한 이용 방법</b><br><br>
        ① 목적지를 선택해요.<br>
        ② 이동 상태를 확인해요.<br>
        ③ 도착하면 보호자에게 알려요.
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚇 지하철 타기 시작", type="primary",
                 use_container_width=True):
        go("destination")
        st.rerun()

    if st.button("👨‍👩‍👧 보호자 정보 설정",
                 use_container_width=True):
        go("guardian")
        st.rerun()


# 2. 목적지 설정
elif st.session_state.page == "destination":
    header("2단계 · 목적지 설정", "어디까지 가시나요?")

    with st.form("route_form"):
        start = st.text_input(
            "출발역",
            value=st.session_state.start
        )
        destination = st.text_input(
            "도착역",
            value=st.session_state.destination,
            placeholder="예: 강남역"
        )
        transport = st.selectbox(
            "이용할 교통수단",
            ["지하철", "버스", "지하철 + 버스"],
            index=[
                "지하철", "버스", "지하철 + 버스"
            ].index(st.session_state.transport)
        )
        save = st.form_submit_button(
            "목적지 선택 완료",
            type="primary",
            use_container_width=True
        )

    if save:
        if not start.strip() or not destination.strip():
            st.error("출발역과 도착역을 입력해 주세요.")
        elif start.strip() == destination.strip():
            st.error("출발역과 도착역이 같아요. 다시 확인해 주세요.")
        else:
            st.session_state.start = start.strip()
            st.session_state.destination = destination.strip()
            st.session_state.transport = transport
            st.session_state.status = "이동 준비"
            go("riding")
            st.rerun()

    st.caption("※ 이 버전은 역 이름을 입력받으며 실제 노선 검색 기능은 포함하지 않아요.")

    if st.button("← 메인 화면", use_container_width=True):
        go("home")
        st.rerun()


# 3. 탑승 및 이동 상태
elif st.session_state.page == "riding":
    header("3단계 · 이동 중", "안전하게 이동하세요")

    st.markdown(f"""
    <div class="info-card">
        <div style="color:#60758F">🚉 출발역</div>
        <h3>{st.session_state.start}</h3>
        <div style="font-size:26px;color:#367CF5">↓</div>
        <div style="color:#60758F">📍 도착역</div>
        <h3>{st.session_state.destination}</h3>
        <hr>
        <b>교통수단:</b> {st.session_state.transport}
    </div>
    """, unsafe_allow_html=True)

    st.info("현재 위치는 자동으로 추적되지 않아요. 실제 상황에 맞게 아래 버튼을 눌러 주세요.")

    if st.button("🚆 이동 중이에요", type="primary",
                 use_container_width=True):
        st.session_state.status = "이동 중"
        st.success("이동 상태가 업데이트되었어요.")

    if st.button("✅ 목적지에 도착했어요",
                 use_container_width=True):
        st.session_state.status = "목적지 도착"
        go("arrived")
        st.rerun()

    if st.button("← 목적지 다시 설정",
                 use_container_width=True):
        go("destination")
        st.rerun()


# 4. 도착 완료
elif st.session_state.page == "arrived":
    header("4단계 · 도착 완료", "목적지에 도착했어요!")

    st.markdown("""
    <div class="big-success">
        <div class="success-icon">✅</div>
        <h2>안전하게 도착하셨나요?</h2>
        <p>도착 확인이 완료되면<br>
        보호자에게 알림을 보낼 수 있어요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.markdown(
        f"**도착역:** {st.session_state.destination}"
    )

    if st.button("📨 보호자에게 도착 알리기",
                 type="primary", use_container_width=True):
        go("notify")
        st.rerun()

    if st.button("← 이동 화면으로",
                 use_container_width=True):
        go("riding")
        st.rerun()


# 보호자 정보 설정
elif st.session_state.page == "guardian":
    header("보호자 설정", "보호자 정보를 입력하세요")

    with st.form("guardian_form"):
        guardian = st.text_input(
            "보호자 이름",
            value=st.session_state.guardian,
            placeholder="예: 아들"
        )
        phone = st.text_input(
            "보호자 휴대전화 번호",
            value=st.session_state.phone,
            placeholder="예: 01012345678"
        )
        save_guardian = st.form_submit_button(
            "보호자 정보 저장",
            type="primary",
            use_container_width=True
        )

    if save_guardian:
        digits = "".join(c for c in phone if c.isdigit())

        if not guardian.strip():
            st.error("보호자 이름을 입력해 주세요.")
        elif not digits or len(digits) < 9 or len(digits) > 15:
            st.error("휴대전화 번호를 확인해 주세요.")
        else:
            st.session_state.guardian = guardian.strip()
            st.session_state.phone = phone.strip()
            st.success("보호자 정보가 저장되었어요.")

    if st.button("← 메인 화면", use_container_width=True):
        go("home")
        st.rerun()


# 5. 보호자 알림
elif st.session_state.page == "notify":
    header("5단계 · 보호자 알림", "도착 소식을 전해요")

    destination = st.session_state.destination
    guardian = st.session_state.guardian or "보호자"

    message = (
        f"[안심지하철] {destination}에 도착했습니다. "
        "안심하세요!"
    )

    st.markdown("""
    <div class="big-success">
        <div class="success-icon">📱</div>
        <h2>도착 알림 준비 완료</h2>
        <p>아래 내용을 확인하고 보호자에게 알려 주세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.write(f"**받는 분:** {guardian}")
    st.text_area("전송할 메시지", value=message, disabled=True)

    digits = "".join(
        c for c in st.session_state.phone if c.isdigit()
    )

    if digits:
        sms_url = f"sms:{digits}?body={quote(message)}"
        st.link_button(
            "💬 문자 앱 열기",
            sms_url,
            use_container_width=True
        )
        st.caption("문자 앱에서 직접 전송 버튼을 눌러야 알림이 전달돼요.")
    else:
        st.warning(
            "보호자 연락처가 등록되지 않았어요. "
            "메시지를 복사해 직접 전달하거나 보호자 정보를 설정해 주세요."
        )

        if st.button("보호자 정보 설정",
                     use_container_width=True):
            go("guardian")
            st.rerun()

    if st.button("🏠 처음 화면으로",
                 type="primary", use_container_width=True):
        go("home")
        st.rerun()

st.divider()
st.caption(
    "안심지하철 | 현재 버전은 실제 GPS 추적 및 자동 문자 발송을 지원하지 않습니다."
)
