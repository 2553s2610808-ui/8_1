# ==================================================
# 간편 역 선택 시스템
# ==================================================

if "전국역자료" not in st.session_state:
    st.session_state["전국역자료"] = None

if "최근검색경로" not in st.session_state:
    st.session_state["최근검색경로"] = []

if "출발역선택" not in st.session_state:
    st.session_state["출발역선택"] = "역을 선택하세요"

if "도착역선택" not in st.session_state:
    st.session_state["도착역선택"] = "역을 선택하세요"

if "경로기준" not in st.session_state:
    st.session_state["경로기준"] = "최소 환승"


# ==================================================
# 전국 역 자료 준비 (처음 한 번)
# ==================================================

with st.expander("전국 역 목록 추가하기", expanded=False):

    st.write(
        "전국 역 목록 파일을 등록하면 "
        "다른 지역의 역도 검색할 수 있어."
    )

    st.link_button(
        "전국 도시철도 역 자료 받기",
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

            st.success("전국 역 목록을 불러왔어!")

        except Exception as e:
            st.error(f"파일을 확인해 줘: {e}")


# ==================================================
# 검색할 역 목록 준비
# ==================================================

기본역목록 = []

for node, info in 역정보.items():

    기본역목록.append({
        "지역": "수도권",
        "노선": info["line"],
        "역명": info["name"]
    })

기본역자료 = pd.DataFrame(기본역목록)

전국역자료 = st.session_state["전국역자료"]

if 전국역자료 is not None:

    역목록자료 = pd.concat(
        [전국역자료, 기본역자료],
        ignore_index=True
    )

else:
    역목록자료 = 기본역자료

역목록자료 = 역목록자료.drop_duplicates(
    subset=["지역", "노선", "역명"]
)

역표시이름 = {}

for _, row in 역목록자료.iterrows():

    이름 = str(row["역명"]).strip()
    노선 = str(row["노선"]).strip()
    지역 = str(row["지역"]).strip()

    if not 이름.endswith("역"):
        이름 += "역"

    표시 = f"{이름} · {노선} · {지역}"

    역표시이름[표시] = str(row["역명"]).strip()

역선택목록 = sorted(역표시이름.keys())

역옵션 = [
    "역을 선택하세요"
] + 역선택목록


def 역표시찾기(이름):

    if not 이름:
        return "역을 선택하세요"

    key = 역이름키(이름)

    for 표시, 원래이름 in 역표시이름.items():

        if 역이름키(원래이름) == key:
            return 표시

    return "역을 선택하세요"


# 저장된 선택이 현재 목록에 없으면 초기화
for key in ["출발역선택", "도착역선택"]:

    if st.session_state[key] not in 역옵션:
        st.session_state[key] = "역을 선택하세요"


# ==================================================
# 최근 검색
# ==================================================

with st.expander("🕘 최근에 검색한 경로"):

    최근기록 = st.session_state["최근검색경로"]

    if 최근기록:

        for i, 기록 in enumerate(최근기록):

            st.write(
                f"{기록['출발']} → {기록['도착']}"
            )

            if st.button(
                "다시 선택",
                key=f"최근경로{i}"
            ):

                st.session_state["출발역선택"] = (
                    역표시찾기(기록["출발"])
                )

                st.session_state["도착역선택"] = (
                    역표시찾기(기록["도착"])
                )

                st.session_state["경로기준"] = (
                    기록["기준"]
                )

                st.rerun()

    else:
        st.caption("최근 검색 기록이 없어.")


# ==================================================
# 출발역과 도착역 바꾸기
# ==================================================

if st.button(
    "↕ 출발역과 도착역 바꾸기",
    use_container_width=True
):

    임시 = st.session_state["출발역선택"]

    st.session_state["출발역선택"] = (
        st.session_state["도착역선택"]
    )

    st.session_state["도착역선택"] = 임시

    st.rerun()


# ==================================================
# 간단한 길찾기 화면
# ==================================================

st.divider()

st.subheader("🚉 지하철 길찾기")

st.caption(
    "역 선택 칸을 누르고 역 이름을 입력하면 "
    "해당 역을 쉽게 찾을 수 있어."
)

with st.form("route_form"):

    st.markdown("### ① 출발역")

    출발선택 = st.selectbox(
        "출발할 역을 선택하세요",
        역옵션,
        key="출발역선택"
    )

    st.markdown("### ② 도착역")

    도착선택 = st.selectbox(
        "도착할 역을 선택하세요",
        역옵션,
        key="도착역선택"
    )

    st.markdown("### ③ 경로 선택")

    기준선택 = st.radio(
        "어떤 경로로 갈까요?",
        [
            "환승 적게 (추천)",
            "이동 역 적게"
        ],
        horizontal=True
    )

    기준 = (
        "최소 환승"
        if 기준선택 == "환승 적게 (추천)"
        else "최단 역 수"
    )

    출발입력 = 역표시이름.get(
        출발선택,
        ""
    )

    도착입력 = 역표시이름.get(
        도착선택,
        ""
    )

    검색버튼 = st.form_submit_button(
        "🔵 길찾기 시작",
        use_container_width=True
    )

    if 검색버튼:

        if (
            출발선택 == "역을 선택하세요"
            or 도착선택 == "역을 선택하세요"
        ):

            st.warning(
                "출발역과 도착역을 모두 선택해 줘."
            )

        else:

            st.session_state["경로검색요청"] = True
