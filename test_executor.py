#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste do Executor API"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TESTE 1: Listar ações disponíveis")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/executor/actions")
print(f"Status: {response.status_code}")
actions = response.json()
print(json.dumps(actions, indent=2, ensure_ascii=False))

print("\n" + "=" * 70)
print("TESTE 2: Executar ação imediata - get_system_info")
print("=" * 70)

response = requests.post(
    f"{BASE_URL}/api/executor/execute",
    json={"action": "get_system_info", "params": {}}
)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Success: {result['success']}")
print(f"Duration: {result.get('duration_ms')}ms")
if result['success']:
    print(f"Platform: {result['data']['platform']}")
    print(f"CPU: {result['data']['cpu_percent']}%")
    print(f"Memory: {result['data']['memory']['percent']}%")

print("\n" + "=" * 70)
print("TESTE 3: Criar tarefa - list_files")
print("=" * 70)

response = requests.post(
    f"{BASE_URL}/api/executor/task/create",
    json={
        "action": "list_files",
        "params": {"path": "C:/Users/lucas/Downloads", "max_files": 10},
        "description": "Listar últimos 10 arquivos em Downloads",
        "critical": False
    }
)
print(f"Status: {response.status_code}")
task_data = response.json()
task_id = task_data['task_id']
print(f"Task ID: {task_id}")
print(f"Task Status: {task_data['task']['status']}")

print("\n" + "=" * 70)
print("TESTE 4: Executar tarefa criada")
print("=" * 70)

response = requests.post(f"{BASE_URL}/api/executor/task/{task_id}/execute")
print(f"Status: {response.status_code}")
exec_result = response.json()
print(f"Success: {exec_result['success']}")
print(f"Final Status: {exec_result['task']['status']}")
if exec_result['success']:
    print(f"Files found: {exec_result['task']['result']['total_files']}")

print("\n" + "=" * 70)
print("TESTE 5: Listar todas as tarefas")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/executor/tasks")
print(f"Status: {response.status_code}")
tasks = response.json()
print(f"Total tasks: {tasks['total']}")

print("\n" + "=" * 70)
print("TESTE 6: Stats do Executor")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/executor/stats")
print(f"Status: {response.status_code}")
stats = response.json()
print(json.dumps(stats['task_stats'], indent=2))

print("\n" + "=" * 70)
print("✅ TODOS OS TESTES CONCLUÍDOS!")
print("=" * 70)
