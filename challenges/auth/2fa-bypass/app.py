# -*- coding: utf-8 -*-
# 2FA Bypass — 비밀번호 단계 후 OTP 단계가 있으나, 보호 자원이 OTP 완료를 검증하지 않음.
import os, secrets
from flask import Flask, request, session, redirect
app = Flask(__name__); app.secret_key = os.urandom(16)
FLAG = os.environ.get("FLAG_2FA", "flag{local}")
USERS = {"guest": "guest"}
OTP = secrets.token_hex(3)  # 사용자에게 알려주지 않음

@app.route("/")
def index():
    return '<a href="/login">login</a> → OTP → /secret'

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return '<form method=post><input name=u value=guest><input name=p value=guest type=password><button>login</button></form>'
    if USERS.get(request.form.get("u")) == request.form.get("p"):
        session["stage"] = "otp"; session["u"] = request.form["u"]   # 1단계 통과
        return redirect("/otp")
    return "login fail"

@app.route("/otp", methods=["GET", "POST"])
def otp():
    if session.get("stage") not in ("otp", "done"):
        return redirect("/login")
    if request.method == "GET":
        return '<form method=post><input name=otp placeholder="OTP 6자리"><button>verify</button></form>'
    if request.form.get("otp") == OTP:
        session["stage"] = "done"; return "2FA 완료. <a href=/secret>secret</a>"
    return "OTP 불일치"

@app.route("/secret")
def secret():
    # ── 결함: OTP 완료('done')가 아니라 비번단계('otp')만 확인 ──
    if session.get("stage") in ("otp", "done"):
        return "기밀: " + FLAG
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9302)
