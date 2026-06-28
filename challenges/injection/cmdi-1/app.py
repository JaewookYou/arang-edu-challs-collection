# -*- coding: utf-8 -*-
# Command Injection (원본 기믹) — Blind. 결과를 돌려주지 않음(return "!"). OOB/리버스셸로 유출.
import os, subprocess
from flask import Flask, request, Response
app = Flask(__name__)
try:
    open("/command_injection_flag.txt", "w").write(os.environ.get("FLAG_CMDI_1", "flag{local}"))
    os.chmod("/command_injection_flag.txt", 0o444)
except Exception:
    pass

@app.route("/")
def index():
    if "cmd" not in request.args:
        # 원본처럼 소스 공개
        return Response(open(__file__).read(), mimetype="text/plain")
    cmd = request.args["cmd"]
    subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)  # 출력 미반환 = Blind
    return "!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9206)
