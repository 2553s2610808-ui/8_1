
    st.divider()
    st.subheader("📍 현재 위치에서 역까지 안내")
    st.write(f"목적지: **{station_label(destination)}**")

    st.caption(
        "위치 확인 버튼을 누르고 브라우저의 위치 권한을 허용해주세요."
    )

    try:
        location = streamlit_geolocation()

        if isinstance(location, dict):
            latitude = location.get("latitude")
            longitude = location.get("longitude")

            if latitude is not None and longitude is not None:
                latitude = float(latitude)
                longitude = float(longitude)

                if (
                    -90 <= latitude <= 90
                    and -180 <= longitude <= 180
                ):
                    st.success("현재 위치를 확인했습니다.")

                    st.write(
                        f"위치 좌표: {latitude:.5f}, {longitude:.5f}"
                    )

                    import urllib.parse

                    destination_query = urllib.parse.quote(
                        station_label(destination) + ", 대한민국"
                    )

                    walking_url = (
                        "https://www.google.com/maps/dir/?api=1"
                        f"&origin={latitude},{longitude}"
                        f"&destination={destination_query}"
                        "&travelmode=walking"
                    )

                    transit_url = (
                        "https://www.google.com/maps/dir/?api=1"
                        f"&origin={latitude},{longitude}"
                        f"&destination={destination_query}"
                        "&travelmode=transit"
                    )

                    st.link_button(
                        "🚶 역까지 도보 길 안내",
                        walking_url,
                        use_container_width=True,
                    )

                    st.link_button(
                        "🚇 대중교통 경로 안내",
                        transit_url,
                        use_container_width=True,
                    )
                else:
                    st.error("위치 좌표가 올바르지 않습니다.")
            else:
                st.info(
                    "위치 정보가 아직 없습니다. 위치 확인 버튼을 누르고 "
                    "브라우저의 위치 권한을 허용해주세요."
                )
        else:
            st.info("브라우저에서 위치를 확인한 후 다시 시도해주세요.")

    except Exception:
        st.error(
            "현재 위치를 확인하지 못했습니다. "
            "HTTPS 접속 여부와 브라우저 위치 권한을 확인해주세요."
        )
