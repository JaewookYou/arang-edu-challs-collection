# 랜덤 플래그/시크릿을 .env 로 생성 (Windows PowerShell 용 — gen_flags.sh 와 동일 역할)
# 사용: PowerShell 에서  .\gen_flags.ps1
$ErrorActionPreference = "Stop"
$envf = Join-Path $PSScriptRoot ".env"

function Rnd  { -join ((1..16) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) }) }
function Flag { "flag{" + (-join ((1..10) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })) + "}" }

$flagVars = @(
  'FLAG_XSS_1','FLAG_XSS_2','FLAG_XSS_3','FLAG_CSRF_1','FLAG_CSRF_2','FLAG_XSLEAK','FLAG_DOMCLOB','FLAG_OPENRED',
  'FLAG_SQLI_1','FLAG_SQLI_2','FLAG_SQLI_3','FLAG_LFI_1','FLAG_LFI_2','FLAG_CMDI_1','FLAG_SSTI_1','FLAG_XXE_1',
  'FLAG_IDOR','FLAG_2FA','FLAG_RACE','FLAG_UPLOAD','FLAG_SSRF','FLAG_PROTO',
  'FLAG_JSP_SQLI','FLAG_JSP_UPLOAD','FLAG_JSP_PATH','FLAG_JSP_CHAIN',
  'FLAG_SECRET_TUNNEL','FLAG_AUTHBYPASS_BASIC','FLAG_AUTHBYPASS_ADV'
)

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# 자동 생성 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') — 커밋 금지(.gitignore)")
$lines.Add("ADMIN_PASSWORD=$(Rnd)")
$lines.Add("PLATFORM_SECRET=$(Rnd)")
foreach ($v in $flagVars) { $lines.Add("$v=$(Flag)") }
# FSI 채팅(2022_fsi_edu_challs) — repo 하드코딩 플래그(고정값, 랜덤 아님). 스코어보드 채점용.
$lines.Add('FLAG_FSI_XSS=fsi2022{n0w_you_4re_g00d_at_xss_m4ybe?}')
$lines.Add('FLAG_FSI_SQLI=fsi2022{yes_y0u_c4n_le4k_fi1e_by_sq1i!}')

# docker compose 호환을 위해 반드시 LF + UTF-8(BOM 없음) 으로 기록
$text = ($lines -join "`n") + "`n"
[System.IO.File]::WriteAllText($envf, $text, (New-Object System.Text.UTF8Encoding $false))

Write-Host "[+] wrote $envf  (플래그 $($flagVars.Count)개 + ADMIN_PASSWORD)"
