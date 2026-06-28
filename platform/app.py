# -*- coding: utf-8 -*-
"""
플랫폼 (스코어보드) — 문제를 호스팅하지 않고 registry.yaml 만 읽어
목록 / 플래그 제출 / 채점 / 랭킹만 담당한다. (문제 컨테이너와 직접 통신하지 않음)
"""
import os, json, time
import yaml
from flask import Flask, request, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.secret_key = os.environ.get("PLATFORM_SECRET", os.urandom(24).hex())

# ── 레지스트리 로드 ──
with open(os.path.join(BASE, "registry.yaml"), encoding="utf-8") as f:
    REG = yaml.safe_load(f)
CATEGORIES = REG.get("categories", {})
CHALLENGES = REG.get("challenges", [])

# ── 플래그 맵: 환경변수(flag_env)에서 주입된 값만 채점에 사용 ──
def flag_map():
    m = {}
    for c in CHALLENGES:
        fe = c.get("flag_env")
        val = os.environ.get(fe) if fe else None
        if val:
            m[val.strip()] = c["id"]
    return m

# ── 사용자 저장 (간단 JSON) ──
USERS_PATH = os.environ.get("USERS_PATH", "/data/users.json")
def load_users():
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}
def save_users(u):
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(u, f, indent=2, ensure_ascii=False)

def current_user():
    return session.get("uid")

# ── 라우트 ──
@app.route("/")
def index():
    if not current_user():
        return redirect(url_for("login"))
    users = load_users()
    solved = set(users.get(current_user(), {}).get("solved", []))
    grouped = {k: [] for k in CATEGORIES}
    for c in CHALLENGES:
        grouped.setdefault(c["category"], []).append({**c, "solved": c["id"] in solved})
    total = len([c for c in CHALLENGES if c.get("status") == "ready"])
    return render_template("main.html", categories=CATEGORIES, grouped=grouped,
                           solved=solved, uid=current_user(), solved_n=len(solved), total=total)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", msg=request.args.get("msg", ""))
    users = load_users()
    uid = request.form.get("userid", "").strip()
    pw = request.form.get("userpw", "")
    u = users.get(uid)
    if u and check_password_hash(u["pw"], pw):
        session["uid"] = uid
        return redirect(url_for("index"))
    return render_template("login.html", msg="아이디 또는 비밀번호가 올바르지 않습니다.")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", msg="")
    users = load_users()
    uid = request.form.get("userid", "").strip()
    pw = request.form.get("userpw", "")
    if not uid or not pw:
        return render_template("register.html", msg="아이디와 비밀번호를 입력하세요.")
    if uid in users:
        return render_template("register.html", msg="이미 존재하는 아이디입니다.")
    users[uid] = {"pw": generate_password_hash(pw), "solved": [], "last": 0}
    save_users(users)
    return redirect(url_for("login", msg="가입 완료. 로그인하세요."))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/submit", methods=["POST"])
def submit():
    if not current_user():
        return redirect(url_for("login"))
    flag = request.form.get("flag", "").strip()
    fm = flag_map()
    users = load_users()
    me = users.setdefault(current_user(), {"pw": "", "solved": [], "last": 0})
    if flag in fm:
        cid = fm[flag]
        if cid not in me["solved"]:
            me["solved"].append(cid)
            me["last"] = time.time()
            save_users(users)
        return redirect(url_for("index", _anchor="ok"))
    return redirect(url_for("index", _anchor="no"))

@app.route("/ranking")
def ranking():
    users = load_users()
    rows = sorted(
        [{"uid": u, "n": len(d.get("solved", [])), "last": d.get("last", 0)} for u, d in users.items()],
        key=lambda r: (-r["n"], r["last"]))
    rows = [r for r in rows if r["n"] > 0]
    return render_template("ranking.html", rows=rows, uid=current_user())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
