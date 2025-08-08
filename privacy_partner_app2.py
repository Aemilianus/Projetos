import streamlit as st
import pandas as pd
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# --- Importar os Reconhecedores Específicos ---
from presidio_analyzer.predefined_recognizers import BrCpfRecognizer, PhoneRecognizer

# --- Carregamento dos Motores e Configuração ---
@st.cache_resource
def get_analyzer():
    """Cria e configura o motor de análise do Presidio com reconhecedores customizados."""
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
    
    analyzer.registry.add_recognizer(BrCpfRecognizer())
    analyzer.registry.add_recognizer(PhoneRecognizer(supported_regions=["BR"]))
    
    return analyzer

@st.cache_resource
def get_anonymizer():
    """Cria o motor de anonimização."""
    return AnonymizerEngine()

try:
    analyzer = get_analyzer()
    anonymizer = get_anonymizer()
    st.set_page_config(page_title="Privacy Partner Demo", layout="centered")

    # Carrega o arquivo CSS (se existir)
    try:
        with open(".streamlit/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Se o arquivo CSS não for encontrado, não faz nada.
        pass

except Exception as e:
    st.error(f"Erro ao carregar modelos: {e}")
    st.stop()

# --- Interface do Mockup ---

# Sidebar
with st.sidebar:
    st.write(" Chats Recentes")
    st.button("💬 Análise de Campanha", use_container_width=True)
    st.button("📊 Relatório de Vendas", use_container_width=True)

# --- BLOCO DE TÍTULO (SEM LOGO) ---
st.markdown("<h1 style='text-align: center; color: #4A4A4A;'>L'ORÉAL GPT</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555; font-weight: normal;'>Demonstração do Privacy Partner</h3>", unsafe_allow_html=True)
st.write("")

# Inicializa o estado da sessão
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'file_is_safe' not in st.session_state:
    st.session_state.file_is_safe = True

# Bloco para Upload e Análise de Arquivo
uploaded_file = st.file_uploader("Ou anexe um arquivo (.csv) para usar como contexto:", type=["csv"])

if uploaded_file:
    with st.spinner("Analisando arquivo em busca de riscos de privacidade..."):
        df = pd.read_csv(uploaded_file)
        file_content_string = df.to_string()
        analyzer_results = analyzer.analyze(text=file_content_string, language="pt")

        if analyzer_results:
            st.error(f"🚨 **PRIVACY PARTNER:** O arquivo `{uploaded_file.name}` contém dados sensíveis e não pode ser usado. O chat está bloqueado até que o arquivo seja removido.")
            st.session_state.file_is_safe = False
        else:
            st.success(f"✅ **PRIVACY PARTNER:** O arquivo `{uploaded_file.name}` foi analisado e é seguro para uso.")
            st.session_state.file_is_safe = True
else:
    # Garante que o chat seja liberado se o arquivo for removido
    if not st.session_state.get('file_uploader_key', True):
        st.session_state.file_is_safe = True

# Exibe as mensagens do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
prompt = st.chat_input("Digite seu prompt ou cole um texto para análise...")

if prompt:
    if not st.session_state.file_is_safe:
        st.warning("Não é possível processar seu prompt pois o arquivo anexado contém dados sensíveis. Por favor, remova o arquivo para continuar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Analisando prompt..."):
            analyzer_results = analyzer.analyze(text=prompt, language="pt")

        if analyzer_results:
            alert_message = "🚨 **ALERTA DO PRIVACY PARTNER!** 🚨\n\nO seu prompt contém dados sensíveis e não será processado. Por favor, remova as informações e tente novamente."
            st.session_state.messages.append({"role": "assistant", "content": alert_message})
            with st.chat_message("assistant"):
                st.warning(alert_message)
        else:
            response_message = "✅ **Privacy Partner:** Nenhuma informação sensível detectada no prompt. \n\n (Aqui viria a resposta normal do L'Oréal GPT...)"
            st.session_state.messages.append({"role": "assistant", "content": response_message})
            with st.chat_message("assistant"):
                st.success(response_message)