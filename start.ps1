#Requires -Version 5.1
<#
  실습 환경 한 번에 구성 (Windows PowerShell)
  ─────────────────────────────────────────────────────────────
  Docker 확인 → 플래그(.env) 생성 → 빌드·기동 → db healthy 대기
  → 상태 출력 → 스코어보드(http://localhost:9000) 자동 열기

  사용 예:
    .\start.ps1                  # 메인(all) + 외부 챌린지(authbypass·secret-tunnel) 자동 기동 + 스코어보드 열기
    .\start.ps1 -Profile client  # 특정 카테고리만 (client/injection/auth/logic/server/jsp/capstone/day1/day2)
    .\start.ps1 -KeepEnv         # 기존 .env(플래그) 유지(재생성 안 함)
    .\start.ps1 -NoBrowser       # 브라우저 자동 열기 끄기
    .\start.ps1 -NoExternal      # 외부 GitHub 챌린지 제외(메인 스택만 기동)
    .\start.ps1 -WithFsi         # FSI(2022_fsi_edu_challs, :9090)도 함께 기동(상위 폴더 레포)
    .\start.ps1 -Down            # 전체 정리(메인 + 외부 + FSI 컨테이너·네트워크 제거)

  ※ 외부 챌린지(authbypass-basic/advanced·secret-tunnel)는 기본으로 함께 기동되며, 매 기동 시
     setup_external.ps1 을 호출해 '현재 .env' 플래그를 재주입한다(폴더 없으면 clone 까지).
     → gen_flags 로 .env 를 새로 만들어도 외부 챌린지 flag 가 스코어보드와 항상 일치.
     FSI 는 별도 레포 + 172.22.0.0/24 고정이라 -WithFsi 일 때만(메인보다 먼저) 기동.
     FSI flag 2종은 registry.yaml + .env(FLAG_FSI_XSS/SQLI)로 스코어보드에 등록됨.
#>
param(
  [ValidateSet('all','day1','day2','client','injection','auth','logic','server','jsp','capstone')]
  [string]$Profile = 'all',
  [switch]$Down,
  [switch]$KeepEnv,
  [switch]$NoBrowser,
  [switch]$External,    # (호환용) 외부 챌린지는 이제 기본 기동 — 이 스위치는 무시됨
  [switch]$NoExternal,  # 외부 챌린지(authbypass·secret-tunnel) 기동 제외
  [switch]$WithFsi      # FSI(2022_fsi_edu_challs) 도 함께 기동(상위 폴더 별도 레포)
)
$FsiDir = Join-Path $PSScriptRoot 'challenges\capstone\fsi-chat'   # setup_external 이 여기로 clone (레포 내부)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
# 콘솔 한글 출력 인코딩(UTF-8) — PS 5.1 및 출력 리다이렉션에서 깨짐 방지
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# 외부 GitHub 챌린지(각자 own docker-compose) — 먼저 .\setup_external.ps1 로 clone+플래그주입 필요
$ExtDirs = @(
  'challenges/auth/authbypass-basic',
  'challenges/auth/authbypass-advanced',
  'challenges/capstone/secret-tunnel'
)

function Info($m) { Write-Host "[*] $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[+] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[!] $m" -ForegroundColor Yellow }

# ── 정리 모드 ──
if ($Down) {
  Info "전체 정리 (docker compose --profile all down)..."
  docker compose --profile all down
  foreach ($d in $ExtDirs) {
    if (Test-Path (Join-Path $d 'docker-compose.yml')) {
      Info "외부 챌린지 정리: $d"
      Push-Location $d; docker compose down; Pop-Location
    }
  }
  if (Test-Path (Join-Path $FsiDir 'docker-compose.yml')) {
    Info "FSI 정리: $FsiDir"
    Push-Location $FsiDir; docker compose down; Pop-Location
  }
  Ok "정리 완료."
  return
}

# ── 0) Docker 확인 ──
Info "Docker 상태 확인..."
docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  Warn "Docker 에 연결할 수 없습니다. Docker Desktop(WSL2 백엔드)을 먼저 실행한 뒤 다시 시도하세요."
  exit 1
}
Ok "Docker 정상."

# ── 1) 플래그(.env) 생성 ──
if ($KeepEnv -and (Test-Path .\.env)) {
  Info ".env 유지(-KeepEnv) — 플래그 재생성 생략."
} else {
  Info "플래그 생성 (.env)..."
  & .\gen_flags.ps1
}

# ── 1.5) FSI (옵션) — 172.22.0.0/24 고정 대역을 선점하도록 메인보다 먼저 기동 ──
if ($WithFsi) {
  if (-not (Test-Path (Join-Path $FsiDir 'docker-compose.yml'))) {
    Info "FSI 폴더 없음 → setup_external.ps1 로 clone+보정(레포 내부 challenges\capstone\fsi-chat)..."
    try { & .\setup_external.ps1 } catch { Warn "setup_external 실패: $($_.Exception.Message)" }
  }
  if (Test-Path (Join-Path $FsiDir 'docker-compose.yml')) {
    # secret-tunnel 의 자동 bridge(/16)가 172.22 를 선점하면 FSI 가 못 뜬다.
    # 잠시 내려 172.22 를 비운 뒤 FSI 가 선점하게 하고, secret-tunnel 은 아래 외부 루프에서 다른 대역으로 재기동.
    $stDir = 'challenges/capstone/secret-tunnel'
    if (Test-Path (Join-Path $stDir 'docker-compose.yml')) {
      Push-Location $stDir; docker compose down 2>$null | Out-Null; Pop-Location
    }
    Info "FSI 기동(메인보다 먼저, 172.22 대역 선점): $FsiDir"
    Push-Location $FsiDir
    try { docker compose up -d --build } finally { Pop-Location }
    Ok "FSI 채팅: http://localhost:9090  (스코어보드 fsi-chat-xss / fsi-chat-sqli)"
  } else {
    Warn "FSI 폴더 없음: $FsiDir  → -WithFsi 건너뜀"
  }
}

# ── 2) 빌드·기동 ──
Info "빌드·기동 (profile=$Profile) — 최초 빌드는 수 분 소요될 수 있습니다..."
docker compose --profile $Profile up -d --build
if ($LASTEXITCODE -ne 0) {
  Warn "기동 실패 — 위 로그를 확인하세요. (이미지 빌드/네트워크 문제일 수 있음)"
  exit 1
}

# ── 3) db(MariaDB) 준비 대기 — db 가 기동된 프로필일 때만 ──
$running = @((docker ps --format '{{.Names}}') 2>$null)
if ($running -contains 'db') {
  Info "db(MariaDB) 준비 대기 — healthy 까지 (sqli/jsp 문제 정상화)..."
  $deadline = (Get-Date).AddSeconds(150)
  do {
    Start-Sleep -Seconds 3
    $h = (docker inspect -f '{{.State.Health.Status}}' db 2>$null)
    Write-Host "    db: $h"
  } while ($h -ne 'healthy' -and (Get-Date) -lt $deadline)
  if ($h -eq 'healthy') { Ok "db healthy — sqli/jsp 문제 정상." }
  else { Warn "db 가 아직 준비되지 않았습니다($h). 잠시 후 'docker compose ps' 로 재확인하세요." }
}

# ── 4) 상태 출력 ──
Info "컨테이너 상태:"
docker compose --profile $Profile ps

# ── 5) 스코어보드 ──
$board = "http://localhost:9000"
Ok "스코어보드: $board  (회원가입 → 로그인 → flag 제출)"
if (-not $NoBrowser) { Start-Process $board }

# ── 6) 외부 GitHub 챌린지 (기본 기동, -NoExternal 로 제외) ──
if (-not $NoExternal) {
  # 매번 setup_external 호출(멱등): 폴더 없으면 clone, 있으면 '현재 .env' 플래그를 재주입.
  # → gen_flags 로 .env 를 새로 만들어도 외부 챌린지 flag 가 스코어보드와 다시 일치.
  Info "외부 챌린지 배치/플래그 재주입 (setup_external.ps1)..."
  try { & .\setup_external.ps1 }
  catch { Warn "setup_external 실패: $($_.Exception.Message)  (네트워크/git 확인)" }
  foreach ($d in $ExtDirs) {
    if (Test-Path (Join-Path $d 'docker-compose.yml')) {
      Info "외부 챌린지 기동: $d"
      Push-Location $d
      try { docker compose up -d --build } finally { Pop-Location }
    } else {
      Warn "외부 챌린지 폴더 없음: $d  → .\setup_external.ps1 수동 실행 필요"
    }
  }
  Ok "외부 챌린지: authbypass-basic :9001 · authbypass-advanced :9005 · secret-tunnel :8090(SSH 2222)"
} else {
  Info "외부 챌린지 제외(-NoExternal)."
}

Write-Host ""
Ok "준비 완료! 정리하려면:  .\start.ps1 -Down"
