import streamlit as st
import requests
import math

st.set_page_config(
    page_title="현재 위치 지하철 길찾기",
    page_icon="🚇",
    layout="centered"
)

# =========================
# 디자인
# =========================

st.markdown("""
<style>
.title {
    font-size: 30px;
    font-weight: bold;
}

.box {
    background: white;
    padding: 18px;
    border-radius: 18px;
    margin: 12px 0;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
}

.station {
    background: #f4f7ff;
    padding: 15px;
    border-radius: 14px;
    margin: 8px 0;
}

.big {
    font-size: 20px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="title">🚇 현재 위치 지하철 길찾기</div>',
    unsafe_allow_html=True
)

st.write(
    "현재 위치를 기준으로 가까운 지하철역을 찾아드립니다."
)

# =========================
# 현재 위치 가져오기
# =========================

위치가져오기 = st.button(
    "📍 현재 위치 사용",
    use_container_width=True
)

# =========================
# 위치 가져오기
# =========================

if 위치가져오기:

    위치코드 = """
    <script>
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            window.parent.postMessage({
                type: "위치정보",
                lat: lat,
                lon: lon
            }, "*");
        },
        function(error) {
            window.parent.postMessage({
                type: "위치오류"
            }, "*");
        }
    );
    </script>
    """

    st.components.v1.html(
        위치코드,
        height=0
    )

    st.info(
        "브라우저에서 위치 권한을 허용해주세요."
    )

# =========================
# 주소 검색
# =========================

def 주소찾기(lat, lon):

    try:

        url = "https://nominatim.openstreetmap.org/reverse"

        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 18
        }

        headers = {
            "User-Agent": "Korean-Subway-Route-App"
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "display_name",
            "현재 위치"
        )

    except Exception:

        return "현재 위치"


# =========================
# 거리 계산
# =========================

def 거리계산(lat1, lon1, lat2, lon2):

    지구반지름 = 6371000

    위도1 = math.radians(lat1)
    위도2 = math.radians(lat2)

    위도차 = math.radians(lat2 - lat1)
    경도차 = math.radians(lon2 - lon1)

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

    return 지구반지름 * c


# =========================
# 주변 지하철역 찾기
# =========================

def 주변역찾기(lat, lon):

    try:

        query = f"""
        [out:json];

        (
          node["railway"="station"](around:3000,{lat},{lon});
          way["railway"="subway"](around:3000,{lat},{lon});
        );

        out center tags;
        """

        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=query,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        역목록 = []

        for element in data.get("elements", []):

            tags = element.get("tags", {})

            이름 = tags.get("name")

            if not 이름:
                continue

            if element["type"] == "node":

                역위도 = element.get("lat")
                역경도 = element.get("lon")

            else:

                center = element.get("center")

                if not center:
                    continue

                역위도 = center.get("lat")
                역경도 = center.get("lon")

            if 역위도 is None or 역경도 is None:
                continue

            거리 = 거리계산(
                lat,
                lon,
                역위도,
                역경도
            )

            역목록.append({
                "이름": 이름,
                "위도": 역위도,
                "경도": 역경도,
                "거리": 거리
            })

        # 같은 역 중복 제거
        결과 = {}

        for 역 in 역목록:

            이름 = 역["이름"]

            if (
                이름 not in 결과
                or 역["거리"] < 결과[이름]["거리"]
            ):
                결과[이름] = 역

        역목록 = list(결과.values())

        역목록.sort(
            key=lambda x: x["거리"]
        )

        return 역목록[:5]

    except Exception:

        return []


# =========================
# 위치가 직접 입력된 경우
# =========================

st.markdown("### 📍 현재 위치")

위도 = st.number_input(
    "현재 위치 위도",
    value=0.0,
    format="%.6f"
)

경도 = st.number_input(
    "현재 위치 경도",
    value=0.0,
    format="%.6f"
)

검색 = st.button(
    "🚇 주변 지하철역 찾기",
    use_container_width=True
)


# =========================
# 주변역 검색
# =========================

if 검색:

    if 위도 == 0.0 or 경도 == 0.0:

        st.warning(
            "현재 위치를 먼저 입력해주세요."
        )

    else:

        with st.spinner(
            "주변 지하철역을 찾고 있습니다."
        ):

            역목록 = 주변역찾기(
                위도,
                경도
            )

        if not 역목록:

            st.error(
                "주변 지하철역을 찾지 못했습니다."
            )

        else:

            st.success(
                f"가까운 지하철역 {len(역목록)}곳을 찾았습니다."
            )

            st.markdown(
                "### 🚇 가까운 지하철역"
            )

            for 번호, 역 in enumerate(
                역목록,
                1
            ):

                거리 = 역["거리"]

                if 거리 < 1000:
                    거리표시 = f"{int(거리)}m"
                else:
                    거리표시 = f"{거리 / 1000:.1f}km"

                st.markdown(
                    f"""
                    <div class="station">

                    <div class="big">
                    {번호}. 🚇 {역["이름"]}
                    </div>

                    <br>

                    현재 위치에서 약
                    <b>{거리표시}</b>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


            # =========================
            # 가장 가까운 역
            # =========================

            가장가까운역 = 역목록[0]

            st.markdown(
                '<div class="box">',
                unsafe_allow_html=True
            )

            st.markdown(
                "### ⭐ 추천 지하철역"
            )

            st.write(
                f"**{가장가까운역['이름']}역**"
            )

            거리 = 가장가까운역["거리"]

            if 거리 < 1000:

                st.write(
                    f"현재 위치에서 약 {int(거리)}m입니다."
                )

            else:

                st.write(
                    f"현재 위치에서 약 {거리 / 1000:.1f}km입니다."
                )

            st.write(
                "먼저 이 역까지 이동한 다음 지하철을 이용할 수 있습니다."
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )


            # =========================
            # 지도
            # =========================

            st.markdown("### 🗺 현재 위치 지도")

            지도HTML = f"""
            <iframe
                width="100%"
                height="500"
                style="border:0; border-radius:16px;"
                src="https://www.openstreetmap.org/export/embed.html?
                bbox={
                    경도 - 0.02
                }%2C{
                    위도 - 0.015
                }%2C{
                    경도 + 0.02
                }%2C{
                    위도 + 0.015
                }&layer=mapnik&marker={위도}%2C{경도}">
            </iframe>
            """

            st.components.v1.html(
                지도HTML,
                height=520
            )


            # =========================
            # 다음 단계
            # =========================

            st.markdown("### 🚉 지하철 이용")

            st.info(
                "현재 버전에서는 가까운 역까지 찾습니다. "
                "실제 노선, 방향, 환승역, 도착역까지 계산하려면 "
                "서울시 대중교통 환승경로 API 연결이 필요합니다."
            )
