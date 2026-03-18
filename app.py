import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
import time
import yfinance as yf
import altair as alt

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GEX ULTRA ELITE PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0b0e14; }
    .header-container { background: rgba(20, 25, 35, 0.8); border-radius: 12px; padding: 25px; border: 1px solid rgba(0, 255, 170, 0.2); margin-bottom: 20px; }
    .metric-card { background: rgba(30, 35, 45, 0.6); border-radius: 10px; padding: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }
    .stButton>button { width: 100%; background: #FF4B4B !important; color: white !important; font-weight: bold; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---
if 'spx_data' not in st.session_state: st.session_state.spx_data = None

with st.sidebar:
    st.header("⚙️ Configurações")
    bridge_url = st.text_input("🔗 Link do Colab (Ngrok):", placeholder="https://xxxx.ngrok-free.app/spx")
    mt5_price = st.number_input("Preço ES no MT5:", value=5100.0, step=0.25)

# --- LOGICA DE SINCRONIZAÇÃO ---
if st.button("🚀 SINCRONIZAR MATRIZ INSTITUCIONAL (SPX)"):
    if not bridge_url:
        st.error("Cole o link do Colab na lateral!")
    else:
        url_limpa = bridge_url.strip()
        if not url_limpa.endswith("/spx"): url_limpa += "/spx"
        with st.spinner("Conectando à matriz CBOE..."):
            try:
                h = {"ngrok-skip-browser-warning": "true"}
                r = requests.get(url_limpa, headers=h, timeout=25)
                if r.status_code == 200:
                    st.session_state.spx_data = r.json()
                    st.session_state.last_update = time.strftime("%H:%M:%S")
                    st.success("✅ DADOS REAIS CARREGADOS!")
                else:
                    st.error(f"Erro {r.status_code}. Verifique o Colab.")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")

# --- PROCESSAMENTO ---
is_live = st.session_state.spx_data is not None
if is_live:
    data = st.session_state.spx_data
    spot = float(data["data"]["last"])
    df = pd.DataFrame(data["data"]["options"])
    # Extração de Strike e Cálculo de GEX Real
    df['Strike'] = df['option'].apply(lambda x: int(re.search(r'(\d{8})$', x).group(1))/1000)
    df['Type'] = df['option'].apply(lambda x: 'C' if 'C' in x else 'P')
    for col in ['gamma', 'open_interest']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['GEX'] = df['gamma'] * df['open_interest'] * 100 * spot**2 * 0.01
    df.loc[df['Type'] == 'P', 'GEX'] *= -1
    status_text = "● LIVE DATA"
else:
    # Dados Demo (Preço atual aproximado do SPX para não ficar feio)
    spot = 5140.0
    strikes = np.linspace(spot-100, spot+100, 50)
    df = pd.DataFrame({'Strike': strikes, 'GEX': np.random.normal(0, 1e7, 50)})
    status_text = "● DEMO MODE"

basis = mt5_price - spot
def adj(v): return v + basis

# --- HEADER ---
st.markdown(f"""
<div class="header-container">
    <h1 style='color:#00FFAA; margin:0;'>GEX ULTRA ELITE PRO</h1>
    <p style='color:#8A94A6; margin:0;'>{status_text} | BASIS: {basis:+.2f} | SYNC: {st.session_state.get('last_update', '--:--')}</p>
</div>
""", unsafe_allow_html=True)

# --- PAINEL DE NÍVEIS (Calculados) ---
p1, p2, p3, p4 = st.columns(4)
# Cálculo simples para exemplo (na live ele usa a matriz real)
zg = spot if not is_live else df.iloc[(df['GEX']).abs().argsort()[:1]]['Strike'].values[0]

with p1: 
    st.caption("MACRO WALLS"); st.code(f"{adj(zg+40):.2f}\n{adj(zg-40):.2f}")
with p2:
    st.caption("INFLEXÃO"); st.code(f"{adj(zg):.2f}\n{adj(zg-12):.2f}")
with p3:
    st.caption("0DTE"); st.code(f"{adj(spot+8):.2f}\n{adj(spot-8):.2f}")
with p4:
    st.caption("S/R"); st.code(f"{adj(spot+20):.2f}\n{adj(spot-20):.2f}")

# --- GRÁFICO ---
chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('Strike:Q', scale=alt.Scale(zero=False)),
    y='GEX:Q',
    color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#FF4B4B'))
).properties(height=350)
st.altair_chart(chart, use_container_width=True)
