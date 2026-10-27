    if st.button("← 메인 화면", use_container_width=True):
        go("home")
        st.rerun()

elif st.session_state.page == "riding":
    header("3단계 · 이동 중", "안전하게 이동하세요")

    # 입력한 역 이름을 HTML에 직접 넣지 않고 Streamlit 텍스트로 표시해 안전하게 처리
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("**🚉 출발역**")
    st.subheader(st.session_state.start)
    st.markdown("**↓**")
    st.markdown("**📍 도착역**")
    st.subheader(st.session_state.destination)
    st.markdown(f"**교통수단:** {st.session_state.transport}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.info("현재 위치는 자동으로 추적되지 않아요. 실제 상황에 맞게 아래 버튼을 눌러 주세요.")

    if st.button("🚆 이동 중이에요", type="primary", use_container_width=True):
        st.session_state.status = "이동 중"
        st.success("이동 상태가 업데이트되었어요.")

    if st.button("✅ 목적지에 도착했어요", use_container_width=True):
        st.session_state.status = "목적지 도착"
        go("arrived")
        st.rerun()

    if st.button("← 목적지 다시 설정", use_container_width=True):
        go("destination")
        st.rerun()

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
    st.write(f"**도착역:** {st.session_state.destination}")

    if st.button("📨 보호자에게 도착 알리기", type="primary", use_container_width=True):
        go("notify")
        st.rerun()

    if st.button("← 이동 화면으로", use_container_width=True):
        go("riding")
        st.rerun()

elif st.session_state.page == "guardian":
    header("보호자 설정", "보호자 정보를 입력하세요")

    with st.form("guardian_form"):
        guardian = st.text_input(
            "보호자 이름",
            value=st.session_state.guardian,
            placeholder="예: 아들",
        )
        phone = st.text_input(
            "보호자 휴대전화 번호",
            value=st.session_state.phone,
            placeholder="예: 01012345678",
        )
        save_guardian = st.form_submit_button(
            "보호자 정보 저장", type="primary", use_container_width=True
        )

    if save_guardian:
        digits = "".join(c for c in phone if c.isdigit())
        if not guardian.strip():
            st.error("보호자 이름을 입력해 주세요.")
        elif not 9 <= len(digits) <= 15:
            st.error("휴대전화 번호를 확인해 주세요.")
        else:
            st.session_state.guardian = guardian.strip()
            st.session_state.phone = phone.strip()
            st.success("보호자 정보가 저장되었어요.")

    if st.button("← 메인 화면", use_container_width=True):
        go("home")
        st.rerun()

elif st.session_state.page == "notify":
    header("5단계 · 보호자 알림", "도착 소식을 전해요")

    destination = st.session_state.destination
    guardian = st.session_state.guardian or "보호자"
    message = f"[안심지하철] {destination}에 도착했습니다. 안심하세요!"

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

    digits = "".join(c for c in st.session_state.phone if c.isdigit())

    if digits:
        sms_url = f"sms:{digits}?body={quote(message)}"
        st.link_button("💬 문자 앱 열기", sms_url, use_container_width=True)
        st.caption("문자 앱에서 직접 전송 버튼을 눌러야 알림이 전달돼요.")
    else:
        st.warning("보호자 연락처가 등록되지 않았어요. 먼저 보호자 정보를 설정해 주세요.")
        if st.button("보호자 정보 설정", use_container_width=True):
            go("guardian")
            st.rerun()

    if st.button("🏠 처음 화면으로", type="primary", use_container_width=True):
        go("home")
        st.rerun()

st.divider()
st.caption("안심지하철 | 현재 버전은 실제 GPS 추적 및 자동 문자 발송을 지원하지 않습니다.")
