import streamlit as st
import requests
import math
import streamlit.components.v1 as components

from streamlit_gps_location import gps_location_button


# =========================
# 기본 설정
# =========================

st.set_page_config(
    page_title="지하철 길안내",
    page_icon="🚇",
    layout="centered"
)

st.markdown("""
<style>
.제목 {
    font-size: 32px;
    font-weight: 800;
}

.설명 {
    color: #666;
    margin-bottom: 20px;
}

.단계 {
    background: #f5f7fa;
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 12px;
}

.단계제목 {
    font-size: 19px;
    font-weight: bold;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


st.markdown(
    '<div class="제목">🚇 지하철 길안내</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="설명">현재 위치에서 목적지까지 가는 길을 안내합니다.</div>',
    unsafe_allow_html=True
)


# =========================
# 현재 위치
# =========================

st.markdown("## 📍 현재 위치")

위치 = gps_location_button(
    buttonText="📍 현재 위치 가져오기"
)


# 위치를 아직 가져오지 않았을 때
if not 위치:
    st.info("위 버튼을 눌러 현재 위치를 허용해주세요.")
    st.stop()


# =========================
# 위치 정보 확인
# =========================

현재위도 = 위치.get("latitude")
현재경도 = 위치.get("longitude")


if 현재위도 is None or 현재경도 is None:
    st.warning("현재 위치를 가져오지 못했습니다.")
    st.stop()


st.success("현재 위치를 확인했습니다.")


# =========================
# 목적지
# =========================

st.markdown("## 🎯 목적지")

목적지 = st.text_input(
    "목적지 역",
    placeholder="예: 강남역"
)

길찾기 = st.button(
    "🚇 길찾기 시작",
    use_container_width=True
)


# 목적지를 입력하지 않았으면 아무것도 표시하지 않음
if not 길찾기:
    st.stop()

if 목적지.strip() == "":
    st.warning("목적지 역을 입력해주세요.")
    st.stop()


목적지 = 목적지.strip()


# =========================
# 목적지 역 찾기
# =========================

try:

    응답 = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": f"서울 {목적지} 지하철역",
            "format": "json",
            "limit": 5,
            "countrycodes": "kr"
        },
        headers={
            "User-Agent": "seoul-subway-guide"
        },
        timeout=10
    )

    응답.raise_for_status()

    결과 = 응답.json()

except requests.exceptions.Timeout:

    st.error("역 정보를 가져오는 데 시간이 너무 오래 걸렸습니다.")
    st.stop()

except requests.exceptions.RequestException:

    st.error("역 정보를 가져오지 못했습니다.")
    st.stop()

except Exception:

    st.error("역을 찾는 중 문제가 발생했습니다.")
    st.stop()


if len(결과) == 0:

    st.warning(
        f"'{목적지}'역을 찾지 못했습니다."
    )

    st.stop()


# 첫 번째 검색 결과
역위도 = float(결과[0]["lat"])
역경도 = float(결과[0]["lon"])


# =========================
# 거리 계산
# =========================

def 거리계산(lat1, lon1, lat2, lon2):

    지구반지름 = 6371000

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    위도차 = math.radians(lat2 - lat1)
    경도차 = math.radians(lon2 - lon1)

    a = (
        math.sin(위도차 / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(경도차 / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return 지구반지름 * c


거리 = 거리계산(
    현재위도,
    현재경도,
    역위도,
    역경도
)


도보시간 = max(
    1,
    round(거리 / 75)
)


# =========================
# 길안내
# =========================

st.divider()

st.markdown("## 🧭 이동 순서")


st.markdown(
    f"""
<div class="단계">
<div class="단계제목">1️⃣ 현재 위치에서 역까지</div>

현재 위치에서 <b>{목적지}역</b>으로 이동하세요.

<br><br>

🚶 거리: 약 <b>{round(거리)}m</b><br>
⏱ 예상 시간: 약 <b>{도보시간}분</b>

</div>
""",
    unsafe_allow_html=True
)


st.markdown(
    f"""
<div class="단계">
<div class="단계제목">2️⃣ {목적지}역으로 들어가기</div>

{목적지}역에 도착하면 지하철 출입구를 통해 역 안으로 들어갑니다.

</div>
""",
    unsafe_allow_html=True
)


st.markdown(
    """
<div class="단계">
<div class="단계제목">3️⃣ 승강장 찾기</div>

역 안의 노선 표지판을 확인하고 목적지 방향의 승강장으로 이동하세요.
</div>
""",
    unsafe_allow_html=True
)


st.markdown(
    """
<div class="단계">
<div class="단계제목">4️⃣ 지하철 탑승</div>

전광판에서 열차의 진행 방향을 확인한 뒤 탑승하세요.
</div>
""",
    unsafe_allow_html=True
)


st.markdown(
    f"""
<div class="단계">
<div class="단계제목">5️⃣ {목적지}역에서 하차</div>

{목적지}역에 도착하면 열차에서 내리세요.
</div>
""",
    unsafe_allow_html=True
)


st.markdown(
    """
<div class="단계">
<div class="단계제목">6️⃣ 출구로 이동</div>

안내 표지판을 확인하고 목적지와 가까운 출구로 나가세요.
</div>
""",
    unsafe_allow_html=True
)


# =========================
# 지도
# =========================

st.divider()

st.markdown("## 🗺 지도")


지도 = f"""
<!DOCTYPE html>
<html>

<head>

<link
rel="stylesheet"
href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
/>

<script
src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
</script>

<style>

#map {{
    width: 100%;
    height: 450px;
    border-radius: 18px;
}}

</style>

</head>

<body>

<div id="map"></div>

<script>

var map = L.map("map").setView(
    [{현재위도}, {현재경도}],
    15
);

L.tileLayer(
    "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
    {{
        maxZoom: 19
    }}
).addTo(map);


L.marker(
    [{현재위도}, {현재경도}]
)
.addTo(map)
.bindPopup("현재 위치");


L.marker(
    [{역위도}, {역경도}]
)
.addTo(map)
.bindPopup("목적지 역");


L.polyline(
    [
        [{현재위도}, {현재경도}],
        [{역위도}, {역경도}]
    ],
    {{
        weight: 5
    }}
).addTo(map);

</script>

</body>
</html>
"""


components.html(
    지도,
    height=470
)


# =========================
# 음성 안내
# =========================

st.divider()

st.markdown("## 🔊 음성 안내")


음성 = (
    f"현재 위치에서 {목적지}역으로 이동하세요. "
    f"역까지 약 {round(거리)}미터입니다. "
    f"도보로 약 {도보시간}분 정도 걸립니다. "
    f"{목적지}역에 도착하면 지하철 표지판을 확인하세요. "
    f"목적지 방향의 승강장으로 이동하세요. "
    f"{목적지}역에서 내린 후 출구로 이동하세요."
)


음성코드 = f"""
<button
onclick="읽기()"
style="
width:100%;
height:55px;
border:none;
border-radius:15px;
font-size:18px;
font-weight:bold;
cursor:pointer;
">
🔊 길안내 듣기
</button>

<script>

function 읽기() {{

    window.speechSynthesis.cancel();

    var 문장 = new SpeechSynthesisUtterance(
        {음성!r}
    );

    문장.lang = "ko-KR";
    문장.rate = 0.9;
    문장.pitch = 1;
    문장.volume = 1;

    window.speechSynthesis.speak(문장);
}}

</script>
"""


components.html(
    음성코드,
    height=70
)
