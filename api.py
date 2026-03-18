from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from playwright.sync_api import sync_playwright
import time
import random
import json
import os

app = FastAPI(title="GEX Elite API")

# Permite que o Streamlit acesse essa API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

USER_DATA_PATH = "/tmp/user_data" # Ou caminho local se rodar no Windows

@app.get("/")
def read_root():
    return {"status": "GEX API Online ⚡"}

@app.get("/api/cboe/{symbol}")
def get_cboe_data(symbol: str):
    symbol = symbol.upper()
    if symbol not in ["SPX", "NDX", "RUT"]:
        raise HTTPException(status_code=400, detail="Ativo inválido")

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                USER_DATA_PATH,
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-dev-shm-usage'],
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.pages[0] if context.pages else context.new_page()
            
            url_json = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"
            page.goto(url_json, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(2, 4))
            
            content = page.inner_text("body")
            
            if "options" in content and "data" in content:
                data = json.loads(content)
                context.close()
                return data
            else:
                context.close()
                raise HTTPException(status_code=403, detail="Bloqueado pela CBOE")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
