"""
GEX ULTRA ELITE TERMINAL PRO (Internal v6.0)
Motor: Yahoo Finance (Anti-Block) | Design: Elite v5.3 Original
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import altair as alt
import re
from datetime import datetime
from scipy.stats import norm

# ============================================================================
# DESIGN ELITE v5.3 (CSS ORIGINAL REPLICADO 1:1)
# ============================================================================
st.set_page_config(page_title="GEX ULTRA ELITE PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');

.stApp { background: linear-gradient(135deg, #0b0e14 0%, #131824 100%); font-family: 'Inter', sans-serif; }

.header-container {
    background: linear-gradient(90deg, rgba(11, 14, 20, 0.9) 0%, rgba(26, 31, 46, 0.7) 100%), 
                url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2000&auto=format&fit=crop') center/cover;
    border-radius: 16px; padding: 35px 30px; margin-bottom: 25px; border: 1px solid rgba(0, 255, 170, 0.2); box-shadow: 0 15px 35px rgba(0,0,0,0.4);
}

.gradient-title { 
    background: linear-gradient(90deg, #00FFAA, #00D4FF); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    font-weight: 800; font-size: 36px; margin: 0; font-family: 'JetBrains Mono', monospace;
}

.metric-card { 
    background: rgba(20, 25, 35, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); 
    border-radius: 12px; padding: 20px; text-align: center; backdrop-filter: blur(12px);
    transition: all 0.3s ease;
}

.playbook-container {
    background: rgba(15, 20, 28, 0.95); border-radius: 12px; padding: 25px; border-left: 6px solid #00FFAA;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05);
}

.copy-panel-title {
    font-size: 13px; color: #8A94A6; text-transform: uppercase; font-weight: 800; 
    border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 5px; letter-spacing: 1px;
}

.stButton>button { 
    width: 100%; background: linear-gradient(90deg, #00FFAA, #00D4FF) !important; 
    color: black !important; font-weight: 900; border-radius: 8px; height: 3.5em; 
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MOTOR MATEMÁTICO (GAMMA CALCULATION)
# ============================================================================
def calculate_gamma(S, K, T, r, iv):
    if T <= 0 or iv <= 0: return 0
    d1 = (np.log(S / K) + (r + 0.5 * iv**2) * T) / (iv * np.sqrt(T))
    gamma = norm.pdf(d1) / (S * iv * np.sqrt(T))
    return gamma

def fetch_yahoo_gex():
    try:
        spx = yf.Ticker("^SPX")
        spot = spx.history(period="1d")['Close'].iloc[-1]
        expirations = spx.options[:2] # Pega 0DTE e a próxima
        
        all_data = []
        for exp in expirations:
            opt = spx.option_chain(exp)
            # T em anos (simplificado para intraday)
            days_to_exp = (datetime.strptime(exp, '%Y-%m-%d') - datetime.now()).days
            T = max(days_to_exp, 0.5) / 365.0
            r = 0.045 # Risk-free rate
            
            for _, row in opt.calls.iterrows():
                g = calculate_gamma(spot, row['strike'], T, r, row['impliedVolatility'])
                all_data.append({'Strike': row['strike'], 'GEX': g * row['openInterest'] * 100 * spot**2 * 0.01, 'Exp': exp, 'Type': 'C'})
            for _, row in opt.puts.iterrows():
                g = calculate_gamma(spot, row['strike'], T, r, row['impliedVolatility'])
                all_data.append({'Strike': row['strike'], 'GEX': g * row['openInterest'] * 100 * spot**2 * 0.01 * -1, 'Exp': exp, 'Type': 'P'})
        
        return spot, pd.DataFrame(all_data)
    except: return None, None

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================
if 'data' not in st.session_state: st.session_state.data = None

with st.sidebar:
    st.header("⚙️ Configurações MT5")
    mt5_price = st.number_input("💻 Preço do ES no seu MT5:", value=5100.0, step=0.25)
    range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)

# O BOTÃO AGORA APONTA PRO YAHOO
if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL (SINCRONIZAR YAHOO)", use_container_width=True):
    with st.spinner("Calculando Gamma via Yahoo Engine..."):
        spot, df = fetch_yahoo_gex()
        if df is not None:
            st.session_state.data = (spot, df)
            st.session_state.last_update = datetime.now().strftime("%H:%M:%S")

# --- RENDERIZAÇÃO ---
update_time = st.session_state.get('last_update', '--:--:--')
st.markdown(f"""
<div class="header-container">
    <div><h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1><p style='color:#8A94A6; margin:0;'>v6.0 YAHOO ENGINE • SYNC: {update_time}</p></div>
</div>
""", unsafe_allow_html=True)

if st.session_state.data:
    spot, df = st.session_state.data
    basis = mt5_price - spot
    def adj(v): return v + basis

    agg = df.groupby('Strike')['GEX'].sum().reset_index()
    zg = agg.iloc[(agg['GEX']).abs().argsort()[:1]]['Strike'].values[0]
    cw, pw = agg.loc[agg['GEX'].idxmax(), 'Strike'], agg.loc[agg['GEX'].idxmin(), 'Strike']
    
    # ROW 1: METRICS & PLAYBOOK
    col1, col2, col3 = st.columns([1, 1, 2.5])
    with col1: st.markdown(f"<div class='metric-card'><small style='color:#8A94A6'>SPX SPOT</small><br><b style='color:#00FFAA; font-size:24px;'>${spot:,.2f}</b></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='metric-card'><small style='color:#8A94A6'>BASIS ES</small><br><b style='color:#00D4FF; font-size:24px;'>{basis:+.2f}</b></div>", unsafe_allow_html=True)
    
    viés = "LONG 📈" if mt5_price > adj(zg) else "SHORT 📉"
    cor = "#00FFAA" if "LONG" in viés else "#ff4b4b"
    with col3:
        st.markdown(f"""<div class="playbook-container" style="border-left-color:{cor};">
            <h2 style="margin:0; color:{cor}; font-family:JetBrains Mono;">{viés}</h2>
            <p style="margin:0; color:#8A94A6;">ZG: {adj(zg):.2f} | Alvo: {adj(cw if cor=="#00FFAA" else pw):.2f}</p>
        </div>""", unsafe_allow_html=True)

    # ROW 2: PANÉIS DE CÓPIA
    st.write("---")
    p1, p2, p3, p4 = st.columns(4)
    with p1: 
        st.markdown("<div class='copy-panel-title'>MACRO WALLS</div>", unsafe_allow_html=True)
        st.code(f"{adj(cw):.2f}\n{adj(pw):.2f}")
    with p2:
        st.markdown("<div class='copy-panel-title'>INFLEXÃO</div>", unsafe_allow_html=True)
        st.code(f"{adj(zg):.2f}\n{adj(zg-15):.2f}")
    with p3:
        st.markdown("<div class='copy-panel-title'>0DTE</div>", unsafe_allow_html=True)
        exp0 = df['Exp'].iloc[0]
        df0 = df[df['Exp'] == exp0].groupby('Strike')['GEX'].sum().reset_index()
        st.code(f"{adj(df0.loc[df0['GEX'].idxmax(), 'Strike']):.2f}\n{adj(df0.loc[df0['GEX'].idxmin(), 'Strike']):.2f}")
    with p4:
        st.markdown("<div class='copy-panel-title'>S/R</div>", unsafe_allow_html=True)
        st.code(f"{adj(cw-10):.2f}\n{adj(zg-15):.2f}")

    # ROW 3: GRÁFICO
    st.markdown("<br>", unsafe_allow_html=True)
    mask = (agg['Strike'] > spot * (1 - range_pct/100)) & (agg['Strike'] < spot * (1 + range_pct/100))
    chart_data = agg[mask].copy()
    chart_data['Strike'] = chart_data['Strike'] + basis
    
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Strike:Q', scale=alt.Scale(zero=False), title="Preço Ajustado ao MT5"),
        y=alt.Y('GEX:Q', title="Gamma Exposure"),
        color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#ff4b4b'))
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

else:
    st.info("Pressione o botão para buscar dados do Yahoo Finance e calcular a matriz.")
