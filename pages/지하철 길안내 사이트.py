import streamlit as st
import requests
import re
import html
import math
import streamlit.components.v1 as components

from streamlit_geolocation import streamlit_geolocation


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="Metro Guide",
    page_icon="🚇",
    layout="centered"
)


# =========================================================
# 디자인
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        linear-gradient(
            180deg,
            #eef4ff 0%,
            #f7f9fc 45%,
            #ffffff 100%
        );
}

.block-container {
    max-width: 900px;
    padding-top: 30px;
    padding-bottom: 60px;
}


/* 메인 헤더 */

.hero {
    background: linear-gradient(
        135deg,
        #315bea,
        #6847e8
    );
    color: white;
    padding: 30px;
    border-radius: 26px;
    margin-bottom: 22px;
    box-shadow: 0 12px 30px rgba(49,91,234,0.22);
}

.hero-small {
    font-size: 14px;
    opacity: 0.85;
    margin-bottom: 7px;
}

.hero-title {
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 8px;
}

.hero-text {
    font-size: 16px;
    opacity: 0.92;
}


/* 카드 */

.card {
    background: rgba(255,255,255,0.96);
    border-radius: 22px;
    padding: 22px;
    margin: 15px 0;
    box-shadow: 0 7px 25px rgba(30,50,90,0.08);
    border: 1px solid #edf0f7;
}


/* 현재 위치 카드 */

.location-card {
    background: linear-gradient(
        135deg,
        #e9f8ef,
        #f7fff9
    );
    border: 1px solid #ccebd7;
    border-radius: 20px;
    padding: 20px;
    margin: 15px 0;
}


/* 역 카드 */

.station-card {
    background: linear-gradient(
        135deg,
        #fff4e5,
        #fffaf2
    );
    border: 1px solid #f4d6a7;
    border-radius: 22px;
    padding: 24px;
    margin: 18px 0;
}

.station-name {
    font-size: 27px;
    font-weight: 800;
    color: #222;
}

.station-distance {
    color: #ef8b17;
    font-size: 18px;
    font-weight: 700;
}


/* 단계 */

.step {
    display: flex;
    gap: 15px;
    padding: 17px;
    background: white;
    border-radius: 17px;
    margin: 10px 0;
    border: 1px solid #edf0f6;
    box-shadow: 0 4px 15px rgba(30,50,90,0.05);
}

.step-number {
    min-width: 38px;
    height: 38px;
    border-radius: 50%;
    background: #315bea;
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
    font-weight: 800;
    font-size: 16px;
}

.step-content {
    flex: 1;
}

.step-main {
    font-size: 16px;
    font-weight: 700;
    color: #20242d;
}

.step-distance {
    color: #315bea;
    font-size: 13px;
    margin-top: 5px;
}


/* 정보 숫자 */

.info-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
}

.info-item {
    background: #f6f8fc;
    padding: 17px;
    border-radius: 16px;
    text-align: center;
}

.info-label {
    color: #777;
    font-size: 13px;
}

.info-value {
    font-size: 20px;
    font-weight: 800;
    margin-top: 5px;
}


/* 노선도 */

.metro-title {
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 5px;
}

.metro-sub {
    color: #777;
    font-size: 14px;
    margin-bottom: 15px;
}


/* 구분 */

.section-title {
    font-size: 24px;
    font-weight: 800;
    margin-top: 30px;
    margin-bottom: 10px;
}


/* 모바일 */

@media (max-width: 600px) {

    .hero-title {
        font-size: 28px;
    }

    .info-grid {
        grid-template-columns: 1fr;
    }

    .station-name {
        font-size: 23px;
    }

}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 함수
# =========================================================

def 주소찾기(장소):

    try:

        if not 장소 or not 장소.strip():
            return None

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": 장소.strip(),
                "format": "json",
                "limit": 5,
                "countrycodes": "kr"
            },
            headers={
                "User-Agent": "Metro-Guide-Korea"
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        return {
            "위도": float(data[0]["lat"]),
            "경도": float(data[0]["lon"]),
            "이름": data[0].get(
                "display_name",
                장소
            )
        }

    except Exception:
        return None


def 영어제거(문장):

    if not 문장:
        return ""

    문장 = re.sub(
        r"[A-Za-z]+",
        "",
        문장
    )

    문장 = re.sub(
        r"\s+",
        " ",
        문장
    )

    return 문장.strip()


def 거리표시(거리):

    if 거리 < 1000:
        return f"{int(거리)}m"

    return f"{거리 / 1000:.1f}km"


def 거리계산(
    위도1,
    경도1,
    위도2,
    경도2
):

    R = 6371000

    lat1 = math.radians(위도1)
    lat2 = math.radians(위도2)

    dlat = math.radians(
        위도2 - 위도1
    )

    dlon = math.radians(
        경도2 - 경도1
    )

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# =========================================================
# 가까운 역 찾기
# =========================================================

def 가까운역찾기(
    위도,
    경도
):

    try:

        query = f"""
        [out:json][timeout:20];

        (
            node["railway"="station"]
            (around:5000,{위도},{경도});

            node["station"="subway"]
            (around:5000,{위도},{경도});
        );

        out;
        """

        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=query,
            timeout=25
        )

        response.raise_for_status()

        data = response.json()

        역목록 = []

        for item in data.get(
            "elements",
            []
        ):

            역위도 = item.get("lat")
            역경도 = item.get("lon")

            if (
                역위도 is None
                or 역경도 is None
            ):
                continue

            이름 = item.get(
                "tags",
                {}
            ).get("name")

            if not 이름:
                continue

            거리 = 거리계산(
                위도,
                경도,
                역위도,
                역경도
            )

            역목록.append({
                "이름": 이름,
                "위도": 역위도,
                "경도": 역경도,
                "거리": 거리
            })

        if not 역목록:
            return None

        역목록.sort(
            key=lambda x: x["거리"]
        )

        return 역목록[0]

    except Exception:
        return None


# =========================================================
# 도보 경로
# =========================================================

def 도보경로찾기(
    출발,
    도착
):

    try:

        url = (
            "https://router.project-osrm.org/"
            "route/v1/foot/"
            f"{출발['경도']},{출발['위도']};"
            f"{도착['경도']},{도착['위도']}"
        )

        response = requests.get(
            url,
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "true"
            },
            timeout=25
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            return None

        routes = data.get("routes")

        if not routes:
            return None

        return routes[0]

    except Exception:
        return None


# =========================================================
# 상세 안내 만들기
# =========================================================

def 상세안내만들기(
    경로,
    역이름
):

    안내목록 = []

    for leg in 경로.get(
        "legs",
        []
    ):

        for step in leg.get(
            "steps",
            []
        ):

            거리 = step.get(
                "distance",
                0
            )

            maneuver = step.get(
                "maneuver",
                {}
            )

            종류 = maneuver.get(
                "type",
                ""
            )

            modifier = maneuver.get(
                "modifier",
                ""
            )

            도로 = 영어제거(
                step.get(
                    "name",
                    ""
                )
            )


            if 종류 == "depart":

                문장 = (
                    "현재 위치에서 "
                    "지하철역 방향으로 출발하세요."
                )

            elif 종류 == "arrive":

                문장 = (
                    f"{역이름}에 도착합니다."
                )

            elif modifier == "left":

                문장 = "왼쪽으로 이동하세요."

            elif modifier == "right":

                문장 = "오른쪽으로 이동하세요."

            elif modifier == "slight left":

                문장 = (
                    "왼쪽 방향으로 "
                    "살짝 이동하세요."
                )

            elif modifier == "slight right":

                문장 = (
                    "오른쪽 방향으로 "
                    "살짝 이동하세요."
                )

            elif 종류 == "roundabout":

                문장 = (
                    "회전교차로를 지나 "
                    "안내된 방향으로 이동하세요."
                )

            elif 종류 == "fork":

                문장 = (
                    "갈림길에서 "
                    "안내된 방향으로 이동하세요."
                )

            elif 종류 == "merge":

                문장 = (
                    "다른 길과 합류한 뒤 "
                    "계속 이동하세요."
                )

            else:

                문장 = (
                    "현재 방향으로 "
                    "계속 직진하세요."
                )


            if 도로:

                문장 += (
                    f" {도로}을 따라 이동하세요."
                )


            안내목록.append({
                "문장": 문장,
                "거리": 거리
            })


    if not 안내목록:

        안내목록.append({
            "문장": (
                "지도에 표시된 경로를 따라 "
                "지하철역까지 이동하세요."
            ),
            "거리": 경로.get(
                "distance",
                0
            )
        })

    return 안내목록


# =========================================================
# 지도
# =========================================================

def 지도만들기(
    경로,
    출발,
    도착,
    역이름
):

    좌표 = 경로[
        "geometry"
    ][
        "coordinates"
    ]

    route = [
        [위도, 경도]
        for 경도, 위도 in 좌표
    ]

    route_json = str(route)

    start_json = str([
        출발["위도"],
        출발["경도"]
    ])

    end_json = str([
        도착["위도"],
        도착["경도"]
    ])

    지도 = f"""
    <!DOCTYPE html>

    <html>

    <head>

    <meta charset="UTF-8">

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
        height: 100%;
        border-radius: 22px;
    }}

    </style>

    </head>

    <body>

    <div id="map"></div>

    <script>

    const map = L.map("map");

    L.tileLayer(
        "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
        {{
            maxZoom: 19,
            attribution: "© OpenStreetMap"
        }}
    ).addTo(map);


    const route = {route_json};

    const start = {start_json};

    const end = {end_json};


    L.polyline(
        route,
        {{
            color: "#315bea",
            weight: 7,
            opacity: 0.9
        }}
    ).addTo(map);


    L.marker(start)
        .addTo(map)
        .bindPopup("📍 현재 위치")
        .openPopup();


    L.marker(end)
        .addTo(map)
        .bindPopup("🚇 {html.escape(역이름)}");


    map.fitBounds(
        L.latLngBounds(route),
        {{
            padding: [35, 35]
        }}
    );

    </script>

    </body>

    </html>
    """

    return 지도


# =========================================================
# 음성
# =========================================================

def 음성버튼(내용):

    안전한내용 = (
        html.escape(내용)
        .replace(
            '"',
            '&quot;'
        )
    )

    return f"""
    <div style="
        padding: 5px 0;
    ">

    <button
        onclick="읽기()"
        style="
            width:100%;
            padding:17px;
            border:none;
            border-radius:16px;
            background:
                linear-gradient(
                    135deg,
                    #315bea,
                    #6847e8
                );
            color:white;
            font-size:17px;
            font-weight:bold;
            cursor:pointer;
        "
    >
        🔊 전체 길안내 듣기
    </button>

    </div>

    <script>

    function 읽기() {{

        window.speechSynthesis.cancel();

        const text =
            "{안전한내용}";

        const speech =
            new SpeechSynthesisUtterance(text);

        speech.lang = "ko-KR";
        speech.rate = 0.88;
        speech.pitch = 1.0;
        speech.volume = 1.0;

        window.speechSynthesis.speak(
            speech
        );
    }}

    </script>
    """


# =========================================================
# 메인 화면
# =========================================================

st.markdown("""
<div class="hero">

    <div class="hero-small">
        SMART METRO GUIDE
    </div>

    <div class="hero-title">
        🚇 지하철 길찾기
    </div>

    <div class="hero-text">
        현재 위치에서 가까운 역을 찾고
        목적지까지 이동하는 방법을 안내해드려요.
    </div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# 현재 위치
# =========================================================

st.markdown(
    '<div class="section-title">📍 현재 위치</div>',
    unsafe_allow_html=True
)

위치 = streamlit_geolocation()


if not 위치:

    st.info(
        "위치 버튼을 눌러 현재 위치 사용을 허용해주세요."
    )

    st.stop()


현재위도 = 위치.get("latitude")
현재경도 = 위치.get("longitude")


if (
    현재위도 is None
    or 현재경도 is None
):

    st.warning(
        "현재 위치를 가져오지 못했습니다. "
        "브라우저의 위치 권한을 확인해주세요."
    )

    st.stop()


st.markdown("""
<div class="location-card">

<b>🟢 현재 위치 확인 완료</b>

<br><br>

현재 위치를 기준으로
가까운 지하철역을 찾아드립니다.

</div>
""", unsafe_allow_html=True)


# =========================================================
# 목적지
# =========================================================

st.markdown(
    '<div class="section-title">🎯 어디로 갈까요?</div>',
    unsafe_allow_html=True
)

목적지 = st.text_input(
    "목적지 역",
    placeholder="예: 강남역, 홍대입구역, 서울역",
    label_visibility="collapsed"
)

검색 = st.button(
    "🚇 길찾기 시작",
    use_container_width=True
)


if not 검색:

    st.markdown("""
    <div class="card">

    <b>💡 이용 방법</b>

    <br><br>

    ① 현재 위치를 허용하세요.<br>
    ② 목적지 역을 입력하세요.<br>
    ③ 길찾기를 누르세요.

    </div>
    """, unsafe_allow_html=True)

    st.stop()


if not 목적지.strip():

    st.warning(
        "목적지 역을 입력해주세요."
    )

    st.stop()


# =========================================================
# 가까운 역 검색
# =========================================================

with st.spinner(
    "주변 지하철역을 찾고 있습니다..."
):

    가까운역 = 가까운역찾기(
        현재위도,
        현재경도
    )


if 가까운역 is None:

    st.error(
        "주변 지하철역을 찾지 못했습니다."
    )

    st.stop()


역이름 = 가까운역["이름"]

역 = {
    "위도": 가까운역["위도"],
    "경도": 가까운역["경도"]
}


# =========================================================
# 가까운 역 카드
# =========================================================

st.markdown(
    f"""
    <div class="station-card">

        <div style="
            font-size:14px;
            color:#9b6a22;
            margin-bottom:6px;
        ">
            가장 가까운 지하철역
        </div>

        <div class="station-name">
            🚉 {역이름}
        </div>

        <br>

        <div class="station-distance">
            현재 위치에서 약
            {거리표시(가까운역["거리"])}
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 현재 위치 → 역
# =========================================================

현재위치 = {
    "위도": 현재위도,
    "경도": 현재경도
}


with st.spinner(
    f"{역이름}까지 도보 경로를 계산하고 있습니다..."
):

    경로 = 도보경로찾기(
        현재위치,
        역
    )


if 경로 is None:

    st.error(
        "도보 경로를 찾지 못했습니다."
    )

    st.stop()


거리 = 경로["distance"]

시간 = 경로["duration"]

예상시간 = max(
    1,
    round(시간 / 60)
)


# =========================================================
# 이동 정보
# =========================================================

st.markdown(
    '<div class="section-title">🚶 이동 정보</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="card">

        <div class="info-grid">

            <div class="info-item">

                <div class="info-label">
                    이동 거리
                </div>

                <div class="info-value">
                    {거리표시(거리)}
                </div>

            </div>


            <div class="info-item">

                <div class="info-label">
                    예상 시간
                </div>

                <div class="info-value">
                    {예상시간}분
                </div>

            </div>


            <div class="info-item">

                <div class="info-label">
                    목적지
                </div>

                <div class="info-value">
                    🚇
                </div>

            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 지도
# =========================================================

st.markdown(
    '<div class="section-title">🗺️ 역까지 가는 길</div>',
    unsafe_allow_html=True
)

지도 = 지도만들기(
    경로,
    현재위치,
    역,
    역이름
)

st.components.v1.html(
    지도,
    height=500
)


# =========================================================
# 상세 길안내
# =========================================================

안내목록 = 상세안내만들기(
    경로,
    역이름
)


st.markdown(
    '<div class="section-title">🧭 이렇게 이동하세요</div>',
    unsafe_allow_html=True
)


for 번호, 안내 in enumerate(
    안내목록,
    1
):

    st.markdown(
        f"""
        <div class="step">

            <div class="step-number">
                {번호}
            </div>

            <div class="step-content">

                <div class="step-main">
                    {안내["문장"]}
                </div>

                <div class="step-distance">
                    약 {거리표시(안내["거리"])}
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 지하철 이용 설명
# =========================================================

st.markdown(
    '<div class="section-title">🚇 지하철 이용하기</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="card">

        <b>1. {역이름}에 도착</b>

        <br><br>

        역 안으로 들어간 뒤
        <b>{목적지}</b> 방향의
        지하철 노선을 확인하세요.

        <br><br>

        <b>2. 승강장 확인</b>

        <br><br>

        전광판에서 목적지 방향의
        열차를 확인한 뒤 승강장으로 이동하세요.

        <br><br>

        <b>3. 환승</b>

        <br><br>

        환승이 필요한 경우
        안내 표지판을 따라 환승 통로로 이동하세요.

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 수도권 지하철 노선도
# =========================================================

st.markdown(
    '<div class="section-title">🗺️ 수도권 지하철 노선도</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="card">

        <div class="metro-title">
            🚇 수도권 지하철 전체 노선
        </div>

        <div class="metro-sub">
            노선도를 확인하면서 이동할 노선을 찾아보세요.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# 서울교통공사 공식 노선도
노선도URL = (
    "https://www.seoulmetro.co.kr/kr/board.do"
)


components.html(
    f"""
    <div style="
        background:white;
        border-radius:20px;
        padding:20px;
        text-align:center;
        box-shadow:0 5px 20px rgba(0,0,0,0.07);
    ">

        <p style="
            font-size:16px;
            font-weight:bold;
        ">
            수도권 지하철 노선도를 확인하세요.
        </p>

        <a
            href="{노선도URL}"
            target="_blank"
            style="
                display:block;
                background:#315bea;
                color:white;
                padding:15px;
                border-radius:14px;
                text-decoration:none;
                font-weight:bold;
            "
        >
            🚇 공식 지하철 노선도 열기
        </a>

    </div>
    """,
    height=120
)


# =========================================================
# 음성 안내
# =========================================================

st.markdown(
    '<div class="section-title">🔊 음성 안내</div>',
    unsafe_allow_html=True
)


음성내용 = (
    f"현재 위치에서 {역이름}까지 이동하세요. "
    f"전체 거리는 {거리표시(거리)}이고 "
    f"예상 시간은 약 {예상시간}분입니다. "
)


for 번호, 안내 in enumerate(
    안내목록,
    1
):

    음성내용 += (
        f"{번호}번째 안내입니다. "
        f"{안내['문장']} "
        f"약 {거리표시(안내['거리'])}입니다. "
    )


음성내용 += (
    f"{역이름}에 도착하면 "
    f"{목적지} 방향의 지하철 노선을 확인하세요."
)


components.html(
    음성버튼(음성내용),
    height=85
)


# =========================================================
# 마지막 안내
# =========================================================

st.markdown("""
<div class="card">

    <b>💙 안전하게 이동하세요!</b>

    <br><br>

    보행 중에는 휴대폰 화면을 계속 보지 말고
    주변 차량과 보행자를 확인해주세요.

</div>
""", unsafe_allow_html=True)
