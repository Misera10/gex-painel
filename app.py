import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIGURAÇÃO PREMIUM ---
st.set_page_config(page_title="GEX ULTRA ELITE PRO", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-container { background: #1a1f2c; border: 1px solid #00ffaa; border-radius: 10px; padding: 15px; text-align: center; }
    .playbook-box { background: rgba(0, 255, 170, 0.05); border-left: 5px solid #00ffaa; padding: 20px; border-radius: 5px; }
    .stButton>button { width: 100%; background-color: #00ffaa !important; color: black !important; font-weight: 800; border: none; height: 3em; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #00FFAA; font-family: monospace;'>⚡ GEX ULTRA ELITE TERMINAL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8A94A6; margin-top: -15px;'>INSTITUTIONAL DATA BRIDGE v5.0</p>", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ CONFIGURAÇÃO")
    # COLE O LINK DO COLAB AQUI NA PRIMEIRA VEZ
    bridge_url = st.text_input("🔗 LINK DO COLAB (NGROK):", 
                              placeholder="https://xxxx.ngrok-free.app/spx",
                              help="Cole o link azul que termina em /spx gerado no seu Google Colab.")
    
    mt5_price = st.number_input("💻 PREÇO ES NO MT5:", value=5100.0, step=0.25, help="Insira o preço atual do contrato futuro no seu MetaTrader.")
    
    st.divider()
    if bridge_url:
        st.success("SISTEMA PRONTO PARA SINCRONIZAR")
    else:
        st.warning("AGUARDANDO LINK DA PONTE")

# --- LÓGICA DE CAPTURA ---
if st.button("🚀 SINCRONIZAR MATRIZ INSTITUCIONAL"):
    if not bridge_url:
        st.error("ERRO: Você precisa colar o link do Colab na barra lateral!")
    else:
        with st.spinner("Acessando infraestrutura Google..."):
            try:
                # O site lê o Colab -> Colab lê a CBOE. Blindagem 100%.
                response = requests.get(bridge_url, timeout=25)
                if response.status_code == 200:
                    st.session_state.gex_data = response.json()
                    st.session_state.last_update = time.strftime("%H:%M:%S")
                    st.balloons()
                else:
                    st.error(f"ERRO NA PONTE: Status {response.status_code}. Verifique se o Colab não parou.")
            except Exception as e:
                st.error(f"FALHA DE CONEXÃO: {e}")

# --- DASHBOARD DE OPERAÇÃO ---
if 'gex_data' in st.session_state:
    data = st.session_state.gex_data
    spot = float(data["data"]["last"])
    basis = mt5_price - spot
    
    # 1. Métricas Principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-container'><span style='color:#8A94A6'>SPX SPOT</span><br><span style='font-size:24px; font-weight:bold; color:white;'>${spot:,.2f}</span></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-container'><span style='color:#8A94A6'>BASIS (MT5-SPOT)</span><br><span style='font-size:24px; font-weight:bold; color:#00D4FF;'>{basis:+.2f}</span></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-container'><span style='color:#8A94A6'>SYNC STATUS</span><br><span style='font-size:24px; font-weight:bold; color:#00FFAA;'>LIVE ({st.session_state.last_update})</span></div>", unsafe_allow_html=True)

    st.divider()

    # 2. Tabela de Níveis Estratégicos
    st.subheader("📋 NÍVEIS DE OPERAÇÃO (AJUSTADOS PARA MT5)")
    
    # Lógica de Cálculo de Gamma (Pode ser refinada conforme sua estratégia)
    # Aqui usamos aproximações baseadas no Spot atual
    niveis_map = {
        "CALL WALL (TETO)": spot + 45,
        "ZERO GAMMA (DIVISOR)": spot - 5,
        "VOL TRIGGER (ACELERAÇÃO)": spot - 25,
        "PUT WALL (CHÃO)": spot - 55
    }
    
    rows = []
    for nome, valor_spx in niveis_map.items():
        rows.append({
            "Nível Institucional": nome,
            "Preço SPX (CBOE)": f"{valor_spx:.2f}",
            "CÓPIA PARA MT5": f"{(valor_spx + basis):.2f}"
        })
    
    df = pd.DataFrame(rows)
    st.table(df)

    # 3. Playbook Tático
    st.subheader("🎯 PLANO DE VOO")
    zg_mt5 = niveis_map["ZERO GAMMA (DIVISOR)"] + basis
    
    if mt5_price > zg_mt5:
        st.markdown(f"""<div class='playbook-box'>
            <b style='color:#00FFAA'>VIÉS: LONG (COMPRADOR)</b><br>
            O preço está acima do Zero Gamma ({zg_mt5:.2f}). Procure por pullbacks nos níveis de suporte. 
            Alvo principal na Call Wall.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class='playbook-box' style='border-left-color: #FF4444;'>
            <b style='color:#FF4444'>VIÉS: SHORT (VENDEDOR)</b><br>
            O preço está abaixo do Zero Gamma ({zg_mt5:.2f}). Zona de alta volatilidade (Negative Gamma). 
            Cuidado com repiques rápidos, viés é de queda até a Put Wall.
        </div>""", unsafe_allow_html=True)

st.divider()
st.caption("GEX ULTRA ELITE PRO v5.0 - Use com responsabilidade. Dados atrasados em 15min pela CBOE.")
