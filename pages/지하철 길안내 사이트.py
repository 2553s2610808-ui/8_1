import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import heapq
import json
import html
import re
import math
from io import StringIO
from itertools import combinations

# ==================================================
# 기본 설정
# ==================================================

st.set_page_config(
    page_title="BLUE ROUTE | 지하철 길찾기",
    page_icon="🚇",
    layout="wide"
)

# ==================================================
# 지하철 데이터 주소
# 공개 CSV에서 역 정보와 역 사이 연결 정보를 가져옴
# ==================================================

STATION_URL = (
    "https://raw.githubusercontent.com/"
    "JoeYunHa/korea_seoul_subway_static_data/"
    "main/data/subway_station.csv"
)

SECTION_URL = (
    "https://raw.githubusercontent.com/"
    "JoeYunHa/korea_seoul_subway_static_data/"
    "main/data/subway_section.csv"
)

# ==================================================
# 파란색 디자인
# ==================================================

st.markdown("""
<style>
.stApp {
    background: #F0F6FF;
    color: #172554;
}

.block-container {
    max-width: 1050px;
    padding-top: 28px;
    padding-bottom: 50px;
}

h1, h2, h3 {
    color: #123B72;
}

.hero {
    padding: 36px;
    border-radius: 25px;
    background: linear-gradient(
        120deg,
        #102A56 0%,
        #1768C4 60%,
        #38BDF8 100%
    );
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 12px 30px rgba(23, 104, 196, 0.18);
}

.hero-title {
    color: white;
    font-size: 36px;
    font-weight: 800;
    margin-bottom: 9px;
}

.hero-subtitle {
    color: #DBEEFF;
    font-size: 15px;
    line-height: 1.8;
}

.section-card {
    background: white;
    border: 1px solid #D6E7FF;
    border-radius: 22px;
    padding: 23px;
    margin-top: 17px;
    margin-bottom: 17px;
    box-shadow: 0 6px 22px rgba(30, 64, 175, 0.05);
}

div[data-testid="stTextInput"] input {
    border: 1px solid #BFDBFE;
    border-radius: 13px;
    min-height: 48px;
    background: white;
    color: #172554;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #2563EB;
    box-shadow: 0 0 0 2px #DBEAFE;
}

div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #1D4ED8, #0284C7);
    border: none;
    border-radius: 13px;
    color: white;
    font-size: 16px;
    font-weight: 800;
    min-height: 50px;
}

div[data-testid="stFormSubmitButton"] button:hover {
    color: white;
    filter: brightness(1.08);
    border: none;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #BFDBFE;
    border-radius: 17px;
    padding: 15px;
}

.route-summary {
    background: linear-gradient(120deg, #DBEAFE, #E0F2FE);
    border: 1px solid #BFDBFE;
    border-radius: 20px;
    padding: 23px;
    margin-top: 20px;
    margin-bottom: 20px;
}

.route-name {
    font-size: 24px;
    font-weight: 800;
    color: #123B72;
    line-height: 1.6;
}

.route-caption {
    color: #2563EB;
    font-size: 14px;
    margin-top: 7px;
}

.segment-card {
    background: white;
    border: 1px solid #D6E7FF;
    border-radius: 18px;
    padding: 20px;
    margin-top: 12px;
    margin-bottom: 12px;
    box-shadow: 0 5px 16px rgba(30, 64, 175, 0.04);
}

.line-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    color: white;
    font-weight: 800;
    font-size: 13px;
    margin-bottom: 10px;
}

.segment-title {
    color: #172554;
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 12px;
}

.station-list {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    align-items: center;
    line-height: 1.8;
}

.station-chip {
    display: inline-block;
    border-radius: 10px;
    padding: 7px 10px;
    color: #1D4ED8;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    font-size: 13px;
    font-weight: 600;
}

.station-arrow {
    color: #60A5FA;
    font-weight: 800;
}

.transfer-card {
    border-left: 5px solid #0284C7;
    background: #E0F2FE;
    border-radius: 13px;
    padding: 15px;
    margin: 14px 0;
    color: #075985;
}

.transfer-title {
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 5px;
}

.small-note {
    color: #64748B;
    font-size: 12px;
    line-height: 1.8;
}

div[data-testid="stExpander"] {
    background: white;
    border: 1px solid #BFDBFE;
    border-radius: 14px;
}

hr {
    border-color: #DBEAFE;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 역 이름 정리
# 서울 = 서울역
# 총신대입구와 이수는 같은 환승역으로 취급
# ==================================================

def 역이름키(이름):
    이름 = re.sub(r"\s+", "", str(이름))

    if 이름.endswith("역") and len(이름) > 1:
        이름 = 이름[:-1]

    별칭 = {
        "서울": "서울역",
        "이수": "이수(총신대입구)",
        "총신대입구": "이수(총신대입구)",
        "총신대입구(이수)": "이수(총신대입구)"
    }

    return 별칭.get(이름, 이름)


def 역이름표시(이름):
    키 = 역이름키(이름)

    if 키 == "서울역":
        return "서울역"

    if 키 == "이수(총신대입구)":
        return "이수(총신대입구)역"

    이름 = str(이름).strip()

    if 이름.endswith("역"):
        return 이름

    return 이름 + "역"


# ==================================================
# 두 역 사이의 거리 계산
# 환승역 연결을 판단할 때 사용
# ==================================================

def 두역거리(a, b):
    if (
        a["lat"] is None or
        a["lng"] is None or
        b["lat"] is None or
        b["lng"] is None
    ):
        return float("inf")

    지구반지름 = 6371000

    위도1 = math.radians(a["lat"])
    위도2 = math.radians(b["lat"])

    위도차 = math.radians(b["lat"] - a["lat"])
    경도차 = math.radians(b["lng"] - a["lng"])

    값 = (
        math.sin(위도차 / 2) ** 2
        + math.cos(위도1)
        * math.cos(위도2)
        * math.sin(경도차 / 2) ** 2
    )

    return (
        2
        * 지구반지름
        * math.asin(min(1, math.sqrt(값)))
    )


# ==================================================
# 데이터 불러오기
# 한 번 불러온 데이터는 캐시에 저장
# ==================================================

@st.cache_data(ttl=86400)
def 데이터불러오기():

    def csv읽기(url):
        response = requests.get(
            url,
            timeout=30
        )
        response.raise_for_status()

        내용 = response.content.decode("utf-8-sig")

        return pd.read_csv(
            StringIO(내용),
            dtype=str,
            keep_default_na=False
        )

    역자료 = csv읽기(STATION_URL)
    구간자료 = csv읽기(SECTION_URL)

    # ----------------------------------------------
    # 역 정보 정리
    # ----------------------------------------------

    역정보 = {}
    역코드표 = {}
    노선별역표 = {}

    for row in 역자료.to_dict("records"):

        node = row.get("station_id", "").strip()
        line = row.get("line", "").strip()
        name = row.get("name", "").strip()
        code = row.get("station_cd", "").strip()

        if not node or not line or not name:
            continue

        try:
            lat = float(row.get("lat", ""))
            lng = float(row.get("lng", ""))
        except (ValueError, TypeError):
            lat = None
            lng = None

        역정보[node] = {
            "line": line,
            "name": name,
            "lat": lat,
            "lng": lng
        }

        if code:
            역코드표.setdefault(
                (line, code),
                node
            )

        key = 역이름키(name)

        노선별역표.setdefault(
            (line, key),
            []
        ).append(node)

    # ----------------------------------------------
    # 각 역의 연결 정보 생성
    # ----------------------------------------------

    그래프 = {
        node: set()
        for node in 역정보
    }

    def 연결(a, b, 이동역수, 환승수):
        if a == b:
            return

        if a not in 그래프 or b not in 그래프:
            return

        그래프[a].add(
            (b, 이동역수, 환승수)
        )

        그래프[b].add(
            (a, 이동역수, 환승수)
        )

    for row in 구간자료.to_dict("records"):

        line = row.get("line", "").strip()

        위쪽코드 = row.get(
            "up_station_code", ""
        ).strip()

        아래쪽코드 = row.get(
            "down_station_code", ""
        ).strip()

        위쪽역 = row.get(
            "up_station_name", ""
        ).strip()

        아래쪽역 = row.get(
            "down_station_name", ""
        ).strip()

        # 역 코드로 먼저 찾기
        a = 역코드표.get((line, 위쪽코드))
        b = 역코드표.get((line, 아래쪽코드))

        # 코드가 맞지 않는 경우 같은 노선의 역 이름으로 찾기
        if not a:
            candidates = 노선별역표.get(
                (line, 역이름키(위쪽역)),
                []
            )
            if candidates:
                a = candidates[0]

        if not b:
            candidates = 노선별역표.get(
                (line, 역이름키(아래쪽역)),
                []
            )
            if candidates:
                b = candidates[0]

        if a and b:
            # 실제 연결된 인접 역끼리만 연결
            연결(a, b, 1, 0)

    # ----------------------------------------------
    # 환승역 연결
    # 역 이름이 같아도 위치가 멀면 연결하지 않음
    # ----------------------------------------------

    역이름별노드 = {}

    for node, info in 역정보.items():

        key = 역이름키(info["name"])

        역이름별노드.setdefault(
            key,
            []
        ).append(node)

    환승거리제한 = 500  # 미터

    for key, nodes in 역이름별노드.items():

        for a, b in combinations(nodes, 2):

            # 같은 노선 안에서는 환승 연결을 만들지 않음
            if 역정보[a]["line"] == 역정보[b]["line"]:
                continue

            거리 = 두역거리(
                역정보[a],
                역정보[b]
            )

            if 거리 <= 환승거리제한:
                연결(a, b, 0, 1)

    # ----------------------------------------------
    # 사용자가 입력한 역 이름으로 노드 찾기
    # ----------------------------------------------

    역검색표 = {}

    for key, nodes in 역이름별노드.items():
        역검색표[key] = sorted(set(nodes))

    return 역정보, 그래프, 역검색표


# ==================================================
# 최단 경로 계산
# 이동 역 수와 환승 횟수를 기준으로 계산
# ==================================================

def 경로찾기(출발노드들, 도착노드들, 그래프, 역정보, 기준):

    거리표 = {}
    이전역표 = {}
    대기열 = []

    def 비용(이동역수, 환승수):
        if 기준 == "최소 환승":
            return (환승수, 이동역수)

        return (이동역수, 환승수)

    # 같은 역 이름의 서로 다른 노선 노드에서 출발 가능
    for node in 출발노드들:

        거리표[node] = (0, 0)

        heapq.heappush(
            대기열,
            (0, 0, node)
        )

    목적지노드 = None

    while 대기열:

        우선비용1, 우선비용2, 현재 = heapq.heappop(
            대기열
        )

        실제이동수, 실제환승수 = 거리표[현재]

        if 비용(
            실제이동수,
            실제환승수
        ) != (우선비용1, 우선비용2):
            continue

        if 현재 in 도착노드들:
            목적지노드 = 현재
            break

        for 다음, 추가이동, 추가환승 in 그래프[현재]:

            새이동수 = 실제이동수 + 추가이동
            새환승수 = 실제환승수 + 추가환승

            새비용 = 비용(
                새이동수,
                새환승수
            )

            이전비용 = 비용(
                *거리표.get(
                    다음,
                    (float("inf"), float("inf"))
                )
            )

            if 새비용 < 이전비용:

                거리표[다음] = (
                    새이동수,
                    새환승수
                )

                이전역표[다음] = 현재

                heapq.heappush(
                    대기열,
                    (
                        새비용[0],
                        새비용[1],
                        다음
                    )
                )

    if 목적지노드 is None:
        return None

    # 목적지부터 출발역까지 역순으로 추적
    경로 = []
    현재 = 목적지노드

    while True:
        경로.append(현재)

        if 현재 not in 이전역표:
            break

        현재 = 이전역표[현재]

    경로.reverse()

    return 경로


# ==================================================
# 경로를 노선 구간별로 분리
# ==================================================

def 구간나누기(경로, 역정보):

    구간들 = []

    for node in 경로:

        line = 역정보[node]["line"]

        if (
            not 구간들
            or 구간들[-1]["line"] != line
        ):

            구간들.append({
                "line": line,
                "nodes": [node]
            })

        else:

            if 구간들[-1]["nodes"][-1] != node:
                구간들[-1]["nodes"].append(node)

    return 구간들


# ==================================================
# 노선 색상
# 노선별 배지는 구별하기 쉽게 노선 고유 색상 사용
# 앱 전체 디자인은 파란색 계열
# ==================================================

노선색상 = {
    "1호선": "#0052A4",
    "2호선": "#00A84D",
    "3호선": "#EF7C1C",
    "4호선": "#00A5DE",
    "5호선": "#996CAC",
    "6호선": "#CD7C2F",
    "7호선": "#747F00",
    "8호선": "#E6186C",
    "9호선": "#BDB092",
    "경의중앙선": "#77C4A3",
    "경춘선": "#0C8E72",
    "공항철도": "#0090D0",
    "신분당선": "#D4003B",
    "수인분당선": "#FABE00",
    "김포골드라인": "#A17800",
    "용인에버라인": "#509F22",
    "인천1호선": "#759CCE",
    "인천2호선": "#ED8000",
    "서해선": "#8FC31F",
    "신림선": "#6789CA",
    "우이신설선": "#B7C452"
}


def 노선배지(line):
    color = 노선색상.get(
        line,
        "#2563EB"
    )

    return (
        '<span class="line-badge" '
        f'style="background:{color};">'
        f'{html.escape(line)}</span>'
    )


def 역표시(node, 역정보):
    return 역이름표시(
        역정보[node]["name"]
    )


# ==================================================
# 음성 안내
# ==================================================

def 음성안내(문장):

    음성문장 = json.dumps(
        문장,
        ensure_ascii=False
    )

    components.html(
        f"""
        <button
            onclick="speakRoute()"
            style="
                width:100%;
                padding:15px;
                border:0;
                border-radius:13px;
                background:linear-gradient(90deg,#1D4ED8,#0284C7);
                color:white;
                font-size:15px;
                font-weight:800;
                cursor:pointer;
            ">
            🔊 음성 안내 듣기
        </button>

        <script>
            const routeText = {음성문장};

            function speakRoute() {{
                if (!window.speechSynthesis) {{
                    alert('이 브라우저는 음성 안내를 지원하지 않습니다.');
                    return;
                }}

                window.speechSynthesis.cancel();

                const utterance =
                    new SpeechSynthesisUtterance(routeText);

                utterance.lang = 'ko-KR';
                utterance.rate = 0.9;

                window.speechSynthesis.speak(utterance);
            }}
        </script>
        """,
        height=65
    )


# ==================================================
# 화면 상단
# ==================================================

st.markdown("""
<div class="hero">
    <div class="hero-title">🚇 BLUE ROUTE</div>
    <div class="hero-subtitle">
        더 깔끔하게, 한눈에 확인하는 지하철 길찾기<br>
        출발역과 도착역을 입력하고 이동 순서를 확인하세요.
    </div>
</div>
""", unsafe_allow_html=True)


# ==================================================
# 지하철 데이터 로딩
# ==================================================

try:
    with st.spinner("지하철 노선 정보를 불러오는 중..."):
        역정보, 그래프, 역검색표 = 데이터불러오기()

except Exception:
    st.error(
        "지하철 데이터를 불러오지 못했어. "
        "인터넷 연결을 확인한 뒤 앱을 다시 실행해 줘."
    )
    st.stop()


# ==================================================
# 출발역 / 도착역 입력
# ==================================================

st.markdown(
    '<div class="section-card">',
    unsafe_allow_html=True
)

with st.form("route_form"):

    st.subheader("어디로 이동할까요?")

    col1, col2 = st.columns(2)

    with col1:
        출발입력 = st.text_input(
            "🔵 출발역",
            placeholder="예: 강남역"
        )

    with col2:
        도착입력 = st.text_input(
            "🔹 도착역",
            placeholder="예: 홍대입구역"
        )

    기준 = st.radio(
        "경로 기준",
        ["최소 환승", "최단 역 수"],
        horizontal=True,
        help=(
            "최소 환승은 환승 횟수를 먼저 줄이고, "
            "최단 역 수는 이동하는 역 수를 먼저 줄여."
        )
    )

    검색버튼 = st.form_submit_button(
        "🔎 경로 찾기",
        use_container_width=True
    )

st.markdown("</div>", unsafe_allow_html=True)


# ==================================================
# 경로 검색 결과
# ==================================================

if 검색버튼:

    출발키 = 역이름키(출발입력)
    도착키 = 역이름키(도착입력)

    if not 출발입력.strip() or not 도착입력.strip():

        st.warning("출발역과 도착역을 모두 입력해 줘.")

    elif 출발키 == 도착키:

        st.info("출발역과 도착역이 같아.")

    elif 출발키 not in 역검색표:

        st.error(
            f"'{출발입력}' 역을 데이터에서 찾을 수 없어. "
            "역 이름을 확인해 줘."
        )

    elif 도착키 not in 역검색표:

        st.error(
            f"'{도착입력}' 역을 데이터에서 찾을 수 없어. "
            "역 이름을 확인해 줘."
        )

    else:

        출발노드들 = 역검색표[출발키]
        도착노드들 = set(역검색표[도착키])

        경로 = 경로찾기(
            출발노드들,
            도착노드들,
            그래프,
            역정보,
            기준
        )

        if not 경로:

            st.error(
                "연결된 경로를 찾지 못했어. "
                "다른 역 이름으로 검색해 줘."
            )

        else:

            구간들 = 구간나누기(
                경로,
                역정보
            )

            총이동역수 = sum(
                max(0, len(구간["nodes"]) - 1)
                for 구간 in 구간들
            )

            총환승횟수 = sum(
                1
                for a, b in zip(경로, 경로[1:])
                if 역정보[a]["line"] != 역정보[b]["line"]
            )

            # --------------------------------------
            # 경로 요약
            # --------------------------------------

            st.markdown(
                f"""
                <div class="route-summary">
                    <div class="route-name">
                        {html.escape(역표시(경로[0], 역정보))}
                        &nbsp; → &nbsp;
                        {html.escape(역표시(경로[-1], 역정보))}
                    </div>
                    <div class="route-caption">
                        {html.escape(기준)} 기준으로 계산한 경로
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "이동 역 수",
                f"{총이동역수}개"
            )

            c2.metric(
                "환승 횟수",
                f"{총환승횟수}회"
            )

            c3.metric(
                "이용 노선",
                f"{len(구간들)}개"
            )

            st.divider()

            # --------------------------------------
            # 상세 경로 표시
            # --------------------------------------

            st.subheader("🧭 이동 경로")

            음성문장목록 = [
                f"{역표시(경로[0], 역정보)}에서 출발합니다."
            ]

            for i, 구간 in enumerate(구간들):

                line = 구간["line"]
                nodes = 구간["nodes"]

                첫역 = 역표시(nodes[0], 역정보)
                마지막역 = 역표시(nodes[-1], 역정보)

                역칩 = (
                    '<span class="station-arrow">→</span>'
                ).join(
                    '<span class="station-chip">'
                    + html.escape(역표시(node, 역정보))
                    + '</span>'
                    for node in nodes
                )

                st.markdown(
                    f"""
                    <div class="segment-card">
                        {노선배지(line)}

                        <div class="segment-title">
                            {html.escape(첫역)}
                            → {html.escape(마지막역)}
                        </div>

                        <div class="station-list">
                            {역칩}
                        </div>

                        <div class="small-note">
                            이 구간에서 이동하는 역 수:
                            {max(0, len(nodes) - 1)}개
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                음성문장목록.append(
                    f"{line}을 타고 "
                    f"{마지막역}까지 이동하세요."
                )

                # 환승 정보 표시
                if i < len(구간들) - 1:

                    다음노선 = 구간들[i + 1]["line"]

                    st.markdown(
                        f"""
                        <div class="transfer-card">
                            <div class="transfer-title">
                                🔄 {html.escape(마지막역)}에서 환승
                            </div>
                            다음 노선인
                            <b>{html.escape(다음노선)}</b>을 이용하세요.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    음성문장목록.append(
                        f"{마지막역}에서 "
                        f"{다음노선}으로 환승하세요."
                    )

            음성문장목록.append(
                f"{역표시(경로[-1], 역정보)}에 도착했습니다."
            )

            # --------------------------------------
            # 전체 역 순서
            # --------------------------------------

            st.divider()
            st.subheader("📍 전체 정차역")

            전체역목록 = [
                역표시(node, 역정보)
                for node in 경로
            ]

            st.markdown(
                '<div class="section-card">',
                unsafe_allow_html=True
            )

            for i, 역이름 in enumerate(전체역목록):

                st.markdown(
                    f"""
                    <div style="
                        display:flex;
                        align-items:center;
                        gap:12px;
                        padding:8px 0;
                    ">
                        <div style="
                            min-width:30px;
                            height:30px;
                            border-radius:50%;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            background:#DBEAFE;
                            color:#1D4ED8;
                            font-weight:800;
                            font-size:12px;
                        ">
                            {i + 1}
                        </div>

                        <div style="
                            font-weight:600;
                            color:#1E3A8A;
                        ">
                            {html.escape(역이름)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if i < len(전체역목록) - 1:
                    st.markdown(
                        '<div style="margin-left:14px;'
                        'border-left:2px solid #93C5FD;'
                        'height:12px;"></div>',
                        unsafe_allow_html=True
                    )

            st.markdown("</div>", unsafe_allow_html=True)

            # --------------------------------------
            # 음성 안내
            # --------------------------------------

            st.divider()
            st.subheader("🔊 음성 안내")

            음성안내(" ".join(음성문장목록))

            # --------------------------------------
            # 안내 사항
            # --------------------------------------

            with st.expander("경로 계산 방식과 주의 사항"):

                st.write(
                    "역과 역 사이의 연결 정보를 이용해 경로를 계산해. "
                    "최소 환승은 환승 횟수를 먼저 줄이고, "
                    "최단 역 수는 이동 역 수를 먼저 줄여."
                )

                st.write(
                    "이 데이터는 실시간 열차 운행 정보를 제공하지 않아. "
                    "실제 시간표, 급행 운행, 운행 중단, 역 내부 환승 통로 "
                    "등은 반영되지 않을 수 있어. 실제 이동 전에는 "
                    "최신 교통 안내도 확인해 줘."
                )

else:

    st.info(
        "출발역과 도착역을 입력한 다음 "
        "**경로 찾기**를 눌러 줘."
    )
