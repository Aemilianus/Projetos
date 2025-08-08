import streamlit as st
import pandas as pd
import re
import google.genergenerativeai as genai
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.predefined_recognizers import EmailRecognizer
 
# --- Reconhecedores Customizados ---
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
 
# --- Carregamento dos Motores ---
@st.cache_resource
def get_analyzer():
    registry = RecognizerRegistry()
    registry.add_recognizer(CustomBrCpfRecognizer(supported_language="pt"))
    registry.add_recognizer(CustomAddressRecognizer(supported_language="pt"))
    registry.add_recognizer(CustomBrPhoneRecognizer(supported_language="pt"))
    registry.add_recognizer(EmailRecognizer(supported_language="pt"))
    
    analyzer = AnalyzerEngine(registry=registry, supported_languages=["pt"])
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
    st.error(f"Loading error: {e}")
    st.stop()
 
# --- Interface do Mockup ---
with st.sidebar:
    st.write("Recent Chats")
    st.button("💬 Campaign Analysis", use_container_width=True)
    st.button("📊 Sales Report", use_container_width=True)
 
st.markdown("<h1 style='text-align: center; color: #4A4A4A;'>L'ORÉAL GPT</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555; font-weight: normal;'>Privacy Partner Demonstration</h3>", unsafe_allow_html=True)
st.write("")
 
if 'messages' not in st.session_state: st.session_state.messages = []
if 'file_is_safe' not in st.session_state: st.session_state.file_is_safe = True
 
# --- BLOCO DE UPLOAD DE ARQUIVO COM A CORREÇÃO ---
uploaded_file = st.file_uploader("Or, attach a file (.csv) to use as context:", type=["csv"])
 
if uploaded_file:
    with st.spinner("Analyzing file cell by cell..."):
        try:
            df = pd.read_csv(uploaded_file, encoding='latin-1')
            problematic_columns = {}
 
            for index, row in df.iterrows():
                for col_name, cell_value in row.items():
                    if cell_value and isinstance(cell_value, str):
                        analyzer_results = analyzer.analyze(text=cell_value, language="pt")
                        if analyzer_results:
                            problematic_columns.setdefault(col_name, set()).add(analyzer_results[0].entity_type)
            
            if problematic_columns:
                st.session_state.file_is_safe = False
st.error(f"🚨 **PRIVACY PARTNER:** The file `{uploaded_file.name}` contains sensitive data. The chat has been locked.")
                
                warning_details = []
                for col, pii_types in problematic_columns.items():
                    warning_details.append(f"- **Column '{col}'** contains data of type: **{', '.join(pii_types)}**.")
                
                summary_text = "\n".join(warning_details)
                
                warning_message = (
                    f"The analysis found potential privacy risks in the following columns:\n"
                    f"{summary_text}\n\n"
                    f"**Recommended Action:** Please anonymize or pseudonymize the data in these columns. You can use the **Privacy Partner Add-in for Excel** to help with this task before uploading the file again."
                )
                st.warning(warning_message, icon="⚠️")
            else:
st.success(f"✅ **PRIVACY PARTNER:** The file `{uploaded_file.name}` is safe to use.")
                st.session_state.file_is_safe = True
                st.session_state.file_content = df.to_string()
        
        # O bloco 'except' que estava faltando agora está aqui
        except Exception as e:
            st.error(f"Could not read the CSV file. Please ensure it is a valid CSV. Error: {e}")
            st.session_state.file_is_safe = False
else:
    st.session_state.file_is_safe = True
    st.session_state.file_content = None
 
# --- Lógica do Chat (Simulado) ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
 
prompt = st.chat_input("Enter your prompt or paste text to analyze...")
 
if prompt:
    if not st.session_state.file_is_safe:
        st.warning("Cannot process prompt because the attached file contains sensitive data. Please remove the file to continue.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.spinner("Processing..."):
            response_text = "✅ **Privacy Partner:** Prompt is safe. (This is a simulation. In a real scenario, the AI's response would appear here.)"
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant"):
                st.markdown(response_text)
