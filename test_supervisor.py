#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste do Supervisor - Sprint 4"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TESTE SUPERVISOR - SPRINT 4")
print("=" * 70)

# ============================================================================
# TESTE 1: Revisar código Python com vulnerabilidade
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 1: Revisar código Python (com eval - vulnerabilidade)")
print("=" * 70)

bad_code = """
def calculate(expression):
    result = eval(expression)  # VULNERABILIDADE!
    return result

user_input = input("Digite uma expressão: ")
print(calculate(user_input))
"""

response = requests.post(
    f"{BASE_URL}/api/supervisor/review-code",
    json={
        "code": bad_code,
        "language": "python",
        "context": {
            "description": "Função de calculadora",
            "purpose": "Avaliar expressões matemáticas"
        }
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    review = result['review']

    print(f"\n=== RESULTADO DA REVISAO ===")
    print(f"Review ID: {review['review_id']}")
    print(f"Overall Score: {review['overall_score']}/100")
    print(f"Approved: {review['approved']}")
    print(f"Summary: {review['summary']}")

    if review['issues']:
        print(f"\n{len(review['issues'])} ISSUES ENCONTRADOS:")
        for issue in review['issues']:
            print(f"\n  [{issue['severity'].upper()}] {issue['type']}")
            print(f"  Mensagem: {issue['message']}")
            print(f"  Sugestao: {issue['suggestion']}")
    else:
        print("\nNenhum issue encontrado!")

    if review['suggestions']:
        print(f"\n{len(review['suggestions'])} SUGESTOES:")
        for sug in review['suggestions']:
            print(f"\n  [{sug['priority']}] {sug['message']}")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 2: Revisar código bom
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 2: Revisar código Python (limpo)")
print("=" * 70)

good_code = """
def calculate_sum(numbers):
    '''Calcula a soma de uma lista de números'''
    if not isinstance(numbers, list):
        raise ValueError("Input deve ser uma lista")

    total = sum(numbers)
    return total

# Uso
nums = [1, 2, 3, 4, 5]
result = calculate_sum(nums)
print(f"Soma: {result}")
"""

response = requests.post(
    f"{BASE_URL}/api/supervisor/review-code",
    json={
        "code": good_code,
        "language": "python"
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    review = result['review']

    print(f"\nOverall Score: {review['overall_score']}/100")
    print(f"Approved: {review['approved']}")
    print(f"Issues: {len(review['issues'])}")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 3: Estatísticas de revisões
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 3: Estatísticas de revisões")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/supervisor/review-stats")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    stats = response.json()
    print(f"\nTotal de revisões: {stats['total_reviews']}")
    print(f"Aprovadas: {stats['approved']}")
    print(f"Rejeitadas: {stats['rejected']}")
    print(f"Score médio: {stats['avg_score']}")
    print(f"Issues críticos: {stats['critical_issues']}")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 4: Solicitar aprovação para tarefa crítica
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 4: Solicitar aprovação para tarefa crítica")
print("=" * 70)

response = requests.post(
    f"{BASE_URL}/api/supervisor/request-approval",
    json={
        "task_id": "task_critical_001",
        "task_description": "Deletar arquivos do diretório /tmp",
        "task_action": "delete_files",
        "task_params": {"path": "/tmp", "pattern": "*.log"},
        "reason": "Tarefa crítica que modifica arquivos do sistema",
        "timeout_minutes": 30
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"\nApproval ID: {result['approval_id']}")
    print(f"Status: {result['status']}")
    print(f"Mensagem: {result['message']}")
    print(f"Expira em: {result.get('expires_at', 'N/A')}")

    approval_id = result['approval_id']
else:
    print(f"ERRO: {response.text}")
    approval_id = None

# ============================================================================
# TESTE 5: Listar aprovações pendentes
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 5: Listar aprovações pendentes")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/supervisor/pending-approvals")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"\nAprovações pendentes: {result['total']}")

    if result['pending']:
        for approval in result['pending']:
            print(f"\n  Approval ID: {approval['approval_id']}")
            print(f"  Tarefa: {approval['task_description']}")
            print(f"  Ação: {approval['task_action']}")
            print(f"  Motivo: {approval['reason']}")
else:
    print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 6: Aprovar tarefa
# ============================================================================

if approval_id:
    print("\n" + "=" * 70)
    print("TESTE 6: Aprovar tarefa crítica")
    print("=" * 70)

    response = requests.post(
        f"{BASE_URL}/api/supervisor/approve",
        json={
            "approval_id": approval_id,
            "notes": "Aprovado após verificação manual"
        }
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nSucesso: {result['success']}")
        print(f"Mensagem: {result['message']}")
        print(f"Task ID: {result.get('task_id', 'N/A')}")
    else:
        print(f"ERRO: {response.text}")

# ============================================================================
# TESTE 7: Estatísticas de aprovações
# ============================================================================

print("\n" + "=" * 70)
print("TESTE 7: Estatísticas de aprovações")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/supervisor/approval-stats")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    stats = response.json()
    print(f"\nTotal de aprovações: {stats['total']}")
    print(f"Pendentes: {stats['pending']}")
    print(f"Aprovadas: {stats['approved']}")
    print(f"Rejeitadas: {stats['rejected']}")
    print(f"Expiradas: {stats['expired']}")
    print(f"Taxa de aprovação: {stats['approval_rate']:.1f}%")
    print(f"Tempo médio de aprovação: {stats['avg_approval_time_minutes']:.2f} minutos")
else:
    print(f"ERRO: {response.text}")

print("\n" + "=" * 70)
print("TESTES COMPLETOS!")
print("=" * 70)
