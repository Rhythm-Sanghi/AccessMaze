param(
    [string]$Package = $PSScriptRoot,
    [string]$Report = (Join-Path $env:TEMP 'AccessMaze-portable-check.json'),
    [switch]$IntegrityOnly
)
$ErrorActionPreference = 'Stop'
$packageRoot = (Resolve-Path -LiteralPath $Package).Path
$manifest = Get-Content -LiteralPath (Join-Path $packageRoot 'package-manifest.json') -Raw | ConvertFrom-Json
$prefix = $packageRoot.TrimEnd('\') + '\'
foreach ($entry in $manifest.files) {
    $filePath = [IO.Path]::GetFullPath((Join-Path $packageRoot $entry.path))
    if (-not $filePath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest path escapes package' }
    $file = Get-Item -LiteralPath $filePath
    $stream = [IO.File]::OpenRead($filePath)
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { $digest = [BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $hasher.Dispose() }
    if ($file.Length -ne $entry.bytes -or $digest -ne $entry.sha256) {
        throw "Package integrity failed: $($entry.path)"
    }
}
if ($IntegrityOnly) { Write-Output 'Package integrity passed'; exit 0 }
$storage = Join-Path $env:TEMP ('AccessMaze portable check ' + [guid]::NewGuid())
[IO.Directory]::CreateDirectory($storage) | Out-Null
$process = New-Object Diagnostics.Process
$info = New-Object Diagnostics.ProcessStartInfo
$info.FileName = Join-Path $packageRoot 'accessmaze-worker.exe'
$info.Arguments = '--resources "' + (Join-Path $packageRoot 'resources') + '" --storage "' + $storage + '"'
$info.WorkingDirectory = $storage
$info.UseShellExecute = $false
$info.CreateNoWindow = $true
$info.RedirectStandardInput = $true
$info.RedirectStandardOutput = $true
$info.RedirectStandardError = $true
$info.StandardOutputEncoding = [Text.Encoding]::UTF8
$info.EnvironmentVariables['PATH'] = Join-Path $env:SystemRoot 'System32'
$info.EnvironmentVariables.Remove('PLAYWRIGHT_BROWSERS_PATH')
$process.StartInfo = $info
$sequence = 0
function Invoke-Worker($method, $parameters = @{}) {
    $script:sequence += 1
    $request = @{version=1; id=[string]$script:sequence; method=$method; params=$parameters} | ConvertTo-Json -Depth 40 -Compress
    $process.StandardInput.WriteLine($request)
    $process.StandardInput.Flush()
    $read = $process.StandardOutput.ReadLineAsync()
    if (-not $read.Wait(30000)) { throw "Worker response timeout: $method" }
    if (-not $read.Result) { throw 'Worker closed its private output pipe' }
    $reply = $read.Result | ConvertFrom-Json
    if ($reply.error) { throw ($reply.error | ConvertTo-Json -Compress) }
    return $reply.result
}
$runs = @()
$timer = [Diagnostics.Stopwatch]::StartNew()
try {
    $process.Start() | Out-Null
    $stderr = $process.StandardError.ReadToEndAsync()
    $health = Invoke-Worker 'health'
    $startup = [Math]::Round($timer.Elapsed.TotalSeconds, 3)
    foreach ($kind in @('accessible', 'broken', 'conditional')) {
        $project = Invoke-Worker 'project.save' @{project=@{name=$kind;journey=$health.templates.$kind}}
        $run = Invoke-Worker 'run.start' @{project_id=$project.id;authorized=$true;allow_effects=$true}
        $deadline = [DateTime]::UtcNow.AddSeconds(45)
        do {
            $result = Invoke-Worker 'run.get' @{id=$run.id}
            if ($result.status -notin @('preparing','running','paused','awaiting_approval')) { break }
            Start-Sleep -Milliseconds 100
        } while ([DateTime]::UtcNow -lt $deadline)
        $expected = if ($kind -eq 'broken') {'failed'} else {'completed_with_limitations'}
        if ($result.status -ne $expected) { throw "Unexpected $kind status: $($result.status)" }
        $jsonReport = Invoke-Worker 'report.export' @{id=$run.id;format='json'}
        $parsed = $jsonReport.content | ConvertFrom-Json
        if ($parsed.id -ne $run.id) { throw 'Report run identity mismatch' }
        $runs += @{fixture=$kind;status=$result.status;findings=@($result.findings).Count}
    }
    $process.StandardInput.Close()
    if (-not $process.WaitForExit(15000)) { throw 'Worker did not stop after EOF' }
    if ($process.ExitCode -ne 0) { throw "Worker exit $($process.ExitCode): $($stderr.Result)" }
    @{integrity='passed';source_commit=$manifest.source_commit;source_dirty=$manifest.source_dirty;
      system_path_only=$true;worker_startup_seconds=$startup;runs=$runs;
      limitation='Automated check on this machine; independent clean Windows installation and manual accessibility review remain required.'} |
        ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $Report -Encoding UTF8
    Write-Output "Portable check passed. Report: $Report"
} finally {
    if ($process.Id -and -not $process.HasExited) { $process.Kill(); $process.WaitForExit() }
    $process.Dispose()
    # Preserve this uniquely named storage directory for diagnosing any failure.
    Write-Output "Check storage: $storage"
}
