#!/usr/bin/env bash
# 외부 GitHub 챌린지(secret-tunnel · authbypass basic/advanced)를 배치하고 .env 플래그를 주입.
# 재실행 안전(idempotent): 이미 받은 폴더는 clone 생략하고, 플래그/키/포트/보정만 '현재 .env' 기준으로 다시 적용.
#   → gen_flags 로 .env 를 재생성한 뒤 이 스크립트를 다시 돌리면 외부 챌린지 플래그가 스코어보드와 다시 일치한다.
# (git 필요)  먼저 ./gen_flags.sh 로 .env 를 만들 것.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
[ -f "$ROOT/.env" ] || { echo "[!] 먼저 ./gen_flags.sh 로 .env 를 생성하세요."; exit 1; }
getf(){ grep "^$1=" "$ROOT/.env" | cut -d= -f2-; }
reinject(){ sed -i.bak "s|flag{[^}]*}|$2|" "$1" && rm -f "$1.bak"; }   # 멱등 주입(현재 flag{...} 를 새 값으로)
# build 시 host 네트워크를 쓰도록 compose override 생성(멱등). DNS 제약 환경(컨테이너 UDP/53 차단 +
# 외부 DNS 차단, alpine musl 은 use-vc 미지원)에서도 빌드가 호스트 systemd-resolved 로 DNS 해석하게 한다.
# start.sh/start.ps1 이 'docker-compose.hostnet.yml' 존재 시 자동으로 -f 포함한다.
write_hostnet_override(){   # $1=대상 디렉터리, $2.. = 서비스명들
  local dir="$1"; shift; local f="$dir/docker-compose.hostnet.yml"
  { echo "# [자동생성: setup_external.sh] build 시 host 네트워크 사용 → DNS 제약 환경 빌드 보정.";
    echo "services:";
    for s in "$@"; do printf '  %s:\n    build:\n      network: host\n' "$s"; done
  } > "$f"
}
# [보정] compose 에 'restart: unless-stopped' 주입(멱등). 업스트림 compose 4종엔 restart 정책이 없어
# 호스트/도커 데몬 재시작(재부팅) 시 컨테이너가 죽은 채 남았다(exit 255) — 메인 스택은 전부
# unless-stopped 라 자동 복구되는데 외부 챌린지만 수동 기동이 필요했던 원인.
add_restart(){   # $1=compose 파일, $2.. = 서비스명들
  local f="$1"; shift
  [ -f "$f" ] || return 0
  sed -i.bak '/^[[:space:]]\+restart:[[:space:]]/d' "$f"                              # 기존 정책 제거(멱등·on-failure 포함)
  for s in "$@"; do sed -i.bak "s|^  $s:[[:space:]]*$|  $s:\n    restart: unless-stopped|" "$f"; done
  rm -f "$f.bak"
}

# [보정] compose 에 메모리·PID 상한 주입(멱등). 업스트림 compose 엔 상한이 없다.
# secret-tunnel 은 설계상 pickle 역직렬화 RCE 라 수강생 페이로드가 Flask 프로세스 안에서
# 그대로 돈다. 상한이 없으면 그 프로세스가 호스트 메모리를 다 먹고 커널이 전역 OOM 을
# 내며 서버 전체가 멎는다(실제 발생: 7/27~7/29 6회, 마지막엔 호스트가 2시간 반 정지 →
# 그 사이 저장 중이던 플랫폼 users.json 까지 잘려 나갔다). 상한을 걸면 사고가 해당
# 컨테이너 하나로 격리되고 restart 정책이 즉시 되살린다.
strip_limits(){  # $1=compose 파일 — 기존 주입분 제거(멱등)
  [ -f "$1" ] || return 0
  sed -i.bak '/^[[:space:]]\+\(mem_limit\|memswap_limit\|pids_limit\):[[:space:]]/d' "$1"
  rm -f "$1.bak"
}
add_limits(){    # $1=compose 파일, $2=메모리(512m), $3=PID 수, $4.. = 서비스명들
  local f="$1" mem="$2" pids="$3"; shift 3
  [ -f "$f" ] || return 0
  for s in "$@"; do
    sed -i.bak "s|^  $s:[[:space:]]*$|  $s:\n    mem_limit: $mem\n    memswap_limit: $mem\n    pids_limit: $pids|" "$f"
  done
  rm -f "$f.bak"
}

ST="$ROOT/challenges/capstone/secret-tunnel"
AB_B="$ROOT/challenges/auth/authbypass-basic"
AB_A="$ROOT/challenges/auth/authbypass-advanced"

# ── (1) secret-tunnel ──
if [ ! -d "$ST" ]; then
  echo "[*] secret-tunnel clone..."
  git clone --depth 1 https://github.com/JaewookYou/whs2-ctf-chall-secret-tunnel "$ST"
else
  echo "[*] secret-tunnel 존재 — clone 생략(플래그/보정 재적용)"
fi
reinject "$ST/docker/flagserver/Dockerfile" "$(getf FLAG_SECRET_TUNNEL)"     # flagserver flag
# ssh 키: 없거나 '[REDACTED]' 플레이스홀더면 실제 RSA 키쌍 생성(피벗 동작 필수)
KEYS="$ST/src/ssh_keys"
if [ ! -f "$KEYS/id_rsa" ] || ! grep -q "PRIVATE KEY" "$KEYS/id_rsa" 2>/dev/null; then
  echo "[*] secret-tunnel ssh 키 생성(플레이스홀더 교체)"
  rm -f "$KEYS/id_rsa" "$KEYS/id_rsa.pub"
  ssh-keygen -t rsa -b 2048 -N "" -C "appuser@extserver" -f "$KEYS/id_rsa" >/dev/null
fi
# extserver Dockerfile 업스트림 오타: 'echo ... > flag.txt' 줄에 RUN 누락(멱등: ^echo 만 매치)
sed -i.bak 's|^echo "flag{dummy_flag_1}"|RUN echo "flag{dummy_flag_1}"|' "$ST/docker/extserver/Dockerfile" && rm -f "$ST/docker/extserver/Dockerfile.bak"
# alpine(musl) 3개 이미지 — host 네트워크 빌드 override(DNS 보정)
write_hostnet_override "$ST" extserver intserver flagserver
add_restart "$ST/docker-compose.yml" extserver intserver flagserver   # 재부팅 후 자동 복구
strip_limits "$ST/docker-compose.yml"                                 # 폭주 격리(호스트 전체 OOM 방지)
add_limits   "$ST/docker-compose.yml" 512m 256 extserver intserver flagserver

# ── (2) authbypass basic/advanced ──
if [ ! -d "$AB_B" ] || [ ! -d "$AB_A" ]; then
  echo "[*] authbypass clone..."
  git clone --depth 1 https://github.com/JaewookYou/whs1-ctf2-authbypass-chall "$TMP/ab"
  [ -d "$AB_B" ] || cp -r "$TMP/ab/auth-bypass-basic"    "$AB_B"
  [ -d "$AB_A" ] || cp -r "$TMP/ab/auth-bypass-advanced" "$AB_A"
else
  echo "[*] authbypass 존재 — clone 생략(플래그/포트 재적용)"
fi
reinject "$AB_B/docker-compose.yml" "$(getf FLAG_AUTHBYPASS_BASIC)"
reinject "$AB_A/docker-compose.yml" "$(getf FLAG_AUTHBYPASS_ADV)"
# advanced 호스트포트 9002→9005 (멱등: 이미 9005면 매치 안 됨)
sed -i.bak 's|"9002:9002"|"9005:9002"|' "$AB_A/docker-compose.yml" && rm -f "$AB_A/docker-compose.yml.bak"
add_restart "$AB_B/docker-compose.yml" arang_bank db     # 재부팅 후 자동 복구
add_restart "$AB_A/docker-compose.yml" arang_bank2 db2
strip_limits "$AB_B/docker-compose.yml"; add_limits "$AB_B/docker-compose.yml" 512m 256 arang_bank
                                         add_limits "$AB_B/docker-compose.yml" 768m 512 db
strip_limits "$AB_A/docker-compose.yml"; add_limits "$AB_A/docker-compose.yml" 512m 256 arang_bank2
                                         add_limits "$AB_A/docker-compose.yml" 768m 512 db2

# ── (3) FSI 채팅(2022_fsi_edu_challs) — 캡스톤 XSS/SQLi (:9090, 자체 compose · 10.111.0.0/24 로 재매핑) ──
FSI="$ROOT/challenges/capstone/fsi-chat"
if [ ! -d "$FSI" ]; then
  echo "[*] FSI(2022_fsi_edu_challs) clone..."
  git clone --depth 1 https://github.com/JaewookYou/2022_fsi_edu_challs "$FSI"
else
  echo "[*] FSI 존재 — clone 생략(플래그/보정 재적용)"
fi
# FSI 플래그는 fsi2022{...} 고정형식(위 reinject 의 flag{} 와 별개) — .env 기준 재주입(멱등)
FSI_SQLI="$(getf FLAG_FSI_SQLI || true)"; FSI_XSS="$(getf FLAG_FSI_XSS || true)"
[ -n "$FSI_SQLI" ] && [ -f "$FSI/docker/mysql/Dockerfile" ] && { sed -i.bak "s|fsi2022{[^}]*}|$FSI_SQLI|" "$FSI/docker/mysql/Dockerfile"; rm -f "$FSI/docker/mysql/Dockerfile.bak"; }
[ -n "$FSI_XSS" ]  && [ -f "$FSI/mysql/init.sql" ]            && { sed -i.bak "s|fsi2022{[^}]*}|$FSI_XSS|"  "$FSI/mysql/init.sql"; rm -f "$FSI/mysql/init.sql.bak"; }
# [보정] compose(업스트림엔 없는 로컬보정): db 컨테이너명 충돌 회피(authbypass-basic 의 mysql-db) + ext/int db-레이스 자동복구(멱등)
FSI_COMPOSE="$FSI/docker-compose.yml"
if [ -f "$FSI_COMPOSE" ]; then
  sed -i.bak 's|container_name: mysql-db|container_name: fsi-mysql-db|' "$FSI_COMPOSE" && rm -f "$FSI_COMPOSE.bak"   # 앱은 고정 IP(10.111.0.5) 접속이라 무영향
  # ext/int db-레이스 자동복구 + 재부팅 후 자동 복구. (이전엔 ext/int 만 on-failure 라 데몬 재시작 시
  #  ext/int 는 살아났는데 db 는 죽은 채 남아 '채팅은 열리는데 로그인/글이 안 되는' 상태가 됐다 → db 포함 3종 모두)
  add_restart "$FSI_COMPOSE" external_server internal_server db
  strip_limits "$FSI_COMPOSE"
  add_limits   "$FSI_COMPOSE" 512m 256 external_server internal_server
  add_limits   "$FSI_COMPOSE" 768m 512 db
fi
# [보정] flag 광역노출 차단(멱등): ext getBoardList 가 `author=<나> or author="admin"` 이라
#   admin 명의로 쓰인 글은 '제목'이 전원 목록에 뜬다. 의도된 풀이가 봇에게 admin 명의로 flag 를
#   적게 하는 것이라, 한 명이 풀면 나머지 전원이 목록에서 flag 를 그냥 읽어버렸다.
#   → 공개는 공지(seed, seq=1)만. 유출은 '봇이 내 아이디 명의로 써주게' 하는 개인 채널로 유도
#     (int/ext /write 모두 author 를 폼에서 받으므로 페이로드가 자기 uid 를 넣으면 본인만 열람).
if [ -f "$FSI/ext/app.py" ]; then
  sed -i.bak "s|or author=\"admin\"'|or (author=\"admin\" and seq=\"1\")'|" "$FSI/ext/app.py" && rm -f "$FSI/ext/app.py.bak"
fi
# 위 접근제어를 UI 에도 명시(멱등) — author=admin 으로 exfil 하면 아무에게도 안 보여 '조용히 실패'하므로,
# 목록 규칙을 보여줘 학습자가 '내 명의로 쓰게 한다'는 설계에 도달하게 한다(체인 자체는 노출 안 함).
BH="$FSI/ext/templates/board.html"
if [ -f "$BH" ] && ! grep -q '내가 작성자' "$BH"; then
  sed -i.bak 's|<h2 class="heading-section">FSI BOARD</h2>|<h2 class="heading-section">FSI BOARD</h2>\n\t\t\t\t\t<p style="color:#888;font-size:14px;">※ 목록에는 <b>내가 작성자(author)로 지정된 글</b>과 공지만 표시됩니다.</p>|' "$BH" && rm -f "$BH.bak"
fi
# [보정] 내부보드 int/app.py 는 db 기동 레이스로 죽으면 재기동 안 됨(entrypoint 가 '&' 백그라운드) → XSS 챌린지용 재시작 루프(멱등)
if [ -f "$FSI/int/entrypoint.sh" ] && ! grep -q 'while true; do python3 /app/app.py' "$FSI/int/entrypoint.sh"; then
  sed -i.bak 's#^python3 /app/app.py&#while true; do python3 /app/app.py; sleep 2; done \&#' "$FSI/int/entrypoint.sh"; rm -f "$FSI/int/entrypoint.sh.bak"
fi
# [보정] 고정 서브넷 172.22.0.0/24 → 10.111.0.0/24 재매핑(멱등). 업스트림은 172.22 고정이나 이 대역은
#   docker 기본 풀(172.16/12) 안이라 다른 프로젝트 bridge·무관 프로젝트(*/16 점유)와 'Pool overlaps' 충돌.
#   풀 밖 10.111.0.0/24 로 옮기면 auto-allocation 충돌이 원천 차단. 앱·iptables·봇 하드코딩 IP 도 함께 이동.
for f in "$FSI/docker-compose.yml" "$FSI/int/app.py" "$FSI/int/entrypoint.sh" "$FSI/int/bot/bot.py" "$FSI/ext/app.py"; do
  [ -f "$f" ] && sed -i 's/172\.22\.0/10.111.0/g' "$f"
done
# ubuntu/debian/mysql 3개 서비스 — host 네트워크 빌드 override(DNS 보정)
write_hostnet_override "$FSI" external_server internal_server db

# ── (4) CRLF→LF 정규화(컨테이너용 파일) ──
find "$ST" "$AB_B" "$AB_A" \
     \( -name '*.sh' -o -name 'Dockerfile' -o -name 'id_rsa' -o -name 'id_rsa.pub' -o -name 'entrypoint.sh' \) \
     -not -path '*/.git/*' -exec sed -i 's/\r$//' {} +
{ [ -d "$FSI" ] && find "$FSI" \( -name '*.sh' -o -name 'Dockerfile' -o -name 'entrypoint.sh' -o -name 'init.sql' \) -not -path '*/.git/*' -exec sed -i 's/\r$//' {} + ; } || true

cat <<'EOF'

[+] 완료(배치/플래그 주입). 외부 챌린지는 각자 자체 compose 로 기동.
    secret-tunnel·fsi-chat 은 빌드 DNS 보정용 docker-compose.hostnet.yml 을 함께 넘긴다(host 네트워크 빌드):
    cd challenges/capstone/secret-tunnel  && docker compose -f docker-compose.yml -f docker-compose.hostnet.yml up -d --build   # 웹 :8090, SSH :2222
    cd challenges/auth/authbypass-basic   && docker compose up -d --build   # :9001-9003
    cd challenges/auth/authbypass-advanced && docker compose up -d --build  # :9005
    cd challenges/capstone/fsi-chat       && docker compose -f docker-compose.yml -f docker-compose.hostnet.yml up -d --build   # FSI 채팅 :9090 (10.111.0.0/24 · start --with-fsi 권장)
  (start.sh/start.ps1 은 hostnet override 가 있으면 자동으로 -f 포함하고, 매 기동 시 이 스크립트로 .env 플래그를 재주입한다)
EOF
