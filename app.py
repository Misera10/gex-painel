"""
GEX ULTRA ELITE TERMINAL PRO (v5.5 - Full Bridge Edition)
Dashboard Completa | Playbook Tático | MT5 Sync | Gráfico de Gamma | Pine Script
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
# 1. CONFIGURAÇÕES VISUAIS PREMIUM
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
.playbook-container { background: rgba(15, 20, 28, 0.95); border-radius: 12px; padding: 25px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
.playbook-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }
.playbook-item { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); }
.copy-panel-title { font-size: 13px; color: #8A94A6; text-transform: uppercase; font-weight: 800; margin-top: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 5px; }
.stButton>button { width: 100%; background: linear-gradient(90deg, #00FFAA, #00D4FF) !important; color: black !important; font-weight: bold; border-radius: 8px; height: 3.5em; border: none; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. LÓGICA DE CÁLCULO INSTITUCIONAL
# ============================================================================
class GEXCalculator:
    def __init__(self, spot: float):
        self.spot = spot

    def calculate_levels(self, df: pd.DataFrame) -> dict:
        if df.empty: return {k: self.spot for k in ['zg', 'cw', 'pw', 'vt', 'l1', 'c1', 'c4']}
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        strikes, gex_vals = agg['Strike'].values, agg['GEX'].values
        
        # Zero Gamma (Ponto de Inflexão)
        zg = self._find_zero(strikes, gex_vals)
        cw = agg.loc[agg['GEX'].idxmax(), 'Strike']
        pw = agg.loc[agg['GEX'].idxmin(), 'Strike']
        
        # Vol Trigger e Níveis Secundários
        vt = agg[(agg['Strike'] > min(pw, zg)) & (agg['Strike'] < max(pw, zg))]['Strike'].mean() or (pw + 10)
        l1 = agg.nlargest(2, 'GEX')['Strike'].iloc[-1]
        c1 = agg[agg['Strike'] > pw].nsmallest(1, 'GEX')['Strike'].iloc[0] if not agg[agg['Strike'] > pw].empty else pw
        
        return {'zg': zg, 'cw': cw, 'pw': pw, 'vt': vt, 'l1': l1, 'c1': c1}

    def _find_zero(self, x, y):
        s = np.sign(y)
        z = np.where(s[1:] != s[:-1])[0]
        if len(z) == 0: return self.spot
        idx = z[0]
        return x[idx] - y[idx] * (x[idx+1] - x[idx]) / (y[idx+1] - y[idx])

# ============================================================================
# 3. INTERFACE E BRIDGE
# ============================================================================
def main():
    if 'spx_data' not in st.session_state: st.session_state.spx_data = None
    if 'last_update' not in st.session_state: st.session_state.last_update = None

    # Header Premium
    st.markdown(f"""
    <div class="header-container">
    <div><h1 class='gradient-title'>GEX ULTRA ELITE PRO</h1><p style='color:#8A94A6; font-size:12px; font-family:monospace; letter-spacing:2px;'>v5.5 BRIDGE • INSTITUTIONAL TERMINAL</p></div>
    <div style='text-align:right; color:#8A94A6; font-family:monospace;'>
        STATUS: {"<span style='color:#00FFAA'>● LIVE</span>" if st.session_state.spx_data else "<span style='color:#FFCC00'>● STANDBY</span>"}<br>
        SYNC: {st.session_state.last_update or '--:--:--'}
    </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Configurações")
        bridge_url = st.text_input("🔗 Link do Colab (Ngrok):", placeholder="https://xxxx.ngrok-free.app/spx")
        mt5_price = st.number_input("💻 Preço ES no MT5:", value=5100.0, step=0.25)
        st.divider()
        range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)

    if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL (SINCRONIZAR)"):
        if not bridge_url:
            st.error("Cole o link do Colab na barra lateral!")
        else:
            url = bridge_url.strip()
            if not url.endswith("/spx"): url += "/spx"
            with st.spinner("Puxando dados institucionais via Bridge..."):
                try:
                    h = {"ngrok-skip-browser-warning": "true"}
                    r = requests.get(url, headers=h, timeout=30)
                    if r.status_code == 200:
                        st.session_state.spx_data = r.json()
                        st.session_state.last_update = time.strftime("%H:%M:%S")
                        st.success("MATRIZ SINCRONIZADA!")
                    else: st.error(f"Erro {r.status_code}: Verifique o Colab.")
                except Exception as e: st.error(f"Falha: {e}")

    # ========================================================================
    # 4. DASHBOARD E GRÁFICOS
    # ========================================================================
    if st.session_state.spx_data:
        data = st.session_state.spx_data
        spot = float(data["data"]["last"])
        basis = mt5_price - spot
        
        # Processamento de Dados
        df = pd.DataFrame(data["data"]["options"])
        df['Strike'] = df['option'].apply(lambda x: int(re.search(r'(\d{8})$', x).group(1))/1000 if re.search(r'(\d{8})$', x) else 0)
        df['Type'] = df['option'].apply(lambda x: 'C' if 'C' in x else 'P')
        for col in ['gamma', 'open_interest']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df['GEX'] = df['gamma'] * df['open_interest'] * 100 * spot**2 * 0.01
        df.loc[df['Type'] == 'P', 'GEX'] *= -1
        
        calc = GEXCalculator(spot)
        lv = calc.calculate_levels(df)
        def adj(v): return v + basis

        # --- MÉTRICAS E PLAYBOOK ---
        col_m1, col_m2, col_pb = st.columns([1, 1, 2.5])
        with col_m1:
            st.markdown(f"<div class='metric-card'><span style='color:#8A94A6; font-size:12px;'>SPX SPOT</span><br><b style='font-size:26px; color:white;'>${spot:,.2f}</b></div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"<div class='metric-card'><span style='color:#8A94A6; font-size:12px;'>BASIS MT5</span><br><b style='font-size:26px; color:#00D4FF;'>{basis:+.2f}</b></div>", unsafe_allow_html=True)
        
        with col_pb:
            viés = "LONG 📈" if mt5_price > adj(lv['zg']) else "SHORT 📉"
            cor = "#00FFAA" if viés == "LONG 📈" else "#FF4444"
            st.markdown(f"""
            <div class="playbook-container" style="border-left: 6px solid {cor};">
            <div style="font-size:24px; font-weight:900; color:{cor};">VIÉS: {viés}</div>
            <div class="playbook-grid">
                <div class="playbook-item"><div style="font-size:10px; color:#8A94A6;">ENTRADA</div><b>{adj(lv['zg']):.2f}</b></div>
                <div class="playbook-item"><div style="font-size:10px; color:#8A94A6;">ALVO</div><b>{adj(lv['cw'] if viés == "LONG 📈" else lv['pw']):.2f}</b></div>
                <div class="playbook-item"><div style="font-size:10px; color:#8A94A6;">STOP</div><b>{adj(lv['vt']):.2f}</b></div>
            </div></div>""", unsafe_allow_html=True)

        # --- NÍVEIS MT5 ---
        st.markdown("<div class='copy-panel-title'>📋 NÍVEIS MT5 (TAXAS INSTITUCIONAIS)</div>", unsafe_allow_html=True)
        x1, x2, x3, x4 = st.columns(4)
        x1.caption("Call Wall"); x1.code(f"{adj(lv['cw']):.2f}", language=None)
        x2.caption("Zero Gamma"); x2.code(f"{adj(lv['zg']):.2f}", language=None)
        x3.caption("Vol Trigger"); x3.code(f"{adj(lv['vt']):.2f}", language=None)
        x4.caption("Put Wall"); x4.code(f"{adj(lv['pw']):.2f}", language=None)

        # --- GRÁFICO ALTAIR ---
        st.subheader("📊 Perfil de Gamma Exposure")
        agg = df.groupby('Strike')['GEX'].sum().reset_index()
        mask = (agg['Strike'] > spot * (1 - range_pct/100)) & (agg['Strike'] < spot * (1 + range_pct/100))
        chart_data = agg[mask].copy()
        chart_data['Strike_MT5'] = chart_data['Strike'] + basis
        
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Strike_MT5:Q', title='Strike Ajustado MT5', scale=alt.Scale(zero=False)),
            y=alt.Y('GEX:Q', title='Exposição ($)'),
            color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#FF4444'))
        ).properties(height=380)
        st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()
