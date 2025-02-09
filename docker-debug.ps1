# Connect to remote Docker host for debugging
# Usage: .\docker-debug.ps1 -RemoteHost <host>

param(
    [Parameter(Mandatory=$true)]
    [string]$RemoteHost
)

$env:DOCKER_HOST = $RemoteHost
Write-Host "Connected to Docker daemon at $RemoteHost"
docker info
docker ps -a
