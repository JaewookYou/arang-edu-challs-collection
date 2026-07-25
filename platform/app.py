# -*- coding: utf-8 -*-
"""
플랫폼 (스코어보드) — 문제를 호스팅하지 않고 registry.yaml 만 읽어
목록 / 플래그 제출 / 채점 / 랭킹만 담당한다. (문제 컨테이너와 직접 통신하지 않음)
"""
import os, json, time
from urllib.parse import urlsplit, urlunsplit
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

# ── 참가자 프로필(반·이름) ──
# 반은 1~40. 기존 계정은 이 필드가 없으므로 로그인 시 /profile 로 보내 보완 입력을 받는다.
CLASS_MIN, CLASS_MAX = 1, 40
CLASS_CHOICES = list(range(CLASS_MIN, CLASS_MAX + 1))

def profile_done(u):
    return bool(u) and bool(u.get("name")) and bool(u.get("classno"))

def parse_profile(form):
    """폼에서 반·이름을 검증해 (classno, name, error) 반환."""
    name = (form.get("name") or "").strip()
    raw = (form.get("classno") or "").strip()
    if not name:
        return None, "", "이름을 입력하세요."
    if len(name) > 20:
        return None, name, "이름은 20자 이하로 입력하세요."
    if not raw.isdigit() or not (CLASS_MIN <= int(raw) <= CLASS_MAX):
        return None, name, "반을 선택하세요(%d~%d반)." % (CLASS_MIN, CLASS_MAX)
    return int(raw), name, None

@app.before_request
def require_profile():
    """로그인했는데 반·이름이 비어 있으면(기존 계정) 보완 입력 페이지로 유도."""
    if not current_user() or request.endpoint in ("profile", "logout", "login", "register", "static"):
        return None
    u = load_users().get(current_user())
    if u is None:          # 계정이 삭제된 세션
        session.clear()
        return redirect(url_for("login"))
    if not profile_done(u):
        return redirect(url_for("profile"))
    return None

# ── 챌린지 URL 호스트 보정 ──
# registry.yaml 의 url 은 localhost 로 고정돼 있지만, 학습자가 어떤 호스트로 대시보드에
# 접속했든(edu.arang.kr·사내 IP·localhost) 그 호스트의 동일 포트로 링크가 향하도록
# 요청 Host 헤더의 호스트명으로 url 의 호스트만 교체한다(포트/경로/스킴은 유지).
def localize_url(url, req_host):
    try:
        host = (req_host or "").rsplit(":", 1)[0]  # 플랫폼(:9000) 포트 제거 → 호스트명만
        if not host:
            return url
        parts = urlsplit(url)
        netloc = "{}:{}".format(host, parts.port) if parts.port else host
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return url

# ── 라우트 ──
@app.route("/")
def index():
    if not current_user():
        return redirect(url_for("login"))
    users = load_users()
    solved = set(users.get(current_user(), {}).get("solved", []))
    grouped = {k: [] for k in CATEGORIES}
    for c in CHALLENGES:
        item = {**c, "solved": c["id"] in solved}
        if item.get("url"):
            item["url"] = localize_url(item["url"], request.host)
        grouped.setdefault(c["category"], []).append(item)
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
        return render_template("register.html", msg="", classes=CLASS_CHOICES, form={})
    users = load_users()
    uid = request.form.get("userid", "").strip()
    pw = request.form.get("userpw", "")
    classno, name, err = parse_profile(request.form)
    # 입력값은 되돌려줘서 오류 시 다시 타이핑하지 않게 한다
    back = {"userid": uid, "name": name, "classno": request.form.get("classno", "")}
    def again(m):
        return render_template("register.html", msg=m, classes=CLASS_CHOICES, form=back)
    if not uid or not pw:
        return again("아이디와 비밀번호를 입력하세요.")
    if err:
        return again(err)
    if uid in users:
        return again("이미 존재하는 아이디입니다.")
    users[uid] = {"pw": generate_password_hash(pw), "solved": [], "last": 0,
                  "classno": classno, "name": name}
    save_users(users)
    return redirect(url_for("login", msg="가입 완료. 로그인하세요."))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    """반·이름 보완 입력 — 이 필드가 없는 기존 계정이 로그인하면 여기로 온다."""
    if not current_user():
        return redirect(url_for("login"))
    users = load_users()
    me = users.get(current_user())
    if me is None:
        session.clear()
        return redirect(url_for("login"))
    if request.method == "GET":
        form = {"name": me.get("name", ""), "classno": me.get("classno", "")}
        return render_template("profile.html", msg="", classes=CLASS_CHOICES, form=form,
                               uid=current_user(), first=not profile_done(me))
    classno, name, err = parse_profile(request.form)
    if err:
        return render_template("profile.html", msg=err, classes=CLASS_CHOICES,
                               form={"name": name, "classno": request.form.get("classno", "")},
                               uid=current_user(), first=not profile_done(me))
    me["classno"], me["name"] = classno, name
    save_users(users)
    return redirect(url_for("index"))

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
    ready = [c for c in CHALLENGES if c.get("status") == "ready"]
    total = len(ready)
    # 카테고리 순서는 registry 의 categories 정의 순서를 따른다
    by_cat = [(k, CATEGORIES[k], [c for c in ready if c["category"] == k]) for k in CATEGORIES]
    by_cat = [t for t in by_cat if t[2]]

    rows = []
    for u, d in users.items():
        solved = [s for s in d.get("solved", []) if s]
        # 참가자만 노출: 프로필을 채웠거나(수강생) 해결 기록이 있는 계정.
        # (부하테스트·검증용으로 만들어진 잔여 계정이 랭킹을 덮지 않게)
        if not solved and not profile_done(d):
            continue
        sset = set(solved)
        # 카테고리별 해결 현황을 서버에서 만들어 템플릿은 그리기만 하게 한다
        cats = []
        for _key, label, chals in by_cat:
            # 키 이름 주의: 'items' 는 Jinja 에서 dict.items 메서드로 잡혀 순회가 깨진다
            lst = [{"id": c["id"], "title": c["title"], "on": c["id"] in sset} for c in chals]
            cats.append({"label": label, "got": sum(1 for i in lst if i["on"]),
                         "tot": len(lst), "chals": lst})
        rows.append({
            "uid": u, "name": d.get("name") or u, "classno": d.get("classno"),
            "n": len(sset), "last": d.get("last", 0), "cats": cats,
            "pct": round(len(sset) * 100 / total) if total else 0,
        })
    rows.sort(key=lambda r: (-r["n"], r["last"] or 0))
    return render_template("ranking.html", rows=rows, uid=current_user(),
                           by_cat=by_cat, total=total)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
