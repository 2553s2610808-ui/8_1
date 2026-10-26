import streamlit as st
import requests
import math
import streamlit.components.v1 as components

from streamlit_geolocation import streamlit_geolocation


# ==========================================
# 기본 설정
# ==========================================

st.set_page_config(
    page_title="지하철 길찾기",
    page_icon="🚇",
    layout="centered"
)


# ==========================================
# 화면 디자인
# ==========================================

st.markdown("""
<style>

.main-title {
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 5px;
}

.sub-title {
    color: #666666;
    margin-bottom: 25px;
}

.step-box {
    padding: 18px;
    border-radius: 16px;
    background: #f5f7fa;
    border: 1px solid #e2e5e9;
    margin-bottom: 12px;
}

.step-title {
    font-size: 19px;
    font-weight: 700;
    margin-bottom: 8px;
}

</style>
""", unsafe_allow_html=True)


st.markdown(
    '<div class="main-title">🚇 지하철 길찾기</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">현재 위치에서 목적지까지 가는 길을 안내합니다.</div>',
    unsafe_allow_html=True
)


# ==========================================
# 현재 위치
# ==========================================

st.markdown("## 📍 현재 위치")

위치 = streamlit_geolocation()


if 위치 is None:
    st.info("위치 버튼을 눌러 현재 위치를 확인해주세요.")
    st.stop()


현재위도 = 위치.get("latitude")
현재경도 = 위치.get("longitude")


if 현재위도 is None or 현재경도 is None:

    st.warning(
        "현재 위치를 가져오지 못했습니다. "
        "브라우저에서 위치 권한을 허용해주세요."
    )

    st.stop()


st.success("현재 위치를 확인했습니다.")


# ==========================================
# 목적지
# ==========================================

st.markdown("## 🎯 목적지")

목적지 = st.text_input(
    "목적지 역",
    placeholder="예: 강남역"
)


찾기 = st.button(
    "🚇 길찾기 시작",
    use_container_width=True
)


# 아무것도 누르지 않았으면 지도 표시 안 함
if not 찾기:
    st.stop()


# ==========================================
# 목적지 입력 확인
# ==========================================

목적지 = 목적지.strip()


if 목적지 == "":
    st.warning("목적지 역을 입력해주세요.")
    st.stop()


# ==========================================
# 목적지 역 위치 찾기
# ==========================================

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
            "User-Agent": "subway-route-app"
        },
        timeout=10
    )

    응답.raise_for_status()

    검색결과 = 응답.json()

except requests.exceptions.Timeout:

    st.error("역 위치를 찾는 데 시간이 너무 오래 걸렸습니다.")
    st.stop()

except requests.exceptions.RequestException:

    st.error("역 위치를 찾는 서버에 연결하지 못했습니다.")
    st.stop()

except Exception:

    st.error("역 위치를 찾는 중 문제가 발생했습니다.")
    st.stop()


if not 검색결과:

    st.warning(
        f"'{목적지}'역을 찾지 못했습니다. "
        "역 이름을 다시 확인해주세요."
    )

    st.stop()


# ==========================================
# 목적지 좌표
# ==========================================

역위도 = float(검색결과[0]["lat"])
역경도 = float(검색결과[0]["lon"])


# ==========================================
# 거리 계산
# ==========================================

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


# ==========================================
# 예상 도보 시간
# ==========================================

도보시간 = max(
    1,
    round(거리 / 75)
)


# ==========================================
# 길안내
# ==========================================

st.divider()

st.markdown("## 🧭 이동 순서")


st.markdown("""
<div class="step-box">

<div class="step-title">
1️⃣ 현재 위치 → 지하철역
</div>

현재 위치에서 목적지 역으로 이동합니다.

</div>
""", unsafe_allow_html=True)


if 거리 < 1000:

    st.write(
        f"🚶 거리: 약 **{round(거리)}m**"
    )

else:

    st.write(
        f"🚶 거리: 약 **{거리 / 1000:.1f}km**"
    )


st.write(
    f"⏱ 예상 도보 시간: 약 **{도보시간}분**"
)


st.markdown(
    f"""
<div class="step-box">

<div class="step-title">
2️⃣ {목적지}역으로 들어가기
</div>

{목적지}역에 도착하면 지하철 출입구를 통해 역 안으로 들어갑니다.

</div>
""",
    unsafe_allow_html=True
)


st.markdown(
    """
<div class="step-box">

<div class="step-title">
3️⃣ 지하철 승강장 찾기
</div>

지하철역 안에서 목적지 방향의 승강장 표지판을 확인합니다.

</div>
""",
    unsafe_allow_html=True
)


st.markdown(
    """
<div class="step-box">

<div class="step-title">
4️⃣ 지하철 탑승
</div>

목적지 방향의 열차를 확인한 후 탑승합니다.

</div>
""",
    unsafe_allow_html=True
)


st.markdown(
    f"""
<div class="step-box">

<div class="step-title">
5️⃣ {목적지}역에서 하차
</div>

{목적지}역에 도착하면 열차에서 내립니다.

</div>
""",
    unsafe_allow_html=True
)


st.markdown(
    """
<div class="step-box">

<div class="step-title">
6️⃣ 역 밖으로 이동
</div>

목적지에 가까운 출구를 확인한 후 역 밖으로 나갑니다.

</div>
""",
    unsafe_allow_html=True
)


# ==========================================
# 지도
# ==========================================

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
    height: 430px;
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
)
.addTo(map);

</script>

</body>

</html>
"""


components.html(
    지도,
    height=450
)


# ==========================================
# 음성 안내
# ==========================================

st.divider()

st.markdown("## 🔊 음성 안내")


음성내용 = (
    f"현재 위치에서 {목적지}역으로 이동하세요. "
    f"역까지 약 {round(거리)}미터입니다. "
    f"도보로 약 {도보시간}분 정도 걸립니다. "
    f"{목적지}역에 도착하면 지하철 표지판을 확인하세요. "
    f"목적지 방향의 열차를 탑승하세요. "
    f"{목적지}역에서 내리세요."
)


음성내용 = " ".join(음성내용.split())


음성화면 = f"""
<button
onclick="말하기()"
style="
width:100%;
height:55px;
border:0;
border-radius:15px;
font-size:18px;
font-weight:bold;
cursor:pointer;
"
>
🔊 길안내 듣기
</button>

<script>

function 말하기() {{

    window.speechSynthesis.cancel();

    const 문장 = new SpeechSynthesisUtterance(
        {음성내용!r}
    );

    문장.lang = "ko-KR";
    문장.rate = 0.9;
    문장.pitch = 1.0;
    문장.volume = 1.0;

    window.speechSynthesis.speak(문장);
}}

</script>
"""


components.html(
    음성화면,
    height=70
)
