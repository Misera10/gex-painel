# Trecho do botão no app.py v5.4.1
if st.button("🚀 PROCESSAR MATRIZ INSTITUCIONAL"):
    # Limpa o link de espaços ou caracteres invisíveis
    url_limpa = bridge_url.strip() 
    
    if not url_limpa.startswith("http"):
        st.error("❌ Erro: O link deve começar com https://")
    else:
        with st.spinner("Conectando..."):
            try:
                headers = {"ngrok-skip-browser-warning": "true"}
                r = requests.get(url_limpa, headers=headers, timeout=30)
                
                if r.status_code == 200:
                    st.session_state.spx_data = r.json()
                    st.success("✅ CONECTADO!")
                else:
                    st.error(f"❌ Erro {r.status_code}: Verifique se o link termina com /spx")
            except Exception as e:
                st.error(f"❌ Falha: {e}")
