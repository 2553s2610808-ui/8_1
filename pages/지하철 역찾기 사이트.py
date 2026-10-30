
import json
import math
from urllib.parse import urlencode

import streamlit as st
import streamlit.components.v1 as components


# ---------------------------------
# 페이지 설정
# ---------------------------------
st.set_page_config(
    page_title="지하철 역찾기",
    page_icon="🚇",
    layout="wide"
)

# ---------------------------------
# 지하철역 정보
# 위도와 경도는 역 위치를 나타내는 참고 좌표
# ---------------------------------
STATIONS = {
    "서울역": {"lines": ["1호선", "4호선"], "lat": 37.5547, "lon": 126.9707},
    "시청역": {"lines": ["1호선", "2호선"], "lat": 37.5657, "lon": 126.9771},
    "종각역": {"lines": ["1호선"], "lat": 37.5702, "lon": 126.9831},
    "종로3가역": {"lines": ["1호선", "3호선", "5호선"], "lat": 37.5716, "lon": 126.9918},
    "종로5가역": {"lines": ["1호선"], "lat": 37.5709, "lon": 127.0019},
    "동대문역": {"lines": ["1호선", "4호선"], "lat": 37.5714, "lon": 127.0097},
    "동묘앞역": {"lines": ["1호선", "6호선"], "lat": 37.5727, "lon": 127.0165},
    "신설동역": {"lines": ["1호선", "2호선"], "lat": 37.5753, "lon": 127.0250},
    "제기동역": {"lines": ["1호선"], "lat": 37.5781, "lon": 127.0349},
    "청량리역": {"lines": ["1호선"], "lat": 37.5800, "lon": 127.0473},
    "회기역": {"lines": ["1호선"], "lat": 37.5898, "lon": 127.0578},
    "외대앞역": {"lines": ["1호선"], "lat": 37.5961, "lon": 127.0630},
    "신이문역": {"lines": ["1호선"], "lat": 37.6019, "lon": 127.0677},
    "석계역": {"lines": ["1호선", "6호선"], "lat": 37.6148, "lon": 127.0659},
    "광운대역": {"lines": ["1호선"], "lat": 37.6236, "lon": 127.0616},
    "월계역": {"lines": ["1호선"], "lat": 37.6332, "lon": 127.0588},
    "녹천역": {"lines": ["1호선"], "lat": 37.6460, "lon": 127.0513},
    "창동역": {"lines": ["1호선", "4호선"], "lat": 37.6532, "lon": 127.0477},
    "방학역": {"lines": ["1호선"], "lat": 37.6670, "lon": 127.0443},
    "도봉역": {"lines": ["1호선"], "lat": 37.6796, "lon": 127.0450},
    "도봉산역": {"lines": ["1호선", "7호선"], "lat": 37.6892, "lon": 127.0462},
    "망월사역": {"lines": ["1호선"], "lat": 37.7098, "lon": 127.0474},
    "의정부역": {"lines": ["1호선"], "lat": 37.7388, "lon": 127.0459},
    "가능역": {"lines": ["1호선"], "lat": 37.7484, "lon": 127.0442},
    "녹양역": {"lines": ["1호선"], "lat": 37.7594, "lon": 127.0423},
    "양주역": {"lines": ["1호선"], "lat": 37.7744, "lon": 127.0447},
    "덕정역": {"lines": ["1호선"], "lat": 37.8432, "lon": 127.0617},
    "지행역": {"lines": ["1호선"], "lat": 37.8923, "lon": 127.0557},
    "동두천중앙역": {"lines": ["1호선"], "lat": 37.9019, "lon": 127.0565},
    "천안역": {"lines": ["1호선"], "lat": 36.8100, "lon": 127.1468},
    "두정역": {"lines": ["1호선"], "lat": 36.83399, "lon": 127.14919},
    "봉명역": {"lines": ["1호선"], "lat": 36.8014, "lon": 127.1357},
    "쌍용역": {"lines": ["1호선"], "lat": 36.7938, "lon": 127.1214},
    "아산역": {"lines": ["1호선"], "lat": 36.7921, "lon": 127.1045},
    "탕정역": {"lines": ["1호선"], "lat": 36.7881, "lon": 127.0847},
    "배방역": {"lines": ["1호선"], "lat": 36.7776, "lon": 127.0528},
    "온양온천역": {"lines": ["1호선"], "lat": 36.7806, "lon": 127.0032},
}


# ---------------------------------
# 거리 계산
# ---------------------------------
def distance_km(lat1, lon1, lat2, lon2):
    radius = 6371
    lat1, lon1, lat2, lon2 = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def maps_url(destination):
    station = STATIONS[destination]
    query = urlencode({
        "api": "1",
        "destination": f"{station['lat']},{station['lon']}",
        "destination_place_id": "",
        "travelmode": "transit"
    })
    return f"https://www.google.com/maps/dir/?{query}"


# ---------------------------------
# 화면 디자인
# ---------------------------------
st.markdown("""
<style>
.stApp {
    background: #ffffff;
}
.main .block-container {
    max-width: 1100px;
    padding-top: 2rem;
}
.app-panel {
    background: #d2e5f5;
    border: 1px solid #263746;
    border-radius: 55px;
    padding: 35px 45px;
    min-height: 650px;
}
.main-title {
    text-align: center;
    color: #123d69;
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 5px;
}
.sub-title {
    text-align: center;
    color: #536779;
    font-size: 18px;
    margin-bottom: 35px;
}
.info-banner {
    background: #ff1010;
    color: white;
    border: 1px solid #111111;
    padding: 22px;
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    margin-top: 25px;
    margin-bottom: 30px;
    border-radius: 0 12px 0 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-panel">', unsafe_allow_html=True)

st.markdown(
    '<div class="main-title">🚇 지하철 역찾기</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-title">가장 가까운 역을 찾고, 빠르고 편리하게 이동하세요!</div>',
    unsafe_allow_html=True
)

# ---------------------------------
# 노선 및 도착지 선택
# ---------------------------------
all_lines = sorted({
    line
    for station in STATIONS.values()
    for line in station["lines"]
})

col1, col2 = st.columns(2)

with col1:
    selected_line = st.selectbox(
        "📍 노선",
        all_lines,
        key="selected_line"
    )

with col2:
    line_stations = [
        name for name, data in STATIONS.items()
        if selected_line in data["lines"]
    ]

    destination = st.selectbox(
        "🚇 도착지",
        line_stations,
        key="destination"
    )

st.markdown(
    '<div class="info-banner">'
    '도착지를 입력하면 현재 위치에서 가장 빨리 도착할 수 있는<br>'
    '노선을 찾아줍니다.'
    '</div>',
    unsafe_allow_html=True
)

if st.button("🚉 도착지 길찾기", use_container_width=True):
    st.link_button(
        "Google 지도에서 대중교통 경로 보기",
        maps_url(destination),
        use_container_width=True
    )

st.divider()

# ---------------------------------
# 기능 탭
# ---------------------------------
tab_nearest, tab_search, tab_route = st.tabs([
    "📍 가까운 역 찾기",
    "🔎 역 검색",
    "🗺️ 도착지 길찾기"
])

# ---------------------------------
# 가까운 역 찾기
# ---------------------------------
with tab_nearest:
    st.subheader("현재 위치에서 가까운 역 찾기")
    st.write("위치 정보 사용을 허용하면 가까운 역을 찾아줍니다.")

    station_data = [
        {
            "name": name,
            "lat": data["lat"],
            "lon": data["lon"],
            "lines": ", ".join(data["lines"])
        }
        for name, data in STATIONS.items()
    ]

    station_json = json.dumps(station_data, ensure_ascii=False)

    html = """
    <div style="font-family:Arial,sans-serif;padding:12px;">
      <button onclick="findNearest()"
        style="background:#1769aa;color:white;border:0;
        border-radius:10px;padding:13px 22px;font-size:16px;
        cursor:pointer;">
        현재 위치로 가까운 역 찾기
      </button>
      <div id="result" style="margin-top:18px;font-size:16px;"></div>
    </div>

    <script>
    const stations = STATION_DATA_PLACEHOLDER;

    function findNearest() {
      const result = document.getElementById("result");
      result.innerHTML = "현재 위치를 확인하고 있습니다...";

      if (!navigator.geolocation) {
        result.innerHTML = "이 브라우저에서는 위치 기능을 사용할 수 없습니다.";
        return;
      }

      navigator.geolocation.getCurrentPosition(
        function(position) {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;

          function distance(lat1, lon1, lat2, lon2) {
            const R = 6371;
            const toRad = x => x * Math.PI / 180;
            const dLat = toRad(lat2 - lat1);
            const dLon = toRad(lon2 - lon1);
            const a =
              Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
            return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
          }

          const sorted = stations.map(s => ({
            ...s,
            distance: distance(lat, lon, s.lat, s.lon)
          })).sort((a,b) => a.distance - b.distance);

          const nearest = sorted[0];

          result.innerHTML =
            "<h3>가장 가까운 역: " + nearest.name + "</h3>" +
            "<p>노선: " + nearest.lines + "</p>" +
            "<p>직선거리 약 " + nearest.distance.toFixed(2) + "km</p>" +
            "<h4>가까운 역 TOP 5</h4>" +
            sorted.slice(0,5).map((s,i) =>
              "<p>" + (i+1) + ". " + s.name +
              " (" + s.distance.toFixed(2) + "km)</p>"
            ).join("");
        },
        function(error) {
          result.innerHTML =
            "위치 정보를 가져오지 못했습니다. 브라우저의 위치 권한을 확인해 주세요.";
        },
        {enableHighAccuracy:true, timeout:10000}
      );
    }
    </script>
    """

    html = html.replace("STATION_DATA_PLACEHOLDER", station_json)
    components.html(html, height=390)


# ---------------------------------
# 역 검색
# ---------------------------------
with tab_search:
    st.subheader("지하철역 검색")

    keyword = st.text_input(
        "찾고 싶은 역 이름을 입력하세요.",
        placeholder="예: 두정역"
    )

    if keyword:
        matched = [
            name for name in STATIONS
            if keyword.strip() in name
        ]

        if matched:
            for name in matched:
                data = STATIONS[name]
                st.success(
                    f"🚉 {name}  |  노선: {', '.join(data['lines'])}"
                )
        else:
            st.warning("검색 결과가 없습니다.")


# ---------------------------------
# 도착지 길찾기
# ---------------------------------
with tab_route:
    st.subheader("목적지 대중교통 길찾기")

    route_destination = st.selectbox(
        "도착할 역을 선택하세요.",
        sorted(STATIONS.keys()),
        key="route_destination"
    )

    route_info = STATIONS[route_destination]

    st.write(f"**도착역:** {route_destination}")
    st.write(f"**운행 노선:** {', '.join(route_info['lines'])}")

    st.link_button(
        "🗺️ Google 지도에서 경로 확인하기",
        maps_url(route_destination),
        use_container_width=True
    )

st.markdown('</div>', unsafe_allow_html=True)
