param(
    [int]$ApiPort = 8000,
    [int]$FrontendPort = 5173,
    [int]$OllamaPort = 11434,
    [switch]$SkipModelWarmup,
    [switch]$SkipInstall,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $Root "frontend"
$NodeDir = "C:\Program Files\nodejs"
$OllamaExe = "ollama"
$StartedOk = $true

function Test-Port {
    param(
        [string]$HostName = "127.0.0.1",
        [int]$Port
    )

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        $connected = $async.AsyncWaitHandle.WaitOne(500, $false)
        if ($connected) {
            $client.EndConnect($async)
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Wait-Port {
    param(
        [string]$Name,
        [int]$Port,
        [int]$TimeoutSeconds = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Port -Port $Port) {
            Write-Host "$Name is accepting connections on port $Port." -ForegroundColor Green
            return $true
        }
        Start-Sleep -Milliseconds 500
    }

    Write-Host "$Name did not respond on port $Port within $TimeoutSeconds seconds." -ForegroundColor Yellow
    return $false
}

function Get-EnvValue {
    param(
        [string]$Key,
        [string]$Default = ""
    )

    $envPath = Join-Path $Root ".env"
    if (-not (Test-Path $envPath)) {
        return $Default
    }

    $line = Get-Content $envPath | Where-Object { $_ -match "^$Key=" } | Select-Object -First 1
    if (-not $line) {
        return $Default
    }

    $value = $line.Substring($Key.Length + 1).Trim()
    return $value.Trim("'").Trim('"')
}

function Get-DatabaseMode {
    $databaseUrl = Get-EnvValue -Key "DATABASE_URL" -Default ""
    if ($databaseUrl) {
        return "PostgreSQL"
    }
    return "SQLite"
}

function Test-NodeChildProcess {
    $script = @"
const { spawnSync } = require('child_process');
const command = process.platform === 'win32' ? 'cmd.exe' : 'sh';
const args = process.platform === 'win32' ? ['/c', 'exit 0'] : ['-c', 'exit 0'];
const result = spawnSync(command, args);
if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status || 0);
"@
    $output = & node -e $script 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Node cannot spawn helper processes on this machine." -ForegroundColor Yellow
        if ($output) {
            Write-Host $output -ForegroundColor DarkYellow
        }
        Write-Host "If the frontend fails with spawn EPERM, run PowerShell as Administrator or allow node.exe and esbuild.exe in Windows Security." -ForegroundColor Yellow
        return $false
    }
    return $true
}

function Start-PowerShellProcess {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )

    $wrappedCommand = "`$Host.UI.RawUI.WindowTitle = '$Title'; Set-Location '$WorkingDirectory'; $Command"
    Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", $wrappedCommand)
}

Write-Host ""
Write-Host "Starting A.R.I.A. Studio..." -ForegroundColor Cyan
$DatabaseMode = Get-DatabaseMode
Write-Host "Database mode: $DatabaseMode" -ForegroundColor DarkGray

if (Test-Path $NodeDir) {
    $env:Path = "$NodeDir;$env:Path"
}

$nodeCommand = Get-Command "node" -ErrorAction SilentlyContinue
if (-not $nodeCommand) {
    Write-Host "Node.js was not found on PATH. The frontend cannot start until Node is installed or added to PATH." -ForegroundColor Red
    $StartedOk = $false
}

$ollamaCommand = Get-Command "ollama" -ErrorAction SilentlyContinue
if ($ollamaCommand) {
    $OllamaExe = $ollamaCommand.Source
}
elseif (Test-Path "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe") {
    $OllamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
}

if (-not (Test-Port -Port $OllamaPort)) {
    Write-Host "Starting Ollama on port $OllamaPort..." -ForegroundColor Yellow
    Start-Process -FilePath $OllamaExe -ArgumentList @("serve") -WindowStyle Hidden
    if (-not (Wait-Port -Name "Ollama" -Port $OllamaPort -TimeoutSeconds 20)) {
        $StartedOk = $false
    }
}
else {
    Write-Host "Ollama is already running." -ForegroundColor Green
}

$Model = Get-EnvValue -Key "OLLAMA_MODEL" -Default "gemma"
if (-not $SkipModelWarmup) {
    Write-Host "Warming A.R.I.A. model: $Model" -ForegroundColor Yellow
    try {
        & $OllamaExe run $Model "Reply with: ready" | Out-Null
        Write-Host "A.R.I.A. model is ready." -ForegroundColor Green
    }
    catch {
        Write-Host "Model warmup failed. The site will still start, but chat may fail until Ollama/model is ready." -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor DarkRed
    }
}
else {
    Write-Host "Skipping A.R.I.A. model warmup." -ForegroundColor DarkGray
}

if (-not (Test-Port -Port $ApiPort)) {
    Write-Host "Starting FastAPI backend on http://127.0.0.1:$ApiPort ..." -ForegroundColor Yellow
    Start-PowerShellProcess `
        -Title "A.R.I.A. API" `
        -WorkingDirectory $Root `
        -Command "python -B -m uvicorn api.main:app --host 127.0.0.1 --port $ApiPort"
    if (-not (Wait-Port -Name "FastAPI backend" -Port $ApiPort -TimeoutSeconds 45)) {
        $StartedOk = $false
    }
}
else {
    Write-Host "FastAPI backend is already running on port $ApiPort." -ForegroundColor Green
}

if ($nodeCommand -and (-not $SkipInstall) -and (-not (Test-Path (Join-Path $FrontendDir "node_modules")))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    try {
        npm.cmd install
    }
    finally {
        Pop-Location
    }
}
elseif ($SkipInstall) {
    Write-Host "Skipping frontend dependency install." -ForegroundColor DarkGray
}

if ($nodeCommand -and (-not (Test-Port -Port $FrontendPort))) {
    Test-NodeChildProcess | Out-Null
    Write-Host "Starting Vite frontend on http://127.0.0.1:$FrontendPort ..." -ForegroundColor Yellow
    Start-PowerShellProcess `
        -Title "A.R.I.A. Frontend" `
        -WorkingDirectory $FrontendDir `
        -Command "`$env:Path = '$NodeDir;' + `$env:Path; npm.cmd run dev -- --host 127.0.0.1 --port $FrontendPort --configLoader native"
    if (-not (Wait-Port -Name "Vite frontend" -Port $FrontendPort -TimeoutSeconds 45)) {
        Write-Host "Frontend did not start. Check the A.R.I.A. Frontend window for the exact npm/Vite error." -ForegroundColor Yellow
        $StartedOk = $false
    }
}
elseif (Test-Port -Port $FrontendPort) {
    Write-Host "Vite frontend is already running on port $FrontendPort." -ForegroundColor Green
}

$FrontendUrl = "http://127.0.0.1:$FrontendPort"
if (-not $NoBrowser) {
    Write-Host "Opening A.R.I.A. Studio..." -ForegroundColor Cyan
    Start-Process $FrontendUrl
}

Write-Host ""
if ($StartedOk) {
    Write-Host "A.R.I.A. Studio is ready:" -ForegroundColor Green
}
else {
    Write-Host "A.R.I.A. Studio started with warnings:" -ForegroundColor Yellow
}
Write-Host "Frontend: $FrontendUrl"
Write-Host "API:      http://127.0.0.1:$ApiPort/api/health"
Write-Host "Ollama:   http://127.0.0.1:$OllamaPort"
Write-Host "Database: $DatabaseMode"
Write-Host ""
Write-Host "Tip: run with -SkipModelWarmup if you want the site to open faster." -ForegroundColor DarkGray
Write-Host "Tip: run with -NoBrowser if you want to start services without opening the app." -ForegroundColor DarkGray
