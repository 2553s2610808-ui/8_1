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
    page_title="현재 위치 지하철 길찾기",
    page_icon="🚇",
    layout="centered"
)


# =========================================================
# 화면 디자인
# =========================================================

st.markdown("""
<style>

.main-title {
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 5px;
}

.sub-title {
    color: #666666;
    margin-bottom: 25px;
}

.info-box {
    background: white;
    padding: 18px;
    border-radius: 16px;
    margin-top: 15px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
}

.step-box {
    background: #f5f7ff;
    padding: 16px;
    margin: 8px 0;
    border-radius: 12px;
}

.step-title {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 7px;
}

.distance {
    color: #4f6fff;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 제목
# =========================================================

st.markdown(
    '<div class="main-title">🚇 현재 위치 지하철 길찾기</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    '현재 위치에서 가까운 지하철역까지 가는 길을 자세하게 안내합니다.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# 현재 위치 자동 확인
# =========================================================

st.markdown("## 📍 현재 위치")

위치 = streamlit_geolocation()


if not 위치:
    st.info(
        "아래 위치 버튼을 눌러 현재 위치 사용을 허용해주세요."
    )
    st.stop()


현재위도 = 위치.get("latitude")
현재경도 = 위치.get("longitude")


if 현재위도 is None or 현재경도 is None:
    st.warning(
        "현재 위치를 가져오지 못했습니다. "
        "브라우저의 위치 권한을 허용해주세요."
    )
    st.stop()


st.success("현재 위치를 확인했습니다.")


# =========================================================
# 목적지 입력
# =========================================================

st.markdown("## 🎯 목적지")

목적지 = st.text_input(
    "목적지 역 또는 장소",
    placeholder="예: 강남역"
)

검색 = st.button(
    "🚇 길찾기 시작",
    use_container_width=True
)


# =========================================================
# 아무것도 입력하지 않았으면 지도 표시 X
# =========================================================

if not 검색:
    st.stop()


if not 목적지.strip():
    st.warning("목적지를 입력해주세요.")
    st.stop()


목적지 = 목적지.strip()


# =========================================================
# 장소 검색
# =========================================================

def 주소찾기(장소):

    try:

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": 장소,
                "format": "json",
                "limit": 5,
                "countrycodes": "kr"
            },
            headers={
                "User-Agent": "Korean-Subway-Route-App"
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
            "이름": data[0].get("display_name", 장소)
        }

    except Exception:
        return None


# =========================================================
# 가까운 지하철역 찾기
# =========================================================

def 가까운역찾기(위도, 경도):

    try:

        overpass = """
        [out:json][timeout:15];

        (
          node
          ["railway"="station"]
          (around:3000,LAT,LON);

          node
          ["station"="subway"]
          (around:3000,LAT,LON);
        );

        out center;
        """

        overpass = overpass.replace("LAT", str(위도))
        overpass = overpass.replace("LON", str(경도))

        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=overpass,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        역목록 = []

        for 요소 in data.get("elements", []):

            역위도 = 요소.get("lat")
            역경도 = 요소.get("lon")

            if 역위도 is None or 역경도 is None:
                continue

            이름 = 요소.get("tags", {}).get("name")

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
# 거리 계산
# =========================================================

def 거리계산(
    위도1,
    경도1,
    위도2,
    경도2
):

    지구반지름 = 6371000

    위도1 = math.radians(위도1)
    위도2 = math.radians(위도2)

    위도차 = math.radians(
        위도2 - 위도1
    )

    경도차 = math.radians(
        경도2 - 경도1
    )

    a = (
        math.sin(위도차 / 2) ** 2
        +
        math.cos(위도1)
        *
        math.cos(위도2)
        *
        math.sin(경도차 / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return 지구반지름 * c


# =========================================================
# 거리 표시
# =========================================================

def 거리표시(거리):

    if 거리 < 1000:
        return f"{int(거리)}m"

    return f"{거리 / 1000:.1f}km"


# =========================================================
# 영어 제거
# =========================================================

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


# =========================================================
# 도보 경로
# =========================================================

def 도보경로찾기(출발, 도착):

    try:

        url = (
            "https://router.project-osrm.org/route/v1/"
            "foot/"
            f"{출발['경도']},{출발['위도']};"
            f"{도착['경도']},{도착['위도']}"
        )

        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        }

        response = requests.get(
            url,
            params=params,
            timeout=20
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
# 지도
# =========================================================

def 지도만들기(경로, 출발, 도착):

    좌표 = 경로["geometry"]["coordinates"]

    지도좌표 = []

    for 경도, 위도 in 좌표:

        지도좌표.append(
            [위도, 경도]
        )

    경로문자열 = str(지도좌표)

    출발문자열 = str([
        출발["위도"],
        출발["경도"]
    ])

    도착문자열 = str([
        도착["위도"],
        도착["경도"]
    ])

    지도HTML = f"""
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

    html,
    body {{
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
    }}

    #map {{
        width: 100%;
        height: 100%;
        border-radius: 16px;
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
            maxZoom: 19
        }}
    ).addTo(map);


    const route = {경로문자열};

    const start = {출발문자열};

    const end = {도착문자열};


    L.polyline(
        route,
        {{
            weight: 6
        }}
    ).addTo(map);


    L.marker(start)
        .addTo(map)
        .bindPopup("현재 위치");


    L.marker(end)
        .addTo(map)
        .bindPopup("지하철역");


    const bounds = L.latLngBounds(route);

    map.fitBounds(
        bounds,
        {{
            padding: [30, 30]
        }}
    );

    </script>

    </body>

    </html>
    """

    return 지도HTML


# =========================================================
# 음성
# =========================================================

def 음성버튼(내용):

    안전한내용 = html.escape(내용)

    음성HTML = f"""
    <div style="
        margin-top:15px;
        padding:15px;
        background:white;
        border-radius:16px;
    ">

        <button
            onclick="읽기()"
            style="
                width:100%;
                padding:14px;
                border:0;
                border-radius:12px;
                background:#4f6fff;
                color:white;
                font-size:17px;
                font-weight:bold;
            "
        >
            🔊 음성 안내 듣기
        </button>

    </div>

    <script>

    function 읽기() {{

        window.speechSynthesis.cancel();

        const 말 = new SpeechSynthesisUtterance(
            "{안전한내용}"
        );

        말.lang = "ko-KR";
        말.rate = 0.9;
        말.pitch = 1.0;
        말.volume = 1.0;

        window.speechSynthesis.speak(말);

    }}

    </script>
    """

    return 음성HTML


# =========================================================
# 현재 위치에서 가까운 역 찾기
# =========================================================

with st.spinner("현재 위치에서 가까운 지하철역을 찾고 있습니다."):

    가까운역 = 가까운역찾기(
        현재위도,
        현재경도
    )


if 가까운역 is None:

    st.error(
        "주변 지하철역을 찾지 못했습니다. "
        "잠시 후 다시 시도해주세요."
    )

    st.stop()


# =========================================================
# 가까운 역 정보
# =========================================================

역이름 = 가까운역["이름"]

역 = {
    "위도": 가까운역["위도"],
    "경도": 가까운역["경도"]
}


st.divider()

st.markdown("## 🚉 가장 가까운 지하철역")

st.markdown(
    f"""
    <div class="info-box">

    <h3>🚇 {역이름}</h3>

    <p>
    현재 위치에서 약
    <b>{거리표시(가까운역["거리"])}</b>
    떨어져 있습니다.
    </p>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 목적지 확인
# =========================================================

목적지역 = 주소찾기(
    목적지
)


if 목적지역 is None:

    st.error(
        "입력한 목적지를 찾지 못했습니다."
    )

    st.stop()


# =========================================================
# 현재 위치 → 지하철역
# =========================================================

현재위치 = {
    "위도": 현재위도,
    "경도": 현재경도
}


with st.spinner(
    f"{역이름}까지 실제 도보 경로를 계산하고 있습니다."
):

    역까지경로 = 도보경로찾기(
        현재위치,
        역
    )


if 역까지경로 is None:

    st.error(
        "현재 위치에서 지하철역까지의 "
        "도보 경로를 찾지 못했습니다."
    )

    st.stop()


# =========================================================
# 이동 정보
# =========================================================

거리 = 역까지경로["distance"]

시간 = 역까지경로["duration"]

예상시간 = max(
    1,
    round(시간 / 60)
)


st.markdown("## 🚶 현재 위치 → 지하철역")

st.markdown(
    f"""
    <div class="info-box">

    <b>출발</b><br>
    현재 위치

    <br><br>

    <b>도착</b><br>
    🚇 {역이름}

    <br><br>

    <b>거리</b><br>
    {거리표시(거리)}

    <br><br>

    <b>예상 시간</b><br>
    약 {예상시간}분

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 상세 지도
# =========================================================

st.markdown("## 🗺 역까지 가는 지도")

지도 = 지도만들기(
    역까지경로,
    현재위치,
    역
)

st.components.v1.html(
    지도,
    height=520
)


# =========================================================
# 상세 이동 순서
# =========================================================

st.markdown("## 🧭 역까지 이동 순서")

안내목록 = []


for 구간 in 역까지경로.get(
    "legs",
    []
):

    for 단계 in 구간.get(
        "steps",
        []
    ):

        거리값 = 단계.get(
            "distance",
            0
        )

        이동종류 = 단계.get(
            "maneuver",
            {}
        )

        종류 = 이동종류.get(
            "type",
            ""
        )

        수정 = 이동종류.get(
            "modifier",
            ""
        )

        도로이름 = 단계.get(
            "name",
            ""
        )

        도로이름 = 영어제거(
            도로이름
        )


        # ---------------------------------
        # 이동 방향
        # ---------------------------------

        if 수정 == "left":
            방향 = "왼쪽"

        elif 수정 == "right":
            방향 = "오른쪽"

        elif 수정 == "slight left":
            방향 = "왼쪽 방향"

        elif 수정 == "slight right":
            방향 = "오른쪽 방향"

        elif 수정 == "straight":
            방향 = "직진"

        else:
            방향 = ""


        # ---------------------------------
        # 안내 문장
        # ---------------------------------

        if 종류 == "depart":

            안내 = "현재 위치에서 출발하세요."

        elif 종류 == "arrive":

            안내 = f"{역이름}에 도착합니다."

        elif 방향 == "왼쪽":

            안내 = "왼쪽으로 이동하세요."

        elif 방향 == "오른쪽":

            안내 = "오른쪽으로 이동하세요."

        elif 방향 == "왼쪽 방향":

            안내 = "왼쪽 방향으로 이동하세요."

        elif 방향 == "오른쪽 방향":

            안내 = "오른쪽 방향으로 이동하세요."

        elif 방향 == "직진":

            안내 = "앞쪽으로 계속 직진하세요."

        else:

            안내 = "현재 방향으로 계속 이동하세요."


        # ---------------------------------
        # 도로 이름 추가
        # ---------------------------------

        if 도로이름:

            안내 += f" {도로이름}을 따라 이동하세요."


        안내목록.append(
            (
                안내,
                거리값
            )
        )


# 안내가 없는 경우
if not 안내목록:

    안내목록.append(
        (
            f"{역이름}까지 지도에 표시된 경로를 따라 이동하세요.",
            거리
        )
    )


# =========================================================
# 번호별 안내
# =========================================================

for 번호, 자료 in enumerate(
    안내목록,
    1
):

    안내 = 자료[0]

    거리값 = 자료[1]

    st.markdown(
        f"""
        <div class="step-box">

        <div class="step-title">
        {번호}. {안내}
        </div>

        <span class="distance">
        약 {거리표시(거리값)}
        </span>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 역 도착 후 안내
# =========================================================

st.markdown(
    f"""
    <div class="step-box">

    <div class="step-title">
    🚇 {역이름} 도착
    </div>

    역에 들어간 뒤 목적지인
    <b>{목적지}</b> 방향의 지하철 노선과
    승강장을 확인하세요.

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 음성 안내
# =========================================================

음성내용 = (
    f"현재 위치에서 {역이름}까지 이동하세요. "
    f"전체 거리는 {거리표시(거리)}이고 "
    f"예상 시간은 약 {예상시간}분입니다. "
)


for 번호, 자료 in enumerate(
    안내목록,
    1
):

    안내 = 자료[0]

    거리값 = 자료[1]

    음성내용 += (
        f"{번호}번째 안내입니다. "
        f"{안내} "
        f"약 {거리표시(거리값)}입니다. "
    )


음성내용 += (
    f"{역이름}에 도착하면 "
    f"{목적지} 방향의 지하철 노선을 확인하세요."
)


st.markdown("## 🔊 음성 안내")

st.components.v1.html(
    음성버튼(음성내용),
    height=100
)
