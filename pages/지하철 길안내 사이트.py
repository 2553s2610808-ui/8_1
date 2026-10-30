
import streamlit as st
import pandas as pd
import requests
import heapq
import re
import json
import math
import difflib
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
# 2. 디자인
# ==================================================

st.markdown("""
<style>

.stApp {
    background: #F1F7FF;
    color: #172554;
}

.block-container {
    max-width: 1050px;
    padding-top: 30px;
    padding-bottom: 50px;
}

h1, h2, h3 {
    color: #123B72;
}

div[data-testid="stTextInput"] input {
    border: 1px solid #BFDBFE;
    border-radius: 12px;
    min-height: 55px;
    background: white;
    color: #172554;
    font-size: 18px;
}

div[data-testid="stButton"] button {
    border-radius: 12px;
    min-height: 45px;
}

div[data-testid="stFormSubmitButton"] button {
    background: #1D4ED8;
    color: white;
    border-radius: 12px;
    min-height: 55px;
    font-size: 18px;
    font-weight: 800;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #BFDBFE;
    border-radius: 15px;
    padding: 14px;
}

hr {
    border-color: #DBEAFE;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. 노선 색상
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

    if 이름.endswith("역"):
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
# 5. 역 사이 거리
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

    값 = min(1, max(0, 값))

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
        math.tan((90 + lat) * math.pi / 360)
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
        출발["lat"],
        출발["lng"]
    )

    dx, dy = 네이버지도용좌표(
        도착["lat"],
        도착["lng"]
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
# 7. 지하철 데이터 불러오기
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

        node = row.get("station_id", "").strip()
        line = row.get("line", "").strip()
        name = row.get("name", "").strip()
        code = row.get("station_cd", "").strip()

        if not node or not line or not name:
            continue

        try:

            lat = float(row.get("lat", ""))
            lng = float(row.get("lng", ""))

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

    # 역 사이 연결
    for row in 구간자료.to_dict("records"):

        line = row.get("line", "").strip()

        code_a = row.get(
            "up_station_code", ""
        ).strip()

        code_b = row.get(
            "down_station_code", ""
        ).strip()

        name_a = row.get(
            "up_station_name", ""
        ).strip()

        name_b = row.get(
            "down_station_name", ""
        ).strip()

        a = 역코드표.get((line, code_a))
        b = 역코드표.get((line, code_b))

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

            연결(a, b)

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

        key = 역이름키(info["name"])

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
# 8. 전국 역 목록 처리
# ==================================================

def 컬럼찾기(df, 후보):

    columns = {
        re.sub(r"[\s_\-]", "", str(c)).lower(): c
        for c in df.columns
    }

    for name in 후보:

        key = re.sub(
            r"[\s_\-]",
            "",
            name
        ).lower()

        if key in columns:
            return columns[key]

    return None


def 전국역자료가공(원본):

    원본 = 원본.copy()

    원본.columns = [
        str(c).strip()
        for c in 원본.columns
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
            "철도운영기관"
        ]
    )

    지역컬럼 = 컬럼찾기(
        원본,
        [
            "권역명",
            "권역",
            "지역명",
            "지역",
            "시도명"
        ]
    )

    if not 역명컬럼:

        raise ValueError(
            "역명 열을 찾지 못했어. "
            "공식 전국 역사정보 파일인지 확인해 줘."
        )

    권역코드표 = {
        "01": "수도권",
        "02": "부산권",
        "03": "대구권",
        "04": "광주권",
        "05": "대전권"
    }

    def 값읽기(row, column):

        if not column:
            return ""

        value = row.get(column, "")

        if pd.isna(value):
            return ""

        return str(value).strip()

    def 지역분류(region, operator, line):

        if region:

            if region in 권역코드표:
                return 권역코드표[region]

            for keyword, result in [
                ("서울", "수도권"),
                ("경기", "수도권"),
                ("인천", "수도권"),
                ("수도권", "수도권"),
                ("부산", "부산권"),
                ("울산", "부산권"),
                ("대구", "대구권"),
                ("광주", "광주권"),
                ("대전", "대전권")
            ]:

                if keyword in region:
                    return result

            return region

        text = operator + " " + line

        for region_name, keywords in {
            "수도권": [
                "서울교통공사",
                "인천교통공사",
                "수도권",
                "신분당선",
                "경의중앙선",
                "수인분당선",
                "경춘선",
                "서해선"
            ],
            "부산권": [
                "부산교통공사",
                "부산김해경전철",
                "부산"
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
        }.items():

            if any(k in text for k in keywords):
                return region_name

        return "지역 확인 필요"

    자료 = []

    for _, row in 원본.iterrows():

        name = 값읽기(row, 역명컬럼)

        if not name:
            continue

        line = 값읽기(row, 노선컬럼)
        operator = 값읽기(row, 기관컬럼)
        region = 값읽기(row, 지역컬럼)

        자료.append({

            "역명": name,
            "노선": line or "정보 없음",
            "지역": 지역분류(
                region,
                operator,
                line
            ),
            "운영기관": operator or "정보 없음"
        })

    결과 = pd.DataFrame(자료)

    if 결과.empty:
        raise ValueError("역 자료가 비어 있어.")

    return 결과.drop_duplicates().reset_index(drop=True)


# ==================================================
# 9. 역 검색 목록 만들기
# ==================================================

def 전체역목록만들기(역정보, 전국역자료, 역검색표):

    자료 = []

    # 기존 길찾기 데이터
    for node, info in 역정보.items():

        자료.append({

            "역명": info["name"],
            "노선": info["line"],
            "지역": "수도권",
            "경로가능": True

        })

    # 전국 자료
    if 전국역자료 is not None:

        for _, row in 전국역자료.iterrows():

            이름 = str(row["역명"])

            자료.append({

                "역명": 이름,
                "노선": str(row["노선"]),
                "지역": str(row["지역"]),
                "경로가능": (
                    역이름키(이름) in 역검색표
                )

            })

    df = pd.DataFrame(자료)

    return df.drop_duplicates(
        subset=["역명", "노선", "지역"]
    )


# ==================================================
# 10. 역 이름 자동완성
# ==================================================

def 역자동완성후보(
    검색어,
    역목록,
    최대=7
):

    검색어 = re.sub(
        r"\s+",
        "",
        str(검색어)
    )

    if not 검색어:
        return []

    검색키 = 역이름키(검색어)

    후보들 = []

    # 이름 중복 통합
    그룹 = 역목록.groupby(
        ["역명", "지역"],
        dropna=False
    )

    for (이름, 지역), 정보 in 그룹:

        이름 = str(이름).strip()
        이름키 = 역이름키(이름)

        if not 이름키:
            continue

        if 검색키 == 이름키:
            순위 = 0

        elif 이름키.startswith(검색키):
            순위 = 1

        elif 검색키 in 이름키:
            순위 = 2

        else:

            점수 = difflib.SequenceMatcher(
                None,
                검색키,
                이름키
            ).ratio()

            if len(검색키) < 2 or 점수 < 0.45:
                continue

            순위 = 3

        점수 = difflib.SequenceMatcher(
            None,
            검색키,
            이름키
        ).ratio()

        노선목록 = sorted(
            set(
                정보["노선"].astype(str)
            )
        )

        경로가능 = bool(
            정보["경로가능"].any()
        )

        후보들.append({

            "역명": 이름,
            "지역": str(지역),
            "노선": ", ".join(노선목록),
            "경로가능": 경로가능,
            "순위": 순위,
            "점수": 점수

        })

    후보들.sort(
        key=lambda x: (
            x["순위"],
            -x["점수"],
            x["역명"]
        )
    )

    return 후보들[:최대]


# ==================================================
# 11. 자동완성 선택
# ==================================================

def 역선택저장(
    위치,
    이름,
    지역,
    경로가능
):

    key = (
        "출발역_검색어"
        if 위치 == "출발"
        else "도착역_검색어"
    )

    st.session_state[key] = 이름

    st.session_state[f"{위치}_선택정보"] = {
        "역명": 이름,
        "지역": 지역,
        "경로가능": 경로가능
    }

    st.session_state["마지막검색"] = None


def 수동입력변경(위치):

    st.session_state[f"{위치}_선택정보"] = None
    st.session_state["마지막검색"] = None


def 출발도착바꾸기():

    출발 = st.session_state.get(
        "출발역_검색어",
        ""
    )

    도착 = st.session_state.get(
        "도착역_검색어",
        ""
    )

    출발정보 = st.session_state.get(
        "출발_선택정보"
    )

    도착정보 = st.session_state.get(
        "도착_선택정보"
    )

    st.session_state["출발역_검색어"] = 도착
    st.session_state["도착역_검색어"] = 출발

    st.session_state["출발_선택정보"] = 도착정보
    st.session_state["도착_선택정보"] = 출발정보

    st.session_state["마지막검색"] = None


def 최근경로불러오기(기록):

    st.session_state["출발역_검색어"] = 기록["출발"]
    st.session_state["도착역_검색어"] = 기록["도착"]

    st.session_state["출발_선택정보"] = None
    st.session_state["도착_선택정보"] = None

    st.session_state["검색기준"] = 기록["기준"]
    st.session_state["마지막검색"] = None


# ==================================================
# 12. 지도 그리기
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

        st.warning("표시할 노선 좌표가 없어.")
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

            "name": 역이름표시(node, 역정보),
            "line": info["line"]

        })

    layers = [

        pdk.Layer(
            "PathLayer",
            data=표시구간,
            get_path="path",
            get_color="color",
            get_width=4,
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

    if 강조경로:

        좌표 = []

        for node in 강조경로:

            info = 역정보.get(str(node))

            if (
                info
                and info["lat"] is not None
                and info["lng"] is not None
            ):

                좌표.append([
                    info["lng"],
                    info["lat"]
                ])

        if len(좌표) >= 2:

            layers.append(
                pdk.Layer(
                    "PathLayer",
                    data=[{"path": 좌표}],
                    get_path="path",
                    get_color=[239, 68, 68],
                    get_width=8,
                    width_min_pixels=4
                )
            )

    if 강조경로:

        중심 = [
            역정보[str(node)]
            for node in 강조경로
            if str(node) in 역정보
            and 역정보[str(node)]["lat"] is not None
            and 역정보[str(node)]["lng"] is not None
        ]

    else:

        중심 = [
            info for info in 역정보.values()
            if info["lat"] is not None
            and info["lng"] is not None
        ]

    if 중심:

        위도 = sum(x["lat"] for x in 중심) / len(중심)
        경도 = sum(x["lng"] for x in 중심) / len(중심)

    else:

        위도, 경도 = 37.5665, 126.9780

    zoom = (
        10
        if 선택노선 == "전체 노선"
        else 11
    )

    if 강조경로 and len(강조경로) > 15:
        zoom = 9.5

    deck = pdk.Deck(

        layers=layers,

        initial_view_state=pdk.ViewState(
            latitude=위도,
            longitude=경도,
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
        height=550
    )


# ==================================================
# 13. 경로 계산
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
# 14. 노선별 경로 정리
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

            구간들[-1]["nodes"].append(node)

    return 구간들


# ==================================================
# 15. 시작 및 지하철 데이터
# ==================================================

st.title("🚇 BLUE ROUTE")

st.caption(
    "역 이름을 입력하면 비슷한 역을 자동으로 찾아줘."
)

try:

    with st.spinner("지하철 정보를 불러오는 중..."):

        (
            역정보,
            그래프,
            역검색표,
            노선도구간
        ) = 데이터불러오기()

except Exception as e:

    st.error("지하철 데이터를 불러오지 못했어.")
    st.caption(str(e))
    st.stop()


# ==================================================
# 16. 전국 역 자료 업로드
# ==================================================

if "전국역자료" not in st.session_state:
    st.session_state["전국역자료"] = None

with st.expander("전국 역 목록 추가하기 (선택 사항)"):

    st.write(
        "다른 지역 역까지 검색하려면 "
        "전국 도시광역철도 역사정보 파일을 올려 줘."
    )

    st.link_button(
        "국가철도공단 역 자료",
        KRIC_URL,
        use_container_width=True
    )

    업로드파일 = st.file_uploader(
        "전국 역 목록 파일",
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

                원본 = pd.read_excel(
                    BytesIO(파일내용),
                    dtype=str
                )

            st.session_state["전국역자료"] = (
                전국역자료가공(원본)
            )

            st.success("전국 역 목록을 불러왔어.")

        except Exception as e:

            st.error(
                f"파일을 읽지 못했어: {e}"
            )


# ==================================================
# 17. 전체 역 목록 만들기
# ==================================================

전체역목록 = 전체역목록만들기(
    역정보,
    st.session_state["전국역자료"],
    역검색표
)


# ==================================================
# 18. 최근 검색 기록
# ==================================================

if "최근검색경로" not in st.session_state:
    st.session_state["최근검색경로"] = []

if "마지막검색" not in st.session_state:
    st.session_state["마지막검색"] = None

if "출발_선택정보" not in st.session_state:
    st.session_state["출발_선택정보"] = None

if "도착_선택정보" not in st.session_state:
    st.session_state["도착_선택정보"] = None

if "출발역_검색어" not in st.session_state:
    st.session_state["출발역_검색어"] = ""

if "도착역_검색어" not in st.session_state:
    st.session_state["도착역_검색어"] = ""

if "검색기준" not in st.session_state:
    st.session_state["검색기준"] = "최소 환승"


with st.expander("🕘 최근 검색 경로"):

    최근기록 = st.session_state["최근검색경로"]

    if 최근기록:

        for i, 기록 in enumerate(최근기록):

            st.write(
                f"**{기록['출발']} → {기록['도착']}**"
            )

            st.button(
                "다시 검색",
                key=f"최근경로_{i}",
                on_click=최근경로불러오기,
                args=(기록,)
            )

    else:

        st.caption("아직 검색한 기록이 없어.")


# ==================================================
# 19. 출발역 자동완성
# ==================================================

st.divider()

st.subheader("🔵 출발역")

st.caption(
    "역 이름을 몇 글자만 입력해 봐."
)

st.text_input(
    "출발역 검색",
    key="출발역_검색어",
    placeholder="예: 강남, 홍대, 서울...",
    on_change=수동입력변경,
    args=("출발",)
)

출발검색어 = st.session_state["출발역_검색어"]

if 출발검색어.strip():

    출발후보 = 역자동완성후보(
        출발검색어,
        전체역목록
    )

    if 출발후보:

        st.caption("아래에서 출발할 역을 선택해 줘.")

        for i, 후보 in enumerate(출발후보):

            표시 = (
                f"📍 {후보['역명']}  |  "
                f"{후보['노선']}  |  {후보['지역']}"
            )

            if not 후보["경로가능"]:
                표시 += " · 경로 데이터 없음"

            st.button(
                표시,
                key=f"출발후보_{i}",
                use_container_width=True,
                on_click=역선택저장,
                args=(
                    "출발",
                    후보["역명"],
                    후보["지역"],
                    후보["경로가능"]
                )
            )

    else:

        st.info(
            "비슷한 역을 찾지 못했어. "
            "다른 글자를 입력해 줘."
        )

if st.session_state["출발_선택정보"]:

    st.success(
        "선택한 출발역: "
        + st.session_state["출발_선택정보"]["역명"]
    )


# ==================================================
# 20. 출발역과 도착역 바꾸기
# ==================================================

st.button(
    "↕️ 출발역과 도착역 바꾸기",
    use_container_width=True,
    on_click=출발도착바꾸기
)


# ==================================================
# 21. 도착역 자동완성
# ==================================================

st.subheader("🟢 도착역")

st.caption(
    "목적지 역 이름을 입력해 줘."
)

st.text_input(
    "도착역 검색",
    key="도착역_검색어",
    placeholder="예: 잠실, 부산, 대전...",
    on_change=수동입력변경,
    args=("도착",)
)

도착검색어 = st.session_state["도착역_검색어"]

if 도착검색어.strip():

    도착후보 = 역자동완성후보(
        도착검색어,
        전체역목록
    )

    if 도착후보:

        st.caption("아래에서 도착할 역을 선택해 줘.")

        for i, 후보 in enumerate(도착후보):

            표시 = (
                f"📍 {후보['역명']}  |  "
                f"{후보['노선']}  |  {후보['지역']}"
            )

            if not 후보["경로가능"]:
                표시 += " · 경로 데이터 없음"

            st.button(
                표시,
                key=f"도착후보_{i}",
                use_container_width=True,
                on_click=역선택저장,
                args=(
                    "도착",
                    후보["역명"],
                    후보["지역"],
                    후보["경로가능"]
                )
            )

    else:

        st.info(
            "비슷한 역을 찾지 못했어. "
            "다른 글자를 입력해 줘."
        )

if st.session_state["도착_선택정보"]:

    st.success(
        "선택한 도착역: "
        + st.session_state["도착_선택정보"]["역명"]
    )


# ==================================================
# 22. 검색 기준
# ==================================================

st.divider()

st.subheader("🧭 이동 방법")

기준선택 = st.radio(
    "어떤 경로로 갈까요?",
    [
        "환승 적게 (추천)",
        "이동 역 적게"
    ],
    horizontal=True,
    key="검색기준표시"
)

기준 = (
    "최소 환승"
    if 기준선택 == "환승 적게 (추천)"
    else "최단 역 수"
)

# 라디오 값과 경로 계산 값 동기화
st.session_state["검색기준"] = 기준


# ==================================================
# 23. 길찾기 시작
# ==================================================

if st.button(
    "🔎 길찾기 시작",
    type="primary",
    use_container_width=True
):

    출발입력 = st.session_state["출발역_검색어"].strip()
    도착입력 = st.session_state["도착역_검색어"].strip()

    if not 출발입력 or not 도착입력:

        st.warning(
            "출발역과 도착역을 모두 입력해 줘."
        )

        st.session_state["마지막검색"] = None

    else:

        출발정보 = st.session_state["출발_선택정보"]
        도착정보 = st.session_state["도착_선택정보"]

        출발키 = 역이름키(출발입력)
        도착키 = 역이름키(도착입력)

        # 전국 목록에서 선택한 경로 미지원 역 확인
        if (
            출발정보
            and 출발정보["역명"] == 출발입력
            and not 출발정보["경로가능"]
        ):

            st.warning(
                "선택한 출발역은 역 목록에는 있지만 "
                "현재 경로 계산 데이터에는 없어."
            )

            st.session_state["마지막검색"] = None

        elif (
            도착정보
            and 도착정보["역명"] == 도착입력
            and not 도착정보["경로가능"]
        ):

            st.warning(
                "선택한 도착역은 역 목록에는 있지만 "
                "현재 경로 계산 데이터에는 없어."
            )

            st.session_state["마지막검색"] = None

        elif 출발키 == 도착키:

            st.warning(
                "출발역과 도착역이 같아."
            )

            st.session_state["마지막검색"] = None

        elif 출발키 not in 역검색표:

            st.warning(
                "현재 경로 계산 자료에 출발역이 없어."
            )

            st.session_state["마지막검색"] = None

        elif 도착키 not in 역검색표:

            st.warning(
                "현재 경로 계산 자료에 도착역이 없어."
            )

            st.session_state["마지막검색"] = None

        else:

            st.session_state["마지막검색"] = {

                "출발": 출발입력,
                "도착": 도착입력,
                "기준": 기준

            }

            최근기록 = [
                기록
                for 기록 in st.session_state["최근검색경로"]
                if not (
                    기록["출발"] == 출발입력
                    and 기록["도착"] == 도착입력
                )
            ]

            최근기록.insert(
                0,
                {
                    "출발": 출발입력,
                    "도착": 도착입력,
                    "기준": 기준
                }
            )

            st.session_state["최근검색경로"] = (
                최근기록[:5]
            )

    st.rerun()


# ==================================================
# 24. 전체 노선도
# ==================================================

with st.expander("🗺️ 지하철 노선도 보기"):

    노선목록 = sorted({
        구간["line"]
        for 구간 in 노선도구간
    })

    선택노선 = st.selectbox(
        "노선 선택",
        ["전체 노선"] + 노선목록,
        key="지도노선선택"
    )

    노선도그리기(
        역정보,
        노선도구간,
        선택노선
    )

    st.link_button(
        "서울교통공사 공식 노선도",
        공식사이버스테이션,
        use_container_width=True
    )


# ==================================================
# 25. 경로 결과
# ==================================================

검색결과 = st.session_state["마지막검색"]

if 검색결과:

    출발입력 = 검색결과["출발"]
    도착입력 = 검색결과["도착"]
    기준 = 검색결과["기준"]

    출발키 = 역이름키(출발입력)
    도착키 = 역이름키(도착입력)

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

        # ------------------------------
        # 음성 안내 문장
        # ------------------------------

        음성문장 = [
            f"{역이름표시(경로[0], 역정보)}에서 출발합니다."
        ]

        # ------------------------------
        # 노선별 경로
        # ------------------------------

        st.divider()

        st.subheader("🚉 이용할 노선")

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
                    f"{len(역목록) - 1}개"
                )

                st.write(
                    "정차역"
                )

                st.write(
                    " → ".join(
                        역이름표시(node, 역정보)
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

            전체역목록.append(이름)

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

        st.subheader("📍 지도에서 경로 보기")

        노선도그리기(
            역정보,
            노선도구간,
            선택노선="전체 노선",
            강조경로=경로
        )

        st.caption(
            "빨간색 선이 검색한 이동 경로야."
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
                "🗺️ 네이버 지도에서 크게 보기",
                네이버URL,
                use_container_width=True
            )

        else:

            st.warning(
                "네이버 지도에 연결할 좌표를 확인하지 못했어."
            )

        # ------------------------------
        # 음성 안내
        # ------------------------------

        st.divider()

        st.subheader("🔊 음성 안내")

        음성문장JS = json.dumps(
            " ".join(음성문장),
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
                        padding:16px;
                        border:none;
                        border-radius:12px;
                        background:linear-gradient(
                            90deg,#1D4ED8,#0284C7
                        );
                        color:white;
                        font-size:17px;
                        font-weight:800;
                        cursor:pointer;
                    ">
                    🔊 안내 듣기
                </button>

                <button id="stopBtn"
                    style="
                        width:110px;
                        padding:16px;
                        border:1px solid #BFDBFE;
                        border-radius:12px;
                        background:white;
                        color:#1E3A8A;
                        font-size:16px;
                        font-weight:800;
                        cursor:pointer;
                    ">
                    ■ 정지
                </button>

            </div>

            <div id="voiceStatus"
                style="
                    margin-top:10px;
                    text-align:center;
                    color:#475569;
                    font-size:14px;
                ">
                안내 듣기를 누르면 음성이 시작돼.
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
                            "안내가 끝났어.";

                        return;
                    }}

                    const speech =
                        new SpeechSynthesisUtterance(
                            chunks[currentChunk]
                        );

                    const voice = getKoreanVoice();

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

                    speech.onend = function(){{

                        currentChunk++;
                        speakNext();

                    }};

                    speech.onerror = function(){{

                        voiceStatus.textContent =
                            "음성 재생에 실패했어. 다시 눌러 줘.";

                    }};

                    window.speechSynthesis.speak(speech);

                }}

                speakBtn.onclick = function(){{

                    if (!("speechSynthesis" in window)) {{

                        voiceStatus.textContent =
                            "이 브라우저는 음성 기능을 지원하지 않아.";

                        return;
                    }}

                    window.speechSynthesis.cancel();

                    window.speechSynthesis.getVoices();

                    chunks = makeChunks(routeText);
                    currentChunk = 0;

                    setTimeout(function(){{

                        speakNext();

                    }}, 150);

                }};

                stopBtn.onclick = function(){{

                    window.speechSynthesis.cancel();

                    currentChunk = chunks.length;

                    voiceStatus.textContent =
                        "음성 안내를 정지했어.";

                }};

                if ("speechSynthesis" in window) {{

                    window.speechSynthesis.onvoiceschanged =
                        function(){{

                            window.speechSynthesis.getVoices();

                        }};

                    window.speechSynthesis.getVoices();

                }}

            </script>
            """,
            height=130
        )
