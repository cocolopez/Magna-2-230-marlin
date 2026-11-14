@echo off
rem Instala el perfil "Hellbot Magna 2 230 Marlin 2.1" en la version MAS NUEVA de Cura instalada.
rem Cerra Cura antes de correrlo. Abri Cura al menos una vez despues de instalarlo/actualizarlo.
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$base = Join-Path $env:APPDATA 'cura';" ^
  "if (-not (Test-Path $base)) { Write-Host 'No encontre la carpeta de Cura. Abri Cura una vez y volve a correr esto.'; exit 1 };" ^
  "$v = Get-ChildItem $base -Directory | Where-Object { $_.Name -match '^\d+\.\d+$' } | Sort-Object { [version]$_.Name } | Select-Object -Last 1;" ^
  "if (-not $v) { Write-Host 'No encontre ninguna version de Cura en' $base; exit 1 };" ^
  "$d = $v.FullName; Write-Host 'Instalando en' $d;" ^
  "New-Item -ItemType Directory -Force (Join-Path $d 'definitions'),(Join-Path $d 'extruders'),(Join-Path $d 'quality') | Out-Null;" ^
  "Copy-Item 'definitions\*.def.json' (Join-Path $d 'definitions') -Force;" ^
  "Copy-Item 'extruders\*.def.json' (Join-Path $d 'extruders') -Force;" ^
  "Copy-Item 'quality\hellbot_magna2_230_marlin' (Join-Path $d 'quality') -Recurse -Force;" ^
  "Write-Host 'Listo. Abri Cura > Agregar impresora > No conectada en red > Hellbot > Hellbot Magna 2 230 Marlin 2.1'"
pause
