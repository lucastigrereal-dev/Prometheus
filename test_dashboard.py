#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste do Dashboard API"""

import requests
import json

# Test stats
print("=" * 70)
print("TESTANDO API STATS")
print("=" * 70)

response = requests.get("http://localhost:8000/api/stats")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

print("\n" + "=" * 70)
print("TESTANDO BUSCA SEMÂNTICA")
print("=" * 70)

# Test search
response = requests.post(
    "http://localhost:8000/api/search",
    json={"query": "como implementar autenticacao", "limit": 2}
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Resultados encontrados: {data['count']}")

if data['results']:
    for i, result in enumerate(data['results'], 1):
        print(f"\n--- Resultado {i} ---")
        print(f"Similaridade: {result['similarity']:.2%}")
        print(f"Fonte: {result['source_type']}")
        print(f"Conteúdo: {result['content'][:200]}...")

print("\n" + "=" * 70)
print("✅ TESTES COMPLETOS!")
print("=" * 70)
print("\nDashboard disponível em: http://localhost:3001")
print("API disponível em: http://localhost:8000")
