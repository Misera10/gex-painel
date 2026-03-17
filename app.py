import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import requests
import re
import yfinance as yf

# Configuração e Injeção de CSS Institucional
st.set_page_config(page_title="GEX ULTRA ELITE", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; }
    div[data-testid="stMetricValue"], code { color: #00FFAA !important; font-family: 'Courier New', monospace; font-size: 20px;}
    p { color: #8A94A6; font-weight: bold; margin-bottom: 2px;}
    .titulo { text-align: center; color: #FFFFFF; font-family: 'Arial', sans-serif; font-weight: 800; padding-bottom: 20px;}
    hr { border-color: #2b313f; margin-top: 10px; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

def calcGammaEx(S, K, vol, T, r, q, optType, OI):
    K, vol, T, OI = map(lambda x: np.asarray(x, dtype=float), [K, vol, T, OI])
    result = np.zeros_like(K, dtype=float)
    valid = (T > 0) & (vol > 0) & (K > 0) & np.isfinite(T) & np.isfinite(vol) & np.isfinite(K)
    if not np.any(valid): return result
    Kv, vv, Tv, OIv = K[valid], vol[valid], T[valid], OI[valid]
    sqrtT = np.sqrt(Tv)
    dp = (np.log(S / Kv) + (r - q + 0.5 * vv**2) * Tv) / (vv * sqrtT)
    dm = dp - vv * sqrtT
    if optType == "call":
        gamma = np.exp(-q * Tv) * norm.pdf(dp) / (S * vv * sqrtT)
        result[valid] = OIv * 100 * S * S * 0.01 * gamma
    else:
        gamma = Kv * np.exp(-r * Tv) * norm.pdf(dm) / (S * S * vv * sqrtT)
        result[valid] = OIv * 100 * S * S * 0.01 * gamma
    return result

def fetch_json(symbol="SPX"):
    headers = {"User-Agent": "Mozilla/5.0"}
    for s in [symbol, f"_{symbol}"]:
        try:
            r = requests.get(f"https://cdn.cboe.com/api/global/delayed_quotes/options/{s}.json", headers=headers, timeout=10)
            r.raise_for_status()
            return r.json()
        except: continue
    raise Exception("Falha na conexão com a CBOE.")

st.markdown("<h1 class='titulo'>⚡ GEX ULTRA ELITE TERMINAL</h1>", unsafe_allow_html=True)

if st.button("INICIAR EXTRAÇÃO AUTOMÁTICA"):
    with st.spinner("Sincronizando dados institucionais (CBOE, VIX & 0DTE)..."):
        try:
            data = fetch_json("SPX")
            spotPrice = data["data"].get("current_price", data["data"].get("last"))
            
            # Extração VIX
            vix_hist = yf.Ticker("^VIX").history(period="1mo")["Close"]
            vix_spot = float(vix_hist.iloc[-1])
            vix_avg = float(vix_hist.mean())
            
            trend_vix = f"⬆️ Acima da média ({vix_avg:.2f})" if vix_spot > vix_avg else f"⬇️ Abaixo da média ({vix_avg:.2f})"
            if vix_spot < 16: regime_vix = "REVERSÃO À MÉDIA (Operar Exaustão)"
            elif vix_spot <= 20: regime_vix = "DIRECIONAL (Operar Pullbacks)"
            else: regime_vix = "ROMPIMENTO / PERIGO (Operar a favor do Fluxo)"

            # Processamento CBOE
            df_raw = pd.DataFrame(data["data"]["options"])
            parsed = df_raw["option"].apply(lambda x: re.search(r'^(.*?)(\d{6})([CP])(\d{8})$', x))
            df_raw["ExpirationDate"] = pd.to_datetime(parsed.apply(lambda m: m.group(2) if m else None), format="%y%m%d") + timedelta(hours=16)
            df_raw["OptionType"] = parsed.apply(lambda m: m.group(3) if m else None)
            df_raw["StrikePrice"] = parsed.apply(lambda m: int(m.group(4))/1000.0 if m else np.nan)
            
            for col in ["iv", "gamma", "open_interest"]: df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce").fillna(0)
            calls = df_raw[df_raw["OptionType"] == "C"].rename(columns={"iv": "CallIV", "gamma": "CallGamma", "open_interest": "CallOpenInt"})
            puts = df_raw[df_raw["OptionType"] == "P"].rename(columns={"iv": "PutIV", "gamma": "PutGamma", "open_interest": "PutOpenInt"})
            
            df = pd.merge(calls[["ExpirationDate", "StrikePrice", "CallIV", "CallGamma", "CallOpenInt"]], puts[["ExpirationDate", "StrikePrice", "PutIV", "PutGamma", "PutOpenInt"]], on=["ExpirationDate", "StrikePrice"], how="outer").fillna(0)
            df['TotalGamma'] = ((df['CallGamma'] * df['CallOpenInt'] * 100 * spotPrice**2 * 0.01) - (df['PutGamma'] * df['PutOpenInt'] * 100 * spotPrice**2 * 0.01)) / 1e9
            
            # Cálculo Macro (Todos os Vencimentos)
            dfAgg = df.groupby(['StrikePrice']).sum(numeric_only=True)
            c_wall = dfAgg['TotalGamma'].idxmax()
            p_wall = dfAgg['TotalGamma'].idxmin()

            # --- CÁLCULO MICRO (0DTE) ---
            min_exp = df['ExpirationDate'].min()
            df_0dte = df[df['ExpirationDate'] == min_exp]
            dfAgg_0dte = df_0dte.groupby(['StrikePrice']).sum(numeric_only=True)
            c_wall_0dte = dfAgg_0dte['TotalGamma'].idxmax() if not dfAgg_0dte.empty else np.nan
            p_wall_0dte = dfAgg_0dte['TotalGamma'].idxmin() if not dfAgg_0dte.empty else np.nan

            # Cálculo Basis ES
            try: es_spot = float(yf.Ticker("ES=F").history(period="1d")["Close"].iloc[-1])
            except: es_spot = spotPrice
            basis = es_spot - spot
