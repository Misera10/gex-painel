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
# CONFIGURAÇÃO E DESIGN COMPACTO
# ============================================================================
st.set_page_config(page_title="GEX ULTRA ELITE TERMINAL", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1a1f2e 100%); font-family: 'Segoe UI', sans-serif; }
    .metric-card { background: rgba(30, 34, 45, 0.85); border: 1px solid rgba(0, 255, 170, 0.2); border-radius: 12px; padding: 20px; margin: 5px 0; backdrop-filter: blur(10px); }
    .metric-card:hover { border-color: #00FFAA; box-shadow: 0 8px 25px rgba(0, 255, 170, 0.2); }
    .gradient-title { background: linear-gradient(90deg, #00FFAA, #00D4FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 32px; margin: 0; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; margin: 2px; }
    .badge-positive { background: rgba(0, 255, 170, 0.15); color: #00FFAA; border: 1px solid rgba(0, 255, 170, 0.3); }
    .badge-negative { background: rgba(255, 68, 68, 0.15); color: #FF4444; border: 1px solid rgba(255, 68, 68, 0.3); }
    code { color: #00FFAA !important; font-size: 24px !important; font-weight: 900 !important; display: block; text-align: center; background: #161a25 !important; border: 1px solid #00FFAA33; border-radius: 8px; margin: 5px 0; }
    .label { color: #8A94A6; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
    .header-box { background: rgba(30, 34, 45, 0.9); padding: 15px; border-radius: 12px; border: 1px solid rgba(0, 255, 170, 0.2); margin-bottom: 10px; }
    .progress-container { background: #2b313f; border-radius: 6px; height: 8px; overflow: hidden; margin: 8px 0; }
    .progress-bar { background: linear-gradient(90deg, #00FFAA, #00D4FF); height: 100%; transition: width 0.5s ease; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# MOTOR MATEMÁTICO E RESILIÊNCIA DE API COM DEBUG
# ============================================================================
@st.cache_data(ttl=300)
def calcGammaEx(S, K, vol, T, r, q, optType, OI):
    K, vol, T, OI = map(lambda x: np.asarray(x, dtype=float), [K, vol, T, OI])
    result = np.zeros_like(K, dtype=float)
    valid = (T > 0) & (vol > 0) & (K > 0)
    if not np.any(valid): return result
    Kv, vv, Tv, OIv = K[valid], vol[valid], T[valid], OI[valid]
    dp = (np.log(S/Kv) + (r-q+0.5*vv**2)*Tv) / (vv*np.sqrt(Tv))
    dm = dp - vv*np.sqrt(Tv)
    gamma = np.exp(-q*Tv)*norm.pdf(dp)/(S*vv*np.sqrt(Tv)) if optType=="call" else Kv*np.exp(-r*Tv)*norm.pdf(dm)/(S*S*vv*np.sqrt(Tv))
    result[valid] = OIv * 100 * S * S * 0.01 * gamma
    return result

def fetch_cboe(symbol="SPX"):
    """Busca dados da CBOE com headers completos e debug ✅"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    try:
        # ✅ URL CORRETA SEM ESPAÇOS
        url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.
