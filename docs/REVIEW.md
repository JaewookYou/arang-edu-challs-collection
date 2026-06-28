# REVIEW — 미검증 문제 정적 코드리뷰

도커가 없는 환경이라 **실 빌드/실행 대신 정적 점검**(Dockerfile·소스·플래그 주입·포트·DB 연동 정합성)을 수행. 대상: PHP 6 · JSP 3 · 캡스톤 3.

## 결론: 구조적으로 견고, 실 빌드는 배포 호스트에서 1회 필요

## 점검 항목 & 결과
| 항목 | 결과 |
|---|---|
| 빌드 컨텍스트 | 전 PHP/JSP 서비스 `context: ., dockerfile: challenges/.../Dockerfile` → repo root 기준 COPY 정상 ✓ |
| 포트 정합 | registry port ↔ Dockerfile `sed`/`EXPOSE` ↔ compose `ports` 일치(91xx~97xx), 중복 없음 ✓ |
| 플래그 주입 | env→소스 경로 정상. 예: sqli-1 `index.php` 가 `admin` 유출 시 `echo getenv('FLAG_SQLI_1')`; lfi-1 `lfiflag.php` 에 `$FLAG_LFI_1`; lfi-2 `/readflag`(chmod 111); jsp-path `WEB-INF/flag.txt`; sqli-3 는 DB(`${FLAG_SQLI_3}`) ✓ |
| DB 연동 | sqli-1/2/3·jsp-sqli → 공유 `db`(MariaDB). `docker/db/init.sh` 가 `chall` DB·`sqli` 유저·테이블 생성, db 프로필에 injection/jsp 포함 ✓ |
| gen_flags 정합 | registry `flag_env` 27/28종 ↔ gen_flags `FLAG_*` 일치(FSI 추가 반영) ✓ |

## 발견·조치한 이슈
1. **php-chain**: 자체 compose 캡스톤인데 registry 에 `own_compose` 미표시 → **추가함**(fsi-chain·jsp-chain 과 통일).
2. **fsi-chain 신규 편입**: 2022_fsi_edu_challs 를 `challenges/capstone/fsi-chain/` 으로 통합. 플래그를 빌드 ARG(`FLAG_FSI_CHAIN`)로 파라미터화, 외부포트 9090→9721, 컨테이너명 `fsi-*`.

## 배포 호스트에서 반드시 1회 (도커 환경 필요 — 여기선 불가)
```bash
docker compose --profile injection build sqli-1 sqli-2 sqli-3 lfi-1 lfi-2   # PHP
docker compose --profile jsp build jsp-sqli jsp-upload jsp-pathtraversal     # JSP (jsp-sqli 는 maven jar 다운로드=인터넷 필요)
# 캡스톤은 각 폴더 자체 compose 로 build
```
빌드 시 외부 의존: jsp-sqli(maven mysql jar), lfi-2(apt gcc), 베이스 이미지 pull → **폐쇄망이면 미리 build 후 image save/load**.

## 잔여 리스크(런타임에서만 확인 가능)
- 각 문제의 실제 풀이→flag 일치(특히 jsp 3 · 캡스톤 3 은 실행 검증 미완).
- fsi 내부 SSRF 의 정적 IP·NET_RAW 의존(호스트 docker 설정에 따라 동작 차이).
