#Requires -Version 5.1
<#
.SYNOPSIS
Configure Daihua CAD from this repository. Requires Windows and Python 3.11+.
.EXAMPLE
.\install.ps1 -Client codex
.EXAMPLE
.\install.ps1 -Client cursor -DryRun -PythonPath C:\Python312\python.exe
#>
[CmdletBinding()]
param(
    [ValidateSet('codex', 'claude', 'cursor', 'generic')]
    [string]$Client = 'codex',
    [string]$ConfigPath,
    [string]$SkillsDir,
    [string]$PythonPath,
    [switch]$SkipDeps,
    [switch]$DryRun,
    [switch]$Check,
    [switch]$Uninstall
)
$ErrorActionPreference = 'Stop'

if (-not $PSScriptRoot -or -not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'scripts/install.py'))) {
    throw 'Run this installer from a complete local clone of Daihua CAD. Ask your agent to clone the repository, then run powershell -NoProfile -ExecutionPolicy Bypass -File <clone>\install.ps1 -Client codex.'
}

# ProcessStartInfo also works in console-less agent hosts. Every argument is
# quoted using the Windows CRT backslash rules, without an intermediary shell.
function ConvertTo-DaihuaArgument([string]$Value) {
    $escaped = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    return '"' + $escaped + '"'
}
function Invoke-DaihuaPython([string]$Executable, [string[]]$Arguments, [switch]$Quiet) {
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $Executable
    $startInfo.Arguments = ($Arguments | ForEach-Object { ConvertTo-DaihuaArgument $_ }) -join ' '
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    $startInfo.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $startInfo.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    $child = New-Object System.Diagnostics.Process
    $child.StartInfo = $startInfo
    try {
        if (-not $child.Start()) { throw 'Unable to start Python process.' }
        # Drain both pipes concurrently, including verbose pip output.
        $outputTask = $child.StandardOutput.ReadToEndAsync()
        $errorTask = $child.StandardError.ReadToEndAsync()
        $child.WaitForExit()
        $outputText = $outputTask.GetAwaiter().GetResult()
        $errorText = $errorTask.GetAwaiter().GetResult()
        if (-not $Quiet -and $outputText) { Write-Host $outputText }
        if (-not $Quiet -and $errorText) { Write-Host $errorText }
        return $child.ExitCode
    } finally {
        $child.Dispose()
    }
}

$pythonCommand = $null
$pythonPrefix = @()
$candidates = @(
    @{ Name = 'py'; Prefix = @('-3.12') },
    @{ Name = 'py'; Prefix = @('-3.11') },
    @{ Name = 'python'; Prefix = @() },
    @{ Name = 'python3'; Prefix = @() }
)
if ($PythonPath) {
    if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
        throw "PythonPath does not exist: $PythonPath"
    }
    $candidates = @(@{ Name = $PythonPath; Prefix = @() }) + $candidates
}
foreach ($candidate in $candidates) {
    $command = Get-Command $candidate.Name -ErrorAction SilentlyContinue
    if (-not $command) { continue }
    try {
        $prefix = @($candidate.Prefix)
        $probeArgs = @($prefix) + @('-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)')
        $probeExitCode = Invoke-DaihuaPython -Executable $command.Source -Arguments $probeArgs -Quiet
        if ($probeExitCode -eq 0) {
            $pythonCommand = $command.Source
            $pythonPrefix = $prefix
            break
        }
    } catch {
        # Try the next launcher or interpreter candidate.
    }
}
if (-not $pythonCommand) {
    throw 'Python 3.11+ was not found. Pass -PythonPath <path-to-python.exe> for an existing installation, or install Python from python.org (include pip and the Python launcher), reopen the terminal, then rerun this installer. If winget is available: winget install --id Python.Python.3.12 -e'
}

$installerArgs = @((Join-Path $PSScriptRoot 'scripts/install.py'), '--client', $Client.ToLowerInvariant())
if ($ConfigPath) { $installerArgs += @('--config', $ConfigPath) }
if ($SkillsDir) { $installerArgs += @('--skills-dir', $SkillsDir) }
if ($SkipDeps) { $installerArgs += '--skip-deps' }
if ($DryRun) { $installerArgs += '--dry-run' }
if ($Check) { $installerArgs += '--check' }
if ($Uninstall) { $installerArgs += '--uninstall' }

$installerExitCode = Invoke-DaihuaPython -Executable $pythonCommand -Arguments (@($pythonPrefix) + @($installerArgs))
if ($installerExitCode -ne 0) {
    throw "Daihua CAD installer failed (exit code $installerExitCode). Review the ERROR message above; no automatic overwrite is performed for a conflicting configuration."
}
