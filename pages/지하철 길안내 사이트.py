import streamlit as st
import requests
import re
import html

st.set_page_config(
    page_title="도보 길찾기",
    page_icon="🚶",
    layout="centered"
)

# =========================
# 화면 디자인
# =========================

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
    padding: 15px;
    margin: 8px 0;
    border-radius: 12px;
}

.distance {
    color: #4f6fff;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 주소 찾기
# =========================

def 주소찾기(장소):

    try:
        if not 장소 or not 장소.strip():
            return None

        url = "https://nominatim.openstreetmap.org/search"

        params = {
            "q": 장소.strip(),
            "format": "json",
            "limit": 1,
            "countrycodes": "kr"
        }

        headers = {
            "User-Agent": "Korean-Walking-Route-App"
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if len(data) == 0:
            return None

        return {
            "위도": float(data[0]["lat"]),
            "경도": float(data[0]["lon"])
        }

    except Exception:
        return None


# =========================
# 영어 제거
# =========================

def 영어제거(문장):

    if not 문장:
        return ""

    문장 = re.sub(r"[A-Za-z]+", "", 문장)
    문장 = re.sub(r"\s+", " ", 문장)

    return 문장.strip()


# =========================
# 거리 표시
# =========================

def 거리표시(거리):

    if 거리 < 1000:
        return f"{int(거리)}m"

    return f"{거리 / 1000:.1f}km"


# =========================
# 도보 경로 찾기
# =========================

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

        return data["routes"][0]

    except Exception:
        return None


# =========================
# 지도
# =========================

def 지도만들기(경로, 출발, 도착):

    좌표 = 경로["geometry"]["coordinates"]

    지도좌표 = []

    for 경도, 위도 in 좌표:
        지도좌표.append([위도, 경도])

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
        html, body {{
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
            .bindPopup("출발지");

        L.marker(end)
            .addTo(map)
            .bindPopup("도착지");

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


# =========================
# 음성
# =========================

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


# =========================
# 제목
# =========================

st.markdown(
    '<div class="main-title">🚶 도보 길찾기</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">출발지와 도착지를 입력하면 도보 경로를 찾아줍니다.</div>',
    unsafe_allow_html=True
)


# =========================
# 입력
# =========================

with st.form("길찾기"):

    출발지 = st.text_input(
        "출발지",
        placeholder="예: 서울역"
    )

    도착지 = st.text_input(
        "도착지",
        placeholder="예: 명동역"
    )

    검색 = st.form_submit_button(
        "🔎 경로 찾기",
        use_container_width=True
    )


# =========================
# 경로 검색
# =========================

if 검색:

    # 아무것도 입력하지 않은 경우
    if not 출발지.strip() and not 도착지.strip():

        st.warning(
            "출발지와 도착지를 입력해주세요."
        )

    # 출발지만 없는 경우
    elif not 출발지.strip():

        st.warning(
            "출발지를 입력해주세요."
        )

    # 도착지만 없는 경우
    elif not 도착지.strip():

        st.warning(
            "도착지를 입력해주세요."
        )

    # 둘 다 입력한 경우
    else:

        with st.spinner("경로를 찾고 있습니다."):

            출발 = 주소찾기(출발지)

            도착 = 주소찾기(도착지)

        if 출발 is None:

            st.error(
                "출발지를 찾지 못했습니다."
            )

        elif 도착 is None:

            st.error(
                "도착지를 찾지 못했습니다."
            )

        else:

            with st.spinner("도보 경로를 계산하고 있습니다."):

                경로 = 도보경로찾기(
                    출발,
                    도착
                )

            if 경로 is None:

                st.error(
                    "도보 경로를 찾지 못했습니다."
                )

            else:

                # =========================
                # 이동 정보
                # =========================

                거리 = 경로["distance"]

                시간 = 경로["duration"]

                예상시간 = max(
                    1,
                    round(시간 / 60)
                )

                st.markdown(
                    '<div class="info-box">',
                    unsafe_allow_html=True
                )

                st.subheader("📍 이동 정보")

                st.write(
                    f"출발지 : **{출발지}**"
                )

                st.write(
                    f"도착지 : **{도착지}**"
                )

                st.write(
                    f"거리 : **{거리표시(거리)}**"
                )

                st.write(
                    f"예상 시간 : **약 {예상시간}분**"
                )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )


                # =========================
                # 지도
                # =========================

                st.markdown("## 🗺 지도")

                지도 = 지도만들기(
                    경로,
                    출발,
                    도착
                )

                st.components.v1.html(
                    지도,
                    height=520
                )


                # =========================
                # 길안내
                # =========================

                st.markdown("## 🚶 길안내")

                안내목록 = []

                for 구간 in 경로.get("legs", []):

                    for 단계 in 구간.get("steps", []):

                        거리값 = 단계.get(
                            "distance",
                            0
                        )

                        도로이름 = 단계.get(
                            "name",
                            ""
                        )

                        도로이름 = 영어제거(
                            도로이름
                        )

                        if 도로이름:

                            안내 = (
                                f"{도로이름}을 따라 "
                                f"계속 이동하세요."
                            )

                        else:

                            안내 = (
                                "현재 방향으로 "
                                "계속 이동하세요."
                            )

                        안내목록.append(
                            (
                                안내,
                                거리값
                            )
                        )


                if not 안내목록:

                    안내목록.append(
                        (
                            "지도에 표시된 길을 따라 이동하세요.",
                            거리
                        )
                    )


                for 번호, 자료 in enumerate(
                    안내목록,
                    1
                ):

                    안내 = 자료[0]
                    거리값 = 자료[1]

                    st.markdown(
                        f"""
                        <div class="step-box">

                        <b>
                        {번호}. {안내}
                        </b>

                        <br>

                        <span class="distance">
                        약 {거리표시(거리값)}
                        </span>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                # =========================
                # 음성
                # =========================

                음성내용 = (
                    f"출발지는 {출발지}입니다. "
                    f"도착지는 {도착지}입니다. "
                    f"전체 거리는 {거리표시(거리)}입니다. "
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


                st.markdown(
                    "## 🔊 음성 안내"
                )

                st.components.v1.html(
                    음성버튼(음성내용),
                    height=100
                )
