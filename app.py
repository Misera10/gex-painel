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
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="GEX ULTRA ELITE TERMINAL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS PREMIUM - DESIGN PROFISSIONAL
# ============================================================================
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1a1f2e 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .metric-card { background: rgba(30, 34, 45, 0.85); border: 1px solid rgba(0, 255, 170, 0.2); border-radius: 12px; padding: 20px; margin: 10px 0; backdrop-filter: blur(10px); transition: all 0.3s ease; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); }
    .metric-card:hover { border-color: #00FFAA; box-shadow: 0 8px 25px rgba(0, 255, 170, 0.2); transform: translateY(-2px); }
    .gradient-title { background: linear-gradient(90deg, #00FFAA, #00D4FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 32px; margin: 0; }
    .subtitle { color: #8A94A6; font-size: 14px; margin: 5px 0 20px 0; }
    .badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin: 2px; }
    .badge-positive { background: rgba(0, 255, 170, 0.15); color: #00FFAA; border: 1px solid rgba(0, 255, 170, 0.3); }
    .badge-negative { background: rgba(255, 68, 68, 0.15); color: #FF4444; border: 1px solid rgba(255, 68, 68, 0.3); }
    .badge-warning { background: rgba(255, 204, 0, 0.15); color: #FFCC00; border: 1px solid rgba(255, 204, 0, 0.3); }
    .badge-info { background: rgba(0, 212, 255, 0.15); color: #00D4FF; border: 1px solid rgba(0, 212, 255, 0.3); }
    code { color: #00FFAA !important; font-family: 'Courier New', monospace; font-size: 28px !important; font-weight: 900 !important; padding: 15px !important; display: block; text-align: center; border-radius: 8px; background: linear-gradient(135deg, #161a25, #1f2533) !important; border: 2px solid #00FFAA33; box-shadow: 0 4px 15px rgba(0, 255, 170, 0.1); }
    .label { color: #8A94A6; font-weight: 600; margin-bottom: 8px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
    .header-box { background: linear-gradient(135deg, rgba(30, 34, 45, 0.9), rgba(26, 31, 46, 0.9)); padding: 25px; border-radius: 12px; border: 1px solid rgba(0, 255, 170, 0.2); margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4); }
    .progress-container { background: #2b313f; border-radius: 6px; height: 10px; overflow: hidden; margin: 10px 0; }
    .progress-bar { background: linear-gradient(90deg, #00FFAA, #00D4FF); height: 100%; border-radius: 6px; transition: width 0.5s ease; }
    .semaforo-alerta { background: linear-gradient(135deg, rgba(255, 204, 0, 0.1), rgba(255, 204, 0, 0.05)); border-left: 5px solid #FFCC00; padding: 15px 20px; border-radius: 8px; color: #FFCC00; font-weight: 700; font-size: 14px; margin: 15px 0; box-shadow: 0 2px 10px rgba(255, 204, 0, 0.1); }
    @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    .animate-slide-in { animation: slideIn 0.5s ease-out; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1a1f2e 0%, #0b0e14 100%); border-right: 1px solid #2b313f; }
    .stButton>button { background: linear-gradient(135deg, #00FFAA, #00D4FF); color: #0b0e14 !important; font-weight: 700; border: none; border-radius: 8px; padding: 10px 24px; transition: all 0.3s ease; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 255, 170, 0.4); }
    hr { border-color: #2b313f; margin: 20px 0; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES MATEMÁTICAS E EXTRAÇÃO DE DADOS
# ============================================================================

@st.cache_data(ttl=300)
def calcGammaEx(S, K, vol, T, r, q, optType, OI):
    K, vol, T, OI = map(lambda x: np.asarray(x, dtype=float), [K, vol, T, OI])
    result = np.zeros_like(K, dtype=float)
    valid = (T > 0) & (vol > 0) & (K > 0) & np.isfinite(T) & np.isfinite(vol) & np.isfinite(K)
    if not np.any(valid): 
        return result
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

@st.cache_data(ttl=60)
def fetch_json(symbol="SPX"):
    headers = {"User-Agent": "Mozilla/5.0"}
    for s in [symbol, f"_{symbol}"]:
        try:
            r = requests.get(f"https://cdn.cboe.com/api/global/delayed_quotes/options/{s}.json", 
                           headers=headers, timeout=10)
            r.raise_for_status()
            return r.json()
        except: 
            continue
    raise Exception("Falha na conexão com a CBOE.")

def fetch_vix_data():
    try:
        vix = yf.Ticker("^VIX")
        vix9d = yf.Ticker("^VIX9D")
        vix_hist = vix.history(period="1mo")["Close"]
        vix_spot = float(vix.history(period="1d")["Close"].iloc[-1])
        vix9d_spot = float(vix9d.history(period="1d")["Close"].iloc[-1])
        return {
            'vix': vix_spot,
            'vix9d': vix9d_spot,
            'vix_avg': float(vix_hist.mean()),
            'vix_high': float(vix_hist.max()),
            'vix_low': float(vix_hist.min())
        }
    except:
        return {'vix': 20.0, 'vix9d': 20.0, 'vix_avg': 20.0, 'vix_high': 25.0, 'vix_low': 15.0}

def generate_trade_signal(spot, basis, levels, regime, vix_data):
    signal = {
        "direction": None,
        "confidence": 0,
        "entry_zone": None,
        "targets": [],
        "invalidation": None,
        "reasoning": [],
        "risk_reward": 0
    }
    
    es_spot = spot + basis
    es_zg = (levels.get('z_gama', spot) + basis) if not pd.isna(levels.get('z_gama')) else es_spot
    es_pw = (levels.get('p_wall_0dte', levels.get('p_wall', spot)) + basis)
    es_cw = (levels.get('c_wall_0dte', levels.get('c_wall', spot)) + basis)
    
    if regime == "NEGATIVO" and es_spot < es_zg:
        signal['direction'] = "SHORT 📉"
        signal['reasoning'].append("✅ Regime GEX Negativo: Dealers amplificam vendas")
        signal['confidence'] += 1
    elif regime == "POSITIVO" and es_spot > es_zg:
        signal['direction'] = "LONG 📈"
        signal['reasoning'].append("✅ Regime GEX Positivo: Mean-reversion favorecido")
        signal['confidence'] += 1
    else:
        signal['reasoning'].append("⚠️ Preço próximo ao Zero Gamma: Aguardar definição")
    
    alvo_pontos = es_spot * 0.005
    
    if signal['direction'] == "SHORT 📉":
        dist_to_put = abs(es_spot - es_pw)
        if dist_to_put > alvo_pontos:
            signal['targets'].append(es_pw)
            signal['confidence'] += 1
            signal['reasoning'].append(f"✅ Alvo técnico limpo em {es_pw:.2f} ({dist_to_put:.0f} pts de espaço)")
        else:
            signal['reasoning'].append(f"❌ Suporte muito próximo ({dist_to_put:.0f} pts). Risco de repique na Put Wall.")
        signal['invalidation'] = es_zg + 10 
        signal['entry_zone'] = f"{es_spot:.2f} - {es_spot-5:.2f}"
        
    elif signal['direction'] == "LONG 📈":
        dist_to_call = abs(es_spot - es_cw)
        if dist_to_call > alvo_pontos:
            signal['targets'].append(es_cw)
            signal['confidence'] += 1
            signal['reasoning'].append(f"✅ Alvo técnico limpo em {es_cw:.2f} ({dist_to_call:.0f} pts de espaço)")
        else:
            signal['reasoning'].append(f"❌ Resistência muito próxima ({dist_to_call:.0f} pts). Risco de rejeição na Call Wall.")
        signal['invalidation'] = es_zg - 10
        signal['entry_zone'] = f"{es_spot:.2f} - {es_spot+5:.2f}"
    
    if vix_data.get('vix9d', 0) > vix_data.get('vix', 0):
        if signal['direction'] == "SHORT 📉":
            signal['confidence'] += 1
            signal['reasoning'].append("🔥 VIX Backwardation: Pânico institucional confirma força da venda.")
        else:
            signal['reasoning'].append("⚠️ VIX Backwardation: Perigoso para operações compradas (Long).")
    else:
        if signal['direction'] == "LONG 📈": 
            signal['confidence'] += 1
        signal['reasoning'].append("✅ Contango Normal: Ambiente estável para predição técnica.")
    
    if signal['invalidation'] and signal['targets']:
        risk = abs(es_spot - signal['invalidation'])
        reward = abs(signal['targets'][0] - es_spot)
        signal['risk_reward'] = reward / risk if risk > 0 else 0
    
    return signal

def generate_trade_report(signal, levels, spot, basis, timestamp):
    direction = signal['direction'] or 'NEUTRO'
    confidence = '🟢 Alta' if signal['confidence']>=3 else '🟡 Média' if signal['confidence']==2 else '🔴 Baixa'
    es_spot = spot + basis
    
    stop_loss_str = f"{signal['invalidation']:.2f}" if signal['invalidation'] else 'N/A'
    alvo_str = f"{signal['targets'][0]:.2f}" if signal['targets'] else 'N/A'
    
    report = f"""# ⚡ GEX ULTRA ELITE - Trade Report
*Gerado em: {timestamp.strftime('%d/%m/%Y %H:%M ET')} | ES (Futuro): {es_spot:.2f} (Basis: {basis:+.2f})*

## 🎯 Sinal de Execução (MetaTrader 5)
| Campo | Valor |
|-------|-------|
| Direção | {direction} |
| Confiança | {confidence} |
| Zona de Entrada | {signal['entry_zone'] or 'Aguardar confirmação'} |
| Score | {signal['confidence']}/3 |

## 📍 Estrutura de Hedging (Ajustada p/ ES)
- 🔴 Put Wall: {(levels.get('p_wall', 0) + basis):.2f}
- 🔄 Zero Gamma: {(levels.get('z_gama', 0) + basis):.2f}  
- 🟢 Call Wall: {(levels.get('c_wall', 0) + basis):.2f}
- 📊 Vol Trigger: {(levels.get('vt', 0) + basis):.2f}

## 🧠 Validação Tática
{chr(10).join(f'- {r}' for r in signal['reasoning'])}

## ⚠️ Gestão de Risco
- Stop Loss Institucional: {stop_loss_str}
- Alvo Primário (Take Profit): {alvo_str}
- Payoff (R:R Estimado): {signal['risk_reward']:.2f}

## 📊 Estrutura de Volatilidade
- VIX Spot: {levels.get('vix', 0):.2f}
- VIX9D: {levels.get('vix9d', 0):.2f}
- Média 20d: {levels.get('vix_avg', 0):.2f}

---
*⚠️ IMPORTANTE: Este relatório usa preços do FUTURO (ES=F) para execução no MetaTrader 5.*
*© 2026 GEX ULTRA ELITE Terminal • Uso profissional*
"""
    return report

def generate_pine_script(levels, basis, timestamp):
    """Gera código Pine Script v5 para plotagem automática no TradingView."""
    lines = [f"//@version=5\nindicator(\"GEX ULTRA ELITE - {timestamp.strftime('%d/%m/%Y')}\", overlay=true)\n"]
    
    def add_line(val, title, color, style, width):
        if not pd.isna(val) and val > 0:
            es_price = val + basis
            lines.append(f'hline({es_price:.2f}, title="{title}", color={color}, linestyle={style}, linewidth={width})')

    lines.append("// 🎯 MACRO ESTRUTURAL")
    add_line(levels.get('c_wall'), "Call Wall Principal", "#FF4444", "hline.style_solid", 2)
    add_line(levels.get('z_gama'), "Zero Gamma (Flip)", "#00FFAA", "hline.style_solid", 3)
    add_line(levels.get('p_wall'), "Put Wall Principal", "#00CC88", "hline.style_solid", 2)
    
    lines.append("\n// ⏱️ MICROESTRUTURA 0DTE")
    add_line(levels.get('c_wall_0dte'), "Call Wall 0DTE", "#FF8888", "hline.style_dashed", 2)
    add_line(levels.get('p_wall_0dte'), "Put Wall 0DTE", "#88FF88", "hline.style_dashed", 2)
    
    lines.append("\n// 📊 NÍVEIS DE FLUXO")
    add_line(levels.get('vt'), "Vol Trigger", "#FFCC00", "hline.style_dotted", 1)
    add_line(levels.get('l1'), "Nível L1", "#4ECDC4", "hline.style_dashed", 1)
    add_line(levels.get('c1'), "Nível C1", "#95E1D3", "hline.style_dashed", 1)
    add_line(levels.get('c4'), "Nível C4", "#F38181", "hline.style_dashed", 1)
    
    return "\n".join(lines)

# ============================================================================
# COMPONENTES VISUAIS
# ============================================================================

def render_header():
    st.markdown("""
    <div style='text-align:center; padding: 20px 0; margin-bottom: 20px;'>
        <h1 class='gradient-title'>⚡ GEX ULTRA ELITE TERMINAL</h1>
        <p class='subtitle'>Terminal Profissional de Gamma Exposure • SPX/ES • Fluxo 0DTE Integrado</p>
        <div style='display:flex; justify-content:center; gap:12px; margin-top:15px; flex-wrap:wrap;'>
            <span class='badge badge-info'>✅ CBOE API</span>
            <span class='badge badge-warning'>⚡ &lt;500ms</span>
            <span class='badge badge-positive'>🔐 Execução Algorítmica</span>
            <span class='badge badge-info'>📊 Ajuste Basis Ativo</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_setup_score(score, max_score=3, regime="NEGATIVO"):
    pct = (score / max_score) * 100
    color = "#00FFAA" if score >= 2 else "#FFCC00" if score == 1 else "#FF4444"
    status = "✅ PISTA LIVRE" if score >= 2 else "⚠️ FILTRO ATIVO" if score == 1 else "❌ TRADE BLOQUEADO"
    
    st.markdown(f"""
    <div class="metric-card animate-slide-in">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span style="color:#8A94A6; font-size:13px; font-weight:700; text-transform:uppercase;">🎯 APROVAÇÃO TÁTICA</span>
            <span class="badge badge-{'positive' if score>=2 else 'warning' if score==1 else 'negative'}">{regime}</span>
        </div>
        <div style="display:flex; align-items:baseline; gap:10px;">
            <div style="font-size:42px; font-weight:900; color:{color}; line-height:1;">{score}/{max_score}</div>
            <div style="color:{color}; font-weight:700; font-size:16px;">{status}</div>
        </div>
        <div class="progress-container">
            <div class="progress-bar" style="width:{pct}%; background: linear-gradient(90deg, {color}, {color}88);"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_status_box(regime_gama, regime_vix, term_structure, timer_0dte, vix_data):
    cor_gama = "#00FFAA" if regime_gama == "POSITIVO" else "#FF4444"
    
    st.markdown(f"""
    <div class="header-box">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:15px;">
            <div>
                <h3 style='margin:0; color:white; font-size:24px;'>REGIME GEX: <span style='color:{cor_gama}'>{regime_gama}</span></h3>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <span class="badge badge-info">VIX {vix_data['vix']:.2f}</span>
                <span class="badge badge-warning">VIX9D {vix_data['vix9d']:.2f}</span>
            </div>
        </div>
        <hr style='border-color:#2b313f; margin:15px 0;'>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap:12px;">
            <div style="color:#8A94A6; font-size:14px;">
                <span style="color:#FFF; font-weight:700;">📈 ESTRATÉGIA:</span> {regime_vix}
            </div>
            <div style="color:#8A94A6; font-size:14px;">
                <span style="color:#FFF; font-weight:700;">📊 VIX CURVE:</span> {term_structure}
            </div>
            <div style="color:#8A94A6; font-size:14px;">
                <span style="color:#E2B714; font-weight:700;">⏱️ 0DTE:</span> {timer_0dte}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_levels_grid(levels, basis=0):
    def fmt(val, is_zg=False):
        if pd.isna(val) or val is None: return "0.00"
        adj = val + basis
        return f"{round(adj * 4) / 4:.2f}" if is_zg else f"{round(adj / 5) * 5:.0f}"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="label">📊 MICROESTRUTURA (0DTE)</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:10px;"></div>', unsafe_allow_html=True)
        st.write('<div class="label">CALL WALL 0DTE (Resistência)</div>', unsafe_allow_html=True)
        st.code(fmt(levels.get('c_wall_0dte')))
        st.write('<div class="label">PUT WALL 0DTE (Suporte)</div>', unsafe_allow_html=True)
        st.code(fmt(levels.get('p_wall_0dte')))
    
    with col2:
        st.markdown('<div class="label">🎯 NÍVEIS ESTRUTURAIS MACRO</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:10px;"></div>', unsafe_allow_html=True)
        st.write('<div class="label">CALL WALL PRINCIPAL</div>', unsafe_allow_html=True)
        st.code(fmt(levels.get('c_wall')))
        st.write('<div class="label">ZERO GAMMA (FLIP)</div>', unsafe_allow_html=True)
        st.code(fmt(levels.get('z_gama'), True))
        st.write('<div class="label">PUT WALL PRINCIPAL</div>', unsafe_allow_html=True)
        st.code(fmt(levels.get('p_wall')))
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    with col3:
        st.write('<div class="label">VOLATILITY TRIGGER</div>', unsafe_allow_html=True)
        st.code(fmt(levels.get('vt')))
    
    with col4:
        st.write('<div class="label">NÍVEL L1 (ALVO ALTO)</div>', unsafe_allow_html=True)
        st.code(fmt(levels.get('l1')))
        st.write('<div class="label">NÍVEL C1 (ALVO BAIXO)</div>', unsafe_allow_html=True)
        st.code(fmt(levels.get('c1')))
        st.write('<div class="label">NÍVEL C4 (EXAUSTÃO)</div>', unsafe_allow_html=True)
        st.code(fmt(levels.get('c4')))

def render_gamma_profile(df_chart, spot_price, zero_gamma, call_wall, put_wall):
    if df_chart.empty: 
        st.warning("Dados insuficientes para gerar o Gamma Profile")
        return
    
    ref_data = pd.DataFrame({
        'level': [spot_price, zero_gamma, call_wall, put_wall],
        'label': ['💰 ES Futuro', '🔄 Zero Gamma', '🔴 Call Wall', '🟢 Put Wall'],
        'color': ['#FFFFFF', '#00FFAA', '#FF6B6B', '#4ECDC4']
    })
    
    rules = alt.Chart(ref_data).mark_rule(strokeDash=[4, 4], strokeWidth=2).encode(
        y='level:Q', color=alt.Color('color:N', scale=None), tooltip=['label:N', alt.Tooltip('level:Q', format='.2f')]
    )
    
    labels = alt.Chart(ref_data[ref_data['label'] != '💰 ES Futuro']).mark_text(
        align='left', dx=8, fontSize=11, fontWeight='bold', color='#8A94A6'
    ).encode(y='level:Q', text='label:N')
    
    bars = alt.Chart(df_chart).mark_bar(opacity=0.9, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        y=alt.Y('StrikePrice:O', sort='descending', title='Strike Price (ES)', 
                axis=alt.Axis(labelColor='#8A94A6', titleColor='#8A94A6', gridColor='#2b313f', labelFontSize=11)),
        x=alt.X('TotalGamma:Q', title='Net GEX ($ Bilhões)', 
                axis=alt.Axis(labelColor='#8A94A6', titleColor='#8A94A6', gridColor='#2b313f', labelFontSize=11)),
        color=alt.Color('TotalGamma:Q', 
                        scale=alt.Scale(domain=[-10, 0, 10], range=['#FF4444', '#333333', '#00FFAA']), legend=None),
        tooltip=[alt.Tooltip('StrikePrice:Q', title='Strike', format='.2f'), alt.Tooltip('TotalGamma:Q', title='Net GEX', format='.3f')]
    )
    
    chart = (bars + rules + labels).properties(
        height=500, title=alt.TitleParams("📊 GAMMA PROFILE: Concentração de Liquidez (Ajustado p/ ES)", 
                                         fontSize=16, color='#FFFFFF', anchor='middle', fontWeight='bold')
    ).configure_view(strokeWidth=0).configure_axis(grid=True, gridColor='#2b313f').configure_title(fontSize=16, color='#FFFFFF')
    
    st.altair_chart(chart, use_container_width=True)

# ============================================================================
# MAIN APP FLOW
# ============================================================================
render_header()

with st.sidebar:
    st.markdown("### ⚙️ CONFIGURAÇÕES DA MESA")
    st.markdown("---")
    
    perfil = st.selectbox("🎯 Gestão de Risco", ["Day Trader (0.5% Alvo / 0.25% Stop)", "Scalper (Rápido)", "Swing"])
    
    st.markdown("#### 🎚️ Parâmetros Institucionais")
    st.slider("Tolerância Distância Wall (pts)", 10, 50, 25, 5)
    
    st.markdown("---")
    st.markdown("### 📊 INFORMAÇÕES")
    st.markdown("""
    <div style="color:#8A94A6; font-size:12px; line-height:1.6;">
    <strong>📡 Fonte:</strong> CBOE API<br>
    <strong>⚡ Latência:</strong> &lt;500ms<br>
    <strong>🔄 Atualização:</strong> Auto (60s)<br>
    <strong>📈 Ativo:</strong> SPX/ES<br>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("🔐 GEX ULTRA ELITE v4.0\n\n*Validação Quantitativa Direta*")

if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL", use_container_width=True, type="primary"):
    with st.spinner("⚡ Calculando derivativos, sincronizando Basis ES e avaliando setup..."):
        try:
            # ==========================================================================
            # COLETA DE DADOS
            # ==========================================================================
            data = fetch_json("SPX")
            spotPrice = data["data"].get("current_price", data["data"].get("last"))
            
            vix_data = fetch_vix_data()
            vix_spot, vix9d_spot, vix_avg = vix_data['vix'], vix_data['vix9d'], vix_data['vix_avg']
            
            if vix9d_spot > vix_spot:
                term_structure = f"🔴 INVERTIDA (VIX9D {vix9d_spot:.2f} > VIX {vix_spot:.2f}) - ALERTA DE ESTRESSE"
            else:
                term_structure = f"🟢 NORMAL (VIX9D {vix9d_spot:.2f} < VIX {vix_spot:.2f}) - CONTANGO"

            if vix_spot < 16: 
                regime_vix = "REVERSÃO À MÉDIA"
            elif vix_spot <= 20: 
                regime_vix = "DIRECIONAL"
            else: 
                regime_vix = "ROMPIMENTO / PERIGO"

            now_et = pd.Timestamp.now('US/Eastern')
            close_et = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
            if now_et > close_et:
                timer_0dte = "MERCADO FECHADO"
            else:
                time_left = close_et - now_et
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                timer_0dte = f"{hours:02d}h {minutes:02d}m restantes"

            # ==========================================================================
            # PROCESSAMENTO CBOE
            # ==========================================================================
            df_raw = pd.DataFrame(data["data"]["options"])
            parsed = df_raw["option"].apply(lambda x: re.search(r'^(.*?)(\d{6})([CP])(\d{8})$', x))
            df_raw["ExpirationDate"] = pd.to_datetime(parsed.apply(lambda m: m.group(2) if m else None), format="%y%m%d") + timedelta(hours=16)
            df_raw["OptionType"] = parsed.apply(lambda m: m.group(3) if m else None)
            df_raw["StrikePrice"] = parsed.apply(lambda m: int(m.group(4))/1000.0 if m else np.nan)
            
            for col in ["iv", "gamma", "open_interest"]: 
                df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce").fillna(0)
            
            calls = df_raw[df_raw["OptionType"] == "C"].rename(columns={"iv": "CallIV", "gamma": "CallGamma", "open_interest": "CallOpenInt"})
            puts = df_raw[df_raw["OptionType"] == "P"].rename(columns={"iv": "PutIV", "gamma": "PutGamma", "open_interest": "PutOpenInt"})
            
            df = pd.merge(calls[["ExpirationDate", "StrikePrice", "CallIV", "CallGamma", "CallOpenInt"]], 
                          puts[["ExpirationDate", "StrikePrice", "PutIV", "PutGamma", "PutOpenInt"]], 
                          on=["ExpirationDate", "StrikePrice"], how="outer").fillna(0)
            
            df['TotalGamma'] = ((df['CallGamma'] * df['CallOpenInt'] * 100 * spotPrice**2 * 0.01) - 
                               (df['PutGamma'] * df['PutOpenInt'] * 100 * spotPrice**2 * 0.01)) / 1e9
            
            # Cálculos Macro
            dfAgg = df.groupby(['StrikePrice']).sum(numeric_only=True)
            c_wall = dfAgg['TotalGamma'].idxmax()
            p_wall = dfAgg['TotalGamma'].idxmin()

            # Cálculo Micro 0DTE
            min_exp = df['ExpirationDate'].min()
            dfAgg_0dte = df[df['ExpirationDate'] == min_exp].groupby(['StrikePrice']).sum(numeric_only=True)
            c_wall_0dte = dfAgg_0dte['TotalGamma'].idxmax() if not dfAgg_0dte.empty else np.nan
            p_wall_0dte = dfAgg_0dte['TotalGamma'].idxmin() if not dfAgg_0dte.empty else np.nan

            # Basis ES
            try: 
                es_spot = float(yf.Ticker("ES=F").history(period="1d")["Close"].iloc[-1])
            except: 
                es_spot = spotPrice
            basis = es_spot - spotPrice
            
            if abs(basis) > 10:
                st.markdown(f"""
                <div class='semaforo-alerta'>
                    ⚠️ BASIS ELEVADO: ES-SPX = {basis:+.2f} pts
                    <br><small>Verifique rollover de contrato ou evento de mercado.</small>
                </div>
                """, unsafe_allow_html=True)

            # Zero Gamma e Níveis de Fluxo
            df["daysTillExp"] = np.where(df["ExpirationDate"].dt.date == datetime.now().date(), 1/262, 
                                         np.busday_count(datetime.now().date(), df["ExpirationDate"].dt.date.values.astype('datetime64[D]')) / 262)
            df_calc = df[df['daysTillExp'] > 0]
            levels_range = np.arange(np.floor(spotPrice * 0.8 / 5) * 5, np.ceil(spotPrice * 1.2 / 5) * 5 + 5, 5.0)
            
            totalGamma = []
            for level in levels_range:
                cg = calcGammaEx(level, df_calc['StrikePrice'], df_calc['CallIV'].replace(0,0.15), df_calc['daysTillExp'], 0, 0, "call", df_calc['CallOpenInt'])
                pg = calcGammaEx(level, df_calc['StrikePrice'], df_calc['PutIV'].replace(0,0.15), df_calc['daysTillExp'], 0, 0, "put", df_calc['PutOpenInt'])
                totalGamma.append((cg - pg).sum() / 1e9)
            
            zeroCrossIdx = np.where(np.diff(np.sign(totalGamma)) != 0)[0]
            if len(zeroCrossIdx) > 0:
                z_gama = float(levels_range[zeroCrossIdx[0]] - totalGamma[zeroCrossIdx[0]] * (levels_range[zeroCrossIdx[0] + 1] - levels_range[zeroCrossIdx[0]]) / (totalGamma[zeroCrossIdx[0] + 1] - totalGamma[zeroCrossIdx[0]]))
            else:
                z_gama = np.nan
            
            df_filt = dfAgg[(dfAgg.index >= spotPrice * 0.8) & (dfAgg.index <= spotPrice * 1.2)]
            top_calls = df_filt['TotalGamma'].nlargest(3).index.tolist()
            l1 = top_calls[1] if (len(top_calls) > 1 and top_calls[0] == c_wall) else (top_calls[0] if len(top_calls)>0 else np.nan)
            c1 = df_filt[df_filt.index > p_wall]['TotalGamma'].idxmin() if not df_filt[df_filt.index > p_wall].empty else np.nan
            c4 = df_filt[df_filt.index < p_wall]['TotalGamma'].idxmin() if not df_filt[df_filt.index < p_wall].empty else np.nan
            vt = df_filt[(df_filt.index > p_wall) & (df_filt.index < z_gama)]['TotalGamma'].idxmin() if not df_filt[(df_filt.index > p_wall) & (df_filt.index < z_gama)].empty else np.nan

            levels_dict = {
                'c_wall': c_wall, 'p_wall': p_wall, 'c_wall_0dte': c_wall_0dte, 'p_wall_0dte': p_wall_0dte, 
                'z_gama': z_gama, 'l1': l1, 'c1': c1, 'c4': c4, 'vt': vt, 'vix': vix_spot, 'vix9d': vix9d_spot, 'vix_avg': vix_avg
            }
            
            regime_gama = "POSITIVO" if spotPrice > z_gama else "NEGATIVO"
            
            # ==========================================================================
            # RENDERIZAÇÃO DA INTERFACE
            # ==========================================================================
            render_status_box(regime_gama, regime_vix, term_structure, timer_0dte, vix_data)
            
            col_score, col_signal = st.columns([1, 2])
            
            with col_score:
                signal = generate_trade_signal(spotPrice, basis, levels_dict, regime_gama, vix_data)
                render_setup_score(signal['confidence'], 3, regime_gama)
                
                st.markdown(f"""
                <div class='metric-card'>
                    <div style="color:#8A94A6; font-size:13px; margin-bottom:8px;">
                        <div style="margin:5px 0;">💰 ES Futuro: <strong style="color:#FFF">{es_spot:.2f}</strong></div>
                        <div style="margin:5px 0;">📊 SPX Basis: <strong style="color:#00FFAA">{basis:+.2f}</strong></div>
                        <div style="margin:5px 0;">📈 SPX Cash: <strong style="color:#8A94A6">{spotPrice:.2f}</strong></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_signal:
                st.markdown('<div class="label">🎯 ORDEM DE EXECUÇÃO (MT5)</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                
                if signal['direction']:
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                        <div style="font-size:32px; font-weight:900; color:{'#00FFAA' if 'LONG' in signal['direction'] else '#FF4444'};">
                            {signal['direction']}
                        </div>
                        <div style="text-align:right;">
                            <div style="color:#8A94A6; font-size:12px;">Ponto de Entrada Recomendado</div>
                            <div style="font-size:22px; font-weight:800; color:#00D4FF;">{signal['entry_zone']}</div>
                        </div>
                    </div>
                    <hr style="border-color:#2b313f; margin:15px 0;">
                    <div style="color:#8A94A6; font-size:14px; line-height:1.8;">
                        {chr(10).join(f'• {r}' for r in signal['reasoning'])}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="color:#8A94A6; text-align:center; padding:20px;">⏳ Aguardando afastamento da zona de compressão...</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                if signal['direction']:
                    report_md = generate_trade_report(signal, levels_dict, spotPrice, basis, datetime.now())
                    st.download_button(
                        label="📄 BAIXAR RELATÓRIO",
                        data=report_md,
                        file_name=f"GEX_Execucao_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                st.markdown("<hr style='border-color:#2b313f; margin:15px 0;'>", unsafe_allow_html=True)
                st.markdown('<div class="label">🖥️ EXPORTAÇÃO PARA TRADINGVIEW</div>', unsafe_allow_html=True)
                pine_code = generate_pine_script(levels_dict, basis, datetime.now())
                
                with st.expander("👉 EXIBIR CÓDIGO PINE SCRIPT (COPIAR E COLAR)"):
                    st.code(pine_code, language="pine")
                    st.caption("No TradingView: Abra o Pine Editor (rodapé) > Apague o conteúdo > Cole este código > Clique em 'Adicionar ao Gráfico'.")
            
            # Grid de Níveis
            st.markdown("<br>", unsafe_allow_html=True)
            render_levels_grid(levels_dict, basis)
            
            # Gamma Profile Chart
            st.markdown("<br>", unsafe_allow_html=True)
            df_chart = dfAgg[(dfAgg.index >= spotPrice * 0.95) & (dfAgg.index <= spotPrice * 1.05)].copy()
            df_chart = df_chart.reset_index()
            df_chart['StrikePrice'] = df_chart['StrikePrice'] + basis  # Ajuste para ES
            render_gamma_profile(df_chart, es_spot, z_gama + basis, c_wall + basis, p_wall + basis)
            
            # Footer
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("""
            <div style='text-align:center; padding:20px; color:#444; font-size:11px; border-top:1px solid #2b313f;'>
                <strong>GEX ULTRA ELITE TERMINAL v4.0</strong><br>
                Validação Quantitativa para MT5 • Dados: CBOE API • Latência &lt;500ms<br>
                © 2026 Todos os direitos reservados • Uso exclusivo para traders profissionais
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Erro de processamento: {str(e)}")
            st.info("💡 Verifique sua conexão com a internet e tente novamente.")

else:
    st.markdown("""
    <div style='text-align:center; padding:60px 20px;'>
        <div style='font-size:80px; margin-bottom:20px;'>⚡</div>
        <h2 style='color:#FFF; margin-bottom:15px;'>Pronto para Execução Institucional</h2>
        <p style='color:#8A94A6; font-size:16px; max-width:600px; margin:0 auto 30px auto; line-height:1.6;'>
            Clique no botão acima para puxar a matriz de opções CBOE, ajustar o Basis do SP500 para o contrato futuro (ES) e rodar a validação matemática do alvo direcional.
        </p>
    </div>
    """, unsafe_allow_html=True)
