      </button>
      <button onclick="stopRoute()" style="
        width:110px; height:52px; border:1px solid #BFDBFE;
        border-radius:12px; background:#EFF6FF; color:#1E3A8A;
        font-size:14px; font-weight:700; cursor:pointer;">
        ■ 중지
      </button>
    </div>
    <script>
      const routeText = {text_json};

      function getSpeechObjects() {{
        let synth = window.speechSynthesis;
        let Utterance = window.SpeechSynthesisUtterance;

        try {{
          if (window.parent && window.parent.speechSynthesis) {{
            synth = window.parent.speechSynthesis;
            Utterance = window.parent.SpeechSynthesisUtterance || Utterance;
          }}
        }} catch (error) {{}}

        return {{ synth, Utterance }};
      }}

      function speakRoute() {{
        const objects = getSpeechObjects();
        if (!objects.synth || !objects.Utterance) {{
          alert('이 브라우저에서는 음성 안내를 지원하지 않습니다.');
          return;
        }}

        objects.synth.cancel();
        const utterance = new objects.Utterance(routeText);
        utterance.lang = 'ko-KR';
        utterance.rate = 0.88;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        objects.synth.speak(utterance);
      }}

      function stopRoute() {{
        const objects = getSpeechObjects();
        if (objects.synth) objects.synth.cancel();
      }}
    </script>
    """


# =========================================================
# 앱 화면
# =========================================================
st.markdown(
    """
    <div class="hero">
      <div class="hero-title">🚇 BLUE ROUTE</div>
      <div class="hero-subtitle">
        출발역과 도착역을 입력하면 지하철 이동 경로를 안내합니다.<br>
        비슷한 역 검색이나 자동 추천 없이 입력한 역 이름만 정확히 확인합니다.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    with st.spinner("지하철 정보를 불러오는 중..."):
        역정보, 그래프, 역검색표 = 데이터불러오기()
except Exception as error:
    st.error("지하철 데이터를 불러오지 못했어. 잠시 후 다시 실행해 줘.")
    st.caption(f"오류 내용: {error}")
    st.stop()

if "route_result" not in st.session_state:
    st.session_state.route_result = None
if "route_error" not in st.session_state:
    st.session_state.route_error = None

with st.form("route_form"):
    st.subheader("어디로 이동할까요?")
    col1, col2 = st.columns(2)

    with col1:
        출발입력 = st.text_input(
            "🔵 출발역",
            placeholder="예: 강남역",
        )

    with col2:
        도착입력 = st.text_input(
            "🔷 도착역",
            placeholder="예: 홍대입구역",
        )

    기준 = st.radio(
        "경로 기준",
        ["최소 환승", "최단 역 수", "최단 시간"],
        horizontal=True,
    )

    검색버튼 = st.form_submit_button(
        "🔎 경로 찾기",
        use_container_width=True,
    )

if 검색버튼:
    st.session_state.route_result = None
    st.session_state.route_error = None

    if not 출발입력.strip() or not 도착입력.strip():
        st.session_state.route_error = "출발역과 도착역을 모두 입력해 줘."
    elif 역이름키(출발입력) == 역이름키(도착입력):
        st.session_state.route_error = "출발역과 도착역이 같아."
    else:
        출발노드들, 출발오류 = 정확한역찾기(
            출발입력,
            역정보,
            역검색표,
            그래프,
        )
        도착노드들, 도착오류 = 정확한역찾기(
            도착입력,
            역정보,
            역검색표,
            그래프,
        )

        if 출발오류:
            st.session_state.route_error = 출발오류
        elif 도착오류:
            st.session_state.route_error = 도착오류
        else:
            결과 = 경로찾기(
                출발노드들,
                set(도착노드들),
                그래프,
                기준,
            )

            if 결과 is None:
                st.session_state.route_error = "두 역 사이의 경로를 찾지 못했어."
            else:
                결과["steps"] = 경로단계만들기(
                    결과["path"],
                    결과["edge_types"],
                    역정보,
                )
                결과["origin_name"] = 역이름표시(
                    결과["path"][0], 역정보
                )
                결과["destination_name"] = 역이름표시(
                    결과["path"][-1], 역정보
                )
                결과["voice_text"] = 음성문장만들기(
                    결과["steps"],
                    역정보,
                    결과["path"][-1],
                )
                st.session_state.route_result = 결과
