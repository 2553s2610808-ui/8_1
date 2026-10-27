
import math
from urllib.parse import urlencode

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="스마트 역찾기",
    page_icon="🚇",
    layout="wide",
)

# 주요 역의 좌표: 위도, 경도
STATIONS = {
    "서울역": {"lines": ["1호선", "4호선", "공항철도"], "lat": 37.5547, "lon": 126.9707},
    "시청": {"lines": ["1호선", "2호선"], "lat": 37.5636, "lon": 126.9759},
    "종각": {"lines": ["1호선"], "lat": 37.5702, "lon": 126.9831},
    "종로3가": {"lines": ["1호선", "3호선", "5호선"], "lat": 37.5710, "lon": 126.9918},
    "동대문": {"lines": ["1호선", "4호선"], "lat": 37.5714, "lon": 127.0095},
    "명동": {"lines": ["4호선"], "lat": 37.5609, "lon": 126.9860},
    "충무로": {"lines": ["3호선", "4호선"], "lat": 37.5614, "lon": 126.9940},
    "홍대입구": {"lines": ["2호선", "경의중앙선", "공항철도"], "lat": 37.5572, "lon": 126.9254},
    "신촌": {"lines": ["2호선"], "lat": 37.5551, "lon": 126.9368},
    "합정": {"lines": ["2호선", "6호선"], "lat": 37.5496, "lon": 126.9139},
    "공덕": {"lines": ["5호선", "6호선", "공항철도"], "lat": 37.5440, "lon": 126.9516},
    "여의도": {"lines": ["5호선", "9호선"], "lat": 37.5216, "lon": 126.9243},
    "당산": {"lines": ["2호선", "9호선"], "lat": 37.5344, "lon": 126.9028},
    "신도림": {"lines": ["1호선", "2호선"], "lat": 37.5088, "lon": 126.8913},
    "노량진": {"lines": ["1호선", "9호선"], "lat": 37.5142, "lon": 126.9420},
    "고속터미널": {"lines": ["3호선", "7호선", "9호선"], "lat": 37.5048, "lon": 127.0049},
    "강남": {"lines": ["2호선", "신분당선"], "lat": 37.4979, "lon": 127.0276},
    "역삼": {"lines": ["2호선"], "lat": 37.5007, "lon": 127.0364},
    "선릉": {"lines": ["2호선", "수인분당선"], "lat": 37.5045, "lon": 127.0490},
    "삼성": {"lines": ["2호선"], "lat": 37.5088, "lon": 127.0632},
    "잠실": {"lines": ["2호선", "8호선"], "lat": 37.5133, "lon": 127.1001},
    "건대입구": {"lines": ["2호선", "7호선"], "lat": 37.5404, "lon": 127.0692},
    "왕십리": {"lines": ["2호선", "5호선", "수인분당선", "경의중앙선"], "lat": 37.5612, "lon": 127.0370},
    "고려대": {"lines": ["6호선"], "lat": 37.5905, "lon": 127.0363},
    "이태원": {"lines": ["6호선"], "lat": 37.5345, "lon": 126.9946},
    "김포공항": {"lines": ["5호선", "9호선", "공항철도"], "lat": 37.5618, "lon": 126.8019},
    "디지털미디어시티": {"lines": ["6호선", "공항철도"], "lat": 37.5761, "lon": 126.9008},
    "판교": {"lines": ["신분당선", "경강선"], "lat": 37.3948, "lon": 127.1112},
    "정자": {"lines": ["신분당선", "수인분당선"], "lat": 37.3670, "lon": 127.1081},
    "광교": {"lines": ["신분당선"], "lat": 37.3021, "lon": 127.0445},
}


def station_label(name):
    return name if name.endswith("역") else name + "역"


def distance_km(lat1, lon1, lat2, lon2):
    """두 좌표 사이의 직선거리(km)를 계산합니다."""
    radius = 6371.0

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

    a = min(1.0, max(0.0, a))
    return 2 * radius * math.asin(math.sqrt(a))


st.title("🚇 스마트 역찾기")
st.caption("내 주변 지하철역을 찾고 길 안내를 확인하세요.")

# 탭을 먼저 선언하므로 tab_nearest NameError가 발생하지 않습니다.
tab_nearest, tab_search, tab_route = st.tabs(
    ["📍 가까운 역 찾기", "🔎 역 검색", "🗺️ 역 간 길찾기"]
)

# --------------------------------------------------
# 1. 현재 위치에서 가까운 역 찾기
# --------------------------------------------------
with tab_nearest:
    st.subheader("내 주변 가장 가까운 지하철역")
    st.write(
        "버튼을 누른 뒤 위치 권한을 허용하세요. "
        "등록된 역의 좌표와 현재 위치를 비교합니다."
    )

    # 위치 정보는 브라우저 안에서 처리합니다.
    components.html(
        """
        <div style="font-family: sans-serif; line-height: 1.6;">
          <button id="locate"
            style="padding:12px 16px;border:0;border-radius:8px;
                   background:#1769aa;color:white;font-size:16px;
                   cursor:pointer;">
            📍 현재 위치로 가까운 역 찾기
          </button>
          <p id="status">위치 확인을 시작하려면 버튼을 누르세요.</p>
          <div id="result"></div>
        </div>

        <script>
        const statusEl = document.getElementById("status");
        const resultEl = document.getElementById("result");

        // Python의 역 좌표 데이터를 브라우저에 전달합니다.
        const stations = STATION_DATA_PLACEHOLDER;

        document.getElementById("locate").addEventListener("click", () => {
          resultEl.innerHTML = "";

          if (!navigator.geolocation) {
            statusEl.textContent = "이 브라우저에서는 위치 기능을 사용할 수 없습니다.";
            return;
          }

          statusEl.textContent = "현재 위치를 확인하고 있습니다...";

          navigator.geolocation.getCurrentPosition(
            (position) => {
              const lat = position.coords.latitude;
              const lon = position.coords.longitude;

              const rad = (deg) => deg * Math.PI / 180;

              const distance = (a, b, c, d) => {
                const R = 6371;
                const dLat = rad(c - a);
                const dLon = rad(d - b);
                const value =
                  Math.sin(dLat / 2) ** 2 +
                  Math.cos(rad(a)) * Math.cos(rad(c)) *
                  Math.sin(dLon / 2) ** 2;
                return 2 * R * Math.asin(Math.sqrt(Math.min(1, value)));
              };

              const results = stations.map((s) => ({
                ...s,
                km: distance(lat, lon, s.lat, s.lon)
              })).sort((a, b) => a.km - b.km);

              const nearest = results[0];
              statusEl.textContent = "현재 위치 확인 완료!";

              const heading = document.createElement("h3");
              heading.textContent = "가장 가까운 역: " + nearest.name;
              resultEl.appendChild(heading);

              const distanceText = document.createElement("p");
              distanceText.textContent =
                "직선거리 " + nearest.km.toFixed(2) + " km";
              resultEl.appendChild(distanceText);

              const lineText = document.createElement("p");
              lineText.textContent = "노선: " + nearest.lines.join(", ");
              resultEl.appendChild(lineText);

              const note = document.createElement("p");
              note.textContent =
                "직선거리 기준입니다. 실제 도보 거리는 다를 수 있습니다.";
              resultEl.appendChild(note);

              const map = document.createElement("a");
              map.href =
                "https://www.google.com/maps/dir/?" +
                new URLSearchParams({
                  api: "1",
                  origin: lat + "," + lon,
                  destination: nearest.name + "역, 대한민국",
                  travelmode: "walking"
                }).toString();
              map.target = "_blank";
              map.rel = "noopener noreferrer";
              map.textContent = "🚶 가장 가까운 역까지 도보 길 안내";
              map.style.display = "inline-block";
              map.style.padding = "12px";
              map.style.background = "#e8f2ff";
              map.style.borderRadius = "8px";
              resultEl.appendChild(map);

              const title = document.createElement("h4");
              title.textContent = "가까운 역 TOP 5";
              resultEl.appendChild(title);

              results.slice(0, 5).forEach((s, i) => {
                const row = document.createElement("p");
                row.textContent =
                  (i + 1) + ". " + s.name + "역 — " +
                  s.km.toFixed(2) + " km";
                resultEl.appendChild(row);
              });
            },
            (error) => {
              const messages = {
                1: "위치 권한이 거부되었습니다. 브라우저 설정에서 허용해주세요.",
                2: "위치를 확인할 수 없습니다. 기기의 위치 서비스를 확인해주세요.",
                3: "위치 확인 시간이 초과되었습니다. 다시 시도해주세요."
              };
              statusEl.textContent =
                messages[error.code] || "위치 확인에 실패했습니다.";
            },
            {
              enableHighAccuracy: true,
              timeout: 15000,
              maximumAge: 60000
            }
          );
        });
        </script>
        """.replace(
            "STATION_DATA_PLACEHOLDER",
            __import__("json").dumps(
                [
                    {
                        "name": name,
                        "lines": data["lines"],
                        "lat": data["lat"],
                        "lon": data["lon"],
                    }
                    for name, data in STATIONS.items()
                ],
                ensure_ascii=False,
            ),
        ),
        height=570,
    )

    st.caption(
        "위치 정보는 브라우저에서 처리됩니다. "
        "위치 확인은 HTTPS 환경에서 작동하며 브라우저 권한이 필요합니다."
    )

# --------------------------------------------------
# 2. 역 검색
# --------------------------------------------------
with tab_search:
    st.subheader("역 이름으로 검색")

    keyword = st.text_input(
        "역 이름",
        placeholder="예: 강남, 서울역, 홍대입구",
        key="station_keyword",
    )

    matches = [
        (name, data)
        for name, data in STATIONS.items()
        if keyword.strip().casefold() in name.casefold()
    ]

    if not keyword.strip():
        st.info("검색할 역 이름을 입력해주세요.")
    elif matches:
        for name, data in matches:
            with st.container(border=True):
                st.subheader(station_label(name))
                st.write("노선: " + ", ".join(data["lines"]))
    else:
        st.warning("검색 결과가 없습니다.")

# --------------------------------------------------
# 3. 역 간 길찾기
# --------------------------------------------------
with tab_route:
    st.subheader("역에서 역으로 길찾기")

    names = list(STATIONS.keys())

    origin = st.selectbox(
        "출발역",
        names,
        index=names.index("서울역"),
        key="route_origin",
    )

    destination = st.selectbox(
        "도착역",
        names,
        index=names.index("강남"),
        key="route_destination",
    )

    if st.button("🗺️ 대중교통 경로 확인", type="primary"):
        if origin == destination:
            st.warning("출발역과 도착역이 같습니다.")
        else:
            start = STATIONS[origin]
            end = STATIONS[destination]

            url = "https://www.google.com/maps/dir/?" + urlencode({
                "api": "1",
                "origin": f"{start['lat']},{start['lon']}",
                "destination": f"{end['lat']},{end['lon']}",
                "travelmode": "transit",
            })

            st.write(
                f"{station_label(origin)} → {station_label(destination)}"
            )
            st.link_button(
                "대중교통 경로를 지도에서 확인",
                url,
                use_container_width=True,
            )

st.divider()
st.caption(
    "주요 역 샘플 데이터 기반 서비스 · 실시간 열차 정보는 제공하지 않습니다."
)
