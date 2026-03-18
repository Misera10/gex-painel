"""
GEX ULTRA ELITE TERMINAL PRO (v5.3 - Cloud Bridge Edition)
Layout Original Preservado | Conexão via Google Colab
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import re
import time
import altair as alt
from datetime import datetime
from scipy.stats import norm

# ============================================================================
# CONFIGURAÇÕES E CSS PREMIUM (ORIGINAL v5.3)
# ============================================================================

st.set_page_config(page_title="GEX ULTRA ELITE PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');
.stApp { background: linear-gradient(135deg, #0b0e14 0%, #131824 100%); font-family: 'Inter', sans-serif; }
.header-container {
    background: linear-gradient(90deg, rgba(11, 14, 20, 0.9) 0%, rgba(26, 31, 46, 0.7) 100%), 
                url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2000&auto=format&fit=crop') center/cover;
    border-radius: 16px; padding: 35px 30px; margin-bottom: 25px; border: 1px solid rgba(0, 255, 170, 0.2);
    box-shadow: 0 15px 35px rgba(0,0,0,0.4); display: flex; justify-content: space-between; align-items: center;
}
.gradient-title { background: linear-gradient(90deg, #00FFAA, #00D4FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    font-weight: 800; font-size: 36px; margin: 0; font-family: 'JetBrains Mono', monospace; }
.metric-card { background: rgba(20, 25, 35, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 20px; text-align: center; backdrop-filter: blur(12px); }
.playbook-container { background: rgba(15, 20, 28, 0.95); border-radius: 12px; padding: 25px; border: 1px solid rgba(255,255,255,0.05); }
.playbook-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }
.playbook-item { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); }
.copy-panel-title { font-size: 13px; color: #8A94A6; text-transform: uppercase; font-weight: 800; margin-top: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LÓGICA DE CÁLCULO (ORIGINAL v5.3)
# ============================================================================

class GEXCalculator:
    def __init__(self, spot: float):
        self.spot = spot

    def calculate_gex_levels(self, df: pd.DataFrame) -> dict:
        if df.empty: return {k: self.spot for k in ['zg', 'cw', 'pw', 'vt', 'l1', 'c1', 'c4']}
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        zg = self._calculate_zero_gamma(agg['Strike'].values, agg['GEX'].values)
        cw = agg.loc[agg['GEX'].idxmax(), 'Strike']
        pw = agg.loc[agg['GEX'].idxmin(), 'Strike']
        vt = agg[(agg['Strike'] > min(pw, zg)) & (agg['Strike'] < max(pw, zg))]['Strike'].mean() or pw
        return {'zg': float(zg), 'cw': float(cw), 'pw': float(pw), 'vt': float(vt), 'l1': float(cw-10), 'c1': float(pw+10), 'c4': float(pw-20)}

    def _calculate_zero_gamma(self, strikes, gex_vals):
        sign_changes = np.where(np.diff(np.sign(gex_vals)) != 0)[0]
        if len(sign_changes) == 0: return self.spot
        idx = sign_changes[0]
        return strikes[idx] - gex_vals[idx] * (strikes[idx+1] - strikes[idx]) / (gex_vals[idx+1] - gex_vals[idx])

# ============================================================================
# INTERFACE E BRIDGE
# ============================================================================

def main():
    if 'spx_data' not in st.session_state: st.session_state.spx_data = None

    # Header
    st.markdown(f"""
    <div class="header-container">
    <div><h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1><p style='color:#8A94A6; font-size:12px;'>v5.3 BRIDGE • SPX INSTITUTIONAL</p></div>
    <div style='text-align:right; color:#8A94A6; font-family:monospace;'>STATUS: {"<span style='color:#00FFAA'>● LIVE</span>" if st.session_state.spx_data else "STANDBY"}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Configurações")
        bridge_url = st.text_input("🔗 Link do Colab (Ngrok):", placeholder="https://xxxx.ngrok-free.app/spx")
        mt5_price = st.number_input("💻 Preço ES no MT5:", value=5100.0, step=0.25)
        st.divider()
        range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)

    if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL", use_container_width=True, type="primary"):
        if not bridge_url:
            st.error("Insira o link do Colab primeiro!")
        else:
            with st.spinner("Conectando à Ponte Google..."):
                try:
                    r = requests.get(bridge_url, timeout=30)
                    if r.status_code == 200:
                        st.session_state.spx_data = r.json()
                        st.success("Dados Sincronizados!")
                    else: st.error("Erro na Ponte.")
                except Exception as e: st.error(f"Falha: {e}")

    if st.session_state.spx_data:
        data = st.session_state.spx_data
        spot = float(data["data"]["last"])
        basis = mt5_price - spot
        
        # Processamento de Dados (v5.3 Logic)
        df = pd.DataFrame(data["data"]["options"])
        df['Strike'] = df['option'].apply(lambda x: int(re.search(r'(\d{8})$', x).group(1))/1000 if re.search(r'(\d{8})$', x) else 0)
        df['Type'] = df['option'].apply(lambda x: 'C' if 'C' in x else 'P')
        for col in ['gamma', 'open_interest']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df['GEX'] = df['gamma'] * df['open_interest'] * 100 * spot**2 * 0.01
        df.loc[df['Type'] == 'P', 'GEX'] *= -1
        
        calc = GEXCalculator(spot)
        levels = calc.calculate_gex_levels(df)
        def adj(v): return v + basis

        # Render Metrics (VIX Simulado/Real)
        c1, c2, c3 = st.columns([1,1,2])
        c1.markdown(f"<div class='metric-card'>SPOT<br><span class='gradient-title' style='font-size:24px'>${spot:,.2f}</span></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>BASIS<br><span style='color:#00D4FF; font-size:24px; font-weight:bold;'>{basis:+.2f}</span></div>", unsafe_allow_html=True)
        
        # Playbook
        with c3:
            color = "#00FFAA" if spot + basis > adj(levels['zg']) else "#FF4444"
            st.markdown(f"""
            <div class="playbook-container" style="border-left: 6px solid {color};">
            <div style="font-size:28px; font-weight:900; color:{color};">{ "LONG 📈" if color == "#00FFAA" else "SHORT 📉" }</div>
            <div class="playbook-grid">
                <div class="playbook-item"><div style="font-size:10px; color:#8A94A6;">ENTRADA</div><b>{adj(levels['zg']):.2f}</b></div>
                <div class="playbook-item"><div style="font-size:10px; color:#8A94A6;">ALVO</div><b>{adj(levels['cw']):.2f}</b></div>
                <div class="playbook-item"><div style="font-size:10px; color:#8A94A6;">STOP</div><b>{adj(levels['vt']):.2f}</b></div>
            </div></div>""", unsafe_allow_html=True)

        # Copy Panel
        st.markdown("<div class='copy-panel-title'>📋 NÍVEIS MT5 (COPIÁVEIS)</div>", unsafe_allow_html=True)
        x1, x2, x3, x4 = st.columns(4)
        x1.code(f"{adj(levels['cw']):.2f}", language=None)
        x2.code(f"{adj(levels['zg']):.2f}", language=None)
        x3.code(f"{adj(levels['vt']):.2f}", language=None)
        x4.code(f"{adj(levels['pw']):.2f}", language=None)

        # Gráfico Altair (v5.3 Style)
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        chart = alt.Chart(agg).mark_bar().encode(
            x=alt.X('Strike:Q', scale=alt.Scale(domain=[spot-100, spot+100])),
            y='GEX:Q',
            color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#FF4444'))
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()
