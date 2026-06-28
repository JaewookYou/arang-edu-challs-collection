# web-pentest-edu — 모의해킹 웹 실습 플랫폼

버그클래스별 CTF 실습 + 모의해킹 실전형 문제 + 캡스톤을, **플랫폼/문제 분리** 구조로 운영하는 교육용 저장소.

## 핵심 구조
```
platform/   스코어보드 전용 (registry.yaml 만 읽어 목록·채점·랭킹). 문제 호스팅 X
bot/        공용 headless-chromium 봇 (클라이언트 문제용, 내부망 전용)
_base/      공통 골격(flask_board 등) — 문제는 '취약한 부분'만 남긴다
challenges/<category>/<id>/   문제 1개 = 1 자기완결 폴더
            └ challenge.yaml · Dockerfile · app.py(또는 src) · solution/ · README.md
```

## 빠른 시작

### Windows PowerShell (권장)
```powershell
.\start.ps1                 # 메인+외부 챌린지 한 번에: Docker확인→플래그→빌드·기동→db대기→스코어보드 열기
.\start.ps1 -Profile client # 특정 카테고리만 (client/injection/auth/logic/server/jsp/capstone/day1/day2)
.\start.ps1 -NoExternal     # 외부 GitHub 챌린지 제외(메인 스택만 기동)
.\start.ps1 -KeepEnv        # 기존 .env(플래그) 유지
.\start.ps1 -Down           # 전체 정리(외부 챌린지 포함)
#   스코어보드 : http://localhost:9000   ·   예시 문제 : http://localhost:9101 (xss-1)
#   외부 챌린지(authbypass :9001/:9005 · secret-tunnel :8090/SSH2222)는 기본 포함.
#   폴더가 없으면 start.ps1 이 setup_external.ps1 을 자동 실행(clone+플래그주입, git 필요).
```

### Linux / macOS (권장)
```bash
chmod +x start.sh               # 최초 1회
./start.sh                      # 메인+외부 챌린지 한 번에: Docker확인→플래그→빌드·기동→db대기→스코어보드 열기
./start.sh --profile client     # 특정 카테고리만 (client/injection/auth/logic/server/jsp/capstone/day1/day2)
./start.sh --no-external        # 외부 GitHub 챌린지 제외(메인 스택만 기동)
./start.sh --keep-env           # 기존 .env(플래그) 유지
./start.sh --down               # 전체 정리(외부 챌린지 포함)
#   외부 챌린지(authbypass :9001/:9005 · secret-tunnel :8090/SSH2222)는 기본 포함(setup_external.sh 자동 호출).
```
수동(Makefile):
```bash
./gen_flags.sh && make up       # 전체 기동 · make up-client(카테고리) · make down
```

## 문제 추가 방법
1. `challenges/<category>/<id>/` 생성 → `app.py`(또는 src) + `challenge.yaml` + `Dockerfile` + `README.md` + `solution/`.
2. 클라이언트 게시판류면 `_base/flask_board` 의 `create_app(...)` 에 취약 옵션만 전달.
3. `platform/registry.yaml` 에 항목 추가(status: ready), `gen_flags.sh` 에 `FLAG_*` 추가.
4. `docker-compose.yml` 에 서비스 + 프로필 추가.

## 현재 상태
- ✅ 인프라: platform(스코어보드: 회원가입·로그인·랭킹) / bot / db(MariaDB) / _base / docker-compose / gen_flags / Makefile
- ✅ **29문제 등록(ready)** — client 8 · injection 8 · **auth 4** · logic 1 · server 3 · jsp 3 · **capstone 2**
  - 검증완료(실 익스플로잇→flag): server-side 7 + csrf 2 + xss/domclob/proto(jsdom) → 13문제
  - 원본 기믹 1:1 복원: xss/csrf/xsleak/sqli/lfi/cmdi/domclob/proto (`../문답해설.txt` 그대로)
  - 정적 코드리뷰 완료(`docs/REVIEW.md`): 빌드컨텍스트·플래그 주입·DB연동 정합. **실 docker build/run 은 배포 호스트에서 1회 필요**
- **PHP·고난도 캡스톤 제외**: 금융권 담당자 대상이라 `php-chain`·`fsi-chain` 제거. 대신 ↓ 외부 챌린지 도입.
- 캡스톤 2종: `jsp-chain`(WEB-INF→탈취, :9711) · `secret-tunnel`(SSH 터널/피벗→내부 flag, :8090, 외부레포)
- **외부 GitHub 챌린지(클론)** — `./setup_external.sh`(Windows: `.\setup_external.ps1`) 로 받아 배치+플래그 주입:
  - `secret-tunnel` (캡스톤) ← github.com/JaewookYou/whs2-ctf-chall-secret-tunnel
  - `authbypass-basic`·`authbypass-advanced` (auth, 금융 은행 인증우회) ← github.com/JaewookYou/whs1-ctf2-authbypass-chall
- 배포: `docs/DEPLOY.md` (외부 챌린지 §3 포함) · 검증 재현: `tools/verify/VERIFY.md`
- 검증 재현: `tools/verify/VERIFY.md`
## 주의 (교육용)
의도적으로 취약한 코드입니다. 격리된 실습 환경에서만 사용하세요. 인터넷에 그대로 노출 금지.
