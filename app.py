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
        url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"
        st.sidebar.info(f"🔍 Conectando...")
        
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            st.sidebar.success(f"✅ Conexão OK")
            return r.json()
        elif r.status_code == 403:
            st.sidebar.error("❌ Bloqueio 403: CBOE bloqueou o acesso")
            st.sidebar.warning("💡 Tente: VPN, aguarde 30min, ou outra rede")
            return None
        elif r.status_code == 404:
            st.sidebar.error(f"❌ Endpoint não encontrado")
            return None
        else:
            st.sidebar.error(f"❌ Erro {r.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.sidebar.error("⏱️ Timeout: Conexão muito lenta")
        return None
    except requests.exceptions.ConnectionError:
        st.sidebar.error("🌐 Erro de conexão: Verifique internet/firewall")
        return None
    except Exception as e:
        st.sidebar.error(f"❌ Erro: {type(e).__name__}")
        return None

def process_levels(data):
    if not data or "data" not in data: 
        return None
    try:
        spot = data["data"].get("current_price", data["data"].get("last"))
        if not spot:
            st.error("❌ Preço não encontrado na resposta da CBOE")
            return None
            
        df = pd.DataFrame(data["data"]["options"])
        if df.empty:
            st.warning("⚠️ Nenhuma opção encontrada")
            return None
            
        parsed = df["option"].apply(lambda x: re.search(r'^(.*?)(\d{6})([CP])(\d{8})$', x))
        df["Exp"] = pd.to_datetime(parsed.apply(lambda m: m.group(2) if m else None), format="%y%m%d") + timedelta(hours=16)
        df["Type"] = parsed.apply(lambda m: m.group(3) if m else None)
        df["Strike"] = parsed.apply(lambda m: int(m.group(4))/1000.0 if m else np.nan)
        
        for c in ["iv", "gamma", "open_interest"]: 
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
            
        calls = df[df["Type"]=="C"].rename(columns={"iv":"CallIV","gamma":"CallG","open_interest":"CallOI"})
        puts = df[df["Type"]=="P"].rename(columns={"iv":"PutIV","gamma":"PutG","open_interest":"PutOI"})
        dff = pd.merge(calls, puts, on=["Exp", "Strike"], how="outer").fillna(0)
        
        dff['TotalG'] = ((dff['CallG']*dff['CallOI']*100*spot**2*0.01)-(dff['PutG']*dff['PutOI']*100*spot**2*0.01))/1e9
        dfAgg = dff.groupby(['Strike']).sum(numeric_only=True)
        
        cw, pw = dfAgg['TotalG'].idxmax(), dfAgg['TotalG'].idxmin()
        min_exp = dff['Exp'].min()
        df0 = dff[dff['Exp']==min_exp].groupby(['Strike']).sum(numeric_only=True)
        cw0 = df0['TotalG'].idxmax() if not df0.empty else 0
        pw0 = df0['TotalG'].idxmin() if not df0.empty else 0
        
        dff["T"] = np.where(dff["Exp"].dt.date==datetime.now().date(), 1/262, 
                           np.busday_count(datetime.now().date(), dff["Exp"].dt.date.values.astype('datetime64[D]'))/262)
        dfc = dff[dff['T']>0]
        
        l_rng = np.arange(np.floor(spot*0.8/5)*5, np.ceil(spot*1.2/5)*5+5, 5.0)
        tg = [(calcGammaEx(l,dfc['Strike'],dfc['CallIV'].replace(0,0.15),dfc['T'],0,0,"call",dfc['CallOI'])
              -calcGammaEx(l,dfc['Strike'],dfc['PutIV'].replace(0,0.15),dfc['T'],0,0,"put",dfc['PutOI'])).sum()/1e9 
              for l in l_rng]
        
        zc = np.where(np.diff(np.sign(tg))!=0)[0]
        zg = float(l_rng[zc[0]]-tg[zc[0]]*5.0/(tg[zc[0]+1]-tg[zc[0]])) if len(zc)>0 else spot
        
        df_f = dfAgg[(dfAgg.index>=spot*0.9)&(dfAgg.index<=spot*1.1)]
        top2 = df_f['TotalG'].nlargest(2)
        l1 = top2.index.tolist()[-1] if len(top2) > 1 else cw
        c1 = df_f[df_f.index>pw]['TotalG'].idxmin() if not df_f[df_f.index>pw].empty else pw
        c4 = df_f[df_f.index<pw]['TotalG'].idxmin() if not df_f[df_f.index<pw].empty else pw
        vt = df_f[(df_f.index>pw)&(df_f.index<zg)]['TotalG'].idxmin() if not df_f[(df_f.index>pw)&(df_f.index<zg)].empty else np.nan
        
        return {'spot':spot, 'cw':cw, 'pw':pw, 'cw0':cw0, 'pw0':pw0, 'zg':zg, 'l1':l1, 'c1':c1, 'c4':c4, 'vt':vt, 'dfAgg':dfAgg}
        
    except Exception as e:
        st.error(f"❌ Erro no processamento: {type(e).__name__}: {str(e)[:200]}")
        return None

# ============================================================================
# APP PRINCIPAL
# ============================================================================
st.markdown("<div style='text-align:center; padding-bottom:10px;'><h1 class='gradient-title'>⚡ GEX ULTRA ELITE v5.9.3 DEBUG</h1></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ CONFIGURAÇÃO")
    tipo_ativo = st.radio("MT5 Asset:", ["SPX500.x (CFD/Mesa)", "ES (Futuro CME)"])
    modo_spy = st.checkbox("Sincronia ETF SPY", value=True)
    st.markdown("---")
    st.caption("✅ Debug Mode Active • Production Ready")

if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL COMPLETA", use_container_width=True, type="primary"):
    with st.spinner("⚡ Calibrando Dados Institucionais..."):
        
        # Teste de conexão inicial
        st.sidebar.markdown("### 🔍 Diagnóstico de Conexão")
        try:
            test_url = "https://cdn.cboe.com/api/global/delayed_quotes/options/SPX.json"
            test_r = requests.get(test_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            st.sidebar.success(f"✅ CBOE Acessível (Status {test_r.status_code})")
        except Exception as e:
            st.sidebar.error(f"❌ CBOE Inacessível: {e}")
            st.error("🌐 Problema de conexão com a CBOE. Verifique:")
            st.info("1. Sua internet\n2. Firewall/VPN corporativo\n3. Tente usar VPN (EUA)\n4. Aguarde 10-15 minutos")
            st.stop()
        
        spx = process_levels(fetch_cboe("SPX"))
        
        if spx:
            spy = process_levels(fetch_cboe("SPY")) if modo_spy else None
            try:
                vx = yf.Ticker("^VIX").history(period="1d")["Close"].iloc[-1]
                vx9 = yf.Ticker("^VIX9D").history(period="1d")["Close"].iloc[-1]
            except: 
                vx, vx9 = 20.0, 20.0
            
            if "CFD" in tipo_ativo: 
                basis, es_spot = 0.0, spx['spot']
            else:
                try: 
                    es_spot = yf.Ticker("ES=F").history(period="1d")["Close"].iloc[-1]
                    basis = es_spot - spx['spot']
                except: 
                    es_spot, basis = spx['spot'], 0.0
                
            score, det = 0, {'regime':False, 'vix':False, 'space':False, 'spy':False}
            reg = "POSITIVO" if spx['spot'] > spx['zg'] else "NEGATIVO"
            
            if reg == "NEGATIVO" and spx['spot'] < spx['zg']: score+=1; det['regime']=True
            elif reg == "POSITIVO" and spx['spot'] > spx['zg']: score+=1; det['regime']=True
            
            if vx9 > vx and reg == "NEGATIVO": score+=1; det['vix']=True
            elif vx9 < vx and reg == "POSITIVO": score+=1; det['vix']=True
            
            if abs(spx['spot'] - spx['pw0']) > 5: score+=1; det['space']=True
            if spy and abs(spy['spot'] - spy['pw']) < 1.5: score+=1; det['spy']=True
            
            st.markdown(f"""<div class='header-box'>
                <h3 style='margin:0;'>REGIME GEX: <span style='color:{'#00FFAA' if reg=='POSITIVO' else '#FF4444'}'>{reg}</span> 
                | VIX Curve: {'🔴 Invertida' if vx9>vx else '🟢 Normal'} ({vx:.2f})</h3>
            </div>""", unsafe_allow_html=True)
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"""<div class="metric-card">
                    <div class="label">🎯 SCORE TÁTICO</div>
                    <div style="font-size:48px; font-weight:900; color:#00FFAA;">{score}/4</div>
                    <div class="progress-container"><div class="progress-bar" style="width:{(score/4)*100}%; background:#00FFAA;"></div></div>
                    <div style="font-size:11px; color:#8A94A6;">
                        {'✅' if det['regime'] else '❌'} Regime | {'✅' if det['vix'] else '❌'} VIX | 
                        {'✅' if det['space'] else '❌'} Espaço | {'✅' if det['spy'] else '❌'} SPY
                    </div>
                </div>""", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-card'><div class='label'>MT5 PRICE ({tipo_ativo[:6]})</div><code>{es_spot:.2f}</code></div>", unsafe_allow_html=True)
                
            with c2:
                st.markdown(f"""<div class="metric-card" style="border-left:5px solid {'#FF4444' if reg=='NEGATIVO' else '#00FFAA'};">
                    <h2>{'SHORT 📉' if reg=='NEGATIVO' else 'LONG 📈'}</h2>
                    <p style="margin:5px 0;"><b>GATILHO:</b> Pullback na VWAP ou Zero Gama ({spx['zg']+basis:.2f})</p>
                    <small style="color:#8A94A6;">Aguarde o pavio de rejeição na linha rosa do MT5 antes da entrada.</small>
                </div>""", unsafe_allow_html=True)
                
                with st.expander("🖥️ PINE SCRIPT (TRADINGVIEW)"):
                    st.code(f"// ZG: {spx['zg']+basis:.2f}\n// PW0: {spx['pw0']+basis:.2f}\n// VT: {spx['vt']+basis:.2f}\n// C1: {spx['c1']+basis:.2f}", language="pine")
            
            st.markdown("---")
            l, r = st.columns(2)
            f = lambda x: f"{round((x+basis)*4)/4:.2f}" if pd.notna(x) else "0.00"
            with l:
                st.write("Put Wall 0DTE (Suporte)")
                st.code(f(spx['pw0']))
                st.write("Vol Trigger (Alçapão)")
                st.code(f(spx['vt']))
            with r:
                st.write("Nível C1 (Alvo Curto)")
                st.code(f(spx['c1']))
                st.write("Nível C4 (Alvo Exaustão)")
                st.code(f(spx['c4']))
                
            df_ch = spx['dfAgg'][(spx['dfAgg'].index >= spx['spot']*0.95)&(spx['dfAgg'].index <= spx['spot']*1.05)].reset_index()
            df_ch['Strike'] += basis
            chart = alt.Chart(df_ch).mark_bar().encode(
                y=alt.Y('Strike:O', sort='descending'), 
                x='TotalG:Q', 
                color=alt.Color('TotalG:Q', scale=alt.Scale(domain=[-10,0,10], range=['#FF4444','#333','#00FFAA']))
            )
            st.altair_chart(chart.properties(height=350), use_container_width=True)
        else:
            st.error("❌ Erro ao processar dados da CBOE. Verifique o sidebar para diagnóstico.")
            st.info("💡 **Soluções:**\n1. Use VPN (conecte em EUA)\n2. Aguarde 15-30 minutos\n3. Tente de outra rede (4G/5G)\n4. Verifique se firewall corporativo está bloqueando")
