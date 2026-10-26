import html
import json

import requests
import streamlit as st
import streamlit.components.v1 as components


# =========================================================
# 앱 기본 설정
# =========================================================

st.set_page_config(
    page_title="서울 길찾기",
    page_icon="🧭",
    layout="wide",
)


# =========================================================
# 외부 서비스 주소
# =========================================================

장소검색주소 = "https://nominatim.openstreetmap.org/search"
경로검색주소 = "https://router.project-osrm.org/route/v1/foot"

요청헤더 = {
    "User-Agent": "Seoul-WayFinder-Streamlit"
}


# =========================================================
# 화면 디자인
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #f5f7fb;
    }

    .상단 {
        background: linear-gradient(
            135deg,
            #4f46e5,
            #7c3aed
        );

        color: white;

        border-radius: 24px;

        padding: 30px;

        margin-bottom: 22px;

        box-shadow:
            0 12px 30px
            rgba(79, 70, 229, 0.18);
    }

    .상단 h1 {
        margin: 0 0 8px 0;
        font-size: 2.2rem;
    }

    .상단 p {
        margin: 0;
        opacity: 0.92;
        font-size: 1rem;
    }

    .카드 {
        background: white;

        border-radius: 20px;

        padding: 22px;

        border: 1px solid #e8eaf1;

        box-shadow:
            0 7px 22px
            rgba(20, 20, 50, 0.05);

        margin-bottom: 16px;
    }

    .경로카드 {
        border-left: 6px solid #6366f1;
    }

    .큰숫자 {
        font-size: 1.6rem;

        font-weight: 800;

        color: #4338ca;
    }

    .설명 {
        color: #6b7280;

        font-size: 0.9rem;
    }

    .단계 {
        display: flex;

        gap: 12px;

        padding: 13px 0;

        border-bottom:
            1px solid #eeeeF4;
    }

    .단계번호 {
        min-width: 30px;

        height: 30px;

        border-radius: 50%;

        background: #eef2ff;

        color: #4338ca;

        display: flex;

        align-items: center;

        justify-content: center;

        font-weight: 800;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 장소 찾기
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def 장소찾기(장소):

    장소 = 장소.strip()

    if not 장소:
        return None

    try:

        응답 = requests.get(
            장소검색주소,

            params={
                "q": f"{장소}, 대한민국",
                "format": "jsonv2",
                "limit": 1,
                "countrycodes": "kr",
            },

            headers=요청헤더,

            timeout=10,
        )

        응답.raise_for_status()

        결과 = 응답.json()

        if not 결과:
            return None

        정보 = 결과[0]

        return {
            "위도": float(정보["lat"]),
            "경도": float(정보["lon"]),
            "이름": 정보.get(
                "display_name",
                장소
            ),
        }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        IndexError,
    ):

        return None


# =========================================================
# 이동 경로 찾기
# =========================================================

@st.cache_data(
    ttl=300,
    show_spinner=False
)
def 이동경로찾기(
    출발위도,
    출발경도,
    도착위도,
    도착경도,
):

    주소 = (
        f"{경로검색주소}/"
        f"{출발경도},{출발위도};"
        f"{도착경도},{도착위도}"
    )

    try:

        응답 = requests.get(
            주소,

            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "true",
            },

            headers=요청헤더,

            timeout=15,
        )

        응답.raise_for_status()

        결과 = 응답.json()

        if 결과.get("code") != "Ok":
            return None

        if not 결과.get("routes"):
            return None

        경로 = 결과["routes"][0]

        return {
            "거리": 경로.get(
                "distance",
                0
            ),

            "시간": 경로.get(
                "duration",
                0
            ),

            "지도경로": 경로[
                "geometry"
            ]["coordinates"],

            "구간": 경로.get(
                "legs",
                []
            ),
        }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        IndexError,
    ):

        return None


# =========================================================
# 거리 표시
# =========================================================

def 거리표시(미터):

    if 미터 < 1000:

        return f"{round(미터)}m"

    return f"{미터 / 1000:.1f}km"


# =========================================================
# 시간 표시
# =========================================================

def 시간표시(초):

    분 = max(
        1,
        round(초 / 60)
    )

    if 분 < 60:

        return f"{분}분"

    시간 = 분 // 60

    나머지 = 분 % 60

    if 나머지 == 0:

        return f"{시간}시간"

    return (
        f"{시간}시간 "
        f"{나머지}분"
    )


# =========================================================
# 방향 한글화
# =========================================================

def 방향표시(
    방향,
    도로이름
):

    도로 = (
        도로이름.strip()
        if 도로이름
        else "도로"
    )

    방향표 = {

        "left":
            "왼쪽으로",

        "right":
            "오른쪽으로",

        "slight left":
            "왼쪽 방향으로",

        "slight right":
            "오른쪽 방향으로",

        "sharp left":
            "왼쪽으로 크게",

        "sharp right":
            "오른쪽으로 크게",

        "straight":
            "직진하여",

        "uturn":
            "유턴하여",
    }

    표시방향 = 방향표.get(
        방향,
        "이동하여"
    )

    return (
        f"{표시방향} "
        f"{도로}"
    )


# =========================================================
# 이동 안내 만들기
# =========================================================

def 이동안내만들기(경로):

    안내 = []

    for 구간 in 경로.get(
        "구간",
        []
    ):

        for 단계 in 구간.get(
            "steps",
            []
        ):

            이동방법 = 단계.get(
                "maneuver",
                {}
            )

            방향 = 이동방법.get(
                "modifier",
                "straight"
            )

            도로 = 단계.get(
                "name",
                ""
            )

            거리 = 단계.get(
                "distance",
                0
            )

            if 거리 < 15:
                continue

            안내.append(
                {
                    "내용":
                        방향표시(
                            방향,
                            도로
                        ),

                    "거리":
                        거리,
                }
            )

    return 안내[:12]


# =========================================================
# 음성 안내 문장 만들기
# =========================================================

def 음성문장만들기(
    출발지,
    도착지,
    경로,
    안내,
):

    문장 = []

    문장.append(
        f"{출발지}에서 "
        f"{도착지}까지 "
        f"안내를 시작합니다."
    )

    문장.append(
        f"총 거리는 "
        f"{거리표시(경로['거리'])}이고, "
        f"예상 시간은 "
        f"{시간표시(경로['시간'])}입니다."
    )

    for 번호, 단계 in enumerate(
        안내[:8],
        start=1
    ):

        문장.append(
            f"{번호}번째 안내입니다. "
            f"{단계['내용']}, "
            f"{거리표시(단계['거리'])} "
            f"이동하세요."
        )

    문장.append(
        "목적지에 도착하면 "
        "안내가 종료됩니다."
    )

    return " ".join(문장)


# =========================================================
# 지도 만들기
# =========================================================

def 지도만들기(
    출발지,
    도착지,
    경로,
):

    좌표 = 경로["지도경로"]

    지도좌표 = [
        [위도, 경도]
        for 경도, 위도 in 좌표
    ]

    지도좌표JSON = json.dumps(
        지도좌표,
        ensure_ascii=False
    )

    출발위도 = 출발지["위도"]
    출발경도 = 출발지["경도"]

    도착위도 = 도착지["위도"]
    도착경도 = 도착지["경도"]

    출발이름 = html.escape(
        출발지["이름"][:100]
    )

    도착이름 = html.escape(
        도착지["이름"][:100]
    )

    return f"""
    <!DOCTYPE html>

    <html lang="ko">

    <head>

    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width,
        initial-scale=1.0"
    >

    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    >

    <style>

    html,
    body,
    #map {{
        height: 100%;
        margin: 0;
    }}

    #map {{
        min-height: 540px;

        border-radius: 18px;

        overflow: hidden;
    }}

    </style>

    </head>

    <body>

    <div id="map"></div>

    <script
        src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
    </script>

    <script>

    const 출발지 = [
        {출발위도},
        {출발경도}
    ];

    const 도착지 = [
        {도착위도},
        {도착경도}
    ];

    const 경로 = {지도좌표JSON};


    const 지도 = L.map(
        "map"
    ).setView(
        출발지,
        14
    );


    L.tileLayer(
        "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
        {{

            maxZoom: 19,

            attribution:
                "&copy; OpenStreetMap 기여자"

        }}
    ).addTo(지도);


    // 출발지
    const 출발아이콘 =
        L.divIcon({{

            className: "",

            html:
                '<div style="' +
                'width:18px;' +
                'height:18px;' +
                'border-radius:50%;' +
                'background:#4f46e5;' +
                'border:4px solid white;' +
                'box-shadow:0 2px 8px #555;' +
                '"></div>',

            iconSize: [
                26,
                26
            ],

            iconAnchor: [
                13,
                13
            ]

        }});


    // 도착지
    const 도착아이콘 =
        L.divIcon({{

            className: "",

            html:
                '<div style="' +
                'width:18px;' +
                'height:18px;' +
                'border-radius:50%;' +
                'background:#ef4444;' +
                'border:4px solid white;' +
                'box-shadow:0 2px 8px #555;' +
                '"></div>',

            iconSize: [
                26,
                26
            ],

            iconAnchor: [
                13,
                13
            ]

        }});


    L.marker(
        출발지,
        {{
            icon: 출발아이콘
        }}
    )
    .addTo(지도)
    .bindPopup(
        "<b>출발지</b><br>"
        + `{출발이름}`
    );


    L.marker(
        도착지,
        {{
            icon: 도착아이콘
        }}
    )
    .addTo(지도)
    .bindPopup(
        "<b>도착지</b><br>"
        + `{도착이름}`
    );


    const 이동선 =
        L.polyline(
            경로,
            {{

                color: "#6366f1",

                weight: 6,

                opacity: 0.85

            }}
        ).addTo(지도);


    지도.fitBounds(
        이동선.getBounds(),
        {{
            padding: [
                30,
                30
            ]
        }}
    );

    </script>

    </body>

    </html>
    """


# =========================================================
# 상단
# =========================================================

st.markdown(
    """
    <div class="상단">

        <h1>
            🧭 서울 길찾기
        </h1>

        <p>
            출발지와 도착지를 입력하면
            지도와 음성으로 이동 방법을 알려드립니다.
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 입력 화면
# =========================================================

st.markdown(
    '<div class="카드">',
    unsafe_allow_html=True,
)


왼쪽, 오른쪽 = st.columns(2)


with 왼쪽:

    출발지입력 = st.text_input(
        "📍 출발지",

        placeholder=
        "예: 서울역"
    )


with 오른쪽:

    도착지입력 = st.text_input(
        "🏁 도착지",

        placeholder=
        "예: 경복궁"
    )


st.caption(
    "역 이름, 장소 이름 또는 주소를 입력할 수 있습니다."
)


검색버튼 = st.button(
    "🧭 경로 찾기",

    type="primary",

    use_container_width=True,
)


st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# 경로 검색
# =========================================================

if 검색버튼:

    if (
        not 출발지입력.strip()
        or not 도착지입력.strip()
    ):

        st.warning(
            "출발지와 도착지를 "
            "모두 입력해주세요."
        )

        st.stop()


    with st.spinner(
        "장소와 이동 경로를 찾는 중입니다..."
    ):

        출발지 = 장소찾기(
            출발지입력
        )

        도착지 = 장소찾기(
            도착지입력
        )


        if 출발지 is None:

            st.error(
                "출발지를 찾지 못했습니다. "
                "역 이름이나 주소를 "
                "조금 더 정확하게 입력해주세요."
            )

            st.stop()


        if 도착지 is None:

            st.error(
                "도착지를 찾지 못했습니다. "
                "역 이름이나 주소를 "
                "조금 더 정확하게 입력해주세요."
            )

            st.stop()


        경로 = 이동경로찾기(
            출발지["위도"],
            출발지["경도"],
            도착지["위도"],
            도착지["경도"],
        )


    if 경로 is None:

        st.error(
            "이동 경로를 찾지 못했습니다. "
            "잠시 후 다시 시도해주세요."
        )

        st.stop()


    st.session_state["출발지"] = 출발지
    st.session_state["도착지"] = 도착지
    st.session_state["경로"] = 경로
    st.session_state["출발지이름"] = 출발지입력
    st.session_state["도착지이름"] = 도착지입력


# =========================================================
# 결과 화면
# =========================================================

if (
    "경로" in st.session_state
    and st.session_state["경로"] is not None
):

    출발지 = st.session_state["출발지"]
    도착지 = st.session_state["도착지"]
    경로 = st.session_state["경로"]

    출발지이름 = st.session_state["출발지이름"]
    도착지이름 = st.session_state["도착지이름"]

    안내 = 이동안내만들기(
        경로
    )


    # -----------------------------------------------------
    # 결과 요약
    # -----------------------------------------------------

    st.markdown(
        '<div class="카드 경로카드">',
        unsafe_allow_html=True,
    )


    st.markdown(
        f"""
        <div class="설명">
            현재 선택한 경로
        </div>

        <h2>
            {html.escape(출발지이름)}
            →
            {html.escape(도착지이름)}
        </h2>
        """,
        unsafe_allow_html=True,
    )


    첫번째, 두번째, 세번째 = st.columns(3)


    with 첫번째:

        st.markdown(
            f"""
            <div class="큰숫자">
                {시간표시(경로["시간"])}
            </div>

            <div class="설명">
                예상 이동 시간
            </div>
            """,
            unsafe_allow_html=True,
        )


    with 두번째:

        st.markdown(
            f"""
            <div class="큰숫자">
                {거리표시(경로["거리"])}
            </div>

            <div class="설명">
                총 이동 거리
            </div>
            """,
            unsafe_allow_html=True,
        )


    with 세번째:

        st.markdown(
            f"""
            <div class="큰숫자">
                {len(안내)}
            </div>

            <div class="설명">
                주요 안내 단계
            </div>
            """,
            unsafe_allow_html=True,
        )


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # =====================================================
    # 지도 / 음성
    # =====================================================

    지도영역, 안내영역 = st.columns(
        [1.6, 1]
    )


    # -----------------------------------------------------
    # 지도
    # -----------------------------------------------------

    with 지도영역:

        st.markdown(
            '<div class="카드">',
            unsafe_allow_html=True,
        )


        st.subheader(
            "🗺️ 이동 경로"
        )


        components.html(
            지도만들기(
                출발지,
                도착지,
                경로,
            ),

            height=570,

            scrolling=False,
        )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    # -----------------------------------------------------
    # 음성 안내
    # -----------------------------------------------------

    with 안내영역:

        st.markdown(
            '<div class="카드">',
            unsafe_allow_html=True,
        )


        st.subheader(
            "🔊 음성 안내"
        )


        음성문장 = 음성문장만들기(
            출발지이름,
            도착지이름,
            경로,
            안내,
        )


        음성JSON = json.dumps(
            음성문장,
            ensure_ascii=False
        )


        components.html(
            f"""
            <script>

            function 음성시작() {{

                if (
                    !("speechSynthesis"
                    in window)
                ) {{

                    document.getElementById(
                        "상태"
                    ).innerText =
                        "이 브라우저에서는 "
                        + "음성 안내를 지원하지 않습니다.";

                    return;
                }}


                window.speechSynthesis.cancel();


                const 문장 =
                    {음성JSON};


                const 음성 =
                    new SpeechSynthesisUtterance(
                        문장
                    );


                음성.lang =
                    "ko-KR";


                음성.rate =
                    0.95;


                음성.pitch =
                    1.0;


                window.speechSynthesis.speak(
                    음성
                );


                document.getElementById(
                    "상태"
                ).innerText =
                    "🔊 음성 안내가 재생되었습니다.";

            }}


            function 음성중지() {{

                if (
                    "speechSynthesis"
                    in window
                ) {{

                    window.speechSynthesis.cancel();


                    document.getElementById(
                        "상태"
                    ).innerText =
                        "⏹️ 음성 안내를 중지했습니다.";

                }}

            }}

            </script>


            <button
                onclick="음성시작()"

                style="
                    width:100%;
                    padding:14px;
                    border:0;
                    border-radius:12px;
                    background:#4f46e5;
                    color:white;
                    font-size:16px;
                    font-weight:700;
                    cursor:pointer;
                    margin-bottom:9px;
                "
            >
                🔊 음성 안내 시작
            </button>


            <button
                onclick="음성중지()"

                style="
                    width:100%;
                    padding:12px;
                    border:1px solid #ddd;
                    border-radius:12px;
                    background:white;
                    color:#333;
                    font-size:15px;
                    cursor:pointer;
                "
            >
                ⏹️ 음성 안내 중지
            </button>


            <p
                id="상태"

                style="
                    font-family:sans-serif;
                    color:#666;
                    font-size:13px;
                "
            >
                버튼을 누르면
                한국어 음성 안내가 시작됩니다.
            </p>
            """,

            height=190,
        )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


        # -------------------------------------------------
        # 이동 방법
        # -------------------------------------------------

        st.markdown(
            '<div class="카드">',
            unsafe_allow_html=True,
        )


        st.subheader(
            "🚶 이동 방법"
        )


        if not 안내:

            st.info(
                "세부 이동 안내가 없습니다."
            )

        else:

            for 번호, 단계 in enumerate(
                안내,
                start=1
            ):

                st.markdown(
                    f"""
                    <div class="단계">

                        <div class="단계번호">
                            {번호}
                        </div>

                        <div>

                            <b>
                                {html.escape(
                                    단계["내용"]
                                )}
                            </b>

                            <br>

                            <span class="설명">
                                약
                                {거리표시(
                                    단계["거리"]
                                )}
                            </span>

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    st.info(
        "💡 현재 버전은 도보 이동 경로를 기준으로 "
        "안내합니다. 실시간 지하철 운행 정보는 포함하지 않습니다."
    )


# =========================================================
# 처음 실행했을 때
# =========================================================

else:

    st.markdown(
        """
        <div class="카드">

        <h3>
            ✨ 사용 방법
        </h3>


        <div class="단계">

            <div class="단계번호">
                1
            </div>

            <div>

                <b>
                    출발지를 입력하세요.
                </b>

                <br>

                <span class="설명">
                    예: 서울역
                </span>

            </div>

        </div>


        <div class="단계">

            <div class="단계번호">
                2
            </div>

            <div>

                <b>
                    도착지를 입력하세요.
                </b>

                <br>

                <span class="설명">
                    예: 경복궁
                </span>

            </div>

        </div>


        <div class="단계">

            <div class="단계번호">
                3
            </div>

            <div>

                <b>
                    경로 찾기를 누르세요.
                </b>

                <br>

                <span class="설명">
                    지도와 음성으로 이동 방법을 확인할 수 있습니다.
                </span>

            </div>

        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    st.success(
        "예시: 출발지에 '서울역', "
        "도착지에 '경복궁'을 입력해보세요."
    )


# =========================================================
# 하단
# =========================================================

st.caption(
    "지도: OpenStreetMap · "
    "장소 검색: Nominatim · "
    "경로 계산: OSRM · "
    "음성: 브라우저 음성 기능"
)
