# -*- coding: utf-8 -*-
# CSRF #1 (원본 기믹) — 마크다운 이미지 치환 + xsscheck. changepw GET, admin 은 내부망에서만.
import os, re, socket
from flask import request, redirect
from flask_board import create_app

def content_filter(c):
    c = c.lower()
    vulns = ["javascript", "frame", "object", "on", "data", "embed", "&#", "base",
             "\\u", "alert", "fetch", "xmlhttprequest", "eval", "constructor"] + list("'\"")
    return any(v in c for v in vulns)

def content_transform(content):
    # 마크다운 이미지 ![alt](url) → <img src="url" id="alt">  (먼저 " 제거)
    return re.sub(r"!\[(.*?)\]\((.*?)\)", r'<img src="\2" id="\1">', content.replace('"', ''))

def extra_setup(app, st):
    users = st["users"]
    @app.route("/changepw")
    def changepw():
        if "userid" not in request.args or "userpw" not in request.args:
            return '<form method="GET" action="/changepw"><input name="userid"><input name="userpw"><button>change</button></form>'
        userid = request.args["userid"]; userpw = request.args["userpw"]
        if userid == "admin":
            if request.remote_addr != socket.gethostbyname("bot"):
                return "admin password is only changed at internal network"
        if userid in users:
            users[userid] = userpw
            return redirect("/login")
        return "user doesn't exist"

app = create_app(
    title="CSRF #1 - admin 비밀번호 변경", chal_id="csrf-1",
    flag=os.environ.get("FLAG_CSRF_1", "flag{local}"),
    admin_password=os.environ.get("ADMIN_PASSWORD", "admin1234"),
    needs_bot=True, flag_in_article=True,
    content_filter=content_filter, content_transform=content_transform,
    render_safe=True, extra_setup=extra_setup,
)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9104)
