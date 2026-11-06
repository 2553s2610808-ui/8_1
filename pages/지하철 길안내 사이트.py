                f"{step['to_line']}으로 직결 운행합니다."
            )

    if not displayed_step:

        st.warning(
            "계산된 경로의 이동 구간을 표시하지 못했어. "
            "다른 경로 기준으로 다시 검색해 줘."
        )

    # -----------------------------------------------------
    # 전체 이동 순서
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "📍 전체 이동 순서"
    )

    route_stations = []

    for node_id in path:

        station_name = 역이름표시(
            node_id,
            역정보
        )

        line_name = 역정보[node_id]["line"]

        # 환승으로 같은 역이 연속될 때 중복 표시하지 않음
        if (
            route_stations
            and route_stations[-1][0] == station_name
        ):

            route_stations[-1] = (
                station_name,
                line_name
            )

        else:

            route_stations.append(
                (
                    station_name,
                    line_name
                )
            )

    for number, (station_name, line_name) in enumerate(
        route_stations,
        start=1
    ):

        st.text(
            f"{number}. {station_name} · {line_name}"
        )

    # -----------------------------------------------------
    # 지도
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "🗺️ 이동 경로 지도"
    )

    st.caption(
        "지도는 역 좌표를 직선으로 연결한 참고용 표시입니다."
    )

    map_html = 지도HTML(
        path,
        역정보
    )

    if map_html:

        components.html(
            map_html,
            height=435,
            scrolling=False
        )

    else:

        st.info(
            "이 경로는 지도 좌표를 표시할 수 없어."
        )

    # -----------------------------------------------------
    # 음성 안내
    # -----------------------------------------------------
    st.divider()

    st.subheader(
        "🔊 음성 안내"
    )

    st.info(
        result["voice_text"]
    )

    components.html(
        음성버튼HTML(result["voice_text"]),
        height=68,
        scrolling=False,
    )


# =========================================================
# 하단 안내
# =========================================================
st.caption(
    "※ 수도권 지하철 데이터 기준이며, 실제 열차 운행 상황·급행·막차 정보는 반영되지 않을 수 있어."
)
