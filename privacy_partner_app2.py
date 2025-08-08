import streamlit as st
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from PIL import Image

# --- Carregamento dos Motores e Configuração ---
@st.cache_resource
def get_analyzer():
    """Cria e configura o motor de análise do Presidio."""
    provider_config = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]
    }
    provider = NlpEngineProvider(nlp_configuration=provider_config)
    nlp_engine = provider.create_engine()
    
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["pt"]
    )
    return analyzer

@st.cache_resource
def get_anonymizer():
    """Cria o motor de anonimização."""
    return AnonymizerEngine()

try:
    analyzer = get_analyzer()
    anonymizer = get_anonymizer()
    st.set_page_config(page_title="L'Oréal GPT - Privacy Partner", layout="centered")

    # Carrega o arquivo CSS
    with open(".streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao carregar modelos: {e}")
    st.stop()

# --- Interface do Mockup ---

# Sidebar com ícones (simulação)
with st.sidebar:
    st.write(" Chats Recentes")
    st.button("💬 Análise de Campanha", use_container_width=True)
    st.button("📊 Relatório de Vendas", use_container_width=True)
    st.button("📝 Ideias para Posts", use_container_width=True)
    st.button("📄 Tradução de Documento", use_container_width=True)

# Bloco para exibir a Logo
try:
    logo = Image.open("logo_loreal_gpt.png")
    # CORREÇÃO APLICADA AQUI:
    st.image(logo, use_column_width=True) # Alterado para o novo parâmetro
except FileNotFoundError:
    st.title("L'ORÉAL GPT") # Fallback caso a imagem não seja encontrada

st.markdown("<h3 style='text-align: center; color: #555; font-weight: normal;'>Bem-vindo à plataforma de IA Generativa da L'Oréal.</h3>", unsafe_allow_html=True)
st.write("") # Adiciona um espaço

# Inicializa o estado da sessão para guardar as mensagens
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Exibe as mensagens do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
prompt = st.chat_input("Digite seu prompt ou cole um texto para análise...")

if prompt:
    # Adiciona a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- LÓGICA DO PRIVACY PARTNER ---
    with st.spinner("Analisando em busca de riscos de privacidade..."):
        analyzer_results = analyzer.analyze(text=prompt, language="pt")

    # Se encontrar riscos, mostra o alerta e não continua
    if analyzer_results:
        alert_message = f"""
        🚨 **ALERTA DO PRIVACY PARTNER!** 🚨

        O texto que você inseriu contém **{len(analyzer_results)}** tipo(s) de informações pessoais/sensíveis.
        
        **Riscos Detectados:**
        """
        tipos_de_risco = list(set([res.entity_type for res in analyzer_results]))
        for tipo in tipos_de_risco:
            alert_message += f"\n- {tipo}"

        alert_message += """
        \n\n**Ação:** Conforme os Termos de Uso, para proteger os dados de nossos clientes e colaboradores, este prompt não será processado. Por favor, remova os dados sensíveis e tente novamente.
        """
        
        st.session_state.messages.append({"role": "assistant", "content": alert_message})
        with st.chat_message("assistant"):
            st.warning(alert_message)

    # Se não encontrar riscos, simula uma resposta normal do GPT
    else:
        response_message = "✅ **Privacy Partner:** Nenhuma informação sensível detectada. Seu prompt foi processado com segurança. \n\n (Aqui viria a resposta normal do L'Oréal GPT...)"
        st.session_state.messages.append({"role": "assistant", "content": response_message})
        with st.chat_message("assistant"):
            st.success(response_message)
