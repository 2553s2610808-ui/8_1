import os
import streamlit as st
import google.generativeai as genai

# Streamlit 페이지 기본 설정 (시니어 모드에 맞게 넓고 깔끔한 레이아웃)
st.set_page_config(
    page_title="어르신 쉬운 지하철 길안내",
    page_icon="🚇",
    layout="centered"
)

# -----------------------------------------------------------------------------
# CSS 스타일링 (어르신을 위한 큰 글씨, 명확한 색상 대비, 큰 버튼 적용)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    /* 전체 폰트 크기 확대 및 가독성 향상 */
    html, body, [class*="css"] {
        font-size: 20px !important;
        font-family: 'Malgun Gothic', '맑은 고딕', sans-serif !important;
    }
    
    /* 제목 스타일 */
    .title-text {
        font-size: 34px !important;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 5px;
    }
    .subtitle-text {
        font-size: 22px !important;
        color: #4B5563;
        text-align: center;
        margin-bottom: 25px;
    }

    /* 입력창 및 라벨 크기 확대 */
    .stTextInput > label {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #1F2937 !important;
    }
    .stTextInput input {
        font-size: 22px !important;
        height: 55px !important;
        border: 2px solid #3B82F6 !important;
        border-radius: 10px !important;
    }

    /* 버튼 스타일 (크고 누르기 쉽게) */
    .stButton > button {
        font-size: 24px !important;
        font-weight: bold !important;
        background-color: #2563EB !important;
        color: white !important;
        height: 60px !important;
        width: 100% !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    .stButton > button:hover {
        background-color: #1D4ED8 !important;
    }

    /* 자주 가는 장소 버튼 스타일 */
    .shortcut-btn button {
        background-color: #F3F4F6 !important;
        color: #1F2937 !important;
        font-size: 18px !important;
        height: 45px !important;
        border: 1px solid #D1D5DB !important;
    }

    /* 결과 카드 스타일 */
    .result-box {
        background-color: #F0F9FF;
        border-left: 8px solid #0284C7;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        font-size: 22px;
        line-height: 1.8;
    }
    
    .tip-box {
        background-color: #FEF3C7;
        border-left: 8px solid #D97706;
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
        font-size: 19px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Gemini API 설정
# -----------------------------------------------------------------------------
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]

if api_key:
    genai.configure(api_key=api_key)

# -----------------------------------------------------------------------------
# AI 경로 탐색 함수
# -----------------------------------------------------------------------------
def get_subway_directions(start_location, destination):
    """
    Gemini 2.5 Flash Lite 모델을 사용하여 어르신 맞춤형 지하철 경로를 생성합니다.
    """
    if not api_key:
        return "⚠️ API 키가 설정되지 않았습니다. Secrets에 GEMINI_API_KEY를 입력해주세요."

    prompt = f"""
    너는 대중교통 이용이 어려운 어르신들을 위한 아주 친절하고 쉬운 지하철 안내 도우미야.
    
    [출발 위치/역]: {start_location}
    [도착 장소/건물/역]: {destination}

    다음 지침에 따라 어르신이 이해하기 가장 쉽게 지하철 길안내를 작성해줘:

    1. **가장 가까운 역 찾기**: 도착지가 건물/장소 이름이라면, 도착지와 가장 가까운 지하철역과 몇 번 출구로 나가야 하는지 정확히 알려줘.
    2. **쉬운 탑승 안내**: 
       - 무슨 색깔 노선(예: 1호선 파란색, 2호선 초록색 등)을 타야 하는지 알려줘.
       - 어느 방향(OO역 방면) 전철을 타야 하는지 명확히 적어줘.
    3. **환승 안내**: 
       - 환승이 필요하다면 어디서 갈아타야 하는지 큰 글씨 느낌으로 알기 쉽게 1단계, 2단계로 나누어 설명해줘. (최대 환승 2회 이하의 쉬운 경로 추천)
       - 환승이 없으면 "갈아탈 필요 없이 한 번에 갑니다"라고 말해줘.
    4. **어르신 친절 팁**:
       - 계단이 부담스러우실 수 있으니 엘리베이터 이용 팁이나 출구 도보 시간(예: 약 5분 소요)을 따뜻한 어조로 알려줘.

    어투는 친절한 존댓말("어르신, ~하세요", "~하시면 됩니다")을 사용하고, 복잡한 기호나 어려운 철도 용어 대신 쉽고 명확하게 작성해줘.
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 길안내를 가져오는 중에 오류가 발생했습니다.\n오류 내용: {str(e)}"

# -----------------------------------------------------------------------------
# 메인 화면 구성
# -----------------------------------------------------------------------------
st.markdown("<div class='title-text'>🚇 어르신 쉬운 지하철 도우미</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle-text'>복잡한 노선도 없이, 목적지만 입력하면 쉽게 알려드립니다!</div>", unsafe_allow_html=True)

st.divider()

# 1. 입력 세션 (출발지 및 목적지)
st.subheader("📍 어디서 출발해서 어디로 가시나요?")

col1, col2 = st.columns(1)

# 세션 상태 초기화 (자주 가는 장소 클릭 시 사용)
if "dest_input" not in st.session_state:
    st.session_state["dest_input"] = ""

start_input = st.text_input(
    "1. 계신 곳 (출발역 또는 현재 위치)", 
    placeholder="예: 서울역, 청량리역, 강남역",
    key="start_key"
)

dest_input = st.text_input(
    "2. 가고자 하는 곳 (목적지 건물이나 역 이름)", 
    value=st.session_state["dest_input"],
    placeholder="예: 서울대병원, 자갈치시장, 롯데월드, 종로3가역",
    key="dest_key"
)

# 2. 어르신 자주 가시는 장소 빠른 선택 (편의 기능)
st.write("💡 **자주 가시는 곳을 누르시면 자동으로 입력됩니다:**")
quick_cols = st.columns(4)

def set_destination(place_name):
    st.session_state["dest_input"] = place_name

with quick_cols[0]:
    if st.button("🏥 서울대병원", key="btn1"):
        set_destination("혜화역 서울대병원")
        st.rerun()
with quick_cols[1]:
    if st.button("🏞️ 남산서울타워", key="btn2"):
        set_destination("명동역 남산타워")
        st.rerun()
with quick_cols[2]:
    if st.button("🛒 동대문시장", key="btn3"):
        set_destination("동대문역 동대문시장")
        st.rerun()
with quick_cols[3]:
    if st.button("🚌 서울고속터미널", key="btn4"):
        set_destination("고속터미널역")
        st.rerun()

st.write("") # 간격 조정

# 3. 길찾기 실행 버튼
search_button = st.button("🔍 쉬운 길안내 시작하기")

# 4. 결과 출력
if search_button:
    if not start_input.strip():
        st.warning("⚠️ 출발하시는 곳이나 출발역을 입력해주세요!")
    elif not dest_input.strip():
        st.warning("⚠️ 가고자 하는 목적지나 건물 이름을 입력해주세요!")
    else:
        with st.spinner("어르신을 위해 가장 쉽고 편한 길을 찾는 중입니다... 잠시만 기다려주세요 ⏳"):
            result_text = get_subway_directions(start_input, dest_input)
            
            st.markdown("### 🗺️ 맞춤 길안내 결과")
            st.markdown(f"<div class='result-box'>{result_text}</div>", unsafe_allow_html=True)
            
            # 어르신 안심 안내 팁
            st.markdown("""
            <div class='tip-box'>
                💡 <b>어르신을 위한 지하철 이용 팁!</b><br>
                - 만 65세 이상 어르신은 <b>우대용 교통카드</b>를 이용하시면 지하철요금이 무료입니다.<br>
                - 계단이 높거나 이용이 불편하실 땐 역 안의 <b>엘리베이터</b>나 <b>역무원 호출 벨</b>을 이용하세요.
            </div>
            """, unsafe_allow_html=True)

# 하단 안내
st.divider()
st.caption("본 서비스는 어르신들의 편리한 대중교통 이용을 돕기 위해 AI(Gemini) 기술을 활용하여 제작되었습니다.")
