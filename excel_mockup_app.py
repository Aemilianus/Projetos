import streamlit as st
import pandas as pd
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

# --- Presidio Configuration ---
@st.cache_resource
def get_analyzer_and_anonymizer():
    cpf_recognizer = PatternRecognizer(
        supported_entity="BR_CPF",
        name="CPF Recognizer",
        patterns=[Pattern(name="cpf", regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b", score=0.9)],
        supported_language="pt"
    )
    
    registry = RecognizerRegistry(supported_languages=["pt"])
    registry.add_recognizer(cpf_recognizer)
    
    provider_config = {"nlp_engine_name": "spacy", "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]}
    provider = NlpEngineProvider(nlp_configuration=provider_config)
    nlp_engine = provider.create_engine()
    
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

# --- NEW: Green Excel Header Bar ---
st.markdown(
    """
    <div style="background-color:#1D6F42;padding:10px;border-top-left-radius:5px;border-top-right-radius:5px;">
        <h1 style="color:white;text-align:left;font-size:18px;font-weight:normal;margin:0;">
            Excel - Sensitive_Test.csv
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Simulation of Excel's Ribbon
st.markdown("##### File | Home | Insert | Formulas | Data | Review")
tabs = st.tabs(["▶️ **Add-ins**", "Help", "Power Pivot"])
excel_tab = tabs[0]

# Sample data from your screenshot
data = {
    'Nome': ['Ana da Silva Santos', 'Maria Da Silva', 'João Dos Santos', 'José da Silva Santos'],
    'CPF': ['123.456.789-11', '123.456.789-11', '123.456.789-11', '123.456.789-11'],
    'Data': ['08/08/2025', '08/08/2025', '08/08/2025', '08/08/2025'],
    'Produto': ['Shampoo', 'Shampoo', 'Shampoo', 'Shampoo'],
    'Marca': ['Kerastase', "L'Oreal Professionnel", 'Redken', 'Redken'],
    'Valor': [150, 120, 130, 130]
}
df = pd.DataFrame(data)

if 'df_data' not in st.session_state:
    st.session_state.df_data = df

# Main container for the "spreadsheet"
with st.container():
    edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="data_editor")

# Logic for the Add-in in the "Add-ins" tab
with excel_tab:
    st.markdown("---")
    col1, col2, col3 = st.columns([2,2,8])
    with col1:
        if st.button("🚀 Privacy Partner Scan", help="Click to scan the spreadsheet for sensitive data."):
            with st.spinner("Analyzing spreadsheet..."):
                findings = []
                current_df = edited_df
                for index, row in current_df.iterrows():
                    for col_name, cell_value in row.items():
                        if cell_value and isinstance(cell_value, str):
                            results = analyzer.analyze(text=cell_value, language="pt")
                            if results:
                                findings.append({'row': index, 'col': col_name, 'text': cell_value, 'type': results[0].entity_type})
                st.session_state.findings = findings

# Sidebar acting as the Add-in's task pane
with st.sidebar:
    st.title("Privacy Partner")
    st.markdown("Your privacy assistant for Excel.")
    st.markdown("---")

    if 'findings' in st.session_state and st.session_state.findings:
        st.warning(f"**Alert!** {len(st.session_state.findings)} sensitive data point(s) found.")
        
        for find in st.session_state.findings:
            st.markdown(f"- **Column '{find['col']}'**: Found **{find['type']}**.")

        st.markdown("---")
        st.markdown("**Recommended Actions:**")

        if st.button("Anonymize Data"):
            anonymized_df = edited_df.copy()
            for find in st.session_state.findings:
                anonymized_df.at[find['row'], find['col']] = f"<{find['type']}>"
            
            st.session_state.df_data = anonymized_df
            st.session_state.findings = []
            st.success("Data has been anonymized!")
            st.rerun()

    else:
        st.success("No sensitive data detected in the spreadsheet.")
