import streamlit as st
import pandas as pd
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# --- Presidio Configuration ---
@st.cache_resource
def get_analyzer_and_anonymizer():
    # --- CORREÇÃO APLICADA AQUI ---
    # 1. Cria um registro para o idioma português
    registry = RecognizerRegistry(supported_languages=["pt"])
    
    # 2. Carrega os reconhecedores padrão (incluindo o de Nomes - PERSON)
    registry.load_predefined_recognizers(languages=["pt"])

    # 3. Define e adiciona nosso reconhecedor customizado de CPF
    cpf_recognizer = PatternRecognizer(
        supported_entity="BR_CPF",
        name="CPF Recognizer",
        patterns=[Pattern(name="cpf", regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b", score=0.9)],
        supported_language="pt"
    )
    registry.add_recognizer(cpf_recognizer)
    
    # 4. Configura o motor de linguagem que alimenta os reconhecedores
    provider_config = {"nlp_engine_name": "spacy", "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]}
    provider = NlpEngineProvider(nlp_configuration=provider_config)
    nlp_engine = provider.create_engine()
    
    # 5. Cria o motor de análise com o registro completo e alinhado
    analyzer = AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["pt"]
    )
    anonymizer = AnonymizerEngine()
    
    return analyzer, anonymizer

analyzer, anonymizer = get_analyzer_and_anonymizer()

# --- Application Interface ---
st.set_page_config(layout="wide", page_title="Privacy Partner - Excel Mockup")

# Green Excel Header Bar
st.markdown(
    """<div style='background-color:#1D6F42;padding:10px;border-radius:5px 5px 0 0;'><h1 style='color:white;text-align:left;font-size:18px;font-weight:normal;margin:0;'>
       Excel - Sensitive_Test.csv</h1></div>""",
    unsafe_allow_html=True
)

# Simulation of Excel's Ribbon
tabs = st.tabs(["File", "Home", "Insert", "▶️ Add-ins"])
excel_tab = tabs[3]

# Sample data
data = {
    'Name': ['Ana da Silva Santos', 'Maria Da Silva', 'João Dos Santos', 'José da Silva Santos'],
    'CPF': ['123.456.789-11', '148.258.127-24', '111.444.777-35', '987.654.321-00']
}
df = pd.DataFrame(data)

# Initialize session state
if 'df_data' not in st.session_state:
    st.session_state.df_data = df.copy()
if 'original_df' not in st.session_state:
    st.session_state.original_df = df.copy()
if 'findings' not in st.session_state:
    st.session_state.findings = []
if 'last_edited_df' not in st.session_state:
    st.session_state.last_edited_df = df.copy()


# Main container for the "spreadsheet"
edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="data_editor", height=250)

# Logic for the Add-in in the "Add-ins" tab
with excel_tab:
    st.markdown("---")
    if st.button("🚀 Privacy Partner Scan", help="Click to scan the spreadsheet for sensitive data."):
        with st.spinner("Analyzing spreadsheet..."):
            findings = []
            for index, row in edited_df.iterrows():
                for col_name, cell_value in row.items():
                    if cell_value and isinstance(cell_value, str):
                        results = analyzer.analyze(text=cell_value, language="pt")
                        if results:
                            findings.append({'row': index, 'col': col_name, 'text': cell_value, 'type': results[0].entity_type})
            st.session_state.findings = findings
            st.session_state.last_edited_df = edited_df.copy() # Save state at scan time
            st.rerun()

# Sidebar acting as the Add-in's task pane
with st.sidebar:
    st.title("Privacy Partner")
    st.markdown("Your privacy assistant for Excel.")
    st.markdown("---")

    if st.button("Reset to Original Data"):
        st.session_state.df_data = st.session_state.original_df.copy()
        st.session_state.findings = []
        st.rerun()

    if st.session_state.findings:
        st.warning(f"**Alert!** {len(st.session_state.findings)} sensitive data point(s) found.")
        
        summary = {}
        for find in st.session_state.findings:
            summary.setdefault(find['col'], []).append(find['type'])
        for col, types in summary.items():
            st.markdown(f"- **Column '{col}'**: Found **{', '.join(set(types))}**.")

        st.markdown("---")
        st.markdown("**Recommended Actions:**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Anonymize"):
                anonymized_df = st.session_state.last_edited_df.copy()
                for find in st.session_state.findings:
                    anonymized_df.at[find['row'], find['col']] = f"<{find['type']}>"
                st.session_state.df_data = anonymized_df
                st.session_state.findings = []
                st.rerun()

        with col2:
            if st.button("Pseudonymize"):
                pseudo_df = st.session_state.last_edited_df.copy()
                for find in st.session_state.findings:
                    pseudo_text = f"{find['type']}_{abs(hash(find['text'])) % 10000}"
                    pseudo_df.at[find['row'], find['col']] = pseudo_text
                st.session_state.df_data = pseudo_df
                st.session_state.findings = []
                st.rerun()
    else:
        st.success("No sensitive data detected.")
