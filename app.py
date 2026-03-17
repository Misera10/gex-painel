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
    code { color: #00FFAA !important; font-family: 'Courier New', monospace; font-size: 34px !important; font-weight: 900 !important; padding: 15px !important; display: block; text-align: center; border-radius: 8px; background-color: #161a25 !important; border: 1px solid #2b313f;}
    p { color: #8A94A6; font-weight: bold; margin-bottom: 2px; font-size: 15px;}
    .titulo { text-align: center; color: #FFFFFF; font-family: 'Arial', sans-serif; font-weight: 800; padding-bottom: 20px;}
    hr { border-color: #2b313f; margin-top: 10px; margin-bottom: 20px;}
    .destaque { color: #FFF; font-weight: bold; }
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
    with st.spinner("Processando GEX, VIX Term Structure e 0DTE..."):
        try:
            data = fetch_json("SPX")
            spotPrice = data["data"].get("current_price", data["data"].get("last"))
            
            # Extração VIX e VIX9D (Term Structure)
            vix_spot = float(yf.Ticker("^VIX").history(period="1d")["Close"].iloc[-1])
            vix9d_spot = float(yf.Ticker("^VIX9D").history(period="1d")["Close"].iloc[-1])
            vix_hist = yf.Ticker("^VIX").history(period="1mo")["Close"]
            vix_avg = float(vix_hist.mean())
            
            trend_vix = f"⬆️ Acima da média ({vix_avg:.2f})" if vix_spot > vix_avg else f"⬇️ Abaixo da média ({vix_avg:.2f})"
            
            if vix9d_spot > vix_spot:
                term_structure = f"🔴 INVERTIDA (VIX9D {vix9d_spot:.2f} > VIX {vix_spot:.2f}) - ALERTA DE ESTRESSE"
            else:
                term_structure = f"🟢 NORMAL (VIX9D {vix9d_spot:.2f} < VIX {vix_spot:.2f}) - CONTANGO"

            if vix_spot < 16: regime_vix = "REVERSÃO À MÉDIA (Operar Exaustão)"
            elif vix_spot <= 20: regime_vix = "DIRECIONAL (Operar Pullbacks)"
            else: regime_vix = "ROMPIMENTO / PERIGO (Operar a favor do Fluxo)"

            # Relógio de Expiração 0DTE (Fuso de NY)
            now_et = pd.Timestamp.now('US/Eastern')
            close_et = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
            if now_et > close_et:
                timer_0dte = "MERCADO FECHADO"
            else:
                diff = close_et - now_et
                h, rem = divmod(diff.seconds, 3600)
                m, s = divmod(rem, 60)
                timer_0dte = f"{h:02d}h {m:02d}m restantes (Fechamento às 16:00 ET)"

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
            
            # Cálculo Macro
            dfAgg = df.groupby(['StrikePrice']).sum(numeric_only=True)
            c_wall = dfAgg['TotalGamma'].idxmax()
            p_wall = dfAgg['TotalGamma'].idxmin()

            # Cálculo Micro (0DTE)
            min_exp = df['ExpirationDate'].min()
            df_0dte = df[df['ExpirationDate'] == min_exp]
            dfAgg_0dte = df_0dte.groupby(['StrikePrice']).sum(numeric_only=True)
            c_wall_0dte = dfAgg_0dte['TotalGamma'].idxmax() if not dfAgg_0dte.empty else np.nan
            p_wall_0dte = dfAgg_0dte['TotalGamma'].idxmin() if not dfAgg_0dte.empty else np.nan

            # Basis ES
            try: es_spot = float(yf.Ticker("ES=F").history(period="1d")["Close"].iloc[-1])
            except: es_spot = spotPrice
            basis = es_spot - spotPrice

            # Zero Gama e Níveis de Fluxo
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

            regime_gama = "POSITIVO" if spotPrice > z_gama else "NEGATIVO"
            cor_gama = "#00FFAA" if spotPrice > z_gama else "#FF4444"

            # Interface de Usuário Atualizada
            st.markdown(f"""
            <div style='background-color:#1E222D; padding:20px; border-radius:10px; border-left: 5px solid {cor_gama}; margin-bottom: 25px;'>
                <h3 style='margin:0; color:white; font-family: Arial;'>REGIME GEX: <span style='color:{cor_gama}'>{regime_gama}</span></h3>
                <hr style='border-color:#2b313f; margin:10px 0;'>
                <p style='margin:5px 0; color:#8A94A6; font-size: 16px;'>ESTRATÉGIA DO DIA: <span class='destaque'>{regime_vix}</span></p>
                <p style='margin:5px 0; color:#8A94A6; font-size: 16px;'>VIX TERM STRUCTURE: <span class='destaque'>{term_structure}</span></p>
                <p style='margin:5px 0; color:#8A94A6; font-size: 16px;'>TEMPO DE EXPIRAÇÃO 0DTE: <span class='destaque' style='color:#E2B714;'>⏱️ {timer_0dte}</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<h4 style='color:#FFF;'>⏱️ MURALHAS 0DTE (Microestrutura)</h4>", unsafe_allow_html=True)
            c0_col, p0_col = st.columns(2)
            with c0_col:
                st.write("CALL WALL 0DTE (Resistência Intraday)")
                st.code(fmt(c_wall_0dte))
            with p0_col:
                st.write("PUT WALL 0DTE (Suporte Intraday)")
                st.code(fmt(p_wall_0dte))
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            st.markdown("<h4 style='color:#FFF;'>🛡️ NÍVEIS MACRO E FLUXO (Estrutural)</h4>", unsafe_allow_html=True)
            c1_col, c2_col = st.columns(2)
            with c1_col:
                st.write("CALL WALL PRINCIPAL")
                st.code(fmt(c_wall))
                st.write("ZERO GAMA (FLIP)")
                st.code(fmt(z_gama, True))
                st.write("PUT WALL PRINCIPAL")
                st.code(fmt(p_wall))
                st.write("VOL TRIGGER")
                st.code(fmt(vt))
            with c2_col:
                st.write("NÍVEL L1 (Alvo Alto)")
                st.code(fmt(l1))
                st.write("NÍVEL C1 (Alvo Baixo)")
                st.code(fmt(c1))
                st.write("NÍVEL C4 (Exaustão Extrema)")
                st.code(fmt(c4))

        except Exception as e: st.error(f"Erro de processamento: {e}")
