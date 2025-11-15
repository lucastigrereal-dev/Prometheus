"""
PROMETHEUS V3 - WEB DASHBOARD
Dashboard em tempo real com FastAPI e WebSockets
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import psutil
import os

logger = logging.getLogger(__name__)

# ============================================================================
# DASHBOARD API
# ============================================================================

class DashboardAPI:
    """API do Dashboard do Prometheus"""
    
    def __init__(self):
        self.app = FastAPI(title="Prometheus Control Center", version="3.0")
        self.websocket_clients = []
        self.system_metrics = {}
        self.command_queue = asyncio.Queue()
        self.setup_routes()
        self.setup_middleware()
    
    def setup_middleware(self):
        """Configura middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Configura rotas da API"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Serve o dashboard principal"""
            return self.get_dashboard_html()
        
        @self.app.get("/api/status")
        async def get_status():
            """Retorna status atual do sistema"""
            return {
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "metrics": await self.get_system_metrics(),
                "modules": await self.get_modules_status(),
                "providers": await self.get_providers_status()
            }
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Retorna métricas do sistema"""
            return await self.get_system_metrics()
        
        @self.app.get("/api/logs")
        async def get_logs(lines: int = 50):
            """Retorna últimas linhas do log"""
            return await self.get_recent_logs(lines)
        
        @self.app.post("/api/command")
        async def execute_command(command: dict):
            """Executa comando no Prometheus"""
            cmd = command.get("command")
            if not cmd:
                raise HTTPException(status_code=400, detail="No command provided")
            
            # Adiciona comando à fila
            await self.command_queue.put(cmd)
            
            return {
                "status": "queued",
                "command": cmd,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/api/jobs")
        async def get_scheduled_jobs():
            """Retorna jobs agendados"""
            return await self.get_jobs_status()
        
        @self.app.post("/api/jobs/{job_id}/run")
        async def run_job(job_id: str):
            """Executa job imediatamente"""
            # Aqui você integraria com o scheduler
            return {"status": "triggered", "job_id": job_id}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket para atualizações em tempo real"""
            await websocket.accept()
            self.websocket_clients.append(websocket)
            
            try:
                while True:
                    # Envia atualizações a cada segundo
                    data = await self.get_realtime_data()
                    await websocket.send_json(data)
                    await asyncio.sleep(1)
            except WebSocketDisconnect:
                self.websocket_clients.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.websocket_clients:
                    self.websocket_clients.remove(websocket)
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do sistema"""
        process = psutil.Process(os.getpid())
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "used": psutil.virtual_memory().used // (1024 * 1024),  # MB
                "total": psutil.virtual_memory().total // (1024 * 1024)  # MB
            },
            "process": {
                "cpu": process.cpu_percent(),
                "memory": process.memory_info().rss // (1024 * 1024),  # MB
                "threads": process.num_threads()
            },
            "disk": {
                "percent": psutil.disk_usage('/').percent,
                "free": psutil.disk_usage('/').free // (1024 * 1024 * 1024)  # GB
            }
        }
    
    async def get_modules_status(self) -> Dict[str, str]:
        """Obtém status dos módulos"""
        # Aqui você integraria com os módulos reais
        return {
            "core": "active",
            "browser_controller": "active",
            "memory_manager": "active",
            "consensus_engine": "active",
            "task_analyzer": "active",
            "scheduler": "active"
        }
    
    async def get_providers_status(self) -> Dict[str, Dict]:
        """Obtém status dos providers de IA"""
        # Aqui você integraria com os providers reais
        return {
            "claude": {"status": "healthy", "requests_today": 127},
            "gpt4": {"status": "healthy", "requests_today": 89},
            "gemini": {"status": "inactive", "requests_today": 0},
            "perplexity": {"status": "healthy", "requests_today": 34}
        }
    
    async def get_recent_logs(self, lines: int = 50) -> List[str]:
        """Obtém logs recentes"""
        log_file = Path("logs/prometheus.log")
        if not log_file.exists():
            return []
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    
    async def get_jobs_status(self) -> List[Dict]:
        """Obtém status dos jobs agendados"""
        # Aqui você integraria com o scheduler
        return [
            {
                "id": "backup_daily",
                "name": "Daily Backup",
                "next_run": "2024-01-01T03:00:00",
                "last_run": "2023-12-31T03:00:00",
                "status": "success"
            },
            {
                "id": "health_check",
                "name": "Health Check",
                "next_run": "2024-01-01T10:30:00",
                "last_run": "2024-01-01T10:00:00",
                "status": "success"
            }
        ]
    
    async def get_realtime_data(self) -> Dict[str, Any]:
        """Obtém dados em tempo real para WebSocket"""
        metrics = await self.get_system_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": metrics["cpu_percent"],
            "memory": metrics["memory"]["percent"],
            "active_tasks": 3,  # Aqui você pegaria do core
            "queue_size": self.command_queue.qsize(),
            "websocket_clients": len(self.websocket_clients)
        }
    
    def get_dashboard_html(self) -> str:
        """Retorna HTML do dashboard"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prometheus Control Center</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #00ff41;
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41; }
            to { text-shadow: 0 0 20px #00ff41, 0 0 30px #00ff41; }
        }
        
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #888;
            font-size: 1.2em;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(0, 255, 65, 0.1);
            border: 1px solid #00ff41;
            border-radius: 10px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 255, 65, 0.3);
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, #00ff41, transparent);
            border-radius: 10px;
            opacity: 0;
            z-index: -1;
            transition: opacity 0.3s ease;
        }
        
        .stat-card:hover::before {
            opacity: 1;
        }
        
        .stat-title {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .stat-unit {
            font-size: 0.6em;
            opacity: 0.6;
            margin-left: 5px;
        }
        
        .progress-bar {
            width: 100%;
            height: 5px;
            background: rgba(0, 255, 65, 0.2);
            border-radius: 5px;
            margin-top: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: #00ff41;
            border-radius: 5px;
            transition: width 0.3s ease;
        }
        
        .modules-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .module-card {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .module-card.active {
            border-color: #00ff41;
            background: rgba(0, 255, 65, 0.05);
        }
        
        .module-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .module-name {
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .module-status {
            font-size: 0.8em;
            opacity: 0.7;
        }
        
        .console {
            background: #000;
            border: 1px solid #00ff41;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            font-family: 'Courier New', monospace;
        }
        
        .console-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            border-bottom: 1px solid #00ff41;
            padding-bottom: 10px;
        }
        
        .console-title {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .console-controls {
            display: flex;
            gap: 10px;
        }
        
        .console-btn {
            background: transparent;
            border: 1px solid #00ff41;
            color: #00ff41;
            padding: 5px 15px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .console-btn:hover {
            background: #00ff41;
            color: #000;
        }
        
        .console-output {
            height: 200px;
            overflow-y: auto;
            font-size: 0.9em;
            line-height: 1.4;
        }
        
        .log-line {
            margin-bottom: 5px;
            padding: 2px 5px;
            border-radius: 3px;
            transition: background 0.3s ease;
        }
        
        .log-line:hover {
            background: rgba(0, 255, 65, 0.1);
        }
        
        .log-info { color: #00ff41; }
        .log-warning { color: #ffff00; }
        .log-error { color: #ff4444; }
        .log-debug { color: #888; }
        
        .command-input {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .command-field {
            flex: 1;
            background: transparent;
            border: 1px solid #00ff41;
            color: #00ff41;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
        }
        
        .command-field:focus {
            outline: none;
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
        }
        
        .command-btn {
            background: #00ff41;
            color: #000;
            border: none;
            padding: 10px 30px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .command-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(0, 255, 65, 0.8);
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .status-online { background: #00ff41; }
        .status-warning { background: #ffff00; }
        .status-offline { background: #ff4444; }
        
        .footer {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            border-top: 1px solid #333;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔥 PROMETHEUS CONTROL CENTER</h1>
        <div class="subtitle">AI-Powered Automation System v3.0</div>
    </div>
    
    <div class="container">
        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">CPU Usage</div>
                <div class="stat-value">
                    <span id="cpu-value">0</span>
                    <span class="stat-unit">%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpu-progress"></div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Memory</div>
                <div class="stat-value">
                    <span id="memory-value">0</span>
                    <span class="stat-unit">%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memory-progress"></div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Active Tasks</div>
                <div class="stat-value">
                    <span id="tasks-value">0</span>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Queue Size</div>
                <div class="stat-value">
                    <span id="queue-value">0</span>
                </div>
            </div>
        </div>
        
        <!-- Modules Status -->
        <div class="modules-section">
            <div class="module-card active" id="module-core">
                <div class="module-icon">🧠</div>
                <div class="module-name">Core</div>
                <div class="module-status">
                    <span class="status-indicator status-online"></span>
                    Active
                </div>
            </div>
            
            <div class="module-card active" id="module-browser">
                <div class="module-icon">🌐</div>
                <div class="module-name">Browser</div>
                <div class="module-status">
                    <span class="status-indicator status-online"></span>
                    Active
                </div>
            </div>
            
            <div class="module-card active" id="module-memory">
                <div class="module-icon">💾</div>
                <div class="module-name">Memory</div>
                <div class="module-status">
                    <span class="status-indicator status-online"></span>
                    Active
                </div>
            </div>
            
            <div class="module-card active" id="module-consensus">
                <div class="module-icon">🤝</div>
                <div class="module-name">Consensus</div>
                <div class="module-status">
                    <span class="status-indicator status-online"></span>
                    Active
                </div>
            </div>
            
            <div class="module-card active" id="module-analyzer">
                <div class="module-icon">🔍</div>
                <div class="module-name">Analyzer</div>
                <div class="module-status">
                    <span class="status-indicator status-online"></span>
                    Active
                </div>
            </div>
            
            <div class="module-card active" id="module-scheduler">
                <div class="module-icon">⏰</div>
                <div class="module-name">Scheduler</div>
                <div class="module-status">
                    <span class="status-indicator status-online"></span>
                    Active
                </div>
            </div>
        </div>
        
        <!-- Console -->
        <div class="console">
            <div class="console-header">
                <div class="console-title">
                    <span class="status-indicator status-online"></span>
                    <span>System Console</span>
                </div>
                <div class="console-controls">
                    <button class="console-btn" onclick="clearConsole()">Clear</button>
                    <button class="console-btn" onclick="toggleAutoScroll()">Auto-scroll</button>
                </div>
            </div>
            <div class="console-output" id="console-output">
                <div class="log-line log-info">[INFO] System initialized successfully</div>
                <div class="log-line log-info">[INFO] Waiting for commands...</div>
            </div>
        </div>
        
        <!-- Command Input -->
        <div class="command-input">
            <input 
                type="text" 
                class="command-field" 
                id="command-input" 
                placeholder="Enter command... (e.g., 'create landing page for client X')"
                onkeypress="if(event.key === 'Enter') executeCommand()"
            >
            <button class="command-btn" onclick="executeCommand()">EXECUTE</button>
        </div>
    </div>
    
    <div class="footer">
        <p>Prometheus AI System © 2024 | Status: <span class="status-indicator status-online"></span> Online</p>
    </div>
    
    <script>
        let ws = null;
        let autoScroll = true;
        
        // WebSocket connection
        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:8000/ws');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected. Reconnecting...');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        // Update dashboard with real-time data
        function updateDashboard(data) {
            // Update CPU
            document.getElementById('cpu-value').textContent = data.cpu?.toFixed(1) || 0;
            document.getElementById('cpu-progress').style.width = (data.cpu || 0) + '%';
            
            // Update Memory
            document.getElementById('memory-value').textContent = data.memory?.toFixed(1) || 0;
            document.getElementById('memory-progress').style.width = (data.memory || 0) + '%';
            
            // Update Tasks
            document.getElementById('tasks-value').textContent = data.active_tasks || 0;
            
            // Update Queue
            document.getElementById('queue-value').textContent = data.queue_size || 0;
        }
        
        // Execute command
        async function executeCommand() {
            const input = document.getElementById('command-input');
            const command = input.value.trim();
            
            if (!command) return;
            
            // Add to console
            addLogLine(`[CMD] ${command}`, 'info');
            
            // Send to API
            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ command: command })
                });
                
                const result = await response.json();
                addLogLine(`[SUCCESS] Command queued: ${result.status}`, 'info');
            } catch (error) {
                addLogLine(`[ERROR] Failed to execute: ${error}`, 'error');
            }
            
            // Clear input
            input.value = '';
        }
        
        // Add log line to console
        function addLogLine(text, level = 'info') {
            const console = document.getElementById('console-output');
            const line = document.createElement('div');
            line.className = `log-line log-${level}`;
            line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
            console.appendChild(line);
            
            if (autoScroll) {
                console.scrollTop = console.scrollHeight;
            }
        }
        
        // Clear console
        function clearConsole() {
            document.getElementById('console-output').innerHTML = '';
            addLogLine('[INFO] Console cleared', 'info');
        }
        
        // Toggle auto-scroll
        function toggleAutoScroll() {
            autoScroll = !autoScroll;
            addLogLine(`[INFO] Auto-scroll ${autoScroll ? 'enabled' : 'disabled'}`, 'info');
        }
        
        // Fetch system status periodically
        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update module status
                for (const [module, status] of Object.entries(data.modules || {})) {
                    const card = document.getElementById(`module-${module}`);
                    if (card) {
                        const indicator = card.querySelector('.status-indicator');
                        if (indicator) {
                            indicator.className = `status-indicator status-${
                                status === 'active' ? 'online' : 
                                status === 'warning' ? 'warning' : 'offline'
                            }`;
                        }
                    }
                }
            } catch (error) {
                console.error('Failed to fetch status:', error);
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            connectWebSocket();
            setInterval(fetchStatus, 5000);
            
            // Add initial log
            addLogLine('[INFO] Dashboard connected', 'info');
            addLogLine('[INFO] WebSocket connected', 'info');
        });
    </script>
</body>
</html>
"""

# ============================================================================
# DASHBOARD RUNNER
# ============================================================================

def run_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Executa o dashboard"""
    dashboard = DashboardAPI()
    uvicorn.run(dashboard.app, host=host, port=port)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Starting Prometheus Dashboard...")
    print("📊 Access at: http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    run_dashboard()
