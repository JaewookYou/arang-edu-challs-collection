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

# ── (3) CRLF→LF 정규화(컨테이너용 파일) ──
find "$ST" "$AB_B" "$AB_A" \
     \( -name '*.sh' -o -name 'Dockerfile' -o -name 'id_rsa' -o -name 'id_rsa.pub' -o -name 'entrypoint.sh' \) \
     -not -path '*/.git/*' -exec sed -i 's/\r$//' {} +

cat <<'EOF'

[+] 완료(배치/플래그 주입). 외부 챌린지는 각자 자체 compose 로 기동:
    cd challenges/capstone/secret-tunnel  && docker compose up -d --build   # 웹 :8090, SSH :2222
    cd challenges/auth/authbypass-basic   && docker compose up -d --build   # :9001-9003
    cd challenges/auth/authbypass-advanced && docker compose up -d --build  # :9005
  (start.ps1 은 이 스크립트를 매 기동 시 호출해 현재 .env 플래그를 재주입한다)
EOF
