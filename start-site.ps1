param(
    [int]$ApiPort = 8000,
    [int]$FrontendPort = 5173,
    [int]$OllamaPort = 11434,
    [switch]$SkipModelWarmup
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $Root "frontend"
$NodeDir = "C:\Program Files\nodejs"
$OllamaExe = "ollama"

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

if (Test-Path $NodeDir) {
    $env:Path = "$NodeDir;$env:Path"
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
    Start-Sleep -Seconds 3
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

if (-not (Test-Port -Port $ApiPort)) {
    Write-Host "Starting FastAPI backend on http://127.0.0.1:$ApiPort ..." -ForegroundColor Yellow
    Start-PowerShellProcess `
        -Title "A.R.I.A. API" `
        -WorkingDirectory $Root `
        -Command "python -B -m uvicorn api.main:app --host 127.0.0.1 --port $ApiPort"
    Start-Sleep -Seconds 2
}
else {
    Write-Host "FastAPI backend is already running on port $ApiPort." -ForegroundColor Green
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    try {
        npm install
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Port -Port $FrontendPort)) {
    Write-Host "Starting Vite frontend on http://127.0.0.1:$FrontendPort ..." -ForegroundColor Yellow
    Start-PowerShellProcess `
        -Title "A.R.I.A. Frontend" `
        -WorkingDirectory $FrontendDir `
        -Command "`$env:Path = '$NodeDir;' + `$env:Path; npm run dev -- --host 127.0.0.1 --port $FrontendPort"
    Start-Sleep -Seconds 2
}
else {
    Write-Host "Vite frontend is already running on port $FrontendPort." -ForegroundColor Green
}

Write-Host ""
Write-Host "A.R.I.A. Studio is ready:" -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
Write-Host "API:      http://127.0.0.1:$ApiPort/api/health"
Write-Host "Ollama:   http://127.0.0.1:$OllamaPort"
Write-Host ""
Write-Host "Tip: run with -SkipModelWarmup if you want the site to open faster." -ForegroundColor DarkGray
