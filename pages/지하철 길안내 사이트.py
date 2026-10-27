import streamlit as st
import requests
import html
import re
from collections import deque

# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="SUBWAY ROUTE",
    page_icon="🚇",
    layout="wide"
)

# =========================================================
# 디자인
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #f5f7fb 0%, #eef2f7 100%);
}

.block-container {
    max-width: 1100px;
    padding-top: 35px;
}

/* 제목 */

.hero {
    background: linear-gradient(135deg, #111827, #26364d);
    padding: 38px 40px;
    border-radius: 28px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.12);
}

.hero-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 8px;
}

.hero-sub {
    font-size: 16px;
    color: #d1d5db;
}

/* 입력 */

.search-card {
    background: white;
    padding: 25px;
    border-radius: 24px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.07);
    margin-bottom: 25px;
}

.station-label {
    font-size: 14px;
    font-weight: 700;
    color: #6b7280;
    margin-bottom: 5px;
}

/* 결과 */

.result-card {
    background: white;
    padding: 28px;
    border-radius: 24px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.07);
    margin-top: 20px;
}

.route-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
}

.station-name {
    font-size: 25px;
    font-weight: 800;
}

.arrow {
    font-size: 25px;
    color: #9ca3af;
}

/* 노선 */

.line-badge {
    display: inline-block;
    padding: 7px 14px;
    border-radius: 999px;
    color: white;
    font-weight: 800;
    font-size: 14px;
    margin-bottom: 10px;
}

.line1 { background:#0052A4; }
.line2 { background:#00A84D; }
.line3 { background:#EF7C1C; }
.line4 { background:#00A5DE; }
.line5 { background:#996CAC; }
.line6 { background:#CD7C2F; }
.line7 { background:#747F00; }
.line8 { background:#E6186C; }
.line9 { background:#BDB092; }

.route-box {
    border-left: 5px solid #d1d5db;
    padding: 5px 0 5px 20px;
    margin: 10px 0;
}

.station-item {
    padding: 10px 0;
    font-size: 16px;
}

.transfer {
    background: #fff7ed;
    border: 1px solid #fed7aa;
    padding: 13px 17px;
    border-radius: 15px;
    margin: 12px 0;
    font-weight: 600;
}

.info {
    background: #f8fafc;
    border-radius: 17px;
    padding: 17px;
    margin-top: 18px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 지하철 노선 데이터
# =========================================================

LINES = {

    "1호선": [
        "소요산", "동두천", "보산", "동두천중앙", "지행",
        "덕정", "덕계", "양주", "녹양", "가능",
        "의정부", "회룡", "망월사", "도봉산", "도봉",
        "방학", "창동", "녹천", "월계", "광운대",
        "석계", "신이문", "외대앞", "회기", "청량리",
        "제기동", "신설동", "동묘앞", "동대문",
        "종로5가", "종로3가", "종각", "시청",
        "서울역", "남영", "용산", "노량진",
        "대방", "신길", "영등포", "신도림",
        "구로"
    ],

    "2호선": [
        "시청", "을지로입구", "을지로3가", "을지로4가",
        "동대문역사문화공원", "신당", "상왕십리", "왕십리",
        "한양대", "뚝섬", "성수", "건대입구", "구의",
        "강변", "잠실나루", "잠실", "잠실새내",
        "종합운동장", "삼성", "선릉", "역삼", "강남",
        "교대", "서초", "방배", "사당", "낙성대",
        "서울대입구", "봉천", "신림", "신대방",
        "구로디지털단지", "대림", "신도림", "문래",
        "영등포구청", "당산", "합정", "홍대입구",
        "신촌", "이대", "아현", "충정로", "시청"
    ],

    "3호선": [
        "대화", "주엽", "정발산", "마두", "백석",
        "대곡", "화정", "원당", "원흥", "삼송",
        "지축", "구파발", "연신내", "불광", "녹번",
        "홍제", "무악재", "독립문", "경복궁",
        "안국", "종로3가", "을지로3가", "충무로",
        "동대입구", "약수", "금호", "옥수", "압구정",
        "신사", "잠원", "고속터미널", "교대",
        "남부터미널", "양재", "매봉", "도곡",
        "대치", "학여울", "대청", "일원", "수서"
    ],

    "4호선": [
        "진접", "오남", "별내별가람", "당고개",
        "상계", "노원", "창동", "쌍문", "수유",
        "미아", "미아사거리", "길음", "성신여대입구",
        "한성대입구", "혜화", "동대문", "동대문역사문화공원",
        "충무로", "명동", "회현", "서울역",
        "숙대입구", "삼각지", "신용산", "이촌",
        "동작", "이수", "사당", "남태령"
    ],

    "5호선": [
        "방화", "개화산", "김포공항", "송정", "마곡",
        "발산", "우장산", "화곡", "까치산", "신정",
        "목동", "오목교", "양평", "영등포구청",
        "영등포시장", "신길", "여의도", "여의나루",
        "마포", "공덕", "애오개", "충정로",
        "서대문", "광화문", "종로3가", "을지로4가",
        "동대문역사문화공원", "청구", "신금호",
        "행당", "왕십리", "마장", "답십리",
        "장한평", "군자", "아차산", "광나루",
        "천호", "강동"
    ],

    "6호선": [
        "응암", "역촌", "불광", "독바위", "연신내",
        "구산", "응암", "새절", "증산", "디지털미디어시티",
        "월드컵경기장", "마포구청", "망원", "합정",
        "상수", "광흥창", "대흥", "공덕", "효창공원앞",
        "삼각지", "녹사평", "이태원", "한강진",
        "버티고개", "약수", "청구", "신당",
        "동묘앞", "창신", "보문", "안암",
        "고려대", "월곡", "상월곡", "돌곶이",
        "석계", "태릉입구", "화랑대", "봉화산"
    ],

    "7호선": [
        "장암", "도봉산", "수락산", "마들", "노원",
        "중계", "하계", "공릉", "태릉입구", "먹골",
        "중화", "상봉", "면목", "사가정", "용마산",
        "중곡", "군자", "어린이대공원", "건대입구",
        "뚝섬유원지", "청담", "강남구청", "학동",
        "논현", "반포", "고속터미널", "내방",
        "이수", "남성", "숭실대입구", "상도",
        "장승배기", "신대방삼거리", "보라매",
        "신풍", "대림", "남구로", "가산디지털단지",
        "철산", "광명사거리", "천왕", "온수"
    ],

    "8호선": [
        "암사", "천호", "강동구청", "몽촌토성",
        "잠실", "석촌", "송파", "가락시장",
        "문정", "장지", "복정", "산성",
        "남한산성입구", "단대오거리", "신흥",
        "수진", "모란"
    ],

    "9호선": [
        "개화", "김포공항", "공항시장", "신방화",
        "마곡나루", "양천향교", "가양", "증미",
        "등촌", "염창", "신목동", "선유도",
        "당산", "국회의사당", "여의도", "샛강",
        "노량진", "노들", "흑석", "동작",
        "구반포", "신반포", "고속터미널", "사평",
        "신논현", "언주", "선정릉", "삼성중앙",
        "봉은사", "종합운동장"
    ]
}


# =========================================================
# 역 이름 검색
# =========================================================

def 역찾기(역이름):

    역이름 = 역이름.strip()

    결과 = []

    for 노선, 역목록 in LINES.items():

        for 역 in 역목록:

            if 역이름 == 역:
                결과.append((노선, 역))

    return 결과


# =========================================================
# 그래프 생성
# =========================================================

def 그래프만들기():

    graph = {}

    for 노선, 역목록 in LINES.items():

        for i in range(len(역목록) - 1):

            a = 역목록[i]
            b = 역목록[i + 1]

            if a not in graph:
                graph[a] = []

            if b not in graph:
                graph[b] = []

            graph[a].append((b, 노선))
            graph[b].append((a, 노선))

    return graph


GRAPH = 그래프만들기()


# =========================================================
# 지하철 최단경로
# =========================================================

def 지하철경로찾기(출발, 도착):

    if 출발 not in GRAPH:
        return None

    if 도착 not in GRAPH:
        return None

    queue = deque()

    queue.append((출발, None))

    visited = {
        출발: (None, None)
    }

    while queue:

        현재, 노선 = queue.popleft()

        if 현재 == 도착:
            break

        for 다음, 다음노선 in GRAPH[현재]:

            if 다음 not in visited:

                visited[다음] = (현재, 다음노선)

                queue.append(
                    (다음, 다음노선)
                )

    if 도착 not in visited:
        return None

    path = []

    current = 도착

    while current is not None:

        이전, 노선 = visited[current]

        path.append(
            (current, 노선)
        )

        current = 이전

    path.reverse()

    return path


# =========================================================
# 경로 정리
# =========================================================

def 경로정리(path):

    결과 = []

    현재노선 = None
    현재역들 = []

    for 역, 노선 in path:

        if 노선 != 현재노선:

            if 현재역들:

                결과.append(
                    (현재노선, 현재역들)
                )

            현재노선 = 노선
            현재역들 = [역]

        else:

            현재역들.append(역)

    if 현재역들:

        결과.append(
            (현재노선, 현재역들)
        )

    return 결과


# =========================================================
# 노선 색상
# =========================================================

LINE_CLASS = {
    "1호선": "line1",
    "2호선": "line2",
    "3호선": "line3",
    "4호선": "line4",
    "5호선": "line5",
    "6호선": "line6",
    "7호선": "line7",
    "8호선": "line8",
    "9호선": "line9"
}


# =========================================================
# 음성 안내
# =========================================================

def 음성안내(텍스트):

    safe_text = html.escape(텍스트)

    st.markdown(
        f"""
        <script>
        function speakRoute() {{
            const text = `{safe_text}`;
            const speech = new SpeechSynthesisUtterance(text);
            speech.lang = "ko-KR";
            speech.rate = 0.9;
            speech.pitch = 1;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(speech);
        }}
        </script>

        <button
            onclick="speakRoute()"
            style="
                width:100%;
                padding:15px;
                border:none;
                border-radius:15px;
                background:#111827;
                color:white;
                font-size:16px;
                font-weight:700;
                cursor:pointer;
            "
        >
        🔊 음성으로 안내 듣기
        </button>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 헤더
# =========================================================

st.markdown("""
<div class="hero">

<div class="hero-title">
🚇 SUBWAY ROUTE
</div>

<div class="hero-sub">
출발역과 도착역을 입력하면 지하철 이동 경로를 안내합니다.
</div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# 입력
# =========================================================

st.markdown(
    '<div class="search-card">',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="station-label">출발역</div>',
    unsafe_allow_html=True
)

출발역 = st.text_input(
    "출발역",
    placeholder="예: 강남",
    label_visibility="collapsed"
)

st.markdown(
    '<div class="station-label">도착역</div>',
    unsafe_allow_html=True
)

도착역 = st.text_input(
    "도착역",
    placeholder="예: 홍대입구",
    label_visibility="collapsed"
)

검색 = st.button(
    "🚇 경로 찾기",
    use_container_width=True
)

st.markdown(
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# 검색 실행
# =========================================================

if 검색:

    출발역 = 출발역.strip()
    도착역 = 도착역.strip()

    if not 출발역 or not 도착역:

        st.warning("출발역과 도착역을 모두 입력해주세요.")

        st.stop()

    if 출발역 == 도착역:

        st.info("출발역과 도착역이 같습니다.")

        st.stop()

    출발정보 = 역찾기(출발역)
    도착정보 = 역찾기(도착역)

    if not 출발정보:

        st.error(
            f"'{출발역}' 역을 찾을 수 없습니다."
        )

        st.stop()

    if not 도착정보:

        st.error(
            f"'{도착역}' 역을 찾을 수 없습니다."
        )

        st.stop()

    path = 지하철경로찾기(
        출발역,
        도착역
    )

    if path is None:

        st.error(
            "두 역 사이의 경로를 찾을 수 없습니다."
        )

        st.stop()

    구간들 = 경로정리(path)

    환승횟수 = max(
        0,
        len(구간들) - 1
    )

    이동역수 = len(path) - 1


    # =====================================================
    # 결과 요약
    # =====================================================

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="route-header">

            <div class="station-name">
                {출발역}
            </div>

            <div class="arrow">
                →
            </div>

            <div class="station-name">
                {도착역}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "이동 역 수",
            f"{이동역수}개"
        )

    with c2:

        st.metric(
            "환승",
            f"{환승횟수}회"
        )

    with c3:

        st.metric(
            "이용 노선",
            f"{len(구간들)}개"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


    # =====================================================
    # 상세 경로
    # =====================================================

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True
    )

    st.subheader("🧭 이동 경로")

    음성문장 = f"{출발역}에서 {도착역}까지 이동합니다. "

    for index, (노선, 역들) in enumerate(구간들):

        css = LINE_CLASS.get(
            노선,
            "line1"
        )

        st.markdown(
            f"""
            <div class="route-box">

                <span class="line-badge {css}">
                    {노선}
                </span>

                <div style="font-size:18px;font-weight:700;">
                    {역들[0]}
                    →
                    {역들[-1]}
                </div>

                <div style="color:#6b7280;margin-top:6px;">
                    {len(역들)-1}개 역 이동
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        음성문장 += (
            f"{노선}을 타고 "
            f"{역들[-1]}역까지 이동합니다. "
        )

        if index < len(구간들) - 1:

            다음노선 = 구간들[index + 1][0]

            환승역 = 역들[-1]

            st.markdown(
                f"""
                <div class="transfer">
                    🔄 {환승역}에서
                    <b>{다음노선}</b>으로 환승하세요.
                </div>
                """,
                unsafe_allow_html=True
            )

            음성문장 += (
                f"{환승역}에서 "
                f"{다음노선}으로 환승합니다. "
            )

    음성문장 += (
        f"최종 목적지는 {도착역}입니다."
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


    # =====================================================
    # 전체 역 목록
    # =====================================================

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True
    )

    st.subheader("📍 정차역")

    전체역 = [
        역
        for 역, 노선 in path
    ]

    st.write(
        " → ".join(전체역)
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


    # =====================================================
    # 음성
    # =====================================================

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True
    )

    st.subheader("🔊 음성 안내")

    음성안내(음성문장)

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


    # =====================================================
    # 지하철 노선도
    # =====================================================

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True
    )

    st.subheader("🗺️ 수도권 지하철 노선도")

    st.markdown(
        """
        <div class="info">
        아래 공식 노선도에서 환승역과 전체 노선을 확인할 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.link_button(
        "🗺️ 공식 지하철 노선도 보기",
        "https://english.seoul.go.kr/wp-content/uploads/2026/03/guidebook_ko.pdf",
        use_container_width=True
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )
