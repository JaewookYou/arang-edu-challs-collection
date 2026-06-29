#!/usr/bin/env bash
# 실습 환경 한 번에 구성 (Linux / macOS) — start.ps1 의 셸 버전
# ─────────────────────────────────────────────────────────────
# Docker 확인 → 플래그(.env) 생성 → 빌드·기동 → db healthy 대기
# → 상태 출력 → 스코어보드(http://localhost:9000) 자동 열기
#
# 사용 예:
#   ./start.sh                     # 메인(all) + 외부 챌린지(authbypass·secret-tunnel) 자동 기동 + 스코어보드 열기
#   ./start.sh --profile client    # 특정 카테고리만 (client/injection/auth/logic/server/jsp/capstone/day1/day2)
#   ./start.sh --keep-env          # 기존 .env(플래그) 유지(재생성 안 함)
#   ./start.sh --no-browser        # 브라우저 자동 열기 끄기
#   ./start.sh --no-external       # 외부 GitHub 챌린지 제외(메인 스택만 기동)
#   ./start.sh --with-fsi          # FSI(2022_fsi_edu_challs, :9090)도 함께 기동(상위 폴더 레포)
#   ./start.sh --down              # 전체 정리(메인 + 외부 + FSI 컨테이너·네트워크 제거)
#
# ※ 외부 챌린지(authbypass-basic/advanced·secret-tunnel)는 기본으로 함께 기동되며, 매 기동 시
#    setup_external.sh 를 호출해 '현재 .env' 플래그를 재주입한다(폴더 없으면 clone 까지).
#    → gen_flags 로 .env 를 새로 만들어도 외부 챌린지 flag 가 스코어보드와 항상 일치.
#    FSI 는 별도 레포 + 10.111.0.0/24 고정이라 --with-fsi 일 때만(메인보다 먼저) 기동.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1
FSI_DIR="$SCRIPT_DIR/challenges/capstone/fsi-chat"   # setup_external 이 여기로 clone (레포 내부)

EXT_DIRS=(
  "challenges/auth/authbypass-basic"
  "challenges/auth/authbypass-advanced"
  "challenges/capstone/secret-tunnel"
)

info(){ printf '\033[36m[*] %s\033[0m\n' "$1"; }
ok(){   printf '\033[32m[+] %s\033[0m\n' "$1"; }
warn(){ printf '\033[33m[!] %s\033[0m\n' "$1"; }

# 외부 챌린지 기동 시 적용할 -f 인자(현재 디렉터리 기준).
#   docker-compose.hostnet.yml(있으면) = 빌드 시 host 네트워크 사용 → DNS 제약 환경에서도 빌드 성공.
#   (setup_external.sh 가 secret-tunnel·fsi-chat 에 이 override 를 생성한다)
compose_overrides(){
  local a="-f docker-compose.yml"
  [ -f docker-compose.hostnet.yml ] && a="$a -f docker-compose.hostnet.yml"
  echo "$a"
}

open_url(){
  if   command -v xdg-open >/dev/null 2>&1; then xdg-open "$1" >/dev/null 2>&1 &
  elif command -v open     >/dev/null 2>&1; then open     "$1" >/dev/null 2>&1 &
  fi
}

# ── 인자 파싱 ──
PROFILE=all; DOWN=0; KEEPENV=0; NOBROWSER=0; NOEXTERNAL=0; WITHFSI=0
while [ $# -gt 0 ]; do
  case "$1" in
    --profile)     PROFILE="$2"; shift 2 ;;
    --profile=*)   PROFILE="${1#*=}"; shift ;;
    --down)        DOWN=1; shift ;;
    --keep-env)    KEEPENV=1; shift ;;
    --no-browser)  NOBROWSER=1; shift ;;
    --no-external) NOEXTERNAL=1; shift ;;
    --with-fsi)    WITHFSI=1; shift ;;
    --external)    shift ;;   # (호환용) 외부 챌린지는 기본 기동 — 무시
    -h|--help)     sed -n '2,21p' "$0"; exit 0 ;;
    *)             warn "알 수 없는 옵션: $1"; shift ;;
  esac
done

# ── 정리 모드 ──
if [ "$DOWN" = 1 ]; then
  info "전체 정리 (docker compose --profile all down)..."
  docker compose --profile all down
  for d in "${EXT_DIRS[@]}"; do
    if [ -f "$d/docker-compose.yml" ]; then
      info "외부 챌린지 정리: $d"
      ( cd "$d" && docker compose down )
    fi
  done
  if [ -f "$FSI_DIR/docker-compose.yml" ]; then
    info "FSI 정리: $FSI_DIR"
    ( cd "$FSI_DIR" && docker compose down )
  fi
  ok "정리 완료."
  exit 0
fi

# ── 0) Docker 확인 ──
info "Docker 상태 확인..."
if ! docker info >/dev/null 2>&1; then
  warn "Docker 에 연결할 수 없습니다. Docker 데몬을 먼저 실행한 뒤 다시 시도하세요."
  exit 1
fi
ok "Docker 정상."

# ── 1) 플래그(.env) 생성 ──
if [ "$KEEPENV" = 1 ] && [ -f .env ]; then
  info ".env 유지(--keep-env) — 플래그 재생성 생략."
else
  info "플래그 생성 (.env)..."
  bash ./gen_flags.sh
fi

# ── 1.5) FSI (옵션) — 고정 대역(10.111.0.0/24, docker 기본 풀 밖)이라 메인/외부와 충돌 없음 ──
if [ "$WITHFSI" = 1 ]; then
  if [ ! -f "$FSI_DIR/docker-compose.yml" ]; then
    info "FSI 폴더 없음 → setup_external.sh 로 clone+보정(레포 내부 challenges/capstone/fsi-chat)..."
    bash ./setup_external.sh || warn "setup_external 실패 (git/네트워크 확인)"
  fi
  if [ -f "$FSI_DIR/docker-compose.yml" ]; then
    info "FSI 기동(메인보다 먼저): $FSI_DIR"
    ( cd "$FSI_DIR" && docker compose $(compose_overrides) up -d --build )
    ok "FSI 채팅: http://localhost:9090  (스코어보드 fsi-chat-xss / fsi-chat-sqli)"
  else
    warn "FSI 폴더 없음: $FSI_DIR  → --with-fsi 건너뜀"
  fi
fi

# ── 2) 빌드·기동 ──
info "빌드·기동 (profile=$PROFILE) — 최초 빌드는 수 분 소요될 수 있습니다..."
if ! docker compose --profile "$PROFILE" up -d --build; then
  warn "기동 실패 — 위 로그를 확인하세요. (이미지 빌드/네트워크 문제일 수 있음)"
  exit 1
fi

# ── 3) db(MariaDB) 준비 대기 — db 가 기동된 프로필일 때만 ──
if docker ps --format '{{.Names}}' | grep -qx db; then
  info "db(MariaDB) 준비 대기 — healthy 까지 (sqli/jsp 문제 정상화)..."
  h=""
  for _ in $(seq 1 50); do          # 50 × 3s = 150s
    sleep 3
    h="$(docker inspect -f '{{.State.Health.Status}}' db 2>/dev/null || true)"
    echo "    db: $h"
    [ "$h" = "healthy" ] && break
  done
  if [ "$h" = "healthy" ]; then ok "db healthy — sqli/jsp 문제 정상."
  else warn "db 가 아직 준비되지 않았습니다($h). 잠시 후 'docker compose ps' 로 재확인하세요."; fi
fi

# ── 4) 상태 출력 ──
info "컨테이너 상태:"
docker compose --profile "$PROFILE" ps

# ── 5) 스코어보드 ──
BOARD="http://localhost:9000"
ok "스코어보드: $BOARD  (회원가입 → 로그인 → flag 제출)"
[ "$NOBROWSER" = 1 ] || open_url "$BOARD"

# ── 6) 외부 GitHub 챌린지 (기본 기동, --no-external 로 제외) ──
if [ "$NOEXTERNAL" != 1 ]; then
  # 매번 setup_external 호출(멱등): 폴더 없으면 clone, 있으면 '현재 .env' 플래그 재주입.
  info "외부 챌린지 배치/플래그 재주입 (setup_external.sh)..."
  bash ./setup_external.sh || warn "setup_external 실패 (네트워크/git 확인)"
  for d in "${EXT_DIRS[@]}"; do
    if [ -f "$d/docker-compose.yml" ]; then
      info "외부 챌린지 기동: $d"
      ( cd "$d" && docker compose $(compose_overrides) up -d --build )
    else
      warn "외부 챌린지 폴더 없음: $d  → ./setup_external.sh 수동 실행 필요"
    fi
  done
  ok "외부 챌린지: authbypass-basic :9001 · authbypass-advanced :9005 · secret-tunnel :8090(SSH 2222)"
else
  info "외부 챌린지 제외(--no-external)."
fi

echo
ok "준비 완료! 정리하려면:  ./start.sh --down"
