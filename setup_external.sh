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
  if ! grep -q 'restart: on-failure' "$FSI_COMPOSE"; then
    sed -i.bak -e 's|^  external_server:|  external_server:\n    restart: on-failure|' -e 's|^  internal_server:|  internal_server:\n    restart: on-failure|' "$FSI_COMPOSE" && rm -f "$FSI_COMPOSE.bak"
  fi
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
