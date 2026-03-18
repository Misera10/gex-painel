import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
import time
import yfinance as yf
import altair as alt
from datetime import datetime

# ============================================================================
# DESIGN PREMIUM (CSS DO SEU LOCAL)
# ============================================================================
st.set_page_config(page_title="GEX ULTRA ELITE PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;700;900&display=swap');
.stApp { background: #0b0e14; font-family: 'Inter', sans-serif; }
.header-container {
    background: linear-gradient(90deg, rgba(11, 14, 20, 0.9) 0%, rgba(26, 31, 46, 0.7) 100%), 
                url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2000&auto=format&fit=crop') center/cover;
    border-radius: 12px; padding: 30px; border: 1px solid rgba(0, 255, 170, 0.2); margin-bottom: 20px;
}
.metric-card { background: rgba(20, 25, 35, 0.8); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 15px; text-align: center; }
.playbook-container { background: rgba(15, 20, 28, 0.95); border-radius: 10px; padding: 20px; border: 1px solid rgba(255,255,255,0.05); }
.copy-panel { background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); }
.stButton>button { width: 100%; background: #FF4B4B !important; color: white !important; font-weight: bold; border-radius: 5px; border: none; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LÓGICA DE DADOS (DEMO VS REAL)
# ============================================================================
if 'spx_data' not in st.session_state: st.session_state.spx_data = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    bridge_url = st.text_input("🔗 Link do Colab (Ngrok):", placeholder="https://xxxx.ngrok-free.app/spx")
    mt5_price = st.number_input("Preço ES no MT5:", value=5100.0, step=0.25)
    range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)

# Dados de Mercado Reais (yfinance)
@st.cache_data(ttl=60)
def get_market():
    try:
        spy = yf.Ticker("SPY").history(period="1d")['Close'].iloc[-1]
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        return spy, vix
    except: return 5100.0, 15.0

spy_val, vix_val = get_market()

# --- HEADER ---
is_live = st.session_state.spx_data is not None
st.markdown(f"""
<div class="header-container">
    <h1 style='color:#00FFAA; margin:0; font-family:JetBrains Mono;'>GEX ULTRA ELITE PRO</h1>
    <p style='color:#8A94A6; margin:0;'>SPX EXCLUSIVE • PLAYBOOK TÁTICO • {"LIVE" if is_live else "DEMO MODE"}</p>
</div>
""", unsafe_allow_html=True)

# --- BOTÃO DE SINCRONIZAÇÃO ---
if st.button("🚀 SINCRONIZAR MATRIZ INSTITUCIONAL (SPX)"):
    if not bridge_url: st.warning("Insira o link do Colab na lateral!")
    else:
        with st.spinner("Conectando..."):
            try:
                h = {"ngrok-skip-browser-warning": "true"}
                r = requests.get(bridge_url.strip(), headers=h, timeout=20)
                if r.status_code == 200:
                    st.session_state.spx_data = r.json()
                    st.rerun()
            except Exception as e: st.error(f"Falha: {e}")

# --- PROCESSAMENTO ---
if is_live:
    data = st.session_state.spx_data
    spot = float(data["data"]["last"])
    df_raw = pd.DataFrame(data["data"]["options"])
    # (Adicione sua lógica real de cálculo de Gamma aqui se necessário)
else:
    spot = 5100.0
    # Dados Demo para o gráfico não abrir vazio
    df_raw = pd.DataFrame({'Strike': np.linspace(5000, 5200, 50), 'GEX': np.random.normal(0, 1e7, 50)})

basis = mt5_price - spot
def adj(v): return v + basis

# ============================================================================
# LAYOUT DAS LINHAS (IGUAL AO SEU PRINT LOCAL)
# ============================================================================

# Linha 1: Métricas e Playbook
c1, c2, c3 = st.columns([1, 1, 2.5])
with c1: st.markdown(f"<div class='metric-card'><small>SPY PRICE</small><br><b style='font-size:22px; color:#FF4B4B;'>${spy_val:.2f}</b></div>", unsafe_allow_html=True)
with c2: st.markdown(f"<div class='metric-card'><small>VIX SPOT</small><br><b style='font-size:22px; color:#FF4B4B;'>{vix_val:.2f}</b></div>", unsafe_allow_html=True)
with c3:
    color = "#00FFAA" if mt5_price > adj(spot) else "#FF4B4B"
    st.markdown(f"""<div class='playbook-container' style='border-left: 5px solid {color};'>
    <h3 style='margin:0; color:{color};'>LONG 📈</h3><p style='margin:0; font-size:12px;'>Aguardar pullback e comprar suporte em {adj(spot):.2f}</p>
    </div>""", unsafe_allow_html=True)

# Linha 2: Painéis de Cópia
st.write("---")
p1, p2, p3, p4 = st.columns(4)
with p1: 
    st.markdown("<div class='copy-panel'><small>MACRO WALLS</small></div>", unsafe_allow_html=True)
    st.code(f"{adj(spot+50):.2f}"); st.code(f"{adj(spot-50):.2f}")
with p2:
    st.markdown("<div class='copy-panel'><small>INFLEXÃO & RISCO</small></div>", unsafe_allow_html=True)
    st.code(f"{adj(spot):.2f}"); st.code(f"{adj(spot-15):.2f}")
with p3:
    st.markdown("<div class='copy-panel'><small>0DTE</small></div>", unsafe_allow_html=True)
    st.code(f"{adj(spot+10):.2f}"); st.code(f"{adj(spot-10):.2f}")
with p4:
    st.markdown("<div class='copy-panel'><small>S/R</small></div>", unsafe_allow_html=True)
    st.code(f"{adj(spot+25):.2f}"); st.code(f"{adj(spot-25):.2f}")

# Linha 3: Gráfico
st.subheader("📊 Perfil Institucional (Gamma Exposure)")
chart = alt.Chart(df_raw).mark_bar().encode(
    x=alt.X('Strike:Q', scale=alt.Scale(zero=False)),
    y='GEX:Q',
    color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#FF4B4B'))
).properties(height=350)
st.altair_chart(chart, use_container_width=True)
