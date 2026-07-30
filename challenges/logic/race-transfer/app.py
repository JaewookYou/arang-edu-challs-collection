# -*- coding: utf-8 -*-
# Race Condition — 잔액 검증과 차감 사이 경합(비원자적). 동시 요청으로 오버드래프트.
import os, time, threading
from flask import Flask, request
app = Flask(__name__)
FLAG = os.environ.get("FLAG_RACE", "flag{local}")

# 목표 vault 임계값. 정상 경로의 최대 이체액은 me=100(전액 1회) 뿐이므로,
# 1000 에 도달하려면 동시 요청 다수가 검증을 함께 통과(오버드래프트)해야 한다.
#  ※ 동시 통과 가능 수 = gunicorn 워커×스레드. Dockerfile 의 --threads 를 충분히
#    크게 두어 10요청 이상 동시 통과가 가능 → 1000 도달. (--threads 8 은
#    최대 8요청만 통과해 800 에서 막혀 풀이 불가였음)
WIN = 1000

# 잔액은 '수강생별' 로 따로 둔다. 예전엔 전역 dict 하나를 전원이 공유해서
#   (1) 한 명이 성공시키면 vault>=1000 이 남아 그 뒤 접속자 전원에게 /flag 가 그냥 열렸고
#   (2) 반대로 누가 me 를 음수로 만들면 나머지 전원이 '잔액 부족' 으로 아예 못 풀었으며
#   (3) /reset 을 아무나 눌러 남의 진행을 날릴 수 있었다.
# 세션 쿠키가 아니라 접속 IP 로 가르는 이유: 이 문제의 풀이는 본질적으로 다중 커넥션
# 동시 요청이라, 쿠키를 안 실어 보내는 병렬 curl·스크립트로도 같은 상태를 봐야 한다.
TTL = 3600
_states = {}
_lock = threading.Lock()


def st():
    """요청자 전용 잔액. 생성/조회만 잠그고, 검증-차감 구간은 잠그지 않는다
    (거기를 잠그면 경합이 사라져 문제가 성립하지 않는다)."""
    ip = request.remote_addr or "?"
    now = time.time()
    with _lock:
        s = _states.get(ip)
        if s is None:
            s = {"me": 100, "vault": 0, "ts": now}
            _states[ip] = s
        s["ts"] = now
        if len(_states) > 512:                       # 오래된 것 정리(무한 증식 방지)
            for k in [k for k, v in _states.items() if now - v["ts"] > TTL]:
                _states.pop(k, None)
    return s


@app.route("/")
def index():
    bal = st()
    return ("<h3>이체</h3>잔액: me=%d vault=%d<br>"
            "<form action='/transfer'><input name='amt' value='100'>"
            "<button>vault 로 이체</button></form>"
            "<p>vault 에 %d 이상 모으면 flag (단, me 는 100 뿐)</p>"
            "<a href='/flag'>/flag</a> · <a href='/reset'>/reset</a>"
            "<p style='color:#888;font-size:13px'>※ 잔액은 접속자별로 따로 관리됩니다."
            " 남의 진행 상황은 보이지 않습니다.</p>") % (bal["me"], bal["vault"], WIN)


@app.route("/transfer")
def transfer():
    bal = st()
    try:
        amt = int(request.args.get("amt", "0"))
    except ValueError:
        return "잘못된 금액"
    if amt > 0 and bal["me"] >= amt:        # 검증
        time.sleep(0.15)                    # ── 경합 창(race window) ──
        bal["me"] -= amt                    # 차감 (비원자적)
        bal["vault"] = bal.get("vault", 0) + amt
        return "ok me=%d vault=%d" % (bal["me"], bal["vault"])
    return "잔액 부족 me=%d" % bal["me"]


@app.route("/flag")
def flag():
    bal = st()
    if bal["vault"] >= WIN:
        return "축하합니다: " + FLAG
    return "vault=%d (%d 필요)" % (bal["vault"], WIN)


@app.route("/reset")
def reset():
    bal = st()
    bal["me"] = 100
    bal["vault"] = 0
    return "reset"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9401)
