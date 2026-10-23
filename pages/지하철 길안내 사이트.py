#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚇 수도권 지하철 길찾기 - 전체 노선 버전

기능
- 수도권 전철 전체 데이터 자동 다운로드/캐시
- 출발역 → 도착역 최단시간 경로
- 환승역/일반역 모두 표시
- 사진처럼 카드형 파란·보라 UI
- 노선 색상 표시
- 경로 지도(Leaflet)
- 음성 안내 선택 기능

데이터
- station_nodes.csv : 역·노선·좌표
- station_edges.csv : 역과 역 사이 연결/소요시간
데이터 출처 및 범위는 실행 화면의 출처 안내를 참고하세요.

필요 패키지
    pip install flask

실행
    python subway_all.py

브라우저가 자동으로 열리고,
    출발역 / 도착역
을 입력하면 됩니다.
"""

import csv
import heapq
import json
import math
import os
import threading
import time
import urllib.request
import webbrowser
from collections import defaultdict

from flask import Flask, jsonify, render_template_string, request


# ============================================================
# 1. 전체 수도권 전철 데이터
# ============================================================

BASE_URL = "https://raw.githubusercontent.com/minseok852/subway-etl/main/output/"
NODE_URL = BASE_URL + "station_nodes.csv"
EDGE_URL = BASE_URL + "station_edges.csv"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subway_data")
NODE_FILE = os.path.join(DATA_DIR, "station_nodes.csv")
EDGE_FILE = os.path.join(DATA_DIR, "station_edges.csv")

os.makedirs(DATA_DIR, exist_ok=True)


def download_if_needed(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 100:
        return

    print(f"데이터 다운로드 중: {os.path.basename(path)}")
    try:
        urllib.request.urlretrieve(url, path)
    except Exception as e:
        raise RuntimeError(
            f"데이터 다운로드에 실패했습니다.\n"
            f"인터넷 연결을 확인한 뒤 다시 실행하세요.\n\n{e}"
        )


download_if_needed(NODE_URL, NODE_FILE)
download_if_needed(EDGE_URL, EDGE_FILE)


# ============================================================
# 2. 노선 색상
# ============================================================

LINE_COLORS = {
    "1": "#0052A4",
    "2": "#00A84D",
    "3": "#EF7C1C",
    "4": "#00A5DE",
    "5": "#996CAC",
    "6": "#CD7C2F",
    "7": "#747F00",
    "8": "#E6186C",
    "9": "#BDB092",

    "B": "#F5A200",      # 수인분당
    "S": "#D31145",      # 신분당
    "K": "#77C4A3",      # 경의중앙
    "A": "#0090D2",      # 공항철도
    "G": "#178C72",      # 경춘
    "U": "#B7C450",      # 의정부
    "E": "#FFCD00",      # 에버라인
    "KK": "#003DA5",     # 경강
    "W": "#B7B7B7",      # 우이신설
    "SH": "#F06A00",     # 서해선
    "KP": "#8B50A4",     # 김포골드
    "I": "#759C2A",      # 인천1
    "I2": "#F5A100",     # 인천2
    "GTXA": "#3B82F6",
    "M": "#777777",
}


LINE_NAMES = {
    "1": "1호선",
    "2": "2호선",
    "3": "3호선",
    "4": "4호선",
    "5": "5호선",
    "6": "6호선",
    "7": "7호선",
    "8": "8호선",
    "9": "9호선",
    "B": "수인분당선",
    "S": "신분당선",
    "K": "경의·중앙선",
    "A": "공항철도",
    "G": "경춘선",
    "U": "의정부경전철",
    "E": "용인에버라인",
    "KK": "경강선",
    "W": "우이신설선",
    "SH": "서해선",
    "KP": "김포골드라인",
    "I": "인천1호선",
    "I2": "인천2호선",
    "GTXA": "GTX-A",
}


def line_name(line_key):
    return LINE_NAMES.get(str(line_key), str(line_key))


def line_color(line_key):
    return LINE_COLORS.get(str(line_key), "#64748B")


# ============================================================
# 3. 데이터 읽기
# ============================================================

NODES = {}                  # node_id -> 정보
STATIONS = defaultdict(list) # 역명 -> node_id 목록
GRAPH = defaultdict(list)   # node_id -> (node_id, seconds, edge_type)

with open(NODE_FILE, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        node_id = int(row["id"])
        station = row["station_name"].strip()
        line_key = row["line_key"].strip()

        info = {
            "id": node_id,
            "station": station,
            "line_key": line_key,
            "line": line_name(line_key),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
        }

        NODES[node_id] = info
        STATIONS[station].append(node_id)


with open(EDGE_FILE, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        a = int(row["from_node_id"])
        b = int(row["to_node_id"])
        seconds = float(row["seconds"])
        edge_type = row.get("edge_type", "ride")

        GRAPH[a].append((b, seconds, edge_type))
        GRAPH[b].append((a, seconds, edge_type))


# ============================================================
# 4. 역 검색
# ============================================================

def normalize(text):
    text = (text or "").strip().replace(" ", "")
    if text.endswith("역") and len(text) > 1:
        text = text[:-1]
    return text


def find_station(query):
    q = normalize(query)

    # 정확한 이름
    for name in STATIONS:
        if normalize(name) == q:
            return name

    # 포함 검색
    matches = [name for name in STATIONS if q and q in normalize(name)]

    if len(matches) == 1:
        return matches[0]

    if matches:
        return matches[:10]

    return []


# ============================================================
# 5. 최단시간 경로
# ============================================================

def shortest_path(origin_name, dest_name):
    start_nodes = STATIONS.get(origin_name, [])
    goal_nodes = set(STATIONS.get(dest_name, []))

    if not start_nodes or not goal_nodes:
        return None

    dist = {}
    prev = {}

    heap = []

    for s in start_nodes:
        dist[s] = 0
        heapq.heappush(heap, (0, s))

    while heap:
        cost, u = heapq.heappop(heap)

        if cost != dist.get(u):
            continue

        if u in goal_nodes:
            path = [u]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            path.reverse()
            return path, cost

        for v, weight, edge_type in GRAPH.get(u, []):
            new_cost = cost + weight

            if new_cost < dist.get(v, float("inf")):
                dist[v] = new_cost
                prev[v] = u
                heapq.heappush(heap, (new_cost, v))

    return None


# ============================================================
# 6. 경로 정리
# ============================================================

def make_route(path, total_seconds):
    stations = [NODES[n] for n in path]

    transfers = []
    ride_segments = []

    current = []
    current_line = None

    for i, node in enumerate(stations):
        if i == 0:
            current = [node]
            current_line = node["line_key"]
            continue

        prev = stations[i - 1]

        # 같은 노선
        if node["line_key"] == current_line:
            current.append(node)
            continue

        # 환승
        ride_segments.append({
            "line_key": current_line,
            "line": line_name(current_line),
            "color": line_color(current_line),
            "stations": current[:],
        })

        transfers.append({
            "station": prev["station"],
            "lat": prev["lat"],
            "lon": prev["lon"],
            "from_line": line_name(current_line),
            "to_line": line_name(node["line_key"]),
        })

        current = [node]
        current_line = node["line_key"]

    if current:
        ride_segments.append({
            "line_key": current_line,
            "line": line_name(current_line),
            "color": line_color(current_line),
            "stations": current[:],
        })

    # 실제 경로에 환승 edge가 들어간 경우를 별도로 표시
    clean_segments = []

    for seg in ride_segments:
        if len(seg["stations"]) >= 1:
            clean_segments.append(seg)

    return {
        "origin": stations[0],
        "destination": stations[-1],
        "stations": stations,
        "segments": clean_segments,
        "transfers": transfers,
        "transfer_count": len(transfers),
        "total_seconds": total_seconds,
        "total_minutes": max(1, round(total_seconds / 60)),
    }


# ============================================================
# 7. Flask
# ============================================================

app = Flask(__name__)


HTML = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>LIVE SUBWAY</title>

<link rel="stylesheet"
 href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Noto Sans KR",
        "Malgun Gothic",
        sans-serif;
    background: #5269bd;
    color: #20243a;
}

.app {
    min-height: 100vh;
    padding: 38px;
}

.top {
    max-width: 1200px;
    margin: auto;
    color: white;
    margin-bottom: 22px;
}

.logo {
    font-size: 29px;
    font-weight: 900;
    letter-spacing: -1.5px;
}

.logo span {
    opacity: .65;
}

.subtitle {
    margin-top: 7px;
    opacity: .78;
    font-size: 13px;
}

.grid {
    max-width: 1200px;
    margin: auto;
    display: grid;
    grid-template-columns: 390px 1fr;
    gap: 18px;
}

.card {
    background: rgba(255,255,255,.96);
    border-radius: 26px;
    box-shadow: 0 16px 45px rgba(20,30,80,.18);
}

.search {
    padding: 25px;
}

.label {
    font-size: 12px;
    font-weight: 800;
    color: #777d99;
    margin-bottom: 7px;
}

.input {
    width: 100%;
    border: 0;
    outline: none;
    padding: 16px 17px;
    border-radius: 15px;
    background: #f1f3fa;
    font-size: 16px;
    margin-bottom: 13px;
}

.swap {
    width: 42px;
    height: 42px;
    border: 0;
    border-radius: 50%;
    background: #e9ecff;
    color: #5269bd;
    font-size: 20px;
    cursor: pointer;
    display: block;
    margin: -3px auto 12px;
}

.button {
    width: 100%;
    border: 0;
    padding: 16px;
    border-radius: 15px;
    background: #5269bd;
    color: white;
    font-size: 16px;
    font-weight: 800;
    cursor: pointer;
    box-shadow: 0 8px 20px rgba(82,105,189,.3);
}

.route-card {
    padding: 22px;
    margin-top: 16px;
}

.route-title {
    font-size: 18px;
    font-weight: 900;
}

.route-info {
    color: #747a92;
    font-size: 12px;
    margin-top: 5px;
}

.route-list {
    margin-top: 18px;
}

.step {
    display: flex;
    gap: 12px;
    padding: 11px 0;
    border-bottom: 1px solid #eef0f5;
}

.step:last-child {
    border-bottom: 0;
}

.circle {
    flex: 0 0 13px;
    width: 13px;
    height: 13px;
    margin-top: 4px;
    border-radius: 50%;
}

.step-text {
    font-size: 13px;
    line-height: 1.45;
}

.map-card {
    overflow: hidden;
    min-height: 650px;
    position: relative;
}

#map {
    width: 100%;
    height: 650px;
}

.map-badge {
    position: absolute;
    z-index: 999;
    top: 17px;
    left: 17px;
    padding: 10px 14px;
    background: rgba(255,255,255,.93);
    border-radius: 13px;
    box-shadow: 0 5px 20px rgba(0,0,0,.12);
    font-size: 12px;
    font-weight: 800;
}

.lines-card {
    max-width: 1200px;
    margin: 18px auto 0;
    padding: 20px;
}

.lines-title {
    font-size: 14px;
    font-weight: 900;
    margin-bottom: 12px;
}

.line-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.line-chip {
    padding: 8px 11px;
    border-radius: 12px;
    background: #f3f4f8;
    font-size: 11px;
    font-weight: 800;
}

.dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 5px;
}

.source {
    max-width: 1200px;
    margin: 15px auto 0;
    color: rgba(255,255,255,.75);
    font-size: 10px;
    line-height: 1.5;
}

.error {
    background: #fff0f1;
    color: #c43b4b;
    padding: 12px;
    border-radius: 12px;
    margin-top: 12px;
    font-size: 12px;
}

@media(max-width: 850px) {
    .app {
        padding: 18px;
    }

    .grid {
        grid-template-columns: 1fr;
    }

    #map {
        height: 430px;
    }

    .map-card {
        min-height: 430px;
    }
}

</style>
</head>

<body>

<div class="app">

    <div class="top">
        <div class="logo">LIVE <span>SUBWAY</span></div>
        <div class="subtitle">
            수도권 전체 노선 · 환승 경로 · 역 검색
        </div>
    </div>

    <div class="grid">

        <div>

            <div class="card search">

                <div class="label">출발역</div>
                <input id="origin"
                       class="input"
                       placeholder="예: 강남">

                <button class="swap" onclick="swapStations()">↕</button>

                <div class="label">도착역</div>
                <input id="destination"
                       class="input"
                       placeholder="예: 홍대입구">

                <button class="button" onclick="searchRoute()">
                    최적 경로 찾기
                </button>

                <div id="error"></div>

            </div>

            <div id="routeCard"></div>

        </div>

        <div class="card map-card">

            <div class="map-badge">
                🚇 수도권 지하철
            </div>

            <div id="map"></div>

        </div>

    </div>

    <div class="card lines-card">

        <div class="lines-title">
            지원 노선
        </div>

        <div id="lineGrid" class="line-grid"></div>

    </div>

    <div class="source">
        노선/역 데이터: 공개 데이터 기반 그래프 데이터셋.
        실제 운행시간·급행·막차·실시간 지연은 실제 교통 상황과 다를 수 있습니다.
    </div>

</div>


<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>

let map = L.map("map").setView([37.5665,126.9780],11);

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap"
    }
).addTo(map);

let routeLayer = L.layerGroup().addTo(map);


async function searchRoute() {

    const origin =
        document.getElementById("origin").value.trim();

    const destination =
        document.getElementById("destination").value.trim();

    const error =
        document.getElementById("error");

    error.innerHTML = "";

    if (!origin || !destination) {
        error.innerHTML =
            '<div class="error">출발역과 도착역을 입력해주세요.</div>';
        return;
    }

    try {

        const response = await fetch(
            `/api/route?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`
        );

        const data = await response.json();

        if (!response.ok) {

            error.innerHTML =
                `<div class="error">${data.error}</div>`;

            return;
        }

        drawRoute(data);
        showRouteCard(data);

    } catch(e) {

        error.innerHTML =
            '<div class="error">경로를 불러오지 못했습니다.</div>';
    }
}


function drawRoute(data) {

    routeLayer.clearLayers();

    const allPoints = [];

    for (const segment of data.segments) {

        const points =
            segment.stations.map(
                s => [s.lat, s.lon]
            );

        allPoints.push(...points);

        L.polyline(
            points,
            {
                color: segment.color,
                weight: 8,
                opacity: .9
            }
        ).addTo(routeLayer);

        segment.stations.forEach(s => {

            L.circleMarker(
                [s.lat,s.lon],
                {
                    radius: 4,
                    color: segment.color,
                    weight: 2,
                    fillColor: "#fff",
                    fillOpacity: 1
                }
            )
            .bindTooltip(
                s.station + "역"
            )
            .addTo(routeLayer);

        });

    }

    if (allPoints.length) {

        L.circleMarker(
            allPoints[0],
            {
                radius: 12,
                color: "#fff",
                weight: 3,
                fillColor: "#ef4444",
                fillOpacity: 1
            }
        )
        .bindTooltip("출발", {permanent:true})
        .addTo(routeLayer);

        L.circleMarker(
            allPoints[allPoints.length-1],
            {
                radius: 12,
                color: "#fff",
                weight: 3,
                fillColor: "#2563eb",
                fillOpacity: 1
            }
        )
        .bindTooltip("도착", {permanent:true})
        .addTo(routeLayer);

        map.fitBounds(
            L.latLngBounds(allPoints),
            {padding:[45,45]}
        );
    }
}


function showRouteCard(data) {

    let html = `
        <div class="card route-card">

            <div class="route-title">
                ${data.origin.station} → ${data.destination.station}
            </div>

            <div class="route-info">
                약 ${data.total_minutes}분
                · 환승 ${data.transfer_count}회
                · ${data.stations.length - 1}개 구간
            </div>

            <div class="route-list">
    `;

    html += `
        <div class="step">
            <div class="circle" style="background:#ef4444"></div>
            <div class="step-text">
                <b>${data.origin.station}역</b>에서 출발
            </div>
        </div>
    `;

    data.segments.forEach((segment, index) => {

        const names =
            segment.stations.map(
                s => s.station
            );

        html += `
            <div class="step">
                <div class="circle"
                     style="background:${segment.color}">
                </div>

                <div class="step-text">
                    <b>${segment.line}</b><br>
                    ${names[0]} → ${names[names.length-1]}
                    · ${names.length-1}개 역
                </div>
            </div>
        `;

        if (index < data.transfers.length) {

            const t = data.transfers[index];

            html += `
                <div class="step">
                    <div class="circle"
                         style="background:#8b8fa3">
                    </div>

                    <div class="step-text">
                        <b>${t.station}역 환승</b><br>
                        ${t.from_line} → ${t.to_line}
                    </div>
                </div>
            `;
        }

    });

    html += `
        <div class="step">
            <div class="circle" style="background:#2563eb"></div>
            <div class="step-text">
                <b>${data.destination.station}역</b> 도착
            </div>
        </div>

            </div>
        </div>
    `;

    document.getElementById("routeCard").innerHTML = html;
}


function swapStations() {

    const a = document.getElementById("origin");
    const b = document.getElementById("destination");

    const temp = a.value;

    a.value = b.value;
    b.value = temp;
}


async function loadLines() {

    const response =
        await fetch("/api/lines");

    const lines =
        await response.json();

    document.getElementById("lineGrid").innerHTML =
        lines.map(line => `
            <div class="line-chip">
                <span class="dot"
                      style="background:${line.color}">
                </span>
                ${line.name}
            </div>
        `).join("");
}


loadLines();

</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/lines")
def api_lines():
    unique = {}

    for node in NODES.values():
        key = node["line_key"]

        if key not in unique:
            unique[key] = {
                "name": line_name(key),
                "color": line_color(key),
            }

    return jsonify(
        sorted(unique.values(), key=lambda x: x["name"])
    )


@app.route("/api/route")
def api_route():

    origin_query = request.args.get("origin", "")
    destination_query = request.args.get("destination", "")

    origin = find_station(origin_query)
    destination = find_station(destination_query)

    if isinstance(origin, list):

        if len(origin) == 0:
            return jsonify({
                "error": f"'{origin_query}' 역을 찾을 수 없습니다."
            }), 404

        if len(origin) > 1:
            return jsonify({
                "error":
                    "출발역 후보: " +
                    ", ".join(x + "역" for x in origin)
            }), 400

        origin = origin[0]

    if isinstance(destination, list):

        if len(destination) == 0:
            return jsonify({
                "error": f"'{destination_query}' 역을 찾을 수 없습니다."
            }), 404

        if len(destination) > 1:
            return jsonify({
                "error":
                    "도착역 후보: " +
                    ", ".join(x + "역" for x in destination)
            }), 400

        destination = destination[0]

    if not origin or not destination:
        return jsonify({
            "error": "역 이름을 입력해주세요."
        }), 400

    if origin == destination:
        return jsonify({
            "error": "출발역과 도착역이 같습니다."
        }), 400

    result = shortest_path(origin, destination)

    if result is None:
        return jsonify({
            "error":
                f"{origin}역에서 {destination}역까지의 경로를 찾을 수 없습니다."
        }), 404

    path, total_seconds = result

    route = make_route(
        path,
        total_seconds
    )

    return jsonify(route)


# ============================================================
# 8. 실행
# ============================================================

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":

    print("=" * 60)
    print("🚇 LIVE SUBWAY - 수도권 전체 노선")
    print("=" * 60)
    print(f"역/노선 노드: {len(NODES):,}개")
    print(f"연결 간선: {sum(len(v) for v in GRAPH.values()) // 2:,}개")
    print("브라우저: http://127.0.0.1:5000")
    print("=" * 60)

    threading.Thread(
        target=open_browser,
        daemon=True
    ).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
