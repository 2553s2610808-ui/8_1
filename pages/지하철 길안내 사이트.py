
import streamlit as st
import pandas as pd
import requests
import heapq
import re
import json
import math
import pydeck as pdk
import streamlit.components.v1 as components

from urllib.parse import quote
from io import StringIO, BytesIO
from itertools import combinations


# ==================================================
# 1. 기본 설정
# ==================================================

st.set_page_config(
    page_title="BLUE ROUTE | 지하철 길찾기",
    page_icon="🚇",
    layout="wide"
)

STATION_URL = (
    "https://raw.githubusercontent.com/"
    "JoeYunHa/korea_seoul_subway_static_data/"
    "main/data/subway_station.csv"
)

SECTION_URL = (
    "https://raw.githubusercontent.com/"
    "JoeYunHa/korea_seoul_subway_static_data/"
    "main/data/subway_section.csv"
)

KRIC_URL = (
    "https://data.kric.go.kr/rips/M_01_01/"
    "detail.do?id=1294&lcd=A"
)

공식사이버스테이션 = (
    "https://www.seoulmetro.co.kr/kr/cyberStation.do"
)


# ==================================================
# 2. 노선별 색상
# ==================================================

노선색상표 = {
    "1호선": [0, 72, 152],
    "2호선": [0, 162, 98],
    "3호선": [255, 119, 0],
    "4호선": [0, 166, 220],
    "5호선": [153, 102, 204],
    "6호선": [205, 153, 0],
    "7호선": [105, 92, 170],
    "8호선": [232, 0, 58],
    "9호선": [178, 168, 153],
    "신분당선": [200, 0, 50],
    "수인분당선": [255, 205, 0],
    "경의중앙선": [119, 198, 161],
    "공항철도": [0, 161, 216],
    "경춘선": [0, 192, 198],
    "우이신설선": [182, 165, 210],
    "서해선": [138, 158, 166],
    "신림선": [103, 173, 70],
    "경강선": [0, 159, 214],
    "김포골드라인": [170, 160, 140],
    "의정부경전철": [255, 190, 0],
    "용인경전철": [80, 180, 80],
    "에버라인": [80, 180, 80],
}


def 노선색상(노선):

    노선문자 = str(노선).replace(" ", "")

    for 이름, 색상 in 노선색상표.items():

        if 이름 in 노선문자:
            return 색상

    return [40, 120, 190]


# ==================================================
# 3. 디자인
# ==================================================

st.markdown("""
<style>

.stApp {
    background: #F1F7FF;
    color: #172554;
}

.block-container {
    max-width: 1100px;
    padding-top: 30px;
    padding-bottom: 50px;
}

h1, h2, h3 {
    color: #123B72;
}

div[data-testid="stTextInput"] input {
    border: 1px solid #BFDBFE;
    border-radius: 12px;
    min-height: 48px;
    background: white;
    color: #172554;
}

div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(
        90deg,
        #1D4ED8,
        #0284C7
    );
    border: none;
    border-radius: 12px;
    color: white;
    font-size: 16px;
    font-weight: 800;
    min-height: 48px;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #BFDBFE;
    border-radius: 15px;
    padding: 14px;
}

div[data-testid="stExpander"] {
    background: white;
    border: 1px solid #BFDBFE;
    border-radius: 12px;
}

hr {
    border-color: #DBEAFE;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 4. 역 이름 정리
# ==================================================

def 역이름키(이름):

    이름 = re.sub(
        r"\s+",
        "",
        str(이름)
    )

    if 이름 in ("서울", "서울역"):
        return "서울역"

    if 이름.endswith("역") and len(이름) > 1:
        이름 = 이름[:-1]

    return 이름


def 역이름표시(node, 역정보):

    정보 = 역정보.get(str(node))

    if not 정보:
        return "역 이름 확인 필요"

    이름 = str(
        정보.get("name", "")
    ).strip()

    if not 이름 or 이름.isdigit():
        return "역 이름 확인 필요"

    if 이름 in ("서울", "서울역"):
        return "서울역"

    if 이름.endswith("역"):
        return 이름

    return 이름 + "역"


# ==================================================
# 5. 역 사이 거리 계산
# ==================================================

def 두역거리(a, b):

    if (
        a["lat"] is None
        or a["lng"] is None
        or b["lat"] is None
        or b["lng"] is None
    ):
        return float("inf")

    반지름 = 6371000

    위도1 = math.radians(a["lat"])
    위도2 = math.radians(b["lat"])

    위도차 = math.radians(
        b["lat"] - a["lat"]
    )

    경도차 = math.radians(
        b["lng"] - a["lng"]
    )

    값 = (
        (1 - math.cos(위도차)) / 2
        + math.cos(위도1)
        * math.cos(위도2)
        * (1 - math.cos(경도차)) / 2
    )

    값 = min(
        1,
        max(0, 값)
    )

    return (
        2 * 반지름
        * math.asin(값 ** 0.5)
    )


# ==================================================
# 6. 네이버 지도
# ==================================================

def 네이버지도용좌표(lat, lng):

    if lat is None or lng is None:
        return None, None

    x = lng * 20037508.34 / 180

    y = math.log(
        math.tan(
            (90 + lat) * math.pi / 360
        )
    ) / (math.pi / 180)

    y = y * 20037508.34 / 180

    return x, y


def 네이버지도경로URL(
    출발노드,
    도착노드,
    역정보
):

    출발 = 역정보.get(str(출발노드))
    도착 = 역정보.get(str(도착노드))

    if not 출발 or not 도착:
        return None

    sx, sy = 네이버지도용좌표(
        출발.get("lat"),
        출발.get("lng")
    )

    dx, dy = 네이버지도용좌표(
        도착.get("lat"),
        도착.get("lng")
    )

    if None in (sx, sy, dx, dy):
        return None

    출발이름 = quote(
        역이름표시(출발노드, 역정보),
        safe=""
    )

    도착이름 = quote(
        역이름표시(도착노드, 역정보),
        safe=""
    )

    return (
        "https://map.naver.com/p/directions/"
        f"{sx:.3f},{sy:.3f},{출발이름}/"
        f"{dx:.3f},{dy:.3f},{도착이름}/-/transit"
        "?c=13.00,0,0,0,dh"
    )


# ==================================================
# 7. 기존 지하철 데이터 불러오기
# ==================================================

@st.cache_data(ttl=86400)
def 데이터불러오기():

    def csv읽기(url):

        response = requests.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        return pd.read_csv(
            StringIO(
                response.content.decode("utf-8-sig")
            ),
            dtype=str,
            keep_default_na=False
        )

    역자료 = csv읽기(STATION_URL)
    구간자료 = csv읽기(SECTION_URL)

    역정보 = {}
    역코드표 = {}
    노선별역표 = {}

    for row in 역자료.to_dict("records"):

        node = row.get(
            "station_id",
            ""
        ).strip()

        line = row.get(
            "line",
            ""
        ).strip()

        name = row.get(
            "name",
            ""
        ).strip()

        code = row.get(
            "station_cd",
            ""
        ).strip()

        if not node or not line or not name:
            continue

        try:

            lat = float(
                row.get("lat", "")
            )

            lng = float(
                row.get("lng", "")
            )

        except (ValueError, TypeError):

            lat = None
            lng = None

        역정보[node] = {
            "line": line,
            "name": name,
            "lat": lat,
            "lng": lng
        }

        if code:

            역코드표.setdefault(
                (line, code),
                node
            )

        key = 역이름키(name)

        노선별역표.setdefault(
            (line, key),
            []
        ).append(node)

    그래프 = {
        node: set()
        for node in 역정보
    }

    노선도구간 = []

    def 연결(a, b, 이동수=1, 환승수=0):

        if a == b:
            return

        if a not in 그래프 or b not in 그래프:
            return

        그래프[a].add(
            (b, 이동수, 환승수)
        )

        그래프[b].add(
            (a, 이동수, 환승수)
        )

    # 인접 역 연결
    for row in 구간자료.to_dict("records"):

        line = row.get(
            "line",
            ""
        ).strip()

        code_a = row.get(
            "up_station_code",
            ""
        ).strip()

        code_b = row.get(
            "down_station_code",
            ""
        ).strip()

        name_a = row.get(
            "up_station_name",
            ""
        ).strip()

        name_b = row.get(
            "down_station_name",
            ""
        ).strip()

        a = 역코드표.get(
            (line, code_a)
        )

        b = 역코드표.get(
            (line, code_b)
        )

        if not a:

            candidates = 노선별역표.get(
                (line, 역이름키(name_a)),
                []
            )

            if candidates:
                a = candidates[0]

        if not b:

            candidates = 노선별역표.get(
                (line, 역이름키(name_b)),
                []
            )

            if candidates:
                b = candidates[0]

        if a and b:

            연결(a, b, 1, 0)

            정보_a = 역정보[a]
            정보_b = 역정보[b]

            if all(
                x is not None
                for x in (
                    정보_a["lat"],
                    정보_a["lng"],
                    정보_b["lat"],
                    정보_b["lng"]
                )
            ):

                노선도구간.append({

                    "line": line,

                    "path": [
                        [
                            정보_a["lng"],
                            정보_a["lat"]
                        ],
                        [
                            정보_b["lng"],
                            정보_b["lat"]
                        ]
                    ],

                    "color": 노선색상(line)
                })

    # 환승 연결
    이름별노드 = {}

    for node, info in 역정보.items():

        key = 역이름키(
            info["name"]
        )

        이름별노드.setdefault(
            key,
            []
        ).append(node)

    for nodes in 이름별노드.values():

        for a, b in combinations(nodes, 2):

            if 역정보[a]["line"] == 역정보[b]["line"]:
                continue

            if 두역거리(
                역정보[a],
                역정보[b]
            ) <= 500:

                연결(a, b, 0, 1)

    역검색표 = {
        key: sorted(set(nodes))
        for key, nodes in 이름별노드.items()
    }

    return (
        역정보,
        그래프,
        역검색표,
        노선도구간
    )


# ==================================================
# 8. 전국 역 목록 불러오기
# ==================================================

def 컬럼찾기(df, 후보목록):

    정리된컬럼 = {}

    for column in df.columns:

        key = re.sub(
            r"[\s_\-]",
            "",
            str(column)
        ).lower()

        정리된컬럼[key] = column

    for candidate in 후보목록:

        key = re.sub(
            r"[\s_\-]",
            "",
            candidate
        ).lower()

        if key in 정리된컬럼:
            return 정리된컬럼[key]

    return None


def 전국역자료가공(원본):

    원본 = 원본.copy()

    원본.columns = [
        str(column).strip()
        for column in 원본.columns
    ]

    역명컬럼 = 컬럼찾기(
        원본,
        [
            "역명(한글)",
            "역명(국문)",
            "한글역명",
            "역명",
            "STIN_NM"
        ]
    )

    노선컬럼 = 컬럼찾기(
        원본,
        [
            "운영노선",
            "운영노선명",
            "선명",
            "노선명",
            "노선",
            "LN_NM"
        ]
    )

    기관컬럼 = 컬럼찾기(
        원본,
        [
            "철도운영기관명",
            "운영기관명",
            "운영기관",
            "철도운영기관",
            "RAIL_OPR_ISTT_NM"
        ]
    )

    지역컬럼 = 컬럼찾기(
        원본,
        [
            "권역명",
            "권역",
            "권역코드",
            "지역명",
            "지역",
            "시도명"
        ]
    )

    if not 역명컬럼:

        raise ValueError(
            "한글 역명 컬럼을 찾지 못했어. "
            "공식 전국 도시광역철도 역사정보 "
            "파일인지 확인해 줘."
        )

    def 값가져오기(row, column):

        if not column:
            return ""

        value = row.get(
            column,
            ""
        )

        if pd.isna(value):
            return ""

        return str(value).strip()

    권역코드표 = {
        "01": "수도권",
        "02": "부산권",
        "03": "대구권",
        "04": "광주권",
        "05": "대전권"
    }

    def 지역분류(region, operator, line):

        region = str(region).strip()

        if region:

            if region in 권역코드표:
                return 권역코드표[region]

            if "수도권" in region:
                return "수도권"

            for keyword, result in [
                ("서울", "수도권"),
                ("경기", "수도권"),
                ("인천", "수도권"),
                ("부산", "부산권"),
                ("울산", "부산권"),
                ("대구", "대구권"),
                ("광주", "광주권"),
                ("대전", "대전권")
            ]:

                if keyword in region:
                    return result

            return region

        all_text = operator + " " + line

        지역키워드 = {
            "수도권": [
                "서울교통공사",
                "인천교통공사",
                "서울메트로",
                "GTX",
                "수도권",
                "신분당선",
                "경의중앙선",
                "수인분당선",
                "경강선",
                "경춘선",
                "서해선"
            ],

            "부산권": [
                "부산교통공사",
                "부산",
                "부산김해경전철",
                "동해선"
            ],

            "대구권": [
                "대구교통공사",
                "대구",
                "대경선"
            ],

            "광주권": [
                "광주교통공사",
                "광주"
            ],

            "대전권": [
                "대전교통공사",
                "대전"
            ]
        }

        for region_name, keywords in 지역키워드.items():

            if any(
                keyword in all_text
                for keyword in keywords
            ):

                return region_name

        return "권역 확인 필요"

    자료 = []

    for _, row in 원본.iterrows():

        역명 = 값가져오기(
            row,
            역명컬럼
        )

        if not 역명:
            continue

        노선 = 값가져오기(
            row,
            노선컬럼
        )

        기관 = 값가져오기(
            row,
            기관컬럼
        )

        지역 = 값가져오기(
            row,
            지역컬럼
        )

        자료.append({

            "지역": 지역분류(
                지역,
                기관,
                노선
            ),

            "운영기관": 기관 or "정보 없음",

            "노선": 노선 or "정보 없음",

            "역명": 역명
        })

    결과 = pd.DataFrame(자료)

    if 결과.empty:
        raise ValueError("역 데이터가 비어 있어.")

    return (
        결과
        .drop_duplicates()
        .sort_values(
            ["지역", "노선", "역명"]
        )
        .reset_index(drop=True)
    )


# ==================================================
# 9. 지하철 지도 그리기
# ==================================================

def 노선도그리기(
    역정보,
    노선도구간,
    선택노선="전체 노선",
    강조경로=None
):

    if 선택노선 == "전체 노선":

        표시구간 = 노선도구간

    else:

        표시구간 = [
            구간 for 구간 in 노선도구간
            if 구간["line"] == 선택노선
        ]

    if not 표시구간:

        st.warning(
            "표시할 역 좌표가 없어."
        )

        return

    역점목록 = []

    for node, info in 역정보.items():

        if (
            info["lat"] is None
            or info["lng"] is None
        ):
            continue

        if (
            선택노선 != "전체 노선"
            and info["line"] != 선택노선
        ):
            continue

        역점목록.append({

            "position": [
                info["lng"],
                info["lat"]
            ],

            "name": 역이름표시(
                node,
                역정보
            ),

            "line": info["line"]
        })

    layers = [

        pdk.Layer(
            "PathLayer",
            data=표시구간,
            get_path="path",
            get_color="color",
            get_width=4,
            width_scale=1,
            width_min_pixels=2,
            pickable=True
        ),

        pdk.Layer(
            "ScatterplotLayer",
            data=역점목록,
            get_position="position",
            get_radius=35,
            radius_min_pixels=2,
            radius_max_pixels=5,
            get_fill_color=[255, 255, 255],
            get_line_color=[30, 80, 140],
            line_width_min_pixels=1,
            stroked=True,
            filled=True,
            pickable=True
        )
    ]

    # 검색 경로 표시
    if 강조경로:

        경로좌표 = []

        for node in 강조경로:

            info = 역정보.get(
                str(node)
            )

            if (
                info
                and info["lat"] is not None
                and info["lng"] is not None
            ):

                경로좌표.append([
                    info["lng"],
                    info["lat"]
                ])

        if len(경로좌표) >= 2:

            layers.append(
                pdk.Layer(
                    "PathLayer",
                    data=[
                        {
                            "path": 경로좌표
                        }
                    ],
                    get_path="path",
                    get_color=[239, 68, 68],
                    get_width=8,
                    width_scale=1,
                    width_min_pixels=4
                )
            )

    if 강조경로:

        중심좌표 = [
            역정보[str(node)]
            for node in 강조경로
            if str(node) in 역정보
            and 역정보[str(node)]["lat"] is not None
            and 역정보[str(node)]["lng"] is not None
        ]

    else:

        중심좌표 = [
            info
            for info in 역정보.values()
            if info["lat"] is not None
            and info["lng"] is not None
        ]

    if 중심좌표:

        중심위도 = sum(
            x["lat"]
            for x in 중심좌표
        ) / len(중심좌표)

        중심경도 = sum(
            x["lng"]
            for x in 중심좌표
        ) / len(중심좌표)

    else:

        중심위도 = 37.5665
        중심경도 = 126.9780

    zoom = (
        10.2
        if 선택노선 == "전체 노선"
        else 11.2
    )

    if 강조경로 and len(강조경로) > 15:
        zoom = 9.8

    deck = pdk.Deck(

        layers=layers,

        initial_view_state=pdk.ViewState(
            latitude=중심위도,
            longitude=중심경도,
            zoom=zoom,
            pitch=0,
            bearing=0
        ),

        map_style="light",

        tooltip={
            "html": "<b>{name}</b><br/>{line}",
            "style": {
                "backgroundColor": "#123B72",
                "color": "white"
            }
        }
    )

    st.pydeck_chart(
        deck,
        use_container_width=True,
        height=560
    )


# ==================================================
# 10. 최적 경로 계산
# ==================================================

def 경로찾기(
    출발노드들,
    도착노드들,
    그래프,
    기준
):

    거리표 = {}
    이전역표 = {}
    대기열 = []

    for node in 출발노드들:

        거리표[node] = (0, 0)

        heapq.heappush(
            대기열,
            (0, 0, node)
        )

    목적지노드 = None

    while 대기열:

        비용1, 비용2, 현재 = heapq.heappop(
            대기열
        )

        if 거리표.get(현재) != (비용1, 비용2):
            continue

        if 현재 in 도착노드들:

            목적지노드 = 현재
            break

        for 다음, 추가이동, 추가환승 in sorted(
            그래프[현재]
        ):

            if 기준 == "최소 환승":

                새비용 = (
                    비용1 + 추가환승,
                    비용2 + 추가이동
                )

            else:

                새비용 = (
                    비용1 + 추가이동,
                    비용2 + 추가환승
                )

            기존비용 = 거리표.get(
                다음,
                (
                    float("inf"),
                    float("inf")
                )
            )

            if 새비용 < 기존비용:

                거리표[다음] = 새비용
                이전역표[다음] = 현재

                heapq.heappush(
                    대기열,
                    (
                        새비용[0],
                        새비용[1],
                        다음
                    )
                )

    if 목적지노드 is None:
        return None

    경로 = []
    현재 = 목적지노드

    while True:

        경로.append(현재)

        if 현재 not in 이전역표:
            break

        현재 = 이전역표[현재]

    경로.reverse()

    return 경로


# ==================================================
# 11. 경로 노선 구분
# ==================================================

def 구간나누기(경로, 역정보):

    구간들 = []

    for node in 경로:

        노선 = 역정보[node]["line"]

        if (
            not 구간들
            or 구간들[-1]["line"] != 노선
        ):

            구간들.append({

                "line": 노선,
                "nodes": [node]

            })

        else:

            구간들[-1]["nodes"].append(
                node
            )

    return 구간들


# ==================================================
# 12. 앱 제목 및 데이터 불러오기
# ==================================================

st.title("🚇 BLUE ROUTE")
st.caption("전국 역 검색과 지하철 길찾기")

try:

    with st.spinner(
        "지하철 정보를 불러오는 중..."
    ):

        (
            역정보,
            그래프,
            역검색표,
            노선도구간
        ) = 데이터불러오기()

except Exception as e:

    st.error(
        "지하철 정보를 불러오지 못했어."
    )

    st.caption(str(e))

    st.stop()


# ==================================================
# 13. 전국 역 목록
# ==================================================

if "전국역자료" not in st.session_state:
    st.session_state["전국역자료"] = None


if "전국역오류" not in st.session_state:
    st.session_state["전국역오류"] = ""


with st.expander(
    "🇰🇷 전국 지하철 역 이름 검색",
    expanded=True
):

    st.subheader("전국 도시·광역철도 역 찾기")

    st.write(
        "역 이름을 몰라도 지역이나 노선을 선택해서 "
        "전국의 역을 찾아볼 수 있어."
    )

    st.link_button(
        "📥 국가철도공단 전국 역 목록 다운로드",
        KRIC_URL,
        use_container_width=True
    )

    st.caption(
        "공식 자료를 내려받은 후 아래에 업로드해 줘."
    )

    업로드파일 = st.file_uploader(
        "전국 역사정보 XLSX 또는 CSV 파일",
        type=["xlsx", "xls", "csv"],
        key="전국역파일"
    )

    if 업로드파일 is not None:

        try:

            파일내용 = 업로드파일.getvalue()

            if 업로드파일.name.lower().endswith(".csv"):

                try:

                    원본 = pd.read_csv(
                        BytesIO(파일내용),
                        dtype=str,
                        encoding="utf-8-sig"
                    )

                except UnicodeDecodeError:

                    원본 = pd.read_csv(
                        BytesIO(파일내용),
                        dtype=str,
                        encoding="cp949"
                    )

            else:

                엑셀 = pd.ExcelFile(
                    BytesIO(파일내용)
                )

                시트 = st.selectbox(
                    "자료 시트 선택",
                    엑셀.sheet_names,
                    key="전국역시트"
                )

                원본 = pd.read_excel(
                    BytesIO(파일내용),
                    sheet_name=시트,
                    dtype=str
                )

            새전국자료 = 전국역자료가공(
                원본
            )

            st.session_state["전국역자료"] = (
                새전국자료
            )

            st.session_state["전국역오류"] = ""

        except Exception as e:

            st.session_state["전국역오류"] = str(e)

    if st.session_state["전국역오류"]:

        st.error(
            st.session_state["전국역오류"]
        )

    전국역자료 = st.session_state["전국역자료"]

    if 전국역자료 is None:

        st.info(
            "공식 파일을 올리기 전에는 기존 길찾기 "
            "데이터에 포함된 역만 목록으로 보여줘."
        )

        전국역자료 = pd.DataFrame([

            {
                "지역": "기존 경로 데이터",
                "운영기관": "기존 데이터",
                "노선": info["line"],
                "역명": info["name"]
            }

            for info in 역정보.values()

        ]).drop_duplicates()

    st.divider()

    # 지역 필터
    지역목록 = sorted(
        전국역자료["지역"].dropna().unique().tolist()
    )

    지역선택 = st.selectbox(
        "📍 지역",
        ["전체 지역"] + 지역목록,
        key="전국지역선택"
    )

    # 운영기관 필터
    기관목록 = sorted(
        전국역자료["운영기관"].dropna().unique().tolist()
    )

    기관선택 = st.selectbox(
        "🏢 운영기관",
        ["전체 기관"] + 기관목록,
        key="전국기관선택"
    )

    # 노선 필터
    노선목록 = sorted(
        전국역자료["노선"].dropna().unique().tolist()
    )

    노선선택 = st.selectbox(
        "🚇 노선",
        ["전체 노선"] + 노선목록,
        key="전국노선선택"
    )

    # 역 이름 검색
    역이름검색 = st.text_input(
        "🔎 역 이름 검색",
        placeholder="예: 강남, 부산대, 대전...",
        key="전국역검색어"
    )

    검색결과 = 전국역자료.copy()

    if 지역선택 != "전체 지역":

        검색결과 = 검색결과[
            검색결과["지역"] == 지역선택
        ]

    if 기관선택 != "전체 기관":

        검색결과 = 검색결과[
            검색결과["운영기관"] == 기관선택
        ]

    if 노선선택 != "전체 노선":

        검색결과 = 검색결과[
            검색결과["노선"] == 노선선택
        ]

    if 역이름검색.strip():

        검색결과 = 검색결과[
            검색결과["역명"].astype(str).str.contains(
                역이름검색.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    st.metric(
        "검색된 역 항목",
        f"{len(검색결과):,}개"
    )

    st.dataframe(
        검색결과[
            ["지역", "운영기관", "노선", "역명"]
        ],
        use_container_width=True,
        height=330,
        hide_index=True
    )

    st.download_button(
        "📥 검색된 역 목록 CSV 저장",
        data=검색결과.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="전국_지하철역목록.csv",
        mime="text/csv",
        use_container_width=True
    )

    # 역 선택
    역선택지도 = {}

    for _, row in 검색결과.iterrows():

        이름 = str(row["역명"])

        표시이름 = (
            이름
            if 이름.endswith("역")
            else 이름 + "역"
        )

        표시 = (
            f"{표시이름} | "
            f"{row['노선']} | "
            f"{row['지역']}"
        )

        역선택지도[표시] = 이름

    역선택목록 = (
        ["선택 안 함"]
        + list(역선택지도.keys())
    )

    st.divider()

    선택역 = st.selectbox(
        "사용할 역 선택",
        역선택목록,
        key="전국역적용선택"
    )

    적용위치 = st.radio(
        "어느 입력칸에 넣을까?",
        ["출발역", "도착역"],
        horizontal=True,
        key="역적용위치"
    )

    if st.button(
        "선택한 역 적용하기",
        use_container_width=True
    ):

        if 선택역 != "선택 안 함":

            if 적용위치 == "출발역":

                st.session_state["출발역입력"] = (
                    역선택지도[선택역]
                )

            else:

                st.session_state["도착역입력"] = (
                    역선택지도[선택역]
                )

            st.success(
                "역을 입력했어. 아래에서 경로를 검색해 봐."
            )

            st.rerun()


# ==================================================
# 14. 최근 검색 및 편의 기능
# ==================================================

if "출발역입력" not in st.session_state:
    st.session_state["출발역입력"] = ""

if "도착역입력" not in st.session_state:
    st.session_state["도착역입력"] = ""

if "최근검색경로" not in st.session_state:
    st.session_state["최근검색경로"] = []


with st.expander("🕘 최근 검색 경로"):

    최근기록 = st.session_state["최근검색경로"]

    if 최근기록:

        for i, 기록 in enumerate(최근기록):

            st.write(
                f"**{기록['출발']} → {기록['도착']}**"
            )

            if st.button(
                "이 경로 다시 불러오기",
                key=f"최근검색_{i}"
            ):

                st.session_state["출발역입력"] = 기록["출발"]

                st.session_state["도착역입력"] = 기록["도착"]

                st.session_state["경로기준"] = 기록["기준"]

                st.rerun()

    else:

        st.caption(
            "아직 검색한 경로가 없어."
        )


# 출발역·도착역 교환
if st.button(
    "↔️ 출발역과 도착역 바꾸기",
    use_container_width=True
):

    임시 = st.session_state["출발역입력"]

    st.session_state["출발역입력"] = (
        st.session_state["도착역입력"]
    )

    st.session_state["도착역입력"] = 임시

    st.rerun()


# ==================================================
# 15. 출발역과 도착역 입력
# ==================================================

with st.form("route_form"):

    st.subheader("어디로 이동할까요?")

    col1, col2 = st.columns(2)

    with col1:

        출발입력 = st.text_input(
            "🔵 출발역",
            placeholder="예: 강남역",
            key="출발역입력"
        )

    with col2:

        도착입력 = st.text_input(
            "🔹 도착역",
            placeholder="예: 홍대입구역",
            key="도착역입력"
        )

    기준 = st.radio(
        "경로 기준",
        ["최소 환승", "최단 역 수"],
        horizontal=True,
        key="경로기준"
    )

    검색버튼 = st.form_submit_button(
        "🔎 경로 찾기",
        use_container_width=True
    )


# ==================================================
# 16. 전체 노선도
# ==================================================

with st.expander(
    "🗺️ 현재 경로 데이터의 지하철 노선도",
    expanded=False
):

    노선목록 = sorted({
        구간["line"]
        for 구간 in 노선도구간
    })

    선택노선 = st.selectbox(
        "확인할 노선",
        ["전체 노선"] + 노선목록,
        key="노선도선택"
    )

    노선도그리기(
        역정보,
        노선도구간,
        선택노선=선택노선
    )

    st.caption(
        "마우스로 이동하고 휠로 확대하거나 축소할 수 있어."
    )

    st.link_button(
        "서울교통공사 공식 사이버스테이션",
        공식사이버스테이션,
        use_container_width=True
    )


# ==================================================
# 17. 경로 결과
# ==================================================

if 검색버튼:

    출발키 = 역이름키(
        출발입력
    )

    도착키 = 역이름키(
        도착입력
    )

    if (
        not 출발입력.strip()
        or not 도착입력.strip()
    ):

        st.warning(
            "출발역과 도착역을 모두 입력해 줘."
        )

    elif 출발키 == 도착키:

        st.info(
            "출발역과 도착역이 같아."
        )

    elif 출발키 not in 역검색표:

        st.error(
            f"'{출발입력}' 역은 현재 경로 계산 데이터에 없어."
        )

        st.caption(
            "전국 역 목록에 표시된다고 해서 "
            "모든 지역의 경로 계산이 가능한 것은 아니야."
        )

    elif 도착키 not in 역검색표:

        st.error(
            f"'{도착입력}' 역은 현재 경로 계산 데이터에 없어."
        )

        st.caption(
            "전국 역 목록에 표시된다고 해서 "
            "모든 지역의 경로 계산이 가능한 것은 아니야."
        )

    else:

        경로 = 경로찾기(
            역검색표[출발키],
            set(역검색표[도착키]),
            그래프,
            기준
        )

        if not 경로:

            st.error(
                "연결된 경로를 찾지 못했어."
            )

        else:

            # 최근 검색 기록 저장
            새기록 = {
                "출발": 출발입력.strip(),
                "도착": 도착입력.strip(),
                "기준": 기준
            }

            최근기록 = [
                기록
                for 기록 in st.session_state["최근검색경로"]
                if not (
                    기록["출발"] == 새기록["출발"]
                    and 기록["도착"] == 새기록["도착"]
                )
            ]

            최근기록.insert(
                0,
                새기록
            )

            st.session_state["최근검색경로"] = (
                최근기록[:5]
            )

            구간들 = 구간나누기(
                경로,
                역정보
            )

            총이동역수 = sum(
                len(구간["nodes"]) - 1
                for 구간 in 구간들
            )

            총환승횟수 = sum(
                역정보[a]["line"] != 역정보[b]["line"]
                for a, b in zip(
                    경로,
                    경로[1:]
                )
            )

            # ------------------------------
            # 경로 요약
            # ------------------------------

            st.divider()

            st.subheader("🧭 이동 경로")

            st.markdown(
                f"## {역이름표시(경로[0], 역정보)} → "
                f"{역이름표시(경로[-1], 역정보)}"
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "이동 역 수",
                f"{총이동역수}개"
            )

            c2.metric(
                "환승 횟수",
                f"{총환승횟수}회"
            )

            c3.metric(
                "이용 노선",
                f"{len(구간들)}개"
            )

            st.divider()

            음성문장 = [
                f"{역이름표시(경로[0], 역정보)}에서 출발합니다."
            ]

            # ------------------------------
            # 노선별 이동 경로
            # ------------------------------

            for i, 구간 in enumerate(구간들):

                노선 = 구간["line"]
                역목록 = 구간["nodes"]

                첫역 = 역이름표시(
                    역목록[0],
                    역정보
                )

                마지막역 = 역이름표시(
                    역목록[-1],
                    역정보
                )

                with st.container(border=True):

                    st.markdown(
                        f"### 🔵 {노선}"
                    )

                    st.markdown(
                        f"**{첫역} → {마지막역}**"
                    )

                    st.caption(
                        f"이 구간 이동 역 수: "
                        f"{max(0, len(역목록) - 1)}개"
                    )

                    st.write("**정차역**")

                    st.write(
                        " → ".join(
                            역이름표시(
                                node,
                                역정보
                            )
                            for node in 역목록
                        )
                    )

                음성문장.append(
                    f"{노선}을 타고 "
                    f"{마지막역}까지 이동하세요."
                )

                if i < len(구간들) - 1:

                    다음노선 = 구간들[i + 1]["line"]

                    st.info(
                        f"🔄 {마지막역}에서 "
                        f"{다음노선}으로 환승하세요."
                    )

                    음성문장.append(
                        f"{마지막역}에서 "
                        f"{다음노선}으로 환승하세요."
                    )

            음성문장.append(
                f"{역이름표시(경로[-1], 역정보)}에 도착했습니다."
            )

            # ------------------------------
            # 전체 이동 순서
            # ------------------------------

            st.divider()

            st.subheader("📍 전체 이동 순서")

            전체역목록 = []

            for node in 경로:

                이름 = 역이름표시(
                    node,
                    역정보
                )

                if 전체역목록:

                    if (
                        역이름키(전체역목록[-1])
                        == 역이름키(이름)
                    ):
                        continue

                전체역목록.append(
                    이름
                )

            with st.container(border=True):

                for 번호, 이름 in enumerate(
                    전체역목록,
                    start=1
                ):

                    st.markdown(
                        f"**{번호}. {이름}**"
                    )

            # ------------------------------
            # 내 이동 지도
            # ------------------------------

            st.divider()

            st.subheader(
                "📍 지도에서 내 이동 경로 보기"
            )

            노선도그리기(
                역정보,
                노선도구간,
                선택노선="전체 노선",
                강조경로=경로
            )

            st.caption(
                "빨간 선이 검색한 이동 경로야."
            )

            # ------------------------------
            # 네이버 지도
            # ------------------------------

            st.divider()

            st.subheader("🗺️ 네이버 지도")

            네이버URL = 네이버지도경로URL(
                경로[0],
                경로[-1],
                역정보
            )

            if 네이버URL:

                st.link_button(
                    "🗺️ 네이버 지도에서 확대해서 보기",
                    네이버URL,
                    use_container_width=True
                )

            else:

                st.warning(
                    "역 좌표를 확인할 수 없어."
                )

            # ------------------------------
            # 음성 안내
            # ------------------------------

            st.divider()

            st.subheader("🔊 음성 안내")

            음성텍스트 = " ".join(
                음성문장
            )

            음성문장JS = json.dumps(
                음성텍스트,
                ensure_ascii=False
            )

            components.html(
                f"""
                <div style="
                    display:flex;
                    gap:10px;
                    width:100%;
                ">

                    <button id="speakBtn"
                        style="
                            flex:1;
                            padding:15px;
                            border:none;
                            border-radius:12px;
                            background:linear-gradient(
                                90deg,#1D4ED8,#0284C7
                            );
                            color:white;
                            font-size:15px;
                            font-weight:800;
                            cursor:pointer;
                        ">
                        🔊 음성 안내 듣기
                    </button>

                    <button id="stopBtn"
                        style="
                            width:110px;
                            padding:15px;
                            border:1px solid #BFDBFE;
                            border-radius:12px;
                            background:white;
                            color:#1E3A8A;
                            font-size:15px;
                            font-weight:800;
                            cursor:pointer;
                        ">
                        ■ 정지
                    </button>

                </div>

                <div id="voiceStatus"
                    style="
                        margin-top:8px;
                        text-align:center;
                        color:#475569;
                        font-size:13px;
                    ">
                    버튼을 누르면 음성 안내가 시작돼.
                </div>

                <script>

                    const routeText = {음성문장JS};

                    const speakBtn =
                        document.getElementById("speakBtn");

                    const stopBtn =
                        document.getElementById("stopBtn");

                    const voiceStatus =
                        document.getElementById("voiceStatus");

                    let chunks = [];
                    let currentChunk = 0;

                    function makeChunks(text) {{

                        return text.match(
                            /[^.!?。]+[.!?。]?/g
                        )
                        ?.map(s => s.trim())
                        .filter(Boolean) || [text];

                    }}

                    function getKoreanVoice() {{

                        const voices =
                            window.speechSynthesis.getVoices();

                        return (
                            voices.find(v =>
                                v.lang &&
                                v.lang.toLowerCase() === "ko-kr"
                            ) ||

                            voices.find(v =>
                                v.lang &&
                                v.lang.toLowerCase().startsWith("ko")
                            ) ||

                            null
                        );

                    }}

                    function speakNext() {{

                        if (currentChunk >= chunks.length) {{

                            voiceStatus.textContent =
                                "음성 안내가 끝났어.";

                            return;
                        }}

                        const speech =
                            new SpeechSynthesisUtterance(
                                chunks[currentChunk]
                            );

                        const voice =
                            getKoreanVoice();

                        if (voice) {{
                            speech.voice = voice;
                        }}

                        speech.lang = "ko-KR";
                        speech.rate = 0.88;
                        speech.pitch = 1.0;
                        speech.volume = 1.0;

                        speech.onstart = function() {{

                            voiceStatus.textContent =
                                "음성 안내 중... " +
                                (currentChunk + 1) +
                                " / " +
                                chunks.length;

                        }};

                        speech.onend = function() {{

                            currentChunk++;
                            speakNext();

                        }};

                        speech.onerror = function() {{

                            voiceStatus.textContent =
                                "음성 재생에 실패했어. 다시 눌러줘.";

                        }};

                        window.speechSynthesis.speak(
                            speech
                        );

                    }}

                    speakBtn.onclick = function() {{

                        if (
                            !("speechSynthesis" in window)
                        ) {{

                            voiceStatus.textContent =
                                "현재 브라우저에서 음성 기능을 지원하지 않아.";

                            return;
                        }}

                        window.speechSynthesis.cancel();

                        window.speechSynthesis.getVoices();

                        chunks = makeChunks(routeText);

                        currentChunk = 0;

                        setTimeout(function() {{

                            speakNext();

                        }}, 150);

                    }};

                    stopBtn.onclick = function(){{

                        if (
                            "speechSynthesis" in window
                        ) {{

                            window.speechSynthesis.cancel();

                        }}

                        currentChunk = chunks.length;

                        voiceStatus.textContent =
                            "음성 안내를 정지했어.";

                    }};

                    if (
                        "speechSynthesis" in window
                    ) {{

                        window.speechSynthesis.onvoiceschanged =
                            function(){{

                                window.speechSynthesis.getVoices();

                            }};

                        window.speechSynthesis.getVoices();

                    }}

                </script>
                """,
                height=125
            )


else:

    st.info(
        "출발역과 도착역을 입력한 다음 "
        "경로 찾기를 눌러 줘."
    )
