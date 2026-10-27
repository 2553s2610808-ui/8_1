def 역표시(node, 역정보):
    정보 = 역정보.get(str(node))

    if not 정보:
        return "역 이름을 불러오지 못했습니다."

    이름 = str(정보.get("name", "")).strip()

    # 역 이름 대신 숫자 코드가 들어온 경우
    if not 이름 or 이름.isdigit():
        return "역 이름을 확인할 수 없습니다."

    if 이름 == "서울":
        return "서울역"

    if 이름 == "이수(총신대입구)":
        return 이름

    if 이름.endswith("역"):
        return 이름

    return 이름 + "역"
