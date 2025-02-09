# Docker Debugging Guide

## Remote Debugging with `--host`

```powershell
$env:DOCKER_HOST = "tcp://<host>:<port>"
docker [command] [options]

# Example:
$env:DOCKER_HOST = "ssh://user@remote-server"
docker system info
```

## Security Considerations
- Use SSH tunnels for secure connections
- Configure TLS certificates for daemon access
- Limit exposure to trusted networks
