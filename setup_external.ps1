# 외부 GitHub 챌린지(secret-tunnel · authbypass)를 배치 + .env 플래그 주입 (Windows PowerShell)
# 재실행 안전(idempotent): 이미 받은 폴더는 clone 생략하고, 플래그/키/포트/보정만 '현재 .env' 기준으로 다시 적용.
#   → gen_flags 로 .env 를 재생성한 뒤 다시 돌리면 외부 챌린지 플래그가 스코어보드와 다시 일치한다.
# git 필요. 먼저 .\gen_flags.ps1 로 .env 생성.
$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
if (-not (Test-Path "$ROOT\.env")) { Write-Error "먼저 .\gen_flags.ps1 로 .env 를 생성하세요."; exit 1 }

function Get-Flag($name) {
  $line = Get-Content "$ROOT\.env" | Where-Object { $_ -match "^$name=" } | Select-Object -First 1
  return ($line -split '=', 2)[1]
}
function Save-Lf($path, $text) {
  [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))
}
function Reinject($path, $newflag) {
  # 현재 파일의 flag{...} 를 새 값으로(멱등). 플래그 형식엔 정규식 치환 특수문자($ 등)가 없어 안전.
  $c = [System.IO.File]::ReadAllText($path)
  $c = [regex]::Replace($c, 'flag\{[^}]*\}', $newflag)
  Save-Lf $path $c
}
function Normalize-Eol($path) { Save-Lf $path ([System.IO.File]::ReadAllText($path) -replace "`r`n", "`n") }

# ── (1) secret-tunnel ──
$st = "$ROOT\challenges\capstone\secret-tunnel"
if (-not (Test-Path $st)) {
  Write-Host "[*] secret-tunnel clone..."
  git clone --depth 1 https://github.com/JaewookYou/whs2-ctf-chall-secret-tunnel $st
} else { Write-Host "[*] secret-tunnel 존재 — clone 생략(플래그/보정 재적용)" }
Reinject "$st\docker\flagserver\Dockerfile" (Get-Flag FLAG_SECRET_TUNNEL)
# ssh 키: 없거나 '[REDACTED]' 플레이스홀더면 실제 RSA 키쌍 생성(피벗 동작 필수)
$keys = "$st\src\ssh_keys"
$needKey = (-not (Test-Path "$keys\id_rsa")) -or (-not (Select-String -Path "$keys\id_rsa" -Pattern "PRIVATE KEY" -Quiet -ErrorAction SilentlyContinue))
if ($needKey) {
  Write-Host "[*] secret-tunnel ssh 키 생성(플레이스홀더 교체)"
  Remove-Item -Force "$keys\id_rsa","$keys\id_rsa.pub" -ErrorAction SilentlyContinue
  ssh-keygen -t rsa -b 2048 -N '""' -C "appuser@extserver" -f "$keys\id_rsa" -q | Out-Null
}
# extserver Dockerfile 업스트림 오타: 'echo ... flag.txt' 줄에 RUN 누락(멱등: ^echo 만 매치)
$exd = [System.IO.File]::ReadAllText("$st\docker\extserver\Dockerfile") -replace "(?m)^echo `"flag\{dummy_flag_1\}`"", "RUN echo `"flag{dummy_flag_1}`""
Save-Lf "$st\docker\extserver\Dockerfile" $exd

# ── (2) authbypass basic/advanced ──
$tmp = Join-Path $env:TEMP ("ab_" + [guid]::NewGuid().ToString('N'))
$abB = "$ROOT\challenges\auth\authbypass-basic"
$abA = "$ROOT\challenges\auth\authbypass-advanced"
if ((-not (Test-Path $abB)) -or (-not (Test-Path $abA))) {
  Write-Host "[*] authbypass clone..."
  git clone --depth 1 https://github.com/JaewookYou/whs1-ctf2-authbypass-chall $tmp
  if (-not (Test-Path $abB)) { Copy-Item -Recurse "$tmp\auth-bypass-basic"    $abB }
  if (-not (Test-Path $abA)) { Copy-Item -Recurse "$tmp\auth-bypass-advanced" $abA }
  Remove-Item -Recurse -Force $tmp
} else { Write-Host "[*] authbypass 존재 — clone 생략(플래그/포트 재적용)" }
Reinject "$abB\docker-compose.yml" (Get-Flag FLAG_AUTHBYPASS_BASIC)
Reinject "$abA\docker-compose.yml" (Get-Flag FLAG_AUTHBYPASS_ADV)
# advanced 호스트포트 9002→9005 (멱등)
$ca = [System.IO.File]::ReadAllText("$abA\docker-compose.yml").Replace('"9002:9002"', '"9005:9002"')
Save-Lf "$abA\docker-compose.yml" $ca

# ── (3) CRLF→LF 정규화 ──
foreach ($d in @($st, $abB, $abA)) {
  Get-ChildItem -Path $d -Recurse -File |
    Where-Object { $_.FullName -notmatch '\\\.git\\' -and
                   ($_.Name -match '\.sh$' -or $_.Name -eq 'Dockerfile' -or $_.Name -like 'id_rsa*') } |
    ForEach-Object { Normalize-Eol $_.FullName }
}

Write-Host ""
Write-Host "[+] 완료(배치/플래그 주입). 외부 챌린지는 각자 자체 compose 로 기동:"
Write-Host "    cd challenges\capstone\secret-tunnel  ; docker compose up -d --build   # 웹 :8090, SSH :2222"
Write-Host "    cd challenges\auth\authbypass-basic   ; docker compose up -d --build   # :9001-9003"
Write-Host "    cd challenges\auth\authbypass-advanced ; docker compose up -d --build  # :9005"
