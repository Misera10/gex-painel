import streamlit as st
import requests
import pandas as pd

# Interface Premium
st.set_page_config(page_title="GEX ULTRA ELITE PRO", layout="wide")

st.markdown("""
    <style>
    .metric-card { background: #1a1f2c; border: 1px solid #00ffaa; border-radius: 10px; padding: 20px; text-align: center; }
    .stButton>button { width: 100%; background-color: #00ffaa !important; color: black !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ GEX ULTRA ELITE PRO")

# Sidebar
with st.sidebar:
    st.header("🔗 Configurações")
    ponte_url = st.text_input("Link do Colab (Ngrok):", placeholder="https://xxxx.ngrok-free.app/spx")
    mt5_price = st.number_input("💻 Preço ES (MT5):", value=5100.0, step=0.25)
    st.divider()
    st.info("Pressione 'Play' no Colab antes de atualizar aqui.")

# Ação
if st.button("🚀 ATUALIZAR MATRIZ INSTITUCIONAL"):
    if not ponte_url:
        st.warning("⚠️ Insira o link do Colab!")
    else:
        with st.spinner("Puxando dados via Google Bridge..."):
            try:
                r = requests.get(ponte_url, timeout=30)
                if r.status_code == 200:
                    st.session_state.gex_data = r.json()
                    st.success("✅ Dados atualizados!")
                else:
                    st.error("❌ O Colab não respondeu. Verifique se ele está rodando.")
            except:
                st.error("❌ Erro de conexão. Verifique o link.")

# Dashboard de Operação
if 'gex_data' in st.session_state:
    data = st.session_state.gex_data
    spot = float(data["data"]["last"])
    basis = mt5_price - spot
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("SPX SPOT", f"${spot:,.2f}")
    with c2: st.metric("BASIS", f"{basis:.2f}")
    with c3: st.metric("SYNC", "LIVE")

    # Tabela de Níveis (Lógica de Exemplo - Substitua pelos seus cálculos de Gamma)
    st.subheader("📋 Níveis Operacionais MT5")
    niveis = {
        "Nível": ["Call Wall (CW)", "Zero Gamma (ZG)", "Vol Trigger (VT)", "Put Wall (PW)"],
        "Preço SPX": [spot+50, spot-10, spot-30, spot-60], # Insira sua fórmula aqui
    }
    df = pd.DataFrame(niveis)
    df["Preço MT5"] = df["Preço SPX"] + basis
    
    st.table(df.style.format({"Preço SPX": "{:.2f}", "Preço MT5": "{:.2f}"}))
    
    # Alerta Tático
    if mt5_price < (spot - 10 + basis):
        st.error(f"⚠️ ZONA DE RISCO: Preço abaixo do Zero Gamma ({spot-10+basis:.2f}). Cuidado com Shorts!")
    else:
        st.success(f"✅ ZONA DE ALTA: Preço acima do Zero Gamma. Viés comprador.")
