import streamlit as st
import pandas as pd
import re
import google.generativeai as genai
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
# Importando os reconhecedores que queremos USAR
from presidio_analyzer.predefined_recognizers import EmailRecognizer

# --- Reconhecedor de CPF Customizado e Inteligente ---
class CustomBrCpfRecognizer(PatternRecognizer):
    PATTERNS = [Pattern(name="cpf", regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b", score=0.8)]
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
    
    # --- CONFIGURAÇÃO SIMPLIFICADA DO ANALYZER ---
    # Inicializa o motor sem filtros, vamos aplicá-los depois.
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["pt"]
    )
    
    # Adicionamos os nossos reconhecedores "especialistas"
    analyzer.registry.add_recognizer(CustomBrCpfRecognizer())
    analyzer.registry.add_recognizer(CustomBrPhoneRecognizer())
    analyzer.registry.add_recognizer(EmailRecognizer())
    
    return analyzer

# --- Configuração e carregamento do modelo Gemini ---
@st.cache_resource
def get_gemini_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash-latest')

try:
    analyzer = get_analyzer()
    gemini_model = get_gemini_model()
    st.set_page_config(page_title="Privacy Partner Demo", layout="centered")
    with open(".streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erro ao carregar. Verifique sua chave de API e arquivos. Erro: {e}")
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

# Lista de entidades que consideramos PII de alto risco
entidades_pii = ["BR_CPF", "PHONE_NUMBER", "EMAIL_ADDRESS", "PERSON"]

uploaded_file = st.file_uploader("Ou anexe um arquivo (.csv) para usar como contexto:", type=["csv"])

if uploaded_file:
    with st.spinner("Analisando arquivo..."):
        df = pd.read_csv(uploaded_file)
        file_content_string = df.to_string()
        # --- MUDANÇA APLICADA AQUI ---
        analyzer_results = analyzer.analyze(text=file_content_string, language="pt", entities=entidades_pii, score_threshold=0.7)
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
            # --- MUDANÇA APLICADA AQUI ---
            analyzer_results = analyzer.analyze(text=prompt, language="pt", entities=entidades_pii, score_threshold=0.7)

        if analyzer_results:
            tipos_de_risco = list(set([res.entity_type for res in analyzer_results]))
            riscos_formatados = "\n".join([f"- {tipo}" for tipo in tipos_de_risco])
            alert_message = f"""
            🚨 **ALERTA DO PRIVACY PARTNER!** 🚨

            Seu prompt contém **{len(tipos_de_risco)}** tipo(s) de informações sensíveis e não será processado.
            
            **Riscos Detectados:**
            {riscos_formatados}
            """
            st.session_state.messages.append({"role": "assistant", "content": alert_message})
            with st.chat_message("assistant"):
                st.warning(alert_message)
        else:
            with st.spinner("Prompt seguro. Enviando para a IA Generativa..."):
                try:
                    full_prompt = prompt
                    if st.session_state.file_content:
                        full_prompt = f"Com base neste contexto:\n---\n{st.session_state.file_content}\n---\n\nResponda à seguinte pergunta: {prompt}"
                    
                    response = gemini_model.generate_content(full_prompt)
                    response_text = response.text
                except Exception as e:
                    response_text = f"Ocorreu um erro ao chamar a API da IA. Detalhes: {e}"

                st.session_state.messages.append({"role": "assistant", "content": response_text})
                with st.chat_message("assistant"):
                    st.markdown(response_text)