# 외부 챌린지 2종 + 2022_fsi_edu_challs — 라이브 도커 검증 결과

> 2026-06-29, Windows 11 + Docker Desktop(WSL2, server 29.2.1 / compose v5.0.2).
> 메인 플랫폼(web-pentest-edu)의 **인-레포 26문제**와 **별개**로, "자체 compose" 외부 문제
> (authbypass basic/advanced · secret-tunnel · 2022_fsi_edu_challs)를 실제 기동·풀이한 기록.
> 인-레포 26문제 검증은 `docs/도커검증_결과.md` 참고.

## 0. 요약

| 구분 | 결과 |
|---|---|
| 검증 대상 | 외부 3문제(A1·A2·A3) + FSI 캡스톤(flag 2개) = **5 flag** |
| 결과 | **5/5 PASS** — 모두 라이브 익스플로잇으로 획득, 기준값과 일치 |
| 기동 중 발견·수정한 결함 | **6건**(빌드/런타임/배포 스크립트) |
| flag 대조 | A1~A3 → `web-pentest-edu/.env` 와 일치 · FSI 2개 → repo 하드코딩값과 일치 |

## 1. 문제별 결과표

| id | 출처 | PASS/FAIL | 획득 flag | 기준값 대조 |
|---|---|---|---|---|
| **A1** authbypass-basic | whs1-ctf2-authbypass-chall :: auth-bypass-basic | **PASS** | `flag{...}` | `.env` FLAG_AUTHBYPASS_BASIC ✔ 일치 |
| **A2** authbypass-advanced | whs1-ctf2-authbypass-chall :: auth-bypass-advanced | **PASS** | `flag{...}` | `.env` FLAG_AUTHBYPASS_ADV ✔ 일치 |
| **A3** secret-tunnel | whs2-ctf-chall-secret-tunnel | **PASS** | `flag{...}` | `.env` FLAG_SECRET_TUNNEL ✔ 일치 |
| **B-1** FSI · XSS flag | 2022_fsi_edu_challs (`mysql/init.sql`) | **PASS** | `fsi2022{n0w_you_4re_g00d_at_xss_m4ybe?}` | init.sql 하드코딩 ✔ 일치 |
| **B-2** FSI · SQLi 파일유출 flag | 2022_fsi_edu_challs (`docker/mysql/Dockerfile`) | **PASS** | `fsi2022{yes_y0u_c4n_le4k_fi1e_by_sq1i!}` | Dockerfile 하드코딩 ✔ 일치 |

> 주의(프롬프트 인젝션/디코이): secret-tunnel extserver 에는 **디코이** `flag{dummy_flag_1}` 가 별도로 존재한다.
> 실제 flag 는 내부망 flagserver 의 `/home/flaguser/flag.txt` 이며 위 표의 값이 정답이다.

## 2. 익스플로잇 재현 요약

### A1 — authbypass-basic (arang_bank) · 음수 이체 로직 결함
`/transfer` 가 `amount > 잔액`·`amount > 10억` 만 검사하고 **음수(양수 검증 누락)** 를 막지 않음.
1. 회원가입 → 로그인(세션 `isLogin`).
2. `/transfer_history` 에서 최초 입금(은행 마스터계좌)의 acctno 확보 → 유효한 타 계좌 `to_address`.
3. `POST /transfer to_address=<그 계좌> amount=-2000000000` → 내 잔액 = `10000 - (-2e9)` = 2,000,010,000 (>10억).
4. `GET /getflag` → flag.

### A2 — authbypass-advanced (arang_bank2) · IDOR + 음수 이체
음수 이체 결함은 동일. 단, advanced 의 `transfer_history` 는 계좌번호를 노출하지 않음 → 인가 우회로 보완.
1. 회원가입 → 로그인.
2. **IDOR** `GET /my?userid=admin` (userid 검증 없이 타인 정보 조회) → admin 계좌번호 취득.
3. 그 계좌로 `amount=-2000000000` 음수 이체 → 잔액 >10억 → `/getflag`.

### A3 — secret-tunnel · pickle RCE → SSH 키 피벗 → 내부망 터널
1. **pickle 역직렬화 RCE**: `/process` 의 `verify_signature` 가 소스에 하드코딩된 `SECRET_KEY`(`very_secret_key_do_not_guess`) 로 md5 서명 검증 → 서명 위조. `b'pickle'` 바이트 필터는 `subprocess.check_output` 페이로드로 우회(출력이 HTTP 응답에 반환).
2. **키 피벗**: appuser 의 `/home/appuser/.ssh/id_rsa` 로 `ctfuser@intserver` 에 SSH 포트포워딩(`-L 19922:flagserver:22`). ctfuser 는 제한쉘이지만 `AllowTcpForwarding yes` 라 포워딩만 사용.
3. **내부망 도달**: 터널 경유로 `flaguser@flagserver` 비밀번호 로그인(`secretpassword1!`, 소스 `flagserver_password.txt`). appuser 가 non-root 라 sshpass 불가 → `SSH_ASKPASS` 로 비번 자동입력.
4. `cat /home/flaguser/flag.txt` → flag. (검증 로그: `uid=1001(flaguser)` 확인)

### B-1 — FSI · 저장형 XSS(첨부파일명) → admin 봇 → 내부 flag 회수
`int/templates/view.html` 가 첨부파일명을 `href="javascript:fileDown('{{filepath}}')"` 에 **무이스케이프** 렌더하고, admin 봇이 `id=uploadFile` 를 **자동 클릭**. `safeQuery` 는 작은따옴표(`'`)를 이스케이프하지 않음 → 파일명이 XSS 벡터.
1. ext(:9090)에 첨부파일명 = XSS 페이로드인 글 작성(공유 board 테이블에 저장).
2. admin 봇이 int(:9090) 로그인 후 글 열람 → uploadFile 클릭 → 페이로드 실행.
3. `fileDown()` 의 `location.replace` 가 즉시 페이지 이동시키므로 **동기 XHR** 사용: admin 세션으로 `/board/1`(flag 글) 읽어 → `/write` 로 board 에 재게시(author=공격자).
4. ext 에서 재게시 글 회수 → flag.

> 봇 재현 메모: 원본 int 봇(`int/bot/bot.py`)은 환경 노후화로 동작 불가(§3-④). 라이브 검증은 동일 동작
> (admin 로그인 → 글 열람 → uploadFile 클릭)을 **selenium standalone-chrome 컨테이너를 같은 compose 네트워크
> (172.22.0.0/24)에 붙여** 수행. 취약점/체인 자체는 앱(ext/int/mysql)에 그대로 존재한다.

### B-2 — FSI · SQLi 파일유출(LOAD_FILE)
`ext/app.py` 의 `download(filepath)` 는 **`safeQuery` 미적용** → `filepath` 가 그대로 SQL 에 삽입.
`GET /download?filepath=x" union select load_file("/upload/flag.txt") -- -`
→ 결과(loginid)가 "file owner(...)≠loginid(...)" 에러 메시지에 **반영** → flag 유출.
(MySQL user 에 `FILE` 권한, `--secure-file-priv=/upload/` 라 `/upload/flag.txt` 읽기 허용.)

## 3. 기동 중 발견·수정한 결함 (★ 없으면 풀이/배포 불가)

| # | 파일 | 증상 | 원인 | 수정 |
|---|---|---|---|---|
| 1 | secret-tunnel `docker/extserver/Dockerfile` | **빌드 파싱 에러** `unknown instruction: echo` (line 44) | 업스트림 오타 — `echo "flag{dummy_flag_1}" > flag.txt` 줄에 `RUN` 누락 | 해당 줄에 `RUN ` 접두 추가 |
| 2 | secret-tunnel `src/ssh_keys/id_rsa`·`id_rsa.pub` | **피벗 불가** — 키 파일이 11바이트 `[REDACTED]` 플레이스홀더 | 공개 레포라 실제 개인키를 커밋하지 않고 가림 | 실제 RSA 2048 키쌍 생성해 교체(extserver authorized_keys·intserver authorized_keys 일치) |
| 3 | (clone 공통) `*.sh`/`entrypoint.sh`/`Dockerfile`/`id_rsa` | arang_bank **Exited(127)** `entrypoint.sh: not found`; alpine 스크립트·ssh키 파싱 실패 | Windows git `autocrlf` 로 clone 시 **CRLF** 변환 → 셸 shebang·키 포맷 깨짐 | 컨테이너용 파일을 **LF** 로 정규화 |
| 4 | FSI `int/bot/bot.py` 실행환경 | admin **XSS 봇 동작 불가** | ① `entrypoint.sh` 가 chrome `.deb` 를 `/app` 에 받고 `/app/bot` 에서 설치(경로 오류) ② 번들 chromedriver=105 인데 `current`(v150) chrome 설치 시도 → **버전 불일치** ③ base=Ubuntu 18.04(EOL)라 최신 chrome glibc 부적합·구버전 .deb 는 Google 에서 삭제됨 | 환경 노후화 이슈. 라이브 검증은 **selenium standalone-chrome 컨테이너**를 봇으로 사용해 체인 재현. 교안 배포본은 chrome+chromedriver **버전 핀 고정(빌드시 동시 설치)** 또는 봇 컨테이너 교체 권장 |
| 5 | FSI `ext/app.py` `/report` | SSRF 트리거가 봇에 도달 못 함 | 봇 주소 하드코딩이 **`172.30.0.4:9000`** (현재 compose 서브넷은 172.22.0.0/24, 봇=172.22.0.4) | `172.22.0.4:9000` 으로 교정 |
| 6 | FSI `docker-compose.yml` | external-server **Exited(1)** `Can't connect to MySQL ... Connection refused` | mysql init 전에 app.py 가 import 시점에 DB 접속 → 경쟁(race) | ext·int 서비스에 `restart: on-failure` 추가 → DB 준비까지 자동 재기동(검증: 2회 재시작 후 정상) |

### 배포 스크립트 보강(재배포 시 #1~#3 자동화)
clone 은 매번 덮어쓰므로, 위 #1~#3 을 `setup_external` 에 통합해 **`gen_flags → setup_external → compose up`** 가 깨끗이 동작하도록 함:
- `setup_external.sh` / `setup_external.ps1`:
  - secret-tunnel clone 후 **실제 SSH 키쌍 생성**(플레이스홀더 교체),
  - extserver Dockerfile **RUN 누락 교정**(sed/Replace),
  - 클론된 셸/Dockerfile/키 **CRLF→LF 정규화**.

## 4. 수정 파일 목록

**플랫폼(재배포 자동화) — 영구:**
- `web-pentest-edu/setup_external.sh` — SSH 키 생성 + extserver RUN 교정 + CRLF→LF 정규화 추가
- `web-pentest-edu/setup_external.ps1` — 동일(PowerShell, `Normalize-Eol` 함수 추가)

**FSI 챌린지 — 영구:**
- `2022_fsi_edu_challs-main/.../ext/app.py` — `/report` SSRF 대상 `172.30.0.4`→`172.22.0.4`
- `2022_fsi_edu_challs-main/.../docker-compose.yml` — external_server·internal_server 에 `restart: on-failure`

**외부 챌린지 clone 산출물 — 이번 런에서 수동 적용(이후엔 setup_external 가 자동 처리):**
- `challenges/capstone/secret-tunnel/docker/extserver/Dockerfile` — line 44 `RUN` 추가
- `challenges/capstone/secret-tunnel/src/ssh_keys/id_rsa`·`id_rsa.pub` — 실제 키쌍 생성
- `challenges/auth/authbypass-basic`·`authbypass-advanced` `entrypoint.sh`·`Dockerfile` + secret-tunnel 셸/키 — CRLF→LF

## 5. 환경 / 네트워크 메모

- **컨테이너명/포트 충돌**: authbypass-basic 과 FSI 가 둘 다 `container_name: mysql-db` → 동시 기동 불가. A 군(basic+secret-tunnel) 먼저 검증 후 down → FSI 기동 순서로 진행. advanced 는 `mysql-db2`/`arang_bank2` 라 충돌 없음. 포트: basic 9001-3 / advanced 9005 / secret-tunnel 8090·2222 / FSI 9090 — 상호 및 메인스택(9000·91xx·92xx)과 무충돌.
- **네트워크 풀 충돌**: FSI 는 `172.22.0.0/24` 고정 + 앱이 IP 하드코딩(mysql=172.22.0.5, 봇=172.22.0.4). 기존 유휴 네트워크 `rcelab`(172.22.0.0/16)과 겹쳐 기동 실패 → 사용 컨테이너 0개 확인 후 `docker network rm rcelab` 로 해소.
- **기동 절차**: `gen_flags`(`.env` 존재) → `setup_external` → 각 폴더 `docker compose up -d --build`.

## 6. 정리(cleanup)

검증 종료 후 외부 3 + FSI 스택은 `docker compose down` 으로 정리. (메인 web-pentest-edu 26문제 스택은
본 검증 범위 밖 — Docker Desktop 재기동 시 restart 정책으로 자동 복귀해 있던 것으로, 그대로 둠.)
