# -*- coding: utf-8 -*-
# XSS #2 (원본 기믹) — 필터: script/on/( )/'/javascript/data/base + 제어문자. flag 는 admin 쿠키.
import os
from flask_board import create_app

def content_filter(c):
    c = c.lower()
    vulns = ["javascript", "script", "on", "data", "base", "(", ")", "'"]
    vulns += [chr(x) for x in range(0x20)]
    return any(v in c for v in vulns)

app = create_app(
    title="XSS #2 - 필터 우회", chal_id="xss-2",
    flag=os.environ.get("FLAG_XSS_2", "flag{local}"),
    admin_password=os.environ.get("ADMIN_PASSWORD", "admin1234"),
    needs_bot=True, flag_in_cookie=True,
    content_filter=content_filter, render_safe=True,
)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9102)
