# NECRO-BOTNET v1.0

A Command and Control (C2) framework with dashboard for red team operations.

## Features

- WebSocket-based real-time dashboard
- Encrypted C2 communication (Fernet)
- Multi-platform zombie payload (Linux/Windows)
- Attack methods: HTTP Flood, SYN Flood, UDP Flood, ICMP Flood, Slowloris
- Live traffic graphs and zombie monitoring
- Anti-debugging and sandbox detection

## Files

| File | Description |
|------|-------------|
| `c2_server.py` | Flask C2 server with web dashboard |
| `zombie_payload.c` | C zombie payload for Linux/Windows |
| `install_deps.sh` | Install build dependencies |
| `build_linux.sh` | Compile Linux zombie payload |
| `build_windows.sh` | Cross-compile Windows zombie payload |
| `run_server.sh` | Start the C2 server |

## Prerequisites

```bash
sudo apt update
sudo apt install -y gcc make python3 python3-pip upx mingw-w64
pip3 install flask flask-socketio cryptography
```

## Build

```bash
chmod +x install_deps.sh && ./install_deps.sh
chmod +x build_linux.sh && ./build_linux.sh
chmod +x build_windows.sh && ./build_windows.sh
```

## Usage

1. Start the C2 server:
```bash
chmod +x run_server.sh && ./run_server.sh
```

2. Access the dashboard at: `http://YOUR_KALI_IP:5000`

3. Deploy the zombie payload to target machines

## Attack Methods

| Method | Description | Impact |
|--------|-------------|--------|
| HTTP Flood | Layer 7 GET floods with random headers | Takes down web servers |
| SYN Flood | Raw TCP SYN packets with spoofed IPs | Consumes connection tables |
| UDP Flood | UDP traffic to random ports | Saturates bandwidth |
| ICMP Flood | Ping of death | Wastes CPU on routers |
| Slowloris | Slow HTTP headers | Exhausts server threads |

## Dashboard Features

- Live zombie count (total and online)
- Attack status (target, method, duration)
- Traffic graph (real-time packets per second)
- Attack power estimation (Gbps)
- Zombie list with IP, status, OS, attack power
- Attack log with timestamps

## Disclaimer

This tool is provided for authorized security testing and educational purposes only. Unauthorized use is illegal.
