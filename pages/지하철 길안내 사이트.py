import streamlit as st
import requests
import math
import streamlit.components.v1 as components
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(
    page_title="지하철 길안내",
    page_icon="🚇",
    layout="centered"
)

st.title("🚇 지하철 길안내")
st.write("현재 위치에서 목적지까지 가는 길을 안내합니다.")

# -------------------------
# 현재 위치
# -------------------------

st.subheader("📍 현재 위치")

위치 = streamlit_geolocation()

if 위치 is None:
    st.info("위치 버튼을 눌러 현재 위치를 확인해주세요.")
    st.stop()

현재위도 = 위치.get("latitude")
현재경도 = 위치.get("longitude")

if 현재위도 is None or 현재경도 is None:
    st.info("현재 위치를 가져오지 못했습니다.")
    st.stop()

st.success("현재 위치를 확인했습니다.")

# -------------------------
# 목적지
# -------------------------

st.subheader("🎯 목적지")

목적지 = st.text_input(
    "목적지 역 이름",
    placeholder="예: 강남역"
)

찾기 = st.button(
    "🚇 길찾기",
    use_container_width=True
)

if not 찾기:
    st.stop()

if not 목적지.strip():
    st.warning("목적지 역을 입력해주세요.")
    st.stop()

# -------------------------
# 목적지 찾기
# -------------------------

try:
    응답 = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": "서울 " + 목적지 + " 지하철역",
            "format": "json",
            "limit": 1,
            "countrycodes": "kr"
        },
        headers={
            "User-Agent": "subway-guide-app"
        },
        timeout=10
    )

    응답.raise_for_status()
    결과 = 응답.json()

except Exception:
    st.error("목적지 위치를 찾는 중 문제가 발생했습니다.")
    st.stop()

if len(결과) == 0:
    st.warning("해당 역을 찾지 못했습니다.")
    st.stop()

역위도 = float(결과[0]["lat"])
역경도 = float(결과[0]["lon"])

# -------------------------
# 거리 계산
# -------------------------

def 거리계산(위도1, 경도1, 위도2, 경도2):

    R = 6371000

    위도1 = math.radians(위도1)
    위도2 = math.radians(위도2)

    위도차 = math.radians(위도2 - 위도1)
    경도차 = math.radians(경도2 - 경도1)

    a = (
        math.sin(위도차 / 2) ** 2
        + math.cos(위도1)
        * math.cos(위도2)
        * math.sin(경도차 / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


거리 = 거리계산(
    현재위도,
    현재경도,
    역위도,
    역경도
)

도보시간 = max(1, round(거리 / 70))

# -------------------------
# 결과
# -------------------------

st.divider()

st.subheader("🧭 이동 순서")

st.markdown("### 1️⃣ 현재 위치에서 역까지")

if 거리 < 1000:
    st.write(
        f"🚶 약 **{round(거리)}m**"
    )
else:
    st.write(
        f"🚶 약 **{거리 / 1000:.1f}km**"
    )

st.write(
    f"약 **{도보시간}분** 정도 걸립니다."
)

st.write(
    f"현재 위치에서 **{목적지}역**으로 이동하세요."
)

st.markdown("### 2️⃣ 역에 도착")

st.write(
    f"**{목적지}역**에 도착하면 지하철 표지판을 확인하세요."
)

st.write(
    "목적지 방향의 승강장으로 이동하세요."
)

st.markdown("### 3️⃣ 지하철 탑승")

st.write(
    "승강장의 행선지를 확인한 후 열차를 타세요."
)

st.write(
    "환승이 필요한 경우 안내 표지판을 따라 환승하세요."
)

st.markdown("### 4️⃣ 목적지 역")

st.write(
    f"**{목적지}역**에서 내리세요."
)

st.write(
    "내린 후 목적지에 가까운 출구를 찾아 역 밖으로 이동하세요."
)

# -------------------------
# 지도
# -------------------------

st.divider()

st.subheader("🗺 지도")

지도 = f"""
<!DOCTYPE html>
<html>
<head>
<link
rel="stylesheet"
href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<style>
#map {{
    width: 100%;
    height: 450px;
    border-radius: 15px;
}}
</style>
</head>

<body>

<div id="map"></div>

<script>

var 지도 = L.map("map").setView(
    [{현재위도}, {현재경도}],
    15
);

L.tileLayer(
    "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
    {{
        maxZoom: 19
    }}
).addTo(지도);

L.marker(
    [{현재위도}, {현재경도}]
).addTo(지도)
.bindPopup("현재 위치");

L.marker(
    [{역위도}, {역경도}]
).addTo(지도)
.bindPopup("{목적지}역");

L.polyline(
    [
        [{현재위도}, {현재경도}],
        [{역위도}, {역경도}]
    ],
    {{
        weight: 5
    }}
).addTo(지도);

</script>

</body>
</html>
"""

components.html(
    지도,
    height=470
)

# -------------------------
# 음성 안내
# -------------------------

st.divider()

st.subheader("🔊 음성 안내")

음성 = (
    f"현재 위치에서 {목적지}역으로 이동하세요. "
    f"역까지 약 {round(거리)}미터입니다. "
    f"도보로 약 {도보시간}분 정도 걸립니다. "
    f"{목적지}역에 도착하면 지하철 표지판을 확인하세요. "
    f"목적지 방향의 열차를 탑승하세요. "
    f"{목적지}역에서 내린 후 출구로 이동하세요."
)

음성코드 = f"""
<button
onclick="읽기()"
style="
width:100%;
padding:16px;
border:none;
border-radius:15px;
font-size:18px;
font-weight:bold;
"
>
🔊 길안내 듣기
</button>

<script>

function 읽기() {{

    speechSynthesis.cancel();

    var 문장 = new SpeechSynthesisUtterance(
        {repr(음성)}
    );

    문장.lang = "ko-KR";
    문장.rate = 0.9;
    문장.pitch = 1;
    문장.volume = 1;

    speechSynthesis.speak(문장);
}}

</script>
"""

components.html(
    음성코드,
    height=70
)
