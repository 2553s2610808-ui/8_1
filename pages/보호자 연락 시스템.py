import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

st.set_page_config(
    page_title="안심지하철",
    page_icon="🚇",
    layout="centered"
)

# 전국 지하철역 목록
STATIONS = {
    "수도권": """
서울역 시청 종각 종로3가 종로5가 동대문 동묘앞 신설동 제기동 청량리 회기 외대앞 신이문 석계 광운대 월계 녹천 창동 도봉 방학 도봉산 수유 미아 미아사거리 길음 성신여대입구 혜화 충무로 명동 회현 숙대입구 삼각지 용산 남영 노량진 대방 신길 영등포 신도림 구로 가산디지털단지 독산 금천구청 안양 금정 군포 의왕 수원 병점 오산 평택 천안
강남 역삼 선릉 삼성 종합운동장 잠실 잠실새내 건대입구 성수 왕십리 한양대 뚝섬 구의 강변 교대 서초 방배 사당 낙성대 서울대입구 봉천 신림 대림 구로디지털단지 신대방 홍대입구 신촌 이대 아현 충정로 을지로입구 을지로3가 을지로4가 동대문역사문화공원 신당 상왕십리 압구정 신사 논현 고속터미널 남부터미널 양재 도곡 수서 오금
대화 주엽 정발산 마두 백석 대곡 화정 원당 삼송 지축 구파발 연신내 불광 녹번 홍제 경복궁 안국 약수 옥수 금호 동대입구 잠원 남태령 선바위 과천 범계 평촌 인덕원 산본 상록수 중앙 안산 오이도
진접 오남 별내별가람 당고개 상계 노원 중계 하계 공릉 태릉입구 먹골 중화 상봉 면목 사가정 용마산 군자 어린이대공원 내방 이수 남성 숭실대 상도 장승배기 신대방삼거리 보라매 신풍 남구로 철산 광명사거리 천왕 온수 역곡 부천 중동 송내 부평 동암 주안 인천 동인천
방화 개화산 김포공항 송정 마곡 발산 화곡 까치산 목동 오목교 영등포구청 당산 여의도 여의나루 마포 공덕 서대문 광화문 청구 신금호 행당 마장 답십리 장한평 아차산 광나루 천호 강동 길동 명일 고덕 상일동 강일 미사 하남풍산 하남시청 하남검단산
응암 역촌 독바위 구산 새절 증산 디지털미디어시티 월드컵경기장 마포구청 망원 합정 상수 광흥창 대흥 효창공원앞 녹사평 이태원 한강진 버티고개 보문 안암 고려대 월곡 상월곡 돌곶이 화랑대 봉화산 신내
암사 강동구청 몽촌토성 석촌 송파 송파나루 한성백제 올림픽공원 둔촌오륜 중앙보훈병원
개화 김포공항 공항시장 신방화 마곡나루 양천향교 가양 증미 등촌 염창 신목동 선유도 국회의사당 샛강 노들 흑석 동작 구반포 신반포 사평 신논현 언주 선정릉 삼성중앙 봉은사
계양 귤현 박촌 임학 계산 작전 갈산 부평구청 부평시장 부평 동수 간석오거리 인천시청 예술회관 인천터미널 선학 신연수 원인재 동춘 동막 캠퍼스타운 테크노파크 인천대입구 센트럴파크 검단오류 왕길 검단사거리 마전 완정 독정 검암 검바위 서구청 가정 석남
문산 파주 금촌 운정 야당 탄현 일산 풍산 백마 곡산 능곡 행신 강매 화전 수색 가좌 서강대 이촌 서빙고 한남 응봉 구리 도농 덕소 팔당 양수 양평 용문
갈매 별내 퇴계원 사릉 금곡 평내호평 마석 청평 가평 남춘천 춘천
서울숲 압구정로데오 한티 구룡 개포동 대모산입구 가천대 태평 모란 야탑 이매 서현 수내 정자 미금 오리 죽전 보정 구성 신갈 기흥 상갈 영통 망포 수원시청 고색 오목천
판교 동천 수지구청 성복 상현 광교중앙 광교 삼동 경기광주 초월 곤지암 이천 부발 여주
시흥대야 신천 시흥시청 시흥능곡 달미 선부 원시
강남대 지석 어정 동백 초당 삼가 명지대 김량장 고진 둔전 전대에버랜드
발곡 회룡 범골 경전철의정부 의정부시청 흥선 의정부중앙 새말 동오 효자 곤제 어룡 송산 탑석
양촌 구래 마산 장기 운양 걸포북변 사우 풍무 고촌
북한산우이 솔밭공원 4.19민주묘지 가오리 화계 삼양 삼양사거리 솔샘 북한산보국문 정릉
서울지방병무청 보라매공원 보라매병원 당곡 서원 서울대벤처타운 관악산
""",
    "부산·김해": """
다대포해수욕장 다대포항 낫개 신장림 장림 동매 신평 하단 당리 사하 괴정 대티 서대신 동대신 토성 자갈치 남포 중앙 부산역 초량 부산진 좌천 범일 범내골 서면 부전 양정 시청 연산 교대 동래 명륜 온천장 부산대 장전 구서 두실 남산 범어사 노포
장산 중동 해운대 동백 벡스코 센텀 민락 수영 광안 금련산 남천 경성대부경대 대연 못골 지게골 문현 국제금융센터 전포 부암 가야 동의대 개금 냉정 주례 감전 사상 모덕 모라 구남 구명 덕천 수정 화명 율리 동원 금곡 호포 증산 부산대양산캠퍼스 남양산 양산
대저 체육공원 강서구청 구포 숙등 남산정 만덕 미남 사직 종합운동장 거제 낙민 충렬사 명장 서동 금사 반여농산물시장 석대 영산대 동부산대 고촌 안평
부전 거제 안락 부산원동 재송 신해운대 송정 오시리아 기장 일광 좌천 월내 서생 남창 덕하 태화강
괘법르네시떼 서부산유통지구 공항 덕두 등구 평강 대사 불암 지내 김해대학 인제대 김해시청 부원 봉황 수로왕릉 박물관 김해
""",
    "대구": """
설화명곡 화원 대곡 진천 월배 상인 월촌 송현 성당못 대명 안지랑 현충로 영대병원 교대 명덕 반월당 중앙로 대구역 칠성시장 신천 동대구역 동구청 아양교 동촌 해안 방촌 용계 율하 신기 반야월 각산 안심
문양 다사 대실 강창 계명대 성서산업단지 이곡 용산 죽전 감삼 두류 내당 반고개 청라언덕 경대병원 대구은행 범어 수성구청 만촌 담티 연호 대공원 고산 신매 사월 정평 임당 영남대
칠곡경대병원 학정 팔거 동천 칠곡운암 구암 태전 매천 매천시장 팔달 공단 팔달시장 원대 북구청 달성공원 서문시장 남산 건들바위 대봉교 수성시장 어린이회관 황금 수성못 지산 범물 용지
""",
    "광주": """
녹동 소태 학동증심사입구 남광주 문화전당 금남로4가 금남로5가 양동시장 돌고개 농성 화정 쌍촌 운천 상무 김대중컨벤션센터 공항 송정공원 광주송정 도산 평동
""",
    "대전": """
판암 신흥 대동 대전역 중앙로 중구청 서대전네거리 오룡 용문 탄방 시청 정부청사 갈마 월평 갑천 유성온천 구암 현충원 월드컵경기장 노은 지족 반석
"""
}

# 중복 역 제거
for region in STATIONS:
    STATIONS[region] = list(dict.fromkeys(STATIONS[region].split()))

REGIONS = list(STATIONS.keys())

def move(page):
    st.session_state.page = page
    st.rerun()

def send_sms(phone, message):
    try:
        sid = st.secrets["TWILIO_ACCOUNT_SID"]
        token = st.secrets["TWILIO_AUTH_TOKEN"]
        sender = st.secrets["TWILIO_PHONE_NUMBER"]
    except Exception:
        return False, "문자 발송 Secrets 설정이 필요합니다."

    if not phone:
        return False, "전화번호를 입력해 주세요."

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        response = requests.post(
            url,
            data={"To": phone, "From": sender, "Body": message},
            auth=HTTPBasicAuth(sid, token),
            timeout=15
        )
        if response.status_code in (200, 201):
            return True, "문자를 발송했습니다."
        return False, "문자 발송 실패: " + str(response.status_code)
    except requests.RequestException:
        return False, "네트워크 오류가 발생했습니다."
    except Exception:
        return False, "문자 발송 중 오류가 발생했습니다."

# 디자인
st.markdown("""
<style>
.stApp {background:#FBFAFF;}
[data-testid="stSidebar"] {background:#F0EBFF;}
.hero {
    background:linear-gradient(135deg,#7654D6,#A58BEF);
    padding:28px;border-radius:20px;color:white;
}
.hero h1,.hero p {color:white;}
div.stButton>button {
    background:#7654D6;color:white;border:0;
    border-radius:12px;min-height:48px;
    font-size:17px;font-weight:bold;width:100%;
}
</style>
""", unsafe_allow_html=True)

# 기본 상태
defaults = {
    "page":"메인 화면",
    "start_region":"수도권",
    "dest_region":"수도권",
    "start_station":"서울역",
    "destination":"강남",
    "phone":"",
    "travelling":False,
    "arrived":False,
    "sms_status":""
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 사이드바
pages = ["메인 화면","목적지 설정","탑승 중","도착 완료","보호자 알림"]
with st.sidebar:
    st.title("🚇 안심지하철")
    st.caption("안전한 이동을 도와드려요.")
    selected = st.radio("메뉴", pages, index=pages.index(st.session_state.page))
    if selected != st.session_state.page:
        st.session_state.page = selected
        st.rerun()

page = st.session_state.page

# 메인 화면
if page == "메인 화면":
    st.markdown("""
    <div class="hero">
    <h1>안심지하철 🚇</h1>
    <p>목적지까지 편안하게 이동하고<br>
    도착 소식을 보호자에게 알려드려요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("오늘도 안전하게 이동해요")
    st.info("전국의 지역별 지하철역을 선택할 수 있어요.")
    st.write("① 목적지 설정")
    st.write("② 지하철 이동")
    st.write("③ 도착 확인")
    st.write("④ 보호자에게 알림")
    if st.button("🚆 지하철 타기 시작하기"):
        move("목적지 설정")

# 목적지 설정
elif page == "목적지 설정":
    st.title("📍 목적지를 설정해 주세요")

    start_region = st.selectbox("출발 지역", REGIONS)
    start_station = st.selectbox(
        "출발역",
        STATIONS[start_region]
    )

    dest_region = st.selectbox("도착 지역", REGIONS)
    destination = st.selectbox(
        "도착역",
        STATIONS[dest_region]
    )

    phone = st.text_input(
        "보호자 전화번호",
        placeholder="+821012345678",
        value=st.session_state.phone
    )

    if st.button("선택 완료하고 이동하기"):
        if start_region == dest_region and start_station == destination:
            st.error("출발역과 도착역을 다르게 선택해 주세요.")
        else:
            st.session_state.start_region = start_region
            st.session_state.dest_region = dest_region
            st.session_state.start_station = start_station
            st.session_state.destination = destination
            st.session_state.phone = phone.strip()
            st.session_state.travelling = True
            st.session_state.arrived = False
            move("탑승 중")

# 탑승 중
elif page == "탑승 중":
    st.title("🚉 안전하게 이동하세요")

    if not st.session_state.travelling:
        st.info("먼저 목적지를 설정해 주세요.")
        if st.button("목적지 설정"):
            move("목적지 설정")
    else:
        st.success(
            "출발역: " + st.session_state.start_region
            + " · " + st.session_state.start_station
        )
        st.markdown("### ⬇️")
        st.info(
            "도착역: " + st.session_state.dest_region
            + " · " + st.session_state.destination
        )

        st.warning("실제 GPS 위치를 자동 추적하지 않습니다. 도착한 뒤 버튼을 눌러 주세요.")

        if st.button("✅ 목적지에 도착했어요"):
            st.session_state.travelling = False
            st.session_state.arrived = True
            move("도착 완료")

# 도착 완료
elif page == "도착 완료":
    st.title("🎉 도착 확인")

    if st.session_state.arrived:
        st.markdown("""
        <div class="hero">
        <h1>도착을 확인했어요!</h1>
        <p>안전하게 이동을 마쳤습니다.</p>
        </div>
        """, unsafe_allow_html=True)

        st.success(
            st.session_state.destination
            + " 도착 · "
            + datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        if st.button("보호자 알림 보내기"):
            move("보호자 알림")
    else:
        st.info("먼저 도착 확인을 해 주세요.")

# 보호자 알림
elif page == "보호자 알림":
    st.title("💌 보호자 알림")

    if not st.session_state.arrived:
        st.info("도착 확인을 먼저 해 주세요.")
    else:
        phone = st.text_input(
            "보호자 전화번호",
            value=st.session_state.phone
        )

        message = (
            "[안심지하철] 탑승자가 목적지에 도착했습니다. "
            + "출발역: " + st.session_state.start_station
            + ", 도착역: " + st.session_state.destination
            + ", 확인 시각: " + datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        st.subheader("전송할 알림 내용")
        st.code(message)

        if st.button("📩 보호자에게 문자 보내기"):
            st.session_state.phone = phone.strip()
            ok, result = send_sms(phone.strip(), message)
            st.session_state.sms_status = result

            if ok:
                st.success(result)
            else:
                st.warning(result)

        if st.session_state.sms_status:
            st.caption(st.session_state.sms_status)

        st.caption("실제 문자 발송은 Twilio 설정이 필요합니다.")

st.divider()
st.caption("안심지하철 | 안전한 이동을 위한 도우미")
