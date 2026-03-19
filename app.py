"""
GEX ULTRA ELITE TERMINAL PRO (v8.2 Final)
Design: Fiel à referência visual | Motor: Deep Scan (Macro Walls) | Radar Live Integrado
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import altair as alt
from datetime import datetime
import time
from scipy.stats import norm
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CSS REPLICA EXATA (Mesa Proprietária)
# ============================================================================
st.set_page_config(page_title="GEX ULTRA ELITE PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&family=Inter:wght@400;600;700;800&display=swap');

.stApp { background: #0f131a; font-family: 'Inter', sans-serif; color: #E0E6ED; }

/* HEADER */
.header-container {
    background: linear-gradient(90deg, rgba(15, 19, 26, 0.95) 0%, rgba(20, 25, 35, 0.8) 100%), 
                url('https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=2000&auto=format&fit=crop') center/cover;
    border-radius: 8px; padding: 20px 25px; margin-bottom: 15px; border: 1px solid rgba(0, 255, 170, 0.1);
}
.gradient-title { background: linear-gradient(90deg, #00FFAA, #00D4FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 24px; margin: 0; font-family: 'JetBrains Mono', monospace; }

/* DIVERGÊNCIA BANNER */
.divergence-alert { background: rgba(255, 71, 87, 0.05); border: 1px solid rgba(255, 71, 87, 0.3); border-radius: 8px; padding: 12px 20px; margin-bottom: 15px; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #ff4757; font-weight: 600; display: flex; align-items: center; }

/* CARDS ES/VIX */
.metric-card { background: #141822; border: 1px solid rgba(255, 255, 255, 0.03); border-radius: 8px; padding: 20px; text-align: center; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
.metric-title { font-size: 11px; color: #8A94A6; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; margin-bottom: 10px; }
.metric-val { font-size: 32px; font-weight: 800; font-family: 'JetBrains Mono'; margin-bottom: 5px; }

/* PLAYBOOK */
.playbook-container { background: #141822; border-radius: 8px; padding: 25px; border-left: 6px solid; border-top: 1px solid rgba(255,255,255,0.03); border-right: 1px solid rgba(255,255,255,0.03); border-bottom: 1px solid rgba(255,255,255,0.03); height: 100%; transition: all 0.3s ease; }
.pb-title { font-size: 11px; color: #8A94A6; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; margin-bottom: 5px; }
.pb-status { font-size: 32px; font-weight: 900; font-family: 'Inter', sans-serif; margin-bottom: 10px; letter-spacing: -1px; }
.pb-desc { font-size: 13px; color: #b0b8c8; margin-bottom: 20px; font-style: italic; }
.pb-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.pb-box { background: #0b0e14; padding: 15px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.02); }
.pb-box-title { font-size: 10px; color: #8A94A6; text-transform: uppercase; font-weight: 800; margin-bottom: 8px; display: flex; align-items: center; gap: 5px; }
.pb-box-val { font-size: 13px; color: #E0E6ED; font-weight: 600; line-height: 1.4; }
.pb-filters { margin-top: 20px; display: flex; align-items: center; gap: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px; }
.filter-label { font-size: 10px; color: #8A94A6; font-weight: 700; text-transform: uppercase; }
.badge { padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; text-transform: uppercase; }

/* CÓPIA */
.copy-section-title { font-size: 12px; color: #8A94A6; text-transform: uppercase; font-weight: 800; margin-top: 25px; margin-bottom: 15px; }
.copy-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.05); }
.copy-cell { background: #141822; padding: 15px; }

/* BOTÃO */
.stButton>button { width: 100%; background: #FF4B4B !important; color: white !important; font-weight: 900; border-radius: 6px; height: 3em; border: none; }
.stButton>button:hover { background: #ff3333 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MOTORES MATEMÁTICOS
# ============================================================================
@st.cache_data(ttl=300)
def fetch_market_engine():
    """Motor Pesado: Baixa matriz de opções e calcula GEX (Varredura Profunda)"""
    try:
        spx = yf.Ticker("^SPX")
        spot_spx = spx.history(period="1d")['Close'].iloc[-1]
        
        # Puxa até 8 vencimentos para capturar Macro Walls
        target_exps = spx.options[:8]
        if not target_exps: return None, "Bolsa não retornou opções."
        
        all_data = []
        for exp in target_exps:
            opt = spx.option_chain(exp)
            T = max((datetime.strptime(exp, '%Y-%m-%d') - datetime.now()).days, 0.5) / 365.0
            r = 0.045
            
            for _, row in opt.calls.iterrows():
                iv, oi = row['impliedVolatility'], row['openInterest']
                if iv > 0 and oi > 0:
                    gamma = norm.pdf((np.log(spot_spx / row['strike']) + (r + 0.5 * iv**2) * T) / (iv * np.sqrt(T))) / (spot_spx * iv * np.sqrt(T))
                    all_data.append({'Strike': row['strike'], 'GEX': gamma * oi * 100 * spot_spx**2 * 0.01, 'Exp': exp, 'Type': 'C'})
            
            for _, row in opt.puts.iterrows():
                iv, oi = row['impliedVolatility'], row['openInterest']
                if iv > 0 and oi > 0:
                    gamma = norm.pdf((np.log(spot_spx / row['strike']) + (r + 0.5 * iv**2) * T) / (iv * np.sqrt(T))) / (spot_spx * iv * np.sqrt(T))
                    all_data.append({'Strike': row['strike'], 'GEX': gamma * oi * 100 * spot_spx**2 * 0.01 * -1, 'Exp': exp, 'Type': 'P'})
        
        return {'spot_spx': spot_spx, 'df': pd.DataFrame(all_data)}, None
    except Exception as e:
        return None, str(e)

def fetch_live_price():
    """Motor Leve: Pega apenas preço atualizado a cada 10s (Para Radar Live)"""
    try:
        es = yf.Ticker("ES=F").history(period="1d")['Close'].iloc[-1]
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        spy = yf.Ticker("SPY").history(period="2d")
        spy_trend = "UP" if spy['Close'].iloc[-1] > spy['Close'].iloc[-2] else "DOWN"
        return es, vix, spy_trend
    except:
        return None, None, None

# ============================================================================
# SIDEBAR / CONFIGURAÇÕES
# ============================================================================
with st.sidebar:
    st.markdown("<h3 style='font-size:16px; margin-bottom:20px;'>⚙️ Configurações</h3>", unsafe_allow_html=True)
    range_pct = st.slider("Range Gráfico (%):", 1, 15, 5)
    
    st.markdown("<div style='background:#1a1f2b; padding:10px; border-radius:6px; margin-bottom:10px; border-left:3px solid #00D4FF;'><span style='font-size:12px; font-weight:bold; color:#00D4FF;'>📊 MODO DE PREÇO</span></div>", unsafe_allow_html=True)
    
    # Toggle Radar Live
    auto_refresh = st.toggle("🔄 Radar Live (Auto-Update Playbook)", value=False, help="Atualiza o Playbook e os preços automaticamente a cada 10 segundos.")
    
    if not auto_refresh:
        mt5_price = st.number_input("Preço Manual (MT5):", value=6614.30, step=0.25)
        usar_mt5 = True
    else:
        usar_mt5 = False

# ============================================================================
# TELA PRINCIPAL
# ============================================================================
st.markdown("""<div class="header-container"><h1 class="gradient-title">GEX ULTRA ELITE PRO</h1>
<p style="color:#8A94A6; margin:0; font-size:11px; text-transform:uppercase; letter-spacing:1px; margin-top:5px;">SPX EXCLUSIVE • PLAYBOOK TÁTICO • MT5 SYNC</p></div>""", unsafe_allow_html=True)

# Botão Pesado (Recalcula Muros)
if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL (SINCRONIZAR)"):
    with st.spinner("Extraindo Matriz Profunda (Aguarde 5 a 10 seg para carregar os muros gigantes)..."):
        data, erro = fetch_market_engine()
        if erro: 
            st.error("Erro na Matriz. Tente novamente.")
        elif data:
            st.session_state.market_data = data
            st.rerun()

if 'market_data' in st.session_state:
    m = st.session_state.market_data
    spot_spx = m['spot_spx']
    
    # Atualiza variáveis leves via Radar ou pega do último state
    live_es, live_vix, live_spy = fetch_live_price()
    es_fut = live_es if live_es else spot_spx
    vix = live_vix if live_vix else 20.0
    spy_trend = live_spy if live_spy else "UP"
    
    # Definição do Basis (Diferença de Spread)
    if not auto_refresh and usar_mt5:
        basis = mt5_price - spot_spx
        divergencia = mt5_price - es_fut
        if abs(divergencia) > 5:
            st.markdown(f"<div class='divergence-alert'>🔴 DIVERGÊNCIA: MT5 ({mt5_price:.2f}) vs Oficial ({es_fut:.2f}) = {divergencia:+.2f} pts</div>", unsafe_allow_html=True)
    else:
        basis = es_fut - spot_spx
    
    # CALCULA OS NÍVEIS COM O NOVO BASIS
    df = m['df']
    agg = df.groupby('Strike')['GEX'].sum().reset_index().sort_values('Strike')
    
    cw = agg.loc[agg['GEX'].idxmax(), 'Strike']
    pw = agg.loc[agg['GEX'].idxmin(), 'Strike']
    
    # Flip exato do Gamma
    signs = np.sign(agg['GEX'].values)
    sign_changes = np.where(np.diff(signs))[0]
    zg = spot_spx
    if len(sign_changes) > 0:
        closest_idx = sign_changes[np.argmin(np.abs(agg['Strike'].iloc[sign_changes] - spot_spx))]
        zg = agg['Strike'].iloc[closest_idx]

    # Vol Trigger
    vt_candidates = agg[(agg['Strike'] < zg) & (agg['Strike'] > pw)]
    vt = vt_candidates.loc[vt_candidates['GEX'].idxmin(), 'Strike'] if not vt_candidates.empty else (pw + (zg - pw)*0.3)
    
    def adj(val): return float(val) + basis

    # ========================================================================
    # RENDERIZAÇÃO DA DASHBOARD
    # ========================================================================
    col1, col2, col3 = st.columns([1, 1, 3.5])
    
    with col1:
        cor_es = "#00D4FF" if auto_refresh else "#E0E6ED"
        label_es = "ES LIVE (RADAR)" if auto_refresh else "ES MT5 (MANUAL)"
        val_es = es_fut if auto_refresh else mt5_price
        st.markdown(f"""<div class='metric-card' style='border-color: {cor_es if auto_refresh else "rgba(255,255,255,0.03)"};'>
            <div class='metric-title'>{label_es}</div>
            <div class='metric-val' style='color:{cor_es};'>{val_es:.2f}</div>
        </div>""", unsafe_allow_html=True)
        
    with col2:
        cor_vix = "#FF4B4B" if vix > 20 else "#00FFAA"
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-title'>VIX SPOT</div>
            <div class='metric-val' style='color:{cor_vix};'>{vix:.2f}</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        es_atual = es_fut if auto_refresh else mt5_price
        
        # Lógica de Playbook
        if es_atual > adj(zg):
            status, cor, desc = "LONG 📈", "#00FFAA", "Regime de Call Gamma. Market Makers estabilizam o preço atuando contra a tendência."
            gatilho, alvo, stop = f"Comprar perto de {adj(zg):.2f} (ZG)", f"Alvo em {adj(cw):.2f} (Call Wall)", f"Fechamento abaixo de {adj(zg):.2f}"
        elif adj(vt) < es_atual <= adj(zg):
            status, cor, desc = "RANGE / CAUTELA ⚠️", "#FFCC00", "Zona de Compressão no S&P 500. Baixa convicção direcional com risco de violinadas."
            gatilho, alvo, stop = f"Comprar {adj(vt):.2f} (VT) ou vender {adj(zg):.2f}", f"Extremo oposto da caixa d'água.", f"Rompimento com volume fora da zona."
        else:
            status, cor, desc = "STRONG SHORT 📉", "#FF4B4B", "Gamma Trap ativado. Dealers forçados a vender contratos para proteção de Delta."
            gatilho, alvo, stop = f"Vender pullbacks na rejeição de {adj(vt):.2f}.", f"Alvo final em {adj(pw):.2f} (Put Wall)", f"Fechamento acima de {adj(vt):.2f}"

        badge_vix = f"<span class='badge' style='background:rgba(255, 71, 87, 0.1); color:#ff4757; border:1px solid #ff4757;'>VIX ALTO ({vix:.2f})</span>" if vix > 20 else f"<span class='badge' style='background:rgba(0, 255, 170, 0.1); color:#00FFAA; border:1px solid #00FFAA;'>VIX CALMO ({vix:.2f})</span>"
        badge_spy = f"<span class='badge' style='background:rgba(255, 71, 87, 0.1); color:#ff4757; border:1px solid #ff4757;'>SPY TREND {spy_trend}</span>" if spy_trend == "DOWN" else f"<span class='badge' style='background:rgba(0, 255, 170, 0.1); color:#00FFAA; border:1px solid #00FFAA;'>SPY TREND {spy_trend}</span>"
        badge_live = "<span class='badge' style='background:rgba(0, 212, 255, 0.1); color:#00D4FF; border:1px solid #00D4FF;'>⚡ RADAR ATIVO</span>" if auto_refresh else ""

        st.markdown(f"""
        <div class="playbook-container" style="border-left-color: {cor};">
            <div class="pb-title">PLANO DE VOO TÁTICO (PLAYBOOK)</div>
            <div class="pb-status" style="color: {cor};">{status}</div>
            <div class="pb-desc">{desc}</div>
            
            <div class="pb-grid">
                <div class="pb-box"><div class="pb-box-title">🟢 GATILHO (ENTRADA)</div><div class="pb-box-val">{gatilho}</div></div>
                <div class="pb-box"><div class="pb-box-title">🎯 ALVOS (TAKE PROFIT)</div><div class="pb-box-val">{alvo}</div></div>
                <div class="pb-box"><div class="pb-box-title">🛑 STOP (INVALIDAÇÃO)</div><div class="pb-box-val">{stop}</div></div>
            </div>
            
            <div class="pb-filters">
                <span class="filter-label">FILTROS DA MESA:</span>
                {badge_vix} {badge_spy} {badge_live}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- ROW 2: PAINEL DE EXPORTAÇÃO ---
    st.markdown("<div class='copy-section-title'>📋 EXPORTAÇÃO MT5</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        st.markdown("<div class='pb-title'>MACRO WALLS</div>", unsafe_allow_html=True)
        st.code(f"Call Wall: {adj(cw):.2f}\nPut Wall:  {adj(pw):.2f}")
    with c2: 
        st.markdown("<div class='pb-title'>INFLEXÃO & RISCO</div>", unsafe_allow_html=True)
        st.code(f"Zero Gamma:  {adj(zg):.2f}\nVol Trigger: {adj(vt):.2f}")
    with c3:
        st.markdown("<div class='pb-title'>MICRO 0DTE</div>", unsafe_allow_html=True)
        df0 = df[df['Exp'] == df['Exp'].iloc[0]].groupby('Strike')['GEX'].sum().reset_index()
        st.code(f"CW 0DTE: {adj(df0.loc[df0['GEX'].idxmax(), 'Strike']):.2f}\nPW 0DTE: {adj(df0.loc[df0['GEX'].idxmin(), 'Strike']):.2f}")
    with c4: 
        st.markdown("<div class='pb-title'>SUPORTE/RESISTÊNCIA</div>", unsafe_allow_html=True)
        st.code(f"L1: {adj(cw-15):.2f}\nC1: {adj(zg-15):.2f}")

    # --- ROW 3: GRÁFICO INSTITUCIONAL ---
    st.markdown("<br>", unsafe_allow_html=True)
    mask = (agg['Strike'] > spot_spx * (1 - range_pct/100)) & (agg['Strike'] < spot_spx * (1 + range_pct/100))
    c_data = agg[mask].copy()
    c_data['Strike'] = c_data['Strike'] + basis
    
    chart = alt.Chart(c_data).mark_bar().encode(
        x=alt.X('Strike:Q', scale=alt.Scale(zero=False), title="Preço Ajustado ao MT5"),
        y=alt.Y('GEX:Q', title="Gamma Exposure", axis=alt.Axis(format='~s')),
        color=alt.condition(alt.datum.GEX > 0, alt.value('#00FFAA'), alt.value('#FF4B4B')),
        tooltip=[alt.Tooltip('Strike', format='.2f'), alt.Tooltip('GEX', format='~s')]
    ).properties(height=400).configure_axis(grid=True, gridColor='rgba(255,255,255,0.05)')
    
    st.altair_chart(chart, use_container_width=True)

    # ========================================================================
    # AUTO-REFRESH LOOP (Mágica do Live)
    # ========================================================================
    if auto_refresh:
        time.sleep(10) # Aguarda 10 segundos
        st.rerun() # Atualiza a tela

else:
    st.info("Pressione o botão vermelho para buscar a liquidez e ativar a dashboard.")
