import streamlit as st
import requests
import html
import json
import re
import streamlit.components.v1 as components

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="서울 길찾기",
    page_icon="🧭",
    layout="wide"
)

# -----------------------------
# 디자인
# -----------------------------
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
        padding: 16px 20px;
        margin-bottom: 10px;
        border-left: 5px solid #6366f1;
        box-shadow: 0 3px 12px rgba(0,0,0,0.04);
    }

    .step-number {
        color: #6366f1;
        font-weight: 800;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 주소 검색
# -----------------------------
def search_location(address):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "kr"
    }

    headers = {
        "User-Agent": "SeoulNavigationApp/1.0"
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


# -----------------------------
# 도보 경로 검색
# -----------------------------
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


# -----------------------------
# 거리 표시
# -----------------------------
def format_distance(meters):
    if meters < 1000:
        return f"{round(meters)}m"

    return f"{meters / 1000:.1f}km"


# -----------------------------
# 시간 표시
# -----------------------------
def format_time(seconds):
    minutes = round(seconds / 60)

    if minutes < 60:
        return f"{minutes}분"

    hours = minutes // 60
    remain = minutes % 60

    if remain == 0:
        return f"{hours}시간"

    return f"{hours}시간 {remain}분"


# -----------------------------
# 안내문 정리
# -----------------------------
def clean_instruction(step):
    maneuver = step.get("maneuver", {})
    instruction = step.get("name", "")

    step_type = maneuver.get("type", "")
    modifier = maneuver.get("modifier", "")

    if step_type == "depart":
        return "출발하세요."

    if step_type == "arrive":
        return "목적지에 도착했습니다."

    if modifier:
        direction = {
            "left": "왼쪽",
            "right": "오른쪽",
            "straight": "직진",
            "slight left": "왼쪽 방향",
            "slight right": "오른쪽 방향",
            "sharp left": "왼쪽으로 크게",
            "sharp right": "오른쪽으로 크게"
        }.get(modifier, modifier)

        if instruction:
            return f"{instruction} 방향으로 {direction} 이동하세요."

        return f"{direction}으로 이동하세요."

    if instruction:
        return f"{instruction} 방향으로 이동하세요."

    return "계속 이동하세요."


# -----------------------------
# 지도 생성
# -----------------------------
def make_map(start, end, route):
    coordinates = route["geometry"]["coordinates"]

    route_points = [
        [point[1], point[0]]
        for point in coordinates
    ]

    start_lat = start["lat"]
    start_lon = start["lon"]

    end_lat = end["lat"]
    end_lon = end["lon"]

    route_json = json.dumps(route_points)

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">

        <link
            rel="stylesheet"
            href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        />

        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

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

            const startMarker = L.marker(start)
                .addTo(map)
                .bindPopup("<b>출발지</b>")
                .openPopup();

            const endMarker = L.marker(end)
                .addTo(map)
                .bindPopup("<b>도착지</b>");

            const line = L.polyline(
                route,
                {{
                    color: "#6366f1",
                    weight: 7,
                    opacity: 0.85
                }}
            ).addTo(map);

            map.fitBounds(line.getBounds(), {{
                padding: [30, 30]
            }});
        </script>

    </body>
    </html>
    """

    return map_html


# -----------------------------
# 음성 안내
# -----------------------------
def make_voice(text):
    safe_text = json.dumps(text, ensure_ascii=False)

    html_code = f"""
    <script>
        function speakRoute() {{
            const text = {safe_text};

            if (!("speechSynthesis" in window)) {{
                alert("이 브라우저에서는 음성 기능을 사용할 수 없습니다.");
                return;
            }}

            window.speechSynthesis.cancel();

            const speech = new SpeechSynthesisUtterance(text);
            speech.lang = "ko-KR";
            speech.rate = 0.95;
            speech.pitch = 1.0;

            window.speechSynthesis.speak(speech);
        }}

        function stopVoice() {{
            window.speechSynthesis.cancel();
        }}
    </script>

    <button
        onclick="speakRoute()"
        style="
            width:48%;
            padding:13px;
            border:0;
            border-radius:12px;
            background:#6366f1;
            color:white;
            font-size:15px;
            font-weight:bold;
            cursor:pointer;
        "
    >
        🔊 음성 안내 시작
    </button>

    <button
        onclick="stopVoice()"
        style="
            width:48%;
            padding:13px;
            border:0;
            border-radius:12px;
            background:#e5e7eb;
            color:#374151;
            font-size:15px;
            font-weight:bold;
            cursor:pointer;
        "
    >
        ⏹️ 음성 중지
    </button>
    """

    return html_code


# -----------------------------
# 화면
# -----------------------------
st.markdown(
    '<div class="main-title">🧭 서울 길찾기</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">출발지와 목적지를 입력하면 지도와 음성으로 이동 경로를 안내합니다.</div>',
    unsafe_allow_html=True
)


# -----------------------------
# 입력창
# -----------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)

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

st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------
# 경로 검색
# -----------------------------
if find_route:

    if not start_address.strip():
        st.warning("출발지를 입력해주세요.")

    elif not end_address.strip():
        st.warning("도착지를 입력해주세요.")

    else:

        with st.spinner("경로를 찾고 있습니다..."):

            start = search_location(start_address)
            end = search_location(end_address)

            if start is None:
                st.error("출발지를 찾을 수 없습니다. 주소나 장소명을 다시 입력해주세요.")

            elif end is None:
                st.error("도착지를 찾을 수 없습니다. 주소나 장소명을 다시 입력해주세요.")

            else:

                route = get_route(start, end)

                if route is None:
                    st.error(
                        "경로를 찾지 못했습니다. "
                        "잠시 후 다시 시도해주세요."
                    )

                else:

                    # 결과 저장
                    st.session_state["route"] = route
                    st.session_state["start"] = start
                    st.session_state["end"] = end


# -----------------------------
# 결과 표시
# -----------------------------
if "route" in st.session_state:

    route = st.session_state["route"]
    start = st.session_state["start"]
    end = st.session_state["end"]

    distance = route["distance"]
    duration = route["duration"]

    st.markdown(
        f"""
        <div class="result-card">
            <div style="font-size:15px; opacity:.9;">
                추천 도보 경로
            </div>

            <div style="font-size:23px; font-weight:800; margin-top:7px;">
                {html.escape(start_address if start_address else "출발지")}
                →
                {html.escape(end_address if end_address else "도착지")}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 요약
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="card">
                <div class="result-number">{format_time(duration)}</div>
                <div class="result-label">예상 소요 시간</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="card">
                <div class="result-number">{format_distance(distance)}</div>
                <div class="result-label">총 이동 거리</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 지도
    st.markdown(
        '<div class="card"><h3>🗺️ 이동 경로</h3>',
        unsafe_allow_html=True
    )

    components.html(
        make_map(start, end, route),
        height=550
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # 음성
    instructions = []

    for step in route.get("legs", [])[0].get("steps", []):
        text = clean_instruction(step)
        instructions.append(text)

    voice_text = " ".join(instructions)

    st.markdown(
        '<div class="card"><h3>🔊 음성 안내</h3>',
        unsafe_allow_html=True
    )

    components.html(
        make_voice(voice_text),
        height=65
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # 상세 안내
    st.markdown(
        '<div class="card"><h3>📋 이동 순서</h3>',
        unsafe_allow_html=True
    )

    for index, instruction in enumerate(instructions, start=1):

        st.markdown(
            f"""
            <div class="step-card">
                <span class="step-number">{index}</span>
                &nbsp;&nbsp;
                {html.escape(instruction)}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

else:

    st.markdown(
        """
        <div class="card" style="text-align:center; padding:50px;">
            <div style="font-size:50px;">🧭</div>
            <h2>어디로 가시나요?</h2>
            <p style="color:#6b7280;">
                출발지와 도착지를 입력하면<br>
                지도와 음성으로 이동 방법을 알려드립니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
