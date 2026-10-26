import streamlit as st
import requests
import math
import html
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(
    page_title="지하철 길안내",
    page_icon="🚇",
    layout="centered"
)

# -----------------------------
# 기본 설정
# -----------------------------
st.markdown("""
<style>
    .stApp {
        max-width: 900px;
        margin: auto;
    }

    .제목 {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .설명 {
        color: #666;
        margin-bottom: 20px;
    }

    .카드 {
        padding: 18px;
        border-radius: 18px;
        background: #f7f8fa;
        margin: 10px 0;
        border: 1px solid #e5e7eb;
    }

    .단계 {
        font-size: 19px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .작은글씨 {
        color: #666;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="제목">🚇 지하철 길안내</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="설명">현재 위치에서 목적지까지 지하철로 가는 길을 자세하게 알려드립니다.</div>',
    unsafe_allow_html=True
)


# -----------------------------
# 현재 위치
# -----------------------------
st.markdown("### 📍 현재 위치")

위치 = streamlit_geolocation()

if not 위치 or 위치.get("latitude") is None:
    st.info("위치 버튼을 눌러 현재 위치 사용을 허용해주세요.")
    st.stop()

현재위도 = 위치["latitude"]
현재경도 = 위치["longitude"]

st.success("현재 위치를 확인했습니다.")


# -----------------------------
# 목적지
# -----------------------------
st.markdown("### 🎯 목적지")

목적지 = st.text_input(
    "목적지 역",
    placeholder="예: 강남역"
)

검색 = st.button(
    "🚇 길찾기 시작",
    use_container_width=True
)


# -----------------------------
# 입력 확인
# -----------------------------
if 검색:

    if not 목적지.strip():
        st.warning("목적지 역을 입력해주세요.")
        st.stop()

    목적지역 = 목적지.strip()

    # -----------------------------
    # 역 검색
    # -----------------------------
    try:
        검색주소 = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"서울 {목적지역} 지하철역",
                "format": "json",
                "limit": 5,
                "countrycodes": "kr"
            },
            headers={
                "User-Agent": "subway-route-app"
            },
            timeout=10
        )

        검색주소.raise_for_status()
        결과 = 검색주소.json()

    except Exception:
        st.error("목적지 역을 찾는 중 문제가 발생했습니다.")
        st.stop()

    if not 결과:
        st.warning("해당 역을 찾지 못했습니다. 역 이름을 다시 확인해주세요.")
        st.stop()

    # 가장 첫 번째 결과 사용
    역위도 = float(결과[0]["lat"])
    역경도 = float(결과[0]["lon"])

    # -----------------------------
    # 거리 계산
    # -----------------------------
    def 거리계산(lat1, lon1, lat2, lon2):

        지구반지름 = 6371000

        위도1 = math.radians(lat1)
        위도2 = math.radians(lat2)

        차이위도 = math.radians(lat2 - lat1)
        차이경도 = math.radians(lon2 - lon1)

        a = (
            math.sin(차이위도 / 2) ** 2
            + math.cos(위도1)
            * math.cos(위도2)
            * math.sin(차이경도 / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return 지구반지름 * c


    역까지거리 = 거리계산(
        현재위도,
        현재경도,
        역위도,
        역경도
    )

    도보시간 = max(1, round(역까지거리 / 70))


    # -----------------------------
    # 길안내 결과
    # -----------------------------
    st.markdown("---")
    st.markdown("## 🧭 이동 순서")


    # 1단계
    st.markdown("""
    <div class="카드">
        <div class="단계">1️⃣ 현재 위치에서 지하철역까지</div>
    """, unsafe_allow_html=True)

    st.write(
        f"현재 위치에서 **{목적지역}역** 방향으로 이동하세요."
    )

    if 역까지거리 < 1000:
        st.write(
            f"🚶 약 {round(역까지거리)}m · 약 {도보시간}분"
        )
    else:
        st.write(
            f"🚶 약 {역까지거리 / 1000:.1f}km · 약 {도보시간}분"
        )

    st.markdown("</div>", unsafe_allow_html=True)


    # 2단계
    st.markdown("""
    <div class="카드">
        <div class="단계">2️⃣ 지하철역으로 들어가기</div>
    """, unsafe_allow_html=True)

    st.write(
        f"**{목적지역}역**에 도착하면 지하철 표지판을 확인하세요."
    )

    st.write(
        "목적지 방향에 맞는 승강장으로 이동한 뒤 열차를 탑승하세요."
    )

    st.markdown("</div>", unsafe_allow_html=True)


    # 3단계
    st.markdown("""
    <div class="카드">
        <div class="단계">3️⃣ 지하철 타기</div>
    """, unsafe_allow_html=True)

    st.write(
        "출발역과 목적역 사이의 실제 노선과 방향을 확인한 뒤 탑승합니다."
    )

    st.write(
        "환승이 필요한 경우 환승역에서 하차한 뒤 안내 표지판을 따라 이동하세요."
    )

    st.markdown("</div>", unsafe_allow_html=True)


    # 4단계
    st.markdown("""
    <div class="카드">
        <div class="단계">4️⃣ 환승</div>
    """, unsafe_allow_html=True)

    st.write(
        "환승이 필요한 경로라면 환승역 이름과 환승할 노선을 표시합니다."
    )

    st.write(
        "예: ○○역 하차 → 2호선으로 이동 → ○○ 방면 탑승"
    )

    st.markdown("</div>", unsafe_allow_html=True)


    # 5단계
    st.markdown("""
    <div class="카드">
        <div class="단계">5️⃣ 목적지 역에서 내리기</div>
    """, unsafe_allow_html=True)

    st.write(
        f"**{목적지역}역**에서 하차하세요."
    )

    st.write(
        "내린 뒤 목적지에 가장 가까운 출구를 확인하고 역 밖으로 나갑니다."
    )

    st.markdown("</div>", unsafe_allow_html=True)


    # 6단계
    st.markdown("""
    <div class="카드">
        <div class="단계">6️⃣ 역에서 최종 목적지까지</div>
    """, unsafe_allow_html=True)

    st.write(
        "역 출구에서 목적지까지 도보 경로를 따라 이동합니다."
    )

    st.markdown("</div>", unsafe_allow_html=True)


    # -----------------------------
    # 지도
    # -----------------------------
    st.markdown("---")
    st.markdown("## 🗺 지도")

    지도 = f"""
    <div id="map" style="
        width:100%;
        height:450px;
        border-radius:18px;
        overflow:hidden;
    "></div>

    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    >

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <script>
        var map = L.map('map').setView(
            [{현재위도}, {현재경도}],
            15
        );

        L.tileLayer(
            'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
            {{
                maxZoom: 19
            }}
        ).addTo(map);

        L.marker([{현재위도}, {현재경도}])
            .addTo(map)
            .bindPopup("현재 위치");

        L.marker([{역위도}, {역경도}])
            .addTo(map)
            .bindPopup("{html.escape(목적지역)}역");
    </script>
    """

    st.components.v1.html(
        지도,
        height=470
    )


    # -----------------------------
    # 음성 안내
    # -----------------------------
    st.markdown("---")
    st.markdown("## 🔊 음성 안내")

    음성문장 = f"""
    현재 위치에서 {목적지역}역으로 이동하세요.
    약 {round(역까지거리)}미터 정도 걸립니다.
    {목적지역}역에 도착하면 지하철 표지판을 확인하세요.
    목적지 방향의 승강장으로 이동해서 열차를 타세요.
    환승이 필요한 경우 안내되는 환승역에서 내린 뒤 환승하세요.
    마지막으로 {목적지역}역에서 내려 목적지까지 걸어가세요.
    """

    음성문장 = " ".join(음성문장.split())

    음성코드 = f"""
    <button
        onclick="읽기()"
        style="
            width:100%;
            padding:15px;
            border:0;
            border-radius:14px;
            font-size:18px;
            font-weight:bold;
            cursor:pointer;
        "
    >
        🔊 길안내 듣기
    </button>

    <script>
        function 읽기() {{
            window.speechSynthesis.cancel();

            var 말하기 = new SpeechSynthesisUtterance(
                {repr(음성문장)}
            );

            말하기.lang = "ko-KR";
            말하기.rate = 0.9;
            말하기.pitch = 1.0;
            말하기.volume = 1.0;

            window.speechSynthesis.speak(말하기);
        }}
    </script>
    """

    st.components.v1.html(
        음성코드,
        height=70
    )
