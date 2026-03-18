# test_api.py
import requests

print("🔍 Testando API CBOE...")
url = "https://cdn.cboe.com/api/global/delayed_quotes/options/SPX.json"
# O disfarce (User-Agent) é obrigatório para não tomar bloqueio (Erro 403)
headers = {"User-Agent": "Mozilla/5.0"} 

try:
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 200:
        data = r.json()
        price = data['data'].get('current_price', 'N/A')
        print(f"✅ Conexão OK | Preço Atual do SPX: {price}")
    else:
        print(f"❌ Falha. Status Code: {r.status_code}")
except Exception as e:
    print(f"❌ Erro de Conexão: {e}")
