st.markdown(
    "<h2 style='text-align:center;'>🚇 지하철 노선 찾기</h2>",
    unsafe_allow_html=True
)

left, right = st.columns(2)

with left:
    start = st.text_input("노선", placeholder="출발역 또는 현재 위치")

with right:
    destination = st.text_input("도착지", placeholder="목적지 입력")

st.markdown("""
<div style="
    background-color:#ff0808;
    border:1px solid black;
    padding:24px;
    text-align:center;
    font-size:20px;
    color:black;
    margin-top:25px;">
    도착지를 입력하면 현재 위치에서 가까운 지하철역을 찾아줍니다.
</div>
""", unsafe_allow_html=True)
