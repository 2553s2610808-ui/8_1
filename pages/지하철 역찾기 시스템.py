import json
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="지하철 역찾기", page_icon="🚇", layout="wide")

# 등록된 주요 역의 좌표. 전체 역 데이터가 아닌 예시 목록입니다.
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

station_list = [
    {"name": name, "lat": data["lat"], "lon": data["lon"],
     "lines": ", ".join(data["lines"])}
    for name, data in STATIONS.items()
]
station_json = json.dumps(station_list, ensure_ascii=False)

def google_walk_url(lat, lon, station):
    from urllib.parse import urlencode
    params = urlencode({
        "api": "1",
        "destination": f"{lat},{lon}",
        "destination_place_id": "",
        "travelmode": "walking",
    })
    return f"https://www.google.com/maps/dir/?{params}"

st.markdown("""
<style>
.stApp {background:#fff;}
.block-container {max-width:1100px;padding-top:2rem;}
.app-panel {background:#d2e5f5;border:1px solid #263746;border-radius:45px;
padding:30px 38px;min-height:650px;}
.main-title {text-align:center;color:#123d69;font-size:40px;font-weight:800;}
.sub-title {text-align:center;color:#536779;font-size:18px;margin-bottom:30px;}
.info-banner {background:#f01419;color:white;border:1px solid #222;
padding:22px;text-align:center;font-size:19px;font-weight:700;
margin:25px 0 30px;border-radius:0 12px 0 12px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-panel">', unsafe_allow_html=True)
st.markdown('<div class="main-title">🚇 지하철 역찾기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">가장 가까운 역을 찾고, 빠르고 편리하게 이동하세요!</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
all_lines = sorted({line for item in STATIONS.values() for line in item["lines"]})
with col1:
    selected_line = st.selectbox("📍 노선", all_lines)
with col2:
    line_stations = [name for name, item in STATIONS.items() if selected_line in item["lines"]]
    destination = st.selectbox("🚇 도착지", line_stations)

st.markdown(
    '<div class="info-banner">도착지를 입력하면 현재 위치에서 가장 빨리 도착할 수 있는<br>노선을 찾아줍니다.</div>',
    unsafe_allow_html=True
)

tab_nearest, tab_search, tab_route = st.tabs(
    ["📍 현재 위치에서 가까운 역", "🔎 역 검색", "🗺️ 도착지 길찾기"]
)

with tab_nearest:
    st.subheader("현재 위치에서 도보로 가장 가까운 역 찾기")
    st.write("버튼을 누르고 브라우저의 위치 권한을 허용하면, 가장 가까운 등록 역까지 도보 경로를 안내합니다.")
    st.caption("※ 가까운 역 후보는 아래 코드에 등록된 주요 역으로 한정됩니다. 지도 서비스가 실제 보행 경로를 계산합니다.")

    html = """
    <div style="font-family:Arial,sans-serif;padding:10px 0;">
      <button id="locate" onclick="findNearest()"
       style="background:#1769aa;color:white;border:0;border-radius:10px;
       padding:14px 22px;font-size:16px;cursor:pointer;">
       📍 현재 위치로 가장 가까운 역 찾기
      </button>
      <div id="status" style="margin-top:16px;color:#173b60;font-size:16px;"></div>
      <div id="details" style="margin-top:10px;"></div>
    </div>
    <script>
    const stations = STATION_DATA_PLACEHOLDER;
    const statusBox = document.getElementById("status");
    const details = document.getElementById("details");

    function distanceKm(aLat, aLon, bLat, bLon) {
      const R = 6371;
      const rad = x => x * Math.PI / 180;
      const dLat = rad(bLat - aLat);
      const dLon = rad(bLon - aLon);
      const a = Math.sin(dLat/2)**2 +
        Math.cos(rad(aLat))*Math.cos(rad(bLat))*Math.sin(dLon/2)**2;
      return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }

    function findNearest() {
      details.innerHTML = "";
      statusBox.textContent = "현재 위치를 확인하고 있습니다...";
      if (!navigator.geolocation) {
        statusBox.textContent = "이 브라우저는 위치 확인 기능을 지원하지 않습니다.";
        return;
      }
      navigator.geolocation.getCurrentPosition(position => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const sorted = stations.map(s => ({
          ...s,
          distance: distanceKm(lat, lon, s.lat, s.lon)
        })).sort((a,b) => a.distance - b.distance);
        const nearest = sorted[0];

        const params = new URLSearchParams({
          api: "1",
          origin: lat + "," + lon,
          destination: nearest.lat + "," + nearest.lon,
          travelmode: "walking"
        });
        const mapUrl = "https://www.google.com/maps/dir/?" + params.toString();

        statusBox.innerHTML =
          "<h3>가장 가까운 역: " + nearest.name + "</h3>" +
          "<p>노선: " + nearest.lines + "</p>" +
          "<p>현재 위치에서 역까지 직선거리 약 " +
          nearest.distance.toFixed(2) + "km</p>" +
          "<p>아래 버튼을 눌러 실제 도보 경로와 예상 시간을 확인하세요.</p>";

        details.innerHTML =
          '<a href="' + mapUrl + '" target="_blank" rel="noopener" ' +
          'style="display:inline-block;background:#e51b23;color:white;' +
          'padding:13px 20px;border-radius:9px;text-decoration:none;' +
          'font-weight:bold;">🚶 ' + nearest.name +
          '까지 도보 길찾기 열기</a>' +
          '<p style="margin-top:12px;color:#555;">' +
          '※ 직선거리 순으로 가까운 역을 골랐으며, 실제 도보 거리·시간은 지도에서 확인해야 합니다.</p>';
      }, error => {
        let message = "위치 정보를 가져오지 못했습니다.";
        if (error.code === 1) message = "위치 권한이 거부되었습니다. 브라우저 주소창 왼쪽의 사이트 설정에서 위치 권한을 허용해 주세요.";
        if (error.code === 2) message = "현재 위치를 확인할 수 없습니다. 기기의 위치 서비스를 확인해 주세요.";
        if (error.code === 3) message = "위치 확인 시간이 초과되었습니다. 다시 시도해 주세요.";
        statusBox.textContent = message;
      }, {enableHighAccuracy:true, timeout:15000, maximumAge:60000});
    }
    </script>
    """
    html = html.replace("STATION_DATA_PLACEHOLDER", station_json)
    components.html(html, height=300)

with tab_search:
    st.subheader("지하철역 검색")
    keyword = st.text_input("역 이름을 입력하세요.", placeholder="예: 두정역")
    if keyword.strip():
        matches = [name for name in STATIONS if keyword.strip() in name]
        if matches:
            for name in matches:
                st.success(f"🚉 {name} | {', '.join(STATIONS[name]['lines'])}")
        else:
            st.warning("검색 결과가 없습니다.")

with tab_route:
    st.subheader("도착지 대중교통 길찾기")
    route_destination = st.selectbox("도착할 역을 선택하세요.", sorted(STATIONS.keys()))
    info = STATIONS[route_destination]
    st.write(f"도착역: **{route_destination}**")
    st.write(f"노선: **{', '.join(info['lines'])}**")
    st.link_button(
        "🗺️ Google 지도에서 대중교통 경로 보기",
        "https://www.google.com/maps/dir/?"
        + __import__("urllib.parse").parse.urlencode({
            "api": "1",
            "destination": f"{info['lat']},{info['lon']}",
            "travelmode": "transit"
        }),
        use_container_width=True
    )

st.markdown('</div>', unsafe_allow_html=True)
