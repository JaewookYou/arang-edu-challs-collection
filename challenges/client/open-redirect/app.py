# -*- coding: utf-8 -*-
# Open Redirect — 불완전한 same-site 검사 우회.
import os, html
from urllib.parse import urlparse
from flask import Flask, request, redirect

FLAG = os.environ.get("FLAG_OPENRED", "flag{local}")
app = Flask(__name__)

def is_safe(url):
    # 의도적으로 허술한 검사: 'localhost' 포함 또는 '/' 시작이면 안전하다고 판단
    return url.startswith("/") or "localhost" in url

@app.route("/")
def index():
    return ('<h3>로그인 후 next 로 이동합니다.</h3>'
            '<form action="/go"><input name="next" value="/welcome" style="width:60%">'
            '<button>이동</button></form>'
            '<p>외부 도메인으로 리다이렉트(open redirect)를 성공시키면 flag 를 드립니다.</p>')

@app.route("/welcome")
def welcome():
    return "welcome (same-site)"

@app.route("/go")
def go():
    nxt = request.args.get("next", "/welcome")
    if not is_safe(nxt):
        return "차단된 리다이렉트", 400
    host = urlparse(nxt if "://" in nxt else "http://x" + nxt).hostname or ""
    # 외부 도메인으로 리다이렉트가 허용되면(=오픈 리다이렉트 성공) flag 노출.
    # ※ 실제 302 로 보내면 브라우저가 그 도메인으로 떠나버려 flag 본문을 못 본다 →
    #    이동시키지 않고 200 페이지로 flag 를 보여준다.
    if host and host not in ("x", "") and "localhost" not in host and not nxt.startswith("/welcome"):
        return ('<h3>open redirect 성공!</h3>'
                '<p>외부 도메인 <b>%s</b> 으로의 리다이렉트가 허용되었습니다. '
                '(실제 브라우저였다면 그대로 그 사이트로 이동)</p>'
                '<p>flag: %s</p>') % (html.escape(host), FLAG)
    return redirect(nxt)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9108)
