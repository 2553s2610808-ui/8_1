import streamlit as st
import requests
import html
import json
import streamlit.components.v1 as components


# ==========================================
# 기본 설정
# ==========================================

st.set_page_config(
    page_title="길찾기",
    page_icon="🧭",
    layout="wide"
)


# ==========================================
# 화면 디자인
# ==========================================

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
    margin-bottom: 20px;
}

.result-number {
    font-size: 30px;
    font-weight: 800;
}

.result-label {
    font-size: 14px;
    color: #6b7280;
}

.step-card {
    background: white;
    border-radius: 15px;
    padding: 17px 20px;
    margin-bottom: 10px;
    border-left: 5px solid #6366f1;
    box-shadow: 0 3px 12px rgba(0,0,0,0.04);
    font-size: 16px;
    line-height: 1.5;
}

.step-number {
    color: #6366f1;
    font-weight: 800;
}

.voice-box {
    background: #f3f4ff;
    border-radius: 15px;
    padding: 18px;
    color: #3730a3;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 주소 검색
# ==========================================

def 위치찾기(주소):

    if not 주소 or not 주소.strip():
        return None

    주소검색주소 = "https://nominatim.openstreetmap.org/search"

    검색조건 = {
        "q": 주소.strip(),
        "format": "json",
        "limit": 1,
        "countrycodes": "kr"
    }

    요청정보 = {
        "User-Agent": "KoreanNavigationApp/1.0"
    }

    try:

        응답 = requests.get(
            주소검색주소,
            params=검색조건,
            headers=요청정보,
            timeout=10
        )

        응답.raise_for_status()

        결과 = 응답.json()

        if not 결과:
            return None

        return {
            "위도": float(결과[0]["lat"]),
            "경도": float(결과[0]["lon"])
        }

    except Exception:
        return None


# ==========================================
# 경로 검색
# ==========================================

def 경로찾기(출발지, 도착지):

    주소 = (
        "https://router.project-osrm.org/route/v1/foot/"
        f"{출발지['경도']},{출발지['위도']};"
        f"{도착지['경도']},{도착지['위도']}"
    )

    조건 = {
        "overview": "full",
        "steps": "true",
        "geometries": "geojson"
    }

    try:

        응답 = requests.get(
            주소,
            params=조건,
            timeout=20
        )

        응답.raise_for_status()

        결과 = 응답.json()

        if 결과.get("code") != "Ok":
            return None

        경로 = 결과.get("routes")

        if not 경로:
            return None

        return 경로[0]

    except Exception:
        return None


# ==========================================
# 거리 표시
# ==========================================

def 거리표시(거리):

    if 거리 < 1000:
        return f"{round(거리)}m"

    return f"{거리 / 1000:.1f}km"


# ==========================================
# 시간 표시
# ==========================================

def 시간표시(시간):

    분 = round(시간 / 60)

    if 분 < 60:
        return f"{분}분"

    시 = 분 // 60
    나머지 = 분 % 60

    if 나머지 == 0:
        return f"{시}시간"

    return f"{시}시간 {나머지}분"


# ==========================================
# 방향 변환
# ==========================================

def 방향변환(방향):

    변환표 = {
        "left": "왼쪽",
        "right": "오른쪽",
        "straight": "직진",
        "slight left": "왼쪽 방향",
        "slight right": "오른쪽 방향",
        "sharp left": "왼쪽으로 크게",
        "sharp right": "오른쪽으로 크게",
        "uturn": "유턴"
    }

    return 변환표.get(방향, "")


# ==========================================
# 이동 순서 만들기
# ==========================================

def 이동순서만들기(경로):

    안내목록 = []

    for 구간 in 경로.get("legs", []):

        for 이동 in 구간.get("steps", []):

            조작 = 이동.get("maneuver", {})

            종류 = 조작.get("type", "")
            방향 = 조작.get("modifier", "")

            거리 = 이동.get("distance", 0)

            길이름 = 이동.get("name", "").strip()

            # 출발
            if 종류 == "depart":

                안내문 = "현재 위치에서 출발하세요."

                if 길이름:
                    안내문 = f"{길이름} 방향으로 출발하세요."

            # 도착
            elif 종류 == "arrive":

                안내문 = "목적지에 도착했습니다."

            # 유턴
            elif 방향 == "uturn":

                if 거리 >= 1:
                    안내문 = (
                        f"{round(거리)}미터 정도 이동한 뒤 "
                        "유턴하세요."
                    )
                else:
                    안내문 = "유턴하세요."

            else:

                방향한글 = 방향변환(방향)

                if 거리 >= 1000:
                    거리문자 = f"{거리 / 1000:.1f}킬로미터"

                elif 거리 >= 100:
                    거리문자 = f"{round(거리 / 10) * 10}미터"

                elif 거리 >= 1:
                    거리문자 = f"{round(거리)}미터"

                else:
                    거리문자 = ""

                if 방향한글:

                    if 길이름 and 거리문자:
                        안내문 = (
                            f"{거리문자} 정도 이동한 뒤 "
                            f"{길이름}에서 {방향한글}으로 이동하세요."
                        )

                    elif 길이름:
                        안내문 = (
                            f"{길이름}에서 "
                            f"{방향한글}으로 이동하세요."
                        )

                    elif 거리문자:
                        안내문 = (
                            f"{거리문자} 정도 이동한 뒤 "
                            f"{방향한글}으로 이동하세요."
                        )

                    else:
                        안내문 = f"{방향한글}으로 이동하세요."

                elif 길이름 and 거리문자:

                    안내문 = (
                        f"{길이름}을 따라 "
                        f"{거리문자} 정도 이동하세요."
                    )

                elif 거리문자:

                    안내문 = (
                        f"{거리문자} 정도 계속 이동하세요."
                    )

                else:

                    안내문 = "계속 이동하세요."

            # 영어가 포함된 안내는 제외
            영어포함 = any(
                "a" <= 글자.lower() <= "z"
                for 글자 in 안내문
            )

            if not 영어포함:
                안내목록.append(안내문)

    if not 안내목록:
        안내목록.append(
            "현재 위치에서 목적지까지 이동하세요."
        )

    return 안내목록


# ==========================================
# 지도 만들기
# ==========================================

def 지도만들기(출발지, 도착지, 경로):

    좌표목록 = 경로["geometry"]["coordinates"]

    지도좌표 = [
        [좌표[1], 좌표[0]]
        for 좌표 in 좌표목록
    ]

    지도좌표문자 = json.dumps(지도좌표)

    출발위도 = 출발지["위도"]
    출발경도 = 출발지["경도"]

    도착위도 = 도착지["위도"]
    도착경도 = 도착지["경도"]

    지도내용 = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<link
rel="stylesheet"
href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">

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
    height: 520px;
    border-radius: 18px;
}}

</style>

</head>

<body>

<div id="map"></div>

<script>

const 출발지 = [{출발위도}, {출발경도}];

const 도착지 = [{도착위도}, {도착경도}];

const 이동경로 = {지도좌표문자};

const 지도 = L.map("map");

L.tileLayer(
    "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
    {{
        attribution: ""
    }}
).addTo(지도);

L.marker(출발지)
    .addTo(지도)
    .bindPopup("출발지");

L.marker(도착지)
    .addTo(지도)
    .bindPopup("도착지");

const 선 = L.polyline(
    이동경로,
    {{
        color: "#6366f1",
        weight: 7,
        opacity: 0.9
    }}
).addTo(지도);

지도.fitBounds(
    선.getBounds(),
    {{
        padding: [30, 30]
    }}
);

</script>

</body>

</html>
"""

    return 지도내용


# ==========================================
# 음성 안내
# ==========================================

def 음성내용만들기(
    출발지,
    도착지,
    경로,
    안내목록
):

    전체거리 = 거리표시(
        경로["distance"]
    )

    예상시간 = 시간표시(
        경로["duration"]
    )

    문장 = []

    문장.append(
        f"{출발지}에서 {도착지}까지 안내해 드리겠습니다."
    )

    문장.append(
        f"전체 거리는 약 {전체거리}이며 "
        f"예상 소요 시간은 {예상시간입니다}."
    )

    for 번호, 안내 in enumerate(
        안내목록,
        start=1
    ):

        문장.append(
            f"{번호}번째 안내입니다. {안내}"
        )

    문장.append(
        "목적지에 도착했습니다. 안내를 종료합니다."
    )

    return " ".join(문장)


# ==========================================
# 음성 버튼
# ==========================================

def 음성화면(음성내용):

    안전한음성내용 = json.dumps(
        음성내용,
        ensure_ascii=False
    )

    return f"""

<script>

const 안내내용 = {안전한음성내용};

function 안내시작() {{

    if (!("speechSynthesis" in window)) {{

        alert(
            "현재 사용 중인 인터넷 프로그램에서는 음성 안내를 사용할 수 없습니다."
        );

        return;
    }}

    window.speechSynthesis.cancel();

    const 음성 = new SpeechSynthesisUtterance(
        안내내용
    );

    음성.lang = "ko-KR";

    음성.rate = 0.88;

    음성.pitch = 1.0;

    음성.volume = 1.0;

    window.speechSynthesis.speak(음성);

}}

function 안내중지() {{

    window.speechSynthesis.cancel();

}}

</script>


<div style="
display:flex;
gap:10px;
width:100%;
">

<button
onclick="안내시작()"
style="
flex:1;
padding:14px;
border:0;
border-radius:12px;
background:#6366f1;
color:white;
font-size:15px;
font-weight:bold;
cursor:pointer;
">
🔊 안내 시작
</button>


<button
onclick="안내중지()"
style="
flex:1;
padding:14px;
border:0;
border-radius:12px;
background:#e5e7eb;
color:#374151;
font-size:15px;
font-weight:bold;
cursor:pointer;
">
⏹️ 안내 중지
</button>

</div>

"""


# ==========================================
# 제목
# ==========================================

st.markdown(
    '<div class="main-title">🧭 길찾기</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    '출발지와 도착지를 입력하면 이동 경로를 안내합니다.'
    '</div>',
    unsafe_allow_html=True
)


# ==========================================
# 입력 화면
# ==========================================

st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
)

왼쪽, 오른쪽 = st.columns(2)

with 왼쪽:

    출발입력 = st.text_input(
        "📍 출발지",
        placeholder="예: 서울역"
    )

with 오른쪽:

    도착입력 = st.text_input(
        "🎯 도착지",
        placeholder="예: 경복궁"
    )


검색버튼 = st.button(
    "🚶 경로 찾기",
    use_container_width=True,
    type="primary"
)

st.markdown(
    '</div>',
    unsafe_allow_html=True
)


# ==========================================
# 검색 버튼을 눌렀을 때
# ==========================================

if 검색버튼:

    # 기존 결과 삭제
    if "경로" in st.session_state:
        del st.session_state["경로"]

    if "출발지" in st.session_state:
        del st.session_state["출발지"]

    if "도착지" in st.session_state:
        del st.session_state["도착지"]

    if not 출발입력.strip():

        st.warning(
            "출발지를 먼저 입력해주세요."
        )

    elif not 도착입력.strip():

        st.warning(
            "도착지를 먼저 입력해주세요."
        )

    else:

        with st.spinner(
            "위치와 이동 경로를 찾고 있습니다..."
        ):

            출발지 = 위치찾기(출발입력)

            도착지 = 위치찾기(도착입력)

            if 출발지 is None:

                st.error(
                    "출발지를 찾지 못했습니다. "
                    "장소 이름이나 주소를 다시 입력해주세요."
                )

            elif 도착지 is None:

                st.error(
                    "도착지를 찾지 못했습니다. "
                    "장소 이름이나 주소를 다시 입력해주세요."
                )

            else:

                경로 = 경로찾기(
                    출발지,
                    도착지
                )

                if 경로 is None:

                    st.error(
                        "이동 경로를 찾지 못했습니다. "
                        "잠시 후 다시 시도해주세요."
                    )

                else:

                    st.session_state["경로"] = 경로

                    st.session_state["출발지"] = 출발지

                    st.session_state["도착지"] = 도착지

                    st.session_state["출발이름"] = 출발입력

                    st.session_state["도착이름"] = 도착입력


# ==========================================
# 결과 화면
# ==========================================

if "경로" in st.session_state:

    경로 = st.session_state["경로"]

    출발지 = st.session_state["출발지"]

    도착지 = st.session_state["도착지"]

    출발이름 = st.session_state["출발이름"]

    도착이름 = st.session_state["도착이름"]


    # --------------------------------------
    # 경로 요약
    # --------------------------------------

    st.markdown(
        f"""
<div class="result-card">

<div style="
font-size:14px;
opacity:.85;
">
추천 도보 경로
</div>

<div style="
font-size:23px;
font-weight:800;
margin-top:8px;
">
{html.escape(출발이름)}
 →
{html.escape(도착이름)}
</div>

</div>
""",
        unsafe_allow_html=True
    )


    # --------------------------------------
    # 거리와 시간
    # --------------------------------------

    왼쪽, 오른쪽 = st.columns(2)

    with 왼쪽:

        st.markdown(
            f"""
<div class="card">

<div class="result-number">
{시간표시(경로["duration"])}
</div>

<div class="result-label">
예상 소요 시간
</div>

</div>
""",
            unsafe_allow_html=True
        )


    with 오른쪽:

        st.markdown(
            f"""
<div class="card">

<div class="result-number">
{거리표시(경로["distance"])}
</div>

<div class="result-label">
총 이동 거리
</div>

</div>
""",
            unsafe_allow_html=True
        )


    # --------------------------------------
    # 지도
    # --------------------------------------

    st.markdown(
        '<div class="card"><h3>🗺️ 이동 경로</h3>',
        unsafe_allow_html=True
    )

    components.html(
        지도만들기(
            출발지,
            도착지,
            경로
        ),
        height=550
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------
    # 이동 순서
    # --------------------------------------

    안내목록 = 이동순서만들기(경로)


    st.markdown(
        '<div class="card"><h3>📋 이동 순서</h3>',
        unsafe_allow_html=True
    )


    for 번호, 안내 in enumerate(
        안내목록,
        start=1
    ):

        st.markdown(
            f"""
<div class="step-card">

<span class="step-number">
{번호}
</span>

&nbsp;&nbsp;

{html.escape(안내)}

</div>
""",
            unsafe_allow_html=True
        )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------
    # 음성 안내
    # --------------------------------------

    전체거리 = 거리표시(
        경로["distance"]
    )

    예상시간 = 시간표시(
        경로["duration"]
    )

    음성문장 = []

    음성문장.append(
        f"{출발이름}에서 {도착이름}까지 안내해 드리겠습니다."
    )

    음성문장.append(
        f"전체 거리는 약 {전체거리}이며 "
        f"예상 소요 시간은 {예상시간}입니다."
    )

    for 번호, 안내 in enumerate(
        안내목록,
        start=1
    ):

        음성문장.append(
            f"{번호}번째 안내입니다. {안내}"
        )

    음성문장.append(
        "목적지에 도착했습니다. 안내를 종료합니다."
    )

    최종음성 = " ".join(음성문장)


    st.markdown(
        """
<div class="card">

<h3>🔊 음성 안내</h3>

<div class="voice-box">
버튼을 누르면 전체 이동 경로를 한국어로 안내합니다.
</div>

""",
        unsafe_allow_html=True
    )


    components.html(
        음성화면(최종음성),
        height=70
    )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ==========================================
# 아무것도 입력하지 않았을 때
# ==========================================

else:

    st.markdown(
        """
<div class="card"
style="
text-align:center;
padding:55px;
">

<div style="font-size:52px;">
🧭
</div>

<h2>
출발지와 도착지를 입력하세요
</h2>

<p style="color:#6b7280;">
두 장소를 입력하면 지도와 이동 순서를 보여드립니다.
</p>

</div>
""",
        unsafe_allow_html=True
    )
