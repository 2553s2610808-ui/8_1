import streamlit as st
import requests
import html
import json
import streamlit.components.v1 as components

# ==========================================
# 기본 설정
# ==========================================

st.set_page_config(
    page_title="서울 길찾기",
    page_icon="🧭",
    layout="wide"
)

# ==========================================
# 디자인
# ==========================================

st.markdown("""
<style>
    .stApp {
        background: #f5f7fb;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        color: #20243a;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #6b7280;
        font-size: 17px;
        margin-bottom: 30px;
    }

    .card {
        background: white;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.06);
        margin-bottom: 20px;
    }

    .result-card {
        background: linear-gradient(135deg, #5b5ff7, #7c4dff);
        color: white;
        border-radius: 20px;
        padding: 24px;
        margin: 15px 0;
    }

    .result-number {
        font-size: 30px;
        font-weight: 800;
    }

    .result-label {
        font-size: 14px;
        opacity: 0.85;
    }

    .step-card {
        background: white;
        border-radius: 15px;
        padding: 17px 20px;
        margin-bottom: 10px;
        border-left: 5px solid #6366f1;
        box-shadow: 0 3px 12px rgba(0,0,0,0.04);
        font-size: 16px;
        line-height: 1.5;
    }

    .step-number {
        color: #6366f1;
        font-weight: 800;
    }

    .voice-box {
        background: #f3f4ff;
        border-radius: 15px;
        padding: 18px;
        color: #3730a3;
        margin-bottom: 15px;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 주소 검색
# ==========================================

def search_location(address):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "kr"
    }

    headers = {
        "User-Agent": "SeoulNavigationApp/2.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "name": data[0].get("display_name", address)
        }

    except Exception:
        return None


# ==========================================
# 경로 검색
# ==========================================

def get_route(start, end):

    url = (
        "https://router.project-osrm.org/route/v1/"
        f"foot/{start['lon']},{start['lat']};"
        f"{end['lon']},{end['lat']}"
    )

    params = {
        "overview": "full",
        "steps": "true",
        "geometries": "geojson"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            return None

        return data["routes"][0]

    except Exception:
        return None


# ==========================================
# 거리
# ==========================================

def format_distance(meters):

    if meters < 1000:
        return f"{round(meters)}m"

    return f"{meters / 1000:.1f}km"


# ==========================================
# 시간
# ==========================================

def format_time(seconds):

    minutes = round(seconds / 60)

    if minutes < 60:
        return f"{minutes}분"

    hours = minutes // 60
    remain = minutes % 60

    if remain == 0:
        return f"{hours}시간"

    return f"{hours}시간 {remain}분"


# ==========================================
# 방향 표현
# ==========================================

def direction_text(modifier):

    directions = {
        "left": "왼쪽",
        "right": "오른쪽",
        "straight": "직진",
        "slight left": "왼쪽 방향",
        "slight right": "오른쪽 방향",
        "sharp left": "왼쪽으로 크게",
        "sharp right": "오른쪽으로 크게",
        "uturn": "유턴"
    }

    return directions.get(modifier, "")


# ==========================================
# 이동 안내 문장 생성
# ==========================================

def make_instruction(step):

    maneuver = step.get("maneuver", {})

    step_type = maneuver.get("type", "")
    modifier = maneuver.get("modifier", "")
    road_name = step.get("name", "").strip()

    distance = step.get("distance", 0)

    distance_text = ""

    if distance >= 1000:
        distance_text = f"{distance / 1000:.1f}킬로미터"
    elif distance >= 100:
        distance_text = f"{round(distance / 10) * 10}미터"
    elif distance >= 1:
        distance_text = f"{round(distance)}미터"

    # 출발
    if step_type == "depart":

        if road_name:
            return f"{road_name} 방향으로 출발하세요."

        return "현재 위치에서 출발하세요."

    # 도착
    if step_type == "arrive":
        return "목적지에 도착했습니다."

    # 유턴
    if modifier == "uturn":

        if distance_text:
            return f"{distance_text} 정도 이동한 뒤 유턴하세요."

        return "유턴하세요."

    # 회전
    direction = direction_text(modifier)

    if direction:

        if road_name and distance_text:
            return (
                f"{distance_text} 정도 이동한 뒤 "
                f"{road_name}에서 {direction}으로 이동하세요."
            )

        if road_name:
            return f"{road_name}에서 {direction}으로 이동하세요."

        if distance_text:
            return f"{distance_text} 정도 이동한 뒤 {direction}으로 이동하세요."

        return f"{direction}으로 이동하세요."

    # 직진
    if modifier == "straight":

        if distance_text:
            return f"{distance_text} 정도 계속 직진하세요."

        return "계속 직진하세요."

    # 그 외
    if road_name and distance_text:
        return f"{road_name}을 따라 {distance_text} 정도 이동하세요."

    if distance_text:
        return f"{distance_text} 정도 계속 이동하세요."

    return "계속 이동하세요."


# ==========================================
# 안내 문장 정리
# ==========================================

def get_instructions(route):

    instructions = []

    for leg in route.get("legs", []):

        for step in leg.get("steps", []):

            text = make_instruction(step)

            if text and text not in instructions:
                instructions.append(text)

    if not instructions:
        instructions.append("현재 위치에서 목적지까지 이동하세요.")

    return instructions


# ==========================================
# 음성용 안내문
# ==========================================

def make_voice_text(start_name, end_name, route, instructions):

    distance = format_distance(route["distance"])
    duration = format_time(route["duration"])

    sentences = []

    sentences.append(
        f"{start_name}에서 출발하여 {end_name}까지 안내해 드립니다."
    )

    sentences.append(
        f"전체 거리는 약 {distance}이고, "
        f"예상 소요 시간은 약 {duration}입니다."
    )

    for index, instruction in enumerate(instructions):

        if index == 0:
            sentences.append(f"먼저, {instruction}")

        else:
            sentences.append(
                f"{index + 1}번째 안내입니다. {instruction}"
            )

    sentences.append("목적지에 도착하면 안내를 종료합니다.")

    return " ".join(sentences)


# ==========================================
# 지도
# ==========================================

def make_map(start, end, route):

    coordinates = route["geometry"]["coordinates"]

    route_points = [
        [point[1], point[0]]
        for point in coordinates
    ]

    route_json = json.dumps(route_points)

    start_lat = start["lat"]
    start_lon = start["lon"]

    end_lat = end["lat"]
    end_lon = end["lon"]

    map_html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="utf-8">

        <link
            rel="stylesheet"
            href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        >

        <script
            src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
        </script>

        <style>

            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
            }}

            #map {{
                width: 100%;
                height: 520px;
                border-radius: 18px;
            }}

        </style>

    </head>

    <body>

        <div id="map"></div>

        <script>

            const start = [{start_lat}, {start_lon}];

            const end = [{end_lat}, {end_lon}];

            const route = {route_json};

            const map = L.map("map");

            L.tileLayer(
                "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
                {{
                    attribution: "&copy; OpenStreetMap contributors"
                }}
            ).addTo(map);

            L.marker(start)
                .addTo(map)
                .bindPopup("출발지");

            L.marker(end)
                .addTo(map)
                .bindPopup("도착지");

            const line = L.polyline(
                route,
                {{
                    color: "#6366f1",
                    weight: 7,
                    opacity: 0.85
                }}
            ).addTo(map);

            map.fitBounds(
                line.getBounds(),
                {{
                    padding: [30, 30]
                }}
            );

        </script>

    </body>

    </html>
    """

    return map_html


# ==========================================
# 음성 안내 UI
# ==========================================

def make_voice_ui(voice_text):

    safe_text = json.dumps(
        voice_text,
        ensure_ascii=False
    )

    return f"""

    <script>

        const 안내문 = {safe_text};

        function 음성시작() {{

            if (!("speechSynthesis" in window)) {{

                alert(
                    "현재 사용 중인 브라우저에서는 음성 안내를 사용할 수 없습니다."
                );

                return;
            }}

            window.speechSynthesis.cancel();

            const 음성 = new SpeechSynthesisUtterance(안내문);

            음성.lang = "ko-KR";

            음성.rate = 0.88;

            음성.pitch = 1.0;

            음성.volume = 1.0;

            window.speechSynthesis.speak(음성);

        }}

        function 음성중지() {{

            window.speechSynthesis.cancel();

        }}

    </script>


    <div style="
        display:flex;
        gap:10px;
        width:100%;
    ">

        <button
            onclick="음성시작()"
            style="
                flex:1;
                padding:14px;
                border:0;
                border-radius:12px;
                background:#6366f1;
                color:white;
                font-size:15px;
                font-weight:bold;
                cursor:pointer;
            "
        >
            🔊 안내 시작
        </button>


        <button
            onclick="음성중지()"
            style="
                flex:1;
                padding:14px;
                border:0;
                border-radius:12px;
                background:#e5e7eb;
                color:#374151;
                font-size:15px;
                font-weight:bold;
                cursor:pointer;
            "
        >
            ⏹️ 안내 중지
        </button>

    </div>

    """


# ==========================================
# 제목
# ==========================================

st.markdown(
    '<div class="main-title">🧭 서울 길찾기</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    '출발지와 목적지를 입력하면 지도와 음성으로 이동 방법을 알려드립니다.'
    '</div>',
    unsafe_allow_html=True
)


# ==========================================
# 입력
# ==========================================

st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    start_address = st.text_input(
        "📍 출발지",
        placeholder="예: 서울역"
    )

with col2:

    end_address = st.text_input(
        "🎯 도착지",
        placeholder="예: 경복궁"
    )


find_route = st.button(
    "🚶 경로 찾기",
    use_container_width=True,
    type="primary"
)

st.markdown(
    '</div>',
    unsafe_allow_html=True
)


# ==========================================
# 검색
# ==========================================

if find_route:

    if not start_address.strip():

        st.warning("출발지를 입력해주세요.")

    elif not end_address.strip():

        st.warning("도착지를 입력해주세요.")

    else:

        with st.spinner("가장 적합한 경로를 찾고 있습니다..."):

            start = search_location(start_address)

            end = search_location(end_address)

            if start is None:

                st.error(
                    "출발지를 찾을 수 없습니다. "
                    "장소명이나 주소를 다시 확인해주세요."
                )

            elif end is None:

                st.error(
                    "도착지를 찾을 수 없습니다. "
                    "장소명이나 주소를 다시 확인해주세요."
                )

            else:

                route = get_route(start, end)

                if route is None:

                    st.error(
                        "현재 이동 경로를 찾지 못했습니다. "
                        "잠시 후 다시 시도해주세요."
                    )

                else:

                    st.session_state["route"] = route

                    st.session_state["start"] = start

                    st.session_state["end"] = end

                    st.session_state["start_address"] = start_address

                    st.session_state["end_address"] = end_address


# ==========================================
# 결과
# ==========================================

if "route" in st.session_state:

    route = st.session_state["route"]

    start = st.session_state["start"]

    end = st.session_state["end"]

    start_address = st.session_state["start_address"]

    end_address = st.session_state["end_address"]


    # --------------------------------------
    # 경로 정보
    # --------------------------------------

    st.markdown(
        f"""
        <div class="result-card">

            <div style="
                font-size:14px;
                opacity:.85;
            ">
                추천 도보 경로
            </div>

            <div style="
                font-size:23px;
                font-weight:800;
                margin-top:8px;
            ">
                {html.escape(start_address)}
                →
                {html.escape(end_address)}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------
    # 거리 / 시간
    # --------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            f"""
            <div class="card">

                <div class="result-number">
                    {format_time(route["duration"])}
                </div>

                <div class="result-label">
                    예상 소요 시간
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with col2:

        st.markdown(
            f"""
            <div class="card">

                <div class="result-number">
                    {format_distance(route["distance"])}
                </div>

                <div class="result-label">
                    총 이동 거리
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # --------------------------------------
    # 지도
    # --------------------------------------

    st.markdown(
        '<div class="card"><h3>🗺️ 이동 경로</h3>',
        unsafe_allow_html=True
    )

    components.html(
        make_map(start, end, route),
        height=550
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------
    # 이동 순서
    # --------------------------------------

    instructions = get_instructions(route)


    st.markdown(
        '<div class="card"><h3>📋 이동 순서</h3>',
        unsafe_allow_html=True
    )


    for index, instruction in enumerate(
        instructions,
        start=1
    ):

        st.markdown(
            f"""
            <div class="step-card">

                <span class="step-number">
                    {index}
                </span>

                &nbsp;&nbsp;

                {html.escape(instruction)}

            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------
    # 음성 안내
    # --------------------------------------

    voice_text = make_voice_text(
        start_address,
        end_address,
        route,
        instructions
    )


    st.markdown(
        """
        <div class="card">

            <h3>🔊 음성 안내</h3>

            <div class="voice-box">
                경로 정보를 자연스러운 한국어 음성으로
                안내합니다.
            </div>

        """,
        unsafe_allow_html=True
    )


    components.html(
        make_voice_ui(voice_text),
        height=70
    )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ==========================================
# 검색 전 화면
# ==========================================

else:

    st.markdown(
        """
        <div class="card"
             style="
                text-align:center;
                padding:55px;
             ">

            <div style="font-size:52px;">
                🧭
            </div>

            <h2>
                어디로 가시나요?
            </h2>

            <p style="color:#6b7280;">
                출발지와 도착지를 입력하면<br>
                지도와 음성으로 이동 방법을 알려드립니다.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )
