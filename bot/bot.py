# -*- coding: utf-8 -*-
"""
공용 봇 — 클라이언트 사이드 문제용. /visit 로 받은 URL을, 같은 오리진에
admin 으로 로그인한 상태로 headless Chromium 으로 방문한다.
내부망 전용(호스트에 노출하지 않음).
"""
import os, time, traceback
from urllib.parse import urlparse
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

app = Flask(__name__)
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "admin")
CHROME_BIN = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
CHROMEDRIVER = os.environ.get("CHROMEDRIVER", "/usr/bin/chromedriver")


def make_driver():
    opts = Options()
    opts.binary_location = CHROME_BIN
    for a in ["--headless=new", "--no-sandbox", "--disable-gpu",
              "--disable-dev-shm-usage", "--window-size=1200,800"]:
        opts.add_argument(a)
    return webdriver.Chrome(service=Service(CHROMEDRIVER), options=opts)


def origin(u):
    p = urlparse(u)
    return f"{p.scheme}://{p.netloc}"


@app.route("/visit", methods=["POST"])
def visit():
    chal = request.form.get("chal", "")
    url = request.form.get("url", "")
    if not url.startswith("http"):
        return "bad url", 400
    print(f"[bot] chal={chal} url={url}", flush=True)
    d = None
    try:
        d = make_driver()
        d.set_page_load_timeout(8)
        try:  # admin 로그인 (실패해도 방문은 진행)
            d.get(origin(url) + "/login")
            d.find_element(By.NAME, "userid").send_keys("admin")
            pw = d.find_element(By.NAME, "userpw")
            pw.send_keys(ADMIN_PW)
            pw.submit()
            time.sleep(1)
        except Exception:
            print("[bot] login skipped", flush=True)
        d.get(url)
        time.sleep(3)
    except Exception:
        print(traceback.format_exc(), flush=True)
    finally:
        if d:
            try:
                d.quit()
            except Exception:
                pass
    return "visited"


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9099)
