import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
import time
import altair as alt

# --- SETUP DA PÁGINA ---
st.set_page_config(page_title="GEX ULTRA ELITE PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background: #0b0e14; color: white; }
    .header-container {
        background: linear-gradient(90deg, rgba(11, 14, 20, 0.9) 0%, rgba(26, 31, 46, 0.7) 100%);
        border-radius: 16px; padding: 30px; border: 1px solid rgba(0, 255, 170, 0.2); margin-bottom: 20px;
    }
    .metric-card { background: rgba(20, 25, 35, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 15px; text-align: center; }
    .playbook-container { background: rgba(15, 20, 28, 0.95); border-radius: 12px; padding: 20px; border: 1px solid rgba(255,255,255,0.05); }
    .stButton>button { width: 100%; background: linear-gradient(90deg, #00FFAA, #00D4FF) !important; color: black !important; font-weight: bold; border: none; height: 3em; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE CÁLCULO ---
def calculate_gex_levels(df, spot):
    agg = df.groupby('Strike')['GEX'].sum().reset_index()
    cw = agg.loc[agg['GEX'].idxmax(), 'Strike']
    pw = agg.loc[agg['GEX'].idxmin(), 'Strike']
    
    # Zero Gamma (Simplificado)
    zg = agg.iloc[(agg['Strike']-spot).abs().argsort()[:1]]['Strike'].values[0]
    vt = (zg + pw) / 2
    c1 = pw + 15
    return {'zg': zg, 'cw': cw, 'pw': pw, 'vt': vt, 'c1': c1}

# --- INTERFACE ---
st.markdown('<div class="header-container"><h1 style="color:#00FFAA; margin:0;">⚡ GEX ULTRA ELITE TERMINAL</h1><p style="color:#8A94A6; margin:0;">v5.5 FULL BRIDGE • INSTITUTIONAL DATA</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configurações")
    bridge_url = st.text_input("🔗 Link do Colab (Ngrok):", placeholder="https://xxxx.ngrok-free.app/spx")
    mt5_price = st.number_input("💻 Preço ES no MT5:", value=5100.0, step=0.25)
    range_pct = st.slider("Range Gráfico (%):", 1, 10, 3)

if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL (FULL SYNC)"):
    if not bridge_url:
        st.error("Cole o link do Colab!")
    else:
        url = bridge_url.strip()
        with st.spinner("Conectando à Ponte..."):
            try:
                headers = {"ngrok-skip-browser-warning": "true"}
                r = requests.get(url, headers=headers, timeout=30)
                if r.status_code == 200:
                    st.session_state.spx_data = r.json()
                    st.session_state.last_update = time.strftime("%H:%M:%S")
                    st.success("DADOS ATUALIZADOS!")
                else: st.error(f"Erro {r.status_code}")
            except Exception as e: st.error(f"Falha: {e}")

if 'spx_data' in st.session_state:
    data = st.session_state.spx_data
    spot = float(data["data"]["last"])
    basis = mt5_price - spot
    
    # Processamento Gamma
    df = pd.DataFrame(data["data"]["options"])
    df['Strike'] = df['option'].apply(lambda x: int(re.search(r'(\d{8})$', x).group(1))/1000)
    df['Type'] = df['option'].apply(lambda x: 'C' if 'C' in x else 'P')
    for col in ['gamma', 'open_interest']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['GEX'] = df['gamma'] * df['open_interest'] * 100 * spot**2 * 0.01
    df.loc[df['Type'] == 'P', 'GEX'] *= -1
    
    lv = calculate_gex_levels(df, spot)
    def adj(v): return v + basis

    # --- DISPLAY ---
    c1, c2, c3 = st.columns([1,1,2])
    c1.markdown(f"<div class='metric-card'>SPX SPOT<br><b style='font-size:24px;'>${spot:,.2f}</b></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>MT5 BASIS<br><b style='font-size:24px; color:#00D4FF;'>{basis:+.2f}</b></div>", unsafe_allow_html=True)
    
    with c3:
        cor = "#00FFAA" if mt5_price > adj(lv['zg']) else "#FF4444"
        st.markdown(f"""
        <div class="playbook-container" style="border-left: 5px solid {cor};">
        <b style="color:{cor}; font-size:20px;">VIÉS: {"ALTA 📈" if cor == "#00FFAA" else "BAIXA 📉"}</b><br>
        <small>ZG: {adj(lv['zg']):.2f} | Alvo: {adj(lv['cw'] if cor=="#00FFAA" else lv['pw']):.2f}</small>
        </div>""", unsafe_allow_html=True)

    st.markdown("### 📋 Níveis Institucionais MT5")
    x1, x2, x3, x4 = st.columns(4)
    x1.metric("Call Wall", f"{adj(lv['cw']):.2f}")
    x2.metric("Zero Gamma", f"{adj(lv['zg']):.2f}")
    x3.metric("Vol Trigger", f"{adj(lv['vt']):.2f}")
    x4.metric("Put Wall", f"{adj(lv['pw']):.2f}")

    # Gráfico
    agg = df.groupby('Strike')['GEX'].sum().reset_index()
    mask = (agg['Strike'] > spot * (1 - range_pct/100)) & (agg['Strike'] < spot * (1 + range_pct/100))
    chart = alt.Chart(agg[mask]).mark_bar().encode(
        x=alt.X('Strike:Q', scale=alt.Scale(zero=False)),
        y='GEX:Q',
        color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#FF4444'))
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    with st.expander("🖥️ PINE SCRIPT"):
        st.code(f'plot({adj(lv["zg"]):.2f}, "ZG", color.white)\nplot({adj(lv["cw"]):.2f}, "CW", color.red)')
