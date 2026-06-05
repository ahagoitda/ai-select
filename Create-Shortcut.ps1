# Run this on the target machine (your desktop) to (re)create a nice desktop shortcut
$project = $PSScriptRoot
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "MyAISelect.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($shortcutPath)

# Use the venv python if present, otherwise system python
$pythonCmd = "python"
if (Test-Path "$project\.venv\Scripts\python.exe") {
    $pythonCmd = "`"$project\.venv\Scripts\python.exe`""
}

$Shortcut.TargetPath = "cmd.exe"
$Shortcut.Arguments = "/c `"cd /d `"$project`" && $pythonCmd ai_select.py`""
$Shortcut.WorkingDirectory = $project
$Shortcut.IconLocation = "shell32.dll, 23"
$Shortcut.Description = "MyAISelect - Custom fast AI screen selector"
$Shortcut.Save()

Write-Host "Shortcut created/updated at: $shortcutPath"
Write-Host "Tip: Right-click shortcut → Properties → Shortcut key to assign e.g. Ctrl+Alt+A"