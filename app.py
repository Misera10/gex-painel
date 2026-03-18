"""
GEX ULTRA ELITE TERMINAL PRO (Internal v5.6 - Full Elite Bridge)
Features: Replicating Local Design | Cloud Ready Bridge
"""

import sys
import os
import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import re
import html
import time
import yfinance as yf
import altair as alt
from datetime import datetime

# ============================================================================
# 1. CONFIGURAÇÕES & DESIGN IMAGÉTICO (ORIGINAL v5.3)
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

.stApp { background: linear-gradient(135deg, #0b0e14 0%, #131824 100%); font-family: 'Inter', sans-serif; }

.header-container {
    background: linear-gradient(90deg, rgba(11, 14, 20, 0.9) 0%, rgba(26, 31, 46, 0.7) 100%), 
                url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2000&auto=format&fit=crop') center/cover;
    border-radius: 16px; padding: 35px 30px; margin-bottom: 25px; border: 1px solid rgba(0, 255, 170, 0.2); box-shadow: 0 15px 35px rgba(0,0,0,0.4);
}

.gradient-title { background: linear-gradient(90deg, #00FFAA, #00D4FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 36px; margin: 0; font-family: 'JetBrains Mono', monospace; }
.header-subtitle { color: #8A94A6; font-size: 13px; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 2px; }

.metric-card { background: rgba(20, 25, 35, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 20px; text-align: center; backdrop-filter: blur(12px); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
.metric-card:hover { transform: translateY(-3px); border-color: rgba(0, 255, 170, 0.3); }

.playbook-container { background: rgba(15, 20, 28, 0.95); border-radius: 12px; padding: 25px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
.playbook-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }
.playbook-item { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); }

.copy-panel-title { font-size: 13px; color: #8A94A6; text-transform: uppercase; font-weight: 800; margin-top: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 5px; }
.offline-banner { background: rgba(255, 204, 0, 0.1); border: 1px solid #FFCC00; color: #FFCC00; padding: 12px; border-radius: 8px; text-align: center; font-weight: 600; margin-bottom: 15px; }

.stButton>button { width: 100%; background: linear-gradient(90deg, #00FFAA, #00D4FF) !important; color: black !important; font-weight: bold; border-radius: 8px; height: 3em; }
div[data-testid="stCodeBlock"] { margin-bottom: -10px !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. LÓGICA DE DADOS & CÁLCULO (INTEGRAÇÃO BRIDGE)
# ============================================================================

# Inicialização do Session State (Ponto Chave para Exibir Antes de Clicar)
if 'spx_data' not in st.session_state: st.session_state.spx_data = None
if 'last_update' not in st.session_state: st.session_state.last_update = None
if 'mt5_basis' not in st.session_state: st.session_state.mt5_basis = 0.0

@st.cache_data(ttl=300)
def fetch_yf_metrics():
    try:
        spy = yf.Ticker("SPY").history(period="2d")
        vix = yf.Ticker("^VIX").history(period="2d")
        vix9d = yf.Ticker("^VIX9D").history(period="2d")
        return {
            'spy': spy['Close'].iloc[-1],
            'spy_chg': ((spy['Close'].iloc[-1] - spy['Close'].iloc[-2]) / spy['Close'].iloc[-2]) * 100,
            'vix': vix['Close'].iloc[-1],
            'vix9d': vix9d['Close'].iloc[-1]
        }
    except: return None

class GEXCalculator:
    def __init__(self, spot): self.spot = spot
    def process(self, df):
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        zg = self._find_zg(agg['Strike'].values, agg['GEX'].values)
        cw = agg.loc[agg['GEX'].idxmax(), 'Strike']
        pw = agg.loc[agg['GEX'].idxmin(), 'Strike']
        vt = agg[(agg['Strike'] > min(pw, zg)) & (agg['Strike'] < max(pw, zg))]['Strike'].mean() or pw
        l1 = agg.nlargest(2, 'GEX')['Strike'].iloc[-1]
        c1 = agg[agg['Strike'] > pw].nsmallest(1, 'GEX')['Strike'].iloc[0] if not agg[agg['Strike'] > pw].empty else pw
        cw_0 = agg.nlargest(1, 'GEX')['Strike'].iloc[0] # Exemplo Simplificado 0DTE
        return {'zg': zg, 'cw': cw, 'pw': pw, 'vt': vt, 'l1': l1, 'c1': c1, 'cw_0': cw_0, 'pw_0': pw}
    def _find_zg(self, x, y):
        s = np.sign(y); z = np.where(s[1:] != s[:-1])[0]
        if len(z)==0: return self.spot
        idx = z[0]; x1, x2, y1, y2 = x[idx], x[idx+1], y[idx], y[idx+1]
        return x1 - y1 * (x2 - x1) / (y2 - y1)

# ============================================================================
# 3. INTERFACE PRINCIPAL (O VISUAL DO SEU LOCAL)
# ============================================================================

# --- SIDEBAR (COM ADIÇÃO DO LINK) ---
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # 🌟 NOVA FUNCIONALIDADE: ADIÇÃO DO LINK BRIDGE 🌟
    st.markdown("""<div style="background: rgba(0,212,255,0.1); padding: 10px; border-radius: 8px; border: 1px solid #00D4FF; margin-bottom: 10px; color: #00D4FF; font-size: 13px;">🔗 PONTE INSTITUCIONAL (GOOGLE COLAB)</div>""", unsafe_allow_html=True)
    bridge_url = st.text_input("Cole o link Ngrok do Colab:", placeholder="https://xxxx.ngrok-free.app/spx")
    
    range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)
    
    st.divider()
    st.markdown("""<div style="background: rgba(0,212,255,0.1); padding: 10px; border-radius: 8px; border-left: 3px solid #00D4FF; color: #00D4FF; font-size: 14px;">📊 MESA PROP MT5</div>""", unsafe_allow_html=True)
    mt5_input = st.number_input("💻 Preço do ES no seu MT5:", value=5100.0, step=0.25)
    usar_mt5 = st.toggle("✅ Usar MT5 para ajustar níveis", value=True)

# --- CABEÇALHO ---
is_live = st.session_state.spx_data is not None
status_html = "<span style='color:#00FFAA'>● LIVE</span>" if is_live else "<span style='color:#FFCC00'>● STANDBY / DEMO</span>"
st.markdown(f"""
<div class="header-container"><div style="display:flex; justify-content:space-between; align-items:center;"><div><h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1><p class='header-subtitle'>SPX EXCLUSIVE • PLAYBOOK TÁTICO • MT5 SYNC (BRIDGE)</p></div>
<div style="text-align:right; color:#8A94A6; font-family:'JetBrains Mono'; font-size:12px; background:rgba(0,0,0,0.4); padding:10px; border-radius:8px;"><div>STATUS: {status_html}</div><div>UPDATE: {st.session_state.last_update or '--:--:--'}</div></div></div></div>
""", unsafe_allow_html=True)

# --- BANNER DEMO (Se não estiver conectado) ---
if not is_live:
    st.markdown('<div class="offline-banner">🟡 MODO DEMO: Exibindo perfil estrutural. Cole o link na barra lateral e pressione Sincronizar para dados reais.</div>', unsafe_allow_html=True)

# --- BOTÃO DE SINCRONIZAÇÃO (Principal) ---
if st.button("🚀 SINCRONIZAR MATRIZ INSTITUCIONAL (SPX)", type="primary"):
    if not bridge_url: st.error("Insira o link Ngrok na barra lateral!")
    else:
        # Garante que o link termina com /spx
        url_limpa = bridge_url.strip()
        if not url_limpa.endswith("/spx"): url_limpa += "/spx"
        
        with st.spinner("Conectando à Ponte Google via Cloud..."):
            try:
                # O segredo para furar o bloqueio do Ngrok
                h = {"ngrok-skip-browser-warning": "true"}
                r = requests.get(url_limpa, headers=h, timeout=30)
                if r.status_code == 200:
                    st.session_state.spx_data = r.json()
                    st.session_state.last_update = time.strftime("%H:%M:%S")
                    st.rerun() # Atualiza a tela para carregar os novos dados
                else: st.error(f"Erro na ponte: {r.status_code}")
            except Exception as e: st.error(f"Falha de conexão: {e}")

# ============================================================================
# 4. DASHBOARD - EXIBIÇÃO AUTOMÁTICA (MANTENDO SEU DESIGN)
# ============================================================================

# Lógica de Dados (Demo vs Real)
if not is_live:
    spot = 5100.0
    strikes_demo = np.arange(4900, 5301, 5)
    gex_demo = (strikes_demo - zg_demo) * 1e5 + np.random.normal(0, 1e6, len(strikes_demo)) # Exemplo de GEX
    df_raw = pd.DataFrame({'Strike': strikes_demo, 'GEX': gex_demo, 'Type': 'C'}) # Estrutura demo
    levels = {'zg': 5080.0, 'cw': 5200.0, 'pw': 5000.0, 'vt': 5040.0, 'l1': 5250.0, 'c1': 5050.0, 'cw_0': 5150.0}
    agg = df_raw
else:
    data = st.session_state.spx_data
    spot = float(data["data"]["last"])
    df_raw = pd.DataFrame(data["data"]["options"])
    # Processamento Gamma Real (Conforme v5.3 anterior)
    df_raw['Strike'] = df_raw['option'].apply(lambda x: int(re.search(r'(\d{8})$', x).group(1))/1000 if re.search(r'(\d{8})$', x) else 0)
    df_raw['Type'] = df_raw['option'].apply(lambda x: 'C' if 'C' in x else 'P')
    for col in ['gamma', 'open_interest']: df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)
    df_raw['GEX'] = df_raw['gamma'] * df_raw['open_interest'] * 100 * spot**2 * 0.01
    df_raw.loc[df_raw['Type'] == 'P', 'GEX'] *= -1
    
    calc = GEXCalculator(spot); levels = calc.process(df_raw)
    agg = df_raw.groupby('Strike')['GEX'].sum().reset_index()

# Lógica Basis MT5
basis = (mt5_input - spot) if usar_mt5 else 0.0
def adj(val): return float(val) + basis

# YAHOO FINANCE & PLAYBOOK (Filtros e Sinais)
spy_m = fetch_yf_metrics() or {'spy': 0, 'spy_chg': 0, 'vix': 0, 'vix9d': 0}

# --- ROW 1: SPY, VIX, PLAYBOOK (Replicando seu Layout) ---
c1, c2, c3 = st.columns([1, 1, 2.5])
with c1:
    color_spy = "#00FFAA" if spy_m['spy_chg'] > 0 else "#ff6b6b"
    st.markdown(f"<div class='metric-card' style='border-left: 3px solid {color_spy};'>SPY (ETF)<br><b style='color:{color_spy}; font-size:28px; font-family:JetBrains Mono;'>${spy_m['spy']:.2f}</b><br><small style='color:{color_spy}'>{spy_m['spy_chg']:+.2f}%</small></div>", unsafe_allow_html=True)
with c2:
    vix_color = "#ff6b6b" if spy_m['vix'] > 20 else "#00FFAA"
    st.markdown(f"<div class='metric-card' style='border-left: 3px solid {vix_color};'>VIX SPOT<br><b style='color:{vix_color}; font-size:28px; font-family:JetBrains Mono;'>{spy_m['vix']:.2f}</b><br><small style='color:#8A94A6'>VIX9D: {spy_m['vix9d']:.2f}</small></div>", unsafe_allow_html=True)

with c3:
    is_long = mt5_input > adj(levels['zg'])
    color_p = "#00FFAA" if is_long else "#ff6b6b"
    # Lógica simplificada de PLAYBOOK (Adicione sua lógica real aqui)
    entry = f"{adj(levels['zg']):.2f} (ZG)" if is_long else f"{adj(levels['vt']):.2f} (VT)"
    targets = f"{adj(levels['l1']):.2f} | {adj(levels['cw']):.2f}"
    stop = adj(levels['zg']-20)
    
    st.markdown(f"""
    <div class="playbook-container" style="border-left: 6px solid {color_p};">
    <small style="color:#8A94A6;">PLANO DE VOO TÁTICO</small><br>
    <b style="color:{color_p}; font-size:32px;">{("LONG 📈" if is_long else "SHORT 📉")}</b>
    <div class="playbook-grid">
    <div class="playbook-item"><small style="color:#8A94A6">Gatilho (Entrada)</small><br><b>{entry}</b></div>
    <div class="playbook-item"><small style="color:#8A94A6">🎯 Alvos (Take Profit)</small><br><b>{targets}</b></div>
    <div class="playbook-item"><small style="color:#8A94A6">🛑 Stop (Invalidação)</small><br><b>{stop:.2f}</b></div>
    </div></div>
    """, unsafe_allow_html=True)

# --- ROW 2: EXPORTAÇÃO (Seus 4 Painéis de Cópia Rápida) ---
st.markdown("<h3 style='margin-top: 20px; font-size: 16px;'><span style='color:#00D4FF;'>📋 EXPORTAÇÃO:</span> Ajustadas para MT5.</h3>", unsafe_allow_html=True)
cp1, cp2, cp3, cp4 = st.columns(4)
with cp1:
    st.caption("MACRO WALLS"); st.code(f"{adj(levels['cw']):.2f} (CW)", language=None); st.code(f"{adj(levels['pw']):.2f} (PW)", language=None)
with cp2:
    st.caption("INFLEXÃO & RISCO"); st.code(f"{adj(levels['zg']):.2f} (ZG)", language=None); st.code(f"{adj(levels['vt']):.2f} (VT)", language=None)
with cp3:
    st.caption("MICRO 0DTE"); st.code(f"{adj(levels['cw_0']):.2f} (CW)", language=None); st.code(f"{adj(levels['pw_0']):.2f} (PW)", language=None) # Ajustado pw_0
with cp4:
    st.caption("SUPORTE/RESISTÊNCIA"); st.code(f"{adj(levels['l1']):.2f} (L1)", language=None); st.code(f"{adj(levels['c1']):.2f} (C1)", language=None)

# --- ROW 3: GRÁFICO ALTAIR (O Design Institucional) ---
st.subheader("📊 Perfil Institucional (Gamma Exposure)")
mask = (agg['Strike'] > spot * (1 - range_pct/100)) & (agg['Strike'] < spot * (1 + range_pct/100))
chart_data = agg[mask].copy()
chart_data['Strike_Adj'] = chart_data['Strike'] + basis # Gráfico segue MT5

chart = alt.Chart(chart_data).mark_bar().encode(
    x=alt.X('Strike_Adj:Q', title='Ativo (MT5 Ajustado)', scale=alt.Scale(zero=False)),
    y=alt.Y('GEX:Q', title='Exposição ($)', axis=alt.Axis(format=".1s")),
    color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#ff6b6b')),
    tooltip=['Strike_Adj', 'GEX']
).properties(height=380)

# Linhas de Referência (ZG, MT5 Price)
lines = alt.Chart(pd.DataFrame({'x': [adj(levels['zg']), mt5_input]})).mark_rule(color='white', strokeDash=[5,5]).encode(x='x:Q')
st.altair_chart(chart + lines, use_container_width=True)

# --- ROW 4: PINE SCRIPT ---
with st.expander("🖥️ PINE SCRIPT (TradingView)"):
    st.code(f'indicator("GEX Levels", overlay=true)\nplot({adj(lv["zg"]):.2f}, "ZG", color.white)\nplot({adj(lv["cw"]):.2f}, "CW", color.red)', language="pine")
