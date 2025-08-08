import streamlit as st
import pandas as pd
import re
import google.generativeai as genai
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
# LINHA ADICIONADA AQUI:
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
def get_analyzer_and_anonymizer():
    registry = RecognizerRegistry()
    registry.add_recognizer(CustomBrCpfRecognizer(supported_language="pt"))
    registry.add_recognizer(CustomAddressRecognizer(supported_language="pt"))
    registry.add_recognizer(CustomBrPhoneRecognizer(supported_language="pt"))
    registry.add_recognizer(EmailRecognizer(supported_language="pt"))
    
    analyzer = AnalyzerEngine(registry=registry, supported_languages=["pt"])
    anonymizer = AnonymizerEngine()
    
    return analyzer, anonymizer

@st.cache_resource
def get_gemini_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash-latest')

try:
    analyzer, anonymizer = get_analyzer_and_anonymizer()
    gemini_model = get_gemini_model()
    st.set_page_config(page_title="Privacy Partner Demo", layout="centered")
    with open(".streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Loading error: {e}")
    st.stop()

# --- Interface do Mockup (em Inglês) ---
with st.sidebar:
    st.write("Recent Chats")
    st.button("💬 Campaign Analysis", use_container_width=True)
    st.button("📊 Sales Report", use_container_width=True)

st.markdown("<h1 style='text-align: center; color: #4A4A4A;'>L'ORÉAL GPT</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555; font-weight: normal;'>Privacy Partner Demonstration</h3>", unsafe_allow_html=True)
st.write("")

# --- Inicialização do Estado da Sessão ---
if 'messages' not in st.session_state: st.session_state.messages = []
if 'file_is_safe' not in st.session_state: st.session_state.file_is_safe = True
if 'original_df' not in st.session_state: st.session_state.original_df = None
if 'anonymized_df' not in st.session_state: st.session_state.anonymized_df = None

# --- LÓGICA DE UPLOAD E ANÁLISE COM ANONIMIZAÇÃO ---
uploaded_file = st.file_uploader("Or, attach a file (.csv) to use as context:", type=["csv"])

if uploaded_file:
    with st.spinner("Analyzing file..."):
        try:
            df = pd.read_csv(uploaded_file, encoding='latin-1')
            st.session_state.original_df = df
            findings = []

            for index, row in df.iterrows():
                for col_name, cell_value in row.items():
                    if cell_value and isinstance(cell_value, str):
                        analyzer_results = analyzer.analyze(text=cell_value, language="pt")
                        if analyzer_results:
                            findings.append(True)
            
            if findings:
                st.session_state.file_is_safe = False
                st.error(f"🚨 **PRIVACY PARTNER:** The file `{uploaded_file.name}` contains sensitive data. Chat is locked.")
                st.info("The analysis found potential privacy risks in the file.")

                if st.button("Anonymize File Directly"):
                    with st.spinner("Anonymizing data..."):
                        anonymized_df = st.session_state.original_df.copy()
                        for index, row in anonymized_df.iterrows():
                            for col_name, cell_value in row.items():
                                if cell_value and isinstance(cell_value, str):
                                    analyzer_results = analyzer.analyze(text=cell_value, language="pt")
                                    if analyzer_results:
                                        anonymized_result = anonymizer.anonymize(
                                            text=cell_value,
                                            analyzer_results=analyzer_results,
                                            operators={"DEFAULT": OperatorConfig("replace", {"new_value": f"<{analyzer_results[0].entity_type}>"})}
                                        )
                                        anonymized_df.at[index, col_name] = anonymized_result.text
                        st.session_state.anonymized_df = anonymized_df
            else:
                st.success(f"✅ **PRIVACY PARTNER:** The file `{uploaded_file.name}` is safe to use.")
                st.session_state.file_is_safe = True
        except Exception as e:
            st.error(f"Could not read the CSV file. Error: {e}")
            st.session_state.file_is_safe = False
else:
    st.session_state.file_is_safe = True
    st.session_state.anonymized_df = None

if st.session_state.anonymized_df is not None:
    st.success("File anonymized successfully!")
    st.dataframe(st.session_state.anonymized_df.head())
    
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_anonymized = convert_df_to_csv(st.session_state.anonymized_df)
    
    st.download_button(
       label="Download Anonymized CSV",
       data=csv_anonymized,
       file_name=f"anonymized_{uploaded_file.name}",
       mime="text/csv",
    )

# --- Lógica do Chat (Simulado) ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Enter your prompt or paste a text for analysis...")
if prompt:
    if not st.session_state.file_is_safe:
        st.warning("Cannot process prompt because the attached file contains sensitive data. Please remove the file or anonymize it first.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner("Processing..."):
            response_text = "✅ **Privacy Partner:** Prompt is safe. (This is a simulation. In a real scenario, the AI's response would appear here.)"
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant"):
                st.markdown(response_text)