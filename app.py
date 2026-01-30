import streamlit as st
import os
import httpx
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from backend.utils import get_current_date_str

API_URL = os.getenv("API_URL", "http://localhost:8001")

# Configuração da Página
st.set_page_config(
    page_title="Agente de Segurança Pública DF",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AUTHENTICATION ---
try:
    with open('auth_config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("Arquivo de configuração de autenticação (auth_config.yaml) não encontrado.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao ler config: {e}")
    st.stop()

try:
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
except Exception as e:
    st.error(f"Erro na inicialização do autenticador: {e}")
    st.stop()

# Render Login Widget
try:
    authenticator.login('main')
except Exception as e:
    st.error(f"Erro no login widget: {e}")

if st.session_state.get('authentication_status') is False:
    st.error('Username/password is incorrect')
elif st.session_state.get('authentication_status') is None:
    st.warning('Please enter your username and password')

if st.session_state.get('authentication_status'):
    # --- APP MAIN LOGIC (PROTECTED) ---
    st.sidebar.write(f"Bem-vindo, **{st.session_state.get('name')}**")
    authenticator.logout('Logout', 'sidebar')

    # Estilização Customizada
    st.markdown("""
        <style>
        .main {
            background-color: #fce4ec; /* Rosa muito claro, suave */
        }
        .stButton>button {
            background-color: #e91e63; /* Rosa vibrante */
            color: white;
            border-radius: 10px;
            padding: 0.5rem 1rem;
            border: none;
        }
        .stButton>button:hover {
            background-color: #c2185b;
        }
        h1 {
            color: #880e4f;
        }
        .news-card {
            padding: 1.5rem;
            background-color: white;
            border-radius: 10px;
            box_shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            border-left: 5px solid #e91e63;
        }
        </style>
        """, unsafe_allow_html=True)

    # Sidebar Configs
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1087/1087840.png", width=100) # Ícone genérico
        
        st.title("Configurações")
        
        # API Key agora é gerida no backend, mas mantemos aqui se quisermos enviar via Header futuramente
        api_key_env = os.getenv("GOOGLE_API_KEY")
        if not api_key_env:
             st.warning("Backend deve estar configurado com a API KEY")

        st.markdown("---")
        st.markdown("**Sobre o Agente**")
        st.info("Este agente busca notícias em tempo real sobre segurança pública no DF usando DuckDuckGo e analisa com Gemini.")

    # Cabeçalho
    st.title("🚔 Agente de Notícias: Segurança Pública DF")
    st.markdown(f"*Data: {get_current_date_str()}*")

    # Tabs
    tab1, tab2 = st.tabs(["🔍 Buscar Notícias", "📂 Histórico salvo"])

    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("O que você deseja investigar?", placeholder="Ex: Operações da PCDF, Crimes em Ceilândia...")
        with col2:
            st.write("") # Espaçamento
            st.write("")
            buscar_btn = st.button("Investigar 🔎", use_container_width=True)

        if buscar_btn and query:
            with st.spinner("O Agente (API) está em campo buscando informações..."):
                try:
                    # Chama a API Backend com Autenticação
                    headers = {"X-API-Key": os.getenv("APP_API_KEY", "insecure_dev_key")}
                    response = httpx.get(f"{API_URL}/news", params={"q": query}, headers=headers, timeout=30.0)
                    if response.status_code == 200:
                        news_items = response.json()
                        st.markdown("### 📝 Relatório de Inteligência (Backend)")
                        
                        if not news_items:
                            st.warning("Nenhuma notícia recente encontrada.")
                        
                        for item in news_items:
                            with st.expander(f"{item['title']} ({item['source']})"):
                                st.write(item['snippet'])
                                st.markdown(f"[Ler completa]({item['url']})")
                                st.caption(f"Publicado em: {item['publishedAt']}")
                        
                        # Análise AI via Groq (novo endpoint)
                        st.divider()
                        st.subheader("🤖 Análise de Inteligência (Groq Llama 3)")
                        with st.spinner("Analisando dados com LLM..."):
                            try:
                                # O agente já faz a busca internamente se necessário, mas podemos passar a query de análise
                                # Ou passar os dados recuperados para ele resumir.
                                # Como o Agente Groq está configurado com Tool Use de busca, podemos apenas passar a query original.
                                chat_response = httpx.get(f"{API_URL}/chat", params={"q": query}, timeout=60.0)
                                if chat_response.status_code == 200:
                                    # O endpoint retorna {"response": ...}
                                    analysis = chat_response.json().get("response")
                                    st.markdown(analysis)
                                else:
                                    st.error("Erro ao gerar análise.")
                            except Exception as e:
                                st.error(f"Erro no módulo de inteligência: {e}")

                    else:
                        st.error(f"Erro na API: {response.status_code}")

                except Exception as e:
                    st.error(f"Erro de conexão com o backend: {e}")

    with tab2:
        st.header("Arquivo de Inteligência (Via API)")
        if st.button("Atualizar Lista"):
            st.rerun()
            
        try:
            response = httpx.get(f"{API_URL}/news", params={"q": "segurança"}, timeout=10.0)
            if response.status_code == 200:
                noticias = response.json()
                if noticias:
                    for n in noticias:
                        with st.container():
                            st.markdown(f"""
                            <div class="news-card">
                                <h3>{n['title']}</h3>
                                <p style="color:gray; font-size:0.8rem;">📅 {n['publishedAt']}</p>
                                <p>{n['snippet']}</p>
                                <a href="{n['url']}" target="_blank">🔗 Link Original</a>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Nenhuma informação arquivada encontrada para 'segurança'.")
            else:
                st.error("Falha ao buscar histórico.")
        except:
            st.warning("Backend offline ou inacessível.")
