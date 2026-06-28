# -*- coding: utf-8 -*-
# XSS #3 — 강한 필터 + flag 는 admin 게시글(0번)에. 직접 view 불가 → XSS 로 읽어 외부 전송.
import os
from flask_board import create_app

def content_filter(c):
    c = c.lower()
    bad = ["javascript", "frame", "object", "on", "data", "base", "\\u",
           "alert", "fetch", "xmlhttprequest", "eval", "constructor"]
    bad += list("()'\"")
    return any(b in c for b in bad)

app = create_app(
    title="XSS #3 - flag 게시글 읽기", chal_id="xss-3",
    flag=os.environ.get("FLAG_XSS_3", "flag{local}"),
    admin_password=os.environ.get("ADMIN_PASSWORD", "admin1234"),
    needs_bot=True, flag_in_article=True,   # 0번 글(admin)에 flag
    content_filter=content_filter, render_safe=True,
)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9103)
