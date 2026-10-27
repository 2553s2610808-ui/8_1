
import math
from urllib.parse import urlencode

import streamlit as st
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(
    page_title="스마트 역찾기",
    page_icon="🚇",
    layout="wide",
)

# 주요 지하철역 좌표 (위도, 경도)
STATIONS = {
    "서울역": {
        "lines": ["1호선", "4호선", "경의중앙선", "공항철도"],
        "lat": 37.5547, "lon": 126.9707,
    },
    "시청": {
        "lines": ["1호선", "2호선"],
        "lat": 37.5636, "lon": 126.9759,
    },
    "종각": {
        "lines": ["1호선"],
        "lat": 37.5702, "lon": 126.9831,
    },
    "종로3가": {
        "lines": ["1호선", "3호선", "5호선"],
        "lat": 37.5710, "lon": 126.9918,
    },
    "동대문": {
        "lines": ["1호선", "4호선"],
        "lat": 37.5714, "lon": 127.0095,
    },
    "명동": {
        "lines": ["4호선"],
        "lat": 37.5609, "lon": 126.9860,
    },
    "충무로": {
        "lines": ["3호선", "4호선"],
        "lat": 37.5614, "lon": 126.9940,
    },
    "홍대입구": {
        "lines": ["2호선", "경의중앙선", "공항철도"],
        "lat": 37.5572, "lon": 126.9254,
    },
    "신촌": {
        "lines": ["2호선"],
        "lat": 37.5551, "lon": 126.9368,
    },
    "합정": {
        "lines": ["2호선", "6호선"],
        "lat": 37.5496, "lon": 126.9139,
    },
    "공덕": {
        "lines": ["5호선", "6호선", "경의중앙선", "공항철도"],
        "lat": 37.5440, "lon": 126.9516,
    },
    "여의도": {
        "lines": ["5호선", "9호선"],
        "lat": 37.5216, "lon": 126.9243,
    },
    "당산": {
        "lines": ["2호선", "9호선"],
        "lat": 37.5344, "lon": 126.9028,
    },
    "신도림": {
        "lines": ["1호선", "2호선"],
        "lat": 37.5088, "lon": 126.8913,
    },
    "노량진": {
        "lines": ["1호선", "9호선"],
        "lat": 37.5142, "lon": 126.9420,
    },
    "고속터미널": {
        "lines": ["3호선", "7호선", "9호선"],
        "lat": 37.5048, "lon": 127.0049,
    },
    "강남": {
        "lines": ["2호선", "신분당선"],
        "lat": 37.4979, "lon": 127.0276,
    },
    "역삼": {
        "lines": ["2호선"],
        "lat": 37.5007, "lon": 127.0364,
    },
    "선릉": {
        "lines": ["2호선", "수인분당선"],
        "lat": 37.5045, "lon": 127.0490,
    },
    "삼성": {
        "lines": ["2호선"],
        "lat": 37.5088, "lon": 127.0632,
    },
    "잠실": {
        "lines": ["2호선", "8호선"],
        "lat": 37.5133, "lon": 127.1001,
    },
    "건대입구": {
        "lines": ["2호선", "7호선"],
        "lat": 37.5404, "lon": 127.0692,
    },
    "왕십리": {
        "lines": ["2호선", "5호선", "수인분당선", "경의중앙선"],
        "lat": 37.5612, "lon": 127.0370,
    },
    "고려대": {
        "lines": ["6호선"],
        "lat": 37.5905, "lon": 127.0363,
    },
    "이태원": {
        "lines": ["6호선"],
        "lat": 37.5345, "lon": 126.9946,
    },
    "김포공항": {
        "lines": ["5호선", "9호선", "공항철도"],
        "lat": 37.5618, "lon": 126.8019,
    },
    "디지털미디어시티": {
        "lines": ["6호선", "경의중앙선", "공항철도"],
        "lat": 37.5761, "lon": 126.9008,
    },
    "판교": {
        "lines": ["신분당선", "경강선"],
        "lat": 37.3948, "lon": 127.1112,
    },
    "정자": {
        "lines": ["신분당선", "수인분당선"],
        "lat": 37.3670, "lon": 127.1081,
    },
    "광교": {
        "lines": ["신분당선"],
        "lat": 37.3021, "lon": 127.0445,
    },
}


def station_label(name):
    """역 이름 뒤에 '역'을 한 번만 붙임."""
    return name if name.endswith("역") else name + "역"


def distance_km(lat1, lon1, lat2, lon2):
    """두 좌표 사이의 직선거리를 km로 계산."""
    radius = 6371.0

    lat1, lon1, lat2, lon2 = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    a = min(1.0, max(0.0, a))
    return 2 * radius * math.asin(math.sqrt(a))


st.title("🚇 스마트 역찾기")
st.write("현재 위치에서 가까운 지하철역을 찾아보세요.")

tab_nearest, tab_search, tab_route = st.tabs(
    ["📍 가까운 역 찾기", "🔎 역 검색", "🗺️ 길찾기"]
)

# 1. 현재 위치에서 가까운 역 찾기
with tab_nearest:
    st.subheader("내 주변 지하철역")
    st.write(
        "아래 위치 확인 기능을 실행하고 브라우저의 "
        "위치 권한을 허용해주세요."
    )

    try:
        location = streamlit_geolocation()

        if isinstance(location, dict):
            lat = location.get("latitude")
            lon = location.get("longitude")

            if lat is not None and lon is not None:
                lat = float(lat)
                lon = float(lon)

                if (
                    math.isfinite(lat)
                    and math.isfinite(lon)
                    and -90 <= lat <= 90
                    and -180 <= lon <= 180
                ):
                    results = []

                    for name, data in STATIONS.items():
                        distance = distance_km(
                            lat,
                            lon,
                            data["lat"],
                            data["lon"],
                        )
                        results.append(
                            (name, distance, data["lines"])
                        )

                    results.sort(key=lambda item: item[1])
                    nearest = results[0]

                    st.success(
                        f"가장 가까운 등록 역: "
                        f"**{station_label(nearest[0])}**"
                    )

                    st.metric(
                        "현재 위치와 역 사이의 직선거리",
                        f"{nearest[1]:.2f} km",
                    )

                    st.write(
                        "노선: " + ", ".join(nearest[2])
                    )

                    st.caption(
                        "직선거리 기준이며, 실제 도보 거리는 "
                        "다를 수 있습니다."
                    )

                    destination = station_label(nearest[0])
                    encoded_destination = (
                        destination + ", 대한민국"
                    )

                    walking_url = (
                        "https://www.google.com/maps/dir/?"
                        + urlencode({
                            "api": "1",
                            "origin": f"{lat},{lon}",
                            "destination": encoded_destination,
                            "travelmode": "walking",
                        })
                    )

                    transit_url = (
                        "https://www.google.com/maps/dir/?"
                        + urlencode({
                            "api": "1",
                            "origin": f"{lat},{lon}",
                            "destination": encoded_destination,
                            "travelmode": "transit",
                        })
                    )

                    st.link_button(
                        "🚶 가장 가까운 역까지 도보 안내",
                        walking_url,
                        use_container_width=True,
                    )

                    st.link_button(
                        "🚇 대중교통 경로 확인",
                        transit_url,
                        use_container_width=True,
                    )

                    st.subheader("가까운 역 TOP 5")

                    for i, (name, km, lines) in enumerate(
                        results[:5], start=1
                    ):
                        st.write(
                            f"**{i}. {station_label(name)}** — "
                            f"{km:.2f} km · {', '.join(lines)}"
                        )

                else:
                    st.error("위치 좌표가 올바르지 않습니다.")
            else:
                st.info(
                    "위치 정보가 없습니다. 브라우저의 위치 권한을 "
                    "허용하고 다시 확인해주세요."
                )

    except Exception:
        st.error(
            "위치를 확인하지 못했습니다. HTTPS 접속과 "
            "브라우저의 위치 권한을 확인해주세요."
        )

# 2. 역 이름 검색
with tab_search:
    keyword = st.text_input(
        "찾을 역 이름",
        placeholder="예: 강남, 서울역, 홍대입구",
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
                st.write(
                    f"좌표: {data['lat']:.5f}, {data['lon']:.5f}"
                )
    else:
        st.warning("등록된 역을 찾을 수 없습니다.")

# 3. 직접 출발역과 도착역 선택
with tab_route:
    station_names = list(STATIONS.keys())

    origin = st.selectbox(
        "출발역",
        station_names,
        index=station_names.index("서울역"),
    )

    destination = st.selectbox(
        "도착역",
        station_names,
        index=station_names.index("강남"),
    )

    if st.button("길찾기", type="primary"):
        if origin == destination:
            st.warning("출발역과 도착역이 같습니다.")
        else:
            start = STATIONS[origin]
            end = STATIONS[destination]

            url = (
                "https://www.google.com/maps/dir/?"
                + urlencode({
                    "api": "1",
                    "origin": (
                        f"{start['lat']},{start['lon']}"
                    ),
                    "destination": (
                        f"{end['lat']},{end['lon']}"
                    ),
                    "travelmode": "transit",
                })
            )

            st.write(
                f"{station_label(origin)} → "
                f"{station_label(destination)}"
            )

            st.link_button(
                "지도에서 경로 확인",
                url,
                use_container_width=True,
            )

st.divider()
st.caption(
    "역찾기 서비스 · 등록된 주요 역 좌표를 사용합니다. "
    "전체 역이나 실시간 열차 정보는 포함하지 않습니다."
)
