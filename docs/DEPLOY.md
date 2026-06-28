# DEPLOY — 서버 배포 가이드

수강생이 **내 서버**를 통해 실습하도록 web-pentest-edu 를 배포하는 절차. 연습문제 3종이 모두 들어있다:

| 유형 | 내용 | 접근 방식 |
|---|---|---|
| ① 기법문제 | xss·csrf·xsleak·sqli·lfi·cmdi·ssti·xxe·domclob·proto·open-redirect (22) | 스코어보드(:9000) 또는 문제 단독 포트(91xx~95xx) |
| ② 워게임 플랫폼 | 회원가입·로그인·랭킹 스코어보드 + 위 문제들 채점 | http://서버:9000 (회원가입 후 풀이) |
| ③ 심화(캡스톤) | php-chain(LFI→…→RCE) · jsp-chain(WEB-INF→탈취) · **fsi-chain(SSRF→MySQL)** | 자체 compose, 9701/9711/9721 |

---

## 0. 사전 요구사항 (배포 호스트)
- **OS**: Linux 서버 또는 **Windows(Docker Desktop)** 둘 다 지원. Windows 절차는 §1-W 참고.
- **Docker** 24+ 와 **Docker Compose v2** (`docker compose ...`). Windows 는 **Docker Desktop(WSL2 백엔드)**.
- **인터넷 연결(빌드 시)** — 일부 이미지가 빌드 중 외부에서 받는다:
  - `jsp-sqli` : maven 에서 `mysql-connector-j` jar 다운로드.
  - `lfi-2` : `apt-get install gcc` (readflag 컴파일).
  - 베이스 이미지(php/tomcat/mariadb/python) pull.
  - → **폐쇄망 배포면** 인터넷 되는 곳에서 한 번 `docker compose build` 후 이미지를 `docker save/load` 로 옮긴다.
- **fsi-chain 캡스톤**은 `internal_server` 가 `NET_ADMIN/NET_RAW`(raw packet) 권한을 요구 → 호스트 docker 가 이 cap 허용해야 함(기본 OK, 일부 관리형 호스팅은 제한).
- 디스크 ~5GB(이미지), 포트 9000 및 91xx~97xx 개방 가능해야 함.

## 1. 빠른 배포 (전체 기동)
```bash
cd web-pentest-edu
./gen_flags.sh                 # 1) 랜덤 플래그 .env 생성 (1회, 재배포 시 새로 생성하면 플래그 갱신)
make up                        # 2) 전체 빌드+기동 (= docker compose --profile all up -d --build)
docker compose ps             # 상태 확인
```
- 스코어보드: `http://서버:9000` → 회원가입 → 문제 목록·풀이·랭킹.
- 예시 문제 단독: `http://서버:9101` (xss-1) … 포트는 `platform/registry.yaml` 참고.

부분 기동(프로필):
```bash
make up-day1        # Day1 문제만      make up-client     # 클라이언트만
make up-injection   # 인젝션만         make up-day2       # Day2 문제만
docker compose --profile all down      # 전체 종료
```

## 1-W. Windows (Docker Desktop) 에서 빌드/배포
> `make`·`./*.sh` 는 윈도우에 없으므로 **PowerShell 등가물**을 제공한다. (또는 WSL2/Git Bash 에서 기존 `.sh` 를 그대로 써도 된다 — 맨 아래)

**준비**
1. **Docker Desktop** 설치 → 설정에서 **WSL2 기반 엔진** 사용, 실행해 둔다(`docker version` 으로 확인).
2. PowerShell 스크립트 실행 허용(1회): 관리자 PowerShell 에서
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```
3. ⚠️ **줄바꿈(CRLF) 주의** — 동봉한 `.gitattributes` 가 컨테이너용 스크립트를 LF 로 고정한다. git 으로 받지 않고 폴더째 복사했다면, 컨테이너가 `entrypoint.sh: not found` / `\r` 오류를 내는지 보고, 그러면 해당 `.sh`·`init.sh` 를 LF 로 저장(VS Code 우하단 CRLF→LF).

**전체 기동 (PowerShell)**
```powershell
cd web-pentest-edu
.\gen_flags.ps1          # 1) 랜덤 플래그 .env 생성 (gen_flags.sh 의 윈도우판)
.\make.ps1 up            # 2) 전체 빌드+기동 (= docker compose --profile all up -d --build)
.\make.ps1 ps            # 상태 확인
```
- 스코어보드: `http://localhost:9000` (또는 `http://서버IP:9000`).
- `.\make.ps1` 타깃: `flags up down ps logs up-day1 up-day2 up-client up-injection up-auth up-logic up-server up-jsp up-capstone` (Makefile 과 동일).
- make.ps1 없이 직접 써도 됨: `docker compose --profile all up -d --build`.

**캡스톤 (PowerShell)** — 플래그를 .env 에서 뽑아 환경변수로 주입
```powershell
# PHP 체인
cd challenges\capstone\php-chain
$env:FLAG_PHP_CHAIN = (Select-String '^FLAG_PHP_CHAIN=' ..\..\..\.env).Line.Split('=')[1]
docker compose up -d --build          # :9700 공개 / :9701 내부
cd ..\..\..

# FSI 채팅 (NET_RAW 필요 — Docker Desktop/WSL2 는 기본 허용)
cd challenges\capstone\fsi-chain
$env:FLAG_FSI_CHAIN = (Select-String '^FLAG_FSI_CHAIN=' ..\..\..\.env).Line.Split('=')[1]
docker compose up -d --build          # :9721
cd ..\..\..
```

**대안: WSL2 / Git Bash** — 리눅스 절차(§1·§2)를 그대로 사용
```bash
# WSL2 우분투 또는 Git Bash 에서 (Docker Desktop WSL 통합 켜둘 것)
cd /mnt/c/.../web-pentest-edu
./gen_flags.sh && docker compose --profile all up -d --build
```

---

## 2. 외부 GitHub 챌린지 + 캡스톤 (자체 compose)
> 금융권 대상이라 PHP·고난도 캡스톤(`php-chain`·`fsi-chain`)은 **제외**했다. 대신 외부 레포 챌린지를 클론해 쓴다.

**(a) 외부 챌린지 받기 — 1회** (git 필요, `.env` 먼저 생성)
```bash
./gen_flags.sh        # (윈도우: .\gen_flags.ps1)
./setup_external.sh   # (윈도우: .\setup_external.ps1)  ← 2개 레포 clone + 플래그 주입 + 포트 재매핑
```
받아지는 것:
- `challenges/capstone/secret-tunnel/`  ← whs2-ctf-chall-secret-tunnel (SSH 터널/피벗)
- `challenges/auth/authbypass-basic/` · `authbypass-advanced/`  ← whs1-ctf2-authbypass-chall (은행 인증우회)

**(b) 기동** (각 자체 compose, 한 번에 하나씩 권장)
```bash
# JSP 체인 (메인 compose 에 포함)
docker compose up -d --build jsp-chain                                   # :9711

# Secret Tunnel (캡스톤)
cd challenges/capstone/secret-tunnel  && docker compose up -d --build    # 웹 :8090, SSH :2222
cd ../../..

# 은행 인증우회 (auth)
cd challenges/auth/authbypass-basic   && docker compose up -d --build    # :9001–9003
cd ../../..
cd challenges/auth/authbypass-advanced && docker compose up -d --build   # :9005 (컨테이너 내부 9002)
cd ../../..
```
> 윈도우는 §1-W 의 PowerShell 방식과 동일하게 각 폴더에서 `docker compose up -d --build`.
> 플래그는 `setup_external` 가 `.env` 값으로 자동 주입한다(스코어보드 채점 일치). 미실행 시 레포 기본 플래그가 들어있다.

## 3. 포트 체계 (방화벽 개방 대상)
| 대역 | 용도 |
|---|---|
| 9000 | 스코어보드(공개) |
| 9101–9108 | client (xss1-3·csrf1-2·xsleak·domclob·open-redirect) |
| 9201–9208 | injection (sqli1-3·lfi1-2·cmdi·ssti·xxe) |
| 9301–9302 / 9401 | auth(idor·2fa) / logic(race) |
| 9501–9503 | server (upload·ssrf·proto) |
| 9601–9603 | jsp (sqli·upload·pathtraversal) |
| 9700/9701 · 9711 · 9721 | 캡스톤 php-chain · jsp-chain · fsi-chain |

→ 수강생에게 **9000(스코어보드)만** 노출하고 싶다면, 문제 컨테이너 포트는 호스트 바인딩을 `127.0.0.1:` 로 제한하고 스코어보드/리버스프록시를 통해서만 접근하게 한다(아래 4).

## 4. 도메인 · HTTPS (리버스 프록시 권장)
nginx 예시 — `edu.example.com` → 스코어보드, `/c/<port>/` → 각 문제:
```nginx
server {
  listen 443 ssl;  server_name edu.example.com;
  ssl_certificate /etc/letsencrypt/live/edu.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/edu.example.com/privkey.pem;
  location / { proxy_pass http://127.0.0.1:9000; }            # 스코어보드
  # 문제별 서브패스(예: xss-1)
  location /p/9101/ { proxy_pass http://127.0.0.1:9101/; }
  # ... registry 포트만큼 반복 (또는 서브도메인 *.edu.example.com 와일드카드)
}
```
- Let’s Encrypt: `certbot --nginx -d edu.example.com`.
- **클라이언트 문제(xss/csrf/xsleak/domclob/proto)** 는 봇(관리자)이 내부망에서 도는 구조라, 문제 README 의 `needs_bot` 가 true 면 봇 컨테이너가 같이 떠야 한다(`make up` 에 포함).

## 5. 플래그 운영
- `./gen_flags.sh` 가 `flag{...}` 랜덤 생성 → `.env` 기록 → compose 가 각 문제/스코어보드에 주입.
- **기수마다 새 플래그**를 원하면 `gen_flags.sh` 재실행 후 `docker compose up -d --build` (DB·바이너리에 박히는 문제는 재빌드 필요: sqli3·lfi·upload·jsp·fsi).
- 스코어보드는 제출 문자열만 `.env` 의 `FLAG_*` 와 비교 → 문제 컨테이너와 직접 통신하지 않음(결합도↓).
- `.env` 는 절대 커밋 금지(`.gitignore` 처리됨).

## 6. 운영 체크리스트
- [ ] `docker compose ps` 전 서비스 `running`/`healthy`.
- [ ] 스코어보드 회원가입→로그인→문제 링크→플래그 제출→랭킹 반영 1회 점검.
- [ ] 기법문제 표본(xss-1·sqli-1·lfi-1) 실제 풀이로 flag 획득 확인.
- [ ] 캡스톤(secret-tunnel·jsp-chain)은 수업/대회 시간에만 별도 기동(리소스·포트 충돌).
- [ ] 외부 노출 포트 최소화(가급적 9000 + 필요한 문제만), 방화벽/보안그룹 설정.
- [ ] 자원: 전체 기동 시 컨테이너 ~30개 → 메모리 4GB+ 권장.

## 7. 트러블슈팅
- **빌드 중 jar/패키지 다운로드 실패** → 호스트 인터넷/프록시 확인(특히 jsp-sqli maven, apt).
- **sqli/jsp-sqli 가 `db error` / DB 연결 실패** → MariaDB 초기화(10~40초) 동안 문제 컨테이너가 먼저 떠서 생기던 **기동 경쟁(readiness race)**. → 해결됨: `db` 에 `healthcheck` 추가 + 의존 문제(`sqli-1/2/3`·`jsp-sqli`)를 `depends_on: { db: { condition: service_healthy } }` 로 변경하여, DB 가 healthy 가 될 때까지 기다린 뒤 기동한다. 그래도 실패하면 `docker compose ps`(db `healthy` 확인)·`docker logs db`(init.sh 가 `chall` DB·`sqli` 유저·테이블 생성했는지) 점검.
- **client(XSS/CSRF 등) 봇이 문제에 안 닿음** → 봇이 방문할 URL 은 반드시 **서비스명**(예: `http://xss-1:9101/...`)으로 입력. `localhost`/공인 IP 로 입력하면 봇 컨테이너가 자기 자신을 치게 되어 실패한다. 봇은 무프로필이라 항상 떠 있음(`docker logs bot` 으로 방문 로그 확인).
- **포트 충돌** → 이미 점유된 호스트 포트면 compose 의 `ports:` 좌측(호스트) 값만 변경.
