import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import requests
import re
import yfinance as yf
import altair as alt

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA E AUTO-REFRESH
# ============================================================================
st.set_page_config(page_title="GEX ULTRA ELITE TERMINAL", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <script>
    function checkTimeAndRefresh() {
        const now = new Date();
        if (now.getHours() === 10 && now.getMinutes() === 45) {
            const today = now.toDateString();
            if (sessionStorage.getItem('last_gex_reload') !== today) {
                sessionStorage.setItem('last_gex_reload', today);
                window.parent.location.reload();
            }
        }
    }
    setInterval(checkTimeAndRefresh, 30000);
    </script>
""", unsafe_allow_html=True)

# ============================================================================
# CSS PREMIUM (Full Design)
# ============================================================================
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1a1f2e 100%); font-family: 'Segoe UI', sans-serif; }
    .metric-card { background: rgba(30, 34, 45, 0.85); border: 1px solid rgba(0, 255, 170, 0.2); border-radius: 12px; padding: 20px; margin: 10px 0; backdrop-filter: blur(10px); }
    .metric-card:hover { border-color: #00FFAA; box-shadow: 0 8px 25px rgba(0, 255, 170, 0.2); }
    .gradient-title { background: linear-gradient(90deg, #00FFAA, #00D4FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 32px; margin: 0; }
    .badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; margin: 2px; }
    .badge-positive { background: rgba(0, 255, 170, 0.15); color: #00FFAA; border: 1px solid rgba(0, 255, 170, 0.3); }
    .badge-negative { background: rgba(255, 68, 68, 0.15); color: #FF4444; border: 1px solid rgba(255, 68, 68, 0.3); }
    .badge-info { background: rgba(0, 212, 255, 0.15); color: #00D4FF; border: 1px solid rgba(0, 212, 255, 0.3); }
    code { color: #00FFAA !important; font-size: 26px !important; font-weight: 900 !important; display: block; text-align: center; background: #161a25 !important; border: 1px solid #00FFAA33; border-radius: 8px; }
    .label { color: #8A94A6; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    .header-box { background: rgba(30, 34, 45, 0.9); padding: 25px; border-radius: 12px; border: 1px solid rgba(0, 255, 170, 0.2); margin-bottom: 20px; }
    .progress-container { background: #2b313f; border-radius: 6px; height: 10px; overflow: hidden; margin: 10px 0; }
    .progress-bar { background: linear-gradient(90deg, #00FFAA, #00D4FF); height: 100%; transition: width 0.5s ease; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES CORE
# ============================================================================
@st.cache_data(ttl=300)
def calcGammaEx(S, K, vol, T, r, q, optType, OI):
    K, vol, T, OI = map(lambda x: np.asarray(x, dtype=float), [K, vol, T, OI])
    result = np.zeros_like(K, dtype=float)
    valid = (T > 0) & (vol > 0) & (K > 0)
    if not np.any(valid): return result
    Kv, vv, Tv, OIv = K[valid], vol[valid], T[valid], OI[valid]
    dp = (np.log(S / Kv) + (r - q + 0.5 * vv**2) * Tv) / (vv * np.sqrt(Tv))
    dm = dp - vv * np.sqrt(Tv)
    gamma = np.exp(-q * Tv) * norm.pdf(dp) / (S * vv * np.sqrt(Tv)) if optType == "call" else Kv * np.exp(-r * Tv) * norm.pdf(dm) / (S * S * vv * np.sqrt(Tv))
    result[valid] = OIv * 100 * S * S * 0.01 * gamma
    return result

@st.cache_data(ttl=60)
def fetch_cboe(symbol="SPX"):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(f"https://cdn.cboe.com/api/global/delayed_quotes/options/  {symbol}.json", headers=headers, timeout=10)
        return r.json()
    except: return None

def fetch_vix():
    try:
        v = yf.Ticker("^VIX").history(period="1d")["Close"].iloc[-1]
        v9 = yf.Ticker("^VIX9D").history(period="1d")["Close"].iloc[-1]
        return {'vix': v, 'vix9d': v9}
    except: return {'vix': 20.0, 'vix9d': 20.0}

def process_levels(data):
    if not data: return None
    spot = data["data"].get("current_price", data["data"].get("last"))
    df = pd.DataFrame(data["data"]["options"])
    parsed = df["option"].apply(lambda x: re.search(r'^(.*?)(\d{6})([CP])(\d{8})$', x))
    df["ExpirationDate"] = pd.to_datetime(parsed.apply(lambda m: m.group(2) if m else None), format="%y%m%d") + timedelta(hours=16)
    df["OptionType"] = parsed.apply(lambda m: m.group(3) if m else None)
    df["StrikePrice"] = parsed.apply(lambda m: int(m.group(4))/1000.0 if m else np.nan)
    for col in ["iv", "gamma", "open_interest"]: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    calls = df[df["OptionType"] == "C"].rename(columns={"iv": "CallIV", "gamma": "CallGamma", "open_interest": "CallOpenInt"})
    puts = df[df["OptionType"] == "P"].rename(columns={"iv": "PutIV", "gamma": "PutGamma", "open_interest": "PutOpenInt"})
    dff = pd.merge(calls, puts, on=["ExpirationDate", "StrikePrice"], how="outer").fillna(0)
    dff['TotalG'] = ((dff['CallGamma']*dff['CallOpenInt']*100*spot**2*0.01) - (dff['PutGamma']*dff['PutOpenInt']*100*spot**2*0.01))/1e9
    
    dfAgg = dff.groupby(['StrikePrice']).sum(numeric_only=True)
    cw, pw = dfAgg['TotalG'].idxmax(), dfAgg['TotalG'].idxmin()
    
    min_exp = dff['ExpirationDate'].min()
    df_0dte = dff[dff['ExpirationDate'] == min_exp].groupby(['StrikePrice']).sum(numeric_only=True)
    cw0 = df_0dte['TotalG'].idxmax() if not df_0dte.empty else np.nan
    pw0 = df_0dte['TotalG'].idxmin() if not df_0dte.empty else np.nan
    
    dff["T"] = np.where(dff["ExpirationDate"].dt.date == datetime.now().date(), 1/262, np.busday_count(datetime.now().date(), dff["ExpirationDate"].dt.date.values.astype('datetime64[D]')) / 262)
    dfc = dff[dff['T'] > 0]
    l_range = np.arange(np.floor(spot*0.8/5)*5, np.ceil(spot*1.2/5)*5+5, 5.0)
    tg = [(calcGammaEx(l, dfc['StrikePrice'], dfc['CallIV'].replace(0,0.15), dfc['T'], 0, 0, "call", dfc['CallOpenInt']) - 
           calcGammaEx(l, dfc['StrikePrice'], dfc['PutIV'].replace(0,0.15), dfc['T'], 0, 0, "put", dfc['PutOpenInt'])).sum()/1e9 for l in l_range]
    zc = np.where(np.diff(np.sign(tg)) != 0)[0]
    zg = float(l_range[zc[0]] - tg[zc[0]]*5.0/(tg[zc[0]+1]-tg[zc[0]])) if len(zc)>0 else spot
    
    # Níveis extras
    df_filt = dfAgg[(dfAgg.index >= spot*0.9) & (dfAgg.index <= spot*1.1)]
    top_c = df_filt['TotalG'].nlargest(3).index.tolist()
    l1 = top_c[1] if len(top_c)>1 else cw
    c1 = df_filt[df_filt.index > pw]['TotalG'].idxmin() if not df_filt[df_filt.index > pw].empty else pw
    c4 = df_filt[df_filt.index < pw]['TotalG'].idxmin() if not df_filt[df_filt.index < pw].empty else pw
    vt = df_filt[(df_filt.index > pw) & (df_filt.index < zg)]['TotalG'].idxmin() if not df_filt[(df_filt.index > pw) & (df_filt.index < zg)].empty else np.nan
    
    return {'spot': spot, 'cw': cw, 'pw': pw, 'cw0': cw0, 'pw0': pw0, 'zg': zg, 'l1': l1, 'c1': c1, 'c4': c4, 'vt': vt, 'dfAgg': dfAgg}

# ============================================================================
# RENDERIZAÇÃO
# ============================================================================
st.markdown("<div style='text-align:center;'><h1 class='gradient-title'>⚡ GEX ULTRA ELITE TERMINAL v5.8</h1></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ SETUP")
    tipo_ativo = st.radio("MT5 Asset:", ["SPX500.x (CFD/Mesa)", "ES (Futuro CME)"])
    st.markdown("---")
    st.markdown("#### 🕵️ Sincronia SPY")
    modo_spy = st.checkbox("Ativar Confluência ETF", value=True)
    st.caption("v5.8 - Multi-Asset Confluence")

if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL COMPLETA", use_container_width=True, type="primary"):
    with st.spinner("⚡ Sincronizando SPX, SPY e VIX..."):
        try:
            spx = process_levels(fetch_cboe("SPX"))
            spy = process_levels(fetch_cboe("SPY")) if modo_spy else None
            v_data = fetch_vix()
            
            # Ajuste de Basis
            if "CFD" in tipo_ativo:
                basis, es_spot = 0.0, spx['spot']
            else:
                try: es_spot = yf.Ticker("ES=F").history(period="1d", interval="1m")["Close"].iloc[-1]; basis = es_spot - spx['spot']
                except: es_spot, basis = spx['spot'], 0.0

            # Lógica de Score (0-4)
            score = 0
            details = {'regime': False, 'vix': False, 'space': False, 'spy': False}
            regime = "POSITIVO" if spx['spot'] > spx['zg'] else "NEGATIVO"
            
            if regime == "NEGATIVO" and spx['spot'] < spx['zg']: score += 1; details['regime'] = True
            if v_data['vix9d'] > v_data['vix']: score += 1; details['vix'] = True
            if abs(spx['spot'] - spx['pw0']) > (spx['spot']*0.002): score += 1; details['space'] = True
            
            # Sincronia SPY (1/10 rule)
            if spy:
                dist_spy = abs(spy['spot'] - spy['pw'])
                if dist_spy < 1.0: score += 1; details['spy'] = True

            # Interface de Status
            st.markdown(f"""
            <div class="header-box">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3>REGIME GEX: <span style="color:{'#00FFAA' if regime=='POSITIVO' else '#FF4444'}">{regime}</span></h3>
                    <div style="display:flex; gap:10px;">
                        <span class="badge badge-info">VIX {v_data['vix']:.2f}</span>
                        <span class="badge {'badge-negative' if v_data['vix9d']>v_data['vix'] else 'badge-positive'}">CURVE: {'INVERTIDA' if v_data['vix9d']>v_data['vix'] else 'NORMAL'}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns([1, 2])
            with c1:
                pct = (score / 4) * 100
                color = "#00FFAA" if score >= 3 else "#FFCC00" if score >= 2 else "#FF4444"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="label">🎯 APROVAÇÃO TÁTICA</div>
                    <div style="font-size:48px; font-weight:900; color:{color};">{score}/4</div>
                    <div class="progress-container"><div class="progress-bar" style="width:{pct}%; background:{color};"></div></div>
                    <div style="font-size:12px; margin-top:10px; color:#8A94A6;">
                        {'✅' if details['regime'] else '❌'} Regime Alinhado<br>
                        {'✅' if details['vix'] else '❌'} VIX Confirmando<br>
                        {'✅' if details['space'] else '❌'} Espaço p/ Alvo<br>
                        {'✅' if details['spy'] else '❌'} Sincronia SPY
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"<div class='metric-card'><div class='label'>MT5 PRICE ({tipo_ativo[:6]})</div><code>{es_spot:.2f}</code></div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='label'>🎯 GATILHO DE EXECUÇÃO SNIPER</div>", unsafe_allow_html=True)
                direction = "SHORT 📉" if regime == "NEGATIVO" else "LONG 📈"
                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid {'#FF4444' if 'SHORT' in direction else '#00FFAA'};">
                    <h2 style="margin:0; color:{'#FF4444' if 'SHORT' in direction else '#00FFAA'};">{direction}</h2>
                    <p style="color:#FFF; font-weight:700; margin-top:10px;">GATILHO: Pullback na VWAP ou Zero Gama ({spx['zg']+basis:.2f})</p>
                    <p style="color:#8A94A6; font-size:13px;">Aguarde o preço encostar na linha rosa do MT5 e deixar um pavio de rejeição antes de clicar.</p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🖥️ TRADINGVIEW CODE (PINE SCRIPT)"):
                    def v(k): val = spx.get(k); return round(val + basis, 2) if pd.notna(val) else 0.0
                    st.code(f"""//@version=5
indicator("GEX ULTRA ELITE v5.8", overlay=true)
zg = input.float({v('zg')}, "Zero Gama")
pw0 = input.float({v('pw0')}, "Put Wall 0DTE")
cw0 = input.float({v('cw0')}, "Call Wall 0DTE")
vt = input.float({v('vt')}, "Vol Trigger")
plot(zg, "ZG", color=color.white, linewidth=2)
plot(pw0, "PW0", color=color.green, linewidth=2, style=plot.style_cross)
plot(cw0, "CW0", color=color.red, linewidth=2, style=plot.style_cross)
plot(vt, "VT", color=color.aqua, linewidth=1)
""", language="pine")

            # Grid de Níveis (L1, C1, C4 etc)
            st.markdown("---")
            col_l, col_r = st.columns(2)
            def fmt(val): return f"{round((val+basis)*4)/4:.2f}" if pd.notna(val) else "0.00"
            with col_l:
                st.markdown("<div class='label'>📊 MICROESTRUTURA 0DTE</div>", unsafe_allow_html=True)
                st.write("Call Wall 0DTE"); st.code(fmt(spx['cw0']))
                st.write("Put Wall 0DTE"); st.code(fmt(spx['pw0']))
                st.write("Vol Trigger"); st.code(fmt(spx['vt']))
            with col_r:
                st.markdown("<div class='label'>🎯 ALVOS ESTRUTURAIS</div>", unsafe_allow_html=True)
                st.write("Nível L1 (Target Up)"); st.code(fmt(spx['l1']))
                st.write("Nível C1 (Target Down)"); st.code(fmt(spx['c1']))
                st.write("Nível C4 (Exaustão)"); st.code(fmt(spx['c4']))

            # Gráfico Profile
            df_chart = spx['dfAgg'][(spx['dfAgg'].index >= spx['spot']*0.95) & (spx['dfAgg'].index <= spx['spot']*1.05)].reset_index()
            df_chart['StrikePrice'] += basis
            chart = alt.Chart(df_chart).mark_bar().encode(
                y=alt.Y('StrikePrice:O', sort='descending'),
                x='TotalG:Q',
                color=alt.Color('TotalG:Q', scale=alt.Scale(domain=[-10,0,10], range=['#FF4444','#333','#00FFAA']))
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
