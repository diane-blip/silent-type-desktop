param([string]$Python = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe", [switch]$CpuOnly)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath $Python)) { throw 'Python 3.12 is required. Supply its path with -Python.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $Python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the app environment.' }
}
$AppPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
# Every package, PyTorch included, must match a SHA-256 in the lock file.
$Lock = if ($CpuOnly) { 'requirements-cpu.lock' } else { 'requirements-cuda.lock' }
$TorchIndex = if ($CpuOnly) { 'https://download.pytorch.org/whl/cpu' } else { 'https://download.pytorch.org/whl/cu130' }
& $AppPython -m pip install --require-hashes --extra-index-url $TorchIndex -r $Lock
if ($LASTEXITCODE -ne 0) { throw 'App dependencies did not install.' }
& $AppPython download_model.py
if ($LASTEXITCODE -ne 0) { throw 'Model installation failed.' }
& $AppPython doctor.py
if ($LASTEXITCODE -ne 0) { throw 'Read the diagnostic result before starting the app.' }
& $AppPython -m silent_type.icon  # drawn from this computer's emoji font, not shipped
if ($LASTEXITCODE -ne 0) { throw 'Could not draw the app icon.' }
$Shell = New-Object -ComObject WScript.Shell
$ShortcutFolder = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$Shortcut = $Shell.CreateShortcut((Join-Path $ShortcutFolder 'Silent Type.lnk'))
$Shortcut.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
$Shortcut.Arguments = '"' + (Join-Path $PSScriptRoot 'start-silent-type.vbs') + '"'
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = 'Silent typing from your webcam'
$Shortcut.IconLocation = (Join-Path $PSScriptRoot 'silent_type\silent-type.ico') + ',0'
$Shortcut.Save()
Write-Output 'Silent Type is installed. Open it from the Start menu. Startup remains off.'
