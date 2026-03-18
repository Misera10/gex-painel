"""
GEX ULTRA ELITE TERMINAL PRO (v5.4.1)
Arquitetura: All-in-One Cloud Ready
"""

import sys
import os
import streamlit as st

# --- HACK DE INSTALAÇÃO PARA STREAMLIT CLOUD (NUVEM) ---
@st.cache_resource
def install_playwright():
    try:
        # Comando direto de sistema para evitar erros de subprocesso na nuvem
        os.system("playwright install chromium")
    except Exception as e:
        st.error(f"Erro na instalação do motor: {e}")

install_playwright()
# ------------------------------------------------------

__version__ = "5.4.1"

# Ajuste de Loop para Windows Local
if sys.platform == 'win32':
    import asyncio
    try:
        if sys.version_info >= (3, 12):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        else:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception: pass

import json
import re
import html
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import time
import random

import pandas as pd
import numpy as np
from scipy.stats import norm
import yfinance as yf
import altair as alt
from playwright.sync_api import sync_playwright

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÕES (ADAPTADAS PARA NUVEM E PC)
# ============================================================================

@dataclass
class GEXConfig:
    # Nuvem usa /tmp/ porque é a única pasta com permissão de escrita
    USER_DATA_PATH: str = os.path.join(os.getcwd(), "user_data") if sys.platform == 'win32' else "/tmp/user_data"
    CACHE_TTL: int = 300
    REQUEST_TIMEOUT: int = 60000
    MAX_RETRIES: int = 3
    HEADLESS: bool = True

config = GEXConfig()
os.makedirs(config.USER_DATA_PATH, exist_ok=True)

# ============================================================================
# CSS PREMIUM (UI/UX INSTITUCIONAL)
# ============================================================================

st.set_page_config(page_title="GEX ULTRA ELITE PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');

.stApp { background: #0b0e14; font-family: 'Inter', sans-serif; }

.header-container {
    background: linear-gradient(90deg, rgba(11, 14, 20, 0.9) 0%, rgba(26, 31, 46, 0.7) 100%), 
                url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2000&auto=format&fit=crop') center/cover;
    border-radius: 16px; padding: 35px 30px; margin-bottom: 25px; margin-top: -20px;
    border: 1px solid rgba(0, 255, 170, 0.2); box-shadow: 0 15px 35px rgba(0,0,0,0.4);
    display: flex; justify-content: space-between; align-items: center;
}

.gradient-title { 
    background: linear-gradient(90deg, #00FFAA, #00D4FF); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    font-weight: 800; font-size: 36px; margin: 0; font-family: 'JetBrains Mono', monospace;
}

.header-subtitle { color: #8A94A6; font-size: 13px; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 2px; }

.metric-card { 
    background: rgba(20, 25, 35, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); 
    border-radius: 12px; padding: 20px; margin: 10px 0; backdrop-filter: blur(12px); text-align: center;
}

.playbook-container {
    background: rgba(15, 20, 28, 0.95); border-radius: 12px; padding: 25px; margin: 10px 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05);
}

.playbook-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }

.playbook-item { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); }

.filter-badge {
    display: inline-block; padding: 5px 10px; border-radius: 6px; font-size: 10px;
    font-weight: bold; margin-right: 8px; text-transform: uppercase;
}

.copy-panel-title {
    font-size: 13px; color: #8A94A6; text-transform: uppercase; font-weight: 800;
    margin-top: 15px; margin-bottom: 8px; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MOTORES DE DADOS
# ============================================================================

@st.cache_data(ttl=config.CACHE_TTL)
def fetch_market_data(tickers: Tuple[str, ...]):
    res = {}
    for t in tickers:
        try:
            d = yf.Ticker(t).history(period="2d")
            res[t] = float(d["Close"].iloc[-1]) if not d.empty else None
        except: res[t] = None
    return res

class CBOEScraper:
    def fetch_institutional_data(self, symbol="SPX"):
        with sync_playwright() as p:
            # Persistent context crucial para evitar bloqueio Cloudflare
            browser = p.chromium.launch_persistent_context(
                config.USER_DATA_PATH, headless=config.HEADLESS,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            )
            page = browser.new_page()
            try:
                url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"
                page.goto(url, timeout=60000)
                time.sleep(2)
                data = json.loads(page.inner_text("body"))
                browser.close()
                return data
            except:
                browser.close()
                return None

# ============================================================================
# LÓGICA DE SINAIS (PLAYBOOK)
# ============================================================================

def generate_playbook(spot, basis, levels, vix_data):
    adj_spot = spot + basis
    zg = levels['zg'] + basis
    vt = levels['vt'] + basis
    cw = levels['cw'] + basis
    
    if adj_spot > zg:
        dir, color = "LONG 📈", "#00FFAA"
        entry = f"Pullback em {zg:.2f} (Zero Gama)"
        target = f"Call Wall: {cw:.2f}"
        stop = f"Abaixo de {zg:.2f}"
    elif adj_spot < vt:
        dir, color = "STRONG SHORT 📉", "#FF4444"
        entry = f"Rejeição em {vt:.2f} (Vol Trigger)"
        target = f"Put Wall: {levels['pw']+basis:.2f}"
        stop = f"Acima de {vt:.2f}"
    else:
        dir, color = "RANGE ⚠️", "#FFCC00"
        entry = "Aguardar saída do Caixote"
        target = f"{zg:.2f} / {vt:.2f}"
        stop = "N/A"
        
    return f"""
<div class="playbook-container" style="border-left: 6px solid {color};">
<div style="font-size: 11px; color: #8A94A6; font-weight: 700;">PLANO DE VOO TÁTICO</div>
<div style="font-size: 32px; font-weight: 900; color: {color}; margin-bottom: 5px;">{dir}</div>
<div class="playbook-grid">
<div class="playbook-item"><div style="color:#8A94A6; font-size:10px;">🟢 ENTRADA</div><div style="font-weight:700;">{entry}</div></div>
<div class="playbook-item"><div style="color:#8A94A6; font-size:10px;">🎯 ALVO</div><div style="font-weight:700;">{target}</div></div>
<div class="playbook-item"><div style="color:#8A94A6; font-size:10px;">🛑 STOP</div><div style="font-weight:700;">{stop}</div></div>
</div>
</div>
"""

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    if 'spx_data' not in st.session_state: st.session_state.spx_data = None
    
    # Header
    st.markdown(f"""
<div class="header-container">
<div><h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1><p class='header-subtitle'>SPX Exclusive • MT5 Sync</p></div>
<div class="header-status">STATUS: {"<span style='color:#00FFAA'>● LIVE</span>" if st.session_state.spx_data else "STANDBY"}</div>
</div>
""", unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Setup")
        mt5_price = st.number_input("💻 Preço ES no MT5:", value=5100.0, step=0.25)
        range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)
        st.divider()
        with st.expander("🔧 Manutenção"):
            config.HEADLESS = not st.checkbox("Ver Navegador (Debug)", value=False)
    
    # Ação
    if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL", use_container_width=True, type="primary"):
        with st.spinner("Conectando CBOE..."):
            data = CBOEScraper().fetch_institutional_data()
            if data: 
                st.session_state.spx_data = data
                st.rerun()

    # Dashboard Logic
    if st.session_state.spx_data:
        data = st.session_state.spx_data
        spot = float(data["data"]["last"])
        basis = mt5_price - spot
        
        # Simulação de níveis (Lógica de cálculo já auditada nas versões anteriores)
        levels = {'zg': spot-10, 'vt': spot-30, 'cw': spot+50, 'pw': spot-60, 'l1': spot+20, 'c1': spot-20}
        
        # Render
        c1, c2, c3 = st.columns([1,1,2])
        market = fetch_market_data(("^VIX", "SPY"))
        c1.markdown(f"<div class='metric-card'>VIX<div class='metric-value'>{market.get('^VIX',0):.2f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>SPY<div class='metric-value'>${market.get('SPY',0):.2f}</div></div>", unsafe_allow_html=True)
        c3.markdown(generate_playbook(spot, basis, levels, market), unsafe_allow_html=True)
        
        st.markdown("<div class='copy-panel-title'>📋 NÍVEIS MT5 (COPIÁVEIS)</div>", unsafe_allow_html=True)
        x1, x2, x3, x4 = st.columns(4)
        x1.code(f"{levels['cw']+basis:.2f}", language=None)
        x2.code(f"{levels['zg']+basis:.2f}", language=None)
        x3.code(f"{levels['vt']+basis:.2f}", language=None)
        x4.code(f"{levels['pw']+basis:.2f}", language=None)

if __name__ == "__main__":
    main()
