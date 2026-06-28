# Windows PowerShell 용 make 대체. (Makefile 의 타깃과 동일)
# 사용 예:  .\make.ps1 flags    .\make.ps1 up    .\make.ps1 up-client    .\make.ps1 down
param([Parameter(Position=0)][string]$target = "help")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$profiles = @{
  "up"="all"; "up-day1"="day1"; "up-day2"="day2"; "up-client"="client";
  "up-injection"="injection"; "up-auth"="auth"; "up-logic"="logic";
  "up-server"="server"; "up-jsp"="jsp"; "up-capstone"="capstone"
}

switch ($target) {
  "flags" { .\gen_flags.ps1 }
  "down"  { docker compose --profile all down }
  "ps"    { docker compose ps }
  "logs"  { docker compose logs -f }
  default {
    if ($profiles.ContainsKey($target)) {
      docker compose --profile $profiles[$target] up -d --build
    } else {
      Write-Host "사용법: .\make.ps1 [flags|up|down|ps|logs|up-day1|up-day2|up-client|up-injection|up-auth|up-logic|up-server|up-jsp|up-capstone]"
    }
  }
}
