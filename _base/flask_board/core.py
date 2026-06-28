# -*- coding: utf-8 -*-
"""flask_board — 클라이언트 사이드 문제 공용 게시판 골격. 문제는 '취약한 부분'만 넘긴다."""
import os
import requests
from flask import (Flask, request, session, redirect, url_for,
                   render_template, make_response)

HERE = os.path.dirname(os.path.abspath(__file__))


def create_app(*, title, chal_id, flag, admin_password,
               needs_bot=False, bot_url=None,
               content_filter=None, content_transform=None, render_safe=True,
               flag_in_cookie=False, flag_in_article=False, flag_in_view_href=False,
               seed_articles=None, extra_setup=None):
    app = Flask(__name__, template_folder=os.path.join(HERE, "templates"))
    app.secret_key = os.urandom(24).hex()
    bot_url = bot_url or os.environ.get("BOT_URL", "http://bot:9099/visit")

    users = {"admin": admin_password}
    articles = list(seed_articles or [])
    if flag_in_article:
        articles.insert(0, {"seq": 0, "subject": "flag", "author": "admin", "content": flag})

    def is_login():
        return session.get("isLogin", False)

    def ctx(**kw):
        return dict(title=title, uid=session.get("userid"), needs_bot=needs_bot, **kw)

    @app.route("/")
    def index():
        return redirect(url_for("board") if is_login() else url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html", **ctx(msg=""))
        uid = request.form.get("userid", "")
        pw = request.form.get("userpw", "")
        if uid in users and users[uid] == pw:
            session["userid"] = uid
            session["isLogin"] = True
            resp = make_response(redirect(url_for("board")))
            if uid == "admin" and flag_in_cookie:
                resp.set_cookie("flag", flag)
            return resp
        return render_template("login.html", **ctx(msg="login fail"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "GET":
            return render_template("register.html", **ctx(msg=""))
        uid = request.form.get("userid", "")
        pw = request.form.get("userpw", "")
        if uid and uid not in users:
            users[uid] = pw
            return redirect(url_for("login"))
        return render_template("register.html", **ctx(msg="already exists"))

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/board")
    def board():
        if not is_login():
            return redirect(url_for("login"))
        me = session["userid"]
        rows = [a for a in articles if a["author"] == me or me == "admin" or a["author"] == "admin"]
        return render_template("board.html", **ctx(articles=rows))

    @app.route("/board/<int:seq>")
    def view(seq):
        if not is_login():
            return redirect(url_for("login"))
        if seq < 0 or seq >= len(articles):
            return "no such article", 404
        a = articles[seq]
        if a["author"] == session["userid"] or session["userid"] == "admin":
            extra = {}
            if flag_in_view_href:
                extra["flag_href"] = flag if session["userid"] == "admin" else "no flag to user"
            return render_template("view.html", **ctx(a=a, render_safe=render_safe, **extra))
        return "<script>alert('not your article');location='/board'</script>"

    @app.route("/write", methods=["GET", "POST"])
    def write():
        if not is_login():
            return redirect(url_for("login"))
        if request.method == "GET":
            return render_template("write.html", **ctx())
        subject = request.form.get("subject", "")
        content = request.form.get("content", "")
        if content_filter and content_filter(content):
            return "<script>alert('blocked');history.go(-1)</script>"
        if content_transform:
            content = content_transform(content)
        articles.append({"seq": len(articles), "subject": subject,
                         "author": session["userid"], "content": content})
        return redirect(url_for("board"))

    if needs_bot:
        @app.route("/report", methods=["GET", "POST"])
        def report():
            if request.method == "GET":
                return render_template("report.html", **ctx())
            url = request.form.get("url", "")
            try:
                requests.post(bot_url, data={"chal": chal_id, "url": url}, timeout=5)
            except Exception:
                pass
            return "<script>alert('reported to admin');history.go(-1)</script>"

    if extra_setup:
        extra_setup(app, {"users": users, "articles": articles, "flag": flag,
                          "is_login": is_login, "ctx": ctx})

    return app
