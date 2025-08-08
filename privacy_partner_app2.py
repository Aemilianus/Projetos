import streamlit as st
import pandas as pd
import re
import google.generativeai as genai
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_analyzer.predefined_recognizers import PhoneRecognizer

# --- Reconhecedor de CPF Customizado e Inteligente ---
class CustomBrCpfRecognizer(PatternRecognizer):
    PATTERNS = [Pattern(name="cpf", regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b", score=0.5)]
    def __init__(self, **kwargs):
        super().__init__(supported_entity="BR_CPF", name="Custom CPF Recognizer (with Checksum)", patterns=self.PATTERNS, **kwargs)
    def validate_result(self, pattern_text: str) -> bool:
        cpf = "".join(re.findall(r'\d', pattern_text))
        if len(cpf) != 11 or len(set(cpf)) == 1: return False
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        d1 = 11 - (soma % 11)
        if d1 >= 10: d1 = 0
        if d1 != int(cpf[9]): return False
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        d2 = 11 - (soma % 11)
        if d2 >= 10: d2 = 0
        if d2 != int(cpf[10]): return False
        return True

# --- Reconhecedor de Telefone Customizado e Criterioso ---
class CustomBrPhoneRecognizer(PatternRecognizer):
    PATTERNS = [Pattern(name="telefone_formatado", regex=r"\b(\(\d{2}\)\s?\d{4,5}-?\d{4}|\d{2}\s\d{4,5}-?\d{4})\b", score=0.9)]
    def __init__(self, **kwargs):
        super().__init__(supported_entity="PHONE_NUMBER", name="Custom Phone Recognizer (Formatted)", patterns=self.PATTERNS, **kwargs)

# --- Carregamento dos Motores e Configuração ---
@st.cache_resource
def get_analyzer():
    provider_config = {"nlp_engine_name": "spacy", "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]}
    provider = NlpEngineProvider(nlp_configuration=provider_config)
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["pt"])
    analyzer.registry.add_recognizer(CustomBrCpfRecognizer())
    analyzer.registry.add_recognizer(CustomBrPhoneRecognizer())
    return analyzer

# --- Configuração e carregamento do modelo Gemini ---
@st.cache_resource
def get_gemini_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # --- CORREÇÃO APLICADA AQUI ---
    # Alterado de 'gemini-pro' para o modelo mais recente
    return genai.GenerativeModel('gemini-1.5-flash-latest')

try:
    analyzer = get_analyzer()
    gemini_model = get_gemini_model()
    st.set_page_config(page_title="Privacy Partner Demo", layout="centered")
    with open(".streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erro ao carregar. Verifique sua chave de API nos 'Secrets' e se o arquivo CSS existe. Erro: {e}")
    st.stop()

# --- Interface do Mockup ---
with st.sidebar:
    st.write(" Chats Recentes")
    st.button("💬 Análise de Campanha", use_container_width=True)
    st.button("📊 Relatório de Vendas", use_container_width=True)

st.markdown("<h1 style='text-align: center; color: #4A4A4A;'>L'ORÉAL GPT</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555; font-weight: normal;'>Demonstração do Privacy Partner</h3>", unsafe_allow_html=True)
st.write("")

if 'messages' not in st.session_state: st.session_state.messages = []
if 'file_is_safe' not in st.session_state: st.session_state.file_is_safe = True
if 'file_content' not in st.session_state: st.session_state.file_content = None

uploaded_file = st.file_uploader("Ou anexe um arquivo (.csv) para usar como contexto:", type=["csv"])

if uploaded_file:
    with st.spinner("Analisando arquivo..."):
        df = pd.read_csv(uploaded_file)
        file_content_string = df.to_string()
        analyzer_results = analyzer.analyze(text=file_content_string, language="pt")
        if analyzer_results:
            st.error(f"🚨 **PRIVACY PARTNER:** O arquivo `{uploaded_file.name}` contém dados sensíveis. O chat está bloqueado.")
            st.session_state.file_is_safe = False
            st.session_state.file_content = None
        else:
            st.success(f"✅ **PRIVACY PARTNER:** O arquivo `{uploaded_file.name}` é seguro para uso.")
            st.session_state.file_is_safe = True
            st.session_state.file_content = file_content_string
else:
    st.session_state.file_is_safe = True
    st.session_state.file_content = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Digite seu prompt ou cole um texto para análise...")

if prompt:
    if not st.session_state.file_is_safe:
        st.warning("Não é possível processar seu prompt pois o arquivo anexado contém dados sensíveis. Remova o arquivo para continuar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Privacy Partner analisando..."):
            analyzer_results = analyzer.analyze(text=prompt, language="pt")

        if analyzer_results:
            alert_message = "🚨 **ALERTA DO