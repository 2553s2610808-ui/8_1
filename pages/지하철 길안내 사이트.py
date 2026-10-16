#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
지하철 길안내 시스템
====================
출발역과 도착역을 입력하면
  1) 최단 시간 경로 (환승 포함)를 계산하고
  2) 단계별 안내를 화면에 출력하며
  3) 지도(HTML, Leaflet)를 브라우저로 열어 경로를 보여주고
  4) 음성(TTS)으로 안내합니다.

사용법
------
  python "지하철 길안내 시스템.py"                 # 실행 후 직접 입력
  python "지하철 길안내 시스템.py" 홍대입구 강남     # 바로 안내
  python "지하철 길안내 시스템.py" 홍대입구 강남 --no-voice --no-map

음성 사용을 위한 선택 설치 (둘 중 하나, 없으면 음성만 건너뜀)
  pip install gTTS        # 인터넷 필요, 한국어 품질 좋음
  pip install pyttsx3     # 오프라인 (OS에 한국어 음성이 설치되어 있어야 함)
  (macOS는 기본 내장 `say` 명령으로도 동작)

※ 지도 화면은 브라우저가 인터넷에서 지도 타일을 불러옵니다.
※ 내장 데이터는 서울 주요 구간 일부(1~5호선)이며 좌표/소요시간은 근사값입니다.
   실제 운행·막차 시간은 공식 앱을 확인하세요.
"""

import argparse
import difflib
import heapq
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import webbrowser

# ─────────────────────────────────────────────────────────────
# 1. 노선 데이터 (역명, 위도, 경도)
# ─────────────────────────────────────────────────────────────
LINES = {
    "1호선": {
        "color": "#0052A4",
        "loop": False,
        "fwd": "구로·인천 방면",
        "bwd": "청량리·소요산 방면",
        "stations": [
            ("청량리", 37.5800, 127.0469), ("제기동", 37.5782, 127.0348),
            ("신설동", 37.5757, 127.0247), ("동묘앞", 37.5727, 127.0166),
            ("동대문", 37.5711, 127.0117), ("종로5가", 37.5710, 127.0019),
            ("종로3가", 37.5704, 126.9921), ("종각", 37.5702, 126.9831),
            ("시청", 37.5657, 126.9769), ("서울역", 37.5547, 126.9707),
            ("남영", 37.5410, 126.9713), ("용산", 37.5299, 126.9647),
            ("노량진", 37.5135, 126.9424), ("대방", 37.5133, 126.9264),
            ("신길", 37.5170, 126.9174), ("영등포", 37.5159, 126.9073),
            ("신도림", 37.5088, 126.8913), ("구로", 37.5030, 126.8819),
        ],
    },
    "2호선": {
        "color": "#00A84D",
        "loop": True,
        "fwd": "외선순환",
        "bwd": "내선순환",
        "stations": [
            ("시청", 37.5657, 126.9769), ("을지로입구", 37.5660, 126.9822),
            ("을지로3가", 37.5663, 126.9917), ("을지로4가", 37.5667, 126.9978),
            ("동대문역사문화공원", 37.5651, 127.0079), ("신당", 37.5658, 127.0196),
            ("상왕십리", 37.5644, 127.0293), ("왕십리", 37.5612, 127.0371),
            ("한양대", 37.5555, 127.0437), ("뚝섬", 37.5474, 127.0473),
            ("성수", 37.5446, 127.0560), ("건대입구", 37.5404, 127.0693),
            ("구의", 37.5370, 127.0858), ("강변", 37.5351, 127.0945),
            ("잠실나루", 37.5207, 127.1037), ("잠실", 37.5133, 127.1001),
            ("잠실새내", 37.5115, 127.0860), ("종합운동장", 37.5109, 127.0736),
            ("삼성", 37.5088, 127.0631), ("선릉", 37.5045, 127.0490),
            ("역삼", 37.5006, 127.0364), ("강남", 37.4979, 127.0276),
            ("교대", 37.4934, 127.0140), ("서초", 37.4916, 127.0078),
            ("방배", 37.4814, 126.9976), ("사당", 37.4766, 126.9816),
            ("낙성대", 37.4769, 126.9637), ("서울대입구", 37.4813, 126.9527),
            ("봉천", 37.4824, 126.9417), ("신림", 37.4842, 126.9296),
            ("신대방", 37.4875, 126.9131), ("구로디지털단지", 37.4852, 126.9015),
            ("대림", 37.4930, 126.8952), ("신도림", 37.5088, 126.8913),
            ("문래", 37.5173, 126.8946), ("영등포구청", 37.5249, 126.8964),
            ("당산", 37.5348, 126.9025), ("합정", 37.5495, 126.9139),
            ("홍대입구", 37.5571, 126.9245), ("신촌", 37.5551, 126.9367),
            ("이대", 37.5568, 126.9464), ("아현", 37.5576, 126.9561),
            ("충정로", 37.5599, 126.9637),
        ],
    },
    "3호선": {
        "color": "#EF7C1C",
        "loop": False,
        "fwd": "수서·오금 방면",
        "bwd": "대화 방면",
        "stations": [
            ("연신내", 37.6190, 126.9211), ("불광", 37.6103, 126.9300),
            ("녹번", 37.6004, 126.9358), ("홍제", 37.5890, 126.9437),
            ("무악재", 37.5826, 126.9500), ("독립문", 37.5745, 126.9577),
            ("경복궁", 37.5759, 126.9735), ("안국", 37.5765, 126.9854),
            ("종로3가", 37.5704, 126.9921), ("을지로3가", 37.5663, 126.9917),
            ("충무로", 37.5612, 126.9942), ("동대입구", 37.5589, 127.0050),
            ("약수", 37.5543, 127.0108), ("금호", 37.5481, 127.0158),
            ("옥수", 37.5404, 127.0178), ("압구정", 37.5271, 127.0285),
            ("신사", 37.5164, 127.0203), ("잠원", 37.5113, 127.0113),
            ("고속터미널", 37.5049, 127.0049), ("교대", 37.4934, 127.0140),
            ("남부터미널", 37.4850, 127.0162), ("양재", 37.4845, 127.0344),
            ("매봉", 37.4871, 127.0468), ("도곡", 37.4909, 127.0553),
            ("대치", 37.4946, 127.0638), ("학여울", 37.4967, 127.0709),
            ("대청", 37.4934, 127.0794), ("일원", 37.4837, 127.0863),
            ("수서", 37.4876, 127.1018),
        ],
    },
    "4호선": {
        "color": "#00A5DE",
        "loop": False,
        "fwd": "사당·오이도 방면",
        "bwd": "당고개 방면",
        "stations": [
            ("길음", 37.6033, 127.0250), ("성신여대입구", 37.5927, 127.0165),
            ("한성대입구", 37.5883, 127.0063), ("혜화", 37.5822, 127.0018),
            ("동대문", 37.5711, 127.0117),
            ("동대문역사문화공원", 37.5651, 127.0079),
            ("충무로", 37.5612, 126.9942), ("명동", 37.5609, 126.9863),
            ("회현", 37.5588, 126.9780), ("서울역", 37.5547, 126.9707),
            ("숙대입구", 37.5446, 126.9721), ("삼각지", 37.5347, 126.9731),
            ("신용산", 37.5292, 126.9677), ("이촌", 37.5223, 126.9739),
            ("동작", 37.5027, 126.9802), ("총신대입구", 37.4865, 126.9817),
            ("사당", 37.4766, 126.9816),
        ],
    },
    "5호선": {
        "color": "#996CAC",
        "loop": False,
        "fwd": "하남검단산 방면",
        "bwd": "방화 방면",
        "stations": [
            ("영등포구청", 37.5249, 126.8964), ("영등포시장", 37.5226, 126.9055),
            ("신길", 37.5170, 126.9174), ("여의도", 37.5216, 126.9243),
            ("여의나루", 37.5271, 126.9328), ("마포", 37.5396, 126.9460),
            ("공덕", 37.5440, 126.9516), ("애오개", 37.5535, 126.9566),
            ("충정로", 37.5599, 126.9637), ("서대문", 37.5658, 126.9667),
            ("광화문", 37.5710, 126.9768), ("종로3가", 37.5704, 126.9921),
            ("을지로4가", 37.5667, 126.9978),
            ("동대문역사문화공원", 37.5651, 127.0079),
            ("청구", 37.5603, 127.0139), ("신금호", 37.5545, 127.0207),
            ("행당", 37.5574, 127.0292), ("왕십리", 37.5612, 127.0371),
            ("마장", 37.5661, 127.0430), ("답십리", 37.5669, 127.0526),
            ("장한평", 37.5614, 127.0645), ("군자", 37.5571, 127.0795),
            ("아차산", 37.5516, 127.0896), ("광나루", 37.5455, 127.1031),
            ("천호", 37.5385, 127.1236), ("강동", 37.5359, 127.1325),
        ],
    },
}

AVG_SPEED_KMH = 40.0     # 평균 운행 속도 (정차 제외)
DWELL_MIN = 0.6          # 역당 정차/가감속 시간(분)
TRANSFER_MIN = 4.0       # 환승 소요 시간(분)

# ─────────────────────────────────────────────────────────────
# 2. 그래프 구성
# ─────────────────────────────────────────────────────────────
COORDS = {}              # 역명 -> (lat, lon)
LINE_INDEX = {}          # 호선 -> {역명: 순번}
for _ln, _info in LINES.items():
    LINE_INDEX[_ln] = {}
    for _i, (_name, _lat, _lon) in enumerate(_info["stations"]):
        COORDS.setdefault(_name, (_lat, _lon))
        LINE_INDEX[_ln][_name] = _i


def haversine_km(a, b):
    r = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dphi = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def build_graph():
    """노드 = (역명, 호선). 같은 호선 인접역 + 같은 역의 호선 간 환승."""
    graph = {}

    def add(u, v, w):
        graph.setdefault(u, []).append((v, w))
        graph.setdefault(v, []).append((u, w))

    by_station = {}
    for ln, info in LINES.items():
        names = [s[0] for s in info["stations"]]
        pairs = list(zip(names, names[1:]))
        if info["loop"]:
            pairs.append((names[-1], names[0]))
        for a, b in pairs:
            minutes = haversine_km(COORDS[a], COORDS[b]) / AVG_SPEED_KMH * 60 + DWELL_MIN
            add((a, ln), (b, ln), minutes)
        for n in names:
            by_station.setdefault(n, []).append(ln)

    for name, lns in by_station.items():
        for i in range(len(lns)):
            for j in range(i + 1, len(lns)):
                add((name, lns[i]), (name, lns[j]), TRANSFER_MIN)
    return graph, by_station


GRAPH, BY_STATION = build_graph()


def shortest_path(origin, dest):
    starts = [(origin, ln) for ln in BY_STATION[origin]]
    goals = {(dest, ln) for ln in BY_STATION[dest]}
    dist = {s: 0.0 for s in starts}
    prev = {}
    heap = [(0.0, s) for s in starts]
    heapq.heapify(heap)
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, math.inf):
            continue
        if u in goals:
            path = [u]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return list(reversed(path)), d
        for v, w in GRAPH[u]:
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    return None, math.inf


# ─────────────────────────────────────────────────────────────
# 3. 경로 → 안내 단계
# ─────────────────────────────────────────────────────────────
def split_segments(path):
    """경로를 호선별 탑승 구간으로 분리. 환승 노드(같은 역, 다른 호선)는 구간 경계."""
    segments = []
    cur = [path[0]]
    for node in path[1:]:
        if node[1] == cur[-1][1]:
            cur.append(node)
        else:
            segments.append(cur)
            cur = [node]
    segments.append(cur)
    return [s for s in segments if len(s) >= 2] or segments


def direction_label(line, stations):
    info = LINES[line]
    idx = LINE_INDEX[line]
    a, b = idx[stations[0]], idx[stations[1]]
    if info["loop"]:
        n = len(info["stations"])
        forward = (b - a) % n == 1
    else:
        forward = b > a
    return info["fwd"] if forward else info["bwd"]


def segment_minutes(seg):
    total = 0.0
    for a, b in zip(seg, seg[1:]):
        total += haversine_km(COORDS[a[0]], COORDS[b[0]]) / AVG_SPEED_KMH * 60 + DWELL_MIN
    return total


def build_guidance(origin, dest, path, total_min):
    segments = split_segments(path)
    steps = []
    transfers = len(segments) - 1

    steps.append(f"{origin}역에서 출발합니다.")
    for i, seg in enumerate(segments):
        line = seg[0][1]
        names = [n for n, _ in seg]
        n_stops = len(names) - 1
        label = direction_label(line, names)
        mins = max(1, round(segment_minutes(seg)))
        steps.append(
            f"{line} {label} 열차를 타세요. "
            f"{n_stops}개 역을 이동해 {names[-1]}역에서 내립니다. 약 {mins}분 걸립니다."
        )
        if i < len(segments) - 1:
            nxt = segments[i + 1][0][1]
            steps.append(f"{names[-1]}역에서 {nxt}으로 환승하세요.")
    steps.append(
        f"{dest}역에 도착했습니다. 총 {round(total_min)}분 정도 걸리며, "
        f"환승은 {transfers}회입니다."
    )
    return steps, segments, transfers


# ─────────────────────────────────────────────────────────────
# 4. 지도 (Leaflet HTML)
# ─────────────────────────────────────────────────────────────
MAP_TEMPLATE = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>지하철 길안내: __TITLE__</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html,body{height:100%;margin:0;font-family:-apple-system,"Malgun Gothic",sans-serif}
  #wrap{display:flex;height:100%}
  #side{width:340px;max-width:40%;overflow:auto;padding:16px;box-sizing:border-box;
        background:#fafafa;border-right:1px solid #ddd}
  #map{flex:1}
  h1{font-size:18px;margin:0 0 4px}
  .sub{color:#666;font-size:13px;margin-bottom:14px}
  .step{display:flex;gap:10px;margin:0 0 12px;font-size:14px;line-height:1.45}
  .dot{flex:none;width:12px;height:12px;border-radius:50%;margin-top:4px}
  @media(max-width:700px){#wrap{flex-direction:column-reverse}
    #side{width:auto;max-width:none;height:45%;border-right:0;border-top:1px solid #ddd}}
</style></head>
<body><div id="wrap">
<div id="side"></div><div id="map"></div></div>
<script>
const DATA = __DATA__;
const map = L.map('map');
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {maxZoom:19, attribution:'&copy; OpenStreetMap'}).addTo(map);

const all = [];
DATA.segments.forEach(seg=>{
  const pts = seg.stations.map(s=>[s.lat,s.lon]);
  all.push(...pts);
  L.polyline(pts,{color:seg.color,weight:7,opacity:.9}).addTo(map);
  seg.stations.forEach(s=>{
    L.circleMarker([s.lat,s.lon],{radius:5,color:seg.color,weight:3,
      fillColor:'#fff',fillOpacity:1}).bindTooltip(s.name+'역').addTo(map);
  });
});
function pin(p,color,label){
  L.circleMarker([p.lat,p.lon],{radius:11,color:'#fff',weight:3,fillColor:color,fillOpacity:1})
   .addTo(map).bindTooltip(label+': '+p.name+'역',{permanent:true,direction:'top',offset:[0,-10]});
}
pin(DATA.origin,'#d32f2f','출발'); pin(DATA.dest,'#1565c0','도착');
DATA.transfers.forEach(t=>{
  L.marker([t.lat,t.lon]).addTo(map).bindTooltip(t.name+'역 환승');
});
map.fitBounds(all,{padding:[40,40]});

const side = document.getElementById('side');
side.innerHTML = '<h1>'+DATA.origin.name+' → '+DATA.dest.name+'</h1>'+
  '<div class="sub">약 '+DATA.total+'분 · 환승 '+DATA.transfer_count+'회</div>'+
  DATA.steps.map((t,i)=>'<div class="step"><span class="dot" style="background:'+
    DATA.dots[i]+'"></span><span>'+t+'</span></div>').join('');
</script></body></html>
"""


def build_map(origin, dest, segments, steps, total_min, transfers, out_path):
    seg_data = []
    for seg in segments:
        line = seg[0][1]
        seg_data.append({
            "line": line,
            "color": LINES[line]["color"],
            "stations": [{"name": n, "lat": COORDS[n][0], "lon": COORDS[n][1]} for n, _ in seg],
        })

    # 환승역 마커: 구간 사이 경계역
    transfer_pts = []
    for i in range(len(segments) - 1):
        n = segments[i][-1][0]
        transfer_pts.append({"name": n, "lat": COORDS[n][0], "lon": COORDS[n][1]})

    # 사이드바 점 색: 출발(빨강) / 각 호선 색 / 환승(회색) / 도착(파랑)
    dots = ["#d32f2f"]
    for i, seg in enumerate(segments):
        dots.append(LINES[seg[0][1]]["color"])
        if i < len(segments) - 1:
            dots.append("#757575")
    dots.append("#1565c0")

    data = {
        "origin": {"name": origin, "lat": COORDS[origin][0], "lon": COORDS[origin][1]},
        "dest": {"name": dest, "lat": COORDS[dest][0], "lon": COORDS[dest][1]},
        "segments": seg_data,
        "transfers": transfer_pts,
        "steps": steps,
        "dots": dots,
        "total": round(total_min),
        "transfer_count": transfers,
    }
    html = (MAP_TEMPLATE
            .replace("__TITLE__", f"{origin} → {dest}")
            .replace("__DATA__", json.dumps(data, ensure_ascii=False)))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


# ─────────────────────────────────────────────────────────────
# 5. 음성 안내 (TTS)
# ─────────────────────────────────────────────────────────────
def _play_audio_file(path):
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["afplay", path])
    elif system == "Windows":
        os.startfile(path)  # 기본 플레이어로 재생
    else:
        for player in (["mpg123", "-q"], ["mpv", "--no-video"], ["ffplay", "-nodisp", "-autoexit"]):
            if shutil.which(player[0]):
                subprocess.run(player + [path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
        raise RuntimeError("재생 가능한 오디오 플레이어가 없습니다.")


def speak(text):
    """gTTS → pyttsx3 → macOS say 순서로 시도. 성공하면 True."""
    try:
        from gtts import gTTS
        path = os.path.join(tempfile.gettempdir(), "subway_guide.mp3")
        gTTS(text=text, lang="ko").save(path)
        _play_audio_file(path)
        return True
    except Exception:
        pass
    try:
        import pyttsx3
        engine = pyttsx3.init()
        for v in engine.getProperty("voices"):
            blob = f"{v.id} {v.name} {getattr(v, 'languages', '')}".lower()
            if "ko" in blob or "korean" in blob or "yuna" in blob:
                engine.setProperty("voice", v.id)
                break
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception:
        pass
    if shutil.which("say"):
        try:
            subprocess.run(["say", "-v", "Yuna", text])
            return True
        except Exception:
            pass
    return False


# ─────────────────────────────────────────────────────────────
# 6. 역 이름 입력 처리
# ─────────────────────────────────────────────────────────────
def normalize(q):
    q = q.strip().replace(" ", "")
    return q[:-1] if q.endswith("역") and len(q) > 1 else q


def resolve_station(prompt, preset=None):
    all_names = sorted(COORDS.keys())
    query = preset
    while True:
        if query is None:
            query = input(prompt)
        q = normalize(query)
        if q in COORDS:
            return q
        contains = [n for n in all_names if q and q in n]
        if len(contains) == 1:
            return contains[0]
        candidates = contains or difflib.get_close_matches(q, all_names, n=5, cutoff=0.5)
        if candidates:
            print(f"'{query}' 와(과) 비슷한 역: " + ", ".join(candidates))
            if len(candidates) == 1:
                ans = input(f"'{candidates[0]}역'이 맞나요? (Enter=예, 아니면 다시 입력) ").strip()
                if not ans:
                    return candidates[0]
                query = ans
                continue
        else:
            print(f"'{query}' 역을 찾을 수 없습니다.")
        print("(지원 역 예: 서울역, 강남, 홍대입구, 잠실 ...)")
        query = None


# ─────────────────────────────────────────────────────────────
# 7. 메인
# ─────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="지하철 길안내 시스템")
    ap.add_argument("origin", nargs="?", help="출발역")
    ap.add_argument("dest", nargs="?", help="도착역")
    ap.add_argument("--no-voice", action="store_true", help="음성 안내 끄기")
    ap.add_argument("--no-map", action="store_true", help="지도 열지 않기")
    ap.add_argument("--map-file", default=os.path.join(tempfile.gettempdir(), "subway_route.html"),
                    help="지도 HTML 저장 경로")
    args = ap.parse_args()

    print("=" * 50)
    print("  🚇 지하철 길안내 시스템")
    print("=" * 50)

    origin = resolve_station("출발역: ", args.origin)
    dest = resolve_station("도착역: ", args.dest)

    if origin == dest:
        print("출발역과 도착역이 같습니다.")
        return

    path, total = shortest_path(origin, dest)
    if path is None:
        print("경로를 찾을 수 없습니다.")
        return

    steps, segments, transfers = build_guidance(origin, dest, path, total)

    lat, lon = COORDS[origin]
    print(f"\n📍 출발지: {origin}역 (위도 {lat:.4f}, 경도 {lon:.4f})")
    print(f"🏁 도착지: {dest}역\n")
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s}")
    print()

    if not args.no_map:
        out = build_map(origin, dest, segments, steps, total, transfers, args.map_file)
        print(f"🗺  지도: {out}")
        try:
            webbrowser.open("file://" + os.path.abspath(out))
        except Exception:
            print("   (브라우저를 자동으로 열지 못했습니다. 위 파일을 직접 열어주세요.)")

    if not args.no_voice:
        print("🔊 음성 안내 중...")
        if not speak(" ".join(steps)):
            print("   음성 출력에 실패했습니다. `pip install gTTS` 또는 `pip install pyttsx3` 후 다시 시도하세요.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n종료합니다.")
        sys.exit(0)
