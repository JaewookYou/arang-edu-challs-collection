# -*- coding: utf-8 -*-
# IDOR/BOLA — 계좌 조회가 소유자 검증 없이 acct 파라미터만으로 동작.
import os
from flask import Flask, request, session, redirect
app = Flask(__name__); app.secret_key = os.urandom(16)
FLAG = os.environ.get("FLAG_IDOR", "flag{local}")
USERS = {"guest": "guest"}
ACCTS = {
    "1001": {"owner": "guest", "balance": 12000, "memo": "내 입출금통장"},
    "1000": {"owner": "admin", "balance": 999999999, "memo": FLAG},  # 관리자 계좌 메모에 flag
}

@app.route("/")
def index():
    if not session.get("u"):
        return redirect("/login")
    return ('로그인: %s (내 계좌 <b>1001</b>)<br><form action="/balance">'
            '<input name="acct" value="1001"><button>잔액조회</button></form>'
            '<p>다른 계좌도 조회될까?</p>') % session["u"]

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return '<form method=post><input name=u value=guest><input name=p value=guest type=password><button>login</button></form>'
    if USERS.get(request.form.get("u")) == request.form.get("p"):
        session["u"] = request.form["u"]; return redirect("/")
    return "login fail"

@app.route("/balance")
def balance():
    if not session.get("u"):
        return redirect("/login")
    acct = request.args.get("acct", "")
    a = ACCTS.get(acct)
    if not a:
        return "없는 계좌"
    # ── IDOR: 세션 사용자와 계좌 소유자 일치 검증이 없음 ──
    return "계좌 %s · 잔액 %s · 메모: %s" % (acct, a["balance"], a["memo"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9301)
