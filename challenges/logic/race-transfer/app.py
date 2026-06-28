# -*- coding: utf-8 -*-
# Race Condition — 잔액 검증과 차감 사이 경합(비원자적). 동시 요청으로 오버드래프트.
import os, time
from flask import Flask, request
app = Flask(__name__)
FLAG = os.environ.get("FLAG_RACE", "flag{local}")
bal = {"me": 100, "vault": 0}   # 시작 잔액 100

# 목표 vault 임계값. 정상 경로의 최대 이체액은 me=100(전액 1회) 뿐이므로,
# 1000 에 도달하려면 동시 요청 다수가 검증을 함께 통과(오버드래프트)해야 한다.
#  ※ 동시 통과 가능 수 = gunicorn 워커×스레드. Dockerfile 의 --threads 를 충분히
#    크게(24) 두어 10요청 이상 동시 통과가 가능 → 1000 도달. (이전 --threads 8 은
#    최대 8요청만 통과해 800 에서 막혀 풀이 불가였음)
WIN = 1000

@app.route("/")
def index():
    return ("<h3>이체</h3>잔액: me=%d vault=%d<br>"
            "<form action='/transfer'><input name='amt' value='100'>"
            "<button>vault 로 이체</button></form>"
            "<p>vault 에 %d 이상 모으면 flag (단, me 는 100 뿐)</p>"
            "<a href='/flag'>/flag</a>") % (bal["me"], bal["vault"], WIN)

@app.route("/transfer")
def transfer():
    amt = int(request.args.get("amt", "0"))
    if amt > 0 and bal["me"] >= amt:        # 검증
        time.sleep(0.15)                    # ── 경합 창(race window) ──
        bal["me"] -= amt                    # 차감 (비원자적)
        bal["vault"] = bal.get("vault", 0) + amt
        return "ok me=%d vault=%d" % (bal["me"], bal["vault"])
    return "잔액 부족 me=%d" % bal["me"]

@app.route("/flag")
def flag():
    if bal["vault"] >= WIN:
        return "축하합니다: " + FLAG
    return "vault=%d (%d 필요)" % (bal["vault"], WIN)

@app.route("/reset")
def reset():
    bal["me"] = 100; bal["vault"] = 0; return "reset"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9401)
