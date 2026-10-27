
import streamlit as st
from urllib.parse import urlencode

st.set_page_config(
    page_title="스마트 역찾기",
    page_icon="🚇",
    layout="wide",
)

# 서울 지하철 주요 역 샘플 데이터
# 형식: 역 이름, 노선 목록, 지역/특징
STATIONS = [
    ("서울역", ["1호선", "4호선", "경의중앙선", "공항철도"], "서울 중구"),
    ("시청", ["1호선", "2호선"], "서울 중구"),
    ("종각", ["1호선"], "서울 종로구"),
    ("종로3가", ["1호선", "3호선", "5호선"], "서울 종로구"),
    ("종로5가", ["1호선"], "서울 종로구"),
    ("동대문", ["1호선", "4호선"], "서울 종로구"),
    ("동대문역사문화공원", ["2호선", "4호선", "5호선"], "서울 중구"),
    ("신설동", ["1호선", "2호선"], "서울 동대문구"),
    ("청량리", ["1호선", "경의중앙선"], "서울 동대문구"),
    ("용산", ["1호선", "경의중앙선"], "서울 용산구"),
    ("노량진", ["1호선", "9호선"], "서울 동작구"),
    ("영등포", ["1호선"], "서울 영등포구"),
    ("신도림", ["1호선", "2호선"], "서울 구로구"),
    ("구로", ["1호선"], "서울 구로구"),
    ("가산디지털단지", ["1호선", "7호선"], "서울 금천구"),
    ("금정", ["1호선", "4호선"], "경기 군포시"),
    ("구로디지털단지", ["2호선"], "서울 구로구"),
    ("대림", ["2호선", "7호선"], "서울 영등포구"),
    ("홍대입구", ["2호선", "경의중앙선", "공항철도"], "서울 마포구"),
    ("합정", ["2호선", "6호선"], "서울 마포구"),
    ("신촌", ["2호선"], "서울 마포구"),
    ("이대", ["2호선"], "서울 서대문구"),
    ("을지로입구", ["2호선"], "서울 중구"),
    ("을지로3가", ["2호선", "3호선"], "서울 중구"),
    ("을지로4가", ["2호선", "5호선"], "서울 중구"),
    ("동대입구", ["3호선"], "서울 중구"),
    ("충무로", ["3호선", "4호선"], "서울 중구"),
    ("약수", ["3호선", "6호선"], "서울 중구"),
    ("압구정", ["3호선"], "서울 강남구"),
    ("신사", ["3호선", "신분당선"], "서울 강남구"),
    ("고속터미널", ["3호선", "7호선", "9호선"], "서울 서초구"),
    ("교대", ["2호선", "3호선"], "서울 서초구"),
    ("양재", ["3호선", "신분당선"], "서울 서초구"),
    ("수서", ["3호선", "수인분당선"], "서울 강남구"),
    ("동작", ["4호선", "9호선"], "서울 동작구"),
    ("이촌", ["4호선", "경의중앙선"], "서울 용산구"),
    ("혜화", ["4호선"], "서울 종로구"),
    ("명동", ["4호선"], "서울 중구"),
    ("삼각지", ["4호선", "6호선"], "서울 용산구"),
    ("서울대입구", ["2호선"], "서울 관악구"),
    ("강남", ["2호선", "신분당선"], "서울 강남구"),
    ("역삼", ["2호선"], "서울 강남구"),
    ("선릉", ["2호선", "수인분당선"], "서울 강남구"),
    ("삼성", ["2호선"], "서울 강남구"),
    ("잠실", ["2호선", "8호선"], "서울 송파구"),
    ("강변", ["2호선"], "서울 광진구"),
    ("건대입구", ["2호선", "7호선"], "서울 광진구"),
    ("왕십리", ["2호선", "5호선", "수인분당선", "경의중앙선"], "서울 성동구"),
    ("성수", ["2호선"], "서울 성동구"),
    ("뚝섬", ["2호선"], "서울 성동구"),
    ("당산", ["2호선", "9호선"], "서울 영등포구"),
    ("영등포구청", ["2호선", "5호선"], "서울 영등포구"),
    ("까치산", ["2호선", "5호선"], "서울 강서구"),
    ("신당", ["2호선", "6호선"], "서울 중구"),
    ("합정", ["2호선", "6호선"], "서울 마포구"),
    ("공덕", ["5호선", "6호선", "경의중앙선", "공항철도"], "서울 마포구"),
    ("여의도", ["5호선", "9호선"], "서울 영등포구"),
    ("광화문", ["5호선"], "서울 종로구"),
    ("청구", ["5호선", "6호선"], "서울 중구"),
    ("군자", ["5호선", "7호선"], "서울 광진구"),
    ("천호", ["5호선", "8호선"], "서울 강동구"),
    ("올림픽공원", ["5호선", "9호선"], "서울 송파구"),
    ("왕십리", ["2호선", "5호선", "수인분당선", "경의중앙선"], "서울 성동구"),
    ("고려대", ["6호선"], "서울 성북구"),
    ("안암", ["6호선"], "서울 성북구"),
    ("이태원", ["6호선"], "서울 용산구"),
    ("월드컵경기장", ["6호선"], "서울 마포구"),
    ("태릉입구", ["6호선", "7호선"], "서울 노원구"),
    ("상봉", ["7호선", "경의중앙선"], "서울 중랑구"),
    ("면목", ["7호선"], "서울 중랑구"),
    ("청담", ["7호선"], "서울 강남구"),
    ("학동", ["7호선"], "서울 강남구"),
    ("논현", ["7호선", "신분당선"], "서울 강남구"),
    ("반포", ["7호선"], "서울 서초구"),
    ("장암", ["7호선"], "경기 의정부시"),
    ("암사", ["8호선"], "서울 강동구"),
    ("몽촌토성", ["8호선"], "서울 송파구"),
    ("석촌", ["8호선", "9호선"], "서울 송파구"),
    ("가락시장", ["3호선", "8호선"], "서울 송파구"),
    ("복정", ["8호선", "수인분당선"], "서울 송파구"),
    ("모란", ["8호선", "수인분당선"], "경기 성남시"),
    ("김포공항", ["5호선", "9호선", "공항철도"], "서울 강서구"),
    ("디지털미디어시티", ["6호선", "경의중앙선", "공항철도"], "서울 마포구"),
    ("인천공항1터미널", ["공항철도"], "인천 중구"),
    ("인천공항2터미널", ["공항철도"], "인천 중구"),
    ("판교", ["신분당선", "경강선"], "경기 성남시"),
    ("정자", ["신분당선", "수인분당선"], "경기 성남시"),
    ("광교", ["신분당선"], "경기 수원시"),
]

# 중복 역 이름 정리
station_map = {}
for name, lines, area in STATIONS:
    if name not in station_map:
        station_map[name] = {"name": name, "lines": [], "area": area}
    for line in lines:
        if line not in station_map[name]["lines"]:
            station_map[name]["lines"].append(line)

stations = sorted(
    station_map.values(),
    key=lambda item: item["name"]
)
all_lines = sorted({line for station in stations for line in station["lines"]})

st.title("🚇 스마트 역찾기")
st.caption("역 이름 검색부터 노선 확인, 출발역과 도착역 찾기까지")

tab_search, tab_line, tab_route = st.tabs(
    ["🔎 역 검색", "🗺️ 노선별 탐색", "📍 길찾기"]
)

with tab_search:
    st.subheader("어떤 역을 찾으세요?")
    keyword = st.text_input(
        "역 이름 입력",
        placeholder="예: 강남, 서울역, 홍대",
        key="station_search",
    )
    line_filter = st.selectbox(
        "노선 필터",
        ["전체 노선"] + all_lines,
        key="search_line",
    )

    results = [
        station for station in stations
        if keyword.strip().casefold() in station["name"].casefold()
        and (
            line_filter == "전체 노선"
            or line_filter in station["lines"]
        )
    ]

    st.write(f"검색 결과: **{len(results)}개 역**")

    if results:
        for station in results:
            with st.container(border=True):
                st.markdown(f"### 🚉 {station['name']}역")
                st.write("노선: " + " · ".join(station["lines"]))
                st.caption("지역: " + station["area"])
    else:
        st.info("검색 결과가 없습니다. 역 이름이나 노선 필터를 바꿔보세요.")

with tab_line:
    st.subheader("노선별로 역 둘러보기")
    selected_line = st.selectbox("노선 선택", all_lines, key="line_select")

    line_stations = [
        station for station in stations
        if selected_line in station["lines"]
    ]

    st.write(f"**{selected_line}** · 등록된 역 {len(line_stations)}개")
    st.caption(
        "아래 목록은 검색용 데이터이며, 실제 노선의 전체 역 순서와 다를 수 있습니다."
    )

    if line_stations:
        for start in range(0, len(line_stations), 10):
            chunk = line_stations[start:start + 10]
            with st.expander(
                f"{start + 1}~{start + len(chunk)}번 역 보기",
                expanded=(start == 0),
            ):
                for station in chunk:
                    st.write(
                        f"🚉 **{station['name']}** — "
                        f"{station['area']}"
                    )
    else:
        st.info("이 노선에 등록된 역이 없습니다.")

with tab_route:
    st.subheader("출발역에서 도착역까지")
    station_names = [station["name"] for station in stations]

    col1, col2 = st.columns(2)
    with col1:
        origin = st.selectbox(
            "출발역",
            station_names,
            index=station_names.index("서울역"),
            key="origin",
        )
    with col2:
        destination = st.selectbox(
            "도착역",
            station_names,
            index=station_names.index("강남"),
            key="destination",
        )

    if st.button("길찾기 링크 만들기", type="primary", use_container_width=True):
        if origin == destination:
            st.warning("출발역과 도착역이 같습니다. 다른 역을 선택해주세요.")
        else:
            start_station = station_map[origin]
            end_station = station_map[destination]
            shared_lines = sorted(
                set(start_station["lines"]) & set(end_station["lines"])
            )

            st.markdown("### 🧭 선택한 경로")
            st.write(f"**출발:** {origin}역 ({', '.join(start_station['lines'])})")
            st.write(f"**도착:** {destination}역 ({', '.join(end_station['lines'])})")

            if shared_lines:
                st.success(
                    "두 역에 공통으로 등록된 노선: "
                    + ", ".join(shared_lines)
                )
            else:
                st.info(
                    "두 역의 공통 노선이 없습니다. 환승 정보는 "
                    "아래 지도에서 확인해주세요."
                )

            params = urlencode({
                "api": "1",
                "origin": origin + "역, 서울",
                "destination": destination + "역, 서울",
                "travelmode": "transit",
            })
            url = "https://www.google.com/maps/dir/?" + params

            st.link_button(
                "🗺️ 지도에서 대중교통 경로 확인",
                url,
                use_container_width=True,
            )
            st.caption(
                "예상 소요 시간, 실제 운행 경로 및 환승 정보는 지도 서비스에서 확인하세요."
            )

st.divider()
st.caption(
    "스마트 역찾기 | 역 데이터는 주요 역 예시이며 실시간 교통 정보가 아닙니다."
)
