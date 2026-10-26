import streamlit as st
import requests
import re
import html

st.set_page_config(
    page_title="도보 길찾기",
    page_icon="🚶",
    layout="centered"
)

# -----------------------------
# 기본 설정
# -----------------------------

st.markdown("""
<style>
body {
    background-color: #f7f9fc;
}

.main-title {
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 5px;
}

.sub-title {
    color: #666;
    margin-bottom: 25px;
}

.route-box {
    background: white;
    padding: 18px;
    border-radius: 18px;
    margin-top: 15px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
}

.step-box {
    background: #f8faff;
    padding: 14px;
    border-radius: 14px;
    margin: 8px 0;
    border-left: 5px solid #4f7cff;
}

.distance {
    color: #4f7cff;
    font-weight: 700;
}

button {
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 주소 검색
# -----------------------------

def 위치찾기(장소):
    try:
        주소 = 장소.strip()

        if not 주소:
            return None

        url = "https://nominatim.openstreetmap.org/search"

        params = {
            "q": 주소,
            "format": "json",
            "limit": 1,
            "countrycodes": "kr"
        }

        headers = {
            "User-Agent": "walking-route-app"
        }

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
            "위도": float(data[0]["lat"]),
            "경도": float(data[0]["lon"]),
            "이름": data[0].get("display_name", 주소)
        }

    except Exception:
        return None


# -----------------------------
# 영어 제거
# -----------------------------

def 영어제거(문장):
    if not 문장:
        return ""

    문장 = re.sub(r"[A-Za-z]+", "", 문장)
    문장 = re.sub(r"\s+", " ", 문장)

    return 문장.strip()


# -----------------------------
# 이동 방법 한국어 변환
# -----------------------------

def 이동설명(문장):

    문장 = 영어제거(문장)

    if not 문장:
        return "앞으로 계속 이동하세요."

    문장 = 문장.replace("우회전", "오른쪽으로 이동하세요.")
    문장 = 문장.replace("좌회전", "왼쪽으로 이동하세요.")

    return 문장


# -----------------------------
# 도보 경로 검색
# -----------------------------

def 경로찾기(출발, 도착):

    try:

        url = (
            f"https://router.project-osrm.org/route/v1/"
            f"foot/{출발['경도']},{출발['위도']};"
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


# -----------------------------
# 거리 표시
# -----------------------------

def 거리표시(거리):

    if 거리 >= 1000:
        return f"{거리 / 1000:.1f}km"

    return f"{int(거리)}m"


# -----------------------------
# 지도 만들기
# -----------------------------

def 지도만들기(경로, 출발, 도착):

    좌표 = 경로["geometry"]["coordinates"]

    지도좌표 = []

    for 경도, 위도 in 좌표:
        지도좌표.append([위도, 경도])

    지도좌표_문자열 = str(지도좌표)

    시작점 = [출발["위도"], 출발["경도"]]
    도착점 = [도착["위도"], 도착["경도"]]

    시작점_문자열 = str(시작점)
    도착점_문자열 = str(도착점)

    지도_html = f"""
    <div style="
        width:100%;
        height:520px;
        border-radius:18px;
        overflow:hidden;
        box-shadow:0 3px 15px rgba(0,0,0,0.12);
    ">
        <div id="지도" style="width:100%;height:100%;"></div>
    </div>

    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    />

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <script>

        const 지도 = L.map('지도');

        L.tileLayer(
            'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
            {{
                maxZoom: 19
            }}
        ).addTo(지도);

        const 경로 = {지도좌표_문자열};

        const 시작점 = {시작점_문자열};
        const 도착점 = {도착점_문자열};

        L.polyline(
            경로,
            {{
                weight: 6
            }}
        ).addTo(지도);

        L.marker(시작점)
            .addTo(지도)
            .bindPopup("출발지");

        L.marker(도착점)
            .addTo(지도)
            .bindPopup("도착지");

        const 경로범위 = L.latLngBounds(경로);

        지도.fitBounds(
            경로범위,
            {{
                padding: [30, 30]
            }}
        );

    </script>
    """

    return 지도_html


# -----------------------------
# 음성 안내
# -----------------------------

def 음성안내(문장):

    안전한문장 = html.escape(문장)

    return f"""
    <div style="
        background:white;
        padding:18px;
        border-radius:18px;
        box-shadow:0 3px 12px rgba(0,0,0,0.08);
        margin-top:15px;
    ">

        <button
            onclick="말하기()"
            style="
                width:100%;
                padding:14px;
                border:none;
                background:#4f7cff;
                color:white;
                font-size:17px;
                font-weight:bold;
                cursor:pointer;
            "
        >
            🔊 음성으로 듣기
        </button>

    </div>

    <script>

        function 말하기() {{

            window.speechSynthesis.cancel();

            const 음성 = new SpeechSynthesisUtterance(
                "{안전한문장}"
            );

            음성.lang = "ko-KR";
            음성.rate = 0.9;
            음성.pitch = 1.0;
            음성.volume = 1.0;

            window.speechSynthesis.speak(음성);
        }}

    </script>
    """


# -----------------------------
# 화면
# -----------------------------

st.markdown(
    '<div class="main-title">🚶 도보 길찾기</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">출발지와 도착지를 입력하면 가장 간단한 도보 경로를 찾아줍니다.</div>',
    unsafe_allow_html=True
)


# -----------------------------
# 입력
# -----------------------------

with st.form("길찾기폼"):

    출발지 = st.text_input(
        "출발지",
        placeholder="예: 서울역"
    )

    도착지 = st.text_input(
        "도착지",
        placeholder="예: 명동역"
    )

    찾기버튼 = st.form_submit_button(
        "🔎 경로 찾기",
        use_container_width=True
    )


# -----------------------------
# 검색 실행
# -----------------------------

if 찾기버튼:

    # 아무것도 입력하지 않은 경우
    if not 출발지.strip() and not 도착지.strip():

        st.warning("출발지와 도착지를 모두 입력해주세요.")

    # 출발지만 입력
    elif not 출발지.strip():

        st.warning("출발지를 입력해주세요.")

    # 도착지만 입력
    elif not 도착지.strip():

        st.warning("도착지를 입력해주세요.")

    else:

        with st.spinner("경로를 찾고 있습니다..."):

            출발정보 = 위치찾기(출발지)
            도착정보 = 위치찾기(도착지)

            if 출발정보 is None:

                st.error(
                    "출발지를 찾을 수 없습니다. 장소 이름을 조금 더 정확하게 입력해주세요."
                )

            elif 도착정보 is None:

                st.error(
                    "도착지를 찾을 수 없습니다. 장소 이름을 조금 더 정확하게 입력해주세요."
                )

            else:

                경로정보 = 경로찾기(
                    출발정보,
                    도착정보
                )

                if 경로정보 is None:

                    st.error(
                        "현재 도보 경로를 찾을 수 없습니다. 다른 장소를 입력해보세요."
                    )

                else:

                    # -----------------------------
                    # 기본 정보
                    # -----------------------------

                    거리 = 경로정보["distance"]
                    시간 = 경로정보["duration"]

                    예상시간 = max(
                        1,
                        round(시간 / 60)
                    )

                    st.markdown(
                        '<div class="route-box">',
                        unsafe_allow_html=True
                    )

                    st.subheader("📍 이동 정보")

                    st.write(
                        f"**출발:** {출발지}"
                    )

                    st.write(
                        f"**도착:** {도착지}"
                    )

                    st.write(
                        f"**거리:** {거리표시(거리)}"
                    )

                    st.write(
                        f"**예상 시간:** 약 {예상시간}분"
                    )

                    st.markdown(
                        '</div>',
                        unsafe_allow_html=True
                    )


                    # -----------------------------
                    # 지도
                    # -----------------------------

                    st.markdown("### 🗺 지도")

                    지도 = 지도만들기(
                        경로정보,
                        출발정보,
                        도착정보
                    )

                    st.components.v1.html(
                        지도,
                        height=540
                    )


                    # -----------------------------
                    # 길안내
                    # -----------------------------

                    st.markdown("### 🚶 길안내")

                    단계목록 = []

                    for 구간 in 경로정보.get("legs", []):

                        for 단계 in 구간.get("steps", []):

                            거리값 = 단계.get("distance", 0)

                            설명 = 단계.get(
                                "name",
                                ""
                            )

                            설명 = 영어제거(
                                설명
                            )

                            if 설명:

                                안내 = f"{설명} 방향으로 계속 이동하세요."

                            else:

                                안내 = "앞으로 계속 이동하세요."

                            단계목록.append(
                                (
                                    안내,
                                    거리값
                                )
                            )


                    if not 단계목록:

                        단계목록 = [
                            (
                                "목적지까지 지도에 표시된 길을 따라 이동하세요.",
                                거리
                            )
                        ]


                    for 번호, (안내, 거리값) in enumerate(
                        단계목록,
                        1
                    ):

                        st.markdown(
                            f"""
                            <div class="step-box">
                                <b>{번호}. {안내}</b>
                                <br>
                                <span class="distance">
                                    약 {거리표시(거리값)}
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )


                    # -----------------------------
                    # 전체 음성 안내
                    # -----------------------------

                    음성문장 = (
                        f"출발지는 {출발지}입니다. "
                        f"도착지는 {도착지}입니다. "
                        f"전체 거리는 {거리표시(거리)}이고 "
                        f"예상 시간은 약 {예상시간}분입니다. "
                    )

                    for 번호, (안내, 거리값) in enumerate(
                        단계목록,
                        1
                    ):

                        음성문장 += (
                            f"{번호}번째, "
                            f"{안내} "
                            f"약 {거리표시(거리값)입니다. "
                        )

                    st.markdown(
                        음성안내(음성문장),
                        unsafe_allow_html=True
                    )
