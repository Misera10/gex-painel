import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import requests
import re
import yfinance as yf

# Configuração da Página
st.set_page_config(page_title="GEX ULTRA ELITE", layout="wide")

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
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/plain,*/*"}
    for s in [symbol, f"_{symbol}"]:
        try:
            r = requests.get(f"https://cdn.cboe.com/api/global/delayed_quotes/options/{s}.json", headers=headers, timeout=10)
            r.raise_for_status()
            return r.json()
        except: continue
    raise Exception("Falha ao conectar com a CBOE.")

st.title("🎯 GEX ULTRA ELITE - Painel Operacional")
st.write("Clique no ícone à direita de cada valor para copiar rapidamente.")

if st.button("🚀 GERAR TAXAS ATUALIZADAS"):
    with st.spinner("Buscando dados na CBOE..."):
        try:
            data = fetch_json("SPX")
            spotPrice = data["data"].get("current_price", data["data"].get("last"))
            df_raw = pd.DataFrame(data["data"]["options"])
            
            parsed = df_raw["option"].apply(lambda x: re.search(r'^(.*?)(\d{6})([CP])(\d{8})$', x))
            df_raw["ExpirationDate"] = pd.to_datetime(parsed.apply(lambda m: m.group(2) if m else None), format="%y%m%d") + timedelta(hours=16)
            df_raw["OptionType"] = parsed.apply(lambda m: m.group(3) if m else None)
            df_raw["StrikePrice"] = parsed.apply(lambda m: int(m.group(4))/1000.0 if m else np.nan)
            
            for col in ["iv", "gamma", "open_interest"]: df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce").fillna(0)

            calls = df_raw[df_raw["OptionType"] == "C"].rename(columns={"iv": "CallIV", "gamma": "CallGamma", "open_interest": "CallOpenInt"})
            puts = df_raw[df_raw["OptionType"] == "P"].rename(columns={"iv": "PutIV", "gamma": "PutGamma", "open_interest": "PutOpenInt"})
            
            df = pd.merge(calls[["ExpirationDate", "StrikePrice", "CallIV", "CallGamma", "CallOpenInt"]],
                          puts[["ExpirationDate", "StrikePrice", "PutIV", "PutGamma", "PutOpenInt"]], 
                          on=["ExpirationDate", "StrikePrice"], how="outer").fillna(0)
            
            df['TotalGamma'] = ((df['CallGamma'] * df['CallOpenInt'] * 100 * spotPrice**2 * 0.01) - 
                                (df['PutGamma'] * df['PutOpenInt'] * 100 * spotPrice**2 * 0.01)) / 1e9
            
            dfAgg = df.groupby(['StrikePrice']).sum(numeric_only=True)
            try: es_spot = float(yf.Ticker("ES=F").history(period="1d")["Close"].iloc[-1])
            except: es_spot = spotPrice
            basis = es_spot - spotPrice

            c_wall = dfAgg['TotalGamma'].idxmax()
            p_wall = dfAgg['TotalGamma'].idxmin()

            # Cálculo Zero Gama
            df["daysTillExp"] = np.where(df["ExpirationDate"].dt.date == datetime.now().date(), 1/262, np.busday_count(datetime.now().date(), df["ExpirationDate"].dt.date.values.astype('datetime64[D]')) / 262)
            df_calc = df[df['daysTillExp'] > 0]
            levels = np.arange(np.floor(spotPrice * 0.8 / 5) * 5, np.ceil(spotPrice * 1.2 / 5) * 5 + 5, 5.0)

            totalGamma = []
            for level in levels:
                cg = calcGammaEx(level, df_calc['StrikePrice'], df_calc['CallIV'].replace(0,0.15), df_calc['daysTillExp'], 0, 0, "call", df_calc['CallOpenInt'])
                pg = calcGammaEx(level, df_calc['StrikePrice'], df_calc['PutIV'].replace(0,0.15), df_calc['daysTillExp'], 0, 0, "put", df_calc['PutOpenInt'])
                totalGamma.append((cg - pg).sum() / 1e9)

            zeroCrossIdx = np.where(np.diff(np.sign(totalGamma)) != 0)[0]
            z_gama = float(levels[zeroCrossIdx[0]] - totalGamma[zeroCrossIdx[0]] * (levels[zeroCrossIdx[0] + 1] - levels[zeroCrossIdx[0]]) / (totalGamma[zeroCrossIdx[0] + 1] - totalGamma[zeroCrossIdx[0]])) if len(zeroCrossIdx) > 0 else np.nan

            df_filt = dfAgg[(dfAgg.index >= spotPrice * 0.8) & (dfAgg.index <= spotPrice * 1.2)]
            top_calls = df_filt['TotalGamma'].nlargest(3).index.tolist()
            l1 = top_calls[1] if (len(top_calls) > 1 and top_calls[0] == c_wall) else (top_calls[0] if len(top_calls)>0 else np.nan)
            
            c1 = df_filt[df_filt.index > p_wall]['TotalGamma'].idxmin() if not df_filt[df_filt.index > p_wall].empty else np.nan
            c4 = df_filt[df_filt.index < p_wall]['TotalGamma'].idxmin() if not df_filt[df_filt.index < p_wall].empty else np.nan
            vt = df_filt[(df_filt.index > p_wall) & (df_filt.index < z_gama)]['TotalGamma'].idxmin() if not df_filt[(df_filt.index > p_wall) & (df_filt.index < z_gama)].empty else np.nan

            def fmt(val, is_zg=False):
                if pd.isna(val): return "0.00"
                adj = val + basis
                return f"{round(adj * 4) / 4:.2f}" if is_zg else f"{round(adj / 5) * 5:.0f}"

            st.divider()
            
            # Interface com botões de cópia
            c1_col, c2_col = st.columns(2)
            
            with c1_col:
                st.subheader("🛡️ Defesas Principais")
                st.write("**CALL WALL (VENDER)**")
                st.code(fmt(c_wall), language="text")
                
                st.write("**ZERO GAMA (FLIP)**")
                st.code(fmt(z_gama, True), language="text")
                
                st.write("**PUT WALL (COMPRAR)**")
                st.code(fmt(p_wall), language="text")

            with c2_col:
                st.subheader("📊 Níveis de Fluxo")
                st.write("**VOL TRIGGER**")
                st.code(fmt(vt), language="text")
                
                st.write("**NÍVEL L1**")
                st.code(fmt(l1), language="text")
                
                st.write("**NÍVEL C1**")
                st.code(fmt(c1), language="text")
                
                st.write("**NÍVEL C4**")
                st.code(fmt(c4), language="text")

            st.divider()
            st.info(f"Basis (ES-SPX): {basis:.2f} | Spot: {spotPrice:.2f}")

        except Exception as e:
            st.error(f"Erro: {e}")
