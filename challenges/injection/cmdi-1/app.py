# -*- coding: utf-8 -*-
# Command Injection (원본 기믹) — Blind. 결과를 돌려주지 않음(return "!"). OOB 또는 개인 회수함으로 유출.
import os, time, hmac, hashlib, signal, threading, subprocess
from flask import Flask, request, Response
app = Flask(__name__)

# '/' 는 항상 읽기전용 원본을 보여 준다. 예전엔 open(__file__) 이었는데, 그러면 수강생이
# `cat flag >> app.py` 로 결과를 회수할 수 있고 — 실제로 그렇게들 썼다 — 그 페이지는
# 전 수강생이 보는 곳이라 남의 문제 플래그(prototype-pollution·domclobbering·xsleak)까지
# 공용 게시판에 붙는 꼴이 됐다. 회수는 아래 개인 회수함(/out)으로만 되게 한다.
SRC = "/opt/app.py.orig" if os.path.exists("/opt/app.py.orig") else __file__
OUT_DIR = "/tmp/out"
TTL = 600          # 회수함 파일 수명(초) — 남의 RCE 가 주워 가는 창을 좁힌다

try:
    open("/command_injection_flag.txt", "w").write(os.environ.get("FLAG_CMDI_1", "flag{local}"))
    os.chmod("/command_injection_flag.txt", 0o444)
except Exception:
    pass
try:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.chmod(OUT_DIR, 0o777)
except Exception:
    pass


def sink_path():
    """요청자별 회수함. 키가 플래그라 남이 경로를 추측할 수 없다.
    IP 는 소켓 주소만 쓴다 — 이 문제는 프록시 없이 직접 노출돼 있어서
    X-Forwarded-For 를 믿으면 남의 IP 를 적어 회수함을 가로챌 수 있다."""
    ip = request.remote_addr or "?"
    key = os.environ.get("FLAG_CMDI_1", "local").encode()
    return os.path.join(OUT_DIR, hmac.new(key, ip.encode(), hashlib.sha256).hexdigest()[:16])


def banner():
    p = sink_path()
    return (
        "# ── 안내(자동 생성) ────────────────────────────────────────────────\n"
        "# Blind 다. 명령 출력은 응답에 담기지 않는다(항상 \"!\").\n"
        "# 결과는 '당신 전용 회수함' 에 적어서 따로 가져간다.\n"
        "#\n"
        "#   1) 적기 :  ?cmd=<명령> > %s\n"
        "#   2) 읽기 :  GET /out          ← 당신에게만 보인다(읽으면 즉시 삭제)\n"
        "#\n"
        "# 회수함 경로는 접속 IP 로 만들어져 사람마다 다르다.\n"
        "# ※ app.py 에 덧붙이는 방식은 더 이상 이 페이지에 뜨지 않는다 —\n"
        "#   그건 전 수강생이 보는 자리라 남의 플래그까지 공개돼서 막았다.\n"
        "# ※ 바깥으로 나가는 OOB(리버스셸/curl)도 그대로 열려 있다.\n"
        "# ──────────────────────────────────────────────────────────────────\n\n"
    ) % p


@app.route("/")
def index():
    if "cmd" not in request.args:
        return Response(banner() + open(SRC).read(), mimetype="text/plain")
    cmd = request.args["cmd"]
    # timeout 필수: 예전엔 무제한이라 리버스셸·리스너처럼 안 끝나는 명령이 워커 스레드를
    # 물고 있었고, 8개가 차면 문제 전체가 응답을 멈췄다.
    # start_new_session + killpg 도 필수: 셸만 죽이면 그 자식(sleep·nc 등)이 고아로 남아
    # PID 를 잠식하다 pids 한도에 걸려 컨테이너가 통째로 멎는다.
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    except Exception:
        return "!"
    try:
        p.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)     # 프로세스 그룹째
        except Exception:
            pass
        try:
            p.communicate(timeout=3)                          # 종료상태 수거(좀비 방지)
        except Exception:
            pass
    except Exception:
        pass
    return "!"                                          # 출력 미반환 = Blind


@app.route("/out")
def out():
    p = sink_path()
    if not os.path.exists(p):
        return Response("(비어 있음) 먼저 결과를 %s 로 보내세요.\n" % p, mimetype="text/plain")
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            data = f.read()
        os.remove(p)                                    # 읽으면 삭제 — 잔류 노출 방지
    except Exception as e:
        return Response("read error: %s\n" % e, mimetype="text/plain")
    return Response(data, mimetype="text/plain")


def cleaner(interval=60):
    """오래된 회수함 정리 — 다른 수강생의 RCE 가 주워 갈 창을 좁힌다."""
    while True:
        time.sleep(interval)
        try:
            now = time.time()
            for n in os.listdir(OUT_DIR):
                f = os.path.join(OUT_DIR, n)
                if os.path.isfile(f) and now - os.path.getmtime(f) > TTL:
                    os.remove(f)
        except Exception:
            pass


threading.Thread(target=cleaner, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9206)
