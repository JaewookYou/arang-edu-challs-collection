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
    # 봇(admin)이 대신 쓴 글을 '신고한 학생'에게 귀속시키기 위한 최근 신고자.
    # 이 배포는 봇 egress 로 외부 리스너를 쓰기 어려워(원격 수강생) 실질 유출 경로가
    # '봇에게 게시글을 쓰게 하기' 다. 그런데 admin 명의 글이 전원에게 보이면 한 명이
    # flag 를 제목에 적는 순간 전 수강생에게 뿌려진다 → 신고자 본인에게만 보이게 한다.
    last_reporter = {"uid": None}
    articles = list(seed_articles or [])
    if flag_in_article:
        articles.insert(0, {"seq": 0, "subject": "flag", "author": "admin", "content": flag})
    # 기동 시점의 시드 글만 '전원 공개'(문제 유도용 admin 글 — 제목만 보이고 본문은 못 봄).
    # 런타임에 admin 명의로 쌓이는 글(= XSS 페이로드가 봇에게 대신 쓰게 한 글)까지 전원에게
    # 보이면, 한 명이 flag 를 제목에 적는 순간 전 수강생 목록에 flag 가 그대로 뿌려진다.
    for a in articles:
        a["pinned"] = True

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
        rows = [a for a in articles
                if a["author"] == me or me == "admin" or a.get("pinned") or a.get("for_user") == me]
        return render_template("board.html", **ctx(articles=rows))

    @app.route("/board/<int:seq>")
    def view(seq):
        if not is_login():
            return redirect(url_for("login"))
        if seq < 0 or seq >= len(articles):
            return "no such article", 404
        a = articles[seq]
        if a["author"] == session["userid"] or session["userid"] == "admin" or a.get("for_user") == session["userid"]:
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
        item = {"seq": len(articles), "subject": subject,
                "author": session["userid"], "content": content}
        # 봇(admin)이 XSS 페이로드로 대신 쓴 글 → 마지막 신고자에게만 보이게 귀속
        if session["userid"] == "admin" and last_reporter["uid"]:
            item["for_user"] = last_reporter["uid"]
        articles.append(item)
        return redirect(url_for("board"))

    if needs_bot:
        @app.route("/report", methods=["GET", "POST"])
        def report():
            if request.method == "GET":
                return render_template("report.html", **ctx())
            url = request.form.get("url", "")
            last_reporter["uid"] = session.get("userid")   # 봇이 쓴 글의 귀속 대상
            try:
                requests.post(bot_url, data={"chal": chal_id, "url": url}, timeout=5)
            except Exception:
                pass
            return "<script>alert('reported to admin');history.go(-1)</script>"

    if extra_setup:
        extra_setup(app, {"users": users, "articles": articles, "flag": flag,
                          "is_login": is_login, "ctx": ctx})

    return app
