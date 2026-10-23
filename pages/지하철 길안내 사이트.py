import html
import json

import requests
import streamlit as st
import streamlit.components.v1 as components


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="Seoul WayFinder",
    page_icon="🧭",
    layout="wide",
)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/foot"

HEADERS = {
    "User-Agent": "Seoul-WayFinder-Streamlit/1.0"
}


# =========================================================
# 디자인
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: #f6f7fb;
    }

    .hero {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white;
        border-radius: 24px;
        padding: 30px;
        margin-bottom: 20px;
        box-shadow: 0 12px 30px rgba(79,70,229,.18);
    }

    .hero h1 {
        margin: 0 0 8px 0;
        font-size: 2.1rem;
    }

    .hero p {
        margin: 0;
        opacity: .92;
    }

    .card {
        background: white;
        border-radius: 20px;
        padding: 22px;
        border: 1px solid #e8eaf1;
        box-shadow: 0 7px 22px rgba(20,20,50,.05);
        margin-bottom: 16px;
    }

    .route-card {
        border-left: 6px solid #6366f1;
    }

    .big-number {
        font-size: 1.6rem;
        font-weight: 800;
        color: #4338ca;
    }

    .muted {
        color: #6b7280;
        font-size: .9rem;
    }

    .step {
        display: flex;
        gap: 12px;
        padding: 13px 0;
        border-bottom: 1px solid #eeeef4;
    }

    .step:last-child {
        border-bottom: none;
    }

    .step-no {
        min-width: 30px;
        height: 30px;
        border-radius: 50%;
        background: #eef2ff;
        color: #4338ca;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API - 장소 검색
# =========================================================
@st.cache_data(ttl=3600, show_spinner=False)
def geocode(place):
    place = place.strip()

    if not place:
        return None

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": f"{place}, 대한민국",
                "format": "jsonv2",
                "limit": 1,
                "countrycodes": "kr",
            },
            headers=HEADERS,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        item = data[0]

        return {
            "lat": float(item["lat"]),
            "lon": float(item["lon"]),
            "display_name": item.get("display_name", place),
        }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        IndexError,
    ):
        return None


# =========================================================
# API - 경로 검색
# =========================================================
@st.cache_data(ttl=300, show_spinner=False)
def get_route(start_lat, start_lon, end_lat, end_lon):

    url = (
        f"{OSRM_URL}/"
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
    )

    try:
        response = requests.get(
            url,
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "true",
            },
            headers=HEADERS,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            return None

        if not data.get("routes"):
            return None

        route = data["routes"][0]

        return {
            "distance_m": route.get("distance", 0),
            "duration_s": route.get("duration", 0),
            "geometry": route["geometry"]["coordinates"],
            "legs": route.get("legs", []),
        }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        IndexError,
    ):
        return None


# =========================================================
# 거리 / 시간 표시
# =========================================================
def format_distance(meters):

    if meters < 1000:
        return f"{round(meters)}m"

    return f"{meters / 1000:.1f}km"


def format_duration(seconds):

    minutes = max(1, round(seconds / 60))

    if minutes < 60:
        return f"{minutes}분"

    hours = minutes // 60
    rest = minutes % 60

    if rest == 0:
        return f"{hours}시간"

    return f"{hours}시간 {rest}분"


# =========================================================
# 방향 안내
# =========================================================
def direction_text(modifier, road_name):

    road = road_name.strip() if road_name else "도로"

    directions = {
        "left": "왼쪽으로",
        "right": "오른쪽으로",
        "slight left": "왼쪽 방향으로",
        "slight right": "오른쪽 방향으로",
        "sharp left": "왼쪽으로 크게",
        "sharp right": "오른쪽으로 크게",
        "straight": "직진하여",
        "uturn": "유턴하여",
    }

    direction = directions.get(
        modifier,
        "이동하여"
    )

    return f"{direction} {road}"


# =========================================================
# 이동 단계 만들기
# =========================================================
def make_steps(route):

    result = []

    for leg in route.get("legs", []):

        for step in leg.get("steps", []):

            maneuver = step.get("maneuver", {})

            modifier = maneuver.get(
                "modifier",
                "straight"
            )

            name = step.get("name", "")

            distance = step.get(
                "distance",
                0
            )

            if distance < 15:
                continue

            result.append(
                {
                    "text": direction_text(
                        modifier,
                        name
                    ),
                    "distance": distance,
                }
            )

    return result[:12]


# =========================================================
# 음성 안내 문장
# =========================================================
def make_voice_text(
    origin_name,
    destination_name,
    route,
    steps,
):

    text = []

    text.append(
        f"{origin_name}에서 "
        f"{destination_name}까지 "
        f"안내를 시작합니다."
    )

    text.append(
        f"예상 거리는 "
        f"{format_distance(route['distance_m'])}, "
        f"예상 시간은 약 "
        f"{format_duration(route['duration_s'])}입니다."
    )

    for i, step in enumerate(
        steps[:8],
        start=1
    ):

        text.append(
            f"{i}번째 안내입니다. "
            f"{step['text']}, "
            f"{format_distance(step['distance'])} "
            f"이동하세요."
        )

    text.append(
        "목적지에 도착하면 "
        "안내가 끝납니다."
    )

    return " ".join(text)


# =========================================================
# 지도 만들기
# =========================================================
def make_map(
    origin,
    destination,
    route,
):

    route_coords = route["geometry"]

    # OSRM은 [경도, 위도]
    # Leaflet은 [위도, 경도]
    leaflet_route = [
        [lat, lon]
        for lon, lat in route_coords
    ]

    route_json = json.dumps(
        leaflet_route,
        ensure_ascii=False,
    )

    origin_lat = origin["lat"]
    origin_lon = origin["lon"]

    destination_lat = destination["lat"]
    destination_lon = destination["lon"]

    origin_label = html.escape(
        origin["display_name"][:100]
    )

    destination_label = html.escape(
        destination["display_name"][:100]
    )

    return f"""
    <!DOCTYPE html>

    <html lang="ko">

    <head>

    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width,
        initial-scale=1.0"
    >

    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    >

    <style>

    html,
    body,
    #map {{
        height: 100%;
        margin: 0;
    }}

    #map {{
        min-height: 540px;
        border-radius: 18px;
        overflow: hidden;
    }}

    </style>

    </head>

    <body>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
    </script>

    <script>

    const origin = [
        {origin_lat},
        {origin_lon}
    ];

    const destination = [
        {destination_lat},
        {destination_lon}
    ];

    const route = {route_json};

    const map = L.map("map").setView(
        origin,
        14
    );

    L.tileLayer(
        "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
        {{
            maxZoom: 19,
            attribution:
                "&copy; OpenStreetMap contributors"
        }}
    ).addTo(map);


    // 출발지 아이콘
    const originIcon = L.divIcon({{
        className: "",

        html:
            '<div style="' +
            'width:18px;' +
            'height:18px;' +
            'border-radius:50%;' +
            'background:#4f46e5;' +
            'border:4px solid white;' +
            'box-shadow:0 2px 8px #555;' +
            '"></div>',

        iconSize: [26, 26],

        iconAnchor: [13, 13]
    }});


    // 도착지 아이콘
    const destinationIcon = L.divIcon({{
        className: "",

        html:
            '<div style="' +
            'width:18px;' +
            'height:18px;' +
            'border-radius:50%;' +
            'background:#ef4444;' +
            'border:4px solid white;' +
            'box-shadow:0 2px 8px #555;' +
            '"></div>',

        iconSize: [26, 26],

        iconAnchor: [13, 13]
    }});


    L.marker(
        origin,
        {{
            icon: originIcon
        }}
    )
    .addTo(map)
    .bindPopup(
        "<b>출발지</b><br>{origin_label}"
    );


    L.marker(
        destination,
        {{
            icon: destinationIcon
        }}
    )
    .addTo(map)
    .bindPopup(
        "<b>도착지</b><br>{destination_label}"
    );


    const line = L.polyline(
        route,
        {{
            color: "#6366f1",
            weight: 6,
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


# =========================================================
# 제목
# =========================================================
st.markdown(
    """
    <div class="hero">

        <h1>🧭 Seoul WayFinder</h1>

        <p>
        출발지와 도착지를 입력하면
        지도와 음성으로 이동 경로를 안내합니다.
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 입력
# =========================================================
st.markdown(
    '<div class="card">',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)


with col1:

    origin_input = st.text_input(
        "📍 출발지",
        placeholder="예: 서울역",
    )


with col2:

    destination_input = st.text_input(
        "🏁 도착지",
        placeholder="예: 경복궁",
    )


st.caption(
    "역 이름, 장소 이름 또는 주소를 입력할 수 있습니다."
)


search_button = st.button(
    "🧭 경로 찾기",
    type="primary",
    use_container_width=True,
)

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# 경로 검색
# =========================================================
if search_button:

    if (
        not origin_input.strip()
        or not destination_input.strip()
    ):

        st.warning(
            "출발지와 도착지를 모두 입력해주세요."
        )

        st.stop()


    with st.spinner(
        "장소와 경로를 찾는 중입니다..."
    ):

        origin = geocode(
            origin_input
        )

        destination = geocode(
            destination_input
        )


        if origin is None:

            st.error(
                "출발지를 찾지 못했습니다. "
                "역 이름이나 주소를 "
                "조금 더 정확하게 입력해주세요."
            )

            st.stop()


        if destination is None:

            st.error(
                "도착지를 찾지 못했습니다. "
                "역 이름이나 주소를 "
                "조금 더 정확하게 입력해주세요."
            )

            st.stop()


        route = get_route(
            origin["lat"],
            origin["lon"],
            destination["lat"],
            destination["lon"],
        )


    if route is None:

        st.error(
            "경로를 계산하지 못했습니다. "
            "잠시 후 다시 시도해주세요."
        )

        st.stop()


    # 결과 저장
    st.session_state.origin = origin
    st.session_state.destination = destination
    st.session_state.route = route
    st.session_state.origin_name = origin_input
    st.session_state.destination_name = destination_input


# =========================================================
# 결과
# =========================================================
if (
    "route" in st.session_state
    and st.session_state.route is not None
):

    origin = st.session_state.origin
    destination = st.session_state.destination
    route = st.session_state.route

    origin_name = st.session_state.origin_name
    destination_name = st.session_state.destination_name

    steps = make_steps(route)


    # -----------------------------------------------------
    # 요약
    # -----------------------------------------------------
    st.markdown(
        '<div class="card route-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="muted">
            현재 선택한 경로
        </div>

        <h2>
            {html.escape(origin_name)}
            →
            {html.escape(destination_name)}
        </h2>
        """,
        unsafe_allow_html=True,
    )


    c1, c2, c3 = st.columns(3)


    with c1:

        st.markdown(
            f"""
            <div class="big-number">
                {format_duration(route["duration_s"])}
            </div>

            <div class="muted">
                예상 이동 시간
            </div>
            """,
            unsafe_allow_html=True,
        )


    with c2:

        st.markdown(
            f"""
            <div class="big-number">
                {format_distance(route["distance_m"])}
            </div>

            <div class="muted">
                총 거리
            </div>
            """,
            unsafe_allow_html=True,
        )


    with c3:

        st.markdown(
            f"""
            <div class="big-number">
                {len(steps)}
            </div>

            <div class="muted">
                주요 안내 단계
            </div>
            """,
            unsafe_allow_html=True,
        )


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------
    # 지도 + 안내
    # -----------------------------------------------------
    left, right = st.columns(
        [1.6, 1]
    )


    with left:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "🗺️ 경로 지도"
        )

        components.html(
            make_map(
                origin,
                destination,
                route,
            ),
            height=570,
            scrolling=False,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    with right:

        # -----------------------------------------------
        # 음성
        # -----------------------------------------------
        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "🔊 음성 안내"
        )

        voice_text = make_voice_text(
            origin_name,
            destination_name,
            route,
            steps,
        )

        voice_json = json.dumps(
            voice_text,
            ensure_ascii=False,
        )


        components.html(
            f"""
            <script>

            function startVoice() {{

                if (!("speechSynthesis" in window)) {{

                    document.getElementById(
                        "message"
                    ).innerText =
                        "이 브라우저는 음성 안내를 지원하지 않습니다.";

                    return;
                }}


                window.speechSynthesis.cancel();


                const text =
                    {voice_json};


                const speech =
                    new SpeechSynthesisUtterance(
                        text
                    );


                speech.lang = "ko-KR";

                speech.rate = 0.95;

                speech.pitch = 1.0;


                window.speechSynthesis.speak(
                    speech
                );


                document.getElementById(
                    "message"
                ).innerText =
                    "🔊 음성 안내가 재생되었습니다.";

            }}


            function stopVoice() {{

                if (
                    "speechSynthesis"
                    in window
                ) {{

                    window.speechSynthesis.cancel();

                    document.getElementById(
                        "message"
                    ).innerText =
                        "⏹️ 음성 안내를 중지했습니다.";

                }}

            }}

            </script>


            <button
                onclick="startVoice()"
                style="
                    width:100%;
                    padding:14px;
                    border:0;
                    border-radius:12px;
                    background:#4f46e5;
                    color:white;
                    font-size:16px;
                    font-weight:700;
                    cursor:pointer;
                    margin-bottom:9px;
                "
            >
                🔊 음성 안내 시작
            </button>


            <button
                onclick="stopVoice()"
                style="
                    width:100%;
                    padding:12px;
                    border:1px solid #ddd;
                    border-radius:12px;
                    background:white;
                    color:#333;
                    font-size:15px;
                    cursor:pointer;
                "
            >
                ⏹️ 음성 안내 중지
            </button>


            <p
                id="message"
                style="
                    font-family:sans-serif;
                    color:#666;
                    font-size:13px;
                "
            >
                버튼을 누르면
                한국어 음성 안내가 시작됩니다.
            </p>
            """,
            height=190,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


        # -----------------------------------------------
        # 이동 안내
        # -----------------------------------------------
        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "🚶 이동 안내"
        )


        if not steps:

            st.info(
                "세부 이동 안내가 없습니다."
            )

        else:

            for i, step in enumerate(
                steps,
                start=1,
            ):

                st.markdown(
                    f"""
                    <div class="step">

                        <div class="step-no">
                            {i}
                        </div>

                        <div>

                            <b>
                                {html.escape(step["text"])}
                            </b>

                            <br>

                            <span class="muted">
                                약
                                {format_distance(step["distance"])}
                            </span>

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    # -----------------------------------------------------
    # 안내
    # -----------------------------------------------------
    st.info(
        "💡 지도는 OpenStreetMap, 경로 계산은 OSRM을 사용합니다. "
        "현재 버전은 도보 경로 중심이며 실시간 지하철 운행 정보는 포함하지 않습니다."
    )


# =========================================================
# 처음 화면
# =========================================================
else:

    st.markdown(
        """
        <div class="card">

        <h3>
            ✨ 이렇게 사용하세요
        </h3>


        <div class="step">

            <div class="step-no">
                1
            </div>

            <div>

                <b>
                    출발지 입력
                </b>

                <br>

                <span class="muted">
                    서울역, 강남역 또는 주소를 입력하세요.
                </span>

            </div>

        </div>


        <div class="step">

            <div class="step-no">
                2
            </div>

            <div>

                <b>
                    도착지 입력
                </b>

                <br>

                <span class="muted">
                    가고 싶은 장소를 입력하세요.
                </span>

            </div>

        </div>


        <div class="step">

            <div class="step-no">
                3
            </div>

            <div>

                <b>
                    경로 찾기
                </b>

                <br>

                <span class="muted">
                    지도와 음성으로 이동 방법을 확인하세요.
                </span>

            </div>

        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    st.success(
        "예시: 출발지에 '서울역', "
        "도착지에 '경복궁'을 입력해보세요."
    )


# =========================================================
# 출처
# =========================================================
st.caption(
    "지도: OpenStreetMap · "
    "장소 검색: Nominatim · "
    "경로 계산: OSRM · "
    "음성: 브라우저 Web Speech API"
)
