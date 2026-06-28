# -*- coding: utf-8 -*-
# XS-Leak (원본 기믹) — admin 이 글을 보면 <a href="javascript:alert('FLAG')"> 가 렌더됨.
# 게시글에 <style> 주입(스크립트는 차단) → 속성 선택자로 flag 를 한 글자씩 누출.
import os
from flask_board import create_app

def content_filter(c):
    c = c.lower()
    vulns = ["javascript", "script", "frame", "object", "embed", "on", "data", "base",
             "\\u", "&#", "alert", "fetch", "xmlhttprequest", "eval", "constructor"]
    return any(v in c for v in vulns)

app = create_app(
    title="XS-Leak - CSS Injection", chal_id="xsleak",
    flag=os.environ.get("FLAG_XSLEAK", "flag{local}"),
    admin_password=os.environ.get("ADMIN_PASSWORD", "admin1234"),
    needs_bot=True, flag_in_view_href=True,   # admin view 에 flag href 노출
    content_filter=content_filter, render_safe=True,
)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9106)
