import streamlit as st
import pandas as pd
import re
import google.generativeai as genai
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistry
from presidio_analyzer.predefined_recognizers import EmailRecognizer

# --- Reconhecedores Customizados ---
class CustomBrCpfRecognizer(PatternRecognizer):
    PATTERNS = [Pattern(name="cpf", regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b", score=0.9)]
    def __init__(self, **kwargs):
        super().__init__(supported_entity="BR_CPF", name="Custom CPF Recognizer", patterns=self.PATTERNS, **kwargs)

class CustomAddressRecognizer(PatternRecognizer):
    PATTERNS = [Pattern(name="endereco", regex=r"\b(Rua|Av\.|Avenida|Travessa|Praça|Est|Estrada)\s[\w\s,.-]+", score=0.8)]
    def __init__(self, **kwargs):
        super().__init__(supported_entity="STREET_ADDRESS", name="Custom Address Recognizer", patterns=self.PATTERNS, **kwargs)

class CustomBrPhoneRecognizer(PatternRecognizer):
    PATTERNS = [Pattern(name="telefone_formatado", regex=r"\b(\(\d{2}\)\s?\d{4,5}-?\d{4}|\d{2}\s\d{4,5}-?\d{4})\b", score=0.9)]
    def __init__(self, **kwargs):
        super().__init__(supported_entity="PHONE_NUMBER", name="Custom Phone Recognizer", patterns=self.PATTERNS, **kwargs)

# --- Carregamento dos Motores e Configuração ---
@st.cache_resource
def get_analyzer():
    registry = RecognizerRegistry(supported_languages=["pt"])
    registry.load_predefined_recognizers(languages=["pt"])
    
    # Adicionamos nossos especialistas, garantindo que eles suportem português
    registry.add_recognizer(CustomBrCpfRecognizer(supported_language="pt"))
    registry.add_recognizer(CustomAddressRecognizer(supported_language="pt"))
    registry.add_recognizer(CustomBrPhoneRecognizer(supported_language="pt"))
    
    # Removemos os reconhecedores padrão que são muito genéricos
    registry.remove_recognizer("PhoneRecognizer")
    registry.remove_recognizer("DateRecognizer")
    
    # O motor de linguagem agora será usado apenas para contexto, não para detecção direta de Nomes
    provider_config = {"nlp_engine_name": "spacy", "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]}
    provider = NlpEngineProvider(nlp_configuration=provider_config)
    nlp_engine = provider.create_engine()
    
    analyzer = AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["pt"]
    )
    return analyzer

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

# Lista de entidades que consideramos PII de alto risco (REMOVEMOS 'PERSON')
entidades_pii = ["BR_CPF", "PHONE_NUMBER", "EMAIL_ADDRESS", "STREET_ADDRESS"]

uploaded_file = st.file_uploader("Ou anexe um arquivo (.csv) para usar como contexto:", type=["csv"])
if uploaded_file:
    with st.spinner("Analisando arquivo..."):
        df = pd.read_csv(uploaded_file)
        file_content_string = df.to_string()
        analyzer_results = analyzer.analyze(text=file_content_string, language="pt", entities=entidades_pii)
        if analyzer_results:
            st.error(f"🚨 **PRIVACY PARTNER:** O arquivo `{uploaded_file.name}` contém dados sensíveis. O chat está bloqueado.")
            st.session_state.file_is_safe = False
        else:
            st.success(f"✅ **PRIVACY PARTNER:** O arquivo `{uploaded_file.name}` é seguro para uso.")
            st.session_state.file_is_safe = True
            st.session_state.file_content = file_content_string
else:
    st.session_state.file_is_safe = True
    st.session_state.file_content = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

prompt = st.chat_input("Digite seu prompt ou cole um texto para análise...")

if prompt:
    if not st.session_state.file_is_safe:
        st.warning("Não é possível processar seu prompt pois o arquivo anexado contém dados sensíveis. Remova o arquivo para continuar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner("Privacy Partner analisando..."):
            analyzer_results = analyzer.analyze(text=prompt, language="pt", entities=entidades_pii)
        if analyzer_results:
            tipos_de_risco = list(set([res.entity_type for res in analyzer_results]))
            riscos_formatados = "\n".join([f"- {tipo}" for tipo in tipos_de_risco])
            
            # --- MENSAGEM DE BLOQUEIO E HIPERLINK CORRIGIDOS ---
            alert_message = (
                f"🚨 **ALERTA DO PRIVACY PARTNER!** 🚨\n\n"
                f"Seu prompt contém informações que podem ser sensíveis e, para garantir a conformidade com nossas políticas de privacidade, ele foi bloqueado.\n\n"
                f"**Riscos Potenciais Detectados:**\n"
                f"{riscos_formatados}\n\n"
                f"---\n"
                f"**Ação Recomendada:** Por favor, remova os dados pessoais identificados e tente enviar seu prompt novamente."
            )
            link_markdown = "<a href='http://www.loreal.com/privacidade' target='_blank' style='color: #0073e6; text-decoration: none;'>Saiba mais sobre como proteger dados sensíveis.</a>"
            
            st.session_state.messages.append({"role": "assistant", "content": f"{alert_message}\n\n{link_markdown}"})
            with st.chat_message("assistant"):
                st.warning(alert_message, icon="⚠️")
                st.markdown(link_markdown, unsafe_allow_html=True)
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