# -*- coding: utf-8 -*-
# SSTI — render_template_string 에 사용자 입력 결합 → RCE.
import os
from flask import Flask, request, render_template_string
app = Flask(__name__)
try:
    open("/flag.txt", "w").write(os.environ.get("FLAG_SSTI_1", "flag{local}"))
except Exception:
    pass

@app.route("/")
def index():
    name = request.args.get("name", "world")
    return render_template_string("<h2>hello " + name + "</h2>")  # SSTI sink

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9207)
