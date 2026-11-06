import heapq
import html as html_lib
import json
import math
import re
from io import StringIO

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="BLUE ROUTE | 지하철 길찾기",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

STATION_URL = (
    "https://raw.githubusercontent.com/"
    "minseok852/subway-etl/main/output/station_nodes.csv"
)
EDGE_URL = (
    "https://raw.githubusercontent.com/"
    "minseok852/subway-etl/main/output/station_edges.csv"
)

HEADERS = {"User-Agent": "BlueRoute-Streamlit/1.0"}

LINE_NAMES = {
    "1": "1호선", "2": "2호선", "3": "3호선", "4": "4호선",
    "5": "5호선", "6": "6호선", "7": "7호선", "8": "8호선",
    "9": "9호선", "B": "수인분당선", "S": "신분당선",
    "K": "경의·중앙선", "A": "공항철도", "G": "경춘선",
    "U": "의정부경전철", "E": "용인에버라인", "KK": "경강선",
    "W": "우이신설선", "SH": "서해선", "KP": "김포골드라인",
    "I": "인천1호선", "I2": "인천2호선", "GTXA": "GTX-A",
    "N": "신림선", "M": "인천공항 자기부상철도",
}

LINE_COLORS = {
    "1": "#0052A4", "2": "#00A84D", "3": "#EF7C1C",
    "4": "#00A5DE", "5": "#996CAC", "6": "#CD7C2F",
    "7": "#747F00", "8": "#E6186C", "9": "#BDB092",
    "B": "#F5A200", "S": "#D31145", "K": "#77C4A3",
    "A": "#0090D2", "G": "#178C72", "U": "#B7C450",
    "E": "#FFCD00", "KK": "#003DA5", "W": "#B7B7B7",
    "SH": "#F06A00", "KP": "#8B50A4", "I": "#759C2A",
    "I2": "#F5A100", "GTXA": "#3B82F6", "N": "#B0CE18",
    "M": "#777777", "인천국제공항선": "#0090D2",
    "수인분당선": "#F5A200", "신분당선": "#D31145",
    "경의·중앙선": "#77C4A3", "경춘선": "#178C72",
    "용인에버라인": "#FFCD00", "경강선": "#003DA5",
    "우이신설선": "#B7B7B7", "서해선": "#F06A00",
    "김포골드라인": "#8B50A4", "인천지하철 1호선": "#759C2A",
    "인천지하철 2호선": "#F5A100", "자기부상철도": "#777777",
    "GTX-A": "#3B82F6", "신림선": "#B0CE18",
}


def 노선이름(line_key):
    key = str(line_key).strip()
    return LINE_NAMES.get(key, key)


def 노선색(line_key):
    return LINE_COLORS.get(
        str(line_key).strip(),
        "#2563EB"
    )


# =========================================================
# 화면 디자인
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            180deg,
            #F2F7FF 0%,
            #F8FBFF 100%
        );
        color: #172554;
    }

    .block-container {
        max-width: 1050px;
        padding-top: 28px;
        padding-bottom: 48px;
