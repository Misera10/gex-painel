# 1. Teste conectividade básica
ping cboe.com

# 2. Teste API diretamente com curl
curl -H "User-Agent: Mozilla/5.0" https://cdn.cboe.com/api/global/delayed_quotes/options/SPX.json

# 3. Teste com Python
python test_cboe.py

# 4. Se tudo falhar, use VPN
#    - NordVPN, ExpressVPN, ou ProtonVPN gratuito
#    - Conecte em servidor EUA
#    - Execute novamente
