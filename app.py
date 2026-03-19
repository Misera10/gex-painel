"""
GEX ULTRA ELITE TERMINAL PRO (SPX/ES Edition v5.3 + MT5 Export)
Features: Dashboard Completa | Painel de Cópia | MT5 Sync | Export CSV | Playbook
Fonte: Yahoo Finance (dados convertidos automaticamente para SPX/ES)
"""

import sys
import os
import csv

__version__ = "5.3.0-SPX-MT5"

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

import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import yfinance as yf
import altair as alt

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

@dataclass
class GEXConfig:
    CACHE_TTL: int = 300
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    TIMEZONE: str = 'America/New_York'

config = GEXConfig()

# ============================================================================
# CSS PREMIUM
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

def get_spx_analysis() -> Dict[str, Any]:
    try:
        es = yf.Ticker("ES=F")
        hist = es.history(period="5d")
        if hist.empty: return {}
        current = float(hist['Close'].iloc[-1])
        previous = float(hist['Close'].iloc[-2])
        change_pct = ((current - previous) / previous) * 100
        return {'price': current, 'change_pct': change_pct, 'trend': 'up' if change_pct > 0 else 'down'}
    except Exception: return {}

# ============================================================================
# EXPORTAÇÃO CSV PARA MT5 (NOVO)
# ============================================================================

def export_to_mt5_csv(levels_adj, filename="gex_levels.csv"):
    """Exporta níveis para CSV compatível com MetaTrader 5"""
    
    # Mapeamento de cores (MT5 entende nomes em inglês)
    color_map = {
        'cw': 'RED', 'pw': 'GREEN', 'zg': 'WHITE', 'vt': 'AQUA',
        'l1': 'GRAY', 'c1': 'FUCHSIA', 'c4': 'PURPLE',
        'cw_0dte': 'ORANGE', 'pw_0dte': 'LIME'
    }
    
    descriptions = {
        'cw': 'Call Wall Macro',
        'pw': 'Put Wall Macro', 
        'zg': 'Zero Gama - Flip Zone',
        'vt': 'Vol Trigger - Gatilho Venda',
        'l1': 'L1 - Alvo Long',
        'c1': 'C1 - Suporte Secundario',
        'c4': 'C4 - Exaustao Put',
        'cw_0dte': 'Call Wall 0DTE',
        'pw_0dte': 'Put Wall 0DTE'
    }
    
    # Caminho padrão do MT5 para arquivos Files/
    mt5_path = r"C:\Program Files\MetaTrader 5\MQL5\Files\gex_levels.csv"
    
    try:
        with open(mt5_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['nivel', 'valor', 'cor', 'descricao'])
            
            for key, value in levels_adj.items():
                if key in color_map:
                    writer.writerow([
                        key.upper(),
                        f"{value:.2f}",
                        color_map[key],
                        descriptions.get(key, '')
                    ])
        
        return True, mt5_path
    except PermissionError:
        return False, "Permissão negada. Execute como Administrador ou verifique se o MT5 está fechado."
    except Exception as e:
        return False, str(e)

# ============================================================================
# YAHOO FINANCE SCRAPER (CONVERTIDO PARA SPX/ES)
# ============================================================================

class SPXDataFetcher:
    def __init__(self):
        self.config = config
    
    def fetch_institutional_data(self, symbol: str = "SPY") -> Optional[Dict]:
        for attempt in range(self.config.MAX_RETRIES):
            try:
                logger.info(f"Tentativa {attempt + 1} para buscar dados SPX")
                
                ticker = yf.Ticker(symbol)
                expirations = ticker.options
                if not expirations:
                    if attempt < self.config.MAX_RETRIES - 1:
                        time.sleep(2)
                        continue
                    return None
                
                nearest_exp = expirations[0]
                chain = ticker.option_chain(nearest_exp)
                calls = chain.calls
                puts = chain.puts
                
                if calls.empty or puts.empty:
                    if attempt < self.config.MAX_RETRIES - 1:
                        time.sleep(2)
                        continue
                    return None
                
                spy_spot = ticker.history(period="1d")["Close"].iloc[-1]
                spx_spot = spy_spot * 10
                
                options_data = []
                
                for _, row in calls.iterrows():
                    if pd.isna(row.get('strike')) or pd.isna(row.get('impliedVolatility')):
                        continue
                    options_data.append({
                        'strike': float(row['strike']) * 10,
                        'type': 'C',
                        'iv': float(row['impliedVolatility'].strip('%')) / 100 if isinstance(row['impliedVolatility'], str) else float(row['impliedVolatility']),
                        'open_interest': float(row['openInterest']) if not pd.isna(row.get('openInterest')) else 0,
                        'lastPrice': float(row['lastPrice']) * 10 if not pd.isna(row.get('lastPrice')) else 0,
                        'expiration': nearest_exp
                    })
                
                for _, row in puts.iterrows():
                    if pd.isna(row.get('strike')) or pd.isna(row.get('impliedVolatility')):
                        continue
                    options_data.append({
                        'strike': float(row['strike']) * 10,
                        'type': 'P',
                        'iv': float(row['impliedVolatility'].strip('%')) / 100 if isinstance(row['impliedVolatility'], str) else float(row['impliedVolatility']),
                        'open_interest': float(row['openInterest']) if not pd.isna(row.get('openInterest')) else 0,
                        'lastPrice': float(row['lastPrice']) * 10 if not pd.isna(row.get('lastPrice')) else 0,
                        'expiration': nearest_exp
                    })
                
                if not options_data:
                    return None
                
                return {
                    "data": {
                        "last": float(spx_spot),
                        "current_price": float(spx_spot),
                        "options": options_data
                    }
                }
                
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1}: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(2)
                continue
        
        return None

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
# GERADOR DE SINAIS
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
    def __init__(self, spot: float, basis: float, levels: Dict[str, float], spx_data: Dict = None):
        self.es_spot = spot + basis
        self.levels = {k: v + basis for k, v in levels.items()}
        self.spx_data = spx_data
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
            direction = "COMPRA 📈"
            color = "#00FFAA"
            regime = "Regime de Call Gamma. Market Makers estabilizam o S&P 500 atuando contra a tendência (Buy the Dip)."
            entry = f"Aguardar pullback e comprar suporte em {es_zg:.2f} (ZG) ou rompimento limpo de {es_l1:.2f} (L1)."
            target = f"Alvo 1: {es_l1:.2f} | Alvo Final: {es_cw:.2f} (Call Wall)"
            stop = f"Fechamento de candle M15/H1 abaixo de {es_zg:.2f}."
            
        elif es_vt < self.es_spot <= es_zg:
            direction = "LATERAL / CAUTELA ⚠️"
            color = "#FFCC00"
            regime = "Zona de Compressão no S&P 500. Baixa convicção direcional com risco de violação de stops."
            entry = f"Comprar perto de {es_vt:.2f} (VT) ou vender nas rejeições de {es_zg:.2f} (ZG)."
            target = f"Extremo oposto da caixa ({es_zg:.2f} se comprado, {es_vt:.2f} se vendido)."
            stop = f"Rompimento com volume fora da zona ({es_vt:.2f} a {es_zg:.2f})."
            
        else:
            direction = "VENDA FORTE 📉"
            color = "#FF4444"
            regime = "Gamma Trap ativado no S&P 500. Dealers forçados a vender contratos, acelerando o pânico."
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
        
        if self.spx_data:
            spx_trend = self.spx_data.get('trend', 'neutral')
            if spx_trend == 'up':
                filters.append('<span class="filter-badge" style="background: rgba(0, 255, 170, 0.15); color: #00FFAA; border: 1px solid #00FFAA;">S&P 500 em ALTA</span>')
            else:
                filters.append('<span class="filter-badge" style="background: rgba(255, 68, 68, 0.15); color: #ff6b6b; border: 1px solid #ff6b6b;">S&P 500 em BAIXA</span>')
                
        filters_html = " ".join(filters) if filters else "<span style='color:#5a6478;'>Sem dados</span>"
        
        return TradeSignal(direction, color, regime, entry, target, stop, filters_html)

def generate_pine_script(levels: Dict[str, float], basis: float, timestamp: datetime) -> str:
    def adj(k: str) -> float: 
        return round(levels.get(k, 0) + basis, 2)
    
    date_str = timestamp.strftime('%d/%m/%Y')
    
    return f"""//@version=5
indicator("GEX ULTRA ELITE - {date_str}", overlay=true)

// === INPUTS ===
cw = input.float({adj('cw')}, "Call Wall")
zg = input.float({adj('zg')}, "Zero Gama")
pw = input.float({adj('pw')}, "Put Wall")
vt = input.float({adj('vt')}, "Vol Trigger")
l1 = input.float({adj('l1')}, "L1")
c1 = input.float({adj('c1')}, "C1")
c4 = input.float({adj('c4')}, "C4")
cw_0dte = input.float({adj('cw_0dte')}, "CW 0DTE")
pw_0dte = input.float({adj('pw_0dte')}, "PW 0DTE")
show_vwap = input.bool(true, "Exibir VWAP")

// === PLOTS ===
plot(cw, "Call Wall", color.red, 2)
plot(zg, "Zero Gama", color.white, 2)
plot(pw, "Put Wall", color.green, 2)
plot(vt, "Vol Trigger", color.aqua, 1)
plot(l1, "L1", color.gray, 1)
plot(c1, "C1", color.fuchsia, 1)
plot(c4, "C4", color.purple, 1)
plot(cw_0dte, "CW 0DTE", color.new(color.red, 40), 3, style=plot.style_circles)
plot(pw_0dte, "PW 0DTE", color.new(color.green, 40), 3, style=plot.style_circles)
plot(show_vwap ? ta.vwap : na, "VWAP", color.orange, 2)

// === LABELS ===
var label lbl_cw = label.new(na, na, "CALL WALL", style=label.style_label_left, size=size.small)
var label lbl_zg = label.new(na, na, "ZERO GAMA", style=label.style_label_left, size=size.small)
var label lbl_pw = label.new(na, na, "PUT WALL", style=label.style_label_left, size=size.small)
var label lbl_cw0 = label.new(na, na, "CW 0DTE", style=label.style_label_left, size=size.tiny)
var label lbl_pw0 = label.new(na, na, "PW 0DTE", style=label.style_label_left, size=size.tiny)
var label lbl_vt = label.new(na, na, "VOL TRIGGER", style=label.style_label_left, size=size.tiny)
var label lbl_l1 = label.new(na, na, "L1", style=label.style_label_left, size=size.tiny)
var label lbl_c1 = label.new(na, na, "C1", style=label.style_label_left, size=size.tiny)
var label lbl_c4 = label.new(na, na, "C4", style=label.style_label_left, size=size.tiny)

// === POSICIONAMENTO INTELIGENTE ===
if barstate.islast
    // Macro (5 barras)
    label.set_xy(lbl_cw, bar_index + 5, cw)
    label.set_xy(lbl_zg, bar_index + 5, zg)
    label.set_xy(lbl_pw, bar_index + 5, pw)
    label.set_color(lbl_cw, color.red)
    label.set_textcolor(lbl_cw, color.white)
    label.set_color(lbl_zg, color.white)
    label.set_textcolor(lbl_zg, color.black)
    label.set_color(lbl_pw, color.green)
    label.set_textcolor(lbl_pw, color.white)
    
    // 0DTE (10-15 barras)
    cw0_offset = 10
    pw0_offset = 10
    
    if math.abs(cw_0dte - pw_0dte) < 5
        cw0_offset := 10
        pw0_offset := 15
    else
        cw0_offset := 10
        pw0_offset := 10
    
    label.set_xy(lbl_cw0, bar_index + cw0_offset, cw_0dte)
    label.set_xy(lbl_pw0, bar_index + pw0_offset, pw_0dte)
    label.set_color(lbl_cw0, color.red)
    label.set_textcolor(lbl_cw0, color.white)
    label.set_color(lbl_pw0, color.green)
    label.set_textcolor(lbl_pw0, color.white)
    
    // Outros níveis (15-20 barras)
    label.set_xy(lbl_vt, bar_index + 15, vt)
    label.set_xy(lbl_l1, bar_index + 20, l1)
    label.set_xy(lbl_c1, bar_index + 20, c1)
    label.set_xy(lbl_c4, bar_index + 20, c4)
    label.set_color(lbl_vt, color.aqua)
    label.set_textcolor(lbl_vt, color.black)
    label.set_color(lbl_l1, color.gray)
    label.set_textcolor(lbl_l1, color.white)
    label.set_color(lbl_c1, color.fuchsia)
    label.set_textcolor(lbl_c1, color.white)
    label.set_color(lbl_c4, color.purple)
    label.set_textcolor(lbl_c4, color.white)
"""

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    if 'spx_data' not in st.session_state: st.session_state.spx_data = None
    if 'last_update' not in st.session_state: st.session_state.last_update = None
    
    # --- CABEÇALHO ---
    status_html = "<span style='color:#00FFAA'>● ONLINE</span>" if st.session_state.spx_data else "<span style='color:#FFCC00'>● STANDBY</span>"
    time_html = st.session_state.last_update or '--:--:--'
    
    st.markdown(f"""
<div class="header-container">
<div>
<h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1>
<p class='header-subtitle'>S&P 500 • ES Futures • Playbook Tático • MT5 Export</p>
</div>
<div class="header-status">
<div style="margin-bottom: 3px;">STATUS: {status_html}</div>
<div>ÚLTIMA ATUALIZAÇÃO: {time_html}</div>
</div>
</div>
""", unsafe_allow_html=True)
    
    # --- DADOS DE MERCADO ---
    with st.spinner("📡 Sincronizando S&P 500..."):
        market_data = fetch_yf_data(("^VIX", "^VIX9D", "ES=F"))
        spx_data = get_spx_analysis()
    
    vix_val = market_data.get("^VIX")
    vix9d_val = market_data.get("^VIX9D")
    es_fut = market_data.get("ES=F")
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Configurações")
        range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)
        
        st.divider()
        st.markdown("""
<div style="background: linear-gradient(90deg, rgba(0,212,255,0.1), transparent); padding: 10px; border-radius: 8px; border-left: 3px solid #00D4FF; margin-bottom: 10px;">
<h4 style="color: #00D4FF; margin: 0; font-size: 14px;">📊 SEU MT5</h4>
</div>
""", unsafe_allow_html=True)
        
        default_mt5 = es_fut if es_fut else 6700.0
        if st.session_state.spx_data:
            default_mt5 = float(st.session_state.spx_data["data"]["last"])
        
        mt5_price = st.number_input("💻 Preço ES no MT5:", value=default_mt5, step=0.25, format="%.2f")
        usar_mt5 = st.toggle("✅ Usar MT5 para ajustar níveis", value=True)
        
        st.divider()
        
        # === EXPORTAÇÃO PARA MT5 ===
        st.markdown("### 📤 EXPORTAR PARA MT5")
        st.caption("Gera arquivo CSV para importar níveis no MetaTrader 5")
        
        if st.button("🔄 Gerar CSV para MT5", use_container_width=True):
            if 'levels_adj' in locals() and levels_adj:
                success, result = export_to_mt5_csv(levels_adj)
                if success:
                    st.success(f"✅ CSV exportado!")
                    st.caption(f"📁 {result}")
                    st.info("💡 No MT5: Insira o indicador GEX_CSV_Importer.mq5")
                else:
                    st.error(f"❌ Erro: {result}")
            else:
                st.warning("⚠️ Processe a matriz primeiro!")
        
        st.divider()
        st.caption("v5.3.0-SPX-MT5 • Yahoo Finance • Sem bloqueios")
        
    # --- BOTÃO PRINCIPAL ---
    data_to_use = st.session_state.spx_data
    is_live = True
    
    if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL (S&P 500)", use_container_width=True, type="primary"):
        with st.spinner("🔍 Buscando dados S&P 500..."):
            fetcher = SPXDataFetcher()
            new_data = fetcher.fetch_institutional_data("SPY")
            if new_data:
                data_to_use = new_data
                st.session_state.spx_data = new_data
                st.session_state.last_update = datetime.now().strftime("%H:%M:%S")
                st.rerun()
            else:
                st.error("❌ Falha ao buscar dados. Tente em 30 segundos.")

    # --- PROCESSAMENTO ---
    if not data_to_use:
        is_live = False
        spot = 6700.0
        
        strikes_demo = [6500, 6550, 6600, 6650, 6700, 6750, 6800, 6850, 6900]
        gex_demo = [-120e6, -50e6, -200e6, -80e6, 10e6, 40e6, 180e6, 90e6, 30e6]
        df = pd.DataFrame({'Strike': strikes_demo, 'GEX': gex_demo, 'Date': '240315'})
        agg = df
        levels = {
            'zg': 6680.0, 'cw': 6800.0, 'pw': 6600.0, 'vt': 6640.0,
            'l1': 6850.0, 'c1': 6650.0, 'c4': 6500.0,
            'cw_0dte': 6750.0, 'pw_0dte': 6650.0
        }
        st.markdown('<div class="offline-banner">🟡 MODO DEMO. Clique em "PROCESSAR" para dados reais.</div>', unsafe_allow_html=True)
    else:
        spot = float(data_to_use["data"]["last"])
        df = pd.DataFrame(data_to_use["data"]["options"])
        
        df = df.rename(columns={
            'strike': 'Strike',
            'type': 'Type',
            'iv': 'iv',
            'open_interest': 'open_interest'
        })
        
        for col in ["iv", "open_interest"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        df = df.dropna(subset=['Strike', 'Type'])
        
        df['GEX'] = df['iv'] * df['open_interest'] * 100 * spot**2 * 0.01
        df.loc[df['Type'] == 'P', 'GEX'] *= -1
        
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        
        calculator = GEXCalculator(spot)
        levels = calculator.calculate_gex_levels(df)

    # --- BASIS/MT5 ---
    if usar_mt5 and mt5_price > 0:
        es_real = mt5_price
        basis = mt5_price - spot
        preco_oficial = es_fut if es_fut else spot
        divergencia = mt5_price - preco_oficial
        
        if abs(divergencia) > 5:
            st.markdown(f'<div class="divergence-alert high">🔴 DIVERGÊNCIA: MT5 ({mt5_price:.2f}) vs Oficial ({preco_oficial:.2f}) = {divergencia:+.2f} pts</div>', unsafe_allow_html=True)
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
    # RENDERIZAÇÃO
    # ========================================================================
    
    # ROW 1: ES, VIX e PLAYBOOK
    top_col1, top_col2, top_col3 = st.columns([1, 1, 2.5])
    
    with top_col1:
        es_price = spx_data.get('price', 0) if spx_data else 0
        es_change = spx_data.get('change_pct', 0) if spx_data else 0
        color_es = "#00FFAA" if es_change > 0 else "#ff6b6b"
        st.markdown(f"""
<div class="metric-card" style="border-left: 3px solid {color_es}; height: 100%;">
<div style="font-size:11px; color:#8A94A6; font-weight:700; letter-spacing: 1px;">ES FUTURES</div>
<div style="font-size:28px; font-weight:700; color:{color_es}; font-family:JetBrains Mono; margin-top: 10px;">{es_price:.0f}</div>
<div style="font-size:12px; color:#b0b8c8; margin-top: 5px;">Var: {es_change:+.2f}%</div>
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
        signal_gen = SignalGenerator(spot, basis, levels, spx_data)
        if vix_val and vix9d_val: signal_gen.add_vix_data(vix_val, vix9d_val)
        signal = signal_gen.generate()
        st.markdown(signal.to_html(), unsafe_allow_html=True)

    # ROW 2: PAINEL DE CÓPIA (5 COLUNAS COM C4)
    st.markdown("<h3 style='margin-top: 20px; font-size: 16px; color: #FFFFFF; font-weight: 600;'><span style='color:#00D4FF;'>📋 NÍVEIS PARA COPIAR (MT5):</span> Clique no ícone para copiar</h3>", unsafe_allow_html=True)
    
    cp_col1, cp_col2, cp_col3, cp_col4, cp_col5 = st.columns(5)
    
    with cp_col1:
        st.markdown("<div class='copy-panel-title'>MACRO WALLS</div>", unsafe_allow_html=True)
        st.caption("Call Wall Principal")
        st.code(f"{levels_adj['cw']:.2f}", language=None)
        st.caption("Put Wall Principal")
        st.code(f"{levels_adj['pw']:.2f}", language=None)
        
    with cp_col2:
        st.markdown("<div class='copy-panel-title'>INFLEXÃO & RISCO</div>", unsafe_allow_html=True)
        st.caption("Zero Gama (Divisa)")
        st.code(f"{levels_adj['zg']:.2f}", language=None)
        st.caption("Vol Trigger (Gatilho)")
        st.code(f"{levels_adj['vt']:.2f}", language=None)
        
    with cp_col3:
        st.markdown("<div class='copy-panel-title'>MICRO 0DTE</div>", unsafe_allow_html=True)
        st.caption("Call Wall 0DTE")
        st.code(f"{levels_adj['cw_0dte']:.2f}", language=None)
        st.caption("Put Wall 0DTE")
        st.code(f"{levels_adj['pw_0dte']:.2f}", language=None)
        
    with cp_col4:
        st.markdown("<div class='copy-panel-title'>ALVOS LONG</div>", unsafe_allow_html=True)
        st.caption("Nível L1 (Call Secundária)")
        st.code(f"{levels_adj['l1']:.2f}", language=None)
        st.caption("Nível C4 (Exaustão Put)")
        st.code(f"{levels_adj['c4']:.2f}", language=None)
        
    with cp_col5:
        st.markdown("<div class='copy-panel-title'>SUPORTE SECUNDÁRIO</div>", unsafe_allow_html=True)
        st.caption("Nível C1 (Suporte)")
        st.code(f"{levels_adj['c1']:.2f}", language=None)
        st.caption("Gamma Flip")
        st.code(f"{levels_adj.get('gamma_flip', levels_adj['zg']):.2f}", language=None)

    # ROW 3: Gráfico
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Gamma Exposure - S&P 500")
    
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
        x=alt.X('Strike:Q', title='Preço ES/S&P 500 (Ajustado MT5)', scale=alt.Scale(zero=False)),
        y=alt.Y('GEX:Q', title='Gamma Exposure ($)'),
        color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#ff6b6b')),
        tooltip=['Strike', 'GEX']
    ).properties(height=380)
    
    rules = alt.Chart(lines_data).mark_rule(strokeDash=[5,5], strokeWidth=2).encode(
        x='Strike:Q',
        color=alt.Color('Color:N', scale=None),
        tooltip=['Level', 'Strike']
    )
    st.altair_chart(chart + rules, use_container_width=True)

    # ROW 4: Pine Script
    with st.expander("🖥️ PINE SCRIPT (TradingView)"):
        pine_code = generate_pine_script(levels, basis, datetime.now())
        st.code(pine_code, language="pine")
        st.download_button(label="📥 Download .pine", data=pine_code, file_name=f"GEX_SPX_{datetime.now().strftime('%Y%m%d')}.pine", mime="text/plain")

    # Footer
    st.divider()
    mt5_status = f"📤 Pronto para exportar" if 'levels_adj' in locals() else "Aguardando dados"
    live_status = "ONLINE" if is_live else "STANDBY"
    st.markdown(f"""
<div style="text-align:center; font-size:11px; color:#5a6478; font-family:JetBrains Mono; text-transform: uppercase;">
GEX ULTRA ELITE PRO v5.3 | Status: {live_status} | MT5 Export: {mt5_status} | S&P 500 / ES Futures
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
