#!/usr/bin/env python
"""
PROMETHEUS SUPREME - WEB INTERFACE
Interface web moderna com FastAPI e WebSockets
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import json
import uvicorn
import sys
from pathlib import Path
from datetime import datetime
from typing import List

sys.path.insert(0, str(Path.cwd()))

app = FastAPI(title="Prometheus Supreme Web Interface")

# HTML da interface - embedded
def get_html_content():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prometheus Supreme - Web Interface</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #00ff41;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: rgba(0, 0, 0, 0.7);
            padding: 20px;
            text-align: center;
            border-bottom: 3px solid #00bfff;
            box-shadow: 0 5px 20px rgba(0, 191, 255, 0.3);
        }

        h1 {
            font-size: 2.5em;
            text-shadow: 0 0 30px #00ff41;
            margin-bottom: 10px;
            animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
            from { text-shadow: 0 0 20px #00ff41; }
            to { text-shadow: 0 0 30px #00ff41, 0 0 40px #00bfff; }
        }

        .status {
            color: #00bfff;
            font-size: 1.2em;
            padding: 5px 15px;
            background: rgba(0, 191, 255, 0.1);
            border-radius: 20px;
            display: inline-block;
        }

        .container {
            flex: 1;
            display: flex;
            gap: 20px;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }

        .left-panel {
            flex: 2;
            display: flex;
            flex-direction: column;
            gap: 20px;
            min-width: 0;
        }

        .right-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 20px;
            min-width: 300px;
        }

        .panel {
            background: rgba(0, 0, 0, 0.5);
            border: 2px solid #00ff41;
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 5px 20px rgba(0, 255, 65, 0.2);
        }

        .panel-title {
            color: #00bfff;
            margin-bottom: 15px;
            font-size: 1.3em;
            font-weight: bold;
            text-transform: uppercase;
        }

        textarea {
            width: 100%;
            background: rgba(0, 0, 0, 0.7);
            color: #00ff41;
            border: 2px solid #00bfff;
            border-radius: 8px;
            padding: 12px;
            font-family: inherit;
            font-size: 1em;
            resize: vertical;
            transition: all 0.3s;
        }

        textarea:focus {
            outline: none;
            border-color: #00ff41;
            box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
        }

        button {
            background: linear-gradient(45deg, #00bfff, #0099cc);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            font-family: inherit;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            margin-right: 10px;
            transition: all 0.3s;
            text-transform: uppercase;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 191, 255, 0.5);
        }

        button:active { transform: translateY(0); }

        button:disabled {
            background: #444;
            cursor: not-allowed;
            transform: none;
        }

        .output {
            flex: 1;
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff41;
            border-radius: 8px;
            padding: 15px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 0.95em;
            max-height: 500px;
            min-height: 300px;
            line-height: 1.5;
        }

        .output-line { margin: 2px 0; padding: 2px 0; }
        .output-line.error { color: #ff0040; }
        .output-line.success { color: #00ff00; }
        .output-line.info { color: #00bfff; }

        .stats-grid { display: grid; gap: 10px; }

        .stats-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            border-left: 3px solid #00bfff;
        }

        .stats-value { color: #00ff41; font-weight: bold; }

        .component {
            padding: 8px;
            margin: 5px 0;
            background: rgba(0, 0, 0, 0.4);
            border-radius: 5px;
            transition: all 0.3s;
        }

        .component.active { border-left: 4px solid #00ff41; }
        .component.inactive { border-left: 4px solid #666; opacity: 0.6; }

        .quick-action {
            display: block;
            width: 100%;
            margin: 8px 0;
            background: rgba(0, 191, 255, 0.1);
            border: 2px solid #00bfff;
            padding: 10px;
            transition: all 0.3s;
        }

        .quick-action:hover {
            background: rgba(0, 191, 255, 0.2);
            border-color: #00ff41;
        }

        .footer {
            background: rgba(0, 0, 0, 0.7);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 2px solid #00bfff;
        }

        .footer-status { color: #00bfff; }
        .time { color: #00ff41; font-weight: bold; }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .processing { animation: pulse 1s infinite; }

        .connection-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-left: 10px;
            background: #00ff41;
            box-shadow: 0 0 10px #00ff41;
        }

        .connection-indicator.offline {
            background: #ff0040;
            box-shadow: 0 0 10px #ff0040;
        }

        @media (max-width: 768px) {
            .container { flex-direction: column; }
            .right-panel { min-width: 0; }
            h1 { font-size: 1.8em; }
        }

        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.3); border-radius: 5px; }
        ::-webkit-scrollbar-thumb { background: #00bfff; border-radius: 5px; }
        ::-webkit-scrollbar-thumb:hover { background: #00ff41; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PROMETHEUS SUPREME</h1>
        <div class="status">
            STATUS: <span id="status">CONECTANDO...</span>
            <span class="connection-indicator" id="indicator"></span>
        </div>
    </div>

    <div class="container">
        <div class="left-panel">
            <div class="panel">
                <div class="panel-title">Comando</div>
                <textarea id="command" rows="4" placeholder="Digite seu comando aqui..."></textarea>
                <div style="margin-top: 15px;">
                    <button id="executeBtn" onclick="executeCommand()">Executar</button>
                    <button onclick="clearAll()">Limpar</button>
                    <button onclick="showExamples()">Exemplos</button>
                </div>
            </div>

            <div class="panel" style="flex: 1;">
                <div class="panel-title">Output</div>
                <div id="output" class="output"></div>
            </div>
        </div>

        <div class="right-panel">
            <div class="panel">
                <div class="panel-title">Estatisticas</div>
                <div class="stats-grid">
                    <div class="stats-item">
                        <span>Tasks Executadas:</span>
                        <span class="stats-value" id="tasks">0</span>
                    </div>
                    <div class="stats-item">
                        <span>Taxa de Sucesso:</span>
                        <span class="stats-value" id="success">100%</span>
                    </div>
                    <div class="stats-item">
                        <span>Aprendizados:</span>
                        <span class="stats-value" id="learnings">0</span>
                    </div>
                    <div class="stats-item">
                        <span>Tempo Total:</span>
                        <span class="stats-value" id="totalTime">0s</span>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title">Componentes</div>
                <div id="components">
                    <div class="component active">
                        <span style="color: #00ff41;">[+]</span> Vision (OCR)
                    </div>
                    <div class="component active">
                        <span style="color: #00ff41;">[+]</span> Supervisor
                    </div>
                    <div class="component active">
                        <span style="color: #00ff41;">[+]</span> Learning
                    </div>
                    <div class="component active">
                        <span style="color: #00ff41;">[+]</span> File Integrity
                    </div>
                    <div class="component inactive">
                        <span style="color: #666;">[-]</span> Brain (Opcional)
                    </div>
                    <div class="component inactive">
                        <span style="color: #666;">[-]</span> Multi-IA (Opcional)
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title">Acoes Rapidas</div>
                <button class="quick-action" onclick="healthCheck()">Health Check</button>
                <button class="quick-action" onclick="showSkills()">Ver Skills</button>
                <button class="quick-action" onclick="showStatus()">Ver Status</button>
                <button class="quick-action" onclick="searchKnowledge()">Buscar Knowledge</button>
            </div>
        </div>
    </div>

    <div class="footer">
        <span class="footer-status" id="footer-status">Pronto para comandos...</span>
        <span class="time" id="time"></span>
    </div>

    <script>
        let ws = null;
        let reconnectInterval = null;

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = protocol + '//' + window.location.hostname + ':8100/ws';

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                document.getElementById("status").textContent = "ONLINE";
                document.getElementById("indicator").classList.remove("offline");
                addOutput("[SISTEMA] Conectado ao Prometheus Supreme!", "success");

                if (reconnectInterval) {
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleResponse(data);
            };

            ws.onclose = function() {
                document.getElementById("status").textContent = "OFFLINE";
                document.getElementById("indicator").classList.add("offline");
                addOutput("[SISTEMA] Conexao perdida. Reconectando...", "error");

                if (!reconnectInterval) {
                    reconnectInterval = setInterval(function() {
                        if (ws.readyState === WebSocket.CLOSED) {
                            connectWebSocket();
                        }
                    }, 3000);
                }
            };

            ws.onerror = function(error) {
                addOutput("[ERRO] Erro na conexao WebSocket", "error");
            };
        }

        function executeCommand() {
            const command = document.getElementById("command").value.trim();
            if (!command) {
                alert("Digite um comando!");
                return;
            }

            if (!ws || ws.readyState !== WebSocket.OPEN) {
                addOutput("[ERRO] Sistema offline. Aguarde a reconexao...", "error");
                return;
            }

            document.getElementById("executeBtn").disabled = true;
            document.getElementById("executeBtn").textContent = "PROCESSANDO...";
            document.getElementById("executeBtn").classList.add("processing");

            addOutput("[COMANDO] " + command, "info");

            ws.send(JSON.stringify({
                action: "execute",
                command: command
            }));
        }

        function handleResponse(data) {
            if (data.type === "result") {
                document.getElementById("executeBtn").disabled = false;
                document.getElementById("executeBtn").textContent = "EXECUTAR";
                document.getElementById("executeBtn").classList.remove("processing");

                if (data.success) {
                    addOutput("[SUCESSO] Comando executado!", "success");
                } else {
                    addOutput("[ERRO] " + (data.error || "Falha na execucao"), "error");
                }

                if (data.output) {
                    addOutput("[OUTPUT] " + data.output);
                }

                if (data.duration) {
                    addOutput("[TEMPO] " + data.duration.toFixed(2) + " segundos", "info");
                }

                updateStats(data.stats);

            } else if (data.type === "health") {
                addOutput("[HEALTH CHECK]", "info");
                addOutput(JSON.stringify(data.health, null, 2));

            } else if (data.type === "skills") {
                addOutput("[SKILLS APRENDIDAS]", "info");
                if (data.skills && data.skills.top_skills) {
                    data.skills.top_skills.forEach(function(skill) {
                        addOutput("  - " + skill.name + ": " + (skill.proficiency * 100).toFixed(1) + "%");
                    });
                }
            }
        }

        function addOutput(text, type) {
            type = type || "";
            const output = document.getElementById("output");
            const line = document.createElement("div");
            line.className = "output-line " + type;
            const timestamp = new Date().toLocaleTimeString();
            line.textContent = "[" + timestamp + "] " + text;
            output.appendChild(line);
            output.scrollTop = output.scrollHeight;
        }

        function clearAll() {
            document.getElementById("command").value = "";
            document.getElementById("output").innerHTML = "";
            addOutput("[SISTEMA] Interface limpa", "info");
        }

        function updateStats(stats) {
            if (stats) {
                document.getElementById("tasks").textContent = stats.tasks_executed || 0;
                document.getElementById("success").textContent = (stats.success_rate || 100).toFixed(1) + "%";
                document.getElementById("learnings").textContent = stats.learnings_acquired || 0;
                document.getElementById("totalTime").textContent = (stats.total_time_saved || 0).toFixed(1) + "s";
            }
        }

        function healthCheck() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: "health_check"}));
            }
        }

        function showSkills() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: "show_skills"}));
            }
        }

        function showStatus() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: "show_status"}));
            }
        }

        function searchKnowledge() {
            const query = prompt("Digite sua busca no Knowledge Base:");
            if (query) {
                document.getElementById("command").value = "Busque no knowledge base: " + query;
                executeCommand();
            }
        }

        function showExamples() {
            const examples = [
                "Crie um script Python para analise de dados",
                "Busque informacoes sobre machine learning",
                "Analise o codigo e sugira melhorias",
                "Crie uma API REST com FastAPI",
                "Automatize o processo de backup"
            ];

            addOutput("[EXEMPLOS DE COMANDOS]", "info");
            examples.forEach(function(ex, i) {
                addOutput("  " + (i+1) + ". " + ex);
            });
        }

        function updateTime() {
            const now = new Date();
            document.getElementById("time").textContent = now.toLocaleString('pt-BR');
        }

        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                executeCommand();
            }
            if (e.ctrlKey && e.key === 'l') {
                e.preventDefault();
                clearAll();
            }
        });

        connectWebSocket();
        setInterval(updateTime, 1000);
        updateTime();

        setTimeout(function() {
            addOutput("[INFO] Digite um comando ou use as acoes rapidas", "info");
        }, 1000);
    </script>
</body>
</html>
"""

# Armazenar instancia global do Prometheus
prometheus_instance = None
connected_clients: List[WebSocket] = []

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve a pagina principal"""
    return get_html_content()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para comunicacao em tempo real"""
    await websocket.accept()
    connected_clients.append(websocket)

    global prometheus_instance

    # Inicializar Prometheus se necessario
    if not prometheus_instance:
        try:
            from prometheus_supreme import PrometheusSupreme
            prometheus_instance = PrometheusSupreme()
            await websocket.send_json({
                "type": "system",
                "message": "Prometheus Supreme inicializado!"
            })
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Erro ao inicializar: {str(e)}"
            })

    try:
        while True:
            # Receber mensagem do cliente
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "execute":
                # Executar comando
                command = data.get("command", "")

                try:
                    result = await prometheus_instance.execute(command)

                    await websocket.send_json({
                        "type": "result",
                        "success": result.get("success", False),
                        "output": str(result.get("output", ""))[:1000],
                        "duration": result.get("duration", 0),
                        "stats": prometheus_instance.stats,
                        "errors": result.get("errors", [])
                    })

                except Exception as e:
                    await websocket.send_json({
                        "type": "result",
                        "success": False,
                        "error": str(e)
                    })

            elif action == "health_check":
                # Health check
                health = await prometheus_instance.get_health_status()
                await websocket.send_json({
                    "type": "health",
                    "health": health
                })

            elif action == "show_skills":
                # Mostrar skills
                skills = await prometheus_instance.get_skills_report()
                await websocket.send_json({
                    "type": "skills",
                    "skills": skills
                })

            elif action == "show_status":
                # Status do sistema
                await websocket.send_json({
                    "type": "result",
                    "output": "Status atualizado",
                    "stats": prometheus_instance.stats
                })

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)


if __name__ == "__main__":
    print("[*] Iniciando Prometheus Supreme Web Interface...")
    print("[*] Acesse em: http://localhost:8100")
    print("[*] Pressione Ctrl+C para parar")

    # Executar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8100,
        log_level="info",
        reload=False
    )
