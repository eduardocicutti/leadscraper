!macro NSIS_HOOK_PREINSTALL
  IfFileExists "$INSTDIR\scraper-sidecar.exe" 0 fim_sidecar
  Push $0
  System::Call 'kernel32::SetEnvironmentVariableW(w "LEAD_SCRAPER_INSTALL_DIR", w "$INSTDIR") i .r0'
  nsExec::ExecToLog /TIMEOUT=15000 `"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -Command "try { $$alvo = Join-Path $$env:LEAD_SCRAPER_INSTALL_DIR 'scraper-sidecar.exe'; Get-CimInstance Win32_Process -Filter 'Name = ''scraper-sidecar.exe''' -ErrorAction Stop | Where-Object ExecutablePath -EQ $$alvo | ForEach-Object { Stop-Process -Id $$_.ProcessId -ErrorAction Stop } } catch { Write-Error $$_; exit 1 }"`
  Pop $0
  ${If} $0 != 0
    DetailPrint "Feche o Lead Scraper e tente novamente: o agente anterior ainda está em execução."
    Pop $0
    Abort
  ${EndIf}
  Pop $0
fim_sidecar:
!macroend
