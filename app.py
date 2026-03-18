"""
GEX ULTRA ELITE TERMINAL PRO (v6.0 - Yahoo Engine Edition)
Design v5.3 Original | Motor Black-Scholes Independente | Anti-Bloqueio
"""

import os
import json
import re
import time
import warnings
import pandas as pd
import numpy as np
import yfinance as yf
import altair as alt
import streamlit as st
from datetime import datetime, timedelta
from scipy.stats import norm

warnings.filterwarnings('ignore')

# ============================================================================
# CSS PREMIUM ORIGINAL (MANTIDO 100%)
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
.gradient-title { background: linear-gradient(90deg, #00FFAA, #00D4FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    font-weight: 800; font-size: 36px; margin: 0; font-family: 'JetBrains Mono', monospace; letter-spacing: -1px; }
.header-subtitle { color: #8A94A6; margin-top: 8px; font-size: 13px; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 2px; }
.metric-card { background: rgba(20, 25, 35, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 20px; text-align: center; backdrop-filter: blur(12px); transition: all 0.3s ease; }
.metric-card:hover { transform: translateY(-3px); border-color: rgba(0, 255, 170, 0.3); }
.playbook-container { background: rgba(15, 20, 28, 0.95); border-radius: 12px; padding: 25px; border: 1px solid rgba(255,255,255,0.05); }
.playbook-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }
.playbook-item { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); }
.copy-panel-title { font-size: 13px; color: #8A94A6; text-transform: uppercase; font-weight: 800; margin-top: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 5px; }
.stButton>button { background: linear-gradient(90deg, #00FFAA, #00D4FF) !important; color: black !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MOTOR MATEMÁTICO (BLACK-SCHOLES PARA GEX)
# ============================================================================
class YahooGEXEngine:
    @staticmethod
    def calculate_gamma(S, K, T, r, iv, type='call'):
        if T <= 0 or iv <= 0: return 0
        d1 = (np.log(S / K) + (r + 0.5 * iv**2) * T) / (iv * np.sqrt(T))
        gamma = norm.pdf(d1) / (S * iv * np.sqrt(T))
        return gamma

    @staticmethod
    def get_data():
        try:
            spx = yf.Ticker("^SPX")
            spot = spx.history(period="1d")['Close'].iloc[-1]
            expirations = spx.options
            
            # Pegamos as 2 primeiras expirações (0DTE e Próxima)
            all_options = []
            for exp in expirations[:2]:
                opt_chain = spx.option_chain(exp)
                
                # Cálculo de Tempo (T em anos)
                t_days = (datetime.strptime(exp, '%Y-%m-%d') - datetime.now()).days
                T = max(t_days, 0.5) / 365.0 
                r = 0.045 # Risk-free rate aproximada
                
                for _, row in opt_chain.calls.iterrows():
                    gamma = YahooGEXEngine.calculate_gamma(spot, row['strike'], T, r, row['impliedVolatility'])
                    gex = gamma * row['openInterest'] * 100 * spot**2 * 0.01
                    all_options.append({'Strike': row['strike'], 'GEX': gex, 'Exp': exp, 'Type': 'C'})
                
                for _, row in opt_chain.puts.iterrows():
                    gamma = YahooGEXEngine.calculate_gamma(spot, row['strike'], T, r, row['impliedVolatility'])
                    gex = gamma * row['openInterest'] * 100 * spot**2 * 0.01 * -1 # Puts subtraem Gamma
                    all_options.append({'Strike': row['strike'], 'GEX': gex, 'Exp': exp, 'Type': 'P'})
            
            return spot, pd.DataFrame(all_options)
        except Exception as e:
            st.error(f"Erro no Yahoo Engine: {e}")
            return None, None

# ============================================================================
# LÓGICA DE NÍVEIS E SINAIS (MANTIDA v5.3)
# ============================================================================
def get_levels(df, spot):
    agg = df.groupby('Strike')['GEX'].sum().reset_index()
    zg_idx = np.where(np.diff(np.sign(agg['GEX'])))[0]
    zg = agg['Strike'].iloc[zg_idx[0]] if len(zg_idx) > 0 else spot
    cw = agg.loc[agg['GEX'].idxmax(), 'Strike']
    pw = agg.loc[agg['GEX'].idxmin(), 'Strike']
    vt = agg[(agg['Strike'] > pw) & (agg['Strike'] < zg)]['Strike'].mean() or (zg - 15)
    
    # 0DTE (Primeira expiração da lista)
    exp0 = df['Exp'].iloc[0]
    df0 = df[df['Exp'] == exp0].groupby('Strike')['GEX'].sum().reset_index()
    cw0 = df0.loc[df0['GEX'].idxmax(), 'Strike']
    pw0 = df0.loc[df0['GEX'].idxmin(), 'Strike']
    
    return {'zg': zg, 'cw': cw, 'pw': pw, 'vt': vt, 'cw0': cw0, 'pw0': pw0, 'l1': cw-10, 'c1': zg-15}

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================
def main():
    # Inicialização
    if 'data_engine' not in st.session_state: st.session_state.data_engine = None
    
    # Header
    st.markdown("""
    <div class="header-container">
        <div><h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1><p class='header-subtitle'>v6.0 Yahoo Engine • Institutional Trading System</p></div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        mt5_input = st.number_input("💻 Preço do ES no seu MT5:", value=5100.0, step=0.25)
        range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)
        st.divider()
        if st.button("🚀 ATUALIZAR MATRIZ (YAHOO)", use_container_width=True):
            with st.spinner("Calculando Gamma via Black-Scholes..."):
                spot, df = YahooGEXEngine.get_data()
                if df is not None:
                    st.session_state.data_engine = (spot, df)
                    st.session_state.update_time = datetime.now().strftime("%H:%M:%S")

    if st.session_state.data_engine:
        spot, df = st.session_state.data_engine
        basis = mt5_input - spot
        levels = get_levels(df, spot)
        def adj(v): return v + basis

        # --- ROW 1: METRICS & PLAYBOOK ---
        c1, c2, c3 = st.columns([1, 1, 2.5])
        with c1: st.markdown(f"<div class='metric-card'>SPX SPOT<br><b class='metric-value'>${spot:,.2f}</b></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'>BASIS ES-SPX<br><b class='metric-value' style='color:#00D4FF !important;'>{basis:+.2f}</b></div>", unsafe_allow_html=True)
        
        with c3:
            viés = "LONG 📈" if mt5_input > adj(levels['zg']) else "SHORT 📉"
            cor = "#00FFAA" if "LONG" in viés else "#ff4757"
            st.markdown(f"""
            <div class="playbook-container" style="border-left: 6px solid {cor};">
                <div style="font-size:11px; color:#8A94A6; font-weight:700;">PLAYBOOK TÁTICO</div>
                <div style="font-size:32px; font-weight:900; color:{cor};">{viés}</div>
                <div class="playbook-grid">
                    <div class="playbook-item"><small>GATILHO</small><br><b>{adj(levels['zg']):.2f}</b></div>
                    <div class="playbook-item"><small>ALVO</small><br><b>{adj(levels['cw'] if 'LONG' in viés else levels['pw']):.2f}</b></div>
                    <div class="playbook-item"><small>STOP</small><br><b>{adj(levels['vt']):.2f}</b></div>
                </div>
            </div>""", unsafe_allow_html=True)

        # --- ROW 2: COPY PANEL ---
        st.markdown("<div class='copy-panel-title'>📋 EXPORTAÇÃO MT5 (CLIQUE PARA COPIAR)</div>", unsafe_allow_html=True)
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1: st.caption("MACRO WALLS"); st.code(f"{adj(levels['cw']):.2f} (CW)\n{adj(levels['pw']):.2f} (PW)")
        with cp2: st.caption("INFLEXÃO"); st.code(f"{adj(levels['zg']):.2f} (ZG)\n{adj(levels['vt']):.2f} (VT)")
        with cp3: st.caption("0DTE"); st.code(f"{adj(levels['cw0']):.2f} (CW)\n{adj(levels['pw0']):.2f} (PW)")
        with cp4: st.caption("S/R"); st.code(f"{adj(levels['l1']):.2f} (L1)\n{adj(levels['c1']):.2f} (C1)")

        # --- ROW 3: GRÁFICO ---
        st.subheader("📊 Perfil Institucional (Gamma Exposure)")
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        mask = (agg['Strike'] > spot * (1 - range_pct/100)) & (agg['Strike'] < spot * (1 + range_pct/100))
        chart_data = agg[mask].copy()
        chart_data['Strike'] = chart_data['Strike'] + basis
        
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Strike:Q', scale=alt.Scale(zero=False)),
            y='GEX:Q',
            color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#ff4757')),
            tooltip=['Strike', 'GEX']
        ).properties(height=380)
        st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()
