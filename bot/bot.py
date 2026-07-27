# -*- coding: utf-8 -*-
"""
공용 봇 — 클라이언트 사이드 문제용. /visit 로 받은 URL을, 같은 오리진에
admin 으로 로그인한 상태로 headless Chromium 으로 방문한다.
내부망 전용(호스트에 노출하지 않음).
"""
import os, time, signal, threading, traceback
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

# 동시에 띄우는 크롬 수 제한. 수강생이 몰려 신고하면 Flask 가 요청마다 스레드를 만들고
# 크롬이 그만큼 뜨면서 메모리·PID 를 잠식해 'session not created / Resource temporarily
# unavailable' 로 봇 전체가 죽는다(실제 발생: 컨테이너에 크롬 잔여 프로세스 9천여 개).
MAX_CONCURRENT = int(os.environ.get("BOT_MAX_CONCURRENT", "3"))
_slots = threading.Semaphore(MAX_CONCURRENT)


def make_driver():
    opts = Options()
    opts.binary_location = CHROME_BIN
    for a in ["--headless=new", "--no-sandbox", "--disable-gpu",
              "--disable-dev-shm-usage", "--window-size=1200,800",
              "--disable-software-rasterizer",
              # crashpad 핸들러가 방문마다 남는다(정리 안 됨) → 아예 끈다.
              # (--no-zygote 는 브라우저 종료 후 렌더러가 고아로 남아 오히려 누수가 커진다)
              "--disable-crash-reporter", "--disable-breakpad",
              "--disable-background-networking", "--disable-component-update"]:
        opts.add_argument(a)
    svc = Service(CHROMEDRIVER)
    return webdriver.Chrome(service=svc, options=opts), svc


def _proc_age(pid):
    """프로세스 나이(초). /proc 만으로 계산(이미지에 ps·psutil 이 없다)."""
    with open("/proc/%s/stat" % pid, "rb") as f:
        starttime = int(f.read().rsplit(b") ", 1)[1].split()[19])   # 22번째 필드
    with open("/proc/uptime") as f:
        uptime = float(f.read().split()[0])
    return uptime - starttime / os.sysconf("SC_CLK_TCK")


def reaper(max_age=45, interval=15):
    """크롬 기동 실패·행(hang) 시 driver.quit() 로도 못 거두는 잔여 프로세스가 남는다.
    정상 방문은 페이지로드 8s + 대기 3s 로 15초 안에 끝나므로, 45초를 넘긴 크롬 계열은
    확실히 찌꺼기다. 짧은 주기로 돌려 누적(→ fork 실패로 봇 전체 정지)을 막는다."""
    while True:
        time.sleep(interval)
        # (1) 좀비 수거 — 이게 핵심이다. 봇이 컨테이너 PID 1 이라 고아가 된 크롬이 이쪽에
        #     붙는데, 종료상태를 안 거두면 좀비로 남아 PID 를 잠식하다 fork 가 실패하고
        #     'session not created / Resource temporarily unavailable' 로 봇이 통째로 멎는다.
        while True:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
            except ChildProcessError:
                break
            except Exception:
                break
        # (2) 살아남은 찌꺼기 크롬 정리
        killed = 0
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                with open("/proc/%s/comm" % pid) as f:
                    comm = f.read().strip()
                if not comm.startswith(("chrome", "chromium")):
                    continue
                if _proc_age(pid) > max_age:
                    os.kill(int(pid), signal.SIGKILL)
                    killed += 1
            except Exception:
                pass
        if killed:
            print("[bot] reaped %d stale chrome processes" % killed, flush=True)


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
    if not _slots.acquire(timeout=120):        # 대기열이 밀리면 요청을 흘려보낸다
        print("[bot] busy — skipped", flush=True)
        return "bot busy", 503
    d = svc = None
    try:
        d, svc = make_driver()
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
        if svc:                 # 드라이버 생성이 실패해도 chromedriver 는 떠 있을 수 있다
            try:
                svc.stop()
            except Exception:
                pass
        _slots.release()
    return "visited"


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    threading.Thread(target=reaper, daemon=True).start()
    app.run(host="0.0.0.0", port=9099)
