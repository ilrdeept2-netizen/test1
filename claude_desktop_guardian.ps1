#Requires -Version 5.1
<#
.SYNOPSIS
    Claude Desktop Guardian - Persistent crash prevention and auto-recovery system

.DESCRIPTION
    Permanently fixes Claude Desktop app crashes by providing always-on monitoring
    and automatic recovery. Not a one-time fix - this system persists across updates.

    Features:
      1) Auto-apply stability settings at system startup (survives updates)
      2) Monitor Claude Desktop process and auto-restart on crash
      3) Detect and recover settings reset by app updates
      4) Permanent GPU acceleration management
      5) Auto-detect and clean corrupted cache
      6) Adaptive crash recovery based on crash history
      7) Register as Windows Scheduled Task for persistence

    Usage:
      .\claude_desktop_guardian.ps1 -Install     # Install Guardian (recommended)
      .\claude_desktop_guardian.ps1 -Watch        # Start manual monitoring
      .\claude_desktop_guardian.ps1 -Protect      # Apply stability settings once
      .\claude_desktop_guardian.ps1 -Uninstall    # Remove Guardian

.PARAMETER Install
    Register Guardian as Windows Scheduled Task for auto-run at login.

.PARAMETER Watch
    Monitor Claude Desktop process and auto-recover on crash.

.PARAMETER Protect
    Check and restore stability settings (one-time, no monitoring).

.PARAMETER Uninstall
    Remove Guardian scheduled tasks and related settings.

.PARAMETER Silent
    Run silently in background (for scheduled task use).
#>

param(
    [switch]$Install,
    [switch]$Watch,
    [switch]$Protect,
    [switch]$Uninstall,
    [switch]$Silent
)

$ErrorActionPreference = "Continue"

# -- Constants --
$GUARDIAN_VERSION = "2.0.0"
$GUARDIAN_NAME = "ClaudeDesktopGuardian"
$GUARDIAN_LOG_DIR = "$env:APPDATA\Claude\guardian_logs"
$GUARDIAN_CONFIG = "$env:APPDATA\Claude\guardian_config.json"
$CLAUDE_CONFIG_DIR = "$env:APPDATA\Claude"
$ELECTRON_FLAGS_FILE = "$CLAUDE_CONFIG_DIR\electron-flags.conf"
$CLAUDE_DESKTOP_CONFIG = "$CLAUDE_CONFIG_DIR\claude_desktop_config.json"
$CRASH_HISTORY_FILE = "$CLAUDE_CONFIG_DIR\guardian_crash_history.json"

$CLAUDE_EXE_PATHS = @(
    "$env:LOCALAPPDATA\Programs\Claude\Claude.exe",
    "$env:PROGRAMFILES\Claude\Claude.exe",
    "$env:PROGRAMFILES(x86)\Claude\Claude.exe"
)

$CACHE_DIRS = @(
    "$env:APPDATA\Claude\Cache",
    "$env:APPDATA\Claude\GPUCache",
    "$env:APPDATA\Claude\Code Cache",
    "$env:APPDATA\Claude\DawnCache",
    "$env:APPDATA\Claude\DawnGraphiteCache",
    "$env:APPDATA\Claude\blob_storage",
    "$env:APPDATA\Claude\Service Worker",
    "$env:LOCALAPPDATA\Claude\Cache"
)

$GPU_STABLE_FLAGS = @(
    "--disable-gpu",
    "--disable-gpu-compositing",
    "--disable-gpu-sandbox",
    "--disable-software-rasterizer",
    "--in-process-gpu"
)

# -- UTF-8 without BOM writer (PowerShell 5.1 Set-Content adds BOM which breaks JSON parsers) --
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $parentDir = Split-Path $Path -Parent
    if ($parentDir -and -not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, $Utf8NoBom)
}

# -- Utility Functions --
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")

    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logLine = "[$timestamp] [$Level] $Message"

    if (-not (Test-Path $GUARDIAN_LOG_DIR)) {
        New-Item -ItemType Directory -Path $GUARDIAN_LOG_DIR -Force | Out-Null
    }

    $logFile = Join-Path $GUARDIAN_LOG_DIR "guardian_$(Get-Date -Format 'yyyyMMdd').log"
    Add-Content -Path $logFile -Value $logLine -ErrorAction SilentlyContinue

    if (-not $Silent) {
        $color = switch ($Level) {
            "INFO"  { "Gray" }
            "OK"    { "Green" }
            "WARN"  { "Yellow" }
            "ERROR" { "Red" }
            "FIX"   { "Magenta" }
            default { "White" }
        }
        Write-Host "  [$Level] $Message" -ForegroundColor $color
    }
}

function Write-Banner {
    if ($Silent) { return }
    Write-Host ""
    Write-Host "  ========================================================" -ForegroundColor Cyan
    Write-Host "   Claude Desktop Guardian v$GUARDIAN_VERSION" -ForegroundColor White
    Write-Host "   Persistent Crash Prevention & Auto-Recovery System" -ForegroundColor Gray
    Write-Host "  ========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Find-ClaudeExe {
    foreach ($p in $CLAUDE_EXE_PATHS) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Get-GuardianConfig {
    if (Test-Path $GUARDIAN_CONFIG) {
        try {
            return Get-Content -Path $GUARDIAN_CONFIG -Raw | ConvertFrom-Json
        } catch {
            return $null
        }
    }
    return $null
}

function Save-GuardianConfig {
    param($Config)
    if (-not (Test-Path $CLAUDE_CONFIG_DIR)) {
        New-Item -ItemType Directory -Path $CLAUDE_CONFIG_DIR -Force | Out-Null
    }
    Write-Utf8NoBom -Path $GUARDIAN_CONFIG -Content ($Config | ConvertTo-Json -Depth 10)
}

function Get-CrashHistory {
    if (Test-Path $CRASH_HISTORY_FILE) {
        try {
            return Get-Content -Path $CRASH_HISTORY_FILE -Raw | ConvertFrom-Json
        } catch {
            return @{ crashes = @(); totalCrashes = 0; lastReset = (Get-Date).ToString("o") }
        }
    }
    return @{ crashes = @(); totalCrashes = 0; lastReset = (Get-Date).ToString("o") }
}

function Save-CrashHistory {
    param($History)
    Write-Utf8NoBom -Path $CRASH_HISTORY_FILE -Content ($History | ConvertTo-Json -Depth 10)
}

# ==============================================================
# Core Feature 1: Stability Settings Protection (survives updates)
# ==============================================================
function Protect-StabilitySettings {
    Write-Log "Checking stability settings..." "INFO"

    $fixCount = 0

    # 1. Ensure config directory exists
    if (-not (Test-Path $CLAUDE_CONFIG_DIR)) {
        New-Item -ItemType Directory -Path $CLAUDE_CONFIG_DIR -Force | Out-Null
        Write-Log "Created Claude config directory" "FIX"
    }

    # 2. Check/restore Electron GPU flags
    $needGpuFlags = $false
    $config = Get-GuardianConfig

    if ($config -and $config.forceDisableGpu) {
        $needGpuFlags = $true
    }

    # Auto-decide based on crash history
    $history = Get-CrashHistory
    if ($history.totalCrashes -ge 2) {
        $needGpuFlags = $true
        Write-Log "Crash history: $($history.totalCrashes) crashes - forcing GPU disable" "WARN"
    }

    if ($needGpuFlags) {
        $currentFlags = ""
        if (Test-Path $ELECTRON_FLAGS_FILE) {
            $currentFlags = Get-Content -Path $ELECTRON_FLAGS_FILE -Raw -ErrorAction SilentlyContinue
        }

        $expectedFlags = $GPU_STABLE_FLAGS -join "`n"

        if ($currentFlags.Trim() -ne $expectedFlags.Trim()) {
            Write-Utf8NoBom -Path $ELECTRON_FLAGS_FILE -Content $expectedFlags
            Write-Log "Restored GPU stability flags (may have been reset by update)" "FIX"
            $fixCount++
        } else {
            Write-Log "GPU stability flags OK" "OK"
        }
    }

    # 3. Check config file (JSON) integrity
    if (Test-Path $CLAUDE_DESKTOP_CONFIG) {
        try {
            $desktopConfig = Get-Content -Path $CLAUDE_DESKTOP_CONFIG -Raw | ConvertFrom-Json
            Write-Log "Config file OK (parseable)" "OK"
        } catch {
            $backupName = "${CLAUDE_DESKTOP_CONFIG}.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Copy-Item -Path $CLAUDE_DESKTOP_CONFIG -Destination $backupName -ErrorAction SilentlyContinue
            $newConfig = [PSCustomObject]@{ allowAutoUpdate = $true }
            Write-Utf8NoBom -Path $CLAUDE_DESKTOP_CONFIG -Content ($newConfig | ConvertTo-Json -Depth 10)
            Write-Log "Corrupted config backed up and recreated: $backupName" "FIX"
            $fixCount++
        }
    }

    # 4. Detect corrupted Session Storage
    $sessionDir = "$CLAUDE_CONFIG_DIR\Session Storage"
    if (Test-Path $sessionDir) {
        $corruptFiles = Get-ChildItem -Path $sessionDir -File -ErrorAction SilentlyContinue |
                        Where-Object { $_.Length -eq 0 }
        if ($corruptFiles.Count -gt 0) {
            Remove-Item -Path $sessionDir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "Deleted corrupted Session Storage ($($corruptFiles.Count) empty files)" "FIX"
            $fixCount++
        }
    }

    # 5. Detect corrupted Local Storage
    $localDir = "$CLAUDE_CONFIG_DIR\Local Storage"
    if (Test-Path $localDir) {
        $corruptLdb = Get-ChildItem -Path $localDir -Filter "*.ldb" -Recurse -ErrorAction SilentlyContinue |
                      Where-Object { $_.Length -eq 0 }
        if ($corruptLdb.Count -gt 0) {
            Remove-Item -Path $localDir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "Deleted corrupted Local Storage ($($corruptLdb.Count) empty files)" "FIX"
            $fixCount++
        }
    }

    # 6. Detect abnormally large GPUCache
    $gpuCache = "$CLAUDE_CONFIG_DIR\GPUCache"
    if (Test-Path $gpuCache) {
        $gpuCacheSize = (Get-ChildItem -Path $gpuCache -Recurse -Force -ErrorAction SilentlyContinue |
                         Measure-Object -Property Length -Sum).Sum
        if ($gpuCacheSize -gt 500MB) {
            Remove-Item -Path $gpuCache -Recurse -Force -ErrorAction SilentlyContinue
            $sizeMB = [math]::Round($gpuCacheSize / 1MB)
            Write-Log "Deleted abnormally large GPUCache (${sizeMB}MB)" "FIX"
            $fixCount++
        }
    }

    # 7. Clean old app version remnants
    $appVersionDirs = Get-ChildItem -Path "$env:LOCALAPPDATA\Claude" -Directory -Filter "app-*" -ErrorAction SilentlyContinue
    if ($appVersionDirs.Count -gt 1) {
        $latest = $appVersionDirs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        $oldDirs = $appVersionDirs | Where-Object { $_.FullName -ne $latest.FullName }
        foreach ($old in $oldDirs) {
            try {
                Remove-Item -Path $old.FullName -Recurse -Force -ErrorAction SilentlyContinue
                Write-Log "Cleaned old version: $($old.Name)" "FIX"
                $fixCount++
            } catch {
                Write-Log "Failed to remove old version (in use): $($old.Name)" "WARN"
            }
        }
    }

    # 8. Protect shortcuts (maintain GPU flags)
    if ($needGpuFlags) {
        $shortcuts = @(
            "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Claude.lnk",
            "$env:USERPROFILE\Desktop\Claude.lnk",
            "$env:PUBLIC\Desktop\Claude.lnk"
        )

        $shell = New-Object -ComObject WScript.Shell -ErrorAction SilentlyContinue
        if ($shell) {
            foreach ($shortcutPath in $shortcuts) {
                if (Test-Path $shortcutPath) {
                    try {
                        $shortcut = $shell.CreateShortcut($shortcutPath)
                        if ($shortcut.Arguments -notmatch "disable-gpu") {
                            $shortcut.Arguments = "$($shortcut.Arguments) --disable-gpu --disable-gpu-compositing".Trim()
                            $shortcut.Save()
                            Write-Log "Restored GPU flags on shortcut: $(Split-Path $shortcutPath -Leaf)" "FIX"
                            $fixCount++
                        }
                    } catch {
                        # ignore
                    }
                }
            }
        }
    }

    if ($fixCount -gt 0) {
        Write-Log "Total $fixCount setting(s) restored" "OK"
    } else {
        Write-Log "All stability settings OK" "OK"
    }

    return $fixCount
}

# ==============================================================
# Core Feature 2: Process Monitoring & Auto-Recovery
# ==============================================================
function Watch-ClaudeProcess {
    Write-Log "Starting Claude Desktop process monitor..." "INFO"

    $claudeExe = Find-ClaudeExe
    if (-not $claudeExe) {
        Write-Log "Claude Desktop executable not found" "ERROR"
        return
    }

    $config = Get-GuardianConfig
    $maxCrashesBeforeGpuDisable = 2
    $maxCrashesBeforeCacheClean = 3
    $maxCrashesBeforeFullReset = 5
    $watchIntervalSec = 10
    $consecutiveCrashes = 0
    $lastSeenPid = 0
    $wasRunning = $false

    while ($true) {
        $claudeProcs = Get-Process -Name "Claude" -ErrorAction SilentlyContinue |
                       Where-Object { $_.Path -eq $claudeExe }

        if ($claudeProcs) {
            # Claude is running
            $mainProc = $claudeProcs | Sort-Object StartTime | Select-Object -First 1

            if (-not $wasRunning) {
                Write-Log "Claude Desktop detected (PID: $($mainProc.Id))" "OK"
                $consecutiveCrashes = 0
            }

            $wasRunning = $true
            $lastSeenPid = $mainProc.Id

            # Monitor memory usage
            $memMB = [math]::Round($mainProc.WorkingSet64 / 1MB)
            if ($memMB -gt 2000) {
                Write-Log "Claude Desktop high memory usage: ${memMB}MB" "WARN"
            }

        } else {
            # Claude is not running
            if ($wasRunning) {
                # Was running but disappeared = crash detected
                $consecutiveCrashes++
                Write-Log "CRASH DETECTED! (consecutive: $consecutiveCrashes, prev PID: $lastSeenPid)" "ERROR"

                # Record crash
                $history = Get-CrashHistory
                $crashEntry = @{
                    timestamp = (Get-Date).ToString("o")
                    pid = $lastSeenPid
                    consecutiveCount = $consecutiveCrashes
                }

                if ($history.crashes -is [Array]) {
                    $crashList = [System.Collections.ArrayList]@($history.crashes)
                } else {
                    $crashList = [System.Collections.ArrayList]::new()
                }
                $crashList.Add($crashEntry) | Out-Null

                # Keep only last 100 entries
                if ($crashList.Count -gt 100) {
                    $crashList = [System.Collections.ArrayList]@($crashList | Select-Object -Last 100)
                }

                $history.crashes = $crashList.ToArray()
                $history.totalCrashes = [int]$history.totalCrashes + 1
                Save-CrashHistory $history

                # Adaptive recovery strategy
                if ($consecutiveCrashes -ge $maxCrashesBeforeFullReset) {
                    Write-Log "$consecutiveCrashes consecutive crashes - FULL CACHE RESET + restart" "FIX"
                    Start-Sleep -Seconds 3
                    Clear-AllCache
                    Protect-StabilitySettings
                    Start-Sleep -Seconds 2
                    Start-ClaudeSafe -ClaudeExe $claudeExe

                } elseif ($consecutiveCrashes -ge $maxCrashesBeforeCacheClean) {
                    Write-Log "$consecutiveCrashes consecutive crashes - cache cleanup + restart" "FIX"
                    Start-Sleep -Seconds 3
                    Clear-ProblematicCache
                    Protect-StabilitySettings
                    Start-Sleep -Seconds 2
                    Start-ClaudeSafe -ClaudeExe $claudeExe

                } elseif ($consecutiveCrashes -ge $maxCrashesBeforeGpuDisable) {
                    Write-Log "$consecutiveCrashes consecutive crashes - disabling GPU + restart" "FIX"

                    # Permanently record GPU disable in guardian config
                    $cfg = Get-GuardianConfig
                    if (-not $cfg) {
                        $cfg = [PSCustomObject]@{
                            forceDisableGpu = $true
                            installedAt = (Get-Date).ToString("o")
                            version = $GUARDIAN_VERSION
                        }
                    } else {
                        $cfg | Add-Member -NotePropertyName "forceDisableGpu" -NotePropertyValue $true -Force
                    }
                    Save-GuardianConfig $cfg

                    Protect-StabilitySettings
                    Start-Sleep -Seconds 2
                    Start-ClaudeSafe -ClaudeExe $claudeExe

                } else {
                    Write-Log "Attempting safe-mode restart after crash..." "FIX"
                    Start-Sleep -Seconds 5
                    Start-ClaudeSafe -ClaudeExe $claudeExe
                }
            }
            $wasRunning = $false
        }

        Start-Sleep -Seconds $watchIntervalSec
    }
}

function Start-ClaudeSafe {
    param([string]$ClaudeExe)

    if (-not $ClaudeExe -or -not (Test-Path $ClaudeExe)) {
        Write-Log "Invalid Claude executable path" "ERROR"
        return
    }

    $launchArgs = @()
    $config = Get-GuardianConfig
    $history = Get-CrashHistory

    # Add safe flags if crash history exists
    if (($config -and $config.forceDisableGpu) -or ($history.totalCrashes -ge 2)) {
        $launchArgs += "--disable-gpu"
        $launchArgs += "--disable-gpu-compositing"
        $launchArgs += "--disable-gpu-sandbox"
        $launchArgs += "--in-process-gpu"
    }

    $argString = $launchArgs -join " "
    Write-Log "Starting Claude Desktop: $ClaudeExe $argString" "INFO"

    try {
        if ($launchArgs.Count -gt 0) {
            Start-Process -FilePath $ClaudeExe -ArgumentList $launchArgs -ErrorAction Stop
        } else {
            Start-Process -FilePath $ClaudeExe -ErrorAction Stop
        }
        Write-Log "Claude Desktop started successfully" "OK"
    } catch {
        Write-Log "Failed to start Claude Desktop: $_" "ERROR"
    }
}

function Clear-ProblematicCache {
    Write-Log "Cleaning problematic cache directories..." "INFO"

    # Stop Claude processes
    Get-Process -Name "Claude*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    $problematic = @(
        "$env:APPDATA\Claude\GPUCache",
        "$env:APPDATA\Claude\DawnCache",
        "$env:APPDATA\Claude\DawnGraphiteCache",
        "$env:APPDATA\Claude\Code Cache"
    )

    foreach ($dir in $problematic) {
        if (Test-Path $dir) {
            Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "Deleted: $dir" "FIX"
        }
    }
}

function Clear-AllCache {
    Write-Log "Full cache reset in progress..." "INFO"

    # Stop Claude processes
    Get-Process -Name "Claude*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3

    foreach ($dir in $CACHE_DIRS) {
        if (Test-Path $dir) {
            $sizeMB = [math]::Round((Get-ChildItem -Path $dir -Recurse -Force -ErrorAction SilentlyContinue |
                       Measure-Object -Property Length -Sum).Sum / 1MB, 1)
            Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "Deleted: $dir (${sizeMB}MB)" "FIX"
        }
    }

    # Also delete Session Storage
    $sessionDir = "$env:APPDATA\Claude\Session Storage"
    if (Test-Path $sessionDir) {
        Remove-Item -Path $sessionDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Deleted Session Storage" "FIX"
    }

    # Also delete Local Storage
    $localDir = "$env:APPDATA\Claude\Local Storage"
    if (Test-Path $localDir) {
        Remove-Item -Path $localDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Deleted Local Storage (re-login required)" "FIX"
    }
}

# ==============================================================
# Core Feature 3: Windows Scheduled Task Registration (persistence)
# ==============================================================
function Install-Guardian {
    Write-Log "Installing Guardian..." "INFO"

    $scriptPath = $MyInvocation.ScriptName
    if (-not $scriptPath) {
        $scriptPath = $PSCommandPath
    }
    if (-not $scriptPath) {
        Write-Log "Cannot determine script path. Please register manually." "ERROR"
        return
    }

    # Create guardian config
    $config = [PSCustomObject]@{
        version = $GUARDIAN_VERSION
        installedAt = (Get-Date).ToString("o")
        scriptPath = $scriptPath
        forceDisableGpu = $false
        autoWatch = $true
    }

    # Keep GPU disabled if crash history exists
    $history = Get-CrashHistory
    if ($history.totalCrashes -ge 2) {
        $config.forceDisableGpu = $true
        Write-Log "Previous crash history found - keeping GPU disabled" "WARN"
    }

    Save-GuardianConfig $config

    # Scheduled Task 1: Settings protection at login
    $protectAction = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Protect -Silent"

    $protectTrigger = New-ScheduledTaskTrigger -AtLogOn

    $protectSettings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

    try {
        Unregister-ScheduledTask -TaskName "${GUARDIAN_NAME}_Protect" -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask `
            -TaskName "${GUARDIAN_NAME}_Protect" `
            -Action $protectAction `
            -Trigger $protectTrigger `
            -Settings $protectSettings `
            -Description "Claude Desktop stability settings protection (auto-run at login)" `
            -ErrorAction Stop | Out-Null
        Write-Log "Scheduled task registered: ${GUARDIAN_NAME}_Protect (settings protection at login)" "OK"
    } catch {
        Write-Log "Scheduled task registration failed (admin required): $_" "WARN"

        # Fallback: create shortcut in Startup folder
        $startupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ClaudeGuardian.lnk"
        try {
            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut($startupPath)
            $shortcut.TargetPath = "powershell.exe"
            $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Protect -Silent"
            $shortcut.WindowStyle = 7  # Minimized
            $shortcut.Description = "Claude Desktop Guardian"
            $shortcut.Save()
            Write-Log "Fallback: Added to Startup folder: $startupPath" "OK"
        } catch {
            Write-Log "Startup shortcut creation also failed: $_" "ERROR"
        }
    }

    # Scheduled Task 2: Process watchdog (background)
    $watchAction = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Watch -Silent"

    $watchTrigger = New-ScheduledTaskTrigger -AtLogOn
    # 5 minute delay for system stabilization
    $watchTrigger.Delay = "PT5M"

    $watchSettings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 24) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5)

    try {
        Unregister-ScheduledTask -TaskName "${GUARDIAN_NAME}_Watch" -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask `
            -TaskName "${GUARDIAN_NAME}_Watch" `
            -Action $watchAction `
            -Trigger $watchTrigger `
            -Settings $watchSettings `
            -Description "Claude Desktop process monitor and auto-recovery" `
            -ErrorAction Stop | Out-Null
        Write-Log "Scheduled task registered: ${GUARDIAN_NAME}_Watch (process monitor)" "OK"
    } catch {
        Write-Log "Watch scheduled task registration failed: $_" "WARN"
    }

    # Run initial settings protection
    $fixCount = Protect-StabilitySettings

    # Create stable launcher batch file
    Create-StableLauncher

    # Reset crash history (count fresh from install)
    $newHistory = @{
        crashes = @()
        totalCrashes = 0
        lastReset = (Get-Date).ToString("o")
        guardianVersion = $GUARDIAN_VERSION
    }
    Save-CrashHistory $newHistory

    Write-Log "" "INFO"
    Write-Log "============================================" "INFO"
    Write-Log "Guardian installation complete!" "OK"
    Write-Log "============================================" "INFO"
    Write-Log "- Stability settings auto-protected at every login" "INFO"
    Write-Log "- Auto safe-mode restart on Claude crash" "INFO"
    Write-Log "- Settings auto-restored after app updates" "INFO"
    Write-Log "- Logs: $GUARDIAN_LOG_DIR" "INFO"
    Write-Log "- Uninstall: .\claude_desktop_guardian.ps1 -Uninstall" "INFO"
    Write-Log "============================================" "INFO"
}

function Uninstall-Guardian {
    Write-Log "Uninstalling Guardian..." "INFO"

    # Remove scheduled tasks
    Unregister-ScheduledTask -TaskName "${GUARDIAN_NAME}_Protect" -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName "${GUARDIAN_NAME}_Watch" -Confirm:$false -ErrorAction SilentlyContinue
    Write-Log "Scheduled tasks removed" "OK"

    # Remove startup shortcut
    $startupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ClaudeGuardian.lnk"
    if (Test-Path $startupPath) {
        Remove-Item -Path $startupPath -Force -ErrorAction SilentlyContinue
        Write-Log "Startup shortcut removed" "OK"
    }

    Write-Log "Guardian uninstalled (logs and history preserved)" "OK"
    Write-Log "To delete logs too: Remove-Item -Recurse '$GUARDIAN_LOG_DIR'" "INFO"
}

function Create-StableLauncher {
    # Use .NET to get correct Desktop path (handles Korean/Unicode usernames)
    $desktopPath = [Environment]::GetFolderPath('Desktop')
    if (-not $desktopPath -or -not (Test-Path $desktopPath)) {
        $desktopPath = "$env:USERPROFILE\Desktop"
        if (-not (Test-Path $desktopPath)) {
            New-Item -ItemType Directory -Path $desktopPath -Force -ErrorAction SilentlyContinue | Out-Null
        }
    }
    $launcherPath = Join-Path $desktopPath "Claude_StableMode.bat"
    $content = @"
@echo off
chcp 65001 >nul
echo ============================================
echo  Claude Desktop - Stable Mode
echo  (Guardian Protected)
echo ============================================
echo.

REM Kill existing Claude processes
taskkill /f /im "Claude.exe" >nul 2>&1
timeout /t 2 >nul

echo [1/3] Cleaned up existing processes
echo [2/3] GPU hardware acceleration DISABLED
echo [3/3] Starting Claude Desktop...
echo.

if exist "%LOCALAPPDATA%\Programs\Claude\Claude.exe" (
    start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox --in-process-gpu
) else if exist "%PROGRAMFILES%\Claude\Claude.exe" (
    start "" "%PROGRAMFILES%\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox --in-process-gpu
) else (
    echo [ERROR] Claude Desktop not found.
    pause
    exit /b 1
)

echo Claude Desktop has started.
timeout /t 3 >nul
"@

    try {
        [System.IO.File]::WriteAllText($launcherPath, $content, [System.Text.Encoding]::UTF8)
        Write-Log "Stable launcher created: $launcherPath" "OK"
    } catch {
        Write-Log "Stable launcher creation failed (non-critical): $_" "WARN"
    }
}

# ==============================================================
# Core Feature 4: Log cleanup (auto-delete old logs)
# ==============================================================
function Clean-OldLogs {
    if (-not (Test-Path $GUARDIAN_LOG_DIR)) { return }

    $oldLogs = Get-ChildItem -Path $GUARDIAN_LOG_DIR -File -Filter "guardian_*.log" -ErrorAction SilentlyContinue |
               Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }

    foreach ($log in $oldLogs) {
        Remove-Item -Path $log.FullName -Force -ErrorAction SilentlyContinue
    }

    if ($oldLogs.Count -gt 0) {
        Write-Log "Cleaned $($oldLogs.Count) old log file(s)" "INFO"
    }
}

# ==============================================================
# Main Execution
# ==============================================================
Write-Banner
Clean-OldLogs

if ($Install) {
    Install-Guardian
} elseif ($Uninstall) {
    Uninstall-Guardian
} elseif ($Watch) {
    Write-Log "Watch mode started (Ctrl+C to stop)" "INFO"
    Protect-StabilitySettings
    Watch-ClaudeProcess
} elseif ($Protect) {
    Protect-StabilitySettings
} else {
    # No parameter - show usage
    if (-not $Silent) {
        Write-Host "  Usage:" -ForegroundColor White
        Write-Host ""
        Write-Host "    .\claude_desktop_guardian.ps1 -Install    # Install Guardian (recommended)" -ForegroundColor Green
        Write-Host "    .\claude_desktop_guardian.ps1 -Watch      # Start manual monitoring" -ForegroundColor Gray
        Write-Host "    .\claude_desktop_guardian.ps1 -Protect    # Apply stability settings once" -ForegroundColor Gray
        Write-Host "    .\claude_desktop_guardian.ps1 -Uninstall  # Remove Guardian" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  First time? Run -Install to:" -ForegroundColor White
        Write-Host "    - Auto-protect stability settings at every login" -ForegroundColor Gray
        Write-Host "    - Auto-restart Claude in safe mode on crash" -ForegroundColor Gray
        Write-Host "    - Auto-restore settings after app updates" -ForegroundColor Gray
        Write-Host ""
    }
}
