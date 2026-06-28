#!/usr/bin/env bash
# 랜덤 플래그/시크릿을 .env 로 생성한다. (강사 배포 시마다 새로 생성 권장)
set -euo pipefail
ENVF="$(dirname "$0")/.env"

rnd() { openssl rand -hex 16 2>/dev/null || head -c16 /dev/urandom | od -An -tx1 | tr -d ' \n'; }
flag() { echo "flag{$(openssl rand -hex 10 2>/dev/null || head -c10 /dev/urandom | od -An -tx1 | tr -d ' \n')}"; }

FLAG_VARS=(
  FLAG_XSS_1 FLAG_XSS_2 FLAG_XSS_3 FLAG_CSRF_1 FLAG_CSRF_2 FLAG_XSLEAK FLAG_DOMCLOB FLAG_OPENRED
  FLAG_SQLI_1 FLAG_SQLI_2 FLAG_SQLI_3 FLAG_LFI_1 FLAG_LFI_2 FLAG_CMDI_1 FLAG_SSTI_1 FLAG_XXE_1
  FLAG_IDOR FLAG_2FA FLAG_RACE FLAG_UPLOAD FLAG_SSRF FLAG_PROTO
  FLAG_JSP_SQLI FLAG_JSP_UPLOAD FLAG_JSP_PATH FLAG_JSP_CHAIN
  FLAG_SECRET_TUNNEL FLAG_AUTHBYPASS_BASIC FLAG_AUTHBYPASS_ADV
)

{
  echo "# 자동 생성 $(date '+%Y-%m-%d %H:%M:%S') — 커밋 금지(.gitignore)"
  echo "ADMIN_PASSWORD=$(rnd)"
  echo "PLATFORM_SECRET=$(rnd)"
  for v in "${FLAG_VARS[@]}"; do echo "$v=$(flag)"; done
  # FSI 채팅(2022_fsi_edu_challs) — repo 하드코딩 플래그(고정값, 랜덤 아님). 스코어보드 채점용.
  echo "FLAG_FSI_XSS=fsi2022{n0w_you_4re_g00d_at_xss_m4ybe?}"
  echo "FLAG_FSI_SQLI=fsi2022{yes_y0u_c4n_le4k_fi1e_by_sq1i!}"
} > "$ENVF"

echo "[+] wrote $ENVF  (플래그 ${#FLAG_VARS[@]}개 + ADMIN_PASSWORD)"
