import heapq
import json
import math
import re
from io import StringIO

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="BLUE ROUTE | 지하철 길찾기",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

STATION_URL = "https://raw.githubusercontent.com/minseok852/subway-etl/main/output/station_nodes.csv"
EDGE_URL = "https://raw.githubusercontent.com/minseok852/subway-etl/main/output/station_edges.csv"

HEADERS = {"User-Agent": "BlueRoute-Streamlit/1.0"}

LINE_NAMES = {
    "1": "1호선", "2": "2호선", "3": "3호선", "4": "4호선",
    "5": "5호선", "6": "6호선", "7": "7호선", "8": "8호선",
    "9": "9호선", "B": "수인분당선", "S": "신분당선",
    "K": "경의·중앙선", "A": "공항철도", "G": "경춘선",
    "U": "의정부경전철", "E": "용인에버라인", "KK": "경강선",
    "W": "우이신설선", "SH": "서해선", "KP": "김포골드라인",
    "I": "인천1호선", "I2": "인천2호선", "GTXA": "GTX-A",
    "N": "신림선", "M": "인천공항 자기부상철도",
}

LINE_COLORS = {
    "1": "#0052A4", "2": "#00A84D", "3": "#EF7C1C",
    "4": "#00A5DE", "5": "#996CAC", "6": "#CD7C2F",
    "7": "#747F00", "8": "#E6186C", "9": "#BDB092",
    "B": "#F5A200", "S": "#D31145", "K": "#77C4A3",
    "A": "#0090D2", "G": "#178C72", "U": "#B7C450",
    "E": "#FFCD00", "KK": "#003DA5", "W": "#B7B7B7",
    "SH": "#F06A00", "KP": "#8B50A4", "I": "#759C2A",
    "I2": "#F5A100", "GTXA": "#3B82F6", "N": "#B0CE18",
    "M": "#777777",

    "수인분당선": "#F5A200",
    "신분당선": "#D31145",
    "경의·중앙선": "#77C4A3",
    "경춘선": "#178C72",
    "인천국제공항선": "#0090D2",
    "의정부": "#B7C450",
    "용인에버라인": "#FFCD00",
    "경강선": "#003DA5",
    "우이신설선": "#B7B7B7",
    "서해선": "#F06A00",
    "김포골드라인": "#8B50A4",
    "인천지하철 1호선": "#759C2A",
    "인천지하철 2호선": "#F5A100",
    "자기부상철도": "#777777",
    "GTX-A": "#3B82F6",
    "신림선": "#B0CE18",
}


def 노선이름(line_key):
    key = str(line_key).strip()
    return LINE_NAMES.get(key, key)


def 노선색(line_key):
    return LINE_COLORS.get(str(line_key), "#2563EB")


# =========================================================
# 파란색 디자인
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #F2F7FF 0%, #F8FBFF 100%);
        color: #172554;
    }

    .block-container {
        max-width: 1050px;
        padding-top: 28px;
        padding-bottom: 48px;
    }

    .hero {
        padding: 30px 32px;
        border-radius: 24px;
        background: linear-gradient(120deg, #102A56 0%, #1768C4 62%, #38BDF8 100%);
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 12px 28px rgba(29, 78, 216, .15);
    }

    .hero-title {
        color: white;
        font-size: 35px;
        font-weight: 900;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        color: #DBEEFF;
        font-size: 14px;
        line-height: 1.7;
        margin-top: 8px;
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
        min-height: 50px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #BFDBFE;
        border-radius: 15px;
        padding: 10px;
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B;
    }

    .route-heading {
        color: #123B72;
        font-size: 24px;
        font-weight: 900;
        padding: 20px;
        border-radius: 16px;
        background: linear-gradient(120deg, #DBEAFE, #E0F2FE);
        border: 1px solid #BFDBFE;
        margin: 12px 0 18px 0;
    }

    .transfer-note {
        background: #E0F2FE;
        border-left: 5px solid #0284C7;
        border-radius: 10px;
        padding: 12px 15px;
        margin: 8px 0 14px 0;
        color: #075985;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 역 이름 정리
# 비슷한 역 검색, 일부 글자 검색, 자동 추천 없음
# =========================================================
def 역이름키(name):
    value = re.sub(r"\s+", "", str(name or "").strip())

    if value.endswith("역"):
        value = value[:-1]

    return value


def 역이름표시(node_id, nodes):
    name = nodes[str(node_id)]["name"]

    return name if name.endswith("역") else f"{name}역"


# =========================================================
# 지하철 데이터 불러오기
# =========================================================
@st.cache_data(ttl=86400, show_spinner=False)
def 데이터불러오기():

    station_response = requests.get(
        STATION_URL,
        headers=HEADERS,
        timeout=30
    )

    station_response.raise_for_status()

    edge_response = requests.get(
        EDGE_URL,
        headers=HEADERS,
        timeout=30
    )

    edge_response.raise_for_status()

    station_df = pd.read_csv(
        StringIO(
            station_response.content.decode("utf-8-sig")
        ),
        dtype=str,
        keep_default_na=False
    )

    edge_df = pd.read_csv(
        StringIO(
            edge_response.content.decode("utf-8-sig")
        ),
        dtype=str,
        keep_default_na=False
    )

    station_required = {
        "id",
        "station_name",
        "line_key",
        "lat",
        "lon"
    }

    edge_required = {
        "from_node_id",
        "to_node_id",
        "seconds",
        "edge_type"
    }

    if not station_required.issubset(station_df.columns):
        raise ValueError(
            "역 데이터의 열 이름이 예상한 형식과 달라."
        )

    if not edge_required.issubset(edge_df.columns):
        raise ValueError(
            "구간 데이터의 열 이름이 예상한 형식과 달라."
        )

    nodes = {}
    station_index = {}

    # 역 정보 저장
    for row in station_df.to_dict("records"):

        node_id = str(row["id"]).strip()
        name = str(row["station_name"]).strip()
        line_key = str(row["line_key"]).strip()

        if not node_id or not name or not line_key:
            continue

        try:
            lat = float(row["lat"])
            lon = float(row["lon"])

        except (TypeError, ValueError):
            lat, lon = None, None

        nodes[node_id] = {
            "name": name,
            "line_key": line_key,
            "line": 노선이름(line_key),
            "lat": lat,
            "lon": lon
        }

        key = 역이름키(name)

        station_index.setdefault(
            key,
            []
        ).append(node_id)

    # 실제 데이터에 저장된 이동 방향을 사용
    graph = {
        node_id: []
        for node_id in nodes
    }

    for row in edge_df.to_dict("records"):

        a = str(row["from_node_id"]).strip()
        b = str(row["to_node_id"]).strip()

        if a not in nodes or b not in nodes:
            continue

        try:
            seconds = float(row["seconds"])

        except (TypeError, ValueError):
            continue

        edge_type = str(
            row["edge_type"]
        ).strip().upper()

        if edge_type not in {"RIDE", "TRANSFER"}:
            continue

        graph[a].append(
            (b, seconds, edge_type)
        )

    return nodes, graph, station_index


# =========================================================
# 역명 정확히 확인
# 좌표가 아닌 실제 환승 연결로 같은 역 판단
# =========================================================
def 정확한역찾기(query, nodes, station_index, graph):

    key = 역이름키(query)

    if not key:
        return None, "역 이름을 입력해 줘."

    # 완전 일치만 확인
    # 비슷한 이름 검색이나 자동 추천은 하지 않음
    matches = station_index.get(key, [])

    if not matches:
        return None, (
            f"'{query}' 역을 찾을 수 없어. "
            "역 이름을 정확히 입력해 줘."
        )

    # 실제 환승 간선으로 노선별 역을 연결
    match_set = set(matches)

    transfer_neighbors = {
        node_id: set()
        for node_id in matches
    }

    for node_id in matches:

        for next_id, _seconds, edge_type in graph.get(node_id, []):

            if (
                edge_type == "TRANSFER"
                and next_id in match_set
            ):

                transfer_neighbors[node_id].add(
                    next_id
                )

                transfer_neighbors[next_id].add(
                    node_id
                )

    groups = []
    remaining = set(matches)

    while remaining:

        root = remaining.pop()

        stack = [root]
        group = [root]

        while stack:

            current = stack.pop()

            for neighbor in transfer_neighbors[current]:

                if neighbor in remaining:

                    remaining.remove(neighbor)
                    group.append(neighbor)
                    stack.append(neighbor)

        groups.append(group)

    # 서로 연결되지 않은 동명이역은 임의로 선택하지 않음
    if len(groups) > 1:

        return None, (
            f"'{query}'이라는 이름의 역이 여러 곳에 있어. "
            "잘못된 역을 선택하지 않도록 검색을 중단했어."
        )

    return groups[0], None


# =========================================================
# 다익스트라 경로 찾기
# =========================================================
def 경로찾기(start_nodes, goal_nodes, graph, 기준):

    def 우선순위(환승수, 이동수, 초):

        if 기준 == "최소 환승":
            return (환승수, 이동수, 초)

        if 기준 == "최단 역 수":
            return (이동수, 환승수, 초)

        return (초, 환승수, 이동수)

    best = {}
    metrics = {}
    previous = {}
    previous_edge = {}

    heap = []

    for start in start_nodes:

        metrics[start] = (0, 0, 0.0)

        best[start] = 우선순위(
            0,
            0,
            0.0
        )

        heapq.heappush(
            heap,
            (best[start], start)
        )

    destination = None

    while heap:

        current_priority, current = heapq.heappop(heap)

        if current_priority != best.get(current):
            continue

        if current in goal_nodes:

            destination = current
            break

        old_transfer, old_ride, old_seconds = metrics[current]

        for nxt, seconds, edge_type in graph.get(current, []):

            if edge_type not in {"RIDE", "TRANSFER"}:
                continue

            is_transfer = edge_type == "TRANSFER"

            new_transfer = (
                old_transfer + (1 if is_transfer else 0)
            )

            new_ride = (
                old_ride + (1 if edge_type == "RIDE" else 0)
            )

            new_seconds = old_seconds + seconds

            new_metrics = (
                new_transfer,
                new_ride,
                new_seconds
            )

            new_priority = 우선순위(
                *new_metrics
            )

            if new_priority < best.get(
                nxt,
                (float("inf"),) * 3
            ):

                best[nxt] = new_priority
                metrics[nxt] = new_metrics

                previous[nxt] = current
                previous_edge[nxt] = edge_type

                heapq.heappush(
                    heap,
                    (new_priority, nxt)
                )

    if destination is None:
        return None

    path = [destination]
    edge_types = []

    current = destination

    while current in previous:

        edge_types.append(
            previous_edge[current]
        )

        current = previous[current]
        path.append(current)

    path.reverse()
    edge_types.reverse()

    total_seconds = metrics[destination][2]

    return {
        "path": path,
        "edge_types": edge_types,
        "total_seconds": total_seconds,
        "transfer_count": metrics[destination][0],
        "ride_count": metrics[destination][1]
    }


# =========================================================
# 실제 간선 종류에 따라 경로 단계 만들기
# RIDE = 열차 이동
# TRANSFER = 환승
# =========================================================
def 경로단계만들기(path, edge_types, nodes):

    steps = []
    active = None

    for index, edge_type in enumerate(edge_types):

        from_id = path[index]
        to_id = path[index + 1]

        from_info = nodes[from_id]
        to_info = nodes[to_id]

        if edge_type == "TRANSFER":

            if active is not None:

                steps.append(active)
                active = None

            steps.append({
                "type": "transfer",
                "station": 역이름표시(from_id, nodes),
                "from_line": 노선이름(
                    from_info["line_key"]
                ),
                "to_line": 노선이름(
                    to_info["line_key"]
                )
            })

        elif edge_type == "RIDE":

            from_line_key = from_info["line_key"]
            to_line_key = to_info["line_key"]

            if active is None:

                active = {
                    "type": "ride",
                    "line_key": from_line_key,
                    "line": 노선이름(from_line_key),
                    "color": 노선색(from_line_key),
                    "nodes": [from_id, to_id]
                }

            elif (
                active["line_key"] == from_line_key
                and active["nodes"][-1] == from_id
            ):

                active["nodes"].append(to_id)

            else:

                steps.append(active)

                active = {
                    "type": "ride",
                    "line_key": from_line_key,
                    "line": 노선이름(from_line_key),
                    "color": 노선색(from_line_key),
                    "nodes": [from_id, to_id]
                }

            # RIDE로 연결된 노선 키가 달라지는 특수 구간 처리
            if to_line_key != active["line_key"]:

                steps.append(active)

                active = {
                    "type": "ride",
                    "line_key": to_line_key,
                    "line": 노선이름(to_line_key),
                    "color": 노선색(to_line_key),
                    "nodes": [to_id]
                }

    if active is not None:
        steps.append(active)

    return steps


# =========================================================
# 음성 안내 문장 만들기
# =========================================================
def 음성문장만들기(steps, nodes, destination_id):

    phrases = []
    ride_number = 0

    for step in steps:

        if step["type"] == "ride":

            if len(step["nodes"]) < 2:
                continue

            ride_number += 1

            start_name = 역이름표시(
                step["nodes"][0],
                nodes
            )

            end_name = 역이름표시(
                step["nodes"][-1],
                nodes
            )

            if ride_number == 1:

                phrases.append(
                    f"{start_name}에서 "
                    f"{step['line']}을 타고 "
                    f"{end_name}까지 이동합니다."
                )

            else:

                phrases.append(
                    f"이어서 {step['line']}을 타고 "
                    f"{end_name}까지 이동합니다."
                )

        elif step["type"] == "transfer":

            phrases.append(
                f"{step['station']}에서 "
                f"{step['from_line']}에서 "
                f"{step['to_line']}으로 환승합니다."
            )

    if ride_number == 0:
        return "경로를 안내할 수 없습니다."

    phrases.append(
        f"{역이름표시(destination_id, nodes)}에 도착했습니다."
    )

    return " ".join(phrases)


# =========================================================
# 지도 HTML
# =========================================================
def 지도HTML(path, nodes):

    points = []

    for node_id in path:

        info = nodes[node_id]

        if (
            info["lat"] is not None
            and info["lon"] is not None
        ):

            points.append([
                info["lat"],
                info["lon"]
            ])

    if not points:
        return None

    points_json = json.dumps(
        points,
        ensure_ascii=False
    )

    start_name_json = json.dumps(
        역이름표시(path[0], nodes),
        ensure_ascii=False
    )

    end_name_json = json.dumps(
        역이름표시(path[-1], nodes),
        ensure_ascii=False
    )

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">

      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      >

      <style>
        html, body {{ margin:0; padding:0; }}
        #map {{ width:100%; height:420px; border-radius:16px; }}
      </style>
    </head>

    <body>

      <div id="map"></div>

      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

      <script>

        const points = {points_json};
        const startName = {start_name_json};
        const endName = {end_name_json};

        const map = L.map('map');

        L.tileLayer(
            'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
            {{
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap'
            }}
        ).addTo(map);

        const routeLine = L.polyline(
            points,
            {{
                color: '#2563EB',
                weight: 6,
                opacity: 0.88
            }}
        ).addTo(map);

        L.circleMarker(
            points[0],
            {{
                radius: 9,
                color: '#FFFFFF',
                weight: 3,
                fillColor: '#16A34A',
                fillOpacity: 1
            }}
        )
        .addTo(map)
        .bindPopup('출발: ' + startName);

        L.circleMarker(
            points[points.length - 1],
            {{
                radius: 9,
                color: '#FFFFFF',
                weight: 3,
                fillColor: '#DC2626',
                fillOpacity: 1
            }}
        )
        .addTo(map)
        .bindPopup('도착: ' + endName);

        if (points.length > 1) {{

            map.fitBounds(
                routeLine.getBounds(),
                {{
                    padding: [25, 25]
                }}
            );

        }} else {{

            map.setView(points[0], 15);

        }}

      </script>

    </body>
    </html>
    """


# =========================================================
# 음성 안내 컴포넌트
# =========================================================
def 음성버튼HTML(text):

    text_json = json.dumps(
        text,
        ensure_ascii=False
    )

    return f"""
    <div style="display:flex; gap:10px;">

      <button onclick="speakRoute()" style="
        flex:1;
        height:52px;
        border:0;
        border-radius:12px;
        background:linear-gradient(90deg,#1D4ED8,#0284C7);
        color:white;
        font-size:16px;
        font-weight:800;
        cursor:pointer;
      ">
        🔊 경로 읽어주기
      </button>

      <button onclick="stopRoute()" style="
        width:110px;
        height:52px;
        border:1px solid #BFDBFE;
        border-radius:12px;
        background:#EFF6FF;
        color:#1E3A8A;
        font-size:14px;
        font-weight:700;
        cursor:pointer;
      ">
        ■ 중지
      </button>

    </div>

    <script>

      const routeText = {text_json};

      function getSpeechObjects() {{

        let synth = window.speechSynthesis;
        let Utterance = window.SpeechSynthesisUtterance;

        try {{

          if (
            window.parent
            && window.parent.speechSynthesis
          ) {{

            synth = window.parent.speechSynthesis;

            Utterance =
                window.parent.SpeechSynthesisUtterance
                || Utterance;

          }}

        }} catch (error) {{}}

        return {{
            synth,
            Utterance
        }};

      }}

      function speakRoute() {{

        const objects = getSpeechObjects();

        if (!objects.synth || !objects.Utterance) {{

            alert(
                '이 브라우저에서는 음성 안내를 지원하지 않습니다.'
            );

            return;
        }}

        objects.synth.cancel();

        const utterance =
            new objects.Utterance(routeText);

        utterance.lang = 'ko-KR';
        utterance.rate = 0.88;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        objects.synth.speak(utterance);

      }}

      function stopRoute() {{

        const objects = getSpeechObjects();

        if (objects.synth) {{
            objects.synth.cancel();
        }}

      }}

    </script>
    """


# =========================================================
# 앱 화면
# =========================================================
st.markdown(
    """
    <div class="hero">

      <div class="hero-title">
        🚇 BLUE ROUTE
      </div>

      <div class="hero-subtitle">
        출발역과 도착역을 입력하면 지하철 이동 경로를 안내합니다.<br>
        비슷한 역 검색이나 자동 추천 없이 입력한 역 이름만 정확히 확인합니다.
      </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 데이터 불러오기
# =========================================================
try:

    with st.spinner(
        "지하철 정보를 불러오는 중..."
    ):

        역정보, 그래프, 역검색표 = 데이터불러오기()

except Exception as error:

    st.error(
        "지하철 데이터를 불러오지 못했어. 잠시 후 다시 실행해 줘."
    )

    st.caption(
        f"오류 내용: {error}"
    )

    st.stop()


# =========================================================
# 세션 상태
# =========================================================
if "route_result" not in st.session_state:
    st.session_state.route_result = None

if "route_error" not in st.session_state:
    st.session_state.route_error = None


# =========================================================
# 검색창
# =========================================================
with st.form("route_form"):

    st.subheader(
        "어디로 이동할까요?"
    )

    col1, col2 = st.columns(2)

    with col1:

        출발입력 = st.text_input(
            "🔵 출발역",
            placeholder="예: 강남역"
        )

    with col2:

        도착입력 = st.text_input(
            "🔷 도착역",
            placeholder="예: 홍대입구역"
        )

    기준 = st.radio(
        "경로 기준",
        [
            "최소 환승",
            "최단 역 수",
            "최단 시간"
        ],
        horizontal=True
    )

    검색버튼 = st.form_submit_button(
        "🔎 경로 찾기",
        use_container_width=True
    )


# =========================================================
# 경로 검색
# =========================================================
if 검색버튼:

    st.session_state.route_result = None
    st.session_state.route_error = None

    if (
        not 출발입력.strip()
        or not 도착입력.strip()
    ):

        st.session_state.route_error = (
            "출발역과 도착역을 모두 입력해 줘."
        )

    elif (
        역이름키(출발입력)
        == 역이름키(도착입력)
    ):

        st.session_state.route_error = (
            "출발역과 도착역이 같아."
        )

    else:

        출발노드들, 출발오류 = 정확한역찾기(
            출발입력,
            역정보,
            역검색표,
            그래프
        )

        도착노드들, 도착오류 = 정확한역찾기(
            도착입력,
            역정보,
            역검색표,
            그래프
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
                기준
            )

            if 결과 is None:

                st.session_state.route_error = (
                    "두 역 사이의 경로를 찾지 못했어."
                )

            else:

                결과["steps"] = 경로단계만들기(
                    결과["path"],
                    결과["edge_types"],
                    역정보
                )

                결과["origin_name"] = 역이름표시(
                    결과["path"][0],
                    역정보
                )

                결과["destination_name"] = 역이름표시(
                    결과["path"][-1],
                    역정보
                )

                결과["voice_text"] = 음성문장만들기(
                    결과["steps"],
                    역정보,
                    결과["path"][-1]
                )

                st.session_state.route_result = 결과


# =========================================================
# 오류 표시
# =========================================================
if st.session_state.route_error:

    st.error(
        st.session_state.route_error
    )


# =========================================================
# 경로 결과 표시
# =========================================================
if st.session_state.route_result:

    result = st.session_state.route_result

    path = result["path"]
    steps = result["steps"]

    st.markdown(
        f"""
        <div class="route-heading">
            {result['origin_name']}
            →
            {result['destination_name']}
        </div>
        """,
        unsafe_allow_html=True
    )

    total_minutes = max(
        1,
        round(result["total_seconds"] / 60)
    )

    if total_minutes < 60:

        time_text = f"약 {total_minutes}분"

    else:

        hours = total_minutes // 60
        mins = total_minutes % 60

        if mins:

            time_text = (
                f"약 {hours}시간 {mins}분"
            )

        else:

            time_text = f"약 {hours}시간"

    m1, m2, m3 = st.columns(3)

    m1.metric(
        "예상 이동 시간",
        time_text
    )

    m2.metric(
        "이동 구간",
        f"{result['ride_count']}개"
    )

    m3.metric(
        "환승 횟수",
        f"{result['transfer_count']}회"
    )

    # -----------------------------------------------------
    # 노선별 이동 경로
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "🧭 이동 경로"
    )

    for step in steps:

        if step["type"] == "ride":

            station_names = [
                역이름표시(node_id, 역정보)
                for node_id in step["nodes"]
            ]

            # 이동한 역이 두 개 이상인 탑승 구간만 표시
            if len(station_names) >= 2:

                st.markdown(
                    f"""
                    <div style="
                        border:1px solid #BFDBFE;
                        background:white;
                        border-radius:15px;
                        padding:17px;
                        margin:10px 0;
                    ">

                        <div style="
                            font-size:18px;
                            font-weight:800;
                            color:{step['color']};
                        ">
                            {step['line']}
                        </div>

                        <div style="
                            margin-top:10px;
                            font-weight:700;
                            color:#1E3A8A;
                        ">
                            {station_names[0]}
                            →
                            {station_names[-1]}
                        </div>

                        <div style="
                            margin-top:10px;
                            line-height:2;
                            color:#334155;
                        ">
                            {' → '.join(station_names)}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

        elif step["type"] == "transfer":

            st.markdown(
                f"""
                <div class="transfer-note">
                    🔄 <b>{step['station']}</b>에서
                    <b>{step['from_line']}</b>에서
                    <b>{step['to_line']}</b>으로 환승하세요.
                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # 전체 이동 순서
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "📍 전체 이동 순서"
    )

    표시할역들 = []

    for node_id in path:

        station_name = 역이름표시(
            node_id,
            역정보
        )

        if (
            표시할역들
            and 역이름키(표시할역들[-1][0])
            == 역이름키(station_name)
        ):

            continue

        표시할역들.append(
            (
                station_name,
                역정보[node_id]["line"]
            )
        )

    for number, (station_name, line_name) in enumerate(
        표시할역들,
        start=1
    ):

        st.write(
            f"**{number}. {station_name}** · {line_name}"
        )

    # -----------------------------------------------------
    # 이동 지도
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "🗺️ 이동 경로 지도"
    )

    map_html = 지도HTML(
        path,
        역정보
    )

    if map_html:

        components.html(
            map_html,
            height=435,
            scrolling=False
        )

    else:

        st.info(
            "이 경로는 지도 좌표를 표시할 수 없어."
        )

    # -----------------------------------------------------
    # 음성 안내
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "🔊 음성 안내"
    )

    st.info(
        result["voice_text"]
    )

    components.html(
        음성버튼HTML(result["voice_text"]),
        height=68,
        scrolling=False
    )


# =========================================================
# 하단 안내
# =========================================================
st.caption(
    "※ 수도권 지하철 데이터 기준이며, 실제 열차 운행 상황·급행·막차 정보는 반영되지 않을 수 있어."
)
