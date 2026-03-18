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

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1a1f2e 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .metric-card { background: rgba(30, 34, 45, 0.85); border: 1px solid rgba(0, 255, 170, 0.2); border-radius: 12px; padding: 20px; margin: 10px 0; backdrop-filter: blur(10px); transition: all 0.3s ease; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); }
    .gradient-title { background: linear-gradient(90deg, #00FFAA, #00D4FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 32px; margin: 0; }
    .badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin: 2px; }
    .badge-positive { background: rgba(0, 255, 170, 0.15); color: #00FFAA; border: 1px solid rgba(0, 255, 170, 0.3); }
    .badge-negative { background: rgba(255, 68, 68, 0.15); color: #FF4444; border: 1px solid rgba(255, 68, 68, 0.3); }
    .badge-warning { background: rgba(255, 204, 0, 0.15); color: #FFCC00; border: 1px solid rgba(255, 204, 0, 0.3); }
    .badge-info { background: rgba(0, 212, 255, 0.15); color: #00D4FF; border: 1px solid rgba(0, 212, 255, 0.3); }
    code { color: #00FFAA !important; font-size: 28px !important; font-weight: 900 !important; text-align: center; display: block; background: #161a25 !important; border: 1px solid #00FFAA33; }
    .label { color: #8A94A6; font-weight: 600; font-size: 13px; text-transform: uppercase; }
    .header-box { background: rgba(30, 34, 45, 0.9); padding: 25px; border-radius: 12px; border: 1px solid rgba(0, 255, 170, 0.2); margin-bottom: 20px; }
    .progress-bar { height: 10px; border-radius: 6px; transition: width 0.5s ease; }
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
def fetch_json(symbol="SPX"):
    headers = {"User-Agent": "Mozilla/5.0"}
    for s in [symbol, f"_{symbol}"]:
        try:
            r = requests.get(f"https://cdn.cboe.com/api/global/delayed_quotes/options/{s}.json", headers=headers, timeout=10)
            if r.status_code == 200: return r.json()
        except: continue
    raise Exception("Falha CBOE")

def fetch_vix_data():
    try:
        v = float(yf.Ticker("^VIX").history(period="1d")["Close"].iloc[-1])
        v9 = float(yf.Ticker("^VIX9D").history(period="1d")["Close"].iloc[-1])
        return {'vix': v, 'vix9d': v9}
    except: return {'vix': 20.0, 'vix9d': 20.0}

def generate_pine_script(levels, basis, timestamp):
    def v(k): val = levels.get(k); return round(val + basis, 2) if pd.notna(val) and val > 0 else 0.0
    return f"""//@version=5
indicator("GEX ULTRA ELITE - {timestamp.strftime('%d/%m/%Y')}", overlay=true)
cw = input.float({v('c_wall')}, "Call Wall Macro")
zg = input.float({v('z_gama')}, "Zero Gama")
pw = input.float({v('p_wall')}, "Put Wall Macro")
vt = input.float({v('vt')}, "Vol Trigger")
cw0 = input.float({v('c_wall_0dte')}, "Call Wall 0DTE")
pw0 = input.float({v('p_wall_0dte')}, "Put Wall 0DTE")

plot(cw > 0 ? cw : na, "CW", color=color.red, linewidth=2)
plot(zg > 0 ? zg : na, "ZG", color=color.white, linewidth=2)
plot(pw > 0 ? pw : na, "PW", color=color.green, linewidth=2)
plot(vt > 0 ? vt : na, "VT", color=color.aqua, linewidth=1)
plot(cw0 > 0 ? cw0 : na, "CW0", color=color.new(color.red, 30), linewidth=2, style=plot.style_cross)
plot(pw0 > 0 ? pw0 : na, "PW0", color=color.new(color.green, 30), linewidth=2, style=plot.style_cross)
"""

# ============================================================================
# APP FLOW
# ============================================================================
st.markdown("<div style='text-align:center; padding: 20px 0;'><h1 class='gradient-title'>⚡ GEX ULTRA ELITE</h1><p class='subtitle'>Sincronização Automática Ativada</p></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ CONFIGURAÇÕES")
    tipo_ativo = st.radio("🎯 Qual ativo você opera no MT5?", ["SPX500.x (CFD / Mesa Proprietária)", "ES (Futuro CME)"], help="CFDs seguem o mercado à vista. Futuros seguem juros.")
    st.markdown("---")
    st.caption("🔐 GEX ULTRA ELITE v5.4 - Auto-Sync")

if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL", use_container_width=True, type="primary"):
    with st.spinner("⚡ Calculando derivativos e sincronizando..."):
        try:
            data = fetch_json("SPX")
            spotPrice = data["data"].get("current_price", data["data"].get("last"))
            vix_data = fetch_vix_data()
            
            # --- O PULO DO GATO: AUTO-SYNC DE CORRETORA ---
            if "CFD" in tipo_ativo:
                basis = 0.0  # CFDs seguem o SPX puro, sem ágio!
                es_spot = spotPrice
            else:
                try:
                    es_spot = float(yf.Ticker("ES=F").history(period="1d", interval="1m")["Close"].iloc[-1])
                    basis = es_spot - spotPrice
                except:
                    basis = 0.0
                    es_spot = spotPrice

            df = pd.DataFrame(data["data"]["options"])
            parsed = df["option"].apply(lambda x: re.search(r'^(.*?)(\d{6})([CP])(\d{8})$', x))
            df["ExpirationDate"] = pd.to_datetime(parsed.apply(lambda m: m.group(2) if m else None), format="%y%m%d") + timedelta(hours=16)
            df["OptionType"] = parsed.apply(lambda m: m.group(3) if m else None)
            df["StrikePrice"] = parsed.apply(lambda m: int(m.group(4))/1000.0 if m else np.nan)
            for col in ["iv", "gamma", "open_interest"]: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            
            calls = df[df["OptionType"] == "C"].rename(columns={"iv": "CallIV", "gamma": "CallGamma", "open_interest": "CallOpenInt"})
            puts = df[df["OptionType"] == "P"].rename(columns={"iv": "PutIV", "gamma": "PutGamma", "open_interest": "PutOpenInt"})
            dff = pd.merge(calls, puts, on=["ExpirationDate", "StrikePrice"], how="outer").fillna(0)
            dff['TotalGamma'] = ((dff['CallGamma'] * dff['CallOpenInt'] * 100 * spotPrice**2 * 0.01) - (dff['PutGamma'] * dff['PutOpenInt'] * 100 * spotPrice**2 * 0.01)) / 1e9
            
            dfAgg = dff.groupby(['StrikePrice']).sum(numeric_only=True)
            c_wall, p_wall = dfAgg['TotalGamma'].idxmax(), dfAgg['TotalGamma'].idxmin()
            
            min_exp = dff['ExpirationDate'].min()
            dfAgg_0dte = dff[dff['ExpirationDate'] == min_exp].groupby(['StrikePrice']).sum(numeric_only=True)
            c_wall_0dte = dfAgg_0dte['TotalGamma'].idxmax() if not dfAgg_0dte.empty else np.nan
            p_wall_0dte = dfAgg_0dte['TotalGamma'].idxmin() if not dfAgg_0dte.empty else np.nan

            dff["daysTillExp"] = np.where(dff["ExpirationDate"].dt.date == datetime.now().date(), 1/262, np.busday_count(datetime.now().date(), dff["ExpirationDate"].dt.date.values.astype('datetime64[D]')) / 262)
            df_calc = dff[dff['daysTillExp'] > 0]
            levels_range = np.arange(np.floor(spotPrice * 0.8 / 5) * 5, np.ceil(spotPrice * 1.2 / 5) * 5 + 5, 5.0)
            
            tg = [(calcGammaEx(l, df_calc['StrikePrice'], df_calc['CallIV'].replace(0,0.15), df_calc['daysTillExp'], 0, 0, "call", df_calc['CallOpenInt']) - 
                   calcGammaEx(l, df_calc['StrikePrice'], df_calc['PutIV'].replace(0,0.15), df_calc['daysTillExp'], 0, 0, "put", df_calc['PutOpenInt'])).sum() / 1e9 for l in levels_range]
            
            z_cross = np.where(np.diff(np.sign(tg)) != 0)[0]
            z_gama = float(levels_range[z_cross[0]] - tg[z_cross[0]] * 5.0 / (tg[z_cross[0] + 1] - tg[z_cross[0]])) if len(z_cross) > 0 else spotPrice
            
            df_filt = dfAgg[(dfAgg.index >= spotPrice * 0.8) & (dfAgg.index <= spotPrice * 1.2)]
            vt = df_filt[(df_filt.index > p_wall) & (df_filt.index < z_gama)]['TotalGamma'].idxmin() if not df_filt[(df_filt.index > p_wall) & (df_filt.index < z_gama)].empty else np.nan
            
            levels_dict = {'c_wall': c_wall, 'p_wall': p_wall, 'c_wall_0dte': c_wall_0dte, 'p_wall_0dte': p_wall_0dte, 'z_gama': z_gama, 'vt': vt}
            regime = "POSITIVO" if spotPrice > z_gama else "NEGATIVO"

            st.markdown(f"<div class='header-box'><h3>REGIME GEX: <span style='color:{'#00FFAA' if regime=='POSITIVO' else '#FF4444'}'>{regime}</span></h3></div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns([1,2])
            with c1:
                st.markdown(f"<div class='metric-card'><div class='label'>PREÇO SINCRONIZADO</div><code>{es_spot:.2f}</code><br><small style='color:#8A94A6;'>Modo: {tipo_ativo}</small></div>", unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="label">🖥️ EXPORTAÇÃO PARA TRADINGVIEW</div>', unsafe_allow_html=True)
                st.code(generate_pine_script(levels_dict, basis, datetime.now()), language="pine")

            df_chart = dfAgg[(dfAgg.index >= spotPrice * 0.95) & (dfAgg.index <= spotPrice * 1.05)].reset_index()
            df_chart['StrikePrice'] += basis
            
            ref = pd.DataFrame({'level': [es_spot, z_gama+basis, c_wall+basis, p_wall+basis], 'label': ['💰 Preço', '🔄 ZG', '🔴 CW', '🟢 PW'], 'color': ['#FFF', '#00FFAA', '#FF6B6B', '#4ECDC4']})
            chart = alt.Chart(df_chart).mark_bar(opacity=0.9).encode(
                y=alt.Y('StrikePrice:O', sort='descending', title='Strike'),
                x=alt.X('TotalGamma:Q', title='Net GEX'),
                color=alt.Color('TotalGamma:Q', scale=alt.Scale(domain=[-10, 0, 10], range=['#FF4444', '#333333', '#00FFAA']), legend=None)
            ) + alt.Chart(ref).mark_rule(strokeDash=[4,4], strokeWidth=2).encode(y='level:Q', color=alt.Color('color:N', scale=None))
            st.altair_chart(chart.properties(height=400).configure_view(strokeWidth=0), use_container_width=True)

        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
