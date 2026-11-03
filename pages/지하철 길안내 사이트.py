import heapq
import html as html_lib
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

STATION_URL = (
    "https://raw.githubusercontent.com/"
    "minseok852/subway-etl/main/output/station_nodes.csv"
)
EDGE_URL = (
    "https://raw.githubusercontent.com/"
    "minseok852/subway-etl/main/output/station_edges.csv"
)

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
    "M": "#777777", "인천국제공항선": "#0090D2",
    "수인분당선": "#F5A200", "신분당선": "#D31145",
    "경의·중앙선": "#77C4A3", "경춘선": "#178C72",
    "용인에버라인": "#FFCD00", "경강선": "#003DA5",
    "우이신설선": "#B7B7B7", "서해선": "#F06A00",
    "김포골드라인": "#8B50A4", "인천지하철 1호선": "#759C2A",
    "인천지하철 2호선": "#F5A100", "자기부상철도": "#777777",
    "GTX-A": "#3B82F6", "신림선": "#B0CE18",
}


def 노선이름(line_key):
    key = str(line_key).strip()
    return LINE_NAMES.get(key, key)


def 노선색(line_key):
    return LINE_COLORS.get(
        str(line_key).strip(),
        "#2563EB"
    )


# =========================================================
# 화면 디자인
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            180deg,
            #F2F7FF 0%,
            #F8FBFF 100%
        );
        color: #172554;
    }

    .block-container {
        max-width: 1050px;
        padding-top: 28px;
        padding-bottom: 48px;
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
        background: linear-gradient(
            90deg,
            #1D4ED8,
            #0284C7
        );
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
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 문자열 정리
# HTML 태그가 섞여 있어도 역 이름만 남김
# =========================================================
def 화면문자열(value):

    text = html_lib.unescape(
        str(value or "")
    )

    text = re.sub(
        r"(?is)<script\b[^>]*>.*?</script>",
        " ",
        text
    )

    text = re.sub(
        r"(?is)<style\b[^>]*>.*?</style>",
        " ",
        text
    )

    text = re.sub(
        r"<[^>]*>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def 역이름키(name):

    value = 화면문자열(name)

    value = re.sub(
        r"\s+",
        "",
        value
    )

    if value.endswith("역"):
        value = value[:-1]

    return value


def 역이름표시(node_id, nodes):

    name = 화면문자열(
        nodes[str(node_id)]["name"]
    )

    if not name:
        return "역 이름 확인 필요"

    return (
        name
        if name.endswith("역")
        else f"{name}역"
    )


def 좌표변환(value):

    try:
        number = float(value)

        if math.isfinite(number):
            return number

    except (TypeError, ValueError):
        pass

    return None


# =========================================================
# 지하철 데이터 불러오기
# =========================================================
@st.cache_data(
    ttl=86400,
    show_spinner=False
)
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

    try:

        station_df = pd.read_csv(
            StringIO(
                station_response.content.decode("utf-8-sig")
            ),
            dtype=str,
            keep_default_na=False,
        )

        edge_df = pd.read_csv(
            StringIO(
                edge_response.content.decode("utf-8-sig")
            ),
            dtype=str,
            keep_default_na=False,
        )

    except Exception as exc:

        raise ValueError(
            "지하철 CSV 파일을 읽지 못했어."
        ) from exc

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

    missing_station = (
        station_required - set(station_df.columns)
    )

    missing_edge = (
        edge_required - set(edge_df.columns)
    )

    if missing_station:

        raise ValueError(
            "역 데이터에 필요한 열이 없어: "
            + ", ".join(sorted(missing_station))
        )

    if missing_edge:

        raise ValueError(
            "구간 데이터에 필요한 열이 없어: "
            + ", ".join(sorted(missing_edge))
        )

    nodes = {}
    station_index = {}

    # 역 정보 저장
    for row in station_df.to_dict("records"):

        node_id = 화면문자열(
            row.get("id")
        )

        name = 화면문자열(
            row.get("station_name")
        )

        line_key = 화면문자열(
            row.get("line_key")
        )

        if not node_id or not name or not line_key:
            continue

        nodes[node_id] = {
            "name": name,
            "line_key": line_key,
            "line": 노선이름(line_key),
            "lat": 좌표변환(row.get("lat")),
            "lon": 좌표변환(row.get("lon")),
        }

        key = 역이름키(name)

        if key:

            station_index.setdefault(
                key,
                []
            ).append(node_id)

    if not nodes:

        raise ValueError(
            "역 데이터가 비어 있어."
        )

    # 이동 간선 저장
    # 원본 데이터의 방향별 소요시간을 유지함
    graph = {
        node_id: []
        for node_id in nodes
    }

    for row in edge_df.to_dict("records"):

        from_id = 화면문자열(
            row.get("from_node_id")
        )

        to_id = 화면문자열(
            row.get("to_node_id")
        )

        if (
            from_id not in nodes
            or to_id not in nodes
        ):
            continue

        seconds = 좌표변환(
            row.get("seconds")
        )

        if seconds is None or seconds < 0:
            continue

        edge_type = 화면문자열(
            row.get("edge_type")
        ).upper()

        if edge_type not in {
            "RIDE",
            "TRANSFER"
        }:
            continue

        graph[from_id].append(
            (to_id, seconds, edge_type)
        )

    if not any(graph.values()):

        raise ValueError(
            "역 사이 이동 데이터가 비어 있어."
        )

    return (
        nodes,
        graph,
        station_index
    )


# =========================================================
# 입력 역 찾기
# 정확히 일치할 때만 허용
# =========================================================
def 정확한역찾기(
    query,
    nodes,
    station_index,
    graph
):

    key = 역이름키(query)

    if not key:

        return None, "역 이름을 입력해 줘."

    # 비슷한 역이나 일부 글자 검색은 하지 않음
    matches = station_index.get(
        key,
        []
    )

    if not matches:

        return None, (
            f"'{화면문자열(query)}' 역을 찾을 수 없어. "
            "역 이름을 정확히 입력해 줘."
        )

    match_set = set(matches)

    transfer_neighbors = {
        node_id: set()
        for node_id in matches
    }

    # 실제 환승 간선으로 같은 역의 노선을 연결
    for node_id in matches:

        for next_id, _seconds, edge_type in graph.get(
            node_id,
            []
        ):

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

    if len(groups) > 1:

        return None, (
            f"'{화면문자열(query)}'이라는 이름의 역이 여러 곳에 있어. "
            "잘못된 역을 선택하지 않도록 검색을 중단했어."
        )

    return groups[0], None


# =========================================================
# 다익스트라 경로 찾기
# =========================================================
def 경로찾기(
    start_nodes,
    goal_nodes,
    graph,
    기준
):

    def 우선순위(
        환승수,
        이동수,
        초
    ):

        if 기준 == "최소 환승":

            return (
                환승수,
                이동수,
                초
            )

        if 기준 == "최단 역 수":

            return (
                이동수,
                환승수,
                초
            )

        return (
            초,
            환승수,
            이동수
        )

    best = {}
    metrics = {}
    previous = {}
    previous_edge = {}

    heap = []

    for start in sorted(start_nodes):

        metrics[start] = (
            0,
            0,
            0.0
        )

        best[start] = 우선순위(
            0,
            0,
            0.0
        )

        heapq.heappush(
            heap,
            (
                best[start],
                start
            )
        )

    destination = None

    while heap:

        current_priority, current = heapq.heappop(
            heap
        )

        if current_priority != best.get(current):
            continue

        if current in goal_nodes:

            destination = current
            break

        old_transfer, old_ride, old_seconds = metrics[
            current
        ]

        for next_id, seconds, edge_type in graph.get(
            current,
            []
        ):

            if edge_type not in {
                "RIDE",
                "TRANSFER"
            }:
                continue

            new_transfer = (
                old_transfer
                + (1 if edge_type == "TRANSFER" else 0)
            )

            new_ride = (
                old_ride
                + (1 if edge_type == "RIDE" else 0)
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
                next_id,
                (float("inf"),) * 3
            ):

                best[next_id] = new_priority

                metrics[next_id] = new_metrics

                previous[next_id] = current

                previous_edge[next_id] = edge_type

                heapq.heappush(
                    heap,
                    (
                        new_priority,
                        next_id
                    )
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

    transfer_count, ride_count, total_seconds = (
        metrics[destination]
    )

    return {
        "path": path,
        "edge_types": edge_types,
        "total_seconds": total_seconds,
        "transfer_count": transfer_count,
        "ride_count": ride_count,
    }


# =========================================================
# 실제 이동 간선으로 경로 단계 만들기
# RIDE = 열차 이동
# TRANSFER = 환승
# =========================================================
def 경로단계만들기(
    path,
    edge_types,
    nodes
):

    steps = []
    active_ride = None

    def 현재탑승구간저장():

        nonlocal active_ride

        if (
            active_ride is not None
            and len(active_ride["nodes"]) >= 2
        ):

            steps.append(active_ride)

        active_ride = None

    for index, edge_type in enumerate(edge_types):

        from_id = path[index]
        to_id = path[index + 1]

        from_info = nodes[from_id]
        to_info = nodes[to_id]

        from_line_key = from_info["line_key"]
        to_line_key = to_info["line_key"]

        # 실제 환승 간선
        if edge_type == "TRANSFER":

            현재탑승구간저장()

            steps.append({
                "type": "transfer",
                "station": 역이름표시(
                    from_id,
                    nodes
                ),
                "from_line": 노선이름(
                    from_line_key
                ),
                "to_line": 노선이름(
                    to_line_key
                ),
            })

            continue

        # RIDE로 연결된 노선은 환승으로 표시하지 않음
        if from_line_key != to_line_key:

            현재탑승구간저장()

            steps.append({
                "type": "direct",
                "from_station": 역이름표시(
                    from_id,
                    nodes
                ),
                "to_station": 역이름표시(
                    to_id,
                    nodes
                ),
                "from_line": 노선이름(
                    from_line_key
                ),
                "to_line": 노선이름(
                    to_line_key
                ),
            })

            continue

        # 같은 노선의 연속된 이동
        if (
            active_ride is None
            or active_ride["line_key"] != from_line_key
            or active_ride["nodes"][-1] != from_id
        ):

            현재탑승구간저장()

            active_ride = {
                "type": "ride",
                "line_key": from_line_key,
                "line": 노선이름(
                    from_line_key
                ),
                "color": 노선색(
                    from_line_key
                ),
                "nodes": [from_id],
            }

        if active_ride["nodes"][-1] != to_id:

            active_ride["nodes"].append(
                to_id
            )

    현재탑승구간저장()

    return steps


# =========================================================
# 음성 문장 만들기
# =========================================================
def 음성문장만들기(
    steps,
    nodes,
    destination_id,
    origin_id
):

    phrases = []
    ride_number = 0

    for step in steps:

        if step["type"] == "ride":

            if len(step["nodes"]) < 2:
                continue

            ride_number += 1

            end_name = 역이름표시(
                step["nodes"][-1],
                nodes
            )

            if ride_number == 1:

                start_name = 역이름표시(
                    origin_id,
                    nodes
                )

                phrases.append(
                    f"{start_name}에서 "
                    f"{step['line']}을 이용해 "
                    f"{end_name}까지 이동합니다."
                )

            else:

                phrases.append(
                    f"{step['line']}을 이용해 "
                    f"{end_name}까지 이동합니다."
                )

        elif step["type"] == "transfer":

            phrases.append(
                f"{step['station']}에서 "
                f"{step['to_line']}으로 환승합니다."
            )

        elif step["type"] == "direct":

            phrases.append(
                f"{step['from_station']}에서 "
                f"{step['to_station']}까지 "
                f"{step['from_line']}과 "
                f"{step['to_line']}의 직결 운행 구간으로 이동합니다."
            )

    if not steps:

        return (
            f"{역이름표시(destination_id, nodes)}에 도착했습니다."
        )

    phrases.append(
        f"{역이름표시(destination_id, nodes)}에 도착했습니다."
    )

    return " ".join(phrases)


# =========================================================
# 지도
# 역 좌표를 연결한 참고용 지도
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
    ).replace("</", "<\\/")

    start_json = json.dumps(
        역이름표시(path[0], nodes),
        ensure_ascii=False
    ).replace("</", "<\\/")

    end_json = json.dumps(
        역이름표시(path[-1], nodes),
        ensure_ascii=False
    ).replace("</", "<\\/")

    return f"""
    <!DOCTYPE html>
    <html lang="ko">

    <head>
      <meta charset="utf-8">

      <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
      >

      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      >

      <style>
        html, body {{
            margin: 0;
            padding: 0;
        }}

        #map {{
            width: 100%;
            height: 420px;
            border-radius: 16px;
        }}
      </style>

    </head>

    <body>

      <div id="map"></div>

      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

      <script>

        const points = {points_json};

        const startName = {start_json};

        const endName = {end_json};

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
# 음성 안내 버튼
# =========================================================
def 음성버튼HTML(text):

    text_json = json.dumps(
        text,
        ensure_ascii=False
    ).replace("</", "<\\/")

    return f"""
    <div style="display:flex;gap:10px;">

      <button
        onclick="speakRoute()"
        style="
          flex:1;
          height:52px;
          border:0;
          border-radius:12px;
          background:linear-gradient(90deg,#1D4ED8,#0284C7);
          color:white;
          font-size:16px;
          font-weight:800;
          cursor:pointer;
        "
      >
        🔊 경로 읽어주기
      </button>

      <button
        onclick="stopRoute()"
        style="
          width:110px;
          height:52px;
          border:1px solid #BFDBFE;
          border-radius:12px;
          background:#EFF6FF;
          color:#1E3A8A;
          font-size:14px;
          font-weight:700;
          cursor:pointer;
        "
      >
        ■ 중지
      </button>

    </div>

    <script>

      const routeText = {text_json};

      function speechWindow() {{

        try {{

          if (
            window.parent
            && window.parent.speechSynthesis
          ) {{

            return window.parent;

          }}

        }} catch (error) {{}}

        return window;

      }}

      function speakRoute() {{

        const target = speechWindow();

        if (
          !target.speechSynthesis
          || !target.SpeechSynthesisUtterance
        ) {{

          alert(
            '이 브라우저에서는 음성 안내를 지원하지 않습니다.'
          );

          return;
        }}

        target.speechSynthesis.cancel();

        const utterance =
            new target.SpeechSynthesisUtterance(routeText);

        utterance.lang = 'ko-KR';
        utterance.rate = 0.88;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        target.speechSynthesis.speak(utterance);

      }}

      function stopRoute() {{

        const target = speechWindow();

        if (target.speechSynthesis) {{

          target.speechSynthesis.cancel();

        }}

      }}

    </script>
    """


# =========================================================
# 상단 화면
# =========================================================
st.title("🚇 BLUE ROUTE")

st.caption(
    "출발역과 도착역을 입력해 지하철 경로를 찾아보세요. "
    "비슷한 역 추천이나 자동 완성은 사용하지 않습니다."
)


# =========================================================
# 데이터 로딩
# =========================================================
try:

    with st.spinner(
        "지하철 정보를 불러오는 중..."
    ):

        역정보, 그래프, 역검색표 = 데이터불러오기()

except Exception as error:

    st.error(
        "지하철 데이터를 불러오지 못했어."
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
            placeholder="예: 강남역",
        )

    with col2:

        도착입력 = st.text_input(
            "🔷 도착역",
            placeholder="예: 홍대입구역",
        )

    기준 = st.radio(
        "경로 기준",
        [
            "최소 환승",
            "최단 역 수",
            "최단 시간"
        ],
        horizontal=True,
    )

    검색버튼 = st.form_submit_button(
        "🔎 경로 찾기",
        use_container_width=True,
    )


# =========================================================
# 경로 계산
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
                    결과["path"][-1],
                    결과["path"][0],
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
# 경로 결과
# =========================================================
if st.session_state.route_result:

    result = st.session_state.route_result

    path = result["path"]
    steps = result["steps"]

    st.divider()

    st.header(
        f"{result['origin_name']} → {result['destination_name']}"
    )

    # 이동 시간
    total_minutes = max(
        1,
        round(result["total_seconds"] / 60)
    )

    if total_minutes < 60:

        time_text = f"약 {total_minutes}분"

    else:

        hours = total_minutes // 60
        minutes = total_minutes % 60

        time_text = (
            f"약 {hours}시간 {minutes}분"
            if minutes
            else f"약 {hours}시간"
        )

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "예상 이동 시간",
        time_text
    )

    metric2.metric(
        "역 사이 이동",
        f"{result['ride_count']}회"
    )

    metric3.metric(
        "환승 횟수",
        f"{result['transfer_count']}회"
    )

    # -----------------------------------------------------
    # 이동 경로
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "🧭 이동 경로"
    )

    displayed_step = False

    for step in steps:

        if step["type"] == "ride":

            station_names = [
                역이름표시(node_id, 역정보)
                for node_id in step["nodes"]
            ]

            if len(station_names) < 2:
                continue

            displayed_step = True

            with st.container(border=True):

                # HTML 코드가 아닌 일반 텍스트로 노선 표시
                st.markdown(
                    f"**{step['line']}**"
                )

                st.write(
                    f"{station_names[0]} → {station_names[-1]}"
                )

                # HTML 태그가 해석되지 않는 일반 텍스트 출력
                st.text(
                    "정차역: "
                    + " → ".join(station_names)
                )

        elif step["type"] == "transfer":

            displayed_step = True

            st.info(
                f"🔄 {step['station']}에서 "
                f"{step['from_line']}에서 "
                f"{step['to_line']}으로 환승하세요."
            )

        elif step["type"] == "direct":

            displayed_step = True

            st.info(
                f"🚇 {step['from_station']}에서 "
                f"{step['to_station']}까지 "
                f"{step['from_line']}에서 "
                f"{step['to_line']}으로 직결 운행합니다."
            )

    if not displayed_step:

        st.warning(
            "계산된 경로의 이동 구간을 표시하지 못했어. "
            "다른 경로 기준으로 다시 검색해 줘."
        )

    # -----------------------------------------------------
    # 전체 이동 순서
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "📍 전체 이동 순서"
    )

    route_stations = []

    for node_id in path:

        station_name = 역이름표시(
            node_id,
            역정보
        )

        line_name = 역정보[node_id]["line"]

        # 환승으로 같은 역이 연속될 때 중복 표시하지 않음
        if (
            route_stations
            and route_stations[-1][0] == station_name
        ):

            route_stations[-1] = (
                station_name,
                line_name
            )

        else:

            route_stations.append(
                (
                    station_name,
                    line_name
                )
            )

    for number, (station_name, line_name) in enumerate(
        route_stations,
        start=1
    ):

        st.text(
            f"{number}. {station_name} · {line_name}"
        )

    # -----------------------------------------------------
    # 지도
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "🗺️ 이동 경로 지도"
    )

    st.caption(
        "지도는 역 좌표를 직선으로 연결한 참고용 표시입니다."
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
        scrolling=False,
    )


# =========================================================
# 하단 안내
# =========================================================
st.caption(
    "※ 수도권 지하철 데이터 기준이며, 실제 열차 운행 상황·급행·막차 정보는 반영되지 않을 수 있어."
)
