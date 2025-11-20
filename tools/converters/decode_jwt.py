# -*- coding: utf-8 -*-
"""Quick JWT decoder to verify Supabase credentials"""

import os
import sys
import io
import json
import base64
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def decode_jwt(jwt_token):
    """Decode JWT and return payload"""
    try:
        parts = jwt_token.split('.')
        payload = base64.urlsafe_b64decode(parts[1] + '==')
        return json.loads(payload)
    except Exception as e:
        return f"Error: {e}"

print("=" * 70)
print("JWT DECODER")
print("=" * 70)

anon_key = os.getenv('SUPABASE_ANON_KEY')
service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
url = os.getenv('SUPABASE_URL')

print(f"\n📍 URL: {url}")
print(f"   Project ID from URL: {url.split('//')[1].split('.')[0] if url else 'N/A'}")

print(f"\n🔑 ANON_KEY Payload:")
if anon_key:
    payload = decode_jwt(anon_key)
    print(json.dumps(payload, indent=2))
else:
    print("   ❌ Not found in .env")

print(f"\n🔑 SERVICE_ROLE_KEY Payload:")
if service_key:
    payload = decode_jwt(service_key)
    print(json.dumps(payload, indent=2))
else:
    print("   ❌ Not found in .env")

print("\n" + "=" * 70)
print("✅ Compare 'ref' in JWT with Project ID in URL")
print("=" * 70)
