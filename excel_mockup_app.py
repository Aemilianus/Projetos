import streamlit as st
import pandas as pd
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

# --- Presidio Configuration ---
@st.cache_resource
def get_analyzer():
    # Define o reconhecedor de CPF
    cpf_recognizer = PatternRecognizer(
        supported_entity="BR_CPF",
        name="CPF Recognizer",
        patterns=[Pattern(name="cpf", regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b", score=0.9)],
        supported_language="pt"
    )
    
    # Cria um registro e adiciona o especialista em CPF
    registry = RecognizerRegistry(supported_languages=["pt"])
    registry.add_recognizer(cpf_recognizer)
    
    # Configura o motor de linguagem para encontrar Nomes de Pessoas
    provider_config = {"nlp_engine_name": "spacy", "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]}
    provider = NlpEngineProvider(nlp_configuration=provider_config)
    nlp_engine = provider.create_engine()
    
    # Cria o motor de análise
    analyzer = AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["pt"]
    )
    return analyzer

analyzer = get_analyzer()

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
    'Nome': ['Ana da Silva Santos', 'Maria Da Silva', 'João Dos Santos'],
    'CPF': ['123.456.789-11', '148.258.127-24', '111.444.777-35'],
}
df = pd.DataFrame(data)

# Initialize session state
if 'df_data' not in st.session_state:
    st.session_state.df_data = df.copy()
if 'original_df' not in st.session_state:
    st.session_state.original_df = df.copy()
if 'findings' not in st.session_state:
    st.session_state.findings = []

# Main container for the "spreadsheet"
edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="data_editor", height=200)

# Logic for the Add-in in the "Add-ins" tab
with excel_tab:
    if st.button("🚀 Privacy Partner Scan", help="Click to scan the spreadsheet for sensitive data."):
        with st.spinner("Analyzing spreadsheet..."):
            findings = []
            for index, row in edited_df.iterrows():
                for col_name, cell_value in row.items():
                    if cell_value and isinstance(cell_value, str):
                        # Analisa apenas para os tipos que queremos: Nomes e CPF
                        results = analyzer.analyze(text=cell_value, language="pt", entities=["PERSON", "BR_CPF"])
                        if results:
                            findings.append({'row': index, 'col': col_name, 'text': cell_value, 'type': results[0].entity_type})
            st.session_state.findings = findings

# Sidebar acting as the Add-in's task pane
with st.sidebar:
    st.title("Privacy Partner")
    st.markdown("Your privacy assistant for Excel.")
    st.markdown("---")

    # Botão de Reset sempre visível
    if st.button("Reset to Original Data"):
        st.session_state.df_data = st.session_state.original_df.copy()
        st.session_state.findings = []
        st.rerun()

    if st.session_state.findings:
        st.warning(f"**Alert!** {len(st.session_state.findings)} sensitive data point(s) found.")
        
        # Display summary
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
                anonymized_df = edited_df.copy()
                for find in st.session_state.findings:
                    anonymized_df.at[find['row'], find['col']] = f"<{find['type']}>"
                st.session_state.df_data = anonymized_df
                st.session_state.findings = []
                st.rerun()

        with col2:
            if st.button("Pseudonymize"):
                pseudo_df = edited_df.copy()
                for find in st.session_state.findings:
                    original_text = find['text']
                    pseudo_text = f"{find['type']}_{abs(hash(original_text)) % 10000}"
                    pseudo_df.at[find['row'], find['col']] = pseudo_text
                st.session_state.df_data = pseudo_df
                st.session_state.findings = []
                st.rerun()
    else:
        st.success("No sensitive data detected.")
