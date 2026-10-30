import streamlit as st
import pandas as pd
import requests
import heapq
import re
import json
import math
from urllib.parse import quote
from io import StringIO
from itertools import combinations
import streamlit.components.v1 as components

# ==================================================
# 기본 설정
# ==================================================

st.set_page_config(
    page_title="BLUE ROUTE | 지하철 길찾기",
    page_icon="🚇",
    layout="wide"
)

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
    background: #F1F7FF;
    color: #172554;
}

.block-container {
    max-width: 1000px;
    padding-top: 30px;
    padding-bottom: 50px;
}

h1, h2, h3 {
    color: #123B72;
}

div[data-testid="stTextInput"] input {
    border: 1px solid #BFDBFE;
    border-radius: 12px;
    min-height: 48px;
    background: white;
    color: #172554;
}

div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #1D4ED8, #0284C7);
    border: none;
    border-radius: 12px;
    color: white;
    font-size: 16px;
    font-weight: 800;
    min-height: 48px;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #BFDBFE;
    border-radius: 15px;
    padding: 14px;
}

div[data-testid="stExpander"] {
    background: white;
    border: 1px solid #BFDBFE;
    border-radius: 12px;
}

hr {
    border-color: #DBEAFE;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# 역 이름 정리
# ==================================================

def 역이름키(이름):
    이름 = re.sub(r"\s+", "", str(이름))

    if 이름 in ("서울", "서울역"):
        return "서울역"

    if 이름.endswith("역") and len(이름) > 1:
        이름 = 이름[:-1]

    return 이름


def 역이름표시(node, 역정보):
    정보 = 역정보.get(str(node))

    if not 정보:
        return "역 이름 확인 필요"

    이름 = str(정보.get("name", "")).strip()

    if not 이름 or 이름.isdigit():
        return "역 이름 확인 필요"

    if 이름 == "서울":
        return "서울역"

    if 이름 == "서울역":
        return "서울역"

    if 이름.endswith("역"):
        return 이름

    return 이름 + "역"


# ==================================================
# 역 사이 거리 계산
# ==================================================

def 두역거리(a, b):

    if (
        a["lat"] is None
        or a["lng"] is None
        or b["lat"] is None
        or b["lng"] is None
    ):
        return float("inf")

    반지름 = 6371000

    위도1 = math.radians(a["lat"])
    위도2 = math.radians(b["lat"])

    위도차 = math.radians(b["lat"] - a["lat"])
    경도차 = math.radians(b["lng"] - a["lng"])

    값 = (
        (1 - math.cos(위도차)) / 2
        + math.cos(위도1)
        * math.cos(위도2)
        * (1 - math.cos(경도차)) / 2
    )

    값 = min(1, max(0, 값))

    return 2 * 반지름 * math.asin(값 ** 0.5)


# ==================================================
# 네이버 지도 URL
# ==================================================

def 네이버지도용좌표(lat, lng):

    if lat is None or lng is None:
        return None, None

    x = lng * 20037508.34 / 180

    y = math.log(
        math.tan((90 + lat) * math.pi / 360)
    ) / (math.pi / 180)

    y = y * 20037508.34 / 180

    return x, y


def 네이버지도경로URL(출발노드, 도착노드, 역정보):

    출발 = 역정보.get(str(출발노드))
    도착 = 역정보.get(str(도착노드))

    if not 출발 or not 도착:
        return None

    sx, sy = 네이버지도용좌표(
        출발.get("lat"),
        출발.get("lng")
    )

    dx, dy = 네이버지도용좌표(
        도착.get("lat"),
        도착.get("lng")
    )

    if None in (sx, sy, dx, dy):
        return None

    출발이름 = quote(
        역이름표시(출발노드, 역정보),
        safe=""
    )

    도착이름 = quote(
        역이름표시(도착노드, 역정보),
        safe=""
    )

    return (
        "https://map.naver.com/p/directions/"
        f"{sx:.3f},{sy:.3f},{출발이름}/"
        f"{dx:.3f},{dy:.3f},{도착이름}/-/transit"
        "?c=13.00,0,0,0,dh"
    )


# ==================================================
# 지하철 데이터 불러오기
# ==================================================

@st.cache_data(ttl=86400)
def 데이터불러오기():

    def csv읽기(url):

        response = requests.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        return pd.read_csv(
            StringIO(
                response.content.decode("utf-8-sig")
            ),
            dtype=str,
            keep_default_na=False
        )

    역자료 = csv읽기(STATION_URL)
    구간자료 = csv읽기(SECTION_URL)

    역정보 = {}
    역코드표 = {}
    노선별역표 = {}

    # 역 정보
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

    # 역 연결 그래프
    그래프 = {
        node: set()
        for node in 역정보
    }

    def 연결(a, b, 이동수=1, 환승수=0):

        if a == b:
            return

        if a not in 그래프 or b not in 그래프:
            return

        그래프[a].add(
            (b, 이동수, 환승수)
        )

        그래프[b].add(
            (a, 이동수, 환승수)
        )

    # 인접 역 연결
    for row in 구간자료.to_dict("records"):

        line = row.get("line", "").strip()

        code_a = row.get(
            "up_station_code", ""
        ).strip()

        code_b = row.get(
            "down_station_code", ""
        ).strip()

        name_a = row.get(
            "up_station_name", ""
        ).strip()

        name_b = row.get(
            "down_station_name", ""
        ).strip()

        a = 역코드표.get((line, code_a))
        b = 역코드표.get((line, code_b))

        if not a:

            candidates = 노선별역표.get(
                (line, 역이름키(name_a)),
                []
            )

            if candidates:
                a = candidates[0]

        if not b:

            candidates = 노선별역표.get(
                (line, 역이름키(name_b)),
                []
            )

            if candidates:
                b = candidates[0]

        if a and b:
            연결(a, b, 1, 0)

    # 환승 연결
    이름별노드 = {}

    for node, info in 역정보.items():

        key = 역이름키(info["name"])

        이름별노드.setdefault(
            key,
            []
        ).append(node)

    for nodes in 이름별노드.values():

        for a, b in combinations(nodes, 2):

            if 역정보[a]["line"] == 역정보[b]["line"]:
                continue

            if 두역거리(
                역정보[a],
                역정보[b]
            ) <= 500:

                연결(a, b, 0, 1)

    역검색표 = {
        key: sorted(set(nodes))
        for key, nodes in 이름별노드.items()
    }

    return 역정보, 그래프, 역검색표


# ==================================================
# 경로 계산
# ==================================================

def 경로찾기(
    출발노드들,
    도착노드들,
    그래프,
    기준
):

    거리표 = {}
    이전역표 = {}
    대기열 = []

    for node in 출발노드들:

        거리표[node] = (0, 0)

        heapq.heappush(
            대기열,
            (0, 0, node)
        )

    목적지노드 = None

    while 대기열:

        비용1, 비용2, 현재 = heapq.heappop(
            대기열
        )

        if 거리표.get(현재) != (비용1, 비용2):
            continue

        if 현재 in 도착노드들:
            목적지노드 = 현재
            break

        for 다음, 추가이동, 추가환승 in sorted(
            그래프[현재]
        ):

            if 기준 == "최소 환승":

                새비용 = (
                    비용1 + 추가환승,
                    비용2 + 추가이동
                )

            else:

                새비용 = (
                    비용1 + 추가이동,
                    비용2 + 추가환승
                )

            기존비용 = 거리표.get(
                다음,
                (float("inf"), float("inf"))
            )

            if 새비용 < 기존비용:

                거리표[다음] = 새비용
                이전역표[다음] = 현재

                heapq.heappush(
                    대기열,
                    (새비용[0], 새비용[1], 다음)
                )

    if 목적지노드 is None:
        return None

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
# 경로를 노선별로 구분
# ==================================================

def 구간나누기(경로, 역정보):

    구간들 = []

    for node in 경로:

        노선 = 역정보[node]["line"]

        if (
            not 구간들
            or 구간들[-1]["line"] != 노선
        ):

            구간들.append({
                "line": 노선,
                "nodes": [node]
            })

        else:

            구간들[-1]["nodes"].append(node)

    return 구간들


# ==================================================
# 화면 제목
# ==================================================

st.title("🚇 BLUE ROUTE")
st.caption("파란색 테마의 지하철 길찾기")


# ==================================================
# 데이터 불러오기
# ==================================================

try:

    with st.spinner("지하철 정보를 불러오는 중..."):

        역정보, 그래프, 역검색표 = 데이터불러오기()

except Exception as e:

    st.error(
        "지하철 데이터를 불러오지 못했어. "
        "인터넷 연결이나 데이터 주소를 확인해 줘."
    )

    st.caption(str(e))

    st.stop()


# ==================================================
# 출발역과 도착역 입력
# ==================================================

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
        horizontal=True
    )

    검색버튼 = st.form_submit_button(
        "🔎 경로 찾기",
        use_container_width=True
    )


# ==================================================
# 결과 출력
# ==================================================

if 검색버튼:

    출발키 = 역이름키(출발입력)
    도착키 = 역이름키(도착입력)

    if (
        not 출발입력.strip()
        or not 도착입력.strip()
    ):

        st.warning(
            "출발역과 도착역을 모두 입력해 줘."
        )

    elif 출발키 == 도착키:

        st.info(
            "출발역과 도착역이 같아."
        )

    elif 출발키 not in 역검색표:

        st.error(
            f"'{출발입력}' 역을 데이터에서 찾을 수 없어."
        )

    elif 도착키 not in 역검색표:

        st.error(
            f"'{도착입력}' 역을 데이터에서 찾을 수 없어."
        )

    else:

        경로 = 경로찾기(
            역검색표[출발키],
            set(역검색표[도착키]),
            그래프,
            기준
        )

        if not 경로:

            st.error(
                "연결된 경로를 찾지 못했어."
            )

        else:

            구간들 = 구간나누기(
                경로,
                역정보
            )

            총이동역수 = sum(
                len(구간["nodes"]) - 1
                for 구간 in 구간들
            )

            총환승횟수 = sum(
                역정보[a]["line"] != 역정보[b]["line"]
                for a, b in zip(
                    경로,
                    경로[1:]
                )
            )

            # ------------------------------
            # 경로 요약
            # ------------------------------

            st.divider()
            st.subheader("🧭 이동 경로")

            st.markdown(
                f"## {역이름표시(경로[0], 역정보)} → "
                f"{역이름표시(경로[-1], 역정보)}"
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

            음성문장 = [
                f"{역이름표시(경로[0], 역정보)}에서 출발합니다."
            ]

            # ------------------------------
            # 노선별 이동 경로
            # ------------------------------

            for i, 구간 in enumerate(구간들):

                노선 = 구간["line"]
                역목록 = 구간["nodes"]

                첫역 = 역이름표시(
                    역목록[0],
                    역정보
                )

                마지막역 = 역이름표시(
                    역목록[-1],
                    역정보
                )

                with st.container(border=True):

                    st.markdown(
                        f"### 🔵 {노선}"
                    )

                    st.markdown(
                        f"**{첫역} → {마지막역}**"
                    )

                    st.caption(
                        f"이 구간 이동 역 수: "
                        f"{max(0, len(역목록) - 1)}개"
                    )

                    st.write("**정차역**")

                    st.write(
                        " → ".join(
                            역이름표시(
                                node,
                                역정보
                            )
                            for node in 역목록
                        )
                    )

                음성문장.append(
                    f"{노선}을 타고 "
                    f"{마지막역}까지 이동하세요."
                )

                if i < len(구간들) - 1:

                    다음노선 = 구간들[i + 1]["line"]

                    st.info(
                        f"🔄 {마지막역}에서 "
                        f"{다음노선}으로 환승하세요."
                    )

                    음성문장.append(
                        f"{마지막역}에서 "
                        f"{다음노선}으로 환승하세요."
                    )

            음성문장.append(
                f"{역이름표시(경로[-1], 역정보)}에 "
                f"도착했습니다."
            )

            # ------------------------------
            # 전체 정차역
            # ------------------------------

            st.divider()
            st.subheader("📍 전체 이동 순서")

            전체역목록 = []

            for node in 경로:

                이름 = 역이름표시(
                    node,
                    역정보
                )

                if 전체역목록:

                    if (
                        역이름키(전체역목록[-1])
                        == 역이름키(이름)
                    ):
                        continue

                전체역목록.append(이름)

            with st.container(border=True):

                for 번호, 이름 in enumerate(
                    전체역목록,
                    start=1
                ):

                    st.markdown(
                        f"**{번호}. {이름}**"
                    )

            # ------------------------------
            # 네이버 지도
            # ------------------------------

            st.divider()
            st.subheader("🗺️ 네이버 지도")

            네이버URL = 네이버지도경로URL(
                경로[0],
                경로[-1],
                역정보
            )

            if 네이버URL:

                st.link_button(
                    "🗺️ 네이버 지도에서 확대해서 보기",
                    네이버URL,
                    use_container_width=True
                )

                st.caption(
                    "네이버 지도에서 출발역과 도착역의 "
                    "대중교통 경로를 크게 볼 수 있어."
                )

            else:

                st.warning(
                    "역 좌표를 확인할 수 없어서 "
                    "네이버 지도 링크를 만들지 못했어."
                )

            # ------------------------------
            # 음성 안내
            # ------------------------------

            st.divider()
            st.subheader("🔊 음성 안내")

            음성텍스트 = " ".join(음성문장)

            음성문장JS = json.dumps(
                음성텍스트,
                ensure_ascii=False
            )

            components.html(
                f"""
                <div style="
                    display:flex;
                    gap:10px;
                    width:100%;
                ">
                    <button id="speakBtn"
                        style="
                            flex:1;
                            padding:15px;
                            border:none;
                            border-radius:12px;
                            background:linear-gradient(
                                90deg,#1D4ED8,#0284C7
                            );
                            color:white;
                            font-size:15px;
                            font-weight:800;
                            cursor:pointer;
                        ">
                        🔊 음성 안내 듣기
                    </button>

                    <button id="stopBtn"
                        style="
                            width:110px;
                            padding:15px;
                            border:1px solid #BFDBFE;
                            border-radius:12px;
                            background:white;
                            color:#1E3A8A;
                            font-size:15px;
                            font-weight:800;
                            cursor:pointer;
                        ">
                        ■ 정지
                    </button>
                </div>

                <div id="voiceStatus"
                    style="
                        margin-top:8px;
                        text-align:center;
                        color:#475569;
                        font-size:13px;
                    ">
                    버튼을 누르면 음성 안내가 시작돼.
                </div>

                <script>
                    const routeText = {음성문장JS};

                    const speakBtn =
                        document.getElementById("speakBtn");

                    const stopBtn =
                        document.getElementById("stopBtn");

                    const voiceStatus =
                        document.getElementById("voiceStatus");

                    let chunks = [];
                    let currentChunk = 0;

                    // 긴 문장을 나눠서 재생
                    function makeChunks(text) {{

                        const sentences = text.split(
                            /(?<=[.!?])\\s+/
                        );

                        const result = [];
                        let current = "";

                        for (const sentence of sentences) {{

                            if (
                                (current + " " + sentence)
                                .trim().length > 180
                            ) {{

                                if (current.trim()) {{
                                    result.push(current.trim());
                                }}

                                current = sentence;

                            }} else {{

                                current = (
                                    current + " " + sentence
                                ).trim();

                            }}
                        }}

                        if (current.trim()) {{
                            result.push(current.trim());
                        }}

                        return result;
                    }}

                    // 한국어 음성 찾기
                    function getKoreanVoice() {{

                        const voices =
                            window.speechSynthesis.getVoices();

                        return (
                            voices.find(v =>
                                v.lang &&
                                v.lang.toLowerCase() === "ko-kr"
                            ) ||

                            voices.find(v =>
                                v.lang &&
                                v.lang.toLowerCase().startsWith("ko")
                            ) ||

                            voices[0]
                        );
                    }}

                    // 다음 문장 재생
                    function speakNext() {{

                        if (currentChunk >= chunks.length) {{

                            voiceStatus.textContent =
                                "음성 안내가 끝났어.";

                            return;
                        }}

                        const speech =
                            new SpeechSynthesisUtterance(
                                chunks[currentChunk]
                            );

                        const voice = getKoreanVoice();

                        if (voice) {{
                            speech.voice = voice;
                        }}

                        speech.lang = "ko-KR";
                        speech.rate = 0.88;
                        speech.pitch = 1.0;
                        speech.volume = 1.0;

                        speech.onstart = function() {{

                            voiceStatus.textContent =
                                "음성 안내 중... " +
                                (currentChunk + 1) +
                                " / " +
                                chunks.length;

                        }};

                        speech.onend = function() {{

                            currentChunk++;
                            speakNext();

                        }};

                        speech.onerror = function() {{

                            voiceStatus.textContent =
                                "음성 재생에 실패했어. 다시 눌러줘.";

                        }};

                        window.speechSynthesis.speak(
                            speech
                        );
                    }}

                    // 음성 시작
                    speakBtn.onclick = function() {{

                        if (!("speechSynthesis" in window)) {{

                            voiceStatus.textContent =
                                "현재 브라우저에서 음성 기능을 지원하지 않아.";

                            return;
                        }}

                        window.speechSynthesis.cancel();

                        chunks = makeChunks(routeText);
                        currentChunk = 0;

                        setTimeout(function() {{
                            speakNext();
                        }}, 100);
                    }};

                    // 음성 정지
                    stopBtn.onclick = function() {{

                        if ("speechSynthesis" in window) {{

                            window.speechSynthesis.cancel();

                        }}

                        currentChunk = chunks.length;

                        voiceStatus.textContent =
                            "음성 안내를 정지했어.";
                    }};

                    // 브라우저 음성 목록 불러오기
                    if ("speechSynthesis" in window) {{

                        window.speechSynthesis.onvoiceschanged =
                            function() {{

                                window.speechSynthesis.getVoices();

                            }};
                    }}
                </script>
                """,
                height=125
            )

            # ------------------------------
            # 주의 사항
            # ------------------------------

            with st.expander("경로 안내 주의 사항"):

                st.write(
                    "역 코드는 내부 경로 계산에만 사용하고, "
                    "화면에는 한글 역 이름을 표시해."
                )

                st.write(
                    "경로 정확도는 공개 데이터의 역 연결 정보에 "
                    "따라 달라질 수 있어. "
                    "실시간 열차 운행이나 급행 정보는 "
                    "반영되지 않을 수 있어."
                )

else:

    st.info(
        "출발역과 도착역을 입력한 다음 "
        "경로 찾기를 눌러 줘."
    )
