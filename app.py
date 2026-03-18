"""
GEX ULTRA ELITE TERMINAL PRO (Internal v5.3)
Features: Nuvem Ready | Dashboard Completa | MT5 Sync | Níveis 0DTE/L1/C1/C4 | Playbook
"""

import sys
import os
import streamlit as st

# --- HACK PARA RODAR NA NUVEM (STREAMLIT CLOUD) ---
@st.cache_resource
def install_playwright():
    os.system("python -m playwright install chromium")
    os.system("python -m playwright install-deps chromium")

install_playwright()
# --------------------------------------------------

__version__ = "5.3.0"

if sys.platform == 'win32':
    import asyncio
    try:
        if sys.version_info >= (3, 12):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        else:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass
    os.environ['PYTHONASYNCIODEBUG'] = '0'

import json
import re
import html
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import time
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import pandas as pd
import numpy as np
from scipy.stats import norm
import yfinance as yf
import altair as alt
from playwright.sync_api import sync_playwright

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

@dataclass
class GEXConfig:
    USER_DATA_PATH: str = os.path.join(os.getcwd(), "user_data")
    CACHE_TTL: int = 300
    REQUEST_TIMEOUT: int = 60000
    MAX_RETRIES: int = 3
    HEADLESS: bool = True
    DELAY_BETWEEN_REQUESTS: int = 5
    TIMEZONE: str = 'America/New_York'

config = GEXConfig()
os.makedirs(config.USER_DATA_PATH, exist_ok=True)

# ============================================================================
# CSS PREMIUM + DESIGN IMAGÉTICO
# ============================================================================

st.set_page_config(
    page_title="GEX ULTRA ELITE PRO", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');

.stApp { 
    background: linear-gradient(135deg, #0b0e14 0%, #131824 100%); 
    font-family: 'Inter', sans-serif;
}

.header-container {
    background: linear-gradient(90deg, rgba(11, 14, 20, 0.9) 0%, rgba(26, 31, 46, 0.7) 100%), 
                url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2000&auto=format&fit=crop') center/cover;
    border-radius: 16px;
    padding: 35px 30px;
    margin-bottom: 25px;
    margin-top: -20px;
    border: 1px solid rgba(0, 255, 170, 0.2);
    box-shadow: 0 15px 35px rgba(0,0,0,0.4);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.gradient-title { 
    background: linear-gradient(90deg, #00FFAA, #00D4FF); 
    -webkit-background-clip: text; 
    -webkit-text-fill-color: transparent; 
    font-weight: 800; 
    font-size: 36px; 
    margin: 0; 
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -1px;
}

.header-subtitle {
    color: #8A94A6;
    margin-top: 8px;
    margin-bottom: 0;
    font-size: 13px;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.header-status {
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #8A94A6;
    background: rgba(0,0,0,0.4);
    padding: 10px 15px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.05);
    backdrop-filter: blur(5px);
}

.metric-card { 
    background: rgba(20, 25, 35, 0.7); 
    border: 1px solid rgba(255, 255, 255, 0.05); 
    border-radius: 12px; 
    padding: 20px; 
    margin: 10px 0; 
    backdrop-filter: blur(12px); 
    text-align: center;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.metric-card:hover {
    transform: translateY(-3px);
    border-color: rgba(0, 255, 170, 0.3);
    box-shadow: 0 8px 25px rgba(0, 255, 170, 0.1);
}

.metric-card.mt5-active {
    border: 1px solid #00D4FF;
    background: linear-gradient(180deg, rgba(0, 212, 255, 0.1) 0%, rgba(20, 25, 35, 0.8) 100%);
}

.metric-value { 
    color: #00FFAA !important; 
    font-size: 26px !important; 
    font-weight: 900 !important; 
    background: rgba(0,0,0,0.3) !important; 
    border: 1px solid rgba(255,255,255,0.05); 
    display: block; 
    padding: 10px; 
    border-radius: 8px; 
    font-family: 'JetBrains Mono', monospace;
    margin-top: 8px;
}

.metric-label { 
    color: #8A94A6; 
    font-weight: 700; 
    font-size: 12px; 
    text-transform: uppercase; 
    letter-spacing: 1px;
}

.playbook-container {
    background: rgba(15, 20, 28, 0.95);
    border-radius: 12px;
    padding: 25px;
    margin: 10px 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.05);
}
.playbook-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-top: 15px;
}
.playbook-item {
    background: rgba(0,0,0,0.3);
    padding: 15px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.03);
}
.playbook-item-title {
    font-size: 11px;
    color: #8A94A6;
    text-transform: uppercase;
    margin-bottom: 8px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.playbook-item-value {
    font-size: 14px;
    color: #E0E6ED;
    font-weight: 700;
    font-family: 'Inter', sans-serif;
}
.filter-badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: bold;
    margin-right: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.divergence-alert {
    background: rgba(255, 71, 87, 0.1);
    border: 1px solid rgba(255, 71, 87, 0.3);
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
}
.divergence-alert.high { background: rgba(255, 71, 87, 0.2); border-color: #ff4757; }
.divergence-alert.medium { background: rgba(255, 204, 0, 0.1); border-color: #ffa502; }

.offline-banner {
    background: rgba(255, 204, 0, 0.1);
    border: 1px solid #FFCC00;
    color: #FFCC00;
    padding: 12px;
    border-radius: 8px;
    text-align: center;
    font-weight: 600;
    margin-bottom: 15px;
    letter-spacing: 0.5px;
}

.copy-panel-title {
    font-size: 13px;
    color: #8A94A6;
    text-transform: uppercase;
    font-weight: 800;
    margin-top: 15px;
    margin-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    padding-bottom: 5px;
    letter-spacing: 1px;
}

div[data-testid="stCodeBlock"] {
    margin-bottom: -10px !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

def sanitize_html(text: str) -> str:
    if not isinstance(text, str): text = str(text)
    return html.escape(text)

@st.cache_data(ttl=config.CACHE_TTL)
def fetch_yf_data(tickers: Tuple[str, ...]) -> Dict[str, Optional[float]]:
    results = {}
    def fetch_single(ticker: str) -> Tuple[str, Optional[float]]:
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if not data.empty: return ticker, float(data["Close"].iloc[-1])
            return ticker, None
        except Exception: return ticker, None
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_single, t): t for t in tickers}
        for future in as_completed(futures):
            ticker, price = future.result()
            results[ticker] = price
    return results

def get_spy_analysis() -> Dict[str, Any]:
    try:
        spy = yf.Ticker("SPY")
        hist = spy.history(period="5d")
        if hist.empty: return {}
        current = float(hist['Close'].iloc[-1])
        previous = float(hist['Close'].iloc[-2])
        change_pct = ((current - previous) / previous) * 100
        return {'price': current, 'change_pct': change_pct, 'trend': 'up' if change_pct > 0 else 'down'}
    except Exception: return {}

# ============================================================================
# CBOE SCRAPER
# ============================================================================

class CBOEScraper:
    def __init__(self):
        self.config = config
    
    def fetch_institutional_data(self, symbol: str = "SPX") -> Optional[Dict]:
        for attempt in range(self.config.MAX_RETRIES):
            try:
                time.sleep(1)
                data = self._scrape_stealth(symbol)
                if data and self._validate_data(data): return data
                if attempt < self.config.MAX_RETRIES - 1: time.sleep(3)
            except Exception as e:
                logger.error(f"Erro: {e}")
        return None
    
    def _scrape_stealth(self, symbol: str) -> Optional[Dict]:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                self.config.USER_DATA_PATH,
                headless=self.config.HEADLESS,
                args=['--disable-blink-features=AutomationControlled', '--disable-web-security', '--no-sandbox'],
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.pages[0] if context.pages else context.new_page()
            try:
                url_json = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"
                page.goto(url_json, wait_until="domcontentloaded", timeout=self.config.REQUEST_TIMEOUT)
                time.sleep(random.uniform(2, 4))
                content = page.inner_text("body")
                
                if "options" in content and "data" in content:
                    data = json.loads(content)
                    context.close()
                    return data
                
                url_chain = f"https://www.cboe.com/indices/quotes/option-chain/{symbol}/"
                page.goto(url_chain, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                page.goto(url_json, timeout=60000)
                content = page.inner_text("body")
                
                if "options" in content:
                    data = json.loads(content)
                    context.close()
                    return data
                
                context.close()
                return None
            except Exception as e:
                context.close()
                raise e
    
    def _validate_data(self, data: Dict) -> bool:
        try: return ("data" in data and "last" in data["data"] and "options" in data["data"] and len(data["data"]["options"]) > 0)
        except Exception: return False

# ============================================================================
# CÁLCULOS MATEMÁTICOS
# ============================================================================

class GEXCalculator:
    def __init__(self, spot: float):
        self.spot = spot
    
    def calculate_gex_levels(self, df: pd.DataFrame) -> Dict[str, float]:
        if df.empty: 
            return {k: self.spot for k in ['zg', 'cw', 'pw', 'vt', 'l1', 'c1', 'c4', 'cw_0dte', 'pw_0dte']}
        
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        strikes, gex_vals = agg['Strike'].values, agg['GEX'].values
        
        zg = self._calculate_zero_gamma(strikes, gex_vals)
        cw = agg.loc[agg['GEX'].idxmax(), 'Strike']
        pw = agg.loc[agg['GEX'].idxmin(), 'Strike']
        vt = self._calculate_vol_trigger(agg, pw, zg)
        
        top_calls = agg.nlargest(3, 'GEX')['Strike'].tolist()
        l1 = top_calls[1] if (len(top_calls) > 1 and top_calls[0] == cw) else (top_calls[0] if len(top_calls)>0 else cw)
        
        c1_df = agg[agg['Strike'] > pw]
        c1 = c1_df.loc[c1_df['GEX'].idxmin(), 'Strike'] if not c1_df.empty else pw
        
        c4_df = agg[agg['Strike'] < pw]
        c4 = c4_df.loc[c4_df['GEX'].idxmin(), 'Strike'] if not c4_df.empty else pw
        
        cw_0dte, pw_0dte = self.spot, self.spot
        if 'Date' in df.columns:
            min_date = df['Date'].min()
            df_0dte = df[df['Date'] == min_date].groupby('Strike')['GEX'].sum().reset_index()
            if not df_0dte.empty:
                cw_0dte = df_0dte.loc[df_0dte['GEX'].idxmax(), 'Strike']
                pw_0dte = df_0dte.loc[df_0dte['GEX'].idxmin(), 'Strike']
        
        return {
            'zg': float(zg), 'cw': float(cw), 'pw': float(pw), 'vt': float(vt),
            'l1': float(l1), 'c1': float(c1), 'c4': float(c4),
            'cw_0dte': float(cw_0dte), 'pw_0dte': float(pw_0dte)
        }
    
    def _calculate_zero_gamma(self, strikes: np.ndarray, gex_vals: np.ndarray) -> float:
        try:
            sign_changes = np.where(np.diff(np.sign(gex_vals)) != 0)[0]
            if len(sign_changes) == 0: return float(strikes[np.argmin(np.abs(gex_vals))])
            idx = sign_changes[0]
            x1, x2, y1, y2 = strikes[idx], strikes[idx + 1], gex_vals[idx], gex_vals[idx + 1]
            if abs(y2 - y1) < 1e-10: return float(x1)
            return float(x1 - y1 * (x2 - x1) / (y2 - y1))
        except: return float(self.spot)
    
    def _calculate_vol_trigger(self, df: pd.DataFrame, pw: float, zg: float) -> float:
        try:
            mask = (df['Strike'] > min(pw, zg)) & (df['Strike'] < max(pw, zg))
            filtered = df[mask]
            if filtered.empty: return float(pw)
            return float(filtered.loc[filtered['GEX'].idxmin(), 'Strike'])
        except: return float(pw)

# ============================================================================
# GERADOR DE SINAIS E PLAYBOOK
# ============================================================================

@dataclass
class TradeSignal:
    direction: str
    color: str
    regime_desc: str
    entry_zone: str
    targets: str
    invalidation: str
    filters_html: str
    
    def to_html(self) -> str:
        return f"""
<div class="playbook-container" style="border-left: 6px solid {self.color};">
<div style="font-size: 11px; color: #8A94A6; letter-spacing: 1px; font-weight: 700;">PLANO DE VOO TÁTICO (PLAYBOOK)</div>
<div style="font-size: 32px; font-weight: 900; color: {self.color}; font-family: 'JetBrains Mono', monospace; margin-top: -2px; margin-bottom: 5px;">{self.direction}</div>
<div style="font-size: 14px; color: #b0b8c8; margin-bottom: 12px; font-style: italic;">{self.regime_desc}</div>
<div class="playbook-grid">
<div class="playbook-item">
<div class="playbook-item-title">🟢 Gatilho (Entrada)</div>
<div class="playbook-item-value">{self.entry_zone}</div>
</div>
<div class="playbook-item">
<div class="playbook-item-title">🎯 Alvos (Take Profit)</div>
<div class="playbook-item-value">{self.targets}</div>
</div>
<div class="playbook-item">
<div class="playbook-item-title">🛑 Stop (Invalidação)</div>
<div class="playbook-item-value">{self.invalidation}</div>
</div>
</div>
<div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; display: flex; align-items: center;">
<span style="font-size: 11px; color: #8A94A6; margin-right: 12px; font-weight: 700;">FILTROS DA MESA:</span>
{self.filters_html}
</div>
</div>
"""

class SignalGenerator:
    def __init__(self, spot: float, basis: float, levels: Dict[str, float], spy_data: Dict = None):
        self.es_spot = spot + basis
        self.levels = {k: v + basis for k, v in levels.items()}
        self.spy_data = spy_data
        self.vix_data = {}
    
    def add_vix_data(self, vix: float, vix9d: float):
        self.vix_data = {'vix': vix, 'vix9d': vix9d}
    
    def generate(self) -> TradeSignal:
        es_zg = self.levels['zg']
        es_vt = self.levels['vt']
        es_cw = self.levels['cw']
        es_pw = self.levels['pw']
        es_l1 = self.levels['l1']
        es_c1 = self.levels['c1']
        
        if self.es_spot > es_zg:
            direction = "LONG 📈"
            color = "#00FFAA"
            regime = "Regime de Call Gamma. Market Makers estabilizam o preço atuando contra a tendência (Buy the Dip)."
            entry = f"Aguardar pullback e comprar suporte em {es_zg:.2f} (ZG) ou rompimento limpo de {es_l1:.2f} (L1)."
            target = f"Alvo 1: {es_l1:.2f} | Alvo Final: {es_cw:.2f} (Call Wall)"
            stop = f"Fechamento de candle M15/H1 abaixo de {es_zg:.2f}."
            
        elif es_vt < self.es_spot <= es_zg:
            direction = "RANGE / CAUTELA ⚠️"
            color = "#FFCC00"
            regime = "Zona de Compressão. Baixa convicção direcional com risco de violação de stops (Choppy Market)."
            entry = f"Comprar perto de {es_vt:.2f} (VT) ou vender nas rejeições de {es_zg:.2f} (ZG)."
            target = f"Extremo oposto da caixa d'água ({es_zg:.2f} se comprado, {es_vt:.2f} se vendido)."
            stop = f"Rompimento com volume fora da zona ({es_vt:.2f} a {es_zg:.2f})."
            
        else:
            direction = "STRONG SHORT 📉"
            color = "#FF4444"
            regime = "Gamma Trap ativado. Dealers forçados a vender contratos para proteção de Delta, acelerando o pânico."
            entry = f"Vender pullbacks na rejeição de {es_vt:.2f} (Vol Trigger) ou na perda de {es_c1:.2f}."
            target = f"Alvo 1: {es_c1:.2f} | Alvo Final: {es_pw:.2f} (Put Wall)"
            stop = f"Preço se recuperar e fechar acima de {es_vt:.2f}."
            
        filters = []
        if self.vix_data:
            vix = self.vix_data.get('vix', 0)
            vix9d = self.vix_data.get('vix9d', 0)
            if vix9d > vix:
                filters.append('<span class="filter-badge" style="background: rgba(255, 68, 68, 0.15); color: #ff6b6b; border: 1px solid #ff6b6b;">VIX Backwardation</span>')
            elif vix > 20:
                filters.append('<span class="filter-badge" style="background: rgba(255, 204, 0, 0.15); color: #FFCC00; border: 1px solid #FFCC00;">VIX Alta Volatilidade</span>')
            else:
                filters.append('<span class="filter-badge" style="background: rgba(0, 255, 170, 0.15); color: #00FFAA; border: 1px solid #00FFAA;">VIX Estável</span>')
        
        if self.spy_data:
            spy_trend = self.spy_data.get('trend', 'neutral')
            if spy_trend == 'up':
                filters.append('<span class="filter-badge" style="background: rgba(0, 255, 170, 0.15); color: #00FFAA; border: 1px solid #00FFAA;">SPY Trend UP</span>')
            else:
                filters.append('<span class="filter-badge" style="background: rgba(255, 68, 68, 0.15); color: #ff6b6b; border: 1px solid #ff6b6b;">SPY Trend DOWN</span>')
                
        filters_html = " ".join(filters) if filters else "<span style='color:#5a6478;'>Sem dados de filtro</span>"
        
        return TradeSignal(direction, color, regime, entry, target, stop, filters_html)

def generate_pine_script(levels: Dict[str, float], basis: float, timestamp: datetime) -> str:
    def adj(k: str) -> float: return round(levels.get(k, 0) + basis, 2)
    date_str = timestamp.strftime('%d/%m/%Y %H:%M')
    return f"""//@version=5
indicator("GEX Elite MT5 - {date_str}", overlay=true)
plot({adj('zg')}, "Zero Gamma", color.white, 2)
plot({adj('cw')}, "Call Wall", color.red, 2)
plot({adj('pw')}, "Put Wall", color.green, 2)
plot({adj('vt')}, "Vol Trigger", color.aqua, 1)
"""

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    if 'spx_data' not in st.session_state: st.session_state.spx_data = None
    if 'last_update' not in st.session_state: st.session_state.last_update = None
    
    # --- CABEÇALHO IMAGÉTICO PREMIUM ---
    status_html = "<span style='color:#00FFAA'>● LIVE</span>" if st.session_state.spx_data else "<span style='color:#FFCC00'>● STANDBY / DEMO</span>"
    time_html = st.session_state.last_update or '--:--:--'
    
    st.markdown(f"""
<div class="header-container">
<div>
<h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1>
<p class='header-subtitle'>SPX Exclusive • Playbook Tático • MT5 Sync</p>
</div>
<div class="header-status">
<div style="margin-bottom: 3px;">STATUS: {status_html}</div>
<div>LAST UPDATE: {time_html}</div>
</div>
</div>
""", unsafe_allow_html=True)
    
    # --- YAHOO FINANCE DATA ---
    with st.spinner("📡 Sincronizando dados de mercado..."):
        market_data = fetch_yf_data(("^VIX", "^VIX9D", "ES=F"))
        spy_data = get_spy_analysis()
    
    vix_val = market_data.get("^VIX")
    vix9d_val = market_data.get("^VIX9D")
    es_fut = market_data.get("ES=F")
    
    # --- SIDEBAR LIMPA ---
    with st.sidebar:
        st.header("⚙️ Configurações")
        range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)
        
        st.divider()
        st.markdown("""
<div style="background: linear-gradient(90deg, rgba(0,212,255,0.1), transparent); padding: 10px; border-radius: 8px; border-left: 3px solid #00D4FF; margin-bottom: 10px;">
<h4 style="color: #00D4FF; margin: 0; font-size: 14px;">📊 MESA PROP MT5</h4>
</div>
""", unsafe_allow_html=True)
        
        default_mt5 = es_fut if es_fut else 5100.0
        if st.session_state.spx_data:
            default_mt5 = float(st.session_state.spx_data["data"]["last"])
        
        mt5_price = st.number_input("💻 Preço do ES no seu MT5:", value=default_mt5, step=0.25, format="%.2f", help="Sincroniza os cálculos e as linhas para o valor da sua corretora.")
        usar_mt5 = st.toggle("✅ Usar MT5 para ajustar níveis", value=True)
        
        st.divider()
        with st.expander("🔧 Manutenção (Anti-Bloqueio)"):
            st.caption("Se a CBOE bloquear repetidas vezes, ative esta chave, clique em processar e resolva o Captcha na janela do Chrome. Depois, desative.")
            modo_debug = st.checkbox("Ativar Modo Debug", value=False)
        
    # --- AÇÃO DOS BOTÕES ---
    data_to_use = st.session_state.spx_data
    is_live = True
    ativo = "SPX"
    
    if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL (SPX)", use_container_width=True, type="primary"):
        with st.spinner("🔍 Conectando à CBOE (Motor Persistente)..."):
            config.HEADLESS = not modo_debug
            scraper = CBOEScraper()
            new_data = scraper.fetch_institutional_data(ativo)
            if new_data:
                data_to_use = new_data
                st.session_state.spx_data = new_data
                st.session_state.last_update = datetime.now().strftime("%H:%M:%S")
                st.rerun()
            else:
                st.error("❌ CBOE bloqueou temporariamente. Ative o Modo Debug na barra lateral ou tente novamente.")

    # --- LÓGICA DE DADOS (DEMO VS REAL) ---
    if not data_to_use:
        is_live = False
        spot = 5100.0
        
        strikes_demo = [4900, 4950, 5000, 5050, 5100, 5150, 5200, 5250, 5300]
        gex_demo = [-120e6, -50e6, -200e6, -80e6, 10e6, 40e6, 180e6, 90e6, 30e6]
        df = pd.DataFrame({'Strike': strikes_demo, 'GEX': gex_demo, 'Date': '240315'})
        agg = df
        levels = {
            'zg': 5080.0, 'cw': 5200.0, 'pw': 5000.0, 'vt': 5040.0,
            'l1': 5250.0, 'c1': 5050.0, 'c4': 4900.0,
            'cw_0dte': 5150.0, 'pw_0dte': 5050.0
        }
        st.markdown('<div class="offline-banner">🟡 MODO DEMO: Exibindo perfil estrutural. Pressione o botão acima para sincronizar com o mercado real.</div>', unsafe_allow_html=True)
    else:
        spot = float(data_to_use["data"]["last"])
        df = pd.DataFrame(data_to_use["data"]["options"])
        
        def parse_option(opt_str):
            if not isinstance(opt_str, str): return None
            match = re.search(r'^([a-zA-Z]+)(\d{6})([CP])(\d{8})$', opt_str)
            if match: return {'date': match.group(2), 'type': match.group(3), 'strike': int(match.group(4)) / 1000.0}
            return None
            
        parsed = df["option"].apply(parse_option)
        df["Date"] = parsed.apply(lambda x: x['date'] if x else None)
        df["Type"] = parsed.apply(lambda x: x['type'] if x else None)
        df["Strike"] = parsed.apply(lambda x: x['strike'] if x else None)
        
        for col in ["iv", "gamma", "open_interest"]: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df = df.dropna(subset=['Strike', 'Type', 'Date'])
        
        df['GEX'] = df['gamma'] * df['open_interest'] * 100 * spot**2 * 0.01
        df.loc[df['Type'] == 'P', 'GEX'] *= -1
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        
        calculator = GEXCalculator(spot)
        levels = calculator.calculate_gex_levels(df)

    # --- LÓGICA MT5 / BASIS ---
    if usar_mt5 and mt5_price > 0:
        es_real = mt5_price
        basis = mt5_price - spot
        preco_oficial = es_fut if es_fut else spot
        divergencia = mt5_price - preco_oficial
        
        if abs(divergencia) > 5:
            st.markdown(f'<div class="divergence-alert high">🔴 DIVERGÊNCIA CRÍTICA: O preço MT5 ({mt5_price:.2f}) está {divergencia:+.2f} pts longe do oficial.</div>', unsafe_allow_html=True)
    else:
        if es_fut:
            es_real = es_fut
            basis = es_real - spot
        else:
            basis = 0.0
            es_real = spot
        divergencia = 0
        
    def adj(val): return float(val) + basis
    levels_adj = {k: adj(v) for k, v in levels.items()}
    
    # ========================================================================
    # RENDERIZAÇÃO DA DASHBOARD
    # ========================================================================
    
    # ROW 1: SPY, VIX e PLANO DE VOO
    top_col1, top_col2, top_col3 = st.columns([1, 1, 2.5])
    
    with top_col1:
        spy_price = spy_data.get('price', 0) if spy_data else 0
        spy_change = spy_data.get('change_pct', 0) if spy_data else 0
        color_spy = "#00FFAA" if spy_change > 0 else "#ff6b6b"
        st.markdown(f"""
<div class="metric-card" style="border-left: 3px solid {color_spy}; height: 100%;">
<div style="font-size:11px; color:#8A94A6; font-weight:700; letter-spacing: 1px;">SPY (ETF)</div>
<div style="font-size:28px; font-weight:700; color:{color_spy}; font-family:JetBrains Mono; margin-top: 10px;">${spy_price:.2f}</div>
<div style="font-size:12px; color:#b0b8c8; margin-top: 5px;">Trend: {spy_change:+.2f}%</div>
</div>
""", unsafe_allow_html=True)
        
    with top_col2:
        vix_color = "#ff6b6b" if (vix_val and vix_val > 20) else "#00FFAA"
        v9 = vix9d_val if vix9d_val else 0
        v = vix_val if vix_val else 0
        st.markdown(f"""
<div class="metric-card" style="border-left: 3px solid {vix_color}; height: 100%;">
<div style="font-size:11px; color:#8A94A6; font-weight:700; letter-spacing: 1px;">VIX SPOT</div>
<div style="font-size:28px; font-weight:700; color:{vix_color}; font-family:JetBrains Mono; margin-top: 10px;">{v:.2f}</div>
<div style="font-size:12px; color:#b0b8c8; margin-top: 5px;">VIX9D: {v9:.2f}</div>
</div>
""", unsafe_allow_html=True)
        
    with top_col3:
        signal_gen = SignalGenerator(spot, basis, levels, spy_data)
        if vix_val and vix9d_val: signal_gen.add_vix_data(vix_val, vix9d_val)
        signal = signal_gen.generate()
        st.markdown(signal.to_html(), unsafe_allow_html=True)

    # ROW 2: PAINEL DE CÓPIA RÁPIDA
    st.markdown("<h3 style='margin-top: 20px; font-size: 16px; color: #FFFFFF; font-weight: 600;'><span style='color:#00D4FF;'>📋 EXPORTAÇÃO:</span> Passe o mouse sobre o número e clique no ícone para copiar as taxas ajustadas para o seu MT5.</h3>", unsafe_allow_html=True)
    
    cp_col1, cp_col2, cp_col3, cp_col4 = st.columns(4)
    
    with cp_col1:
        st.markdown("<div class='copy-panel-title'>MACRO WALLS</div>", unsafe_allow_html=True)
        st.caption("Call Wall Principal")
        st.code(f"{levels_adj['cw']:.2f}", language=None)
        st.caption("Put Wall Principal")
        st.code(f"{levels_adj['pw']:.2f}", language=None)
        
    with cp_col2:
        st.markdown("<div class='copy-panel-title'>INFLEXÃO & RISCO</div>", unsafe_allow_html=True)
        st.caption("Zero Gama (Divisa de Tendência)")
        st.code(f"{levels_adj['zg']:.2f}", language=None)
        st.caption("Vol Trigger (Gatilho de Queda)")
        st.code(f"{levels_adj['vt']:.2f}", language=None)
        
    with cp_col3:
        st.markdown("<div class='copy-panel-title'>MICRO 0DTE</div>", unsafe_allow_html=True)
        st.caption("Call Wall (0DTE)")
        st.code(f"{levels_adj['cw_0dte']:.2f}", language=None)
        st.caption("Put Wall (0DTE)")
        st.code(f"{levels_adj['pw_0dte']:.2f}", language=None)
        
    with cp_col4:
        st.markdown("<div class='copy-panel-title'>SUPORTE/RESISTÊNCIA</div>", unsafe_allow_html=True)
        st.caption("Nível L1 (Top Call Secundária)")
        st.code(f"{levels_adj['l1']:.2f}", language=None)
        st.caption("Nível C1 (Suporte Secundário)")
        st.code(f"{levels_adj['c1']:.2f}", language=None)

    # ROW 3: Gráfico Visual
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Perfil Institucional (Gamma Exposure)")
    
    mask = (agg['Strike'] > spot * (1 - range_pct/100)) & (agg['Strike'] < spot * (1 + range_pct/100))
    chart_data = agg[mask].copy()
    chart_data['Strike'] = chart_data['Strike'] + basis 
    
    lines_data = pd.DataFrame([
        {'Strike': levels_adj['zg'], 'Level': 'ZG', 'Color': '#FFFFFF'},
        {'Strike': levels_adj['vt'], 'Level': 'VT', 'Color': '#00D4FF'},
        {'Strike': levels_adj['cw'], 'Level': 'CW', 'Color': '#FF6B6B'},
        {'Strike': levels_adj['pw'], 'Level': 'PW', 'Color': '#00FF44'}
    ])
    
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Strike:Q', title='Preço do Ativo (Ajustado ao seu MT5)', scale=alt.Scale(zero=False)),
        y=alt.Y('GEX:Q', title='Exposição Líquida em Dólares ($)'),
        color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#ff6b6b')),
        tooltip=['Strike', 'GEX']
    ).properties(height=380)
    
    rules = alt.Chart(lines_data).mark_rule(strokeDash=[5,5], strokeWidth=2).encode(
        x='Strike:Q',
        color=alt.Color('Color:N', scale=None),
        tooltip=['Level', 'Strike']
    )
    st.altair_chart(chart + rules, use_container_width=True)

    # ROW 4: Exportação Pine Script
    with st.expander("🖥️ PINE SCRIPT (Exportar para TradingView)"):
        pine_code = generate_pine_script(levels, basis, datetime.now())
        st.code(pine_code, language="pine")
        st.download_button(label="📥 Download .pine", data=pine_code, file_name=f"GEX_ELITE_{datetime.now().strftime('%Y%m%d')}.pine", mime="text/plain")

    # Footer
    st.divider()
    mt5_status = f"Sincronizado ({mt5_price:.2f})" if usar_mt5 else "Desativado"
    live_status = "ONLINE (LIVE)" if is_live else "OFFLINE (DEMO)"
    st.markdown(f"""
<div style="text-align:center; font-size:11px; color:#5a6478; font-family:JetBrains Mono; text-transform: uppercase;">
GEX ULTRA ELITE PRO | Status: {live_status} | MT5 Sync: {mt5_status}
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
