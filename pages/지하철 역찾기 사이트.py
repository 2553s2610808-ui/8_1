
import json
import streamlit.components.v1 as components

# 가까운 역 탭 내부에 넣을 코드
with tab_nearest:
    st.subheader("📍 현재 위치에서 가까운 역 찾기")
    st.write("현재 위치를 확인한 뒤 주변 역을 찾아보세요.")

    st.info(
        "이 기능은 브라우저의 위치 권한을 사용합니다. "
        "HTTPS 주소에서 실행해주세요."
    )

    components.html(
        """
        <div style="font-family: sans-serif;">
          <button id="locate"
            style="padding:12px 18px; border:0; border-radius:8px;
                   background:#1769aa; color:white; cursor:pointer;">
            📍 현재 위치 확인
          </button>
          <p id="status">버튼을 눌러 위치를 확인하세요.</p>
          <a id="maplink" target="_blank" rel="noopener"
             style="display:none; padding:12px 0;">
             🗺️ 지도에서 주변 역 확인하기
          </a>
        </div>

        <script>
          const button = document.getElementById("locate");
          const status = document.getElementById("status");
          const link = document.getElementById("maplink");

          button.addEventListener("click", function () {
            if (!navigator.geolocation) {
              status.textContent =
                "이 브라우저는 위치 확인을 지원하지 않습니다.";
              return;
            }

            status.textContent = "현재 위치를 확인하는 중입니다...";
            link.style.display = "none";

            navigator.geolocation.getCurrentPosition(
              function (position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                const params = new URLSearchParams({
                  api: "1",
                  origin: lat + "," + lon,
                  destination: lat + "," + lon,
                  travelmode: "walking"
                });

                // 지도에서 주변 지하철역을 검색
                const url =
                  "https://www.google.com/maps/search/subway+station/@" +
                  lat + "," + lon + ",15z";

                link.href = url;
                link.style.display = "inline-block";
                status.textContent =
                  "위치를 확인했습니다. 아래 링크를 눌러 주변 역을 확인하세요.";
              },
              function (error) {
                if (error.code === 1) {
                  status.textContent =
                    "위치 권한이 거부되었습니다. 브라우저 설정에서 허용해주세요.";
                } else if (error.code === 2) {
                  status.textContent =
                    "현재 위치를 확인할 수 없습니다. GPS 또는 위치 서비스를 확인해주세요.";
                } else {
                  status.textContent =
                    "위치 확인 시간이 초과되었습니다. 다시 시도해주세요.";
                }
              },
              {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 60000
              }
            );
          });
        </script>
        """,
        height=180,
    )
