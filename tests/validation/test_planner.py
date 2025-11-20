#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste do Planner API"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TESTE PLANNER - SPRINT 2")
print("=" * 70)

print("\n" + "=" * 70)
print("TESTE 1: Criar Plano - 'organize meus downloads'")
print("=" * 70)

response = requests.post(
    f"{BASE_URL}/api/planner/create-plan",
    json={
        "user_request": "Quero organizar meus downloads em pastas por tipo de arquivo",
        "max_knowledge_results": 3
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    plan = result['plan']

    print(f"\nPlan ID: {plan['plan_id']}")
    print(f"Conhecimento usado: {plan['knowledge_used']['count']} chunks")
    if plan['knowledge_used']['count'] > 0:
        print(f"Top similarity: {plan['knowledge_used']['top_similarity']:.0%}")

    print(f"\nPlano gerado:")
    print(f"  Summary: {plan['plan'].get('summary', 'N/A')}")
    print(f"  Steps: {len(plan['plan'].get('steps', []))}")
    print(f"  Complexity: {plan['plan'].get('complexity', 'N/A')}")
    print(f"  Duration: {plan['plan'].get('estimated_duration', 'N/A')}")

    if plan['plan'].get('steps'):
        print(f"\n  Detalhes dos steps:")
        for step in plan['plan']['steps']:
            print(f"    {step['order']}. {step['description']}")
            print(f"       Action: {step.get('action', 'N/A')}")

    plan_id = plan['plan_id']
else:
    print(f"ERRO: {response.text}")
    plan_id = None

print("\n" + "=" * 70)
print("TESTE 2: Historico de Planejamentos")
print("=" * 70)

response = requests.get(f"{BASE_URL}/api/planner/history?limit=5")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    history = response.json()
    print(f"Total de planos no historico: {history['total']}")

    for i, plan in enumerate(history['history'][:3], 1):
        print(f"\n  {i}. {plan['plan_id']}")
        print(f"     Request: {plan['user_request'][:60]}...")
        print(f"     Knowledge: {plan['knowledge_used']['count']} chunks")

if plan_id:
    print("\n" + "=" * 70)
    print("TESTE 3: Converter Plano em Tarefas")
    print("=" * 70)

    response = requests.post(
        f"{BASE_URL}/api/planner/plan-to-tasks",
        json={"plan_id": plan_id}
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nTarefas criadas: {result['tasks_created']}")

        for task in result['tasks']:
            print(f"\n  Task ID: {task['task_id']}")
            print(f"  Action: {task['action']}")
            print(f"  Description: {task['description']}")

print("\n" + "=" * 70)
print("TESTE COMPLETO!")
print("=" * 70)
