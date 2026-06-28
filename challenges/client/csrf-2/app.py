# -*- coding: utf-8 -*-
# CSRF #2 (원본 기믹) — changepw 에 csrf_token 필요(세션). XSS 로 토큰 누출 후 CSRF.
import os, socket, binascii
from flask import request, session, redirect
from flask_board import create_app

def content_filter(c):
    c = c.lower()
    vulns = ["javascript", "frame", "object", "on", "data", "base", "\\u", "embed", "&#",
             "alert", "fetch", "xmlhttprequest", "eval", "constructor"] + list("'\"")
    return any(v in c for v in vulns)

def extra_setup(app, st):
    users = st["users"]
    @app.route("/changepw")
    def changepw():
        if "userid" not in request.args or "userpw" not in request.args:
            session["csrf_token"] = binascii.hexlify(os.urandom(16)).decode()
            return ('<form id="form1" method="GET" action="/changepw">'
                    '<input name="userid"><input name="userpw">'
                    '<input type="hidden" name="csrf_token" value="%s"></form>') % session["csrf_token"]
        if "csrf_token" not in request.args:
            return "please input csrf token"
        if request.args["csrf_token"] != session.get("csrf_token"):
            return "csrf token not match!"
        userid = request.args["userid"]; userpw = request.args["userpw"]
        if userid == "admin":
            if request.remote_addr != socket.gethostbyname("bot"):
                return "admin password is only changed at internal network"
        if userid in users:
            users[userid] = userpw
            return redirect("/login")
        return "user doesn't exist"

app = create_app(
    title="CSRF #2 - 토큰 누출 체이닝", chal_id="csrf-2",
    flag=os.environ.get("FLAG_CSRF_2", "flag{local}"),
    admin_password=os.environ.get("ADMIN_PASSWORD", "admin1234"),
    needs_bot=True, flag_in_article=True,
    content_filter=content_filter, render_safe=True, extra_setup=extra_setup,
)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9105)
