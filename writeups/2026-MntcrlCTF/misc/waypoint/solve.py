#!/usr/bin/env python3
"""
waypoint - MntcrlCTF 2026 (misc)

DJI 비행 로그(csv) 51개에서 숨겨진 메시지를 복원한다.

핵심 아이디어
  - 각 csv는 드론 한 번의 비행 기록(latitude/longitude 시계열)이다.
  - 비행 경로를 lon(x)-lat(y) 평면에 그리면 글자 한 조각이 그려진다.
  - 메시지는 캠퍼스 서쪽 구역(lon < 16.888)에 격자로 배치되어 있고,
    동쪽 구역(원/직선/사각형 등 단순 도형)은 "그냥 테스트한" 미끼다.
  - 서쪽 비행들을 '실제 좌표 그대로' 한 캔버스에 겹쳐 그리면
    위/아래 두 줄의 손글씨 텍스트(=플래그)가 자연스럽게 나타난다.

사용법:
  python solve.py <csv들이 있는 폴더>   # 기본값: 현재 폴더
"""
import csv
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 메시지 구역과 미끼 구역을 가르는 경도 경계
LON_SPLIT = 16.888


def smooth(values, window=5):
    """GPS 지터를 줄이기 위한 단순 이동평균."""
    out = []
    for i in range(len(values)):
        lo = max(0, i - window // 2)
        hi = min(len(values), i + window // 2 + 1)
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out


def load_flights(folder):
    flights = []
    for path in glob.glob(os.path.join(folder, "*.csv")):
        lat, lon = [], []
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)  # header
            for row in reader:
                lat.append(float(row[2]))
                lon.append(float(row[3]))
        flights.append({
            "name": os.path.basename(path),
            "lon": lon,
            "lat": lat,
            "clon": sum(lon) / len(lon),
            "clat": sum(lat) / len(lat),
        })
    return flights


def plot_message(flights, out_path):
    """서쪽(메시지) 비행만 실제 좌표에 겹쳐 그린다 -> 플래그가 보인다."""
    msg = [f for f in flights if f["clon"] < LON_SPLIT]
    fig, ax = plt.subplots(figsize=(26, 5))
    for f in msg:
        ax.plot(smooth(f["lon"]), smooth(f["lat"]), "-", lw=1.0, color="black")
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"[+] message  -> {out_path}  ({len(msg)} flights)")


def plot_overview(flights, out_path):
    """전체 비행 경로 + 두 구역(메시지 vs 미끼)을 색으로 구분."""
    fig, ax = plt.subplots(figsize=(26, 6))
    for f in flights:
        color = "black" if f["clon"] < LON_SPLIT else "tab:red"
        ax.plot(smooth(f["lon"]), smooth(f["lat"]), "-", lw=0.7, color=color)
    ax.set_aspect("equal")
    ax.set_title("black = hidden message (west grid)   |   red = decoy 'tests' (east)")
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[+] overview -> {out_path}")


def plot_single(flights, out_path):
    """동쪽 미끼 중 가장 깔끔한 원(circle) 한 개 = '비행 1개가 도형 1개를 그린다' 예시."""
    east = [f for f in flights if f["clon"] >= LON_SPLIT]
    # 가로/세로로 가장 넓게 퍼진(=도형을 크게 그린) 비행 하나 선택
    target = max(east, key=lambda f: (max(f["lon"]) - min(f["lon"])) *
                                     (max(f["lat"]) - min(f["lat"])))
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(smooth(target["lon"]), smooth(target["lat"]), "-", lw=1.2, color="black")
    ax.scatter(target["lon"][0], target["lat"][0], c="green", s=30, label="start")
    ax.scatter(target["lon"][-1], target["lat"][-1], c="red", s=30, label="end")
    ax.set_aspect("equal")
    ax.legend()
    ax.set_title(f"single flight: {target['name']}")
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[+] single   -> {out_path}")


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    flights = load_flights(folder)
    print(f"[*] loaded {len(flights)} flight logs from {folder}")

    images = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
    os.makedirs(images, exist_ok=True)
    plot_single(flights, os.path.join(images, "single_flight.png"))
    plot_overview(flights, os.path.join(images, "overview.png"))
    plot_message(flights, os.path.join(images, "message.png"))
    print("[*] flag: mntcrl{n3v3r_tru5t_4_p1l0t}")


if __name__ == "__main__":
    main()
