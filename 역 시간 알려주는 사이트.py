import streamlit as st
from datetime import datetime, date, time, timedelta

st.set_page_config(
    page_title="기차 안심 도우미",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
:root { --teal: #62d4d0; --teal-dark: #2eaaa7; --ink: #26363a; --muted: #7b8a8d; --paper: #f1f3f6; }
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; color: var(--ink); }
.stApp { background: #edf0f4; }
.block-container { max-width: 1400px; padding-top: 2rem; padding-bottom: 2rem; }
h1, h2, h3 { color: #26363a !important; letter-spacing: -0.03em; }
h1 { font-size: 2.15rem !important; font-weight: 800 !important; }
h2 { font-size: 1.45rem !important; font-weight: 800 !important; }
h3 { font-size: 1.1rem !important; font-weight: 700 !important; }
p, label, .stMarkdown { font-size: 1rem; }
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255,255,255,0.96); border: 1px solid #f7f8fa;
  border-radius: 24px; padding: 1.1rem; box-shadow: 0 12px 32px rgba(48,68,77,0.06);
}
div[data-testid="stMetric"] { background: #f6fbfb; padding: 1rem; border-radius: 18px; border: 1px solid #e1f4f3; }
div[data-testid="stMetricLabel"] { font-size: 1rem !important; color: #657578 !important; }
div[data-testid="stMetricValue"] { font-size: 1.7rem !important; color: #26363a !important; font-weight: 800; }
div.stButton > button {
  background: #62d4d0; color: #173b3c; border: 0; border-radius: 999px;
  min-height: 3.1rem; font-size: 1.05rem; font-weight: 800;
}
div.stButton > button:hover { background: #4bc4c0; color: #173b3c; border: 0; }
.stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input {
  border-radius: 12px !important; min-height: 2.8rem;
}
.stFileUploader { background: #f7fbfb; border-radius: 16px; padding: .5rem; }
div[data-testid="stAlert"] { border-radius: 14px; }
.small-muted { color: #7b8a8d; font-size: .9rem; }
.hero {
  background: linear-gradient(115deg, #6bd9d4 0%, #a5e9e3 100%);
  border-radius: 26px; padding: 1.6rem 1.8rem; margin-bottom: 1.2rem;
  color: #183c3d; box-shadow: 0 12px 30px rgba(66,180,175,.13);
}
.hero-title { font-size: 1.7rem; font-weight: 800; margin-bottom: .35rem; }
.hero-sub { font-size: 1rem; opacity: .88; }
.illustration { font-size: 3.4rem; line-height: 1.25; }
.pill { display: inline-block; padding: .3rem .7rem; border-radius: 999px; background: #e4f8f6; color: #258d89; font-size: .85rem; font-weight: 700; }
@media (max-width: 800px) {
  .block-container { padding: 1rem .8rem; }
  h1 { font-size: 1.7rem !important; }
  .hero { padding: 1.2rem; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-title">🚆 기차 안심 도우미</div>
  <div class="hero-sub">기차 여행, 서두르지 않도록 미리 준비해요. 집에서 나갈 시간부터 도착 예정 시간까지 한눈에 확인할 수 있어요.</div>
</div>
""", unsafe_allow_html=True)

top1, top2, top3 = st.columns(3, gap="large")
with top1:
    with st.container(border=True):
        st.markdown('<div class="pill">STEP 01 · 준비하기</div>', unsafe_allow_html=True)
        st.markdown('<div class="illustration">🧳</div>', unsafe_allow_html=True)
        st.subheader("기차표 확인")
        st.write("예매한 표를 참고해 열차 정보를 입력해 주세요.")
        ticket_file = st.file_uploader("기차표 이미지 또는 PDF (선택)", type=["png", "jpg", "jpeg", "webp", "pdf"])
        if ticket_file:
            st.success(f"첨부 완료: {ticket_file.name}")
            if ticket_file.type.startswith("image/"):
                st.image(ticket_file, use_container_width=True)
            else:
                st.caption("PDF를 열어 내용을 확인한 뒤, 옆 칸에 정보를 입력해 주세요.")
        st.caption("※ 첨부한 표의 글자를 자동으로 읽지는 않습니다.")

with top2:
    with st.container(border=True):
        st.markdown('<div class="pill">STEP 02 · 입력하기</div>', unsafe_allow_html=True)
        st.markdown('<div class="illustration">🗺️</div>', unsafe_allow_html=True)
        st.subheader("여행 정보")
        train_date = st.date_input("기차 타는 날짜", value=date.today() + timedelta(days=1))
        departure_station = st.text_input("출발역", placeholder="예: 서울역")
        arrival_station = st.text_input("도착역", placeholder="예: 부산역")
        train_name = st.text_input("열차 이름 또는 번호 (선택)", placeholder="예: KTX 123")
        departure_time = st.time_input("기차 출발 시각", value=time(9, 0), step=300)
        arrival_time = st.time_input("기차 도착 시각", value=time(11, 45), step=300)

with top3:
    with st.container(border=True):
        st.markdown('<div class="pill">STEP 03 · 시간 확인</div>', unsafe_allow_html=True)
        st.markdown('<div class="illustration">⏰</div>', unsafe_allow_html=True)
        st.subheader("역까지 이동")
        travel_minutes = st.number_input("집에서 역까지 (분)", min_value=0, max_value=600, value=40, step=5)
        extra_minutes = st.number_input("이동 여유 시간 (분)", min_value=0, max_value=180, value=15, step=5,
                                        help="교통 상황이나 길 찾기에 대비한 여유 시간입니다.")
        station_buffer = st.number_input("기차 출발 전 역 도착 (분)", min_value=10, max_value=120, value=30, step=5,
                                         help="이동이 불편하거나 처음 가는 역이라면 30~45분 이상 권장합니다.")
        st.markdown('<p class="small-muted">엘리베이터 이용, 승강장 찾기 등을 고려해 여유 있게 준비하세요.</p>', unsafe_allow_html=True)

st.divider()
st.markdown("## 오늘의 일정")
st.write("여행 정보를 입력한 뒤 아래 버튼을 눌러 시간을 계산하세요.")

if st.button("시간표 계산하기", type="primary", use_container_width=True):
    errors = []
    if not departure_station.strip():
        errors.append("출발역을 입력해 주세요.")
    if not arrival_station.strip():
        errors.append("도착역을 입력해 주세요.")
    if departure_station.strip() and arrival_station.strip() and departure_station.strip() == arrival_station.strip():
        errors.append("출발역과 도착역이 같은지 확인해 주세요.")

    departure_dt = datetime.combine(train_date, departure_time)
    arrival_dt = datetime.combine(train_date, arrival_time)
    if arrival_dt <= departure_dt:
        arrival_dt += timedelta(days=1)

    if errors:
        for error in errors:
            st.error(error)
    else:
        station_arrival_dt = departure_dt - timedelta(minutes=int(station_buffer))
        leave_home_dt = station_arrival_dt - timedelta(minutes=int(travel_minutes) + int(extra_minutes))
        st.success(f"{departure_station.strip()}에서 출발해 {arrival_station.strip()}에 도착하는 일정이에요.")
        if train_name.strip():
            st.caption(f"열차: {train_name.strip()}")
        r1, r2, r3, r4 = st.columns(4, gap="medium")
        with r1:
            st.metric("🏠 집에서 출발", leave_home_dt.strftime("%m월 %d일 %H:%M"))
        with r2:
            st.metric("🚉 역 도착", station_arrival_dt.strftime("%m월 %d일 %H:%M"))
        with r3:
            st.metric("🚆 기차 출발", departure_dt.strftime("%m월 %d일 %H:%M"))
        with r4:
            st.metric("🏁 목적지 도착", arrival_dt.strftime("%m월 %d일 %H:%M"))

        with st.container(border=True):
            st.subheader("출발 전 체크리스트")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.checkbox("기차표 날짜와 시간 확인", key="ticket_check")
            with c2:
                st.checkbox("신분증과 기차표 준비", key="id_check")
            with c3:
                st.checkbox("역 전광판에서 승강장 확인", key="platform_check")
        st.warning("계산 결과는 입력한 예상 시간에 따른 안내입니다. 교통 체증이나 역 내부 이동에 따라 달라질 수 있으니 여유 있게 출발하세요.")

st.markdown("""
<div style="text-align:center; color:#7b8a8d; font-size:.85rem; padding:1.2rem 0 .5rem;">
이 앱은 기차표 예약이나 실시간 열차 운행 정보를 제공하지 않습니다.<br>
열차 시간 변경 여부는 코레일 또는 실제 예매처에서 확인해 주세요.
</div>
""", unsafe_allow_html=True)
