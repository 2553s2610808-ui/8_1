import streamlit as st
import streamlit.components.v1 as components
import heapq
import html
import json
from itertools import combinations

# ==================================================
# 기본 설정
# ==================================================

st.set_page_config(
    page_title="지하철 길찾기",
    page_icon="🚇",
    layout="centered"
)

# ==================================================
# 색상 및 디자인
# ==================================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #F5F3FF, #FDF2F8, #ECFEFF);
    color: #1F2937;
}

.block-container {
    max-width: 950px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #312E81;
}

.hero {
    padding: 35px 28px;
    border-radius: 26px;
    background: linear-gradient(135deg, #312E81, #7C3AED, #DB2777);
    color: white;
    box-shadow: 0 12px 30px rgba(88, 28, 135, 0.18);
    margin-bottom: 24px;
}

.hero-title {
    font-size: 36px;
    font-weight: 800;
    margin-bottom: 8px;
    color: white;
}

.hero-subtitle {
    font-size: 15px;
    color: #F3E8FF;
    line-height: 1.6;
}

div[data-testid="stTextInput"] input {
    border-radius: 14px;
    border: 1px solid #DDD6FE;
    background: #FFFFFF;
    color: #1F2937;
    min-height: 48px;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #8B5CF6;
    box-shadow: 0 0 0 2px #EDE9FE;
}

div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #7C3AED, #DB2777);
    color: white;
    border: none;
    border-radius: 14px;
    min-height: 50px;
    font-size: 16px;
    font-weight: 800;
}

div[data-testid="stFormSubmitButton"] button:hover {
    color: white;
    border: none;
    filter: brightness(1.08);
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E9D5FF;
    border-radius: 17px;
    padding: 15px;
}

.segment-card {
    background: white;
    border: 1px solid #E9D5FF;
    border-radius: 20px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: 0 5px 16px rgba(49, 46, 129, 0.05);
}

.segment-title {
    font-size: 19px;
    font-weight: 800;
    color: #1F2937;
    margin-bottom: 13px;
}

.line-badge {
    display: inline-block;
    padding: 6px 13px;
    border-radius: 999px;
    color: white;
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 12px;
}

.station-list {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    align-items: center;
    margin: 12px 0;
}

.station-chip {
    padding: 7px 10px;
    border-radius: 10px;
    background: #F5F3FF;
    border: 1px solid #DDD6FE;
    color: #4C1D95;
    font-size: 13px;
    font-weight: 600;
}

.station-arrow {
    color: #A78BFA;
    font-weight: 800;
}

.transfer-card {
    background: #FFF1F2;
    border: 1px solid #FDA4AF;
    border-radius: 16px;
    padding: 15px;
    margin: 12px 0;
    color: #9F1239;
}

.transfer-title {
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 4px;
}

.route-summary {
    background: linear-gradient(135deg, #EDE9FE, #FCE7F3);
    border: 1px solid #DDD6FE;
    border-radius: 20px;
    padding: 22px;
    margin: 18px 0;
}

.route-big {
    font-size: 23px;
    font-weight: 800;
    color: #312E81;
}

.small-note {
    color: #6B7280;
    font-size: 12px;
    line-height: 1.7;
}

div[data-testid="stExpander"] {
    background: white;
    border-radius: 15px;
    border: 1px solid #E9D5FF;
}

hr {
    border-color: #E9D5FF;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# 지하철 노선 데이터
# 현재는 일부 역만 등록된 예시 데이터
# ==================================================

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
        "대방", "신길", "영등포", "신도림", "구로"
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
        "홍제", "무악재", "독립문", "경복궁", "안국",
        "종로3가", "을지로3가", "충무로", "동대입구",
        "약수", "금호", "옥수", "압구정", "신사",
        "잠원", "고속터미널", "교대", "남부터미널",
        "양재", "매봉", "도곡", "대치", "학여울",
        "대청", "일원", "수서"
    ],

    "4호선": [
        "진접", "오남", "별내별가람", "당고개",
        "상계", "노원", "창동", "쌍문", "수유", "미아",
        "미아사거리", "길음", "성신여대입구",
        "한성대입구", "혜화", "동대문",
        "동대문역사문화공원", "충무로", "명동", "회현",
        "서울역", "숙대입구", "삼각지", "신용산",
        "이촌", "동작", "이수", "사당", "남태령"
    ],

    "5호선": [
        "방화", "개화산", "김포공항", "송정", "마곡",
        "발산", "우장산", "화곡", "까치산", "신정",
        "목동", "오목교", "양평", "영등포구청",
        "영등포시장", "신길", "여의도", "여의나루",
        "마포", "공덕", "애오개", "충정로", "서대문",
        "광화문", "종로3가", "을지로4가",
        "동대문역사문화공원", "청구", "신금호",
        "행당", "왕십리", "마장", "답십리",
        "장한평", "군자", "아차산", "광나루", "천호", "강동"
    ],

    "6호선": [
        "응암", "역촌", "불광", "독바위", "연신내",
        "구산", "응암", "새절", "증산", "디지털미디어시티",
        "월드컵경기장", "마포구청", "망원", "합정",
        "상수", "광흥창", "대흥", "공덕", "효창공원앞",
        "삼각지", "녹사평", "이태원", "한강진",
        "버티고개", "약수", "청구", "신당", "동묘앞",
        "창신", "보문", "안암", "고려대", "월곡",
        "상월곡", "돌곶이", "석계", "태릉입구",
        "화랑대", "봉화산"
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
        "문정", "장지", "복정", "산성", "남한산성입구",
        "단대오거리", "신흥", "수진", "모란"
    ],

    "9호선": [
        "개화", "김포공항", "공항시장", "신방화",
        "마곡나루", "양천향교", "가양", "증미",
        "등촌", "염창", "신목동", "선유도", "당산",
        "국회의사당", "여의도", "샛강", "노량진",
        "노들", "흑석", "동작", "구반포", "신반포",
        "고속터미널", "사평", "신논현", "언주",
        "선정릉", "삼성중앙", "봉은사", "종합운동장"
    ]
}


# ==================================================
# 역 목록 및 그래프 생성
# ==================================================

def 그래프만들기():
    graph = {}
    station_lines = {}

    # 노선별 역 연결
    for line, stations in LINES.items():
        for station in stations:
            node = (line, station)
            graph.setdefault(node, [])
            station_lines.setdefault(station, set()).add(line)

        for a, b in zip(stations, stations[1:]):
            node_a = (line, a)
            node_b = (line, b)

            if node_a == node_b:
                continue

            graph[node_a].append((node_b, 1, 0))
            graph[node_b].append((node_a, 1, 0))

    # 같은 역 이름을 가진 서로 다른 노선끼리 환승 연결
    for station, lines in station_lines.items():
        nodes = [(line, station) for line in sorted(lines)]

        for node_a, node_b in combinations(nodes, 2):
            graph[node_a].append((node_b, 0, 1))
            graph[node_b].append((node_a, 0, 1))

    return graph, station_lines


GRAPH, STATION_LINES = 그래프만들기()


# ==================================================
# 역 이름 정리
# '강남역'은 '강남'으로 찾되 '서울역'은 그대로 유지
# ==================================================

def 역이름정리(name):
    name = name.strip()

    if name in STATION_LINES:
        return name

    if name.endswith("역"):
        without_suffix = name[:-1].strip()

        if without_suffix in STATION_LINES:
            return without_suffix

    return name


def 역표시(name):
    if name.endswith("역"):
        return name

    return name + "역"


# ==================================================
# 경로 찾기
# 이동 역 수가 적은 경로를 우선으로 찾고,
# 이동 역 수가 같으면 환승이 적은 경로를 선택
# ==================================================

def 지하철경로찾기(start, end):

    start_nodes = [
        (line, start)
        for line in sorted(STATION_LINES.get(start, set()))
    ]

    end_nodes = {
        (line, end)
        for line in STATION_LINES.get(end, set())
    }

    if not start_nodes or not end_nodes:
        return None

    distance = {}
    previous = {}
    queue = []

    for node in start_nodes:
        distance[node] = (0, 0)
        heapq.heappush(
            queue,
            (0, 0, node[0], node[1])
        )

    destination = None

    while queue:
        stops, transfers, line, station = heapq.heappop(queue)
        current = (line, station)

        if distance.get(current) != (stops, transfers):
            continue

        if current in end_nodes:
            destination = current
            break

        for next_node, add_stops, add_transfers in GRAPH[current]:
            new_cost = (
                stops + add_stops,
                transfers + add_transfers
            )

            if new_cost < distance.get(
                next_node,
                (float("inf"), float("inf"))
            ):
                distance[next_node] = new_cost
                previous[next_node] = current

                heapq.heappush(
                    queue,
                    (
                        new_cost[0],
                        new_cost[1],
                        next_node[0],
                        next_node[1]
                    )
                )

    if destination is None:
        return None

    path = []
    current = destination

    while current in previous:
        path.append(current)
        current = previous[current]

    path.append(current)
    path.reverse()

    return path


# ==================================================
# 경로를 노선별 구간으로 나누기
# 환승역은 앞 노선과 다음 노선에 모두 표시
# ==================================================

def 구간정리(path):
    segments = []

    for line, station in path:

        if not segments:
            segments.append({
                "line": line,
                "stations": [station]
            })
            continue

        last_segment = segments[-1]

        if last_segment["line"] == line:
            if last_segment["stations"][-1] != station:
                last_segment["stations"].append(station)
        else:
            # 환승역이 다음 노선의 시작역에도 들어가도록 처리
            segments.append({
                "line": line,
                "stations": [station]
            })

    return segments


# ==================================================
# 노선 색상
# ==================================================

LINE_COLORS = {
    "1호선": "#2563EB",
    "2호선": "#16A34A",
    "3호선": "#F97316",
    "4호선": "#0EA5E9",
    "5호선": "#8B5CF6",
    "6호선": "#C2410C",
    "7호선": "#65A30D",
    "8호선": "#DB2777",
    "9호선": "#A8A29E"
}


def 노선배지(line):
    color = LINE_COLORS.get(line, "#7C3AED")
    text_color = "#1F2937" if line == "9호선" else "#FFFFFF"

    return (
        f'<span class="line-badge" '
        f'style="background:{color};color:{text_color};">'
        f'{html.escape(line)}</span>'
    )


# ==================================================
# 음성 안내
# ==================================================

def 음성안내(내용):

    message = json.dumps(내용, ensure_ascii=False)

    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;background:transparent;">
            <button onclick="speakRoute()"
                style="
                    width:100%;
                    padding:14px;
                    border:0;
                    border-radius:14px;
                    background:linear-gradient(90deg,#7C3AED,#DB2777);
                    color:white;
                    font-size:15px;
                    font-weight:700;
                    cursor:pointer;
                ">
                🔊 음성 안내 듣기
            </button>

            <script>
                const routeMessage = {message};

                function speakRoute() {{
                    if (!('speechSynthesis' in window)) {{
                        alert('이 브라우저는 음성 안내를 지원하지 않습니다.');
                        return;
                    }}

                    window.speechSynthesis.cancel();

                    const speech = new SpeechSynthesisUtterance(routeMessage);
                    speech.lang = 'ko-KR';
                    speech.rate = 0.9;

                    window.speechSynthesis.speak(speech);
                }}
            </script>
        </body>
        </html>
        """,
        height=60,
        scrolling=False
    )


# ==================================================
# 화면 제목
# ==================================================

st.markdown("""
<div class="hero">
    <div class="hero-title">🚇 지하철 길찾기</div>
    <div class="hero-subtitle">
        출발역과 도착역을 입력하고 이동 경로를 확인하세요.<br>
        환승역과 노선별 정차역도 한눈에 볼 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)


# ==================================================
# 출발역 / 도착역 입력
# ==================================================

with st.form("route_form"):

    col1, col2 = st.columns(2)

    with col1:
        start_input = st.text_input(
            "🟣 출발역",
            placeholder="예: 강남역"
        )

    with col2:
        end_input = st.text_input(
            "🩷 도착역",
            placeholder="예: 홍대입구역"
        )

    submitted = st.form_submit_button(
        "🔎 경로 찾기",
        use_container_width=True
    )


# ==================================================
# 검색 결과
# ==================================================

if submitted:

    start = 역이름정리(start_input)
    end = 역이름정리(end_input)

    if not start_input.strip() or not end_input.strip():
        st.warning("출발역과 도착역을 모두 입력해 줘.")

    elif start == end:
        st.info("출발역과 도착역이 같아.")

    elif start not in STATION_LINES:
        st.error(
            f"'{start_input}' 역은 현재 등록된 데이터에 없어. "
            "역 이름을 확인해 줘."
        )

    elif end not in STATION_LINES:
        st.error(
            f"'{end_input}' 역은 현재 등록된 데이터에 없어. "
            "역 이름을 확인해 줘."
        )

    else:
        path = 지하철경로찾기(start, end)

        if path is None:
            st.error("두 역 사이의 경로를 찾을 수 없어.")

        else:
            segments = 구간정리(path)

            total_stops = sum(
                len(segment["stations"]) - 1
                for segment in segments
            )

            total_transfers = len(segments) - 1

            # ------------------------------
            # 경로 요약
            # ------------------------------

            st.markdown(
                f"""
                <div class="route-summary">
                    <div class="route-big">
                        {html.escape(역표시(start))}
                        &nbsp;→&nbsp;
                        {html.escape(역표시(end))}
                    </div>
                    <div style="margin-top:9px;color:#6D28D9;font-weight:600;">
                        추천 이동 경로
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            c1, c2, c3 = st.columns(3)

            c1.metric("이동 역 수", f"{total_stops}개")
            c2.metric("환승 횟수", f"{total_transfers}회")
            c3.metric("이용 노선", f"{len(segments)}개")

            st.divider()

            # ------------------------------
            # 노선별 상세 안내
            # ------------------------------

            st.subheader("🧭 이동 경로")

            speech_parts = [
                f"{역표시(start)}에서 출발합니다."
            ]

            for i, segment in enumerate(segments):

                line = segment["line"]
                stations = segment["stations"]

                chips = (
                    '<span class="station-arrow">→</span>'
                ).join(
                    f'<span class="station-chip">'
                    f'{html.escape(역표시(station))}'
                    f'</span>'
                    for station in stations
                )

                start_label = 역표시(stations[0])
                end_label = 역표시(stations[-1])

                st.markdown(
                    f"""
                    <div class="segment-card">
                        {노선배지(line)}

                        <div class="segment-title">
                            {html.escape(start_label)}
                            → {html.escape(end_label)}
                        </div>

                        <div class="station-list">
                            {chips}
                        </div>

                        <div class="small-note">
                            이 구간에서 이동하는 역 수:
                            {len(stations) - 1}개
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if i == 0:
                    speech_parts.append(
                        f"{line}을 타고 "
                        f"{end_label}까지 이동하세요."
                    )
                else:
                    transfer_station = stations[0]

                    speech_parts.append(
                        f"{역표시(transfer_station)}에서 "
                        f"{line}으로 환승한 뒤 "
                        f"{end_label}까지 이동하세요."
                    )

                # 환승 안내
                if i < len(segments) - 1:

                    transfer_station = stations[-1]
                    next_line = segments[i + 1]["line"]

                    st.markdown(
                        f"""
                        <div class="transfer-card">
                            <div class="transfer-title">
                                🔄 {html.escape(역표시(transfer_station))}
                                에서 환승
                            </div>
                            <div>
                                다음 노선인
                                <b>{html.escape(next_line)}</b>을
                                이용하세요.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            speech_parts.append(
                f"{역표시(end)}에 도착했습니다."
            )

            # ------------------------------
            # 전체 이동 순서
            # ------------------------------

            st.divider()
            st.subheader("🗺️ 전체 경로 노선도")

            with st.container(border=True):

                for i, segment in enumerate(segments):

                    st.markdown(
                        노선배지(segment["line"]),
                        unsafe_allow_html=True
                    )

                    station_text = "　→　".join(
                        역표시(station)
                        for station in segment["stations"]
                    )

                    st.write(station_text)

                    if i < len(segments) - 1:
                        st.markdown(
                            '<div style="color:#DB2777;font-weight:700;'
                            'padding:5px 0;">'
                            '↓ 환승'
                            '</div>',
                            unsafe_allow_html=True
                        )

            # ------------------------------
            # 음성 안내
            # ------------------------------

            st.divider()
            st.subheader("🔊 음성 안내")

            음성안내(" ".join(speech_parts))

            # ------------------------------
            # 안내 사항
            # ------------------------------

            with st.expander("경로 안내가 실제와 다를 수 있는 이유"):
                st.write(
                    "현재 코드에는 주요 역 위주의 예시 노선 데이터가 "
                    "들어 있어. 모든 역과 지선이 등록된 것은 아니므로 "
                    "실제 운행 경로를 완벽하게 보장하지는 않아. "
                    "전체 수도권 경로를 정확히 안내하려면 완전한 역 데이터와 "
                    "실제 환승 정보를 추가해야 해."
                )

else:
    st.info(
        "출발역과 도착역을 입력한 다음 **경로 찾기**를 눌러 줘."
    )
