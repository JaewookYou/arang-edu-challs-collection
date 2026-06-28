# -*- coding: utf-8 -*-
# SSRF — 사용자 URL 을 서버가 대신 요청. 내부 전용 엔드포인트를 호출해 flag 획득.
import os, requests
from flask import Flask, request
app = Flask(__name__)
FLAG = os.environ.get("FLAG_SSRF", "flag{local}")

@app.route("/")
def index():
    return ('<h3>URL 미리보기</h3><form><input name="url" value="http://example.com" style="width:60%">'
            '<button>fetch</button></form>'
            '<p>서버가 입력한 URL 을 대신 요청합니다. 내부 전용 자원에 닿을 수 있을까?</p>')

@app.route("/fetch")
def fetch():
    url = request.args.get("url", "")
    if not url:
        return "url 필요"
    try:
        r = requests.get(url, timeout=3)        # ── SSRF sink (스킴/호스트 검증 없음) ──
        return "<pre>" + r.text[:2000] + "</pre>"
    except Exception as e:
        return "fetch error: " + str(e), 502

@app.route("/internal/flag")
def internal_flag():
    # 내부(localhost)에서의 요청만 허용 — 외부에서 직접 접근 불가
    if request.remote_addr in ("127.0.0.1", "::1"):
        return FLAG
    return "forbidden (internal only)", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9502)
