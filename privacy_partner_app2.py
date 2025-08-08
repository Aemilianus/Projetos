import streamlit as st
import pandas as pd
import re
import google.generativeai as genai
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.predefined_recognizers import EmailRecognizer
 
# --- Reconhecedores Customizados (Nossos "Especialistas") ---
class CustomBrCpfRecognizer(PatternRecognizer):
    PATTERNS = [Pattern(name="CPF", regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b", score=0.9)]
    def __init__(self, **kwargs):
        super().__init__(supported_entity="BR_CPF", name="Custom CPF Recognizer", patterns=self.PATTERNS, **kwargs)
 
class CustomAddressRecognizer(PatternRecognizer):
    PATTERNS = [Pattern(name="Endereco", regex=r"\b(Rua|Av\.|Avenida|Travessa|Praça|Est|Estrada)\s[\w\s,.-]+", score=0.8)]
    def __init__(self, **kwargs):
        super().__init__(supported_entity="STREET_ADDRESS", name="Custom Address Recognizer", patterns=self.PATTERNS, **kwargs)
 
class CustomBrPhoneRecognizer(PatternRecognizer):
    PATTERNS = [Pattern(name="Telefone", regex=r"\b(\(\d{2}\)\s?\d{4,5}-?\d{4}|\d{2}\s\d{4,5}-?\d{4})\b", score=0.9)]
    def __init__(self, **kwargs):
        super().__init__(supported_entity="PHONE_NUMBER", name="Custom Phone Recognizer", patterns=self.PATTERNS, **kwargs)
 
# --- Carregamento dos Motores (Versão Simplificada e Robusta) ---
@st.cache_resource
def get_analyzer():
    # 1. Começamos com um registro vazio
    registry = RecognizerRegistry()
    
    # 2. Adicionamos APENAS os especialistas que confiamos
    registry.add_recognizer(CustomBrCpfRecognizer(supported_language="pt"))
    registry.add_recognizer(CustomAddressRecognizer(supported_language="pt"))
    registry.add_recognizer(CustomBrPhoneRecognizer(supported_language="pt"))
    registry.add_recognizer(EmailRecognizer(supported_language="pt"))
    
    # 3. Criamos o Analyzer Engine apenas com nosso registro customizado, sem NLP Engine complexo
    analyzer = AnalyzerEngine(
        registry=registry,
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
    st.error(f"Loading error. Please check your API key and files. Error: {e}")
    st.stop()
 
# --- Interface do Mockup (em Inglês) ---
with st.sidebar:
    st.write("Recent Chats")
    st.button("💬 Campaign Analysis", use_container_width=True)
    st.button("📊 Sales Report", use_container_width=True)
 
st.markdown("<h1 style='text-align: center; color: #4A4A4A;'>L'ORÉAL GPT</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555; font-weight: normal;'>Privacy Partner Demonstration</h3>", unsafe_allow_html=True)
st.write("")
 
if 'messages' not in st.session_state: st.session_state.messages = []
if 'file_is_safe' not in st.session_state: st.session_state.file_is_safe = True
if 'file_content' not in st.session_state: st.session_state.file_content = None
 
uploaded_file = st.file_uploader("Or, attach a file (.csv) to use as context:", type=["csv"])
 
if uploaded_file:
    with st.spinner("Analyzing file..."):
        df = pd.read_csv(uploaded_file)
        file_content_string = df.to_string()
        analyzer_results = analyzer.analyze(text=file_content_string, language="pt")
        if analyzer_results:
st.error(f"🚨 **PRIVACY PARTNER:** The file `{uploaded_file.name}` contains sensitive data. Chat is locked.")
            st.session_state.file_is_safe = False
        else:
st.success(f"✅ **PRIVACY PARTNER:** The file `{uploaded_file.name}` is safe to use.")
            st.session_state.file_is_safe = True
            st.session_state.file_content = file_content_string
else:
    st.session_state.file_is_safe = True
    st.session_state.file_content = None
 
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)
 
prompt = st.chat_input("Enter your prompt or paste text to analyze...")
 
if prompt:
    if not st.session_state.file_is_safe:
        st.warning("Cannot process prompt because the attached file contains sensitive data. Please remove the file to continue.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner("Privacy Partner analyzing..."):
            analyzer_results = analyzer.analyze(text=prompt, language="pt")
        if analyzer_results:
            tipos_de_risco = list(set([res.entity_type for res in analyzer_results]))
            riscos_formatados = "\n".join([f"- {tipo}" for tipo in tipos_de_risco])
            alert_message = (
                f"🚨 **PRIVACY PARTNER ALERT!** 🚨\n\n"
                f"Your prompt contains potentially sensitive information and has been blocked to ensure compliance with our privacy policies.\n\n"
                f"**Potential Risks Detected:**\n"
                f"{riscos_formatados}\n\n"
                f"---\n"
                f"**Recommended Action:** Please remove the identified personal data and try submitting your prompt again."
            )
link_markdown = f"https://www.lorealanywhere.com/redir/352098' target='_blank' style='color: #0073e6; text-decoration: none;'>Learn more about protecting sensitive data.</a>"
            st.session_state.messages.append({"role": "assistant", "content": f"{alert_message}\n\n{link_markdown}"})
            with st.chat_message("assistant"):
                st.warning(alert_message, icon="⚠️")
                st.markdown(link_markdown, unsafe_allow_html=True)
        else:
            with st.spinner("Prompt is safe. Sending to the Generative AI..."):
                try:
                    full_prompt = prompt
                    if st.session_state.file_content:
                        full_prompt = f"Based on this context:\n---\n{st.session_state.file_content}\n---\n\nAnswer the following question: {prompt}"
                    response = gemini_model.generate_content(full_prompt)
                    response_text = response.text
                except Exception as e:
                    response_text = f"An error occurred while calling the AI API. Details: {e}"
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                with st.chat_message("assistant"):
                    st.markdown(response_text)
