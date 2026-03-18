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

.gradient-title { 
    background: linear-gradient(90deg, #00FFAA, #00D4FF); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    font-weight: 800; font-size: 36px; margin: 0; font-family: 'JetBrains Mono', monospace; 
}

.metric-card { 
    background: rgba(20, 25, 35, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); 
    border-radius: 12px; padding: 20px; text-align: center; backdrop-filter: blur(12px); 
}

.playbook-container { 
    background: rgba(15, 20, 28, 0.95); border-radius: 12px; padding: 25px; 
    border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.playbook-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }

.playbook-item { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); }

.copy-panel-title { 
    font-size: 13px; color: #8A94A6; text-transform: uppercase; font-weight: 800; 
    margin-top: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 5px;
}

.stButton>button { 
    width: 100%; background: linear-gradient(90deg, #00FFAA, #00D4FF) !important; 
    color: black !important; font-weight: bold; border: none; height: 3.5em; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LÓGICA DE CÁLCULO (ORIGINAL v5.3)
# ============================================================================

class GEXCalculator:
    def __init__(self, spot: float):
        self.spot = spot

    def calculate_gex_levels(self, df: pd.DataFrame) -> dict:
        if df.empty: return {k: self.spot for k in ['zg', 'cw', 'pw', 'vt', 'l1', 'c1']}
        
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        strikes, gex_vals = agg['Strike'].values, agg['GEX'].values
        
        # Zero Gamma
        zg = self._calculate_zero_gamma(strikes, gex_vals)
        # Walls
        cw = agg.loc[agg['GEX'].idxmax(), 'Strike']
        pw = agg.loc[agg['GEX'].idxmin(), 'Strike']
        # Vol Trigger (Média entre PW e ZG para simplificação da v5.3)
        vt = agg[(agg['Strike'] > min(pw, zg)) & (agg['Strike'] < max(pw, zg))]['Strike'].mean() or pw
        
        return {
            'zg': float(zg), 'cw': float(cw), 'pw': float(pw), 
            'vt': float(vt), 'l1': float(cw - 5), 'c1': float(pw + 5)
        }

    def _calculate_zero_gamma(self, strikes, gex_vals):
        sign_changes = np.where(np.diff(np.sign(gex_vals)) != 0)[0]
        if len(sign_changes) == 0: return self.spot
        idx = sign_changes[0]
        x1, x2, y1, y2 = strikes[idx], strikes[idx+1], gex_vals[idx], gex_vals[idx+1]
        return x1 - y1 * (x2 - x1) / (y2 - y1)

# ============================================================================
# INTERFACE E BRIDGE
# ============================================================================

def main():
    if 'spx_data' not in st.session_state: st.session_state.spx_data = None
    if 'last_update' not in st.session_state: st.session_state.last_update = None

    # Header Premium
    st.markdown(f"""
    <div class="header-container">
    <div><h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1><p style='color:#8A94A6; font-size:12px; font-family:monospace; letter-spacing:2px;'>v5.3 BRIDGE • SPX INSTITUTIONAL</p></div>
    <div style='text-align:right; color:#8A94A6; font-family:monospace;'>
        STATUS: {"<span style='color:#00FFAA'>● LIVE</span>" if st.session_state.spx_data else "<span style='color:#FFCC00'>● STANDBY</span>"}<br>
        UPDATE: {st.session_state.last_update or '--:--:--'}
    </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Configurações")
        bridge_url = st.text_input("🔗 Link do Colab (Ngrok):", placeholder="https://xxxx.ngrok-free.app/spx")
        mt5_price = st.number_input("💻 Preço ES no MT5:", value=5100.0, step=0.25)
        st.divider()
        range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)

    # Ação de Sincronização
    if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL", use_container_width=True, type="primary"):
        if not bridge_url:
            st.error("ERRO: Cole o link do Colab na barra lateral!")
        else:
            with st.spinner("Conectando à Ponte Google via Cloud..."):
                try:
                    r = requests.get(bridge_url, timeout=30)
                    if r.status_code == 200:
                        st.session_state.spx_data = r.json()
                        st.session_state.last_update = time.strftime("%H:%M:%S")
                        st.success("DADOS SINCRONIZADOS COM SUCESSO!")
                    else: st.error(f"Erro na ponte: {r.status_code}")
                except Exception as e: st.error(f"Falha de conexão: {e}")

    # Dashboard Principal
    if st.session_state.spx_data:
        data = st.session_state.spx_data
        spot = float(data["data"]["last"])
        basis = mt5_price - spot
        
        # Processamento de Gamma
        df = pd.DataFrame(data["data"]["options"])
        
        # Extração de Strike e Tipo via Regex (Lógica v5.3)
        def parse_opt(x):
            m = re.search(r'(\d{8})$', x)
            strike = int(m.group(1))/1000 if m else 0
            tp = 'C' if 'C' in x else 'P'
            return strike, tp

        df['Strike'], df['Type'] = zip(*df['option'].apply(parse_opt))
        for col in ['gamma', 'open_interest']: 
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df['GEX'] = df['gamma'] * df['open_interest'] * 100 * spot**2 * 0.01
        df.loc[df['Type'] == 'P', 'GEX'] *= -1
        
        calc = GEXCalculator(spot)
        levels = calc.calculate_gex_levels(df)
        def adj(v): return v + basis

        # ROW 1: Métricas e Playbook
        c1, c2, c3 = st.columns([1,1,2])
        with c1:
            st.markdown(f"<div class='metric-card'><span style='color:#8A94A6; font-size:12px;'>SPX SPOT</span><br><b style='font-size:24px; color:#00FFAA;'>${spot:,.2f}</b></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><span style='color:#8A94A6; font-size:12px;'>BASIS (MT5)</span><br><b style='font-size:24px; color:#00D4FF;'>{basis:+.2f}</b></div>", unsafe_allow_html=True)
        
        with c3:
            color = "#00FFAA" if mt5_price > adj(levels['zg']) else "#FF4444"
            st.markdown(f"""
            <div class="playbook-container" style="border-left: 6px solid {color};">
            <div style="font-size:24px; font-weight:900; color:{color};">{ "VIÉS: LONG 📈" if color == "#00FFAA" else "VIÉS: SHORT 📉" }</div>
            <div class="playbook-grid">
                <div class="playbook-item"><div style="font-size:10px; color:#8A94A6;">ENTRADA (ZG)</div><b style="color:white;">{adj(levels['zg']):.2f}</b></div>
                <div class="playbook-item"><div style="font-size:10px; color:#8A94A6;">ALVO (WALL)</div><b style="color:white;">{adj(levels['cw']):.2f}</b></div>
                <div class="playbook-item"><div style="font-size:10px; color:#8A94A6;">STOP (VT)</div><b style="color:white;">{adj(levels['vt']):.2f}</b></div>
            </div></div>""", unsafe_allow_html=True)

        # ROW 2: Painel de Cópia
        st.markdown("<div class='copy-panel-title'>📋 NÍVEIS MT5 (CLIQUE PARA COPIAR)</div>", unsafe_allow_html=True)
        x1, x2, x3, x4 = st.columns(4)
        x1.caption("Call Wall"); x1.code(f"{adj(levels['cw']):.2f}", language=None)
        x2.caption("Zero Gamma"); x2.code(f"{adj(levels['zg']):.2f}", language=None)
        x3.caption("Vol Trigger"); x3.code(f"{adj(levels['vt']):.2f}", language=None)
        x4.caption("Put Wall"); x4.code(f"{adj(levels['pw']):.2f}", language=None)

        # ROW 3: Gráfico Visual Altair
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        mask = (agg['Strike'] > spot * (1 - range_pct/100)) & (agg['Strike'] < spot * (1 + range_pct/100))
        chart_data = agg[mask].copy()
        
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Strike:Q', title='Strike SPX', scale=alt.Scale(zero=False)),
            y=alt.Y('GEX:Q', title='Gamma Exposure ($)'),
            color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#FF4444')),
            tooltip=['Strike', 'GEX']
        ).properties(height=350, title="Perfil de Exposição Institucional")
        st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()
