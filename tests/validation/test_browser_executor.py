#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste do Browser Executor - Sprint 3"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TESTE BROWSER EXECUTOR - SPRINT 3")
print("=" * 70)

# ============================================================================
# TESTE 1: Listar ações disponíveis
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 1: Listar ações de browser disponíveis")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/browser/actions")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"\nAções disponíveis: {len(result['actions'])}")
    for action in result['actions']:
        print(f"  - {action}")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 2: Verificar status (deve estar não-inicializado)
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 2: Verificar status (antes de inicializar)")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/browser/status")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    status = response.json()
    print(f"\nBrowser inicializado: {status['initialized']}")
    print(f"Método: {status['browser_method']}")
    print(f"Execuções: {status['total_executions']}")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 3: Executar navegação simples (auto-init)
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 3: Navegar para Google (auto-init)")
print("=" * 70)

response = requests.post(
    f"{BASE_URL}/api/browser/execute",
    json={
        "action": "navigate",
        "params": {
            "url": "https://www.google.com"
        }
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    if result['success']:
        print(f"\n✅ Navegação bem-sucedida!")
        print(f"URL: {result['data']['url']}")
        print(f"Método usado: {result['data']['method']}")
    else:
        print(f"\n❌ Falha na navegação: {result.get('error')}")
else:
    print(f"ERRO: {response.text}")

# Aguardar um pouco para a página carregar
time.sleep(2)

# ============================================================================
# TESTE 4: Obter informações da página
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 4: Obter informações da página")
print("=" * 70)

response = requests.post(
    f"{BASE_URL}/api/browser/execute",
    json={
        "action": "get_page_info",
        "params": {}
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    if result['success']:
        print(f"\n✅ Informações obtidas!")
        page_info = result['data']
        print(f"Título: {page_info.get('title', 'N/A')}")
        print(f"URL: {page_info.get('url', 'N/A')}")
        print(f"Forms: {page_info.get('forms_count', 0)}")
        print(f"Inputs: {page_info.get('inputs_count', 0)}")
        print(f"Botões: {page_info.get('buttons_count', 0)}")
        print(f"Links: {page_info.get('links_count', 0)}")
    else:
        print(f"\n❌ Falha: {result.get('error')}")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 5: Tirar screenshot
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 5: Tirar screenshot da página")
print("=" * 70)

response = requests.post(
    f"{BASE_URL}/api/browser/execute",
    json={
        "action": "screenshot",
        "params": {
            "path": "data/executor/screenshots/test_google.png",
            "full_page": False
        }
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    if result['success']:
        print(f"\n✅ Screenshot salvo!")
        print(f"Caminho: {result['data']['path']}")
    else:
        print(f"\n❌ Falha: {result.get('error')}")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 6: Histórico de execuções
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 6: Histórico de execuções de browser")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/browser/history?limit=10")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    history = response.json()
    print(f"\nTotal de execuções: {history['total']}")

    for i, execution in enumerate(history['history'], 1):
        print(f"\n  {i}. {execution['action']}")
        print(f"     Sucesso: {execution['result'].get('success', False)}")
        print(f"     Duração: {execution['duration_ms']:.0f}ms")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 7: Fechar navegador
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 7: Fechar navegador")
print("=" * 70)

response = requests.post(f"{BASE_URL}/api/browser/close")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    if result['success']:
        print(f"\n✅ Navegador fechado!")
        print(f"Mensagem: {result['message']}")
    else:
        print(f"\n❌ Falha ao fechar")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 8: Planner com Browser Actions
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 8: Planner gerando plano com ações de browser")
print("=" * 70)

response = requests.post(
    f"{BASE_URL}/api/planner/create-plan",
    json={
        "user_request": "Quero fazer uma busca no Google por 'Prometheus AI' e capturar um screenshot dos resultados",
        "max_knowledge_results": 3
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    plan = result['plan']

    print(f"\n✅ Plano criado!")
    print(f"Plan ID: {plan['plan_id']}")
    print(f"Conhecimento usado: {plan['knowledge_used']['count']} chunks")

    print(f"\nPlano gerado:")
    print(f"  Summary: {plan['plan'].get('summary', 'N/A')}")
    print(f"  Steps: {len(plan['plan'].get('steps', []))}")
    print(f"  Complexity: {plan['plan'].get('complexity', 'N/A')}")

    if plan['plan'].get('steps'):
        print(f"\n  Detalhes dos steps:")
        for step in plan['plan']['steps']:
            print(f"    {step['order']}. {step['description']}")
            print(f"       Action: {step.get('action', 'N/A')}")
            print(f"       Params: {step.get('params', {})}")

            # Verificar se gerou ações de browser
            if step.get('action') in ['navigate', 'click_element', 'fill_input', 'screenshot']:
                print(f"       🌐 BROWSER ACTION DETECTADA!")
else:
    print(f"ERRO: {response.text}")

print("\n" + "=" * 70)
print("TESTES COMPLETOS!")
print("=" * 70)
