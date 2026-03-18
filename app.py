"""
GEX ULTRA ELITE TERMINAL PRO (v7.0)
Design Elite v5.3 Original Replicado 1:1 | Sem menções ao Yahoo na UI | Motor Interno Estável
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
    border-radius: 12px; padding: 15px; text-align: center; backdrop-filter: blur(12px);
}

.playbook-container {
    background: rgba(15, 20, 28, 0.95); border-radius: 12px; padding: 25px; border-left: 6px solid #00FFAA;
    border: 1px solid rgba(255,255,255,0.05);
}

.copy-panel-title {
    font-size: 13px; color: #8A94A6; text-transform: uppercase; font-weight: 800; 
    border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 5px;
}

/* BOTÃO VERDE/AZUL ORIGINAL */
.stButton>button { 
    width: 100%; background: linear-gradient(90deg, #00FFAA, #00D4FF) !important; 
    color: black !important; font-weight: 900; border-radius: 8px; height: 3.5em; 
}

.filter-badge {
    padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-right: 5px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MOTOR MATEMÁTICO INTERNO (Black-Scholes)
# ============================================================================
def calculate_gamma(S, K, T, r, iv):
    if T <= 0 or iv <= 0: return 0
    d1 = (np.log(S / K) + (r + 0.5 * iv**2) * T) / (iv * np.sqrt(T))
    gamma = norm.pdf(d1) / (S * iv * np.sqrt(T))
    return gamma

def fetch_market_data_internal():
    try:
        spx = yf.Ticker("^SPX")
        spot = spx.history(period="1d")['Close'].iloc[-1]
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        spy_hist = yf.Ticker("SPY").history(period="2d")
        spy_price = spy_hist['Close'].iloc[-1]
        spy_change = ((spy_price / spy_hist['Close'].iloc[-2]) - 1) * 100
        
        expirations = spx.options[:2]
        all_data = []
        for exp in expirations:
            opt = spx.option_chain(exp)
            T = max((datetime.strptime(exp, '%Y-%m-%d') - datetime.now()).days, 0.5) / 365.0
            for _, row in opt.calls.iterrows():
                g = calculate_gamma(spot, row['strike'], T, 0.045, row['impliedVolatility'])
                all_data.append({'Strike': row['strike'], 'GEX': g * row['openInterest'] * 100 * spot**2 * 0.01, 'Exp': exp, 'Type': 'C'})
            for _, row in opt.puts.iterrows():
                g = calculate_gamma(spot, row['strike'], T, 0.045, row['impliedVolatility'])
                all_data.append({'Strike': row['strike'], 'GEX': g * row['openInterest'] * 100 * spot**2 * 0.01 * -1, 'Exp': exp, 'Type': 'P'})
        
        return {
            'spot': spot, 'df': pd.DataFrame(all_data), 
            'vix': vix, 'spy_price': spy_price, 'spy_change': spy_change
        }
    except: return None

# ============================================================================
# INTERFACE
# ============================================================================
if 'market' not in st.session_state: st.session_state.market = None

with st.sidebar:
    st.header("⚙️ Configurações MT5")
    mt5_price = st.number_input("💻 Preço ES no MT5:", value=5100.0, step=0.25)
    range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)

# BOTÃO COM TEXTO LIMPO (SEM MENCIONAR YAHOO)
if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL (SINCRONIZAR)", use_container_width=True):
    with st.spinner("Sincronizando dados de mercado..."):
        res = fetch_market_data_internal()
        if res:
            st.session_state.market = res
            st.session_state.update_time = datetime.now().strftime("%H:%M:%S")

# Header
st.markdown(f"""<div class="header-container"><div><h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1>
<p style='color:#8A94A6; margin:0;'>v7.0 • DESIGN v5.3 • SYNC: {st.session_state.get('update_time', '--:--')}</p></div></div>""", unsafe_allow_html=True)

if st.session_state.market:
    m = st.session_state.market
    spot, df, basis = m['spot'], m['df'], mt5_price - m['spot']
    def adj(v): return v + basis

    agg = df.groupby('Strike')['GEX'].sum().reset_index()
    zg = agg.iloc[(agg['GEX']).abs().argsort()[:1]]['Strike'].values[0]
    cw, pw = agg.loc[agg['GEX'].idxmax(), 'Strike'], agg.loc[agg['GEX'].idxmin(), 'Strike']

    # ROW 1: METRICS
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f"<div class='metric-card'><small style='color:#8A94A6'>SPX SPOT</small><br><b style='color:#00FFAA; font-size:22px;'>${spot:,.2f}</b></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-card'><small style='color:#8A94A6'>BASIS ES</small><br><b style='color:#00D4FF; font-size:22px;'>{basis:+.2f}</b></div>", unsafe_allow_html=True)
    m3.markdown(f"<div class='metric-card'><small style='color:#8A94A6'>VIX</small><br><b style='color:{'#ff4b4b' if m['vix']>20 else '#00FFAA'}; font-size:22px;'>{m['vix']:.2f}</b></div>", unsafe_allow_html=True)
    m4.markdown(f"<div class='metric-card'><small style='color:#8A94A6'>SPY</small><br><b style='color:{'#00FFAA' if m['spy_change']>0 else '#ff4b4b'}; font-size:22px;'>{m['spy_change']:+.2f}%</b></div>", unsafe_allow_html=True)

    # PLAYBOOK COM CONFLUÊNCIA
    st.write("")
    viés = "LONG 📈" if mt5_price > adj(zg) else "SHORT 📉"
    conf = "ALTA ✅" if (viés == "LONG 📈" and m['spy_change'] > 0) or (viés == "SHORT 📉" and m['spy_change'] < 0) else "BAIXA ⚠️"
    cor = "#00FFAA" if "LONG" in viés else "#ff4b4b"
    
    st.markdown(f"""
    <div class="playbook-container" style="border-left-color:{cor};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h2 style="margin:0; color:{cor}; font-family:JetBrains Mono;">{viés}</h2>
            <div style="text-align:right;"><small style="color:#8A94A6;">CONFLUÊNCIA SPY</small><br><b style="color:{cor if conf=="ALTA ✅" else "#FFCC00"}">{conf}</b></div>
        </div>
        <div style="margin-top:10px;">
            <span class="filter-badge" style="background:rgba(0,212,255,0.1); color:#00D4FF; border:1px solid #00D4FF;">SPY ${m['spy_price']:.2f}</span>
            <span class="filter-badge" style="background:rgba(255,255,255,0.1); color:#FFF; border:1px solid #FFF;">ZG: {adj(zg):.2f}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # ROW 2: COPY PANELS
    st.write("---")
    p1, p2, p3, p4 = st.columns(4)
    with p1: st.markdown("<div class='copy-panel-title'>MACRO WALLS</div>", unsafe_allow_html=True); st.code(f"{adj(cw):.2f}\n{adj(pw):.2f}")
    with p2: st.markdown("<div class='copy-panel-title'>INFLEXÃO</div>", unsafe_allow_html=True); st.code(f"{adj(zg):.2f}\n{adj(zg-15):.2f}")
    with p3: 
        st.markdown("<div class='copy-panel-title'>0DTE</div>", unsafe_allow_html=True)
        df0 = df[df['Exp'] == df['Exp'].iloc[0]].groupby('Strike')['GEX'].sum().reset_index()
        st.code(f"{adj(df0.loc[df0['GEX'].idxmax(), 'Strike']):.2f}\n{adj(df0.loc[df0['GEX'].idxmin(), 'Strike']):.2f}")
    with p4: st.markdown("<div class='copy-panel-title'>S/R</div>", unsafe_allow_html=True); st.code(f"{adj(cw-10):.2f}\n{adj(zg-15):.2f}")

    # ROW 3: CHART
    mask = (agg['Strike'] > spot * (1 - range_pct/100)) & (agg['Strike'] < spot * (1 + range_pct/100))
    c_data = agg[mask].copy(); c_data['Strike'] = c_data['Strike'] + basis
    chart = alt.Chart(c_data).mark_bar().encode(
        x=alt.X('Strike:Q', scale=alt.Scale(zero=False)), y='GEX:Q',
        color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#ff4b4b'))
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

else: st.info("Sincronize para ativar o terminal.")
