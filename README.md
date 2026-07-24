# NECRO-BOTNET v1.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows-lightgrey.svg)]()
[![Language](https://img.shields.io/badge/language-Python%20%7C%20C-blue.svg)]()

A Command and Control (C2) framework with real-time dashboard for authorized security testing and educational purposes.

> **Disclaimer**: This software is provided for authorized security testing and educational purposes only. Unauthorized use is illegal and unethical.

## Overview

NECRO-BOTNET is a C2 framework featuring a Flask-based web dashboard for managing zombie nodes and coordinating distributed attacks. It demonstrates botnet command and control architecture for educational purposes.

## Features

| Feature | Description |
|---------|-------------|
| Real-time Dashboard | WebSocket-based monitoring interface |
| Encrypted C2 | Fernet symmetric encryption for communications |
| Multi-platform | Zombie payload for Linux and Windows |
| Attack Methods | HTTP, SYN, UDP, ICMP, Slowloris floods |
| Live Monitoring | Traffic graphs and zombie status |
| Anti-Analysis | Debugger and sandbox detection |

## Project Structure

```
NECRO-BOTNET/
├── c2_server.py        # Flask C2 server with web dashboard
├── zombie_payload.c    # C zombie payload for Linux/Windows
├── README.md           # This file
├── LICENSE             # MIT License
├── SECURITY.md         # Security policy
└── CONTRIBUTING.md     # Contribution guidelines
```

## Prerequisites

### System Dependencies
```bash
sudo apt update
sudo apt install -y gcc make python3 python3-pip upx mingw-w64
```

### Python Dependencies
```bash
pip3 install flask flask-socketio cryptography
```

## Build

### Linux Zombie
```bash
gcc -O2 -s -static -o zombie_linux zombie_payload.c -lpthread -lcurl
upx --ultra-brute zombie_linux -o zombie_linux_obf
```

### Windows Zombie (cross-compile from Kali)
```bash
x86_64-w64-mingw32-gcc -O2 -s -static -o zombie.exe zombie_payload.c -lws2_32 -lwininet -lpthread
upx --ultra-brute zombie.exe -o zombie_obf.exe
```

## Usage

### Start C2 Server
```bash
python3 c2_server.py --host 0.0.0.0 --port 5000 --attack-port 4444
```

### Access Dashboard
Open browser to: `http://YOUR_KALI_IP:5000`

### Command Line Options
```
--host HOST        Bind address (default: 0.0.0.0)
--port PORT        Web dashboard port (default: 5000)
--attack-port PORT C2 socket port (default: 4444)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WEB DASHBOARD                        │
│  - Real-time zombie monitoring                          │
│  - Attack control interface                             │
│  - Traffic statistics and graphs                        │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    C2 SERVER                            │
│  - Flask + SocketIO                                     │
│  - Fernet encryption                                   │
│  - Zombie management                                    │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                 ZOMBIE PAYLOAD                          │
│  - C-based multi-platform agent                         │
│  - Anti-analysis techniques                             │
│  - Attack execution modules                             │
└─────────────────────────────────────────────────────────┘
```

## Attack Methods

| Method | Description | Impact |
|--------|-------------|--------|
| HTTP Flood | Layer 7 GET floods with random headers | Web server overload |
| SYN Flood | Raw TCP SYN packets with spoofed IPs | Connection table exhaustion |
| UDP Flood | UDP traffic to random ports | Bandwidth saturation |
| ICMP Flood | Ping of death | Router CPU exhaustion |
| Slowloris | Slow HTTP headers | Thread exhaustion |

## Configuration

Edit the following in `c2_server.py`:

```python
DEFAULT_C2_HOST = "0.0.0.0"        # Bind address
DEFAULT_C2_PORT = 5000              # Web dashboard port
DEFAULT_ATTACK_PORT = 4444          # C2 socket port
SECRET_KEY = b"YOUR_SECRET_KEY"    # Encryption key
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web dashboard |
| `/api/zombies` | GET | List all zombies |
| `/api/stats` | GET | Get attack statistics |
| `/api/attack/start` | POST | Start an attack |
| `/api/attack/stop` | POST | Stop current attack |

## Detection Indicators

- Flask/SocketIO server running on port 5000
- Unusual outbound connections on port 4444
- Large volumes of ICMP/UDP traffic
- Multiple concurrent connections to same target

## Legal Notice

This software is provided for **authorized security testing and educational purposes only**.

- **Authorization Required**: You must have explicit written permission from the system owner
- **Legal Compliance**: Unauthorized access to computer systems is illegal
- **No Warranty**: This software is provided "as is" without warranty
- **Liability**: The author assumes no responsibility for misuse

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Security

For reporting security vulnerabilities, see [SECURITY.md](SECURITY.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**wsuits6** - [GitHub](https://github.com/wsuits6)
