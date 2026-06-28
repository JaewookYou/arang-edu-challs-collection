# -*- coding: utf-8 -*-
# XSS #1 — 기본 (Stored XSS → admin 쿠키 탈취)
# 이 문제의 '취약점'은 아래 설정 한 곳뿐:
#   render_safe=True   → 게시글 본문을 escape 없이 출력 (XSS sink)
#   content_filter=None → 입력 필터 없음
#   flag_in_cookie=True → admin 봇이 flag 를 쿠키로 보유
import os
from flask_board import create_app

app = create_app(
    title="XSS #1 — 기본",
    chal_id="xss-1",
    flag=os.environ.get("FLAG_XSS_1", "flag{local_test_flag}"),
    admin_password=os.environ.get("ADMIN_PASSWORD", "admin1234"),
    needs_bot=True,
    flag_in_cookie=True,
    content_filter=None,   # 필터 없음
    render_safe=True,      # ← XSS sink
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9101)
